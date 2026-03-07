from typing import Dict, Optional

from fastapi import APIRouter, Query

from app.core.interaction_store import load_interactions
from app.core.kt_inference import estimate_dkt_next_correct, estimate_skill_mastery, rank_question_for_student
from app.core.question_bank import get_questions
from app.core.database import questions_collection
import random

router = APIRouter()


def _skill_stats(records) -> Dict[str, Dict]:
    stats = {}
    for r in records:
        skill = str(r.get("skill_id") or "unknown")
        if skill not in stats:
            stats[skill] = {"attempts": 0, "correct": 0}
        stats[skill]["attempts"] += 1
        stats[skill]["correct"] += int(bool(r.get("outcome")))
    return stats


def _score_question(question: Dict, stats: Dict[str, Dict]) -> float:
    skill = str(question.get("skill_id") or "unknown")
    s = stats.get(skill)
    if not s:
        return 1.0
    attempts = max(1, s["attempts"])
    accuracy = s["correct"] / attempts
    return 1.0 - accuracy + min(0.25, attempts / 100.0)


@router.get("/recommend/{student_id}")
async def recommend(
    student_id: str,
    limit: int = Query(5, ge=1, le=50),
    subject: Optional[str] = None,
    grade: Optional[int] = Query(None, ge=1, le=12),
):
    records = load_interactions(student_id=student_id, limit=5000)
    stats = _skill_stats(records)
    skill_mastery = estimate_skill_mastery(records)
    dkt_next = estimate_dkt_next_correct(records)

    # Get teacher-generated questions from MongoDB
    mongo_questions = []
    try:
        query = {"approved": True, "status": "active"}
        if subject:
            query["subject"] = subject
        if grade:
            query["grade"] = grade
        
        cursor = questions_collection.find(query).limit(limit * 10)
        mongo_qs = await cursor.to_list(length=limit * 10)
        for q in mongo_qs:
            q.pop("_id", None)
            mongo_questions.append(q)
    except:
        pass

    # Pull candidate pool from question bank
    candidate_limit = min(1600, max(260, limit * 90))
    start_offset = (len(records) * 13 + sum(ord(ch) for ch in str(student_id))) % 500
    base_questions = get_questions(
        subject=subject,
        grade=grade,
        offset=start_offset,
        limit=candidate_limit,
        include_generated=True,
    )
    
    # Combine both sources
    questions = mongo_questions + base_questions

    recent_question_ids = {
        str(r.get("problem_id") or r.get("quest_id"))
        for r in sorted(records, key=lambda r: int(r.get("timestamp", 0) or 0), reverse=True)[:120]
    }

    scored = []
    for q in questions:
        base_score = _score_question(q, stats)
        kt_score, kt_details = rank_question_for_student(
            q,
            records,
            skill_mastery=skill_mastery,
            dkt_next=dkt_next,
        )
        seen_penalty = -0.08 if str(q.get("id")) in recent_question_ids else 0.0
        final_score = 0.45 * base_score + 0.55 * kt_score + seen_penalty
        scored.append((final_score, q, kt_details))

    scored.sort(key=lambda row: row[0], reverse=True)
    selected = scored[:limit]

    quests = [
        {
            "quest_id": q["id"],
            "problemId": q["id"],
            "subject": q.get("subject"),
            "grade": q.get("grade"),
            "skill_id": q.get("skill_id"),
            "skill_str": q.get("skill_label"),
            "difficulty": q.get("difficulty"),
            "recommendation_score": round(score, 4),
            "kt_signal": details,
        }
        for score, q, details in selected
    ]

    return {
        "student_id": student_id,
        "count": len(quests),
        "quests": quests,
        "reason": "Sorted by KT remediation need, recency, and unseen-skill priority",
    }
