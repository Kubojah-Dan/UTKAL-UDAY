"""
Fix incomplete translations - questions that have language_variants but missing some languages
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

async def fix_incomplete_translations():
    """Fix questions that have language_variants but are missing some languages"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("FIXING INCOMPLETE TRANSLATIONS")
    print("="*60)
    
    # Find questions with language_variants but incomplete
    cursor = questions_collection.find({
        "approved": True,
        "status": "active",
        "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
    })
    
    incomplete = []
    async for q in cursor:
        langs = q.get("language_variants", {})
        missing_langs = [lang for lang in ALL_LANGUAGES if lang not in langs]
        if missing_langs:
            incomplete.append({
                "question": q,
                "missing": missing_langs
            })
    
    print(f"\nFound {len(incomplete)} questions with incomplete translations")
    
    if len(incomplete) == 0:
        print("✓ All questions have complete translations!")
        client.close()
        return
    
    # Show samples
    print(f"\nSample incomplete questions:")
    for i, item in enumerate(incomplete[:5], 1):
        q = item["question"]
        print(f"  {i}. {q.get('id')}: Missing {', '.join(item['missing'])}")
    
    # Fix them by re-translating
    print(f"\nRe-translating {len(incomplete)} questions...")
    
    batch_size = 10
    fixed_count = 0
    
    for i in range(0, len(incomplete), batch_size):
        batch_items = incomplete[i:i+batch_size]
        batch_questions = [item["question"] for item in batch_items]
        
        print(f"\nBatch {i//batch_size + 1} ({len(batch_questions)} questions)...")
        
        try:
            # Re-translate entire batch
            translated = translate_questions_batch(batch_questions, TARGET_LANGUAGES)
            
            # Update MongoDB
            for q in translated:
                result = await questions_collection.update_one(
                    {"id": q["id"]},
                    {"$set": {"language_variants": q.get("language_variants", {})}}
                )
                if result.modified_count > 0:
                    fixed_count += 1
                    print(f"  ✓ {q['id']}")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n" + "="*60)
    print(f"COMPLETE: Fixed {fixed_count}/{len(incomplete)} questions")
    print("="*60)
    
    client.close()

async def fix_all_missing_translations():
    """Fix ALL questions without proper translations"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("FIXING ALL MISSING TRANSLATIONS")
    print("="*60)
    
    # Find ALL questions that need translation
    # Either no language_variants OR incomplete language_variants
    cursor = questions_collection.find({
        "approved": True,
        "status": "active"
    })
    
    needs_translation = []
    async for q in cursor:
        langs = q.get("language_variants", {})
        
        # Check if missing language_variants entirely
        if not langs or langs == {}:
            needs_translation.append(q)
            continue
        
        # Check if missing any required languages
        missing_langs = [lang for lang in ALL_LANGUAGES if lang not in langs]
        if missing_langs:
            needs_translation.append(q)
    
    print(f"\nFound {len(needs_translation)} questions needing translation")
    
    if len(needs_translation) == 0:
        print("✓ All questions have complete translations!")
        client.close()
        return
    
    # Translate in batches
    batch_size = 10
    fixed_count = 0
    
    for i in range(0, len(needs_translation), batch_size):
        batch = needs_translation[i:i+batch_size]
        
        print(f"\nBatch {i//batch_size + 1} ({len(batch)} questions)...")
        
        try:
            translated = translate_questions_batch(batch, TARGET_LANGUAGES)
            
            for q in translated:
                result = await questions_collection.update_one(
                    {"id": q["id"]},
                    {"$set": {"language_variants": q.get("language_variants", {})}}
                )
                if result.modified_count > 0:
                    fixed_count += 1
                    print(f"  ✓ {q['id']}")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    print(f"\n" + "="*60)
    print(f"COMPLETE: Fixed {fixed_count}/{len(needs_translation)} questions")
    print("="*60)
    
    client.close()

async def verify_translations():
    """Verify all translations are complete"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("VERIFYING TRANSLATIONS")
    print("="*60)
    
    total = await questions_collection.count_documents({"approved": True, "status": "active"})
    
    # Count complete translations
    cursor = questions_collection.find({
        "approved": True,
        "status": "active"
    })
    
    complete = 0
    incomplete = 0
    
    async for q in cursor:
        langs = q.get("language_variants", {})
        if all(lang in langs for lang in ALL_LANGUAGES):
            complete += 1
        else:
            incomplete += 1
    
    print(f"\nTotal active questions: {total}")
    print(f"Complete translations: {complete} ({round(complete/total*100 if total > 0 else 0)}%)")
    print(f"Incomplete translations: {incomplete} ({round(incomplete/total*100 if total > 0 else 0)}%)")
    
    if incomplete == 0:
        print("\n✅ ALL QUESTIONS HAVE COMPLETE TRANSLATIONS!")
    else:
        print(f"\n⚠️  {incomplete} questions still need translation")
    
    print("="*60)
    
    client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "incomplete":
            asyncio.run(fix_incomplete_translations())
        elif sys.argv[1] == "all":
            asyncio.run(fix_all_missing_translations())
        elif sys.argv[1] == "verify":
            asyncio.run(verify_translations())
        else:
            print("Usage:")
            print("  python fix_translations.py incomplete  - Fix questions with incomplete translations")
            print("  python fix_translations.py all         - Fix ALL questions needing translation")
            print("  python fix_translations.py verify      - Verify translation status")
    else:
        print("Usage:")
        print("  python fix_translations.py incomplete  - Fix questions with incomplete translations")
        print("  python fix_translations.py all         - Fix ALL questions needing translation")
        print("  python fix_translations.py verify      - Verify translation status")
        print("\nRecommended: Run 'all' to fix everything at once")
