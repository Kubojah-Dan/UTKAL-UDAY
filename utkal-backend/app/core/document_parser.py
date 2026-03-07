import os
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
import pdfplumber
from docx import Document
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from Word document"""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"DOCX extraction error: {e}")
    return text.strip()

def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF or Word document"""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text: str, max_tokens: int = 800) -> List[str]:
    """Split text into chunks for processing"""
    # Simple chunking by paragraphs
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # Rough token estimate: 1 token ≈ 4 chars
        if len(current_chunk) + len(para) < max_tokens * 4:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

GROQ_PARSE_PROMPT = """You are a JSON-only parser. Receive a block of extracted text from a teacher's PDF or Word containing multiple questions. Parse the text and return ONLY a single valid JSON array named "questions". Do NOT return any explanatory text, markdown, or code fences — only valid JSON.

Output schema for each question object (every field must appear; if unknown, use null or empty array):

{
  "id": "<string, unique, format: subject_grade_topic_seq e.g. math_g3_add_0001>",
  "source_doc": "<string: original file name or upload id>",
  "subject": "<Math|Science|English|Other>",
  "grade": <integer>,
  "board": "<string or null>",
  "medium": "<string (language of source) e.g. en>",
  "type": "<mcq|descriptive|short_answer|fill_blank|image_mcq>",
  "marks": <integer or null>,
  "difficulty": "<easy|medium|hard|null>",
  "topic": "<string>",
  "subtopic": "<string|null>",
  "question": "<string: question text, blanks represented by ____ for fill_blank>",
  "options": ["opt1","opt2",...],
  "answer": "<string: correct option text or short answer>",
  "expected_points": ["point1","point2",...],
  "explanation": "<string|null>",
  "image": {
     "has_image": <true|false>,
     "suggested_image_query": "<string|null>",
     "image_license_preference": "<public-domain|cc-by|cc-by-sa|null>",
     "image_source_url": "<URL|null>"
  },
  "hints": ["hint1","hint2"],
  "tags": ["ncert","addition","units"],
  "language_variants": {},
  "confidence": <0.0-1.0>,
  "raw_extracted_snippet": "<string: snippet used to create this Q>",
  "parse_notes": "<string|null>"
}

RULES:
1. ALWAYS return an array named "questions". Even if empty, return {"questions": []}.
2. Preserve teacher's original phrasing when possible.
3. For MCQs, include all options in "options" and the correct option text in "answer".
4. For fill_blank, represent blanks as '____' in the "question" field.
5. For descriptive questions (5 marks), set type to "descriptive" and marks to 5, populate expected_points array.
6. If the text references an embedded image, set image.has_image true.
7. Do NOT include any explanatory text outside the JSON.
8. Output must be syntactically valid JSON. Use double quotes for strings.

OUTPUT:
Respond now with the JSON array of parsed questions from the following extracted text:

"""

def parse_questions_with_groq(text: str, source_doc: str) -> List[Dict]:
    """Parse questions from text using Groq AI"""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")
    
    client = Groq(api_key=GROQ_API_KEY)
    chunks = chunk_text(text)
    all_questions = []
    
    # Limit to first 2 chunks to avoid rate limits
    chunks = chunks[:2]
    
    for i, chunk in enumerate(chunks):
        try:
            # Add delay between requests to avoid rate limiting
            if i > 0:
                import time
                time.sleep(2)
            
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                    {"role": "user", "content": GROQ_PARSE_PROMPT + chunk}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            questions = data.get("questions", [])
            
            # Add source_doc to each question
            for q in questions:
                q["source_doc"] = source_doc
                if not q.get("id"):
                    q["id"] = f"{q.get('subject', 'unk').lower()[:3]}_g{q.get('grade', 0)}_{len(all_questions):04d}"
            
            all_questions.extend(questions)
        except Exception as e:
            print(f"Groq parsing error for chunk: {e}")
            continue
    
    return all_questions

def validate_question(question: Dict) -> bool:
    """Validate parsed question structure"""
    required = ["subject", "grade", "type", "question"]
    for field in required:
        if not question.get(field):
            return False
    
    if question["type"] == "mcq" and len(question.get("options", [])) < 2:
        return False
    
    if question["type"] == "fill_blank" and "____" not in question["question"]:
        return False
    
    if question["type"] == "descriptive" and not question.get("expected_points"):
        return False
    
    return True
