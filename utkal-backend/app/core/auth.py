import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional

from fastapi import Header, HTTPException

AUTH_SECRET = os.environ.get("UTKAL_AUTH_SECRET", "utkal-dev-secret-change-me")
TOKEN_TTL_SECONDS = int(os.environ.get("UTKAL_TOKEN_TTL_SECONDS", 60 * 60 * 24 * 7))
TEACHER_PASSWORD = os.environ.get("UTKAL_TEACHER_PASSWORD", "teacher123")


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return base64.b64encode(salt + dk).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        raw = base64.b64decode(stored_hash.encode("utf-8"))
        salt, dk = raw[:16], raw[16:]
        check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
        return hmac.compare_digest(dk, check)
    except Exception:
        return False


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf8").rstrip("=")


def _b64_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("utf8"))


def verify_teacher_password(password: str) -> bool:
    return password == TEACHER_PASSWORD


def create_token(payload: Dict) -> str:
    now = int(time.time())
    payload_out = {
        **payload,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    body = _b64_encode(json.dumps(payload_out, separators=(",", ":")).encode("utf8"))
    sig = hmac.new(AUTH_SECRET.encode("utf8"), body.encode("utf8"), hashlib.sha256).digest()
    return f"{body}.{_b64_encode(sig)}"


def decode_token(token: str) -> Dict:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    expected = hmac.new(AUTH_SECRET.encode("utf8"), body.encode("utf8"), hashlib.sha256).digest()
    supplied = _b64_decode(sig)
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    try:
        payload = json.loads(_b64_decode(body).decode("utf8"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")
    return payload


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    token = authorization.split(" ", 1)[1].strip()
    return decode_token(token)
