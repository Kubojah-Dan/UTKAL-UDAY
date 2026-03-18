"""
Run XES translation for all questions from questions.json
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from translate_xes_questions import translate_xes_questions

if __name__ == "__main__":
    asyncio.run(translate_xes_questions())
