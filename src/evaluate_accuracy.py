import torch
from src.nllb_inference import NLLBTranslator
from src.transliterate_utils import transliterate_tanglish
import os
import pandas as pd
try:
    from peft import PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False

def evaluate():
    test_cases = [
        {"tanglish": "eppadi irukinga?", "expected": "How are you?", "style": "spoken"},
        {"tanglish": "saaptiya?", "expected": "Did you eat?", "style": "casual"},
        {"tanglish": "enna da soldra?", "expected": "What are you saying?", "style": "casual"},
        {"tanglish": "eppa varuva?", "expected": "When will you come?", "style": "spoken"},
        {"tanglish": "kai kadikkidhu", "expected": "It's expensive", "style": "casual"},
        {"tanglish": "veetukku poren", "expected": "I'm going home", "style": "spoken"},
        {"tanglish": "enna vishayam mashi?", "expected": "What's the matter man?", "style": "chennai"}
    ]
    
    adapter_path = os.path.join(os.getcwd(), "nllb_lora_refined", "best_model")
    
    results = []
    
    print("--- Loading Base Model ---")
    translator = NLLBTranslator()
    
    print("--- Running Base Evaluation ---")
    base_outputs = []
    for case in test_cases:
        tamil_script = transliterate_tanglish(case["tanglish"])
        out = translator.translate(tamil_script, style="standard")
        base_outputs.append(out)
        print(f"Base: {case['tanglish']} -> {out}")

    print("\n--- Loading Adapter (In-Place) ---")
    if PEFT_AVAILABLE and os.path.exists(adapter_path):
        translator.model = PeftModel.from_pretrained(translator.model, adapter_path, low_cpu_mem_usage=True).to(translator.device)
        print("Adapter Loaded.")
    else:
        print("Adapter skip (not found or peft missing)")

    print("--- Running Enhanced Evaluation ---")
    enhanced_outputs = []
    for case in test_cases:
        tamil_script = transliterate_tanglish(case["tanglish"])
        out = translator.translate(tamil_script, style=case["style"])
        enhanced_outputs.append(out)
        print(f"Enhanced: {case['tanglish']} ({case['style']}) -> {out}")

    for idx, case in enumerate(test_cases):
        results.append({
            "Tanglish": case["tanglish"],
            "Expected": case["expected"],
            "Base": base_outputs[idx],
            "Enhanced": enhanced_outputs[idx],
            "Style": case["style"]
        })
    
    df = pd.DataFrame(results)
    print("\n--- Evaluation Results ---")
    print(df.to_string(index=False))
    
    df.to_csv("data/evaluation_results.csv", index=False)
    print("\nResults saved to data/evaluation_results.csv")

if __name__ == "__main__":
    evaluate()
