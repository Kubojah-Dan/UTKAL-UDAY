"""
Admin API endpoints — teacher-only actions.
  POST /admin/generate-batch   - trigger nightly batch generation manually
  GET  /admin/question-stats   - question count per grade/subject
"""
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from typing import Optional

from app.core.auth import get_current_user

router  = APIRouter()
logger  = logging.getLogger("admin")


def _require_teacher(user: dict):
    if user.get("role") not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher role required")


@router.post("/admin/generate-batch")
async def generate_batch(
    background_tasks: BackgroundTasks,
    grade: Optional[int] = None,
    subject: Optional[str] = None,
    count: int = 50,
    user=Depends(get_current_user),
):
    """
    Trigger nightly batch question generation.
    Runs in background so the HTTP response is immediate.
    """
    _require_teacher(user)

    grades   = [grade]   if grade   else None
    subjects = [subject] if subject else None

    async def _run():
        from scripts.nightly_batch_generate import run_batch
        summary = await run_batch(grades=grades, subjects=subjects, count_per=count)
        logger.info(f"Batch generation complete: {summary}")

    background_tasks.add_task(_run)

    return {
        "status": "started",
        "message": f"Batch generation started in background for "
                   f"grade={'all' if not grade else grade}, "
                   f"subject={'all' if not subject else subject}, "
                   f"count_per={count}",
    }


@router.get("/admin/question-stats")
async def question_stats(user=Depends(get_current_user)):
    """Return question counts per grade and subject from MongoDB."""
    _require_teacher(user)

    try:
        from app.core.database import questions_collection

        pipeline = [
            {"$match": {"approved": True, "status": "active"}},
            {"$group": {
                "_id": {"grade": "$grade", "subject": "$subject"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id.grade": 1, "_id.subject": 1}},
        ]
        cursor = questions_collection.aggregate(pipeline)
        rows = await cursor.to_list(length=1000)
        stats = [
            {
                "grade":   r["_id"].get("grade"),
                "subject": r["_id"].get("subject"),
                "count":   r["count"],
            }
            for r in rows
        ]
        total = sum(r["count"] for r in stats)
        return {"total": total, "breakdown": stats}

    except Exception as e:
        logger.error(f"Question stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch question stats")
