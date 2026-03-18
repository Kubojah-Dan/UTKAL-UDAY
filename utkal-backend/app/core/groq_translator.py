"""
Groq API Translation Service - Fast, Scalable Translation
Uses Groq's Llama models for instant translation
"""
import os
from typing import Dict, List, Optional
from groq import Groq

# Client will be initialized lazily
_client = None

def get_client():
    """Get or create Groq client"""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        _client = Groq(api_key=api_key)
    return _client

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "or": "Odia"
}

def translate_batch(texts: List[str], target_lang: str, source_lang: str = "en") -> List[str]:
    """
    Translate multiple texts in one API call for efficiency
    
    Args:
        texts: List of texts to translate
        target_lang: Target language code (hi, ta, te, or)
        source_lang: Source language code (default: en)
    
    Returns:
        List of translated texts
    """
    if not texts or target_lang == source_lang:
        return texts
    
    target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    
    # Create batch translation prompt
    prompt = f"""Translate the following texts from English to {target_name}. Return ONLY the translations, one per line, in the same order. Do not add explanations or numbering.

Texts to translate:
"""
    for i, text in enumerate(texts, 1):
        prompt += f"{i}. {text}\n"
    
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse translations (split by newlines, remove numbering)
        translations = []
        for line in result.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove numbering like "1. " or "1) "
            if line[0].isdigit():
                line = line.split('.', 1)[-1].split(')', 1)[-1].strip()
            translations.append(line)
        
        # Ensure we have the same number of translations
        if len(translations) != len(texts):
            print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
            # Pad with original texts if needed
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])
        
        return translations[:len(texts)]
        
    except Exception as e:
        print(f"Batch translation error: {e}")
        return texts  # Return original texts on error

def translate_question(question_data: Dict, target_langs: List[str]) -> Dict:
    """
    Translate a question object to multiple languages using batch translation
    
    Args:
        question_data: Question dictionary with fields to translate
        target_langs: List of target language codes
    
    Returns:
        Question data with language_variants field added
    """
    print(f"\n--- Groq Translation ---")
    print(f"Target languages: {target_langs}")
    print(f"Question: {question_data.get('question', '')[:50]}...")
    
    if not target_langs:
        return question_data
    
    language_variants = {}
    
    # Always include English
    language_variants["en"] = {
        "question": question_data.get("question"),
        "passage": question_data.get("passage"),
        "instructions": question_data.get("instructions"),
        "options": question_data.get("options", []),
        "explanation": question_data.get("explanation"),
        "hint": question_data.get("hint"),
        "expected_points": question_data.get("expected_points", []),
    }
    
    for lang in target_langs:
        if lang == "en":
            continue
        
        print(f"\nTranslating to {lang}...")
        
        # Collect all texts to translate
        texts_to_translate = []
        texts_to_translate.append(question_data.get("question", ""))
        
        passage_idx = None
        instructions_idx = None
        if question_data.get("passage"):
            passage_idx = len(texts_to_translate)
            texts_to_translate.append(question_data.get("passage", ""))
        if question_data.get("instructions"):
            instructions_idx = len(texts_to_translate)
            texts_to_translate.append(question_data.get("instructions", ""))
        
        # Add options (skip numbers/short math)
        options = question_data.get("options", [])
        option_indices = []
        for i, opt in enumerate(options):
            if opt.strip().replace('.', '').replace('-', '').isdigit() or len(opt) <= 3:
                option_indices.append(None)  # Skip translation
            else:
                option_indices.append(len(texts_to_translate))
                texts_to_translate.append(opt)
        
        # Add explanation and hint if present
        explanation_idx = None
        hint_idx = None
        
        if question_data.get("explanation"):
            explanation_idx = len(texts_to_translate)
            texts_to_translate.append(question_data.get("explanation"))
        
        if question_data.get("hint"):
            hint_idx = len(texts_to_translate)
            texts_to_translate.append(question_data.get("hint"))
        
        expected_points = question_data.get("expected_points", [])
        expected_indices = []
        for point in expected_points:
            point_text = str(point or "").strip()
            if not point_text:
                expected_indices.append(None)
                continue
            expected_indices.append(len(texts_to_translate))
            texts_to_translate.append(point_text)
        
        # Translate all at once
        translations = translate_batch(texts_to_translate, lang)
        
        # Extract translations
        translated_question = translations[0] if translations else question_data.get("question")
        translated_passage = translations[passage_idx] if passage_idx is not None else question_data.get("passage")
        translated_instructions = translations[instructions_idx] if instructions_idx is not None else question_data.get("instructions")
        
        # Reconstruct options
        translated_options = []
        for i, opt in enumerate(options):
            if option_indices[i] is None:
                translated_options.append(opt)  # Keep original
            else:
                translated_options.append(translations[option_indices[i]])
        
        translated_explanation = translations[explanation_idx] if explanation_idx is not None else question_data.get("explanation")
        translated_hint = translations[hint_idx] if hint_idx is not None else question_data.get("hint")
        translated_expected = []
        for idx, point in enumerate(expected_points):
            expected_translation_idx = expected_indices[idx] if idx < len(expected_indices) else None
            if expected_translation_idx is None:
                translated_expected.append(point)
            else:
                translated_expected.append(translations[expected_translation_idx])
        
        language_variants[lang] = {
            "question": translated_question,
            "passage": translated_passage,
            "instructions": translated_instructions,
            "options": translated_options,
            "explanation": translated_explanation,
            "hint": translated_hint,
            "expected_points": translated_expected,
        }
        
        print(f"✓ {lang} translation complete")
    
    question_data["language_variants"] = language_variants
    print(f"\nLanguages added: {list(language_variants.keys())}")
    return question_data

def translate_questions_batch(questions: List[Dict], target_langs: List[str]) -> List[Dict]:
    """
    Translate multiple questions efficiently
    
    Args:
        questions: List of question dictionaries
        target_langs: List of target language codes
    
    Returns:
        List of questions with translations added
    """
    print(f"\n=== BATCH TRANSLATION ===")
    print(f"Questions: {len(questions)}")
    print(f"Languages: {target_langs}")
    
    translated_questions = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Translating question: {question.get('id')}")
        translated = translate_question(question, target_langs)
        translated_questions.append(translated)
    
    print(f"\n✓ Batch translation complete: {len(translated_questions)} questions")
    return translated_questions
