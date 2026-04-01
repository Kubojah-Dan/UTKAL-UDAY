import os
import re
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"

SUPPORTED_LANGUAGES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "or": "od-IN"  # Odia - Sarvam uses 'od-IN'
}

NUMERIC_OR_SYMBOLIC_TEXT = re.compile(r"^[\d\s.,%+\-*/=()^:;<>[\]{}|\\]+$")


def _should_translate_option(option: object) -> bool:
    text = str(option or "").strip()
    if not text:
        return False
    return not NUMERIC_OR_SYMBOLIC_TEXT.fullmatch(text)

def translate_text(text: str, target_lang: str, source_lang: str = "en") -> Optional[str]:
    """Translate text using Sarvam.ai API with correct format"""
    if not SARVAM_API_KEY or not text:
        return None
    
    if target_lang == source_lang:
        return text
    
    # Map to Sarvam language codes
    source_code = SUPPORTED_LANGUAGES.get(source_lang, "en-IN")
    target_code = SUPPORTED_LANGUAGES.get(target_lang)
    
    if not target_code:
        return None
    
    try:
        import time
        time.sleep(0.3)  # Rate limit: 3 requests/second
        
        response = requests.post(
            SARVAM_TRANSLATE_URL,
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "input": text,
                "source_language_code": source_code,
                "target_language_code": target_code,
                "speaker_gender": "Male",
                "mode": "formal",
                "model": "mayura:v1",
                "enable_preprocessing": False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("translated_text")
        else:
            return None
    except Exception:
        return None

def translate_question(question_data: Dict, target_langs: List[str]) -> Dict:
    """Translate a question object to multiple languages"""
    print(f"\n--- translate_question called ---")
    print(f"Target languages: {target_langs}")
    print(f"Question: {question_data.get('question', '')[:50]}...")
    
    if not SARVAM_API_KEY or not target_langs:
        print("Skipping: No API key or no target languages")
        return question_data
    
    language_variants = {}
    
    for lang in target_langs:
        print(f"\nProcessing language: {lang}")
        if lang == "en":
            language_variants["en"] = {
                "question": question_data.get("question"),
                "options": question_data.get("options", []),
                "explanation": question_data.get("explanation"),
                "hint": question_data.get("hint")
            }
            print("Added English variant")
            continue
        
        translated_question = translate_text(question_data.get("question", ""), lang)
        print(f"Question translated: {translated_question[:50] if translated_question else 'FAILED'}...")
        
        translated_options = [
            translate_text(opt, lang) if _should_translate_option(opt) else opt
            for opt in question_data.get("options", [])
        ]
        print(f"Options translated: {len([o for o in translated_options if o])} of {len(question_data.get('options', []))}")
        
        translated_explanation = translate_text(question_data.get("explanation", ""), lang) if question_data.get("explanation") else None
        translated_hint = translate_text(question_data.get("hint", ""), lang) if question_data.get("hint") else None
        
        language_variants[lang] = {
            "question": translated_question or question_data.get("question"),
            "options": [opt or orig for opt, orig in zip(translated_options, question_data.get("options", []))],
            "explanation": translated_explanation or question_data.get("explanation"),
            "hint": translated_hint or question_data.get("hint")
        }
        print(f"Added {lang} variant")
    
    question_data["language_variants"] = language_variants
    print(f"\nFinal language_variants keys: {list(language_variants.keys())}")
    return question_data

def batch_translate(texts: List[str], target_lang: str, source_lang: str = "en") -> List[str]:
    """Translate multiple texts efficiently"""
    return [translate_text(text, target_lang, source_lang) or text for text in texts]
