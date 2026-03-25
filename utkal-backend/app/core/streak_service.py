"""
Streak and Daily Challenge tracking
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from app.core.database import async_db


streaks_collection = async_db["student_streaks"]
daily_challenge_collection = async_db["daily_challenges"]


async def get_or_create_streak(student_id: str) -> Dict:
    doc = await streaks_collection.find_one({"student_id": student_id})
    if not doc:
        doc = {
            "student_id": student_id,
            "current_streak": 0,
            "longest_streak": 0,
            "last_active_date": None,
            "total_days_active": 0,
        }
        await streaks_collection.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def update_streak(student_id: str) -> Dict:
    today = date.today().isoformat()
    doc = await get_or_create_streak(student_id)

    last = doc.get("last_active_date")
    current = doc.get("current_streak", 0)
    longest = doc.get("longest_streak", 0)
    total_days = doc.get("total_days_active", 0)

    if last == today:
        # Already active today, no change
        return doc

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if last == yesterday:
        current += 1
    else:
        current = 1  # streak broken or first day

    longest = max(longest, current)
    total_days += 1

    updated = {
        "current_streak": current,
        "longest_streak": longest,
        "last_active_date": today,
        "total_days_active": total_days,
    }
    await streaks_collection.update_one(
        {"student_id": student_id},
        {"$set": updated},
        upsert=True
    )
    return {**doc, **updated}


async def get_daily_challenge(grade: int, subject: str = "Math") -> Optional[Dict]:
    """Get today's daily challenge question"""
    today = date.today().isoformat()
    challenge = await daily_challenge_collection.find_one({
        "date": today,
        "grade": grade,
        "subject": subject
    })
    if challenge:
        challenge.pop("_id", None)
    return challenge


async def set_daily_challenge(grade: int, subject: str, question_id: str, bonus_xp: int = 50):
    """Set today's daily challenge"""
    today = date.today().isoformat()
    await daily_challenge_collection.update_one(
        {"date": today, "grade": grade, "subject": subject},
        {"$set": {
            "date": today,
            "grade": grade,
            "subject": subject,
            "question_id": question_id,
            "bonus_xp": bonus_xp,
        }},
        upsert=True
    )


async def check_daily_challenge_completed(student_id: str, grade: int) -> bool:
    today = date.today().isoformat()
    doc = await daily_challenge_collection.find_one({
        "date": today,
        "grade": grade,
        f"completed.{student_id}": {"$exists": True}
    })
    return doc is not None


async def mark_daily_challenge_completed(student_id: str, grade: int, subject: str = "Math"):
    today = date.today().isoformat()
    await daily_challenge_collection.update_one(
        {"date": today, "grade": grade, "subject": subject},
        {"$set": {f"completed.{student_id}": datetime.utcnow().isoformat()}}
    )
