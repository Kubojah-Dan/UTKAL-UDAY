import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from app.core.generated_question_bank import (
    SUBJECTS,
    generate_procedural_questions,
    get_generated_question_by_id,
    normalize_subject,
)
from app.core.xes_question_bank import get_xes_question_by_id, get_xes_questions

BASE_DIR = Path(__file__).resolve().parents[1]
QUESTION_BANK_FILE = BASE_DIR / "content" / "question_bank.json"


@lru_cache(maxsize=1)
def _load_bank() -> Dict:
    if not QUESTION_BANK_FILE.exists():
        return {"version": None, "questions": []}
    return json.loads(QUESTION_BANK_FILE.read_text(encoding="utf8"))


def refresh_question_bank_cache() -> None:
    _load_bank.cache_clear()
    _load_static_questions.cache_clear()
    _static_index.cache_clear()


def _matches_subject(question: Dict, subject: Optional[str]) -> bool:
    if subject is None:
        return True
    return str(question.get("subject", "")).strip().lower() == subject.lower()


def _matches_grade(question: Dict, grade: Optional[int]) -> bool:
    if grade is None:
        return True
    try:
        return int(question.get("grade", -1)) == int(grade)
    except (TypeError, ValueError):
        return False


@lru_cache(maxsize=1)
def _load_static_questions() -> List[Dict]:
    bank = _load_bank()
    questions = bank.get("questions", [])
    return questions if isinstance(questions, list) else []


@lru_cache(maxsize=1)
def _static_index() -> Dict[str, Dict]:
    return {str(q.get("id")): q for q in _load_static_questions() if q.get("id") is not None}


def _collect_base_questions(subject: Optional[str], grade: Optional[int]) -> List[Dict]:
    canonical_subject = normalize_subject(subject) if subject else None

    static_questions = [
        q for q in _load_static_questions() if _matches_subject(q, canonical_subject) and _matches_grade(q, grade)
    ]

    include_xes = canonical_subject in (None, "Mathematics")
    xes_questions = []
    if include_xes:
        xes_questions = [q for q in get_xes_questions() if _matches_grade(q, grade)]

    return static_questions + xes_questions


def get_questions(
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    include_generated: bool = True,
) -> List[Dict]:
    safe_offset = max(0, int(offset or 0))
    canonical_subject = normalize_subject(subject) if subject else None
    base = _collect_base_questions(canonical_subject, grade)

    if limit is None:
        static_slice = base[safe_offset:]
        if not include_generated:
            return static_slice
        generated_offset = max(0, safe_offset - len(base))
        generated = generate_procedural_questions(
            subject=canonical_subject,
            grade=grade,
            offset=generated_offset,
            limit=400,
        )
        return static_slice + generated

    safe_limit = max(0, int(limit or 0))
    if safe_limit == 0:
        return []

    static_slice = base[safe_offset : safe_offset + safe_limit]
    remaining = safe_limit - len(static_slice)
    if remaining <= 0 or not include_generated:
        return static_slice

    generated_offset = max(0, safe_offset - len(base))
    generated = generate_procedural_questions(
        subject=canonical_subject,
        grade=grade,
        offset=generated_offset,
        limit=remaining,
    )
    return static_slice + generated


def get_question_by_id(question_id: str) -> Optional[Dict]:
    key = str(question_id or "").strip()
    if not key:
        return None

    static_q = _static_index().get(key)
    if static_q:
        return static_q

    xes_q = get_xes_question_by_id(key)
    if xes_q:
        return xes_q

    gen_q = get_generated_question_by_id(key)
    if gen_q:
        return gen_q

    return None


def list_subjects() -> List[str]:
    static_subjects = {str(q.get("subject", "")) for q in _load_static_questions() if q.get("subject")}
    static_subjects.update(SUBJECTS)
    static_subjects.add("Mathematics")  # Explicitly include XES subject.
    return sorted(static_subjects)
