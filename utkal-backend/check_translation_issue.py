"""Check why specific questions fail translation"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.groq_translator import translate_questions_batch
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/utkal_uday")

async def check_and_fix():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    # Get one untranslated question
    q = await questions_collection.find_one({"id": "math_g10_algebra_0001"})
    
    if not q:
        print("Question not found!")
        client.close()
        return
    
    print(f"\n=== Checking: {q['id']} ===")
    print(f"Has language_variants: {bool(q.get('language_variants'))}")
    print(f"Value: {q.get('language_variants')}")
    print(f"Question text: {q.get('question', '')[:100]}")
    
    # Try to translate it
    print(f"\n=== Attempting translation ===")
    try:
        translated = translate_questions_batch([q], ["hi", "ta", "te", "or"])
        print(f"✓ Translation successful!")
        print(f"Languages: {list(translated[0].get('language_variants', {}).keys())}")
        
        # Save it
        result = await questions_collection.update_one(
            {"id": q["id"]},
            {"$set": {"language_variants": translated[0].get("language_variants", {})}}
        )
        print(f"✓ Saved to MongoDB: {result.modified_count} modified")
        
    except Exception as e:
        print(f"✗ Translation failed: {e}")
        import traceback
        traceback.print_exc()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_and_fix())
