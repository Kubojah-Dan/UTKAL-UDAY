import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from app.core.auth import get_current_user
from app.core.database import questions_collection, student_attempts_collection
import random

from app.core.question_bank import get_question_by_id, get_questions, list_subjects
from app.core.xes_question_bank import get_xes_dataset_summary

router = APIRouter()

BASE = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE / "models"
QUEST_MAP_FILE = MODELS_DIR / "quest2skill.json"
SKILL_REGISTRY_FILE = MODELS_DIR / "skill_registry.json"
LSTM_FILE = MODELS_DIR / "temporal_lstm.pt"
DKT_XES_FILE = MODELS_DIR / "dkt_xes3g5m.pt"
DKT_XES_META_FILE = MODELS_DIR / "dkt_xes3g5m_meta.json"
BKT_XES_FILE = MODELS_DIR / "bkt_params_xes3g5m.json"


@lru_cache(maxsize=1)
def _load_quest_map():
    if not QUEST_MAP_FILE.exists():
        return {}
    return json.loads(QUEST_MAP_FILE.read_text(encoding="utf8"))


@lru_cache(maxsize=1)
def _load_bkt():
    primary = MODELS_DIR / "bkt_params_xes3g5m.json"
    fallback = MODELS_DIR / "bkt_params.json"
    f = primary if primary.exists() else fallback
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf8"))


@lru_cache(maxsize=1)
def _load_skill_registry():
    if not SKILL_REGISTRY_FILE.exists():
        return {}
    return json.loads(SKILL_REGISTRY_FILE.read_text(encoding="utf8"))


@router.get("/quest2skill")
def get_quest2skill(
    quest_id: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000),
    include_all: bool = False,
):
    data = _load_quest_map()
    if not data:
        raise HTTPException(status_code=404, detail="quest2skill not available")

    if quest_id is not None:
        item = data.get(str(quest_id))
        if item is None:
            raise HTTPException(status_code=404, detail="quest mapping not found")
        return item

    if include_all:
        return data

    keys = list(data.keys())[:limit]
    return {k: data[k] for k in keys}


@router.get("/bkt/latest")
def get_bkt_latest():
    data = _load_bkt()
    if not data:
        raise HTTPException(status_code=404, detail="bkt params not available")
    return data


@router.get("/subjects")
def subjects():
    return {"subjects": list_subjects()}


@router.get("/questions")
async def questions(
    subject: Optional[str] = None,
    grade: Optional[int] = Query(None, ge=1, le=12),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    include_generated: bool = Query(True),
):
    """Get questions including teacher-generated ones from MongoDB"""
    try:
        # Get teacher-generated questions from MongoDB
        query = {"approved": True, "status": "active"}
        if subject:
            query["subject"] = subject
        if grade:
            query["grade"] = grade
        
        cursor = questions_collection.find(query).limit(limit)
        mongo_questions = await cursor.to_list(length=limit)
        
        # Remove MongoDB _id
        for q in mongo_questions:
            q.pop("_id", None)
        
        # Get base questions from question bank
        base_questions = get_questions(
            subject=subject,
            grade=grade,
            limit=max(0, limit - len(mongo_questions)),
            offset=offset,
            include_generated=include_generated,
        )
        
        # Combine both sources
        all_questions = mongo_questions + base_questions
        
        return {
            "questions": all_questions[:limit],
            "count": len(all_questions),
            "offset": offset,
            "limit": limit,
            "mongo_count": len(mongo_questions),
            "base_count": len(base_questions),
        }
    except Exception as e:
        # Fallback to base questions only
        items = get_questions(
            subject=subject,
            grade=grade,
            limit=limit,
            offset=offset,
            include_generated=include_generated,
        )
        return {
            "questions": items,
            "count": len(items),
            "offset": offset,
            "limit": limit,
        }


@router.get("/questions/{question_id}")
async def question_by_id(question_id: str):
    """Get question by ID from MongoDB or question bank"""
    try:
        # Try MongoDB first
        mongo_q = await questions_collection.find_one({"id": question_id, "approved": True})
        if mongo_q:
            mongo_q.pop("_id", None)
            # Debug: Log if translations exist
            has_translations = bool(mongo_q.get("language_variants"))
            print(f"Question {question_id}: has_translations={has_translations}")
            if has_translations:
                print(f"  Languages: {list(mongo_q['language_variants'].keys())}")
            return mongo_q
    except Exception as e:
        print(f"Error fetching from MongoDB: {e}")
    
    # Fallback to question bank
    q = get_question_by_id(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="question not found")
    return q


@router.get("/datasets/xes3g5m/inspect")
def inspect_xes_dataset():
    summary = get_xes_dataset_summary()
    if not summary.get("present"):
        return summary

    sample = get_question_by_id("XES-2") or get_question_by_id("XES-1")
    return {"summary": summary, "sample_question": sample}


def _estimate_subject_readiness() -> dict:
    skill_registry = _load_skill_registry()
    all_skill_names = " ".join(skill_registry.keys()).lower()

    math_keywords = ["algebra", "fraction", "geometry", "addition", "subtraction", "decimal", "equation"]
    science_keywords = ["physics", "chemistry", "biology", "plant", "animal", "electricity", "matter"]

    math_hits = sum(1 for k in math_keywords if k in all_skill_names)
    science_hits = sum(1 for k in science_keywords if k in all_skill_names)

    return {
        "math_keyword_hits": math_hits,
        "science_keyword_hits": science_hits,
        "math_ready": math_hits >= 3,
        "science_ready": science_hits >= 2,
    }


@router.get("/models/readiness")
def model_readiness():
    bkt = _load_bkt()
    subjects_in_bank = list_subjects()
    readiness = _estimate_subject_readiness()

    model_files = [f.name for f in MODELS_DIR.glob("*") if f.is_file()]
    xes_like_files = [name for name in model_files if "xes" in name.lower() or "dkt" in name.lower() or "sakt" in name.lower()]

    status = "pilot_ready_math_only"
    has_any_temporal = LSTM_FILE.exists() or DKT_XES_FILE.exists()
    has_any_bkt = bool(bkt) or BKT_XES_FILE.exists()
    if not has_any_bkt or not has_any_temporal:
        status = "not_ready"
    elif DKT_XES_FILE.exists() and BKT_XES_FILE.exists() and readiness["science_ready"]:
        status = "production_candidate"
    elif DKT_XES_FILE.exists() and BKT_XES_FILE.exists():
        status = "production_candidate_math_core"
    elif xes_like_files:
        status = "improving_with_xes"

    recommendations = []
    if not readiness["science_ready"]:
        recommendations.append("Current training is weak for Science; add XES3G5M + science-aligned data.")
    if "Science" in subjects_in_bank and not xes_like_files:
        recommendations.append("Model artifacts show ASSISTments-style math bias; add your XES3G5M trained model.")
    if not DKT_XES_FILE.exists():
        recommendations.append("Train and export dkt_xes3g5m.pt for sequence-aware mastery tracking.")
    if not BKT_XES_FILE.exists():
        recommendations.append("Train and export bkt_params_xes3g5m.json for calibrated per-skill tracing.")
    recommendations.append("Calibrate BKT per new curriculum skills before live student rollout.")

    return {
        "status": status,
        "bkt_skill_count": len(bkt),
        "has_temporal_lstm": LSTM_FILE.exists(),
        "has_dkt_xes": DKT_XES_FILE.exists(),
        "has_dkt_xes_meta": DKT_XES_META_FILE.exists(),
        "has_bkt_xes": BKT_XES_FILE.exists(),
        "model_files": model_files,
        "detected_xes_or_sakt_files": xes_like_files,
        "subject_readiness": readiness,
        "question_bank_subjects": subjects_in_bank,
        "recommendations": recommendations,
    }

@router.get("/questions/next")
async def get_next_question(
    grade: int = Query(..., ge=1, le=12),
    subject: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get next question for student with rotation (avoid repeats)"""
    try:
        student_id = user.get("id")
        
        # Get questions student has already attempted
        attempted_cursor = student_attempts_collection.find(
            {"student_id": student_id},
            {"question_id": 1}
        )
        attempted_ids = [doc["question_id"] async for doc in attempted_cursor]
        
        # Query for questions not yet attempted
        query = {
            "grade": grade,
            "approved": True,
            "status": "active",
            "id": {"$nin": attempted_ids}
        }
        
        if subject:
            query["subject"] = subject
        
        # Get available questions
        cursor = questions_collection.find(query).limit(50)
        available = await cursor.to_list(length=50)
        
        # If no unattempted questions, allow repeats
        if not available:
            query.pop("id")
            cursor = questions_collection.find(query).limit(50)
            available = await cursor.to_list(length=50)
        
        if not available:
            # Fallback to generated questions
            from app.core.question_bank import get_questions
            fallback = get_questions(subject=subject, grade=grade, limit=1)
            if fallback:
                return fallback[0]
            raise HTTPException(status_code=404, detail="No questions available")
        
        # Random selection
        question = random.choice(available)
        question.pop("_id", None)
        
        return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch question: {str(e)}")
