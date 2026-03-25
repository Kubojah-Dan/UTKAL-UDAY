"""
Student engagement endpoints: streaks, daily challenges, offline download
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from app.core.database import questions_collection
from app.core.streak_service import (
    get_or_create_streak, update_streak,
    get_daily_challenge, set_daily_challenge,
    check_daily_challenge_completed, mark_daily_challenge_completed
)
from app.core.spaced_repetition import get_next_review_date
import random

router = APIRouter()


@router.get("/student/streak/{student_id}")
async def get_streak(student_id: str):
    streak = await get_or_create_streak(student_id)
    return streak


@router.post("/student/streak/{student_id}/update")
async def record_activity(student_id: str):
    """Call this whenever a student answers a question"""
    streak = await update_streak(student_id)
    bonus_xp = 0
    message = None
    if streak["current_streak"] > 1:
        bonus_xp = min(streak["current_streak"] * 5, 50)
        message = f"{streak['current_streak']} day streak! +{bonus_xp} bonus XP"
    return {**streak, "bonus_xp": bonus_xp, "message": message}


@router.get("/student/daily-challenge")
async def daily_challenge(
    grade: int = Query(..., ge=1, le=12),
    student_id: Optional[str] = None
):
    """Get today's daily challenge question"""
    challenge = await get_daily_challenge(grade)

    # Auto-create if none exists
    if not challenge:
        cursor = questions_collection.find({
            "grade": grade,
            "approved": True,
            "status": "active",
            "difficulty": "hard"
        })
        hard_questions = await cursor.to_list(length=50)
        if not hard_questions:
            cursor = questions_collection.find({
                "grade": grade,
                "approved": True,
                "status": "active"
            })
            hard_questions = await cursor.to_list(length=50)

        if hard_questions:
            chosen = random.choice(hard_questions)
            await set_daily_challenge(grade, "Math", chosen["id"], bonus_xp=50)
            challenge = {"question_id": chosen["id"], "bonus_xp": 50, "grade": grade}

    if not challenge:
        return {"available": False}

    # Fetch the actual question
    q = await questions_collection.find_one({"id": challenge["question_id"]})
    if not q:
        return {"available": False}
    q.pop("_id", None)

    completed = False
    if student_id:
        completed = await check_daily_challenge_completed(student_id, grade)

    return {
        "available": True,
        "completed": completed,
        "bonus_xp": challenge.get("bonus_xp", 50),
        "question": q
    }


@router.post("/student/daily-challenge/complete")
async def complete_daily_challenge(payload: dict):
    student_id = payload.get("student_id")
    grade = payload.get("grade", 1)
    if not student_id:
        return {"error": "student_id required"}
    await mark_daily_challenge_completed(student_id, grade)
    return {"success": True, "bonus_xp": 50, "message": "Daily challenge complete! +50 XP"}


@router.get("/student/spaced-review/{student_id}")
async def get_spaced_review_questions(
    student_id: str,
    grade: int = Query(..., ge=1, le=12),
    limit: int = Query(5, ge=1, le=20)
):
    """Get questions due for spaced repetition review"""
    from datetime import datetime
    from app.core.database import async_db

    reviews_col = async_db["spaced_reviews"]
    now = datetime.utcnow().isoformat()

    # Find questions due for review
    cursor = reviews_col.find({
        "student_id": student_id,
        "next_review": {"$lte": now}
    }).sort("next_review", 1).limit(limit)

    due = await cursor.to_list(length=limit)
    question_ids = [r["question_id"] for r in due]

    questions = []
    for qid in question_ids:
        q = await questions_collection.find_one({"id": qid})
        if q:
            q.pop("_id", None)
            questions.append(q)

    return {"questions": questions, "count": len(questions), "due_count": len(due)}


@router.post("/student/spaced-review/update")
async def update_spaced_review(payload: dict):
    """Update spaced repetition schedule after answering"""
    from app.core.database import async_db

    reviews_col = async_db["spaced_reviews"]
    student_id = payload.get("student_id")
    question_id = payload.get("question_id")
    correct = payload.get("correct", False)
    time_ms = payload.get("time_ms", 30000)
    hints = payload.get("hints", 0)

    if not student_id or not question_id:
        return {"error": "student_id and question_id required"}

    existing = await reviews_col.find_one({"student_id": student_id, "question_id": question_id})
    ease_factor = existing.get("ease_factor", 2.5) if existing else 2.5
    interval = existing.get("interval_days", 0) if existing else 0

    review_data = get_next_review_date(correct, time_ms, hints, ease_factor, interval)

    await reviews_col.update_one(
        {"student_id": student_id, "question_id": question_id},
        {"$set": {
            "student_id": student_id,
            "question_id": question_id,
            **review_data,
            "attempts": (existing.get("attempts", 0) if existing else 0) + 1
        }},
        upsert=True
    )
    return {"success": True, **review_data}


@router.get("/questions/download")
async def download_questions_for_offline(
    grade: int = Query(..., ge=1, le=12),
    subject: Optional[str] = None,
    limit: int = Query(200, ge=1, le=500)
):
    """Download questions for offline use"""
    query = {"approved": True, "status": "active", "grade": grade}
    if subject:
        query["subject"] = subject

    cursor = questions_collection.find(query).limit(limit)
    questions = await cursor.to_list(length=limit)
    for q in questions:
        q.pop("_id", None)

    return {"questions": questions, "count": len(questions), "grade": grade}
