from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import create_token, get_current_user, verify_teacher_password

router = APIRouter()


class LoginRequest(BaseModel):
    role: Literal["student", "teacher"]
    name: str = Field(min_length=2, max_length=60)
    student_id: Optional[str] = None
    password: Optional[str] = None


@router.post("/auth/login")
def login(payload: LoginRequest):
    role = payload.role
    user_id = payload.student_id or payload.name.strip().lower().replace(" ", "-")

    if role == "teacher":
        if not verify_teacher_password(payload.password or ""):
            raise HTTPException(status_code=401, detail="Invalid teacher credentials")
        user_id = f"teacher-{user_id}"

    token = create_token(
        {
            "user_id": user_id,
            "role": role,
            "name": payload.name.strip(),
        }
    )
    return {
        "token": token,
        "user": {"id": user_id, "name": payload.name.strip(), "role": role},
    }


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    return {"user": {"id": user.get("user_id"), "name": user.get("name"), "role": user.get("role")}}
