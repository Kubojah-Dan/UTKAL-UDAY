"""
Groq API Translation Service - Fast, Scalable Translation
Uses Groq's Llama models for instant translation
"""
import os
import time
from typing import Dict, List
from groq import Groq

_client = None

def get_client():
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
    if not texts or target_lang == source_lang:
        return texts

    target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    prompt = f"Translate the following texts from English to {target_name}. Return ONLY the translations, one per line, in the same order. Do not add explanations or numbering.\n\nTexts to translate:\n"
    for i, text in enumerate(texts, 1):
        prompt += f"{i}. {text}\n"

    for attempt in range(4):  # retry up to 4 times
        try:
            client = get_client()
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            result = response.choices[0].message.content.strip()
            translations = []
            for line in result.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line[0].isdigit():
                    line = line.split('.', 1)[-1].split(')', 1)[-1].strip()
                translations.append(line)

            if len(translations) != len(texts):
                print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
                while len(translations) < len(texts):
                    translations.append(texts[len(translations)])

            return translations[:len(texts)]

        except Exception as e:
            err = str(e)
            if "429" in err or "Too Many Requests" in err or "rate_limit" in err.lower():
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s, 240s
                print(f"Rate limit hit. Waiting {wait}s before retry {attempt+1}/4...")
                time.sleep(wait)
            else:
                print(f"Batch translation error: {e}")
                return texts

    print("Max retries reached, returning original texts")
    return texts


def translate_question(question_data: Dict, target_langs: List[str]) -> Dict:
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

        options = question_data.get("options", [])
        option_indices = []
        for opt in options:
            if str(opt).strip().replace('.', '').replace('-', '').isdigit() or len(str(opt)) <= 3:
                option_indices.append(None)
            else:
                option_indices.append(len(texts_to_translate))
                texts_to_translate.append(str(opt))

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

        translations = translate_batch(texts_to_translate, lang)

        translated_question = translations[0] if translations else question_data.get("question")
        translated_passage = translations[passage_idx] if passage_idx is not None else question_data.get("passage")
        translated_instructions = translations[instructions_idx] if instructions_idx is not None else question_data.get("instructions")

        translated_options = []
        for i, opt in enumerate(options):
            if option_indices[i] is None:
                translated_options.append(opt)
            else:
                translated_options.append(translations[option_indices[i]])

        translated_explanation = translations[explanation_idx] if explanation_idx is not None else question_data.get("explanation")
        translated_hint = translations[hint_idx] if hint_idx is not None else question_data.get("hint")

        translated_expected = []
        for idx, point in enumerate(expected_points):
            ei = expected_indices[idx] if idx < len(expected_indices) else None
            translated_expected.append(translations[ei] if ei is not None else point)

        language_variants[lang] = {
            "question": translated_question,
            "passage": translated_passage,
            "instructions": translated_instructions,
            "options": translated_options,
            "explanation": translated_explanation,
            "hint": translated_hint,
            "expected_points": translated_expected,
        }

        print(f"OK {lang} translation complete")

    question_data["language_variants"] = language_variants
    print(f"\nLanguages added: {list(language_variants.keys())}")
    return question_data


def translate_questions_batch(questions: List[Dict], target_langs: List[str]) -> List[Dict]:
    print(f"\n=== BATCH TRANSLATION ===")
    print(f"Questions: {len(questions)}")
    print(f"Languages: {target_langs}")

    translated_questions = []
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Translating question: {question.get('id')}")
        translated = translate_question(question, target_langs)
        translated_questions.append(translated)

    print(f"\nOK Batch translation complete: {len(translated_questions)} questions")
    return translated_questions
