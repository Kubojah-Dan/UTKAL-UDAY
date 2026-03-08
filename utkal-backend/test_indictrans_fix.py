"""Quick test for IndicTrans2 import fix"""
import sys
sys.path.insert(0, 'models')

print("Testing tokenizer import...")
try:
    from transformers import PreTrainedTokenizer
    print("✓ Direct import works")
except ImportError as e:
    print(f"✗ Direct import failed: {e}")

print("\nTesting custom tokenizer...")
try:
    from tokenization_indictrans import IndicTransTokenizer
    print("✓ Custom tokenizer imports successfully")
except Exception as e:
    print(f"✗ Custom tokenizer failed: {e}")

print("\nTesting AutoTokenizer...")
try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        'models',
        trust_remote_code=True,
        local_files_only=True,
        use_fast=False
    )
    print("✓ AutoTokenizer loads successfully")
except Exception as e:
    print(f"✗ AutoTokenizer failed: {e}")

print("\nTesting translation service...")
try:
    from app.core.indictrans_translator import load_model
    model, tokenizer, processor = load_model()
    if model and tokenizer and processor:
        print("✓ Translation service loads successfully")
    else:
        print("✗ Translation service returned None")
except Exception as e:
    print(f"✗ Translation service failed: {e}")
    import traceback
    traceback.print_exc()
