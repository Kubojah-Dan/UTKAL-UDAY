"""
Leaderboard service — 4-scope, rank-aware, motivational gap display.
Scopes: class | school | district | state
"""
from typing import Optional, List
from app.core.database import async_db
from datetime import datetime

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
    district: Optional[str] = None,
):
    """Upsert student stats into leaderboard collection."""
    await leaderboard_col.update_one(
        {"student_id": student_id},
        {"$set": {
            "student_id":     student_id,
            "name":           name,
            "school":         school,
            "grade":          grade,
            "district":       district or "",
            "total_xp":       total_xp,
            "level":          level,
            "badges_earned":  badges_earned,
            "accuracy":       round(accuracy, 3),
            "total_attempts": total_attempts,
            "last_active":    datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )


async def get_leaderboard(
    scope: str = "school",
    scope_value: Optional[str] = None,
    grade: Optional[int] = None,
    limit: int = 100,
) -> List[dict]:
    """
    Get ranked leaderboard for a scope.
    scope: 'class' | 'school' | 'district' | 'state'
    Returns rows with: rank, xp_gap_to_next, motivation_message
    """
    query: dict = {}
    if grade:
        query["grade"] = grade

    if scope == "school" and scope_value:
        query["school"] = scope_value
    elif scope == "district" and scope_value:
        query["district"] = scope_value
    elif scope == "class" and scope_value:
        query["school"] = scope_value
        if grade:
            query["grade"] = grade
    # scope == "state" → no additional filter

    cursor = leaderboard_col.find(query).sort("total_xp", -1).limit(limit)
    rows = await cursor.to_list(length=limit)

    # Add rank and XP gap to next position
    ranked = []
    for i, row in enumerate(rows):
        row.pop("_id", None)
        rank = i + 1
        xp_gap = 0
        if i > 0:
            xp_gap = rows[i - 1].get("total_xp", 0) - row.get("total_xp", 0)

        merit = _get_merit_tier_from_rank(rank)
        row.update({
            "rank":            rank,
            "xp_gap_to_next":  xp_gap,
            "merit_tier":      merit,
        })
        ranked.append(row)

    return ranked


async def get_my_rank(
    student_id: str,
    scope: str = "school",
    scope_value: Optional[str] = None,
    grade: Optional[int] = None,
) -> dict:
    """
    Get a specific student's rank and motivational message.
    Returns {rank, total_xp, xp_gap_to_next, motivation_message, merit_tier}
    """
    rows = await get_leaderboard(scope=scope, scope_value=scope_value, grade=grade, limit=1000)
    for row in rows:
        if row.get("student_id") == student_id:
            rank = row["rank"]
            gap  = row["xp_gap_to_next"]
            total_xp = row.get("total_xp", 0)

            if rank == 1:
                msg = "🏆 You're #1! Defend your crown!"
            elif gap > 0:
                msg = f"You're #{rank} — only {gap} XP behind #{rank - 1}! Keep going!"
            else:
                msg = f"You're #{rank}! Keep studying to climb higher."

            return {
                "rank":               rank,
                "total_xp":           total_xp,
                "xp_gap_to_next":     gap,
                "motivation_message": msg,
                "merit_tier":         _get_merit_tier_from_rank(rank),
                "found":              True,
            }

    return {"found": False, "rank": None, "merit_tier": None, "motivation_message": "Start practicing to appear on the leaderboard!"}


def _get_merit_tier_from_rank(rank: int) -> Optional[str]:
    """Determine merit tier from rank."""
    if rank <= 10:  return "legend"
    if rank <= 50:  return "mentor"
    if rank <= 100: return "scholar"
    return None


async def get_merit_tier(student_id: str, scope: str = "school", scope_value: Optional[str] = None, grade: Optional[int] = None) -> Optional[str]:
    """Return a student's merit tier string or None."""
    result = await get_my_rank(student_id=student_id, scope=scope, scope_value=scope_value, grade=grade)
    return result.get("merit_tier")


async def get_hall_of_fame(grade: Optional[int] = None, limit: int = 10) -> List[dict]:
    """Return all-time Top 10 students per grade (permanent Hall of Fame)."""
    query = {}
    if grade:
        query["grade"] = grade
    cursor = leaderboard_col.find(query).sort("total_xp", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    for i, row in enumerate(rows):
        row.pop("_id", None)
        row["rank"] = i + 1
        row["merit_tier"] = _get_merit_tier_from_rank(i + 1)
    return rows
