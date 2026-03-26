from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr

from app.core.auth import create_token, get_current_user, verify_teacher_password, hash_password, verify_password
from app.core.database import async_db

router = APIRouter()
users_col = async_db["users"]


class RegisterRequest(BaseModel):
    role: Literal["student", "teacher"]
    name: str = Field(min_length=2, max_length=60)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)
    school: str = Field(min_length=2, max_length=120)
    class_grade: int = Field(ge=1, le=12)
    student_id: Optional[str] = None
    teacher_code: Optional[str] = None  # secret code for teacher registration


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
async def register(payload: RegisterRequest):
    email = payload.email.strip().lower()

    # Check duplicate email
    existing = await users_col.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    # Teacher registration requires the teacher code
    if payload.role == "teacher":
        if not verify_teacher_password(payload.teacher_code or ""):
            raise HTTPException(status_code=401, detail="Invalid teacher registration code")

    # Build user_id: use student_id if provided, else derive from email
    user_id = payload.student_id or email.split("@")[0].replace(".", "-")
    if payload.role == "teacher":
        user_id = f"teacher-{user_id}"

    user_doc = {
        "user_id": user_id,
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "name": payload.name.strip(),
        "school": payload.school.strip(),
        "class_grade": payload.class_grade,
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    }
    await users_col.insert_one(user_doc)

    token = create_token({
        "user_id": user_id,
        "role": payload.role,
        "name": payload.name.strip(),
        "school": payload.school.strip(),
        "class_grade": payload.class_grade,
    })
    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": payload.name.strip(),
            "role": payload.role,
            "school": payload.school.strip(),
            "class_grade": payload.class_grade,
        },
    }


@router.post("/auth/login")
async def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    user_doc = await users_col.find_one({"email": email})

    if not user_doc or not verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = user_doc["user_id"]
    token = create_token({
        "user_id": user_id,
        "role": user_doc["role"],
        "name": user_doc["name"],
        "school": user_doc["school"],
        "class_grade": user_doc["class_grade"],
    })
    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": user_doc["name"],
            "role": user_doc["role"],
            "school": user_doc["school"],
            "class_grade": user_doc["class_grade"],
        },
    }


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    return {
        "user": {
            "id": user.get("user_id"),
            "name": user.get("name"),
            "role": user.get("role"),
            "school": user.get("school"),
            "class_grade": user.get("class_grade"),
        }
    }
