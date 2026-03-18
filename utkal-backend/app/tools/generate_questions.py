import os
import json
import uuid
import re
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
    type: str = "mcq"  # mcq, descriptive, image_mcq, fill_blank, short_answer
    marks: Optional[int] = 1
    passage: Optional[str] = None
    instructions: Optional[str] = None
    question: str
    options: List[str] = Field(default_factory=list)
    answer: str
    accepted_answers: Optional[List[str]] = Field(default_factory=list)
    expected_points: Optional[List[str]] = Field(default_factory=list)  # For descriptive questions
    explanation: Optional[str] = None
    skill_id: Optional[str] = None
    skill_label: Optional[str] = None
    hint: Optional[str] = None
    hints: Optional[List[str]] = Field(default_factory=list)
    image: Optional[dict] = None  # Image metadata

class QuestionBatch(BaseModel):
    questions: List[Question]

SUPPORTED_TYPES = {"mcq", "image_mcq", "fill_blank", "short_answer", "descriptive"}


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _clean_multiline(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    blank_seen = False
    for raw in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if line:
            lines.append(line)
            blank_seen = False
        elif lines and not blank_seen:
            lines.append("")
            blank_seen = True
    return "\n".join(lines).strip()


def _clean_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, dict):
        raw_items = [value[k] for k in sorted(value.keys(), key=lambda x: str(x))]
    else:
        raw_items = re.split(r"\n|;|\|", str(value))
    out = []
    seen = set()
    for item in raw_items:
        clean = _clean_text(item)
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _default_marks(qtype: str) -> int:
    if qtype == "descriptive":
        return 5
    if qtype == "short_answer":
        return 2
    return 1


def _normalize_type(raw_type: object, options: List[str], marks: int, question: str) -> str:
    token = _clean_text(raw_type).lower().replace("-", "_").replace(" ", "_")
    alias = {
        "multiple_choice": "mcq",
        "multiple_choice_question": "mcq",
        "fill_in_the_blank": "fill_blank",
        "fill_blank": "fill_blank",
        "short": "short_answer",
        "short_answer": "short_answer",
        "long_answer": "descriptive",
        "essay": "descriptive",
        "subjective": "descriptive",
    }
    qtype = alias.get(token, token)
    if qtype not in SUPPORTED_TYPES:
        if len(options) >= 2:
            qtype = "mcq"
        elif "____" in question:
            qtype = "fill_blank"
        elif marks >= 5:
            qtype = "descriptive"
        else:
            qtype = "short_answer"
    if qtype in {"mcq", "image_mcq"} and len(options) < 2:
        qtype = "short_answer"
    return qtype


def _normalize_generated_question(payload: dict, canonical_subject: str, grade: int, topic: str, seq: int) -> Question:
    question = _clean_multiline(payload.get("question"))
    passage = _clean_multiline(payload.get("passage")) or None
    instructions = _clean_multiline(payload.get("instructions")) or None
    options = _clean_list(payload.get("options"))

    marks = payload.get("marks")
    try:
        marks = int(float(str(marks)))
    except (TypeError, ValueError):
        marks = 0

    qtype = _normalize_type(payload.get("type"), options, marks, question)
    if not marks or marks < 1:
        marks = _default_marks(qtype)

    answer = _clean_text(payload.get("answer"))
    if qtype in {"mcq", "image_mcq"} and not answer and options:
        answer = options[0]
    if not answer and qtype in {"short_answer", "descriptive"}:
        answer = "Answers may vary. Refer to key points."
    if qtype == "fill_blank" and "____" not in question:
        if answer and answer.lower() in question.lower():
            question = re.sub(re.escape(answer), "____", question, count=1, flags=re.IGNORECASE)
        else:
            question = f"{question} ____".strip()

    expected_points = _clean_list(payload.get("expected_points"))
    if qtype == "descriptive" and not expected_points:
        source = _clean_multiline(payload.get("explanation")) or answer
        if source:
            expected_points = [p for p in re.split(r"\n|;|\. ", source) if _clean_text(p)][:4]
            expected_points = [_clean_text(p) for p in expected_points if _clean_text(p)]

    accepted_answers = _clean_list(payload.get("accepted_answers"))
    if answer:
        accepted_answers.append(answer)
    if qtype in {"short_answer", "descriptive"} and expected_points:
        accepted_answers.extend(expected_points[:3])
    accepted_answers = _clean_list(accepted_answers)

    if not accepted_answers and answer:
        accepted_answers = [answer]

    hints = _clean_list(payload.get("hints"))
    hint = _clean_text(payload.get("hint")) or (hints[0] if hints else None)

    image = payload.get("image") if isinstance(payload.get("image"), dict) else {
        "has_image": False,
        "suggested_image_query": None,
        "image_license_preference": None
    }
    image["has_image"] = bool(image.get("has_image", False))
    image["suggested_image_query"] = _clean_text(image.get("suggested_image_query")) or None
    image["image_license_preference"] = _clean_text(image.get("image_license_preference")) or None

    difficulty = _clean_text(payload.get("difficulty")).lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "hard" if grade >= 9 else ("medium" if grade >= 5 else "easy")

    slug_topic = topic.lower().replace(" ", "_")
    generated_id = payload.get("id") or f"{canonical_subject.lower()[:3]}_g{grade}_{slug_topic}_{seq:03d}_{uuid.uuid4().hex[:4]}"

    return Question(
        id=generated_id,
        subject=canonical_subject,
        grade=grade,
        board=_clean_text(payload.get("board")) or "NCERT",
        medium=_clean_text(payload.get("medium")) or "English",
        topic=_clean_text(payload.get("topic")) or topic,
        difficulty=difficulty,
        type=qtype,
        marks=marks,
        passage=passage,
        instructions=instructions,
        question=question,
        options=options,
        answer=answer,
        accepted_answers=accepted_answers,
        expected_points=expected_points,
        explanation=_clean_multiline(payload.get("explanation")) or None,
        skill_id=_clean_text(payload.get("skill_id")) or f"skill_{slug_topic}",
        skill_label=_clean_text(payload.get("skill_label")) or topic,
        hint=hint,
        hints=hints,
        image=image,
    )


def _target_type_mix(subject: str, count: int, include_descriptive: bool) -> List[str]:
    mix = ["mcq", "fill_blank", "short_answer"]
    if include_descriptive or count >= 4:
        mix.append("descriptive")
    if subject.lower() == "english" and count >= 3:
        mix.append("passage_based")
    return mix


def generate_questions(topic: str, grade: int, subject: str, count: int = 5, include_descriptive: bool = False, multilingual: bool = False):
    from app.core.generated_question_bank import normalize_subject
    
    canonical_subject = normalize_subject(subject) or subject
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    client = Groq(api_key=api_key)
    
    type_mix = _target_type_mix(canonical_subject, count, include_descriptive)
    
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
Generate {count} high-quality {canonical_subject} questions for Grade {grade} on topic "{topic}".

Requirements:
- Use a mix of formats: {", ".join(type_mix)}.
- Keep language age-appropriate for Grade {grade}.
- Include at least 30% non-MCQ questions.
- For English/passage-based questions, place the full reading text in "passage" and keep "question" as the actual sub-question.
- Preserve multi-paragraph passage formatting with newline breaks.
- For fill_blank, include ____ in question text.
- answer must never be null.
- For descriptive, include expected_points and marks=5.
- For short_answer, marks=2.
- For mcq/image_mcq, provide 4 options and answer as option text (not A/B/C/D).
- Align with NCERT expectations.{multilingual_instruction}

Return only a valid JSON object:
{{
  "questions": [
    {{
      "subject": "{canonical_subject}",
      "grade": {grade},
      "topic": "{topic}",
      "difficulty": "easy|medium|hard",
      "type": "mcq|image_mcq|fill_blank|short_answer|descriptive",
      "marks": 1,
      "passage": "",
      "instructions": "",
      "question": "",
      "options": [],
      "answer": "",
      "accepted_answers": [],
      "expected_points": [],
      "explanation": "",
      "hint": "",
      "hints": [],
      "image": {{
        "has_image": false,
        "suggested_image_query": null,
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

        raw_questions = data.get("questions", [])
        if not isinstance(raw_questions, list):
            raw_questions = []

        normalized_questions: List[Question] = []
        for idx, payload in enumerate(raw_questions, 1):
            if not isinstance(payload, dict):
                continue
            normalized_questions.append(
                _normalize_generated_question(
                    payload=payload,
                    canonical_subject=canonical_subject,
                    grade=grade,
                    topic=topic,
                    seq=idx,
                )
            )

        if not normalized_questions:
            return []

        validated_batch = QuestionBatch(questions=normalized_questions)
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
