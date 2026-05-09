"""
Batch Study Card Generation Script.
Generates comprehensive concept cards for all subjects and grades using Groq.
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List

logger = logging.getLogger("batch_cards")
logging.basicConfig(level=logging.INFO)

SUBJECTS = ["Mathematics", "Science", "English", "Environmental Science", "Social Science"]
# Focus on common grades first to ensure quality
GRADES = [1, 3, 5, 6, 7, 8, 9, 10]

async def generate_cards_for_subject_grade(subject: str, grade: int, count: int = 10) -> List[dict]:
    """Uses Groq to generate concept cards without needing source text."""
    try:
        from app.core.groq_translator import get_client
        client = get_client()
        if not client:
            return []

        prompt = f"""Generate {count} educational concept cards for Grade {grade} {subject} (India NCERT curriculum).
Return ONLY a valid JSON array of objects. Each object must have:
- "title": Name of the concept
- "definition": Clear, simple explanation (1-2 sentences)
- "example": A real-world example or application
- "formula": Mathematical/Scientific formula if any (else null)
- "tip": A helpful study tip or mnemonic
- "chapter": The name of the chapter this belongs to

Ensure the content is age-appropriate for Grade {grade}.
"""
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096,
        )
        
        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw)
        cards = []
        for c in data:
            cards.append({
                "id":         str(uuid.uuid4()),
                "subject":    subject,
                "grade":      grade,
                "chapter":    c.get("chapter", "General Concepts"),
                "title":      c.get("title", ""),
                "definition": c.get("definition", ""),
                "example":    c.get("example", ""),
                "formula":    c.get("formula"),
                "tip":        c.get("tip", ""),
                "source":     "batch_ai_generated",
                "created_at": datetime.utcnow().isoformat(),
                "synced":     0
            })
        return cards
    except Exception as e:
        logger.error(f"Failed generation for {subject} G{grade}: {e}")
        return []

async def run_batch():
    from app.core.database import async_db
    col = async_db["study_cards"]
    
    total = 0
    for subject in SUBJECTS:
        for grade in GRADES:
            # Skip EVS for high grades, skip Science for low grades
            if subject == "Environmental Science" and grade > 5: continue
            if subject == "Science" and grade <= 5: continue
            
            logger.info(f"Generating cards for {subject} Grade {grade}...")
            cards = await generate_cards_for_subject_grade(subject, grade)
            if cards:
                try:
                    await col.insert_many(cards, ordered=False)
                    logger.info(f"  Inserted {len(cards)} cards.")
                    total += len(cards)
                except Exception as e:
                    logger.error(f"  Insert failed: {e}")
            
            # Pacing to avoid rate limits
            await asyncio.sleep(2)
            
    logger.info(f"Batch complete. Total cards generated: {total}")

if __name__ == "__main__":
    asyncio.run(run_batch())
