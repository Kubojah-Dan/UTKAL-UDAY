"""
Seed script for Utkal Uday Study Notes.
Populates Grade 9 NCERT-aligned concept cards for Math, Science, Social Science, and English.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import datetime

MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "utkal_uday"

NOTES_DATA = [
    # ── MATHEMATICS ────────────────────────────────────────────────────────
    {
        "subject": "Mathematics",
        "grade": 9,
        "chapter": "Number Systems",
        "title": "Rational vs Irrational Numbers",
        "content": "A rational number can be written as p/q (q≠0). An irrational number cannot. Examples: √2, π, 0.101101110...",
        "audio_text": "A rational number can be expressed as a fraction p over q where q is not zero. Irrational numbers like root 2 or pi cannot be expressed as simple fractions.",
        "tags": ["Numbers", "NCERT"]
    },
    {
        "subject": "Mathematics",
        "grade": 9,
        "chapter": "Polynomials",
        "title": "Remainder Theorem",
        "content": "Let p(x) be any polynomial of degree ≥ 1 and let 'a' be any real number. If p(x) is divided by (x-a), the remainder is p(a).",
        "audio_text": "The Remainder Theorem states that if you divide a polynomial p of x by x minus a, the remainder is simply the value of the polynomial at a.",
        "tags": ["Algebra", "Polynomials"]
    },
    {
        "subject": "Mathematics",
        "grade": 9,
        "chapter": "Lines and Angles",
        "title": "Parallel Lines Property",
        "content": "If a transversal intersects two parallel lines, then each pair of corresponding angles is equal.",
        "audio_text": "When a line crosses two parallel lines, the corresponding angles are equal. This is a fundamental property in geometry.",
        "tags": ["Geometry", "Angles"]
    },

    # ── SCIENCE ────────────────────────────────────────────────────────────
    {
        "subject": "Science",
        "grade": 9,
        "chapter": "Matter in Our Surroundings",
        "title": "States of Matter",
        "content": "Matter exists in three states: Solid (fixed shape/volume), Liquid (fixed volume/no shape), and Gas (no fixed shape/volume).",
        "audio_text": "Matter comes in three primary states: solids, liquids, and gases. Solids have a fixed shape, liquids flow to fit their container, and gases expand to fill the entire space.",
        "tags": ["Chemistry", "Matter"]
    },
    {
        "subject": "Science",
        "grade": 9,
        "chapter": "The Fundamental Unit of Life",
        "title": "The Cell",
        "content": "The cell is the basic structural and functional unit of life. Robert Hooke discovered cells in 1665.",
        "audio_text": "The cell is known as the basic unit of life. It was first discovered by Robert Hooke in 1665 using a primitive microscope.",
        "tags": ["Biology", "Cell"]
    },
    {
        "subject": "Science",
        "grade": 9,
        "chapter": "Motion",
        "title": "Distance vs Displacement",
        "content": "Distance is the total path length covered. Displacement is the shortest straight-line distance between initial and final points.",
        "audio_text": "Distance is how much ground an object has covered. Displacement is the straight line change in position from start to finish.",
        "tags": ["Physics", "Motion"]
    },

    # ── SOCIAL SCIENCE ─────────────────────────────────────────────────────
    {
        "subject": "Social Science",
        "grade": 9,
        "chapter": "The French Revolution",
        "title": "The Three Estates",
        "content": "French society was divided into: 1st Estate (Clergy), 2nd Estate (Nobility), and 3rd Estate (Commoners/Peasants).",
        "audio_text": "Before the revolution, French society was split into three estates. The first was the clergy, the second the nobility, and the third estate included everyone else, from merchants to peasants.",
        "tags": ["History", "Revolution"]
    },
    {
        "subject": "Social Science",
        "grade": 9,
        "chapter": "Physical Features of India",
        "title": "The Himalayan Mountains",
        "content": "The Himalayas are geologically young and structurally fold mountains. They stretch over the northern borders of India.",
        "audio_text": "The Himalayas are young fold mountains that protect India's northern border. They are among the highest and most rugged mountain ranges in the world.",
        "tags": ["Geography", "India"]
    },

    # ── ENGLISH ────────────────────────────────────────────────────────────
    {
        "subject": "English",
        "grade": 9,
        "chapter": "Grammar",
        "title": "Tenses: Present Perfect",
        "content": "Used for actions that happened at an indefinite time in the past or began in the past and continue to the present. Form: has/have + past participle.",
        "audio_text": "We use the present perfect tense for actions that connect the past to the present. It is formed using have or has followed by the past participle of the verb.",
        "tags": ["Grammar", "Writing"]
    },
    {
        "subject": "English",
        "grade": 9,
        "chapter": "Literature: The Fun They Had",
        "title": "Theme: Future of Education",
        "content": "The story contrasts mechanical, home-based learning with the old school system involving human teachers and social interaction.",
        "audio_text": "The Fun They Had explores a future where children learn alone from machines, making them miss the social fun of old schools with human teachers.",
        "tags": ["Literature", "Isaac Asimov"]
    }
]

async def seed_notes():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    col = db["study_cards"]
    
    print(f"Cleaning existing notes for Grade 9...")
    await col.delete_many({"grade": 9})
    
    notes_to_insert = []
    for data in NOTES_DATA:
        note = {
            "id": str(uuid.uuid4()),
            "subject": data["subject"],
            "grade": data["grade"],
            "chapter": data["chapter"],
            "title": data["title"],
            "content": data["content"],
            "audio_text": data["audio_text"],
            "tags": data["tags"],
            "created_at": datetime.datetime.utcnow().isoformat(),
            "approved": True
        }
        notes_to_insert.append(note)
    
    if notes_to_insert:
        result = await col.insert_many(notes_to_insert)
        print(f"Successfully seeded {len(result.inserted_ids)} Grade 9 concept cards!")
    else:
        print("No notes to seed.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_notes())
