"""
Fix ALL translation issues - 42 untranslated + 82 incomplete = 124 total
"""
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
TARGET_LANGUAGES = ["hi", "ta", "te", "or"]
ALL_LANGUAGES = ["en", "hi", "ta", "te", "or"]

async def fix_all():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*70)
    print("FIXING ALL TRANSLATION ISSUES")
    print("="*70)
    
    cursor = questions_collection.find({"approved": True, "status": "active"})
    
    needs_fix = []
    async for q in cursor:
        langs = q.get("language_variants", {})
        if not langs or not all(lang in langs for lang in ALL_LANGUAGES):
            needs_fix.append(q)
    
    print(f"\n📊 Found {len(needs_fix)} questions needing fixes")
    
    if len(needs_fix) == 0:
        print("\n✅ ALL QUESTIONS COMPLETE!")
        client.close()
        return
    
    batch_size = 5  # Smaller batches for reliability
    fixed = 0
    failed = []
    
    for i in range(0, len(needs_fix), batch_size):
        batch = needs_fix[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(needs_fix) + batch_size - 1) // batch_size
        
        print(f"\n[Batch {batch_num}/{total_batches}] {len(batch)} questions...")
        
        try:
            translated = translate_questions_batch(batch, TARGET_LANGUAGES)
            for q in translated:
                result = await questions_collection.update_one(
                    {"id": q["id"]},
                    {"$set": {"language_variants": q.get("language_variants", {})}}
                )
                if result.modified_count > 0:
                    fixed += 1
                    print(f"  ✓ {q['id']}")
        except Exception as e:
            print(f"  ✗ Batch error: {e}")
            # Try individual questions
            for q in batch:
                try:
                    single = translate_questions_batch([q], TARGET_LANGUAGES)
                    if single:
                        result = await questions_collection.update_one(
                            {"id": single[0]["id"]},
                            {"$set": {"language_variants": single[0].get("language_variants", {})}}
                        )
                        if result.modified_count > 0:
                            fixed += 1
                            print(f"  ✓ {q['id']} (retry)")
                except Exception as e2:
                    failed.append(q['id'])
                    print(f"  ✗ {q['id']}: {str(e2)[:50]}")
    
    print(f"\n" + "="*70)
    print(f"✅ Fixed {fixed}/{len(needs_fix)} questions")
    if failed:
        print(f"❌ Failed: {len(failed)} questions")
        print(f"Failed IDs: {', '.join(failed[:10])}")
    print("="*70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_all())
