from collections import defaultdict
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.core.interaction_store import load_interactions
from app.core.question_bank import get_question_by_id

router = APIRouter()


def _require_teacher(user: Dict):
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Teacher role required")


def _resolve_subject_grade(row):
    subject = row.get("subject")
    grade = row.get("grade")
    if subject and grade is not None:
        return subject, grade

    q = get_question_by_id(str(row.get("problem_id") or row.get("quest_id")))
    if not q:
        return subject or "Unknown", grade if grade is not None else "Unknown"
    return subject or q.get("subject", "Unknown"), grade if grade is not None else q.get("grade", "Unknown")


def _aggregate(records):
    students = defaultdict(lambda: {"attempts": 0, "correct": 0, "time_sum": 0})
    subjects = defaultdict(lambda: {"attempts": 0, "correct": 0})
    grades = defaultdict(lambda: {"attempts": 0, "correct": 0})
    skills = defaultdict(lambda: {"attempts": 0, "correct": 0})

    for row in records:
        sid = str(row.get("student_id") or "unknown")
        students[sid]["attempts"] += 1
        students[sid]["correct"] += int(bool(row.get("outcome")))
        students[sid]["time_sum"] += int(row.get("time_ms") or 0)

        subject, grade = _resolve_subject_grade(row)
        subjects[str(subject)]["attempts"] += 1
        subjects[str(subject)]["correct"] += int(bool(row.get("outcome")))
        grades[str(grade)]["attempts"] += 1
        grades[str(grade)]["correct"] += int(bool(row.get("outcome")))

        skill = str(row.get("skill_id") or "unknown")
        skills[skill]["attempts"] += 1
        skills[skill]["correct"] += int(bool(row.get("outcome")))

    return students, subjects, grades, skills


@router.get("/teacher/analytics")
def teacher_analytics(
    user=Depends(get_current_user),
    recent_limit: int = Query(30, ge=5, le=200),
):
    _require_teacher(user)
    records = load_interactions(limit=50000)
    students, subjects, grades, skills = _aggregate(records)

    total_attempts = len(records)
    total_correct = sum(int(bool(r.get("outcome"))) for r in records)
    avg_time = sum(int(r.get("time_ms") or 0) for r in records) / max(1, total_attempts)

    student_progress = []
    for sid, s in students.items():
        attempts = s["attempts"]
        student_progress.append(
            {
                "student_id": sid,
                "attempts": attempts,
                "correct": s["correct"],
                "accuracy": s["correct"] / max(1, attempts),
                "avg_time_ms": s["time_sum"] / max(1, attempts),
            }
        )
    student_progress.sort(key=lambda x: (-x["attempts"], x["student_id"]))

    subject_breakdown = [
        {
            "subject": subject,
            "attempts": payload["attempts"],
            "accuracy": payload["correct"] / max(1, payload["attempts"]),
        }
        for subject, payload in subjects.items()
    ]
    subject_breakdown.sort(key=lambda x: -x["attempts"])

    grade_breakdown = [
        {
            "grade": grade,
            "attempts": payload["attempts"],
            "accuracy": payload["correct"] / max(1, payload["attempts"]),
        }
        for grade, payload in grades.items()
    ]
    grade_breakdown.sort(key=lambda x: str(x["grade"]))

    skill_mastery = [
        {
            "skill_id": skill,
            "attempts": payload["attempts"],
            "accuracy": payload["correct"] / max(1, payload["attempts"]),
        }
        for skill, payload in skills.items()
    ]
    skill_mastery.sort(key=lambda x: (-x["attempts"], x["skill_id"]))

    recent = sorted(records, key=lambda r: int(r.get("timestamp", 0)), reverse=True)[:recent_limit]

    return {
        "overview": {
            "total_students": len(students),
            "total_attempts": total_attempts,
            "overall_accuracy": total_correct / max(1, total_attempts),
            "avg_time_ms": avg_time,
        },
        "subject_breakdown": subject_breakdown,
        "grade_breakdown": grade_breakdown,
        "student_progress": student_progress,
        "skill_mastery": skill_mastery[:20],
        "recent_activity": recent,
    }


@router.get("/teacher/student/{student_id}")
def teacher_student_detail(student_id: str, user=Depends(get_current_user)):
    _require_teacher(user)
    records = load_interactions(student_id=student_id, limit=10000)
    students, subjects, grades, skills = _aggregate(records)
    student = students.get(student_id, {"attempts": 0, "correct": 0, "time_sum": 0})

    return {
        "student_id": student_id,
        "attempts": student["attempts"],
        "accuracy": student["correct"] / max(1, student["attempts"]),
        "avg_time_ms": student["time_sum"] / max(1, student["attempts"]),
        "subject_breakdown": subjects,
        "grade_breakdown": grades,
        "skill_breakdown": skills,
        "recent": sorted(records, key=lambda r: int(r.get("timestamp", 0)), reverse=True)[:50],
    }
