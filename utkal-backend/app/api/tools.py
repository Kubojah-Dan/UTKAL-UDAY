from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.tools.generate_questions import generate_questions

router = APIRouter()

class GenerateRequest(BaseModel):
    topic: str
    grade: int
    subject: str = "Math"
    count: int = 5

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
        
        # Return as list of dicts for frontend
        return [q.model_dump() for q in results]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
