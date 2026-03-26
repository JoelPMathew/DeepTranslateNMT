import torch
from src.nllb_inference import NLLBTranslator
import os
from src.transliterate_utils import transliterate_tanglish

def test_enhanced():
    phrases = [
        "enna da soldra",
        "eppadi irukinga?",
        "saaptiya?"
    ]
    
    print("=== TESTING ENHANCED MODEL ===")
    adapter_path = os.path.join(os.getcwd(), "nllb_lora_results", "best_model")
    translator = NLLBTranslator(adapter_path=adapter_path)
    
    for p in phrases:
        print(f"\nTanglish: {p}")
        tamil_script = transliterate_tanglish(p)
        print(f"Tamil Script: {tamil_script}")
        # Test with casual style
        result = translator.translate(tamil_script, style="casual")
        print(f"Enhanced Translation: {result}")

if __name__ == "__main__":
    test_enhanced()
