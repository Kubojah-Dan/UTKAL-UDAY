import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
QUESTION_BANK_FILE = BASE_DIR / "content" / "question_bank.json"


@lru_cache(maxsize=1)
def _load_bank() -> Dict:
    if not QUESTION_BANK_FILE.exists():
        return {"version": None, "questions": []}
    return json.loads(QUESTION_BANK_FILE.read_text(encoding="utf8"))


def refresh_question_bank_cache() -> None:
    _load_bank.cache_clear()


def get_questions(subject: Optional[str] = None, grade: Optional[int] = None) -> List[Dict]:
    bank = _load_bank()
    questions = bank.get("questions", [])
    if subject:
        subject_key = subject.strip().lower()
        questions = [q for q in questions if str(q.get("subject", "")).lower() == subject_key]
    if grade is not None:
        questions = [q for q in questions if int(q.get("grade", -1)) == int(grade)]
    return questions


def get_question_by_id(question_id: str) -> Optional[Dict]:
    for q in _load_bank().get("questions", []):
        if str(q.get("id")) == str(question_id):
            return q
    return None


def list_subjects() -> List[str]:
    subjects = sorted({str(q.get("subject", "")) for q in _load_bank().get("questions", []) if q.get("subject")})
    return subjects
