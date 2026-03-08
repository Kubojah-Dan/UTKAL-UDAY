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
    type: str = "mcq"  # mcq, descriptive, image_mcq, fill_blank
    marks: Optional[int] = 1
    question: str
    options: List[str] = []
    answer: str
    accepted_answers: Optional[List[str]] = None
    expected_points: Optional[List[str]] = []  # For descriptive questions
    explanation: Optional[str] = None
    skill_id: Optional[str] = None
    skill_label: Optional[str] = None
    hint: Optional[str] = None
    image: Optional[dict] = None  # Image metadata

class QuestionBatch(BaseModel):
    questions: List[Question]

def generate_questions(topic: str, grade: int, subject: str, count: int = 5, include_descriptive: bool = False, multilingual: bool = False):
    from app.core.generated_question_bank import normalize_subject
    
    canonical_subject = normalize_subject(subject) or subject
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    client = Groq(api_key=api_key)
    
    # Adjust prompt for descriptive questions
    question_types = "Multiple Choice Questions (MCQ)"
    if include_descriptive:
        question_types = "a mix of Multiple Choice Questions (MCQ) and Descriptive Questions (5 marks)"
    
    # Add multilingual instruction if requested
    multilingual_instruction = ""
    if multilingual:
        multilingual_instruction = """
    - For each question, also provide translations in Hindi, Tamil, Telugu, and Odia.
    - Add a "translations" field with keys: "hi", "ta", "te", "or".
    - Each translation should include: question, options (if MCQ), explanation, hint.
    - Keep numbers and mathematical symbols unchanged in translations.
        """
    
    prompt = f"""
    You are an expert educator specializing in the Indian NCERT curriculum.
    Generate {count} unique, high-quality {canonical_subject} questions for Grade {grade} on the topic of "{topic}".
    
    Criteria:
    - Language: Simple English suitable for students.
    - Context: Culturally appropriate examples for India.
    - Format: {question_types}.
    - For descriptive questions: Set marks to 5, provide expected_points array with key points students should cover.
    - For image-based questions: Set has_image to true and provide suggested_image_query.
    - Alignment: Strictly follow NCERT guidelines for Grade {grade}.{multilingual_instruction}
    
    Return ONLY a valid JSON object. Do not include any introductory or concluding text, no markdown code blocks, and no backticks.
    
    The JSON structure MUST be:
    {{
      "questions": [
        {{
          "subject": "{canonical_subject}",
          "grade": {grade},
          "topic": "{topic}",
          "difficulty": "easy/medium/hard",
          "type": "mcq or descriptive or image_mcq",
          "marks": 1 for mcq or 5 for descriptive,
          "question": "The question text",
          "options": ["Option A", "Option B", "Option C", "Option D"] (empty for descriptive),
          "answer": "The correct option text or key answer points",
          "expected_points": ["point1", "point2", "point3"] (for descriptive only),
          "explanation": "Brief explanation",
          "hint": "A small clue",
          "image": {{
            "has_image": true/false,
            "suggested_image_query": "description for image search",
            "image_license_preference": "public-domain"
          }}
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
            
            # Set default marks if not provided
            if not q.marks:
                q.marks = 5 if q.type == "descriptive" else 1
        
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
