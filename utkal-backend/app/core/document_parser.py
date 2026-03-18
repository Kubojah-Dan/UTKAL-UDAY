import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber
from docx import Document
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WHITESPACE_RE = re.compile(r"[ \t]+")
QUESTION_START_RE = re.compile(r"(?mi)^(?=(?:question\s*\d+|q\.?\s*\d+|\d+\s*[\).:-]))")
NULL_TOKENS = {"", "null", "none", "n/a", "na", "not provided", "unknown", "-"}

TYPE_ALIASES = {
    "mcq": "mcq",
    "multiple choice": "mcq",
    "multiple_choice": "mcq",
    "multiple choice question": "mcq",
    "single choice": "mcq",
    "image mcq": "image_mcq",
    "image_mcq": "image_mcq",
    "picture mcq": "image_mcq",
    "fill_blank": "fill_blank",
    "fill in the blank": "fill_blank",
    "fill in blanks": "fill_blank",
    "fill_in_the_blank": "fill_blank",
    "short answer": "short_answer",
    "short_answer": "short_answer",
    "short": "short_answer",
    "descriptive": "descriptive",
    "long answer": "descriptive",
    "essay": "descriptive",
    "subjective": "descriptive",
    "text": "short_answer",
    "numeric": "short_answer",
}

OBJECTIVE_TYPES = {"mcq", "image_mcq", "fill_blank"}
SUBJECTIVE_TYPES = {"short_answer", "descriptive"}


def _is_nullish(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in NULL_TOKENS


def _normalize_block_text(value: object, preserve_paragraphs: bool = True) -> str:
    if value is None:
        return ""

    text = str(value).replace("\r\n", "\n").replace("\r", "\n").replace("\u200b", " ")
    lines = []
    blank_run = 0

    for raw_line in text.split("\n"):
        line = WHITESPACE_RE.sub(" ", raw_line).strip()
        if line:
            lines.append(line)
            blank_run = 0
            continue

        if not preserve_paragraphs:
            continue

        if lines and blank_run == 0:
            lines.append("")
        blank_run += 1

    normalized = "\n".join(lines).strip()
    if preserve_paragraphs:
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def _normalize_short_text(value: object) -> str:
    return _normalize_block_text(value, preserve_paragraphs=False)


def _slug(value: object, fallback: str = "general") -> str:
    token = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return token or fallback


def _safe_int(value: object, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _coerce_grade(value: object, fallback: Optional[int]) -> int:
    grade = _safe_int(value, default=fallback if fallback is not None else 3)
    if grade is None:
        grade = 3
    return max(1, min(12, grade))


def _normalize_subject(value: object, fallback: Optional[str]) -> str:
    subject = _normalize_short_text(value)
    if _is_nullish(subject):
        subject = _normalize_short_text(fallback) if fallback else "Other"
    lowered = subject.lower()
    if lowered in {"math", "maths"}:
        return "Mathematics"
    if lowered == "english language":
        return "English"
    if lowered in {"sci", "science"}:
        return "Science"
    return subject or "Other"


def _coerce_difficulty(value: object, grade: int, marks: int) -> str:
    raw = _normalize_short_text(value).lower()
    if raw in {"easy", "medium", "hard"}:
        return raw
    if marks >= 5 or grade >= 9:
        return "hard"
    if marks >= 2 or grade >= 5:
        return "medium"
    return "easy"


def _normalize_options(value: object) -> List[str]:
    normalized: List[str] = []

    if isinstance(value, list):
        candidates = value
    elif isinstance(value, dict):
        candidates = [value[k] for k in sorted(value.keys(), key=lambda item: str(item))]
    elif _is_nullish(value):
        candidates = []
    else:
        candidates = [part for part in re.split(r"\n|;|\|", str(value)) if part.strip()]

    seen = set()
    for item in candidates:
        option = _normalize_block_text(item, preserve_paragraphs=True)
        if _is_nullish(option):
            continue
        key = option.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(option)

    return normalized


def _coerce_text_list(value: object) -> List[str]:
    if _is_nullish(value):
        return []

    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    else:
        text = str(value)
        if "\n" in text or ";" in text:
            items = re.split(r"\n|;", text)
        else:
            items = [text]

    out: List[str] = []
    seen = set()
    for item in items:
        normalized = _normalize_block_text(item, preserve_paragraphs=False)
        if _is_nullish(normalized):
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def _resolve_mcq_answer(answer: str, options: List[str]) -> str:
    if not answer:
        return ""
    if not options:
        return answer

    letter_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}
    normalized = answer.strip().lower()
    normalized = normalized.replace("option", "").replace("choice", "").strip()
    normalized = normalized.rstrip(".)")
    if normalized in letter_map:
        idx = letter_map[normalized]
        if idx < len(options):
            return options[idx]

    for option in options:
        if option.casefold() == answer.casefold():
            return option

    return answer


def _infer_type(raw_type: object, options: List[str], question: str, marks: int) -> str:
    token = _normalize_short_text(raw_type).lower()
    if token in TYPE_ALIASES:
        qtype = TYPE_ALIASES[token]
    else:
        qtype = TYPE_ALIASES.get(token.replace("-", " ").replace("_", " "), "")

    if not qtype:
        if len(options) >= 2:
            qtype = "mcq"
        elif "____" in question:
            qtype = "fill_blank"
        elif marks >= 5:
            qtype = "descriptive"
        else:
            qtype = "short_answer"

    if qtype in {"mcq", "image_mcq"} and len(options) < 2:
        return "short_answer"

    return qtype


def _default_marks(qtype: str) -> int:
    if qtype == "descriptive":
        return 5
    if qtype == "short_answer":
        return 2
    return 1


def _extract_expected_points(answer: str, explanation: str) -> List[str]:
    points: List[str] = []
    source = answer or explanation
    if not source:
        return points

    for piece in re.split(r"\n|;|\. ", source):
        point = _normalize_block_text(piece, preserve_paragraphs=False)
        if len(point) < 3:
            continue
        points.append(point)
        if len(points) == 5:
            break
    return points


def _ensure_fill_blank_text(question: str, accepted_answers: List[str]) -> str:
    if "____" in question:
        return question

    if accepted_answers:
        candidate = accepted_answers[0]
        pattern = re.compile(re.escape(candidate), re.IGNORECASE)
        if pattern.search(question):
            return pattern.sub("____", question, count=1)

    trimmed = question.rstrip()
    if trimmed.endswith("?"):
        return f"{trimmed[:-1]} ____?"
    return f"{trimmed} ____"


def _normalize_hints(value: object, hint_value: object) -> List[str]:
    hints = _coerce_text_list(value)
    if not hints and not _is_nullish(hint_value):
        hints = _coerce_text_list(hint_value)
    return hints


def _normalize_image(payload: object) -> Dict:
    base = {
        "has_image": False,
        "suggested_image_query": None,
        "image_license_preference": None,
        "image_source_url": None,
    }
    if not isinstance(payload, dict):
        return base

    has_image = payload.get("has_image")
    if isinstance(has_image, str):
        has_image = has_image.strip().lower() in {"true", "1", "yes", "y"}
    elif not isinstance(has_image, bool):
        has_image = False

    base["has_image"] = bool(has_image)
    base["suggested_image_query"] = _normalize_short_text(payload.get("suggested_image_query")) or None
    base["image_license_preference"] = _normalize_short_text(payload.get("image_license_preference")) or None
    base["image_source_url"] = _normalize_short_text(payload.get("image_source_url")) or None
    return base


def _build_question_id(
    source_doc: str,
    subject: str,
    grade: int,
    topic: str,
    question: str,
    sequence: int,
) -> str:
    digest = hashlib.md5(
        f"{source_doc}|{subject}|{grade}|{topic}|{question}|{sequence}".encode("utf8")
    ).hexdigest()[:8]
    return f"{_slug(subject, 'sub')}_g{grade}_{_slug(topic, 'topic')}_{digest}"


def _normalize_question_payload(
    payload: Dict,
    source_doc: str,
    sequence: int,
    grade_hint: Optional[int],
    subject_hint: Optional[str],
) -> Dict:
    question = _normalize_block_text(payload.get("question"), preserve_paragraphs=True)
    passage = _normalize_block_text(payload.get("passage"), preserve_paragraphs=True)
    instructions = _normalize_block_text(payload.get("instructions"), preserve_paragraphs=True)
    options = _normalize_options(payload.get("options"))

    marks = _safe_int(payload.get("marks"), default=None)
    marks = marks if marks is not None and marks > 0 else 0
    inferred_marks = marks or _default_marks("short_answer")
    qtype = _infer_type(payload.get("type"), options, question, inferred_marks)
    marks = marks or _default_marks(qtype)

    grade = _coerce_grade(payload.get("grade"), grade_hint)
    subject = _normalize_subject(payload.get("subject"), subject_hint)
    topic = _normalize_short_text(payload.get("topic")) or "General"
    subtopic = _normalize_short_text(payload.get("subtopic")) or None

    answer = _normalize_block_text(payload.get("answer"), preserve_paragraphs=False)
    if qtype in {"mcq", "image_mcq"}:
        answer = _resolve_mcq_answer(answer, options)

    expected_points = _coerce_text_list(payload.get("expected_points"))
    explanation = _normalize_block_text(payload.get("explanation"), preserve_paragraphs=True)
    if qtype in SUBJECTIVE_TYPES and not expected_points:
        expected_points = _extract_expected_points(answer, explanation)

    accepted_answers = _coerce_text_list(payload.get("accepted_answers"))
    if answer:
        accepted_answers.append(answer)
    if qtype in SUBJECTIVE_TYPES and expected_points:
        accepted_answers.extend(expected_points[:3])

    deduped_answers = []
    seen = set()
    for candidate in accepted_answers:
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped_answers.append(candidate)
    accepted_answers = deduped_answers

    if qtype == "fill_blank":
        question = _ensure_fill_blank_text(question, accepted_answers)

    if not answer:
        if qtype in {"mcq", "image_mcq"} and options:
            answer = options[0]
        elif qtype in SUBJECTIVE_TYPES:
            answer = "Answers may vary. Refer to expected points."
        elif accepted_answers:
            answer = accepted_answers[0]

    if not accepted_answers and answer:
        accepted_answers = [answer]

    difficulty = _coerce_difficulty(payload.get("difficulty"), grade, marks)
    hints = _normalize_hints(payload.get("hints"), payload.get("hint"))
    tags = _coerce_text_list(payload.get("tags"))
    raw_snippet = _normalize_block_text(payload.get("raw_extracted_snippet"), preserve_paragraphs=True)
    if not raw_snippet:
        raw_snippet = "\n\n".join(part for part in [passage, question] if part).strip()[:600]

    confidence = min(1.0, max(0.0, _safe_float(payload.get("confidence"), default=0.65)))
    parse_notes = _normalize_short_text(payload.get("parse_notes")) or None
    board = _normalize_short_text(payload.get("board")) or None
    medium = _normalize_short_text(payload.get("medium")) or "en"
    image = _normalize_image(payload.get("image"))

    provided_id = _normalize_short_text(payload.get("id"))
    question_id = provided_id or _build_question_id(
        source_doc=source_doc,
        subject=subject,
        grade=grade,
        topic=topic,
        question=question,
        sequence=sequence,
    )

    language_variants = payload.get("language_variants")
    if not isinstance(language_variants, dict):
        language_variants = {}

    normalized = {
        "id": question_id,
        "source_doc": source_doc,
        "subject": subject,
        "grade": grade,
        "board": board,
        "medium": medium,
        "type": qtype,
        "marks": marks,
        "difficulty": difficulty,
        "topic": topic,
        "subtopic": subtopic,
        "passage": passage,
        "instructions": instructions,
        "question": question,
        "options": options,
        "answer": answer,
        "accepted_answers": accepted_answers,
        "expected_points": expected_points,
        "explanation": explanation,
        "image": image,
        "hints": hints,
        "tags": tags,
        "language_variants": language_variants,
        "confidence": confidence,
        "raw_extracted_snippet": raw_snippet,
        "parse_notes": parse_notes,
    }

    return normalized


def _split_long_block(block: str, max_chars: int) -> List[str]:
    if len(block) <= max_chars:
        return [block]

    paragraphs = [p for p in block.split("\n\n") if p.strip()]
    if len(paragraphs) <= 1:
        return [block[i : i + max_chars] for i in range(0, len(block), max_chars)]

    out = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            out.append(current.strip())
        current = para
    if current:
        out.append(current.strip())
    return out


def _split_question_blocks(text: str) -> List[str]:
    starts = [m.start() for m in QUESTION_START_RE.finditer(text)]
    if len(starts) < 2:
        return [text]

    blocks: List[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(text)
        block = text[start:end].strip()
        if block:
            blocks.append(block)
    return blocks or [text]


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF while preserving paragraph structure."""
    pages: List[str] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = _normalize_block_text(
                    page.extract_text(layout=True, x_tolerance=2, y_tolerance=3),
                    preserve_paragraphs=True,
                )

                if len(page_text) < 40:
                    fallback = _normalize_block_text(page.extract_text(), preserve_paragraphs=True)
                    if len(fallback) > len(page_text):
                        page_text = fallback

                if len(page_text) < 40:
                    try:
                        import pytesseract

                        image = page.to_image(resolution=220).original
                        ocr_text = _normalize_block_text(
                            pytesseract.image_to_string(image),
                            preserve_paragraphs=True,
                        )
                        if len(ocr_text) > len(page_text):
                            page_text = ocr_text
                    except Exception:
                        pass

                if page_text:
                    pages.append(page_text)
    except Exception as e:
        print(f"PDF extraction error: {e}")

    return "\n\n".join(pages).strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from Word documents while keeping paragraph boundaries."""
    chunks: List[str] = []
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            value = _normalize_block_text(para.text, preserve_paragraphs=False)
            chunks.append(value if value else "")
    except Exception as e:
        print(f"DOCX extraction error: {e}")
    return _normalize_block_text("\n".join(chunks), preserve_paragraphs=True)


def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF or Word document."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, max_tokens: int = 1100) -> List[str]:
    """Split extracted text into Groq-friendly chunks."""
    normalized = _normalize_block_text(text, preserve_paragraphs=True)
    if not normalized:
        return []

    max_chars = max(1200, max_tokens * 4)
    question_blocks = _split_question_blocks(normalized)
    chunks: List[str] = []
    current = ""

    for block in question_blocks:
        for sub_block in _split_long_block(block, max_chars):
            candidate = f"{current}\n\n{sub_block}".strip() if current else sub_block
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                chunks.append(current.strip())
            current = sub_block

    if current:
        chunks.append(current.strip())

    return chunks


GROQ_PARSE_PROMPT = """You extract exam questions from OCR text and output JSON only.

Return exactly:
{"questions":[...]}

Each question object must include these keys:
"id","source_doc","subject","grade","board","medium","type","marks","difficulty","topic","subtopic",
"passage","instructions","question","options","answer","accepted_answers","expected_points","explanation",
"image","hints","tags","language_variants","confidence","raw_extracted_snippet","parse_notes"

Rules:
1. Preserve passage paragraphs exactly (use \\n and blank lines where needed).
2. If multiple questions share one passage, repeat that passage in each question object.
3. Allowed type values: mcq, image_mcq, fill_blank, short_answer, descriptive.
4. For MCQ/image_mcq, answer must be option text (not letter labels).
5. For fill_blank, include ____ in the question text.
6. answer must never be null. For descriptive, provide concise model answer + expected_points.
7. Output valid JSON only, no markdown, no extra commentary.
"""


def parse_questions_with_groq(
    text: str,
    source_doc: str,
    grade: Optional[int] = None,
    subject: Optional[str] = None,
) -> List[Dict]:
    """Parse questions from extracted text using Groq with post-normalization."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")

    normalized_text = _normalize_block_text(text, preserve_paragraphs=True)
    if not normalized_text:
        return []

    chunks = chunk_text(normalized_text)
    if not chunks:
        return []

    client = Groq(api_key=GROQ_API_KEY)
    all_questions: List[Dict] = []
    seen_content_keys = set()

    for i, chunk in enumerate(chunks):
        try:
            if i > 0:
                time.sleep(1)

            metadata = {
                "source_doc": source_doc,
                "grade_hint": grade,
                "subject_hint": subject,
                "chunk_index": i + 1,
                "total_chunks": len(chunks),
            }
            prompt = (
                f"{GROQ_PARSE_PROMPT}\n\n"
                f"Metadata:\n{json.dumps(metadata, ensure_ascii=False)}\n\n"
                f"Extracted Text:\n{chunk}"
            )

            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Return only valid JSON. No markdown."},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            raw_questions = data.get("questions", [])
            if isinstance(raw_questions, dict):
                raw_questions = [raw_questions]
            if not isinstance(raw_questions, list):
                raw_questions = []

            for raw in raw_questions:
                if not isinstance(raw, dict):
                    continue
                normalized = _normalize_question_payload(
                    payload=raw,
                    source_doc=source_doc,
                    sequence=len(all_questions) + 1,
                    grade_hint=grade,
                    subject_hint=subject,
                )
                content_key = (
                    f"{normalized.get('subject','').casefold()}|"
                    f"{normalized.get('grade')}|"
                    f"{normalized.get('passage','').casefold()}|"
                    f"{normalized.get('question','').casefold()}"
                )
                if content_key in seen_content_keys:
                    continue
                seen_content_keys.add(content_key)
                all_questions.append(normalized)
        except Exception as e:
            print(f"Groq parsing error for chunk {i + 1}/{len(chunks)}: {e}")
            continue

    # Ensure IDs are unique even when model repeats IDs.
    used_ids = set()
    for question in all_questions:
        base = question.get("id") or _build_question_id(
            source_doc=source_doc,
            subject=question.get("subject", "Other"),
            grade=_safe_int(question.get("grade"), default=3) or 3,
            topic=question.get("topic", "General"),
            question=question.get("question", ""),
            sequence=len(used_ids) + 1,
        )
        candidate = base
        suffix = 1
        while candidate in used_ids:
            candidate = f"{base}_{suffix:02d}"
            suffix += 1
        question["id"] = candidate
        used_ids.add(candidate)

    return all_questions


def validate_question(question: Dict) -> bool:
    """Validate normalized question payload before approval."""
    required = ["subject", "grade", "type", "question"]
    for field in required:
        value = question.get(field)
        if _is_nullish(value):
            return False

    grade = _safe_int(question.get("grade"), default=None)
    if grade is None or grade < 1 or grade > 12:
        return False

    qtype = _infer_type(
        raw_type=question.get("type"),
        options=_normalize_options(question.get("options")),
        question=_normalize_block_text(question.get("question"), preserve_paragraphs=True),
        marks=_safe_int(question.get("marks"), default=1) or 1,
    )

    options = _normalize_options(question.get("options"))
    if qtype in {"mcq", "image_mcq"} and len(options) < 2:
        return False

    text = _normalize_block_text(question.get("question"), preserve_paragraphs=True)
    if qtype == "fill_blank" and "____" not in text:
        return False

    answer = _normalize_short_text(question.get("answer"))
    accepted_answers = _coerce_text_list(question.get("accepted_answers"))
    if qtype in OBJECTIVE_TYPES and not answer and not accepted_answers:
        return False

    return True
