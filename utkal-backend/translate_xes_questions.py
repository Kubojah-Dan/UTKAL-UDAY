"""
Translate XES questions from questions.json file
"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.groq_translator import translate_questions_batch
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/utkal_uday")
XES_FILE = Path(__file__).parent / "data" / "XES3G5M" / "metadata" / "questions.json"

async def translate_xes_questions():
    """Load XES questions, translate them, and save to MongoDB"""
    
    print("\n" + "="*60)
    print("TRANSLATING XES QUESTIONS")
    print("="*60)
    
    # Load XES questions
    with open(XES_FILE, 'r', encoding='utf-8') as f:
        xes_data = json.load(f)
    
    print(f"\nLoaded {len(xes_data)} XES questions from file")
    
    # Convert to question format
    questions = []
    for qid, qdata in xes_data.items():
        question = {
            "id": f"xes_{qid}",
            "question": qdata.get("content", ""),
            "answer": qdata.get("answer", [""])[0] if qdata.get("answer") else "",
            "type": qdata.get("type", "fill in the blank"),
            "options": list(qdata.get("options", {}).values()) if qdata.get("options") else [],
            "explanation": qdata.get("analysis", ""),
            "subject": "Mathematics",
            "grade": 3,  # XES is Grade 3-5
            "difficulty": "medium",
            "skill_id": "xes_skill",
            "skill_label": "XES Problem",
            "approved": True,
            "status": "active"
        }
        questions.append(question)
    
    # Translate in batches
    TARGET_LANGUAGES = ["hi", "ta", "te", "or"]
    batch_size = 10
    translated_count = 0
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i+batch_size]
        print(f"\nTranslating batch {i//batch_size + 1} ({len(batch)} questions)...")
        
        try:
            translated_batch = translate_questions_batch(batch, TARGET_LANGUAGES)
            
            # Save to MongoDB
            for question in translated_batch:
                await questions_collection.update_one(
                    {"id": question["id"]},
                    {"$set": question},
                    upsert=True
                )
                translated_count += 1
                print(f"  ✓ {question['id']}")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: Translated {translated_count}/{len(questions)} XES questions")
    print(f"{'='*60}\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(translate_xes_questions())
