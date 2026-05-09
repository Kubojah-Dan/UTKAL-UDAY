"""
Notes API — study cards and formula sheets.
  GET /notes                        — paginated study cards by grade/subject/chapter
  GET /notes/formula-sheet/{subject}/{grade} — pre-built formula reference sheet
  GET /notes/chapters/{subject}/{grade}     — list of available chapters
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.core.study_cards import get_study_cards, get_formula_sheet

router = APIRouter()
logger = logging.getLogger("notes")


@router.get("/notes")
async def list_study_cards(
    subject:  Optional[str] = Query(None),
    grade:    Optional[int] = Query(None, ge=1, le=12),
    chapter:  Optional[str] = Query(None),
    limit:    int           = Query(100, ge=1, le=500),
    user=Depends(get_current_user),
):
    """
    Return study concept cards filtered by subject, grade, chapter.
    Works offline once cached to IndexedDB on the frontend.
    """
    cards = await get_study_cards(subject=subject, grade=grade, chapter=chapter, limit=limit)
    return {
        "cards":  cards,
        "count":  len(cards),
        "filters": {"subject": subject, "grade": grade, "chapter": chapter},
    }


@router.get("/notes/formula-sheet/{subject}/{grade}")
async def formula_sheet(
    subject: str,
    grade: int,
    user=Depends(get_current_user),
):
    """
    Return the formula reference sheet for a subject/grade.
    These are static and available offline immediately.
    """
    formulas = get_formula_sheet(subject, grade)
    if not formulas:
        # Try with lowercase / partial match
        subject_map = {
            "math": "Mathematics", "mathematics": "Mathematics",
            "physics": "Physics", "chemistry": "Chemistry",
        }
        norm = subject_map.get(subject.lower(), subject)
        formulas = get_formula_sheet(norm, grade)

    return {
        "subject":  subject,
        "grade":    grade,
        "formulas": formulas,
        "count":    len(formulas),
    }


@router.get("/notes/chapters/{subject}/{grade}")
async def list_chapters(
    subject: str,
    grade: int,
    user=Depends(get_current_user),
):
    """Return distinct chapter names available for a subject/grade."""
    try:
        from app.core.database import async_db
        col = async_db["study_cards"]
        pipeline = [
            {"$match": {"subject": subject, "grade": grade}},
            {"$group": {"_id": "$chapter"}},
            {"$sort": {"_id": 1}},
        ]
        cursor = col.aggregate(pipeline)
        rows = await cursor.to_list(length=200)
        chapters = [r["_id"] for r in rows if r["_id"]]
        return {"subject": subject, "grade": grade, "chapters": chapters}
    except Exception as e:
        logger.error(f"Chapter list failed: {e}")
        return {"subject": subject, "grade": grade, "chapters": []}


@router.post("/notes/generate")
async def generate_cards_from_text(
    payload: dict,
    user=Depends(get_current_user),
):
    """
    Teacher endpoint: generate study cards from pasted chapter text.
    Body: { subject, grade, chapter, text }
    """
    if user.get("role") not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher role required")

    subject = payload.get("subject", "")
    grade   = int(payload.get("grade", 6))
    chapter = payload.get("chapter", "Chapter 1")
    text    = payload.get("text", "")

    if not text:
        raise HTTPException(status_code=400, detail="Chapter text is required")

    from app.core.study_cards import generate_study_cards_from_text, save_study_cards
    cards = await generate_study_cards_from_text(text, subject, grade, chapter)
    inserted = await save_study_cards(cards)

    return {
        "status":   "ok",
        "generated": len(cards),
        "inserted":  inserted,
        "subject":   subject,
        "grade":     grade,
        "chapter":   chapter,
    }
