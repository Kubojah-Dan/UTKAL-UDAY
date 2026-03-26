"""
AI batch question generator using Groq API.
Generates 100 questions per call, caches to MongoDB to avoid re-generation.
"""
import json
import os
import uuid
from groq import AsyncGroq

groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY", ""))


def _parse_response(response) -> list:
    try:
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        data = json.loads(content.strip())
        # Handle both array and {"questions": [...]} formats
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("questions", "items", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []
    except Exception as e:
        print(f"[ai_generator] parse error: {e}")
        return []


def _normalize_question(q: dict, grade: int, subject: str, topic: str) -> dict:
    """Ensure every generated question has required fields."""
    difficulty_map = {1: "easy", 2: "easy", 3: "easy", 4: "medium", 5: "medium"}
    diff_raw = q.get("difficulty", 3)
    if isinstance(diff_raw, int):
        difficulty = difficulty_map.get(diff_raw, "hard")
    else:
        difficulty = str(diff_raw).lower() if str(diff_raw).lower() in ("easy", "medium", "hard") else "medium"

    qtype = str(q.get("type", "mcq")).lower().replace("-", "_").replace(" ", "_")
    if qtype not in ("mcq", "fill_blank", "true_false", "short_answer"):
        qtype = "mcq"

    return {
        "id": f"AI-{subject[:3].upper()}-G{grade}-{uuid.uuid4().hex[:8]}",
        "source": "ai_generated",
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "skill_label": topic,
        "skill_id": f"ai-{subject.lower()[:3]}-g{grade}-{topic.lower().replace(' ', '-')}",
        "difficulty": difficulty,
        "type": qtype,
        "question": str(q.get("question", "")),
        "options": q.get("options") or [],
        "answer": str(q.get("answer", "")),
        "accepted_answers": [str(q.get("answer", ""))],
        "explanation": str(q.get("explanation", "")),
        "hint": str(q.get("hint", "")),
        "bloom_level": q.get("bloom_level", 3),
        "bloom_label": q.get("bloom_label", "Apply"),
        "approved": True,
        "status": "active",
        "language": "en",
        "media": [],
    }


async def _save_to_mongodb(questions: list):
    try:
        from app.core.database import questions_collection
        if not questions:
            return
        ops = []
        from pymongo import UpdateOne
        for q in questions:
            ops.append(UpdateOne({"id": q["id"]}, {"$setOnInsert": q}, upsert=True))
        questions_collection.bulk_write(ops, ordered=False)
        print(f"[ai_generator] saved {len(questions)} questions to MongoDB")
    except Exception as e:
        print(f"[ai_generator] MongoDB save error: {e}")


async def batch_generate_questions(grade: int, subject: str, topic: str, count: int = 50) -> list:
    """
    Generate questions via Groq. Single API call = up to 50 questions.
    Results are cached in MongoDB so we never regenerate the same topic.
    """
    # Check cache first
    try:
        from app.core.database import questions_collection
        existing_count = questions_collection.count_documents({
            "source": "ai_generated", "grade": grade, "subject": subject, "topic": topic
        })
        if existing_count >= count:
            cursor = questions_collection.find({
                "source": "ai_generated", "grade": grade, "subject": subject, "topic": topic
            }).limit(count)
            cached = list(cursor)
            for q in cached:
                q.pop("_id", None)
            print(f"[ai_generator] cache hit: {len(cached)} questions for {subject} G{grade} {topic}")
            return cached
    except Exception as e:
        print(f"[ai_generator] cache check error: {e}")

    prompt = (
        f"Generate {count} varied questions for Grade {grade} {subject} on topic: {topic}. "
        f"Include MCQ (40%), fill-in-blank (30%), true/false (20%), short answer (10%). "
        f"Output a JSON array only. Each item: "
        f'{{\"question\": str, \"type\": \"mcq\"|\"fill_blank\"|\"true_false\"|\"short_answer\", '
        f'\"options\": list or null, \"answer\": str, \"difficulty\": 1-5, \"explanation\": str}}'
    )

    try:
        response = await groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert educator. Output only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        raw = _parse_response(response)
        questions = [_normalize_question(q, grade, subject, topic) for q in raw if q.get("question")]
        await _save_to_mongodb(questions)
        return questions
    except Exception as e:
        print(f"[ai_generator] Groq error: {e}")
        return []
