"""
Diagnostic script to check question sources and translations
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

async def diagnose():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    questions_collection = db.questions
    
    print("\n" + "="*60)
    print("QUESTION DIAGNOSTIC")
    print("="*60)
    
    # Check Grade 10 questions
    grade_10_query = {"grade": 10, "approved": True, "status": "active"}
    total_g10 = await questions_collection.count_documents(grade_10_query)
    
    with_trans_g10 = await questions_collection.count_documents({
        **grade_10_query,
        "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
    })
    
    print(f"\nGrade 10 Questions:")
    print(f"  Total: {total_g10}")
    print(f"  With translations: {with_trans_g10}")
    print(f"  Without translations: {total_g10 - with_trans_g10}")
    
    # Sample a Grade 10 question
    if total_g10 > 0:
        sample = await questions_collection.find_one(grade_10_query)
        print(f"\nSample Grade 10 Question:")
        print(f"  ID: {sample.get('id')}")
        print(f"  Subject: {sample.get('subject')}")
        print(f"  Has language_variants: {bool(sample.get('language_variants'))}")
        if sample.get('language_variants'):
            print(f"  Languages: {list(sample['language_variants'].keys())}")
    
    # Check all grades
    print(f"\n{'Grade':<10} {'Total':<10} {'Translated':<15} {'Missing':<10}")
    print("-" * 50)
    for grade in range(1, 13):
        query = {"grade": grade, "approved": True, "status": "active"}
        total = await questions_collection.count_documents(query)
        with_trans = await questions_collection.count_documents({
            **query,
            "language_variants": {"$exists": True, "$ne": None, "$ne": {}}
        })
        missing = total - with_trans
        print(f"{grade:<10} {total:<10} {with_trans:<15} {missing:<10}")
    
    print("\n" + "="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
