"""
Leaderboard API — 4-scope tiered leaderboard with motivational rank gaps.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user
from app.core.leaderboard_service import (
    get_leaderboard, get_my_rank, get_hall_of_fame
)

router = APIRouter()
logger = logging.getLogger("leaderboard")


@router.get("/leaderboard")
async def leaderboard(
    scope:       str           = Query("school", description="class|school|district|state"),
    scope_value: Optional[str] = Query(None, description="School name / district name"),
    grade:       Optional[int] = Query(None, ge=1, le=12),
    limit:       int           = Query(50, ge=5, le=200),
    user=Depends(get_current_user),
):
    """
    Get ranked leaderboard for a scope.
    Each row includes: rank, total_xp, xp_gap_to_next, merit_tier.
    """
    # Default scope_value to user's school if not specified
    if not scope_value and scope in ("school", "class"):
        scope_value = user.get("school") or None

    rows = await get_leaderboard(
        scope=scope,
        scope_value=scope_value,
        grade=grade,
        limit=limit,
    )

    return {
        "scope":       scope,
        "scope_value": scope_value,
        "grade":       grade,
        "count":       len(rows),
        "rows":        rows,
    }


@router.get("/leaderboard/my-rank")
async def my_rank(
    scope:       str           = Query("school"),
    scope_value: Optional[str] = Query(None),
    grade:       Optional[int] = Query(None, ge=1, le=12),
    user=Depends(get_current_user),
):
    """Return the authenticated student's personal rank + motivational gap message."""
    student_id = str(user.get("user_id") or user.get("id") or "")

    if not scope_value and scope in ("school", "class"):
        scope_value = user.get("school") or None

    result = await get_my_rank(
        student_id=student_id,
        scope=scope,
        scope_value=scope_value,
        grade=grade or user.get("class_grade"),
    )
    return result


@router.get("/leaderboard/hall-of-fame")
async def hall_of_fame(
    grade: Optional[int] = Query(None, ge=1, le=12),
    limit: int           = Query(10, ge=3, le=20),
    user=Depends(get_current_user),
):
    """Return the all-time Top 10 Hall of Fame per grade."""
    rows = await get_hall_of_fame(grade=grade, limit=limit)
    return {"grade": grade, "hall_of_fame": rows}
