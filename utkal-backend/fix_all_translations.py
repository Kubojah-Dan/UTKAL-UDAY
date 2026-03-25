"""
Fix ALL translation issues - processes one question at a time with rate limit handling.
Groq free tier: 30 requests/minute. Each question needs 4 API calls (hi, ta, te, or).
We add a 3-second delay between languages to stay safely under the limit.
"""
import asyncio
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/utkal_uday")
TARGET_LANGUAGES = ["hi", "ta", "te", "or"]
ALL_LANGUAGES = ["en", "hi", "ta", "te", "or"]
DELAY_BETWEEN_LANGS = 3   # seconds between each language API call
DELAY_BETWEEN_QUESTIONS = 2  # seconds between questions


def translate_one_question(question, target_langs):
    """Translate a single question with per-language delay to avoid rate limits."""
    from app.core.groq_translator import translate_batch

    language_variants = {
        "en": {
            "question": question.get("question"),
            "options": question.get("options", []),
            "explanation": question.get("explanation"),
            "hint": question.get("hint"),
        }
    }

    for lang in target_langs:
        texts = [question.get("question", "")]
        options = question.get("options", [])
        opt_indices = []
        for opt in options:
            s = str(opt).strip()
            if s.replace('.','').replace('-','').replace('/','').isdigit() or len(s) <= 3:
                opt_indices.append(None)
            else:
                opt_indices.append(len(texts))
                texts.append(s)

        if question.get("explanation"):
            exp_idx = len(texts)
            texts.append(question["explanation"])
        else:
            exp_idx = None

        if question.get("hint"):
            hint_idx = len(texts)
            texts.append(question["hint"])
        else:
            hint_idx = None

        print(f"  -> {lang}...", end=" ", flush=True)
        translated = translate_batch(texts, lang)
        print("done")

        t_options = []
        for i, opt in enumerate(options):
            idx = opt_indices[i]
            t_options.append(translated[idx] if idx is not None else opt)

        language_variants[lang] = {
            "question": translated[0] if translated else question.get("question"),
            "options": t_options,
            "explanation": translated[exp_idx] if exp_idx is not None else question.get("explanation"),
            "hint": translated[hint_idx] if hint_idx is not None else question.get("hint"),
        }

        time.sleep(DELAY_BETWEEN_LANGS)  # respect rate limit

    return language_variants


async def fix_all():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    col = db.questions

    print("\n" + "="*60)
    print("FIXING ALL TRANSLATION ISSUES")
    print("="*60)

    # Find all questions needing translation
    cursor = col.find({"approved": True, "status": "active"})
    needs_fix = []
    async for q in cursor:
        langs = q.get("language_variants", {})
        if not langs or not all(lang in langs for lang in ALL_LANGUAGES):
            needs_fix.append(q)

    total = len(needs_fix)
    print(f"\nFound {total} questions needing fixes")
    if total == 0:
        print("ALL QUESTIONS COMPLETE!")
        client.close()
        return

    # Estimate time
    secs_per_q = (DELAY_BETWEEN_LANGS * 4) + DELAY_BETWEEN_QUESTIONS
    est_mins = round(total * secs_per_q / 60, 1)
    print(f"Estimated time: ~{est_mins} minutes ({secs_per_q}s per question)")
    print("Processing one question at a time to respect API rate limits...\n")

    fixed = 0
    failed = []

    for i, q in enumerate(needs_fix, 1):
        qid = q.get("id", "unknown")
        print(f"[{i}/{total}] {qid}")

        try:
            language_variants = translate_one_question(q, TARGET_LANGUAGES)
            result = await col.update_one(
                {"id": qid},
                {"$set": {"language_variants": language_variants}}
            )
            if result.modified_count > 0:
                fixed += 1
                print(f"  Saved ({fixed}/{total} done)")
            else:
                print(f"  No change (already up to date)")
                fixed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append(qid)

        if i < total:
            time.sleep(DELAY_BETWEEN_QUESTIONS)

    print(f"\n" + "="*60)
    print(f"COMPLETE: {fixed}/{total} questions translated")
    if failed:
        print(f"FAILED ({len(failed)}): {', '.join(failed[:10])}")
    print("="*60)

    client.close()


if __name__ == "__main__":
    asyncio.run(fix_all())
