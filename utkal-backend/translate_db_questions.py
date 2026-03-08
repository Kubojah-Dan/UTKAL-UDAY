"""
Script to translate all existing questions in MongoDB to 5 languages
Run this to add translations to questions that don't have them yet
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API key is loaded
if not os.getenv("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not found in environment variables")
    print("Please add GROQ_API_KEY=your_key_here to utkal-backend/.env file")
    sys.exit(1)

from app.core.groq_translator import translate_questions_batch

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/utkal_uday")
TARGET_LANGUAGES = ["hi", "ta", "te", "or"]

async def translate_existing_questions():
    """Translate all questions in database that don't have translations"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("=" * 60)
    print("TRANSLATING EXISTING QUESTIONS IN DATABASE")
    print("=" * 60)
    
    # Find questions without language_variants
    query = {
        "$or": [
            {"language_variants": {"$exists": False}},
            {"language_variants": None},
            {"language_variants": {}}
        ],
        "approved": True,
        "status": "active"
    }
    
    cursor = questions_collection.find(query)
    questions = await cursor.to_list(length=None)
    
    print(f"\nFound {len(questions)} questions without translations")
    
    if len(questions) == 0:
        print("✓ All questions already have translations!")
        return
    
    # Process in batches of 10 for efficiency
    batch_size = 10
    total_translated = 0
    
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i+batch_size]
        print(f"\n--- Batch {i//batch_size + 1} ({len(batch)} questions) ---")
        
        try:
            # Translate batch
            translated_batch = translate_questions_batch(batch, TARGET_LANGUAGES)
            
            # Update each question in MongoDB
            for question in translated_batch:
                result = await questions_collection.update_one(
                    {"id": question["id"]},
                    {"$set": {"language_variants": question.get("language_variants", {})}}
                )
                
                if result.modified_count > 0:
                    total_translated += 1
                    print(f"✓ Translated: {question['id']}")
            
        except Exception as e:
            print(f"✗ Error translating batch: {e}")
            continue
    
    print("\n" + "=" * 60)
    print(f"TRANSLATION COMPLETE: {total_translated}/{len(questions)} questions")
    print("=" * 60)
    
    client.close()

async def translate_specific_grade(grade: int):
    """Translate questions for a specific grade only"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print(f"\n=== Translating Grade {grade} Questions ===\n")
    
    query = {
        "grade": grade,
        "$or": [
            {"language_variants": {"$exists": False}},
            {"language_variants": None},
            {"language_variants": {}}
        ],
        "approved": True,
        "status": "active"
    }
    
    cursor = questions_collection.find(query)
    questions = await cursor.to_list(length=None)
    
    print(f"Found {len(questions)} Grade {grade} questions to translate")
    
    if len(questions) == 0:
        print(f"✓ All Grade {grade} questions already translated!")
        client.close()
        return
    
    # Translate all at once
    try:
        translated = translate_questions_batch(questions, TARGET_LANGUAGES)
        
        # Update MongoDB
        for question in translated:
            await questions_collection.update_one(
                {"id": question["id"]},
                {"$set": {"language_variants": question.get("language_variants", {})}}
            )
        
        print(f"\n✓ Successfully translated {len(translated)} Grade {grade} questions")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    client.close()

async def check_translation_status():
    """Check how many questions have translations"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    total = await questions_collection.count_documents({"approved": True, "status": "active"})
    
    with_translations = await questions_collection.count_documents({
        "approved": True,
        "status": "active",
        "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
    })
    
    without_translations = total - with_translations
    
    print("\n" + "=" * 60)
    print("TRANSLATION STATUS")
    print("=" * 60)
    print(f"Total active questions: {total}")
    print(f"With translations: {with_translations} ({round(with_translations/total*100 if total > 0 else 0)}%)")
    print(f"Without translations: {without_translations}")
    print("=" * 60 + "\n")
    
    client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            # Check status only
            asyncio.run(check_translation_status())
        elif sys.argv[1] == "grade":
            # Translate specific grade
            if len(sys.argv) < 3:
                print("Usage: python translate_db_questions.py grade <grade_number>")
                sys.exit(1)
            grade = int(sys.argv[2])
            asyncio.run(translate_specific_grade(grade))
        else:
            print("Unknown command. Use: status, grade <N>, or no args to translate all")
    else:
        # Translate all questions
        print("\nStarting translation of all questions...")
        print("This may take several minutes depending on question count.\n")
        asyncio.run(check_translation_status())
        asyncio.run(translate_existing_questions())
        asyncio.run(check_translation_status())
