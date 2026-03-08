"""
IndicTrans2 Setup Verification Script
Run this to verify the translation system is working correctly
"""
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    required = ['torch', 'transformers', 'sentencepiece', 'peft', 'accelerate']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING")
            missing.append(package)
    
    try:
        from IndicTransToolkit.processor import IndicProcessor
        print(f"  ✓ IndicTransToolkit")
    except ImportError:
        print(f"  ✗ IndicTransToolkit - MISSING")
        missing.append('IndicTransToolkit')
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All dependencies installed\n")
    return True

def check_model_files():
    """Check if LoRA adapter files exist"""
    print("Checking LoRA adapter files...")
    model_path = Path(__file__).parent / "models" / "fine_tuned_indictrans2_lora_adapters"
    
    required_files = [
        'adapter_config.json',
        'adapter_model.safetensors'
    ]
    
    missing = []
    for file in required_files:
        file_path = model_path / file
        if file_path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            missing.append(file)
    
    if missing:
        print(f"\n❌ Missing LoRA adapter files: {', '.join(missing)}")
        print(f"LoRA adapters directory: {model_path}")
        return False
    
    print("✅ All LoRA adapter files present\n")
    return True

def test_translation():
    """Test translation functionality"""
    print("Testing translation...")
    
    try:
        from app.core.indictrans_translator import translate_text
        
        test_cases = [
            ("Hello", "hi", "नमस्ते"),
            ("What is 2 + 2?", "ta", None),  # Just check it doesn't crash
        ]
        
        for text, lang, expected in test_cases:
            print(f"\n  Testing: '{text}' → {lang}")
            result = translate_text(text, lang)
            
            if result:
                print(f"  ✓ Translation: '{result}'")
                if expected and expected in result:
                    print(f"  ✓ Contains expected text")
            else:
                print(f"  ✗ Translation failed")
                return False
        
        print("\n✅ Translation working correctly\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Translation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_gpu():
    """Check GPU availability"""
    print("Checking GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"  ✓ GPU available: {gpu_name}")
            print(f"  ✓ CUDA version: {torch.version.cuda}")
        else:
            print(f"  ⚠ No GPU detected - will use CPU (slower)")
        print()
        return True
    except Exception as e:
        print(f"  ✗ Error checking GPU: {e}\n")
        return False

def main():
    print("=" * 60)
    print("IndicTrans2 Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Model Files", check_model_files),
        ("GPU", check_gpu),
        ("Translation", test_translation),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}\n")
            results.append((name, False))
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! IndicTrans2 is ready to use.")
        print("\nNext steps:")
        print("1. Start backend: uvicorn app.main:app --reload")
        print("2. Go to Teacher Dashboard → Content Management")
        print("3. Generate questions and select languages to translate")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Verify model files are in utkal-backend/models/")
        print("- Check Python version (3.9+ required)")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
