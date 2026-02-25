from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import math
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.core.interaction_store import load_interactions
from app.core.question_bank import get_question_by_id

router = APIRouter()

XP_PER_LEVEL = 120


def _safe_int(value, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _optional_int(value) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _epoch_ms(raw_ts) -> int:
    ts = _safe_int(raw_ts, 0)
    if ts < 10_000_000_000:
        return ts * 1000
    return ts


def _level_from_xp(xp: int) -> int:
    return max(1, (max(0, xp) // XP_PER_LEVEL) + 1)


def _skill_gpa(accuracy: float) -> float:
    return round(max(0.0, min(1.0, float(accuracy))) * 4.0, 2)


def _node_id(label: str) -> str:
    digest = hashlib.md5(label.encode("utf8")).hexdigest()[:10]
    return f"kc-{digest}"


def _badge_count(stat: Dict) -> int:
    attempts = stat["attempts"]
    correct = stat["correct"]
    fast_correct = stat["fast_correct"]
    subjects_seen = len(stat["subjects"])
    xp_sum = stat["xp_sum"]
    accuracy = correct / max(1, attempts)

    badges = 0
    if correct > 0:
        badges += 1
    if attempts >= 10:
        badges += 1
    if attempts >= 20 and accuracy >= 0.8:
        badges += 1
    if fast_correct >= 5:
        badges += 1
    if subjects_seen >= 3:
        badges += 1
    if _level_from_xp(xp_sum) >= 5:
        badges += 1
    if attempts >= 40:
        badges += 1
    if attempts >= 30 and accuracy >= 0.9:
        badges += 1
    if xp_sum >= 1500:
        badges += 1
    return badges


def _require_teacher(user: Dict):
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Teacher role required")


def _resolve_subject_grade(row: Dict) -> Tuple[str, object]:
    subject = row.get("subject")
    grade = row.get("grade")
    if subject and grade is not None:
        return str(subject), grade

    q = get_question_by_id(str(row.get("problem_id") or row.get("quest_id")))
    if not q:
        return str(subject or "Unknown"), grade if grade is not None else "Unknown"
    return str(subject or q.get("subject", "Unknown")), grade if grade is not None else q.get("grade", "Unknown")


def _record_school(row: Dict) -> str:
    school = str(row.get("school") or "").strip()
    return school


def _record_class_grade(row: Dict) -> Optional[int]:
    explicit = _optional_int(row.get("class_grade"))
    if explicit is not None:
        return explicit
    return _optional_int(row.get("grade"))


def _filter_records(records: List[Dict], school: Optional[str], class_grade: Optional[int]) -> List[Dict]:
    school_key = (school or "").strip().lower()
    filtered = []
    for row in records:
        row_school = _record_school(row)
        row_class_grade = _record_class_grade(row)

        if school_key and row_school.lower() != school_key:
            continue
        if class_grade is not None and row_class_grade != class_grade:
            continue
        filtered.append(row)
    return filtered


def _aggregate(records: List[Dict]):
    students = defaultdict(
        lambda: {
            "attempts": 0,
            "correct": 0,
            "time_sum": 0,
            "xp_sum": 0,
            "fast_correct": 0,
            "subjects": set(),
            "schools": set(),
            "class_grades": set(),
        }
    )
    subjects = defaultdict(lambda: {"attempts": 0, "correct": 0, "xp_sum": 0})
    grades = defaultdict(lambda: {"attempts": 0, "correct": 0})
    class_grades = defaultdict(lambda: {"attempts": 0, "correct": 0})
    schools = defaultdict(lambda: {"attempts": 0, "correct": 0})
    skills = defaultdict(lambda: {"attempts": 0, "correct": 0})

    for row in records:
        sid = str(row.get("student_id") or "unknown")
        correct = int(bool(row.get("outcome")))
        time_ms = _safe_int(row.get("time_ms"), 0)
        xp_awarded = max(0, _safe_int(row.get("xp_awarded"), 0))

        students[sid]["attempts"] += 1
        students[sid]["correct"] += correct
        students[sid]["time_sum"] += time_ms
        students[sid]["xp_sum"] += xp_awarded
        if correct and 0 < time_ms <= 45000:
            students[sid]["fast_correct"] += 1

        subject, grade = _resolve_subject_grade(row)
        school = _record_school(row) or "Unknown"
        class_grade = _record_class_grade(row)

        students[sid]["subjects"].add(subject)
        students[sid]["schools"].add(school)
        if class_grade is not None:
            students[sid]["class_grades"].add(class_grade)

        subjects[subject]["attempts"] += 1
        subjects[subject]["correct"] += correct
        subjects[subject]["xp_sum"] += xp_awarded

        grade_key = str(grade if grade is not None else "Unknown")
        grades[grade_key]["attempts"] += 1
        grades[grade_key]["correct"] += correct

        class_key = str(class_grade if class_grade is not None else "Unknown")
        class_grades[class_key]["attempts"] += 1
        class_grades[class_key]["correct"] += correct

        schools[school]["attempts"] += 1
        schools[school]["correct"] += correct

        skill = str(row.get("skill_id") or "unknown")
        skills[skill]["attempts"] += 1
        skills[skill]["correct"] += correct

    return students, subjects, grades, class_grades, schools, skills


def _breakdown_payload(name: str, bucket: Dict, include_xp: bool = False) -> List[Dict]:
    payload = []
    for key, stat in bucket.items():
        row = {
            name: key,
            "attempts": stat["attempts"],
            "accuracy": stat["correct"] / max(1, stat["attempts"]),
        }
        if include_xp:
            row["xp"] = stat.get("xp_sum", 0)
        payload.append(row)
    return payload


def _sorted_numeric_or_text(value: object):
    try:
        return (0, int(value))
    except (TypeError, ValueError):
        return (1, str(value))


def _daily_trend(records: List[Dict], window_days: int = 30) -> List[Dict]:
    by_day = defaultdict(lambda: {"attempts": 0, "correct": 0, "xp": 0})
    max_seen_ts = 0
    for row in records:
        ts = _epoch_ms(row.get("timestamp"))
        if ts <= 0:
            continue
        max_seen_ts = max(max_seen_ts, ts)
        day = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")
        by_day[day]["attempts"] += 1
        by_day[day]["correct"] += int(bool(row.get("outcome")))
        by_day[day]["xp"] += max(0, _safe_int(row.get("xp_awarded"), 0))

    end_dt = datetime.now(tz=timezone.utc)
    if max_seen_ts > 0:
        end_dt = datetime.fromtimestamp(max_seen_ts / 1000.0, tz=timezone.utc)
    start_dt = end_dt - timedelta(days=max(1, window_days) - 1)

    out = []
    cursor = start_dt
    while cursor <= end_dt:
        day = cursor.strftime("%Y-%m-%d")
        stat = by_day.get(day, {"attempts": 0, "correct": 0, "xp": 0})
        out.append(
            {
                "date": day,
                "attempts": stat["attempts"],
                "accuracy": stat["correct"] / max(1, stat["attempts"]),
                "xp": stat["xp"],
            }
        )
        cursor += timedelta(days=1)
    return out


def _record_skill_route(row: Dict) -> List[str]:
    q = get_question_by_id(str(row.get("problem_id") or row.get("quest_id")))
    if q and isinstance(q.get("skill_route"), list) and q.get("skill_route"):
        return [str(seg).strip() for seg in q.get("skill_route", []) if str(seg).strip()]

    fallback_skill = str(row.get("skill_id") or "").strip()
    if fallback_skill:
        return [fallback_skill]
    return ["unknown"]


def _build_xai_payload(records: List[Dict]) -> Dict:
    node_stats = defaultdict(lambda: {"attempts": 0, "correct": 0})
    edge_stats = defaultdict(lambda: {"support": 0, "correct": 0})

    for row in records:
        outcome = int(bool(row.get("outcome")))
        route = _record_skill_route(row)
        if not route:
            continue

        for label in route:
            node_stats[label]["attempts"] += 1
            node_stats[label]["correct"] += outcome

        for i in range(len(route) - 1):
            src = route[i]
            dst = route[i + 1]
            edge_stats[(src, dst)]["support"] += 1
            edge_stats[(src, dst)]["correct"] += outcome

    if not node_stats:
        return {
            "graph": {"nodes": [], "edges": []},
            "root_causes": [],
            "prerequisite_gaps": [],
            "causal_chains": [],
        }

    node_id_map = {label: _node_id(label) for label in node_stats.keys()}
    nodes = []
    node_lookup: Dict[str, Dict] = {}
    for label, stat in node_stats.items():
        attempts = stat["attempts"]
        accuracy = stat["correct"] / max(1, attempts)
        gpa = _skill_gpa(accuracy)
        risk_score = (1.0 - accuracy) * math.log(attempts + 1.0)
        risk = "high" if accuracy < 0.5 else ("medium" if accuracy < 0.7 else "low")
        node = {
            "id": node_id_map[label],
            "label": label,
            "attempts": attempts,
            "accuracy": round(accuracy, 4),
            "gpa": gpa,
            "risk": risk,
            "risk_score": round(risk_score, 4),
        }
        nodes.append(node)
        node_lookup[node["id"]] = node

    edges = []
    for (src_label, dst_label), stat in edge_stats.items():
        support = stat["support"]
        accuracy = stat["correct"] / max(1, support)
        edges.append(
            {
                "source": node_id_map[src_label],
                "target": node_id_map[dst_label],
                "source_label": src_label,
                "target_label": dst_label,
                "support": support,
                "accuracy": round(accuracy, 4),
                "weight": round(min(1.0, support / 25.0), 4),
            }
        )

    nodes.sort(key=lambda n: (-n["attempts"], n["label"]))
    edges.sort(key=lambda e: (-e["support"], e["source_label"], e["target_label"]))

    root_candidates = [n for n in nodes if n["attempts"] >= 5]
    root_candidates.sort(key=lambda n: (-n["risk_score"], n["gpa"]))
    root_causes = [
        {
            "skill_id": n["id"],
            "skill_label": n["label"],
            "attempts": n["attempts"],
            "accuracy": n["accuracy"],
            "gpa": n["gpa"],
            "risk": n["risk"],
            "recommended_action": (
                "Prerequisite micro-lessons + guided practice"
                if n["risk"] == "high"
                else "Targeted practice and quick check-ins"
            ),
        }
        for n in root_candidates[:12]
    ]

    prerequisite_gaps = []
    for e in edges:
        src = node_lookup[e["source"]]
        dst = node_lookup[e["target"]]
        if src["attempts"] < 3 or dst["attempts"] < 3:
            continue
        gap = round(dst["gpa"] - src["gpa"], 2)
        if gap < 0.35:
            continue
        prerequisite_gaps.append(
            {
                "prerequisite_id": src["id"],
                "prerequisite_label": src["label"],
                "prerequisite_gpa": src["gpa"],
                "dependent_id": dst["id"],
                "dependent_label": dst["label"],
                "dependent_gpa": dst["gpa"],
                "gap": gap,
                "support": e["support"],
            }
        )
    prerequisite_gaps.sort(key=lambda g: (-g["gap"], -g["support"], g["prerequisite_label"]))
    prerequisite_gaps = prerequisite_gaps[:20]

    adjacency = defaultdict(list)
    edge_support = {}
    for e in edges:
        adjacency[e["source"]].append(e["target"])
        edge_support[(e["source"], e["target"])] = e["support"]

    causal_chains = []
    for root in root_causes[:8]:
        path = [root["skill_id"]]
        visited = set(path)
        cursor = root["skill_id"]
        supports = []
        for _ in range(4):
            neighbors = [n for n in adjacency.get(cursor, []) if n not in visited]
            if not neighbors:
                break
            # Expand toward weaker downstream nodes first.
            neighbors.sort(key=lambda nid: (node_lookup[nid]["gpa"], -node_lookup[nid]["attempts"]))
            nxt = neighbors[0]
            supports.append(edge_support.get((cursor, nxt), 0))
            path.append(nxt)
            visited.add(nxt)
            cursor = nxt
        if len(path) < 2:
            continue
        chain_nodes = [node_lookup[nid] for nid in path]
        avg_gpa = round(sum(n["gpa"] for n in chain_nodes) / len(chain_nodes), 2)
        weakest = min(chain_nodes, key=lambda n: n["gpa"])
        confidence = round(min(1.0, (sum(supports) / max(1, len(supports))) / 12.0), 3)
        causal_chains.append(
            {
                "path": [n["label"] for n in chain_nodes],
                "weakest_skill": weakest["label"],
                "avg_gpa": avg_gpa,
                "confidence": confidence,
            }
        )
    causal_chains.sort(key=lambda c: (c["avg_gpa"], -c["confidence"]))
    causal_chains = causal_chains[:12]

    return {
        "graph": {"nodes": nodes[:120], "edges": edges[:240]},
        "root_causes": root_causes,
        "prerequisite_gaps": prerequisite_gaps,
        "causal_chains": causal_chains,
    }


def _filter_options(records: List[Dict], teacher_school: Optional[str], teacher_grade: Optional[int]) -> Dict:
    schools = sorted({_record_school(r) for r in records if _record_school(r)})
    grades = sorted({_record_class_grade(r) for r in records if _record_class_grade(r) is not None})

    if teacher_school and teacher_school not in schools:
        schools.append(teacher_school)
        schools.sort()
    if teacher_grade is not None and teacher_grade not in grades:
        grades.append(teacher_grade)
        grades.sort()

    return {"schools": schools, "class_grades": grades}


@router.get("/teacher/analytics")
def teacher_analytics(
    user=Depends(get_current_user),
    recent_limit: int = Query(30, ge=5, le=200),
    school: Optional[str] = Query(None),
    class_grade: Optional[int] = Query(None, ge=1, le=12),
    trend_days: int = Query(30, ge=7, le=120),
):
    _require_teacher(user)
    records = load_interactions(limit=50000)

    teacher_school = str(user.get("school") or "").strip() or None
    teacher_grade = _optional_int(user.get("class_grade"))
    selected_school = school.strip() if school else teacher_school
    selected_grade = class_grade if class_grade is not None else teacher_grade

    filtered_records = _filter_records(records, selected_school, selected_grade)
    students, subjects, grades, class_grades, schools, skills = _aggregate(filtered_records)

    total_attempts = len(filtered_records)
    total_correct = sum(int(bool(r.get("outcome"))) for r in filtered_records)
    avg_time = sum(_safe_int(r.get("time_ms"), 0) for r in filtered_records) / max(1, total_attempts)
    total_xp = sum(max(0, _safe_int(r.get("xp_awarded"), 0)) for r in filtered_records)

    student_progress = []
    for sid, stat in students.items():
        attempts = stat["attempts"]
        xp = stat["xp_sum"]
        schools_seen = sorted(stat["schools"])
        grades_seen = sorted(stat["class_grades"])
        student_progress.append(
            {
                "student_id": sid,
                "attempts": attempts,
                "correct": stat["correct"],
                "accuracy": stat["correct"] / max(1, attempts),
                "avg_time_ms": stat["time_sum"] / max(1, attempts),
                "xp": xp,
                "level": _level_from_xp(xp),
                "badges": _badge_count(stat),
                "school": schools_seen[0] if len(schools_seen) == 1 else ("Mixed" if schools_seen else "Unknown"),
                "class_grade": (
                    grades_seen[0]
                    if len(grades_seen) == 1
                    else ("Mixed" if grades_seen else None)
                ),
            }
        )
    student_progress.sort(key=lambda x: (-x["xp"], -x["attempts"], x["student_id"]))

    subject_breakdown = _breakdown_payload("subject", subjects, include_xp=True)
    subject_breakdown.sort(key=lambda x: -x["attempts"])

    grade_breakdown = _breakdown_payload("grade", grades)
    grade_breakdown.sort(key=lambda x: _sorted_numeric_or_text(x["grade"]))

    class_grade_breakdown = _breakdown_payload("class_grade", class_grades)
    class_grade_breakdown.sort(key=lambda x: _sorted_numeric_or_text(x["class_grade"]))

    school_breakdown = _breakdown_payload("school", schools)
    school_breakdown.sort(key=lambda x: -x["attempts"])

    skill_mastery = _breakdown_payload("skill_id", skills)
    skill_mastery.sort(key=lambda x: (-x["attempts"], x["skill_id"]))

    recent = sorted(filtered_records, key=lambda r: _safe_int(r.get("timestamp"), 0), reverse=True)[:recent_limit]
    trend = _daily_trend(filtered_records, window_days=trend_days)
    xai_payload = _build_xai_payload(filtered_records)

    return {
        "filters": {"school": selected_school, "class_grade": selected_grade},
        "filter_options": _filter_options(records, teacher_school, teacher_grade),
        "trend_window_days": trend_days,
        "overview": {
            "total_students": len(students),
            "total_attempts": total_attempts,
            "overall_accuracy": total_correct / max(1, total_attempts),
            "avg_time_ms": avg_time,
            "total_xp": total_xp,
        },
        "daily_trend": trend,
        "subject_breakdown": subject_breakdown,
        "grade_breakdown": grade_breakdown,
        "class_grade_breakdown": class_grade_breakdown,
        "school_breakdown": school_breakdown,
        "student_progress": student_progress,
        "skill_mastery": skill_mastery[:20],
        "xai": xai_payload,
        "recent_activity": recent,
    }


@router.get("/teacher/student/{student_id}")
def teacher_student_detail(student_id: str, user=Depends(get_current_user)):
    _require_teacher(user)
    records = load_interactions(student_id=student_id, limit=10000)

    teacher_school = str(user.get("school") or "").strip() or None
    teacher_grade = _optional_int(user.get("class_grade"))
    filtered_records = _filter_records(records, teacher_school, teacher_grade)

    students, subjects, grades, class_grades, schools, skills = _aggregate(filtered_records)
    student = students.get(
        student_id,
        {"attempts": 0, "correct": 0, "time_sum": 0, "xp_sum": 0, "fast_correct": 0, "subjects": set()},
    )

    return {
        "student_id": student_id,
        "attempts": student["attempts"],
        "accuracy": student["correct"] / max(1, student["attempts"]),
        "avg_time_ms": student["time_sum"] / max(1, student["attempts"]),
        "xp": student["xp_sum"],
        "level": _level_from_xp(student["xp_sum"]),
        "badges": _badge_count(student),
        "subject_breakdown": _breakdown_payload("subject", subjects, include_xp=True),
        "grade_breakdown": _breakdown_payload("grade", grades),
        "class_grade_breakdown": _breakdown_payload("class_grade", class_grades),
        "school_breakdown": _breakdown_payload("school", schools),
        "skill_breakdown": _breakdown_payload("skill_id", skills),
        "recent": sorted(filtered_records, key=lambda r: _safe_int(r.get("timestamp"), 0), reverse=True)[:50],
    }
