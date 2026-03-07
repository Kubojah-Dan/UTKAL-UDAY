from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from pathlib import Path
from app.tools.generate_questions import generate_questions
from app.core.document_parser import extract_text_from_file, parse_questions_with_groq, validate_question
from app.core.translation import translate_question
from app.core.database import questions_collection, quizzes_collection
from app.tools.svg_generator import generate_svg_shape, generate_svg_fraction, generate_svg_number_line, generate_svg_bar_chart, generate_svg_clock

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

class GenerateSVGRequest(BaseModel):
    svg_type: str
    params: dict

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
        questions = parse_questions_with_groq(text, file.filename)
        
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
        
        saved_count = 0
        translation_errors = 0
        
        for question in req.questions:
            # Try translation if requested, but don't fail if it errors
            if req.translate_to:
                print(f"\nTranslating question: {question.get('id')}")
                try:
                    question = translate_question(question, req.translate_to)
                    print(f"Translation completed. Languages: {list(question.get('language_variants', {}).keys())}")
                except Exception as e:
                    print(f"Translation skipped for question {question.get('id')}: {e}")
                    translation_errors += 1
            
            # Add metadata
            question["approved"] = True
            question["status"] = "active"
            
            # Save to MongoDB
            result = await questions_collection.update_one(
                {"id": question["id"]},
                {"$set": question},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                saved_count += 1
        
        message = f"Successfully saved {saved_count} questions to database"
        if translation_errors > 0:
            message += f" (translation skipped for {translation_errors} questions - check Sarvam API key)"
        
        print(f"\n=== RESULT: {message} ===")
        
        return {
            "success": True,
            "saved_count": saved_count,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save questions: {str(e)}")

@router.post("/tools/create-quiz")
async def create_quiz(req: CreateQuizRequest):
    """Create a quiz from selected questions"""
    try:
        quiz_id = f"quiz_{req.subject.lower()}_g{req.grade}_{uuid.uuid4().hex[:8]}"
        
        quiz = {
            "id": quiz_id,
            "title": req.title,
            "grade": req.grade,
            "subject": req.subject,
            "question_ids": req.question_ids,
            "duration_minutes": req.duration_minutes,
            "status": "active",
            "created_at": None  # Will be set by MongoDB
        }
        
        await quizzes_collection.insert_one(quiz)
        
        return {"success": True, "quiz_id": quiz_id, "quiz": quiz}
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
    duration: int = Form(30)
):
    """Upload PDF with quiz questions and create quiz"""
    try:
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        text = extract_text_from_file(str(file_path))
        if not text or len(text) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text")
        
        questions = parse_questions_with_groq(text, file.filename)
        valid_questions = [q for q in questions if validate_question(q)]
        
        question_ids = []
        for q in valid_questions:
            q["approved"] = True
            q["status"] = "active"
            q["grade"] = grade
            result = await questions_collection.insert_one(q)
            question_ids.append(q["id"])
        
        quiz_id = f"quiz_{grade}_{uuid.uuid4().hex[:8]}"
        quiz = {
            "id": quiz_id,
            "title": title,
            "grade": grade,
            "question_ids": question_ids,
            "duration_minutes": duration,
            "status": "active"
        }
        await quizzes_collection.insert_one(quiz)
        
        os.remove(file_path)
        
        return {
            "success": True,
            "quiz_id": quiz_id,
            "question_count": len(question_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/notifications")
async def get_notifications(student_id: str, grade: Optional[int] = None):
    """Get new quiz notifications for student"""
    try:
        query = {"status": "active"}
        if grade:
            query["grade"] = grade
        
        cursor = quizzes_collection.find(query).sort("_id", -1).limit(5)
        quizzes = await cursor.to_list(length=5)
        
        notifications = []
        for quiz in quizzes:
            notifications.append({
                "title": f"New Quiz: {quiz['title']}",
                "message": f"Grade {quiz['grade']} - {quiz['duration_minutes']} minutes",
                "quiz_id": quiz["id"]
            })
        
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/quiz-analytics")
async def get_quiz_analytics(grade: Optional[int] = None):
    """Get quiz analytics for teacher dashboard"""
    try:
        from app.core.database import student_attempts_collection
        
        print(f"\n=== QUIZ ANALYTICS REQUEST ===")
        print(f"Grade filter: {grade}")
        
        pipeline = [
            {"$match": {"quiz_id": {"$exists": True}}},
            {"$group": {
                "_id": "$quiz_id",
                "attempts": {"$sum": 1},
                "avg_score": {"$avg": "$score"},
                "last_attempt": {"$max": "$timestamp"}
            }}
        ]
        
        cursor = student_attempts_collection.aggregate(pipeline)
        results = await cursor.to_list(length=100)
        print(f"Aggregation results: {len(results)} quiz IDs found")
        
        analytics = []
        for result in results:
            print(f"Processing quiz_id: {result['_id']}")
            quiz = await quizzes_collection.find_one({"id": result["_id"]})
            if quiz:
                print(f"  Quiz found: {quiz.get('title')} (Grade {quiz.get('grade')})")
                if not grade or quiz.get("grade") == grade:
                    analytics.append({
                        "quiz_id": result["_id"],
                        "title": quiz.get("title", "Unknown"),
                        "grade": quiz.get("grade", 0),
                        "attempts": result["attempts"],
                        "avg_score": round(result.get("avg_score", 0)),
                        "last_attempt": result["last_attempt"]
                    })
            else:
                print(f"  Quiz NOT found in quizzes collection")
        
        print(f"Returning {len(analytics)} analytics records")
        print(f"Analytics: {analytics}")
        
        return {"analytics": analytics}
    except Exception as e:
        print(f"ERROR in quiz-analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/quizzes")
async def get_quizzes(grade: Optional[int] = None, subject: Optional[str] = None):
    """Get available quizzes"""
    try:
        query = {"status": "active"}
        if grade:
            query["grade"] = grade
        if subject:
            query["subject"] = subject
        
        cursor = quizzes_collection.find(query)
        quizzes = await cursor.to_list(length=100)
        
        for q in quizzes:
            q.pop("_id", None)
        
        return {"quizzes": quizzes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quizzes: {str(e)}")

@router.post("/tools/generate-svg")
async def generate_svg(req: GenerateSVGRequest):
    """Generate SVG image for visual questions"""
    try:
        svg_type = req.svg_type.lower()
        params = req.params
        
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
        else:
            raise HTTPException(status_code=400, detail="Invalid SVG type")
        
        return {"success": True, "svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/save-quiz-attempt")
async def save_quiz_attempt(payload: dict):
    """Save quiz attempt to MongoDB for analytics"""
    try:
        from app.core.database import student_attempts_collection
        
        attempt = {
            "quiz_id": payload.get("quiz_id"),
            "student_id": payload.get("student_id"),
            "score": payload.get("score"),
            "correct": payload.get("correct"),
            "total": payload.get("total"),
            "timestamp": payload.get("timestamp"),
            "answers": payload.get("answers", {})
        }
        
        await student_attempts_collection.insert_one(attempt)
        
        return {"success": True, "message": "Quiz attempt saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))