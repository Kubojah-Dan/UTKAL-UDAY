"""
Study Cards — backend core module.
Generates NCERT-aligned concept cards from chapter text using Groq API.
Cards are stored in MongoDB `study_cards` collection and synced offline.
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger("study_cards")

# ── Formula reference sheets (offline, no AI needed) ──────────────────────

FORMULA_SHEETS = {
    "Mathematics": {
        8: [
            {"name": "Area of Rectangle",     "formula": "A = l × w"},
            {"name": "Area of Triangle",      "formula": "A = ½ × b × h"},
            {"name": "Area of Circle",        "formula": "A = π × r²"},
            {"name": "Circumference",         "formula": "C = 2πr"},
            {"name": "Pythagoras Theorem",    "formula": "a² + b² = c²"},
            {"name": "Simple Interest",       "formula": "SI = (P × R × T) / 100"},
            {"name": "Compound Interest",     "formula": "A = P(1 + R/100)ⁿ"},
            {"name": "Volume of Cuboid",      "formula": "V = l × w × h"},
        ],
        9: [
            {"name": "Quadratic Formula",     "formula": "x = (-b ± √(b²-4ac)) / 2a"},
            {"name": "Distance Formula",      "formula": "d = √[(x₂-x₁)² + (y₂-y₁)²]"},
            {"name": "Midpoint Formula",      "formula": "M = ((x₁+x₂)/2, (y₁+y₂)/2)"},
            {"name": "Slope of a Line",       "formula": "m = (y₂-y₁)/(x₂-x₁)"},
            {"name": "Area of Triangle (coord)","formula":"A = ½|x₁(y₂-y₃)+x₂(y₃-y₁)+x₃(y₁-y₂)|"},
            {"name": "Heron's Formula",       "formula": "A = √[s(s-a)(s-b)(s-c)], s=(a+b+c)/2"},
        ],
        10: [
            {"name": "sin²θ + cos²θ",         "formula": "= 1"},
            {"name": "1 + tan²θ",             "formula": "= sec²θ"},
            {"name": "1 + cot²θ",             "formula": "= cosec²θ"},
            {"name": "sin(30°)",              "formula": "= 1/2"},
            {"name": "cos(60°)",              "formula": "= 1/2"},
            {"name": "tan(45°)",              "formula": "= 1"},
            {"name": "Arithmetic Progression nth term", "formula": "aₙ = a + (n-1)d"},
            {"name": "Sum of AP",             "formula": "Sₙ = n/2 × [2a + (n-1)d]"},
        ],
    },
    "Physics": {
        9: [
            {"name": "Newton's 2nd Law",      "formula": "F = m × a"},
            {"name": "Work Done",             "formula": "W = F × d × cos θ"},
            {"name": "Kinetic Energy",        "formula": "KE = ½mv²"},
            {"name": "Potential Energy",      "formula": "PE = mgh"},
            {"name": "Power",                 "formula": "P = W/t"},
            {"name": "Speed",                 "formula": "v = d/t"},
            {"name": "Acceleration",          "formula": "a = (v-u)/t"},
        ],
        10: [
            {"name": "Ohm's Law",             "formula": "V = I × R"},
            {"name": "Electric Power",        "formula": "P = VI = I²R = V²/R"},
            {"name": "Lens Formula",          "formula": "1/f = 1/v - 1/u"},
            {"name": "Mirror Formula",        "formula": "1/f = 1/v + 1/u"},
            {"name": "Magnification (lens)",  "formula": "m = h'/h = v/u"},
            {"name": "Snell's Law",           "formula": "n₁sin θ₁ = n₂sin θ₂"},
        ],
    },
    "Chemistry": {
        9: [
            {"name": "Molar Mass",            "formula": "M = mass (g) / moles (mol)"},
            {"name": "Density",               "formula": "ρ = mass / volume"},
            {"name": "Avogadro's Number",     "formula": "Nₐ = 6.022 × 10²³ particles/mol"},
        ],
        10: [
            {"name": "pH Scale",              "formula": "pH = -log[H⁺]; pH<7 acid, pH>7 base"},
            {"name": "Neutralisation",        "formula": "Acid + Base → Salt + Water"},
        ],
    },
}


def get_formula_sheet(subject: str, grade: int) -> List[dict]:
    """Return pre-built formula sheet for a subject/grade combo."""
    subject_sheets = FORMULA_SHEETS.get(subject, {})
    # Find the closest grade at or below requested grade
    available = sorted([g for g in subject_sheets if g <= grade], reverse=True)
    if not available:
        return []
    return subject_sheets[available[0]]


# ── Concept Card Generation (Groq) ─────────────────────────────────────────

async def generate_study_cards_from_text(
    chapter_text: str,
    subject: str,
    grade: int,
    chapter: str,
    max_cards: int = 15,
) -> List[dict]:
    """
    Use Groq to extract concept cards from chapter text.
    Each card: {title, definition, example, formula, tip}
    Falls back to empty list if Groq unavailable.
    """
    try:
        from app.core.groq_translator import groq_client
        if groq_client is None:
            return []

        prompt = f"""Extract {max_cards} key concept cards from this {subject} Grade {grade} chapter text.
Return a JSON array only. Each object:
- "title": concept name (short)
- "definition": 1-2 sentence clear definition
- "example": concrete example or application
- "formula": mathematical/chemical formula if applicable (else null)
- "tip": memory tip or common misconception warning

Chapter text:
{chapter_text[:3000]}

Return only the raw JSON array."""

        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        cards_data = json.loads(raw)

        cards = []
        for c in cards_data:
            cards.append({
                "id":         str(uuid.uuid4()),
                "subject":    subject,
                "grade":      grade,
                "chapter":    chapter,
                "title":      c.get("title", ""),
                "definition": c.get("definition", ""),
                "example":    c.get("example", ""),
                "formula":    c.get("formula"),
                "tip":        c.get("tip", ""),
                "source":     "groq_extracted",
                "created_at": datetime.utcnow().isoformat(),
                "synced":     0,
            })
        return cards

    except Exception as e:
        logger.warning(f"Study card generation failed: {e}")
        return []


async def save_study_cards(cards: List[dict]) -> int:
    """Upsert study cards into MongoDB."""
    if not cards:
        return 0
    try:
        from app.core.database import async_db
        col = async_db["study_cards"]
        result = await col.insert_many(cards, ordered=False)
        return len(result.inserted_ids)
    except Exception as e:
        logger.error(f"Failed to save study cards: {e}")
        return 0


async def get_study_cards(
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    chapter: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """Fetch study cards from MongoDB."""
    try:
        from app.core.database import async_db
        col = async_db["study_cards"]
        query = {}
        if subject:  query["subject"] = subject
        if grade:    query["grade"]   = grade
        if chapter:  query["chapter"] = chapter
        cursor = col.find(query).limit(limit)
        rows = await cursor.to_list(length=limit)
        for r in rows:
            r.pop("_id", None)
        return rows
    except Exception as e:
        logger.error(f"Failed to fetch study cards: {e}")
        return []
