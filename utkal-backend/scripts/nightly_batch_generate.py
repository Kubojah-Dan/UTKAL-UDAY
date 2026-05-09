"""
Nightly batch question generation script.
Generates 50 new questions per grade per subject using Groq API,
auto-translates them, and pushes to MongoDB.

Usage:
  python -m app.scripts.nightly_batch_generate
  (or trigger via POST /admin/generate-batch)
"""
import asyncio
import json
import logging
import os
import random
import uuid
from datetime import datetime

logger = logging.getLogger("batch_generate")
logging.basicConfig(level=logging.INFO)


SUBJECTS = ["Mathematics", "Science", "English", "Environmental Science", "Social Science"]
GRADES   = list(range(1, 13))
BATCH_SIZE = 25

# Languages for auto-translation
TARGET_LANGS = os.getenv("UTKAL_STARTUP_LOCALIZATION_LANGUAGES", "hi,ta,te,or").split(",")


async def generate_batch_for_grade_subject(grade: int, subject: str, count: int = BATCH_SIZE) -> list:
    """
    Generate `count` questions for a grade/subject using Groq API.
    Falls back to procedural generators if Groq is unavailable.
    """
    try:
        from app.core.groq_translator import get_client
        client = get_client()
        if client is None:
            raise ImportError("Groq client not available")

        prompt = f"""Generate {count} educational questions for Grade {grade} {subject} (NCERT curriculum, India).
Aim for a mix of Multiple Choice (MCQ) and Short Answer questions.

Return ONLY a valid JSON array of objects. Each object must have:
- "question": string
- "type": "mcq" or "short_answer"
- "options": array of 4 strings (only for mcq, else empty array [])
- "answer": string (for mcq, MUST match one option; for short_answer, the correct value)
- "topic": string
- "hint": string
- "explanation": string
- "difficulty": "easy" | "medium" | "hard"
- "bloom_level": integer 1-6

Return only the raw JSON array, no markdown or prose.
"""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=8192,
        )
        raw = response.choices[0].message.content.strip()
        
        # Robust JSON cleaning
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        
        # Try to fix truncated JSON by finding the last closing bracket
        if not raw.endswith("]"):
            last_bracket = raw.rfind("}")
            if last_bracket != -1:
                raw = raw[:last_bracket+1] + "]"
        
        try:
            questions = json.loads(raw)
            return questions
        except json.JSONDecodeError as je:
            logger.warning(f"Groq JSON parse error: {je}. Raw length: {len(raw)}")
            # One more attempt: try to find the start and end of the array
            start = raw.find("[")
            end = raw.rfind("]")
            if start != -1 and end != -1:
                try:
                    return json.loads(raw[start:end+1])
                except:
                    pass
            raise je
    except Exception as e:
        logger.warning(f"Groq generation failed ({e}), falling back to procedural generator")
        return _procedural_fallback(grade, subject, count)


def _procedural_fallback(grade: int, subject: str, count: int) -> list:
    """Use local procedural generators as fallback."""
    try:
        if subject == "Mathematics":
            from app.generators.math_generator import generate_questions_for_grade
            return generate_questions_for_grade(grade, count_per_topic=max(5, count // 10))[:count]
        elif subject in ("Science", "Environmental Science"):
            from app.generators.science_generator import generate_questions_for_grade
            return generate_questions_for_grade(grade, count)[:count]
        elif subject == "Social Science":
            from app.generators.social_science_generator import generate_questions_for_grade
            return generate_questions_for_grade(grade, count)[:count]
        else:
            return []
    except Exception as e:
        logger.error(f"Procedural fallback failed: {e}")
        return []


async def translate_questions(questions: list, langs: list) -> list:
    """Auto-translate all questions to target languages."""
    try:
        from app.core.question_localization import queue_question_localization
        for q in questions:
            queue_question_localization(q, target_langs=langs)
    except Exception as e:
        logger.warning(f"Translation queue failed: {e}")
    return questions


async def push_to_mongodb(questions: list, grade: int, subject: str):
    """Upsert generated questions into MongoDB."""
    try:
        from app.core.database import questions_collection
        if not questions:
            return 0

        docs = []
        for q in questions:
            opts = q.get("options") or []
            if not isinstance(opts, list):
                opts = []
            
            # Auto-detect type if not provided or inconsistent
            suggested_type = q.get("type", "mcq")
            if suggested_type == "mcq" and len(opts) < 2:
                suggested_type = "short_answer"

            doc = {
                "id":         str(uuid.uuid4()),
                "subject":    subject,
                "grade":      grade,
                "question":   q.get("question", ""),
                "options":    opts,
                "answer":     q.get("answer", ""),
                "topic":      q.get("topic", subject),
                "skill_label":q.get("topic", subject),
                "hint":       q.get("hint", ""),
                "explanation":q.get("explanation", ""),
                "difficulty": q.get("difficulty", "medium"),
                "bloom_level":q.get("bloom_level", 1),
                "type":       suggested_type,
                "approved":   True,
                "status":     "active",
                "source":     "batch_generated",
                "generated_at": datetime.utcnow().isoformat(),
            }
            docs.append(doc)

        if not docs:
            return 0

        try:
            result = await questions_collection.insert_many(docs, ordered=False)
            inserted = len(result.inserted_ids)
            logger.info(f"  Inserted {inserted} questions for Grade {grade} {subject}")
            return inserted
        except Exception as bulk_err:
            logger.error(f"Bulk insert failed for Grade {grade} {subject}: {bulk_err}")
            # Fallback to individual inserts if bulk fails (e.g. duplicate IDs or connection blip)
            count_success = 0
            for d in docs:
                try:
                    await questions_collection.insert_one(d)
                    count_success += 1
                except Exception:
                    continue
            return count_success

    except Exception as e:
        logger.error(f"MongoDB push failed for Grade {grade} {subject}: {e}")
        return 0


async def run_batch(grades=None, subjects=None, count_per=BATCH_SIZE, translate=True):
    """
    Main entry point: generate + translate + push questions for all grade/subject combos.

    Returns a summary dict.
    """
    grades   = grades   or GRADES
    subjects = subjects or SUBJECTS
    summary  = {"total_generated": 0, "by_grade_subject": {}}

    for grade in grades:
        for subject in subjects:
            logger.info(f"Generating {count_per} questions: Grade {grade} {subject}...")
            try:
                questions = await generate_batch_for_grade_subject(grade, subject, count_per)
                if translate and questions:
                    await translate_questions(questions, TARGET_LANGS)
                inserted = await push_to_mongodb(questions, grade, subject)
                summary["total_generated"] += inserted
                summary["by_grade_subject"][f"Grade {grade} {subject}"] = inserted
                
                # Add pacing delay to avoid hitting rate limits
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"Failed Grade {grade} {subject}: {e}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_batch())
