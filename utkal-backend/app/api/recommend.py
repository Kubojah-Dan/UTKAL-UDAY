from typing import Dict, Optional

from fastapi import APIRouter, Query

from app.core.interaction_store import load_interactions
from app.core.question_bank import get_questions

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
def recommend(
    student_id: str,
    limit: int = Query(5, ge=1, le=50),
    subject: Optional[str] = None,
    grade: Optional[int] = Query(None, ge=1, le=12),
):
    questions = get_questions(subject=subject, grade=grade)
    records = load_interactions(student_id=student_id, limit=5000)
    stats = _skill_stats(records)

    ranked = sorted(questions, key=lambda q: _score_question(q, stats), reverse=True)
    selected = ranked[:limit]

    quests = [
        {
            "quest_id": q["id"],
            "problemId": q["id"],
            "subject": q.get("subject"),
            "grade": q.get("grade"),
            "skill_id": q.get("skill_id"),
            "skill_str": q.get("skill_label"),
            "difficulty": q.get("difficulty"),
        }
        for q in selected
    ]

    return {
        "student_id": student_id,
        "count": len(quests),
        "quests": quests,
        "reason": "Sorted by low estimated mastery and unseen skills",
    }
