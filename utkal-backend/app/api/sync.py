import datetime
import json
import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.auth import decode_token
from app.core.distill import compute_bkt_updates
from app.core.interaction_store import append_interactions
from app.core.question_bank import get_question_by_id
from app.schemas.models import SyncPayload

router = APIRouter()
logger = logging.getLogger("sync")
logging.basicConfig(level=logging.INFO)

API_KEY = os.environ.get("UTKAL_SYNC_KEY", "dev-key-please-change")
RATE_LIMIT = int(os.environ.get("UTKAL_RATE_LIMIT", 60))
RATE_WINDOW = int(os.environ.get("UTKAL_RATE_WINDOW", 60))
_rate_store = defaultdict(lambda: deque())

MAP_FILE = Path(__file__).resolve().parents[1] / "models" / "quest2skill.json"
_quest_map_cache = None


def _load_quest_map():
    global _quest_map_cache
    if _quest_map_cache is not None:
        return _quest_map_cache
    if MAP_FILE.exists():
        try:
            _quest_map_cache = json.loads(MAP_FILE.read_text(encoding="utf8"))
        except Exception:
            _quest_map_cache = {}
    else:
        _quest_map_cache = {}
    return _quest_map_cache


def _check_rate(ip: str) -> bool:
    now = time.time()
    dq = _rate_store[ip]
    while dq and dq[0] < now - RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT:
        return False
    dq.append(now)
    return True


def _authenticate(x_api_key: Optional[str], authorization: Optional[str]) -> dict:
    if x_api_key and x_api_key == API_KEY:
        return {"user_id": "service-sync", "role": "service"}

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        return decode_token(token)

    raise HTTPException(status_code=401, detail="Missing valid API key or bearer token")


def _enrich_interaction(it, user):
    quest_map = _load_quest_map()

    skill_id = it.skill_id
    if not skill_id:
        mapped = quest_map.get(str(it.quest_id)) or {}
        skill_id = str(mapped.get("skill_id") or mapped.get("skill_str") or "")

    subject = it.subject
    grade = it.grade
    school = (it.school or "").strip() or (user.get("school") or "")
    class_grade = it.class_grade if it.class_grade is not None else user.get("class_grade")
    question = get_question_by_id(str(it.problem_id or it.quest_id))
    if question:
        subject = subject or question.get("subject")
        grade = grade if grade is not None else question.get("grade")

    class InteractionObj:
        def __init__(self):
            self.interaction_id = it.interaction_id
            self.quest_id = str(it.quest_id)
            self.problem_id = str(it.problem_id or it.quest_id)
            self.timestamp = int(it.timestamp)
            self.outcome = bool(it.outcome)
            self.time_ms = int(it.time_ms or 0)
            self.hints = int(it.hints or 0)
            self.path_steps = int(it.path_steps or 0)
            self.skill_id = str(skill_id or "")
            self.skill = self.skill_id
            self.subject = subject
            self.grade = grade
            self.school = school
            self.class_grade = int(class_grade) if class_grade is not None else None
            self.xp_awarded = int(it.xp_awarded or 0)

    return InteractionObj()


@router.post("/sync")
async def sync(
    request: Request,
    payload: SyncPayload,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    user = _authenticate(x_api_key, authorization)

    client_ip = request.client.host or "unknown"
    if not _check_rate(client_ip):
        logger.warning("Rate limit exceeded for %s", client_ip)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    student_id = payload.student_id
    if user.get("role") == "student":
        student_id = str(user.get("user_id"))

    interactions = [_enrich_interaction(it, user) for it in payload.interactions]

    try:
        append_interactions(student_id, interactions)
    except Exception as e:
        logger.exception("Failed to persist interactions: %s", e)

    try:
        bkt_updates = compute_bkt_updates(interactions, student_id=student_id)
    except Exception as e:
        logger.exception("Error computing BKT updates: %s", e)
        bkt_updates = {}

    return {
        "status": "ok",
        "accepted": len(interactions),
        "student_id": student_id,
        "bkt_params": bkt_updates,
        "server_time": datetime.datetime.utcnow().isoformat(),
    }

@router.post("/sync/interactions")
async def sync_interactions(
    request: Request,
    payload: dict,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    """Simplified endpoint for direct interaction sync"""
    user = _authenticate(x_api_key, authorization)
    
    client_ip = request.client.host or "unknown"
    if not _check_rate(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    student_id = payload.get("student_id")
    interactions_data = payload.get("interactions", [])
    
    if not student_id or not interactions_data:
        raise HTTPException(status_code=400, detail="Missing student_id or interactions")
    
    # Convert dict to interaction objects
    class InteractionItem:
        def __init__(self, data):
            for k, v in data.items():
                setattr(self, k, v)
    
    interaction_objs = [InteractionItem(it) for it in interactions_data]
    enriched = [_enrich_interaction(it, user) for it in interaction_objs]
    
    try:
        append_interactions(student_id, enriched)
    except Exception as e:
        logger.exception("Failed to persist interactions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save interactions")
    
    return {
        "status": "ok",
        "accepted": len(enriched),
        "student_id": student_id
    }
