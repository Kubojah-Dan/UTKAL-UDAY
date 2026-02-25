import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
STORE_FILE = BASE_DIR / "data" / "interactions.jsonl"


def append_interactions(student_id: str, interactions: Iterable) -> None:
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STORE_FILE.open("a", encoding="utf8") as f:
        for it in interactions:
            payload = {
                "interaction_id": getattr(it, "interaction_id", None),
                "student_id": student_id,
                "quest_id": str(getattr(it, "quest_id", "")),
                "problem_id": str(getattr(it, "problem_id", "") or ""),
                "skill_id": str(getattr(it, "skill_id", "") or ""),
                "timestamp": int(getattr(it, "timestamp", 0) or 0),
                "outcome": bool(getattr(it, "outcome", False)),
                "time_ms": int(getattr(it, "time_ms", 0) or 0),
                "hints": int(getattr(it, "hints", 0) or 0),
                "path_steps": int(getattr(it, "path_steps", 0) or 0),
                "subject": str(getattr(it, "subject", "") or ""),
                "grade": getattr(it, "grade", None),
                "school": str(getattr(it, "school", "") or ""),
                "class_grade": getattr(it, "class_grade", None),
                "xp_awarded": int(getattr(it, "xp_awarded", 0) or 0),
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_interactions(student_id: Optional[str] = None, limit: int = 5000) -> List[Dict]:
    if not STORE_FILE.exists():
        return []

    with STORE_FILE.open("r", encoding="utf8") as f:
        lines = [line.strip() for line in f if line.strip()]

    records = []
    seen = set()
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue

        if student_id and str(row.get("student_id")) != str(student_id):
            continue

        interaction_id = row.get("interaction_id")
        dedupe_key = interaction_id or (
            row.get("student_id"),
            row.get("quest_id"),
            row.get("timestamp"),
            row.get("outcome"),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        records.append(row)
        if len(records) >= limit:
            break

    records.reverse()
    return records
