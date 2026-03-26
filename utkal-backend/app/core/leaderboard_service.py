"""
Leaderboard service - stores student XP/level/badges in MongoDB
Updated on every sync so leaderboard reflects real activity.
"""
from typing import Optional, List
from app.core.database import async_db

leaderboard_col = async_db["student_leaderboard"]


async def upsert_student_stats(
    student_id: str,
    name: str,
    school: str,
    grade: int,
    total_xp: int,
    level: int,
    badges_earned: int,
    accuracy: float,
    total_attempts: int,
):
    """Upsert student stats into leaderboard collection."""
    from datetime import datetime
    await leaderboard_col.update_one(
        {"student_id": student_id},
        {"$set": {
            "student_id": student_id,
            "name": name,
            "school": school,
            "grade": grade,
            "total_xp": total_xp,
            "level": level,
            "badges_earned": badges_earned,
            "accuracy": round(accuracy, 3),
            "total_attempts": total_attempts,
            "last_active": datetime.utcnow().isoformat(),
        }},
        upsert=True
    )


async def get_leaderboard(
    grade: int,
    school: Optional[str] = None,
    limit: int = 50,
) -> List[dict]:
    """
    Get leaderboard for a grade.
    If school is provided, filter to that school only.
    Always sorted by total_xp descending.
    """
    query: dict = {"grade": grade}
    if school:
        query["school"] = school

    cursor = leaderboard_col.find(query).sort("total_xp", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    for r in rows:
        r.pop("_id", None)
    return rows
