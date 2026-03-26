import torch
from src.nllb_inference import NLLBTranslator
import os

def test_comparison():
    phrases = [
        "enna da soldra",
        "eppadi irukinga?",
        "saaptiya?",
        "enna vishayam?"
    ]
    
    print("=== BASE MODEL ===")
    base_translator = NLLBTranslator()
    for p in phrases:
        print(f"Tanglish: {p}")
        tamil = base_translator.translate(p, src_lang="tam_Taml", tgt_lang="eng_Latn") # wait, tam_Taml is for Tamil script
        # Let's use it as a probe
        print(f"Result: {tamil}")

    print("\n=== ENHANCED MODEL ===")
    adapter_path = os.path.join(os.getcwd(), "nllb_lora_results", "best_model")
    enhanced_translator = NLLBTranslator(adapter_path=adapter_path)
    for p in phrases:
        print(f"Tanglish: {p}")
        # Note: We need to transliterate first for best results
        from src.transliterate_utils import transliterate_tanglish
        tamil_script = transliterate_tanglish(p)
        result = enhanced_translator.translate(tamil_script, style="casual")
        print(f"Tamil: {tamil_script} -> Translation: {result}")

if __name__ == "__main__":
    test_comparison()
