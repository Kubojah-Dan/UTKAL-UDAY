"""
Seed script to populate initial Study Cards for various subjects and grades.
"""
import asyncio
import uuid
from datetime import datetime
from app.core.database import async_db

INITIAL_CARDS = [
    # Science - Grade 9
    {
        "subject": "Science",
        "grade": 9,
        "chapter": "Cell - The Fundamental Unit of Life",
        "title": "Mitochondria",
        "definition": "Known as the powerhouse of the cell, these organelles generate most of the cell's supply of adenosine triphosphate (ATP).",
        "example": "Active cells like muscle cells have thousands of mitochondria to provide energy for movement.",
        "formula": None,
        "tip": "Mitochondria have their own DNA and ribosomes, unlike most other organelles!",
    },
    {
        "subject": "Science",
        "grade": 9,
        "chapter": "Motion",
        "title": "Velocity",
        "definition": "The rate of change of displacement of an object with respect to time, including its direction.",
        "example": "A car traveling at 60 km/h towards the North.",
        "formula": "v = Δs / Δt",
        "tip": "Speed is just how fast; Velocity is how fast AND in what direction.",
    },
    # Social Science - Grade 9
    {
        "subject": "Social Science",
        "grade": 9,
        "chapter": "Democratic Rights",
        "title": "Right to Equality",
        "definition": "A fundamental right that ensures equal treatment of all citizens before the law and prohibits discrimination.",
        "example": "Untouchability has been abolished and its practice is a punishable crime.",
        "formula": None,
        "tip": "This is covered under Articles 14-18 of the Indian Constitution.",
    },
    {
        "subject": "Social Science",
        "grade": 9,
        "chapter": "Physical Features of India",
        "title": "The Himalayas",
        "definition": "Geologically young and structurally fold mountains stretching over the northern borders of India.",
        "example": "Mount Everest, the highest peak in the world, is part of this range.",
        "formula": None,
        "tip": "They act as a giant barrier against cold winds from Central Asia.",
    },
    # English - Grade 9
    {
        "subject": "English",
        "grade": 9,
        "chapter": "Grammar - Tenses",
        "title": "Present Perfect Tense",
        "definition": "Used to describe an action that happened at an unspecified time in the past or began in the past and continues to the present.",
        "example": "I have finished my homework. (The action is complete but the time isn't specified).",
        "formula": "Subject + has/have + past participle (V3)",
        "tip": "Don't use it with specific time expressions like 'yesterday' or 'last week'.",
    },
    {
        "subject": "English",
        "grade": 9,
        "chapter": "Figures of Speech",
        "title": "Metaphor",
        "definition": "A figure of speech that describes an object or action in a way that isn’t literally true, but helps explain an idea or make a comparison.",
        "example": "The classroom was a zoo. (Comparing classroom chaos to a zoo directly).",
        "formula": None,
        "tip": "Unlike a Simile, a Metaphor does NOT use 'like' or 'as'.",
    }
]

async def seed():
    print("Seeding Study Cards...")
    col = async_db["study_cards"]
    
    # Add metadata fields
    docs = []
    for c in INITIAL_CARDS:
        c["id"] = str(uuid.uuid4())
        c["source"] = "seed_script"
        c["created_at"] = datetime.utcnow().isoformat()
        c["synced"] = 0
        docs.append(c)
    
    try:
        # Clear existing seeded cards to avoid duplicates if re-run
        await col.delete_many({"source": "seed_script"})
        result = await col.insert_many(docs)
        print(f"Successfully seeded {len(result.inserted_ids)} cards.")
    except Exception as e:
        print(f"Error seeding cards: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
