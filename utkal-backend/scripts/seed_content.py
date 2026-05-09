import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import async_db
from app.generators.science_generator import generate_questions_for_grade as gen_science
from app.generators.social_science_generator import generate_questions_for_grade as gen_social

questions_col = async_db["questions"]

async def seed_subject(subject_name, generator_func, grades=range(1, 11), count_per_grade=50):
    print(f"--- Seeding {subject_name} ---")
    total_added = 0
    for grade in grades:
        print(f"Generating questions for Grade {grade}...")
        questions = generator_func(grade, count_per_grade)
        
        # Add 'approved' and 'status' flags needed by the app
        for q in questions:
            q["approved"] = True
            q["status"] = "active"
            # Ensure ID is unique and formatted consistently
            q["id"] = f"SEED-{subject_name[:3].upper()}-G{grade}-{q['id'][:8]}"
        
        if questions:
            try:
                # Use insert_many for efficiency
                result = await questions_col.insert_many(questions, ordered=False)
                added = len(result.inserted_ids)
                total_added += added
                print(f"  Successfully added {added} questions for Grade {grade}")
            except Exception as e:
                print(f"  Error inserting for Grade {grade}: {e}")
    
    print(f"Finished {subject_name}. Total questions added: {total_added}")

async def main():
    print("Starting Utkal Uday Content Seeding...")
    
    # Seed Science / EVS
    await seed_subject("Science/EVS", gen_science)
    
    # Seed Social Science
    await seed_subject("Social Science", gen_social)
    
    print("\nSeeding complete! You can now use these subjects in the app.")

if __name__ == "__main__":
    asyncio.run(main())
