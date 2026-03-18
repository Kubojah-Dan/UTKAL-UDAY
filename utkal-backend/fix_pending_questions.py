"""
Fix teacher-uploaded questions that are stuck in pending state
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

async def check_pending_questions():
    """Check all pending questions"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("CHECKING PENDING QUESTIONS")
    print("="*60)
    
    # Find all pending questions
    cursor = questions_collection.find({"approved": False})
    pending = await cursor.to_list(length=None)
    
    print(f"\nFound {len(pending)} pending questions")
    
    if len(pending) == 0:
        print("✓ No pending questions!")
        client.close()
        return
    
    # Group by grade
    by_grade = {}
    for q in pending:
        grade = q.get("grade", "Unknown")
        if grade not in by_grade:
            by_grade[grade] = []
        by_grade[grade].append(q)
    
    print(f"\nPending questions by grade:")
    for grade in sorted(by_grade.keys()):
        print(f"  Grade {grade}: {len(by_grade[grade])} questions")
    
    # Show samples
    print(f"\nSample pending questions:")
    for i, q in enumerate(pending[:5], 1):
        print(f"\n  {i}. ID: {q.get('id', 'NO_ID')}")
        print(f"     Subject: {q.get('subject', 'N/A')}")
        print(f"     Grade: {q.get('grade', 'N/A')}")
        print(f"     Question: {q.get('question', '')[:80]}...")
        print(f"     Has translations: {bool(q.get('language_variants'))}")
    
    client.close()

async def approve_all_pending(translate=True):
    """Approve all pending questions and optionally translate them"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("APPROVING ALL PENDING QUESTIONS")
    print("="*60)
    
    # Find all pending questions
    cursor = questions_collection.find({"approved": False})
    pending = await cursor.to_list(length=None)
    
    if len(pending) == 0:
        print("\n✓ No pending questions to approve!")
        client.close()
        return
    
    print(f"\nFound {len(pending)} pending questions")
    
    # Translate if requested
    if translate:
        print(f"\nTranslating to: {', '.join(TARGET_LANGUAGES)}")
        
        # Process in batches
        batch_size = 10
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i+batch_size]
            print(f"\nBatch {i//batch_size + 1}: Translating {len(batch)} questions...")
            
            try:
                translated_batch = translate_questions_batch(batch, TARGET_LANGUAGES)
                
                # Update each question
                for q in translated_batch:
                    await questions_collection.update_one(
                        {"id": q["id"]},
                        {"$set": {
                            "approved": True,
                            "status": "active",
                            "language_variants": q.get("language_variants", {})
                        }}
                    )
                    print(f"  ✓ {q['id']}")
            
            except Exception as e:
                print(f"  ✗ Error: {e}")
                # Still approve without translation
                for q in batch:
                    await questions_collection.update_one(
                        {"id": q["id"]},
                        {"$set": {
                            "approved": True,
                            "status": "active"
                        }}
                    )
    else:
        # Just approve without translation
        for q in pending:
            await questions_collection.update_one(
                {"id": q["id"]},
                {"$set": {
                    "approved": True,
                    "status": "active"
                }}
            )
        print(f"\n✓ Approved {len(pending)} questions (no translation)")
    
    print(f"\n" + "="*60)
    print(f"COMPLETE: Approved {len(pending)} questions")
    print("="*60)
    
    client.close()

async def check_question_availability():
    """Check if questions are available to students"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("QUESTION AVAILABILITY CHECK")
    print("="*60)
    
    for grade in [1, 3, 9, 10, 12]:
        total = await questions_collection.count_documents({
            "grade": grade,
            "approved": True,
            "status": "active"
        })
        
        with_trans = await questions_collection.count_documents({
            "grade": grade,
            "approved": True,
            "status": "active",
            "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
        })
        
        print(f"\nGrade {grade}:")
        print(f"  Available questions: {total}")
        print(f"  With translations: {with_trans}")
        print(f"  Status: {'✓ Ready' if total > 0 else '✗ No questions'}")
    
    print("\n" + "="*60)
    
    client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            asyncio.run(check_pending_questions())
        elif sys.argv[1] == "approve":
            translate = "--no-translate" not in sys.argv
            asyncio.run(approve_all_pending(translate=translate))
        elif sys.argv[1] == "availability":
            asyncio.run(check_question_availability())
        else:
            print("Usage:")
            print("  python fix_pending_questions.py check          - Check pending questions")
            print("  python fix_pending_questions.py approve        - Approve and translate all")
            print("  python fix_pending_questions.py approve --no-translate  - Approve without translation")
            print("  python fix_pending_questions.py availability   - Check question availability")
    else:
        print("Usage:")
        print("  python fix_pending_questions.py check          - Check pending questions")
        print("  python fix_pending_questions.py approve        - Approve and translate all")
        print("  python fix_pending_questions.py availability   - Check question availability")
