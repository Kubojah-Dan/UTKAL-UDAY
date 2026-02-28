import os
import json
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configuration
MODEL_NAME = "llama-3.1-8b-instant"  # Highly stable model on Groq

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    grade: int
    board: str = "NCERT"
    medium: str = "English"
    topic: str
    difficulty: str
    type: str = "mcq"
    question: str
    options: List[str]
    answer: str
    accepted_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    skill_id: Optional[str] = None
    skill_label: Optional[str] = None
    hint: Optional[str] = None

class QuestionBatch(BaseModel):
    questions: List[Question]

def generate_questions(topic: str, grade: int, subject: str, count: int = 5):
    from app.core.generated_question_bank import normalize_subject
    
    canonical_subject = normalize_subject(subject) or subject
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are an expert educator specializing in the Indian NCERT curriculum.
    Generate {count} unique, high-quality {canonical_subject} questions for Grade {grade} on the topic of "{topic}".
    
    Criteria:
    - Language: Simple English suitable for students.
    - Context: Culturally appropriate examples for India.
    - Format: Multiple Choice Questions (MCQ).
    - Alignment: Strictly follow NCERT guidelines for Grade {grade}.
    
    Return ONLY a valid JSON object. Do not include any introductory or concluding text, no markdown code blocks, and no backticks.
    
    The JSON structure MUST be:
    {{
      "questions": [
        {{
          "subject": "{canonical_subject}",
          "grade": {grade},
          "topic": "{topic}",
          "difficulty": "easy/medium/hard",
          "type": "mcq",
          "question": "The question text",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": "The correct option text exactly as it appears in options",
          "explanation": "Brief explanation",
          "hint": "A small clue"
        }}
      ]
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_NAME,
            temperature=0.2,
            top_p=0.9,
            response_format={"type": "json_object"}
        )
        
        content = chat_completion.choices[0].message.content
        if not content:
             raise ValueError("Empty response from Groq API")
             
        data = json.loads(content)
        
        # Validate and add IDs
        validated_batch = QuestionBatch(**data)
        for q in validated_batch.questions:
            slug_topic = topic.lower().replace(' ', '_')
            q.id = f"{canonical_subject.lower()[:3]}_g{grade}_{slug_topic}_{uuid.uuid4().hex[:6]}"
            if not q.skill_id:
                q.skill_id = f"skill_{slug_topic}"
            if not q.skill_label:
                q.skill_label = topic
        
        return validated_batch.questions

    except Exception as e:
        print(f"Error generating questions for {topic} (Grade {grade}, Subject {canonical_subject}): {type(e).__name__}: {e}")
        return []

if __name__ == "__main__":
    # Test generation
    print("Generating test questions for Science Grade 10...")
    qs = generate_questions("Human Eye", 10, "Science", 2)
    for q in qs:
        print(f"Q: {q.question}")
        print(f"Options: {q.options}")
        print(f"A: {q.answer}")
        print("-" * 20)
    
    print("\nGenerating test questions for English Grade 5...")
    qs2 = generate_questions("Tenses", 5, "English", 2)
    for q in qs2:
        print(f"Q: {q.question}")
        print(f"Options: {q.options}")
        print(f"A: {q.answer}")
        print("-" * 20)
    
    # Save to a temporary file if needed
    if qs:
        with open("generated_questions_test.json", "w") as f:
            json.dump([q.dict() for q in qs], f, indent=2)
        print(f"Saved {len(qs)} questions to generated_questions_test.json")
