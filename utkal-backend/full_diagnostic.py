"""
Comprehensive diagnostic to identify all question and translation issues
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/utkal_uday")

async def full_diagnostic():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*70)
    print("COMPREHENSIVE QUESTION DIAGNOSTIC")
    print("="*70)
    
    # 1. Total questions
    total_all = await questions_collection.count_documents({})
    total_active = await questions_collection.count_documents({"approved": True, "status": "active"})
    total_pending = await questions_collection.count_documents({"approved": False})
    
    print(f"\n📊 OVERALL STATISTICS")
    print(f"  Total questions in DB: {total_all}")
    print(f"  Active & approved: {total_active}")
    print(f"  Pending approval: {total_pending}")
    
    # 2. Translation status
    with_trans = await questions_collection.count_documents({
        "approved": True,
        "status": "active",
        "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
    })
    
    without_trans = total_active - with_trans
    
    print(f"\n🌐 TRANSLATION STATUS")
    print(f"  With translations: {with_trans} ({round(with_trans/total_active*100 if total_active > 0 else 0)}%)")
    print(f"  Without translations: {without_trans} ({round(without_trans/total_active*100 if total_active > 0 else 0)}%)")
    
    # 3. Questions by source
    print(f"\n📁 QUESTIONS BY SOURCE")
    
    # Count by ID pattern
    cursor = questions_collection.find({"approved": True, "status": "active"}, {"id": 1})
    all_ids = [doc["id"] async for doc in cursor]
    
    xes_count = len([id for id in all_ids if id.lower().startswith("xes")])
    math_count = len([id for id in all_ids if "math_g" in id.lower()])
    english_count = len([id for id in all_ids if "english_g" in id.lower()])
    science_count = len([id for id in all_ids if "science_g" in id.lower()])
    other_count = total_active - (xes_count + math_count + english_count + science_count)
    
    print(f"  XES questions: {xes_count}")
    print(f"  Math generated: {math_count}")
    print(f"  English generated: {english_count}")
    print(f"  Science generated: {science_count}")
    print(f"  Other: {other_count}")
    
    # 4. Untranslated questions by source
    print(f"\n❌ UNTRANSLATED QUESTIONS BY SOURCE")
    
    cursor = questions_collection.find({
        "approved": True,
        "status": "active",
        "$or": [
            {"language_variants": {"$exists": False}},
            {"language_variants": None},
            {"language_variants": {}}
        ]
    }, {"id": 1})
    
    untranslated_ids = [doc["id"] async for doc in cursor]
    
    xes_untrans = len([id for id in untranslated_ids if id.lower().startswith("xes")])
    math_untrans = len([id for id in untranslated_ids if "math_g" in id.lower()])
    english_untrans = len([id for id in untranslated_ids if "english_g" in id.lower()])
    science_untrans = len([id for id in untranslated_ids if "science_g" in id.lower()])
    other_untrans = len(untranslated_ids) - (xes_untrans + math_untrans + english_untrans + science_untrans)
    
    print(f"  XES: {xes_untrans}")
    print(f"  Math: {math_untrans}")
    print(f"  English: {english_untrans}")
    print(f"  Science: {science_untrans}")
    print(f"  Other: {other_untrans}")
    
    # 5. Sample untranslated questions
    if untranslated_ids:
        print(f"\n📝 SAMPLE UNTRANSLATED QUESTIONS (first 10)")
        for i, qid in enumerate(untranslated_ids[:10], 1):
            q = await questions_collection.find_one({"id": qid})
            print(f"  {i}. {qid}")
            print(f"     Subject: {q.get('subject', 'N/A')}, Grade: {q.get('grade', 'N/A')}")
            print(f"     Question: {q.get('question', '')[:60]}...")
    
    # 6. Grade breakdown
    print(f"\n📚 GRADE BREAKDOWN")
    print(f"{'Grade':<8} {'Total':<8} {'Translated':<12} {'Missing':<10} {'%':<8}")
    print("-" * 55)
    
    for grade in range(1, 13):
        total_g = await questions_collection.count_documents({
            "grade": grade,
            "approved": True,
            "status": "active"
        })
        
        trans_g = await questions_collection.count_documents({
            "grade": grade,
            "approved": True,
            "status": "active",
            "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
        })
        
        missing_g = total_g - trans_g
        pct = round(trans_g/total_g*100 if total_g > 0 else 0)
        
        if total_g > 0:
            print(f"{grade:<8} {total_g:<8} {trans_g:<12} {missing_g:<10} {pct}%")
    
    # 7. Check for questions with incomplete translations
    print(f"\n⚠️  INCOMPLETE TRANSLATIONS")
    cursor = questions_collection.find({
        "approved": True,
        "status": "active",
        "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
    })
    
    incomplete_count = 0
    async for q in cursor:
        langs = q.get("language_variants", {})
        if not all(lang in langs for lang in ["en", "hi", "ta", "te", "or"]):
            incomplete_count += 1
    
    print(f"  Questions with incomplete language sets: {incomplete_count}")
    
    # 8. Check pending approval questions
    if total_pending > 0:
        print(f"\n⏳ PENDING APPROVAL QUESTIONS")
        cursor = questions_collection.find({"approved": False}).limit(10)
        pending_list = await cursor.to_list(length=10)
        
        for i, q in enumerate(pending_list, 1):
            print(f"  {i}. {q.get('id', 'NO_ID')}")
            print(f"     Subject: {q.get('subject', 'N/A')}, Grade: {q.get('grade', 'N/A')}")
            print(f"     Status: {q.get('status', 'N/A')}, Approved: {q.get('approved', False)}")
    
    # 9. Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    
    if without_trans > 0:
        print(f"  1. Run: python translate_db_questions.py")
        print(f"     This will translate {without_trans} questions")
    
    if xes_untrans > 0:
        print(f"  2. XES questions need translation: {xes_untrans} questions")
        print(f"     These may be from questions.json file")
    
    if total_pending > 0:
        print(f"  3. Approve {total_pending} pending questions via teacher dashboard")
    
    if incomplete_count > 0:
        print(f"  4. Fix {incomplete_count} questions with incomplete translations")
    
    print(f"\n" + "="*70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(full_diagnostic())
