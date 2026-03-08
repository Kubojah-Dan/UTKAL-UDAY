"""
IndicTrans2 Translation Service with LoRA Adapters - Offline Translation
No API costs, runs locally on server
"""
import os
import torch
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Model will be loaded lazily on first use
_model = None
_tokenizer = None
_processor = None

MODEL_ID = "ai4bharat/indictrans2-en-indic-1B"
LORA_ADAPTERS_PATH = Path(__file__).parent.parent.parent / "models" / "fine_tuned_indictrans2_lora_adapters"

SUPPORTED_LANGUAGES = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "or": "ory_Orya"  # Odia
}

def load_model():
    """Load IndicTrans2 base model with LoRA adapters (lazy loading)"""
    global _model, _tokenizer, _processor
    
    if _model is not None:
        return _model, _tokenizer, _processor
    
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from peft import PeftModel
        from IndicTransToolkit.processor import IndicProcessor
        
        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading IndicTrans2 model from {MODEL_ID}...")
        
        # Load tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        
        # Load base model (float16 for efficiency)
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        # Load and attach LoRA adapters
        print(f"Loading LoRA adapters from {LORA_ADAPTERS_PATH}...")
        _model = PeftModel.from_pretrained(base_model, str(LORA_ADAPTERS_PATH))
        _model = _model.to(DEVICE)
        _model.eval()
        
        # Initialize processor
        _processor = IndicProcessor(inference=True)
        
        print(f"IndicTrans2 model with LoRA adapters loaded successfully on {DEVICE}")
        return _model, _tokenizer, _processor
        
    except Exception as e:
        print(f"Failed to load IndicTrans2 model: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def translate_text(text: str, target_lang: str, source_lang: str = "en") -> Optional[str]:
    """
    Translate text using IndicTrans2 model
    
    Args:
        text: Text to translate
        target_lang: Target language code (hi, ta, te, or)
        source_lang: Source language code (default: en)
    
    Returns:
        Translated text or None if translation fails
    """
    if not text or target_lang == source_lang:
        return text
    
    # Map to IndicTrans2 language codes
    src_code = SUPPORTED_LANGUAGES.get(source_lang)
    tgt_code = SUPPORTED_LANGUAGES.get(target_lang)
    
    if not src_code or not tgt_code:
        print(f"Unsupported language: {source_lang} -> {target_lang}")
        return None
    
    try:
        model, tokenizer, processor = load_model()
        if model is None:
            return None
        
        # Preprocess
        batch = processor.preprocess_batch([text], src_lang=src_code, tgt_lang=tgt_code)
        
        # Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(model.device)
        
        # Generate translation
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )
        
        # Decode
        decoded = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )
        
        # Postprocess
        translation = processor.postprocess_batch(decoded, lang=tgt_code)
        
        return translation[0] if translation else None
        
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def translate_question(question_data: Dict, target_langs: List[str]) -> Dict:
    """
    Translate a question object to multiple languages
    
    Args:
        question_data: Question dictionary with fields to translate
        target_langs: List of target language codes
    
    Returns:
        Question data with language_variants field added
    """
    print(f"\n--- IndicTrans2 translation ---")
    print(f"Target languages: {target_langs}")
    print(f"Question: {question_data.get('question', '')[:50]}...")
    
    if not target_langs:
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
        
        # Translate question
        translated_question = translate_text(question_data.get("question", ""), lang)
        print(f"Question translated: {translated_question[:50] if translated_question else 'FAILED'}...")
        
        # Translate options (skip if numbers/symbols)
        options = question_data.get("options", [])
        translated_options = []
        for opt in options:
            # Skip translation for numbers and short math expressions
            if opt.strip().replace('.', '').replace('-', '').isdigit() or len(opt) <= 3:
                translated_options.append(opt)
            else:
                trans_opt = translate_text(opt, lang)
                translated_options.append(trans_opt or opt)
        
        print(f"Options translated: {len([o for o in translated_options if o])} of {len(options)}")
        
        # Translate explanation and hint if present
        translated_explanation = None
        translated_hint = None
        
        if question_data.get("explanation"):
            translated_explanation = translate_text(question_data.get("explanation"), lang)
        
        if question_data.get("hint"):
            translated_hint = translate_text(question_data.get("hint"), lang)
        
        language_variants[lang] = {
            "question": translated_question or question_data.get("question"),
            "options": translated_options,
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
