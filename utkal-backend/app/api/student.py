"""
Student engagement endpoints: streaks, daily challenges, offline download
"""
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from app.core.database import questions_collection
from app.core.streak_service import (
    get_or_create_streak, update_streak,
    get_daily_challenge, set_daily_challenge,
    check_daily_challenge_completed, mark_daily_challenge_completed
)
from app.core.spaced_repetition import get_next_review_date
from app.core.leaderboard_service import upsert_student_stats, get_leaderboard
from app.core.question_localization import prepare_question_for_delivery, prepare_questions_for_delivery
from app.core.generated_question_bank import normalize_subject
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
    student_id: Optional[str] = None,
    language: Optional[str] = None,
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
    q = await prepare_question_for_delivery(
        q,
        target_langs=[language] if language else None,
        queue_missing=False,
    )

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
    limit: int = Query(5, ge=1, le=20),
    language: Optional[str] = None,
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
            prepared = await prepare_question_for_delivery(
                q,
                target_langs=[language] if language else None,
                queue_missing=False,
            )
            questions.append(prepared)

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


@router.get("/leaderboard")
async def leaderboard(
    grade: int = Query(..., ge=1, le=12),
    school: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get leaderboard for a grade.
    Pass school= to filter to one school, omit for all schools.
    """
    rows = await get_leaderboard(grade=grade, school=school, limit=limit)
    return {"leaderboard": rows, "count": len(rows), "grade": grade, "school": school}


@router.post("/leaderboard/update")
async def update_leaderboard(payload: dict):
    """
    Called by frontend after every sync to keep leaderboard current.
    Payload: student_id, name, school, grade, total_xp, level, badges_earned, accuracy, total_attempts
    """
    await upsert_student_stats(
        student_id=payload["student_id"],
        name=payload["name"],
        school=payload.get("school", ""),
        grade=int(payload.get("grade", 1)),
        total_xp=int(payload.get("total_xp", 0)),
        level=int(payload.get("level", 1)),
        badges_earned=int(payload.get("badges_earned", 0)),
        accuracy=float(payload.get("accuracy", 0)),
        total_attempts=int(payload.get("total_attempts", 0)),
    )
    return {"success": True}


@router.get("/student/questions/download")
async def download_questions_for_offline(
    grade: int = Query(..., ge=1, le=12),
    subject: Optional[str] = None,
    limit: int = Query(500, ge=1, le=1000),
    language: Optional[str] = None,
):
    """Download questions for offline use — includes generated questions to hit 500/subject"""
    from app.core.question_bank import get_questions

    canonical_subject = normalize_subject(subject) if subject else None
    query = {"approved": True, "status": "active", "grade": grade}
    if canonical_subject:
        query["subject"] = canonical_subject

    cursor = questions_collection.find(query).limit(limit)
    mongo_qs = await cursor.to_list(length=limit)
    for q in mongo_qs:
        q.pop("_id", None)

    remaining = limit - len(mongo_qs)
    generated = []
    if remaining > 0:
        generated = get_questions(subject=canonical_subject or subject, grade=grade, limit=remaining, include_generated=True)

    all_questions = mongo_qs + generated
    prepared = await prepare_questions_for_delivery(
        all_questions,
        target_langs=[language] if language else None,
        queue_missing=bool(language and language != "en"),
        queue_limit=min(limit, 60),
    )
    return {
        "questions": prepared,
        "count": len(prepared),
        "grade": grade,
        "subject": canonical_subject or subject,
        "warming_localizations": bool(language and language != "en"),
    }


@router.get("/quests/next/{student_id}")
async def get_next_quest(
    student_id: str,
    grade: int = Query(..., ge=1, le=12),
    subject: Optional[str] = None,
    language: Optional[str] = None,
    exclude_ids: Optional[List[str]] = Query(None),
):
    """Dynamic quest generation: finds weakest topic and assembles 10 questions"""
    from app.core.interaction_store import load_interactions
    from app.core.kt_inference import estimate_skill_mastery
    from app.core.question_bank import get_questions

    records = load_interactions(student_id=student_id, limit=2000)
    mastery = estimate_skill_mastery(records)
    recent_question_ids = {
        str(r.get("problem_id") or r.get("quest_id") or "")
        for r in records[-120:]
        if str(r.get("problem_id") or r.get("quest_id") or "").strip()
    }
    excluded_ids = {
        str(question_id).strip()
        for question_id in (exclude_ids or [])
        if str(question_id).strip()
    }
    blocked_ids = recent_question_ids | excluded_ids

    # Find weakest topic
    weakest_topic = None
    if mastery:
        weakest_topic = min(mastery, key=mastery.get)

    # Get questions for weakest topic or general
    questions = get_questions(subject=subject, grade=grade, limit=120, include_generated=True)
    filtered_questions = [q for q in questions if str(q.get("id") or "") not in blocked_ids]
    if filtered_questions:
        questions = filtered_questions

    # Filter by weakest topic if found
    if weakest_topic:
        topic_qs = [q for q in questions if weakest_topic.lower() in str(q.get("skill_id", "")).lower()]
        if len(topic_qs) >= 5:
            questions = topic_qs

    if not questions:
        questions = get_questions(subject=subject, grade=grade, limit=50, include_generated=True)
        questions = [q for q in questions if str(q.get("id") or "") not in excluded_ids] or questions

    random.shuffle(questions)
    selected = questions[:10]

    return {
        "student_id": student_id,
        "weakest_topic": weakest_topic,
        "questions": await prepare_questions_for_delivery(
            selected,
            target_langs=[language] if language else None,
            queue_missing=bool(language and language != "en"),
            queue_limit=2,
        ),
        "count": len(selected),
    }
