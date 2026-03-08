"""
Quick script to translate the remaining 13 questions
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from translate_db_questions import translate_existing_questions, check_translation_status

async def main():
    print("Checking status...")
    await check_translation_status()
    
    print("\nTranslating remaining questions...")
    await translate_existing_questions()
    
    print("\nFinal status:")
    await check_translation_status()

if __name__ == "__main__":
    asyncio.run(main())
