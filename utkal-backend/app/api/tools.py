from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import uuid
from pathlib import Path
from app.tools.generate_questions import generate_questions
from app.core.auth import get_current_user
from app.core.document_parser import extract_text_from_file, parse_questions_with_groq, validate_question
from app.core.groq_translator import translate_questions_batch
from app.core.database import (
    async_db,
    notifications_collection,
    questions_collection,
    quizzes_collection,
    student_attempts_collection,
)
from app.tools.svg_generator import (
    generate_svg_shape, generate_svg_fraction, generate_svg_number_line,
    generate_svg_bar_chart, generate_svg_clock, generate_svg_pie_chart,
    generate_svg_ruler, generate_svg_angle, generate_svg_thermometer,
    generate_svg_place_value, generate_svg_venn_diagram, generate_svg_coins,
    generate_svg_shapes_grid, generate_svg_food_chain, generate_svg_plant_parts,
    generate_svg_water_cycle, generate_svg_cell, generate_svg_magnet,
    generate_svg_states_of_matter,
)
from app.tools.content_pack_generator import generate_content_pack, list_content_packs, get_content_pack

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class GenerateRequest(BaseModel):
    topic: str
    grade: int
    subject: str = "Math"
    count: int = 5

class ApproveQuestionsRequest(BaseModel):
    questions: List[dict]
    translate_to: Optional[List[str]] = []

class CreateQuizRequest(BaseModel):
    title: str
    grade: int
    subject: str
    question_ids: List[str]
    duration_minutes: Optional[int] = 30

class CreateAnnouncementRequest(BaseModel):
    title: str
    message: str
    grade: int
    duration_hours: Optional[int] = 24
    action_label: Optional[str] = None
    action_path: Optional[str] = None

class GenerateSVGRequest(BaseModel):
    svg_type: str
    params: dict


users_col = async_db["users"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _iso_in_hours(hours: int) -> str:
    return (_utc_now() + timedelta(hours=max(1, int(hours or 24)))).isoformat()


def _parse_iso(raw: object) -> Optional[datetime]:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_school(value: object) -> str:
    return str(value or "").strip()


def _quiz_expiry(quiz: Dict) -> Optional[datetime]:
    expires_at = _parse_iso(quiz.get("expires_at"))
    if expires_at:
        return expires_at

    created_at = _parse_iso(quiz.get("created_at"))
    if created_at:
        return created_at + timedelta(hours=24)

    return None


def _quiz_is_active(quiz: Dict, now: Optional[datetime] = None) -> bool:
    if str(quiz.get("status") or "").strip().lower() != "active":
        return False
    now = now or _utc_now()
    expiry = _quiz_expiry(quiz)
    if expiry is None:
        return False
    return expiry > now


def _quiz_matches_scope(quiz: Dict, school: str, grade: Optional[int], subject: Optional[str] = None) -> bool:
    quiz_school = _normalize_school(quiz.get("school"))
    quiz_grade = quiz.get("grade")
    quiz_subject = str(quiz.get("subject") or "").strip()

    if school and quiz_school and quiz_school.casefold() != school.casefold():
        return False
    if grade is not None and int(quiz_grade or 0) != int(grade):
        return False
    if subject and quiz_subject and quiz_subject.casefold() != str(subject).strip().casefold():
        return False
    return True


async def _student_attempted_quiz(quiz_id: str, student_id: str) -> bool:
    if not quiz_id or not student_id:
        return False
    record = await student_attempts_collection.find_one({"quiz_id": quiz_id, "student_id": student_id})
    return bool(record)


def _serialize_quiz(quiz: Dict, now: Optional[datetime] = None, attempted: bool = False) -> Dict:
    payload = dict(quiz)
    payload.pop("_id", None)
    now = now or _utc_now()
    expiry = _quiz_expiry(payload)
    remaining_seconds = max(0, int((expiry - now).total_seconds())) if expiry else 0
    payload["created_at"] = payload.get("created_at") or ""
    payload["expires_at"] = expiry.isoformat() if expiry else ""
    payload["attempted"] = attempted
    payload["is_expired"] = not _quiz_is_active(payload, now=now)
    payload["time_remaining_minutes"] = remaining_seconds // 60
    return payload


def _public_document(payload: Dict) -> Dict:
    out = dict(payload)
    out.pop("_id", None)
    return out


async def _active_quizzes_for_student(student_id: str, school: str, grade: Optional[int], subject: Optional[str] = None) -> List[Dict]:
    now = _utc_now()
    cursor = quizzes_collection.find({"status": "active"}).sort("created_at", -1)
    quizzes = await cursor.to_list(length=100)
    visible: List[Dict] = []

    for quiz in quizzes:
        if not _quiz_is_active(quiz, now=now):
            continue
        if not _quiz_matches_scope(quiz, school=school, grade=grade, subject=subject):
            continue
        attempted = await _student_attempted_quiz(str(quiz.get("id") or ""), student_id)
        if attempted:
            continue
        visible.append(_serialize_quiz(quiz, now=now, attempted=False))

    return visible


async def _active_notifications_for_student(school: str, grade: Optional[int]) -> List[Dict]:
    now = _utc_now()
    cursor = notifications_collection.find({"status": "active"}).sort("created_at", -1)
    records = await cursor.to_list(length=50)
    active: List[Dict] = []
    for record in records:
        record.pop("_id", None)
        expires_at = _parse_iso(record.get("expires_at"))
        if not expires_at or expires_at <= now:
            continue
        if school and _normalize_school(record.get("school")).casefold() != school.casefold():
            continue
        if grade is not None and int(record.get("grade") or 0) != int(grade):
            continue
        active.append(record)
    return active

@router.post("/tools/generate-questions")
async def api_generate_questions(req: GenerateRequest):
    try:
        results = generate_questions(
            topic=req.topic,
            grade=req.grade,
            subject=req.subject,
            count=req.count
        )
        if not results:
             raise HTTPException(status_code=500, detail="AI failed to generate results. Check API key and logs.")
        
        return [q.model_dump() for q in results]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@router.post("/tools/upload-document")
async def upload_document(file: UploadFile = File(...), grade: int = Form(...), subject: str = Form(...)):
    """Upload PDF/Word document and extract questions"""
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text
        text = extract_text_from_file(str(file_path))
        
        if not text or len(text) < 50:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from document")
        
        # Parse questions with Groq
        questions = parse_questions_with_groq(
            text=text,
            source_doc=file.filename,
            grade=grade,
            subject=subject,
        )
        for q in questions:
            q["grade"] = grade
            q["subject"] = subject
        
        # Validate questions
        valid_questions = [q for q in questions if validate_question(q)]
        
        # Clean up file
        os.remove(file_path)
        
        return {
            "success": True,
            "total_parsed": len(questions),
            "valid_questions": len(valid_questions),
            "questions": valid_questions
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/tools/approve-questions")
async def approve_questions(req: ApproveQuestionsRequest):
    """Approve and save questions to database with optional translation"""
    try:
        print(f"\n=== APPROVE QUESTIONS ===")
        print(f"Questions to approve: {len(req.questions)}")
        print(f"Languages to translate: {req.translate_to}")
        
        # Batch translate all questions at once if translation requested
        questions = req.questions
        if req.translate_to:
            try:
                questions = translate_questions_batch(questions, req.translate_to)
                print(f"✓ Batch translation complete")
            except Exception as e:
                print(f"Translation error: {e}")
                raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
        
        # Save all questions to MongoDB
        saved_count = 0
        for question in questions:
            question["approved"] = True
            question["status"] = "active"
            
            result = await questions_collection.update_one(
                {"id": question["id"]},
                {"$set": question},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                saved_count += 1
        
        langs_msg = f" with translations to {', '.join(req.translate_to)}" if req.translate_to else ""
        message = f"Successfully saved {saved_count} questions{langs_msg}"
        try:
            from app.core.question_bank import refresh_question_bank_cache

            refresh_question_bank_cache()
        except Exception:
            pass
        
        print(f"\n=== RESULT: {message} ===")
        
        return {
            "success": True,
            "saved_count": saved_count,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save questions: {str(e)}")

@router.post("/tools/create-quiz")
async def create_quiz(req: CreateQuizRequest, user=Depends(get_current_user)):
    """Create a quiz from selected questions"""
    try:
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Teacher role required")

        quiz_id = f"quiz_{req.subject.lower()}_g{req.grade}_{uuid.uuid4().hex[:8]}"
        created_at = _iso_now()
        
        quiz = {
            "id": quiz_id,
            "title": req.title,
            "grade": req.grade,
            "subject": req.subject,
            "question_ids": req.question_ids,
            "duration_minutes": req.duration_minutes,
            "status": "active",
            "school": _normalize_school(user.get("school")),
            "teacher_id": user.get("user_id"),
            "teacher_name": user.get("name"),
            "created_at": created_at,
            "expires_at": _iso_in_hours(24),
        }
        
        await quizzes_collection.insert_one(quiz)
        
        return {"success": True, "quiz_id": quiz_id, "quiz": _public_document(quiz)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quiz: {str(e)}")

@router.get("/tools/questions")
async def get_questions(grade: Optional[int] = None, subject: Optional[str] = None, limit: int = 50):
    """Get questions from database"""
    try:
        query = {"approved": True, "status": "active"}
        if grade:
            query["grade"] = grade
        if subject:
            query["subject"] = subject
        
        cursor = questions_collection.find(query).limit(limit)
        questions = await cursor.to_list(length=limit)
        
        # Remove MongoDB _id field
        for q in questions:
            q.pop("_id", None)
        
        return {"questions": questions, "count": len(questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")

@router.post("/tools/upload-quiz")
async def upload_quiz(
    file: UploadFile = File(...),
    grade: int = Form(...),
    title: str = Form(...),
    duration: int = Form(30),
    user=Depends(get_current_user),
):
    """Upload PDF with quiz questions and create quiz"""
    try:
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Teacher role required")

        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        text = extract_text_from_file(str(file_path))
        if not text or len(text) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text")
        
        questions = parse_questions_with_groq(
            text=text,
            source_doc=file.filename,
            grade=grade,
            subject=None,
        )
        valid_questions = [q for q in questions if validate_question(q)]
        if not valid_questions:
            raise HTTPException(status_code=400, detail="No valid quiz questions were found in the uploaded file")
        
        question_ids = []
        inferred_subject = None
        for q in valid_questions:
            q["approved"] = True
            q["status"] = "active"
            q["grade"] = grade
            await questions_collection.insert_one(q)
            question_ids.append(q["id"])
            if not inferred_subject:
                inferred_subject = q.get("subject")
        
        quiz_id = f"quiz_{grade}_{uuid.uuid4().hex[:8]}"
        created_at = _iso_now()
        quiz = {
            "id": quiz_id,
            "title": title,
            "grade": grade,
            "subject": inferred_subject or "Mixed",
            "question_ids": question_ids,
            "duration_minutes": duration,
            "status": "active",
            "school": _normalize_school(user.get("school")),
            "teacher_id": user.get("user_id"),
            "teacher_name": user.get("name"),
            "created_at": created_at,
            "expires_at": _iso_in_hours(24),
        }
        await quizzes_collection.insert_one(quiz)
        try:
            from app.core.question_bank import refresh_question_bank_cache

            refresh_question_bank_cache()
        except Exception:
            pass
        
        os.remove(file_path)
        
        return {
            "success": True,
            "quiz_id": quiz_id,
            "question_count": len(question_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/notifications/announcement")
async def create_announcement(req: CreateAnnouncementRequest, user=Depends(get_current_user)):
    """Teacher announcement for students in the same school and grade."""
    try:
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Teacher role required")

        notification_id = f"notice_{uuid.uuid4().hex[:10]}"
        payload = {
            "id": notification_id,
            "kind": "announcement",
            "title": req.title.strip(),
            "message": req.message.strip(),
            "grade": int(req.grade),
            "school": _normalize_school(user.get("school")),
            "status": "active",
            "created_at": _iso_now(),
            "expires_at": _iso_in_hours(req.duration_hours or 24),
            "created_by": user.get("user_id"),
            "created_by_name": user.get("name"),
            "action_label": (req.action_label or "").strip() or None,
            "action_path": (req.action_path or "").strip() or None,
        }

        await notifications_collection.insert_one(payload)
        return {"success": True, "notification": _public_document(payload)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/notifications")
async def get_notifications(student_id: Optional[str] = None, grade: Optional[int] = None, user=Depends(get_current_user)):
    """Get active quiz and teacher notifications for the signed-in student."""
    try:
        if user.get("role") != "student":
            return {"notifications": []}

        resolved_student_id = str(user.get("user_id") or student_id or "").strip()
        resolved_grade = int(user.get("class_grade") or grade or 0) or None
        resolved_school = _normalize_school(user.get("school"))

        quizzes = await _active_quizzes_for_student(
            student_id=resolved_student_id,
            school=resolved_school,
            grade=resolved_grade,
        )
        announcements = await _active_notifications_for_student(
            school=resolved_school,
            grade=resolved_grade,
        )

        notifications: List[Dict] = []
        for quiz in quizzes[:5]:
            notifications.append(
                {
                    "id": f"quiz:{quiz['id']}",
                    "kind": "quiz",
                    "title": f"New Quiz: {quiz['title']}",
                    "message": f"Grade {quiz['grade']} - {quiz['duration_minutes']} minutes",
                    "quiz_id": quiz["id"],
                    "action_label": "Start Quiz",
                    "action_path": f"/quiz/{quiz['id']}",
                    "created_at": quiz.get("created_at"),
                    "expires_at": quiz.get("expires_at"),
                }
            )

        for announcement in announcements[:5]:
            notifications.append(
                {
                    "id": announcement["id"],
                    "kind": announcement.get("kind") or "announcement",
                    "title": announcement.get("title"),
                    "message": announcement.get("message"),
                    "action_label": announcement.get("action_label"),
                    "action_path": announcement.get("action_path"),
                    "created_at": announcement.get("created_at"),
                    "expires_at": announcement.get("expires_at"),
                }
            )

        notifications.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"notifications": notifications[:8]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/quiz-analytics")
async def get_quiz_analytics(grade: Optional[int] = None, user=Depends(get_current_user)):
    """Quiz analytics plus absentee lists for the teacher's school and selected grade."""
    try:
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Teacher role required")

        teacher_school = _normalize_school(user.get("school"))
        target_grade = int(grade or user.get("class_grade") or 0) or None
        cursor = quizzes_collection.find({"school": teacher_school}).sort("created_at", -1)
        quizzes = await cursor.to_list(length=100)

        analytics: List[Dict] = []
        now = _utc_now()
        for quiz in quizzes:
            if target_grade is not None and int(quiz.get("grade") or 0) != target_grade:
                continue

            attempts = await student_attempts_collection.find({"quiz_id": quiz.get("id")}).to_list(length=500)
            attempt_by_student: Dict[str, Dict] = {}
            for attempt in attempts:
                sid = str(attempt.get("student_id") or "").strip()
                if sid and sid not in attempt_by_student:
                    attempt_by_student[sid] = attempt

            eligible_students_cursor = users_col.find(
                {
                    "role": "student",
                    "school": teacher_school,
                    "class_grade": int(quiz.get("grade") or 0),
                },
                {"user_id": 1, "name": 1, "email": 1},
            )
            eligible_students = await eligible_students_cursor.to_list(length=1000)
            attempted_students = [
                {
                    "student_id": sid,
                    "name": attempt.get("student_name") or sid,
                    "score": round(float(attempt.get("score") or 0), 2),
                    "submitted_at": attempt.get("timestamp") or attempt.get("submitted_at"),
                }
                for sid, attempt in sorted(
                    attempt_by_student.items(),
                    key=lambda item: str(item[1].get("timestamp") or item[1].get("submitted_at") or ""),
                    reverse=True,
                )
            ]

            absent_students = []
            for student in eligible_students:
                student_id_value = str(student.get("user_id") or "").strip()
                if not student_id_value or student_id_value in attempt_by_student:
                    continue
                absent_students.append(
                    {
                        "student_id": student_id_value,
                        "name": student.get("name") or student_id_value,
                        "email": student.get("email") or "",
                    }
                )

            avg_score = 0.0
            if attempt_by_student:
                avg_score = sum(float(a.get("score") or 0) for a in attempt_by_student.values()) / len(attempt_by_student)

            quiz_payload = _serialize_quiz(quiz, now=now, attempted=False)
            analytics.append(
                {
                    "quiz_id": quiz.get("id"),
                    "title": quiz.get("title", "Unknown"),
                    "grade": quiz.get("grade", 0),
                    "subject": quiz.get("subject") or "Mixed",
                    "attempts": len(attempt_by_student),
                    "avg_score": round(avg_score, 2),
                    "last_attempt": attempted_students[0]["submitted_at"] if attempted_students else None,
                    "eligible_count": len(eligible_students),
                    "absent_count": len(absent_students),
                    "is_expired": quiz_payload.get("is_expired"),
                    "expires_at": quiz_payload.get("expires_at"),
                    "attempted_students": attempted_students[:25],
                    "absent_students": absent_students[:50],
                }
            )

        return {"analytics": analytics}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/quizzes")
async def get_quizzes(grade: Optional[int] = None, subject: Optional[str] = None, user=Depends(get_current_user)):
    """Get active quizzes for the signed-in student within the teacher's school and grade scope."""
    try:
        if user.get("role") != "student":
            return {"quizzes": []}

        quizzes = await _active_quizzes_for_student(
            student_id=str(user.get("user_id") or "").strip(),
            school=_normalize_school(user.get("school")),
            grade=int(user.get("class_grade") or grade or 0) or None,
            subject=subject,
        )
        return {"quizzes": quizzes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quizzes: {str(e)}")

@router.post("/tools/generate-svg")
async def generate_svg(req: GenerateSVGRequest):
    """Generate SVG image for visual questions"""
    try:
        svg_type = req.svg_type.lower()
        params = req.params or {}

        # Accept full question JSON where SVG config is nested under "svg".
        if isinstance(params.get("svg"), dict):
            svg_block = params.get("svg", {})
            nested_type = svg_block.get("type")
            nested_params = svg_block.get("parameters")
            if isinstance(nested_type, str) and nested_type.strip():
                svg_type = nested_type.lower().strip()
            if isinstance(nested_params, dict):
                params = nested_params

            markup = svg_block.get("svg_markup")
            if isinstance(markup, str) and "<svg" in markup.lower():
                return {"success": True, "svg": markup}
        
        # Allow direct SVG markup passthrough too.
        if isinstance(params.get("svg_markup"), str) and "<svg" in params["svg_markup"].lower():
            return {"success": True, "svg": params["svg_markup"]}
        
        if svg_type in ["circle", "rectangle", "triangle", "square"]:
            svg = generate_svg_shape(svg_type, params)
        elif svg_type == "fraction":
            svg = generate_svg_fraction(params.get("numerator", 1), params.get("denominator", 2))
        elif svg_type == "number_line":
            svg = generate_svg_number_line(params.get("start", 0), params.get("end", 10), params.get("marked", 5))
        elif svg_type == "bar_chart":
            svg = generate_svg_bar_chart(params.get("values", []), params.get("labels", []))
        elif svg_type == "clock":
            svg = generate_svg_clock(params.get("hours", 3), params.get("minutes", 30))
        elif svg_type == "pie_chart":
            svg = generate_svg_pie_chart(params.get("values", [3, 2, 1]), params.get("labels", []), params.get("colors", []))
        elif svg_type == "ruler":
            svg = generate_svg_ruler(params.get("length_cm", 10))
        elif svg_type == "angle":
            svg = generate_svg_angle(params.get("degrees", 60), params.get("label", ""))
        elif svg_type == "thermometer":
            svg = generate_svg_thermometer(params.get("temperature", 37), params.get("min_temp", 0), params.get("max_temp", 100), params.get("unit", "°C"))
        elif svg_type == "place_value":
            svg = generate_svg_place_value(params.get("number", 345))
        elif svg_type == "venn_diagram":
            svg = generate_svg_venn_diagram(params.get("set_a_label", "A"), params.get("set_b_label", "B"), params.get("intersection_label", "A∩B"))
        elif svg_type == "coins":
            svg = generate_svg_coins(params.get("coins", [1, 2, 5, 10]))
        elif svg_type == "shapes_grid":
            svg = generate_svg_shapes_grid(params.get("shapes", ["circle", "square", "triangle", "rectangle"]))
        elif svg_type == "food_chain":
            svg = generate_svg_food_chain(params.get("organisms", []))
        elif svg_type == "plant_parts":
            svg = generate_svg_plant_parts(params.get("labeled", True))
        elif svg_type == "water_cycle":
            svg = generate_svg_water_cycle(params.get("labeled", True))
        elif svg_type == "cell":
            svg = generate_svg_cell(params.get("cell_type", "animal"))
        elif svg_type == "magnet":
            svg = generate_svg_magnet(params.get("poles_labeled", True))
        elif svg_type == "states_of_matter":
            svg = generate_svg_states_of_matter(params.get("state", "all"))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid SVG type: {svg_type}")
        
        return {"success": True, "svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/save-quiz-attempt")
async def save_quiz_attempt(payload: dict, user=Depends(get_current_user)):
    """Save quiz attempt to MongoDB for analytics"""
    try:
        if user.get("role") != "student":
            raise HTTPException(status_code=403, detail="Student role required")

        student_id = str(user.get("user_id") or payload.get("student_id") or "").strip()
        quiz_id = str(payload.get("quiz_id") or "").strip()
        if not student_id or not quiz_id:
            raise HTTPException(status_code=400, detail="quiz_id and student session are required")

        attempt = {
            "quiz_id": quiz_id,
            "student_id": student_id,
            "student_name": user.get("name"),
            "school": _normalize_school(user.get("school")),
            "class_grade": user.get("class_grade"),
            "score": payload.get("score"),
            "correct": payload.get("correct"),
            "total": payload.get("total"),
            "timestamp": payload.get("timestamp") or _iso_now(),
            "submitted_at": _iso_now(),
            "answers": payload.get("answers", {}),
        }

        await student_attempts_collection.update_one(
            {"quiz_id": quiz_id, "student_id": student_id},
            {"$set": attempt},
            upsert=True,
        )
        
        return {"success": True, "message": "Quiz attempt saved"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/batch-generate-questions")
async def api_batch_generate_questions(
    grade: int,
    subject: str,
    topic: str,
    count: int = 50,
):
    """AI batch question generation with MongoDB caching. Free tier safe (1 call = 50 questions)."""
    from app.generators.ai_generator import batch_generate_questions
    questions = await batch_generate_questions(grade=grade, subject=subject, topic=topic, count=count)
    return {"questions": questions, "count": len(questions), "cached": len(questions) > 0}


@router.post("/tools/generate-content-pack")
async def api_generate_content_pack(grade: int, subject: str, limit: int = 2000, language: Optional[str] = None):
    """Generate offline content pack for students"""
    try:
        result = await generate_content_pack(questions_collection, grade, subject, limit, language=language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/content-packs")
async def api_list_content_packs():
    """List all available content packs"""
    try:
        packs = await list_content_packs()
        return {"packs": packs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/content-pack/{pack_id}")
async def api_get_content_pack(pack_id: str):
    """Download a specific content pack"""
    try:
        pack = await get_content_pack(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail="Content pack not found")
        return pack
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
