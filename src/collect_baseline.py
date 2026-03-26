import torch
from src.nllb_inference import NLLBTranslator
from src.transliterate_utils import transliterate_tanglish
import pandas as pd

def collect_baseline():
    test_cases = [
        {"tanglish": "eppadi irukinga?", "expected": "How are you?", "style": "spoken"},
        {"tanglish": "saaptiya?", "expected": "Did you eat?", "style": "casual"},
        {"tanglish": "enna da soldra?", "expected": "What are you saying?", "style": "casual"},
        {"tanglish": "eppa varuva?", "expected": "When will you come?", "style": "spoken"},
        {"tanglish": "kai kadikkidhu", "expected": "It's expensive", "style": "casual"},
        {"tanglish": "veetukku poren", "expected": "I'm going home", "style": "spoken"},
        {"tanglish": "enna vishayam mashi?", "expected": "What's the matter man?", "style": "chennai"}
    ]
    
    print("--- Loading Base Model (No Adapters) ---")
    translator = NLLBTranslator() # Loads base model
    
    results = []
    print("--- Collecting Base Outputs ---")
    for case in test_cases:
        tamil_script = transliterate_tanglish(case["tanglish"])
        # Use standard mode for base model
        out = translator.translate(tamil_script, style="standard")
        print(f"Base: {case['tanglish']} -> {out}")
        results.append({
            "Tanglish": case["tanglish"],
            "Tamil": tamil_script,
            "Expected": case["expected"],
            "Base_Output": out,
            "Style": case["style"]
        })
    
    df = pd.DataFrame(results)
    df.to_csv("data/base_baseline.csv", index=False)
    print("\nBaseline saved to data/base_baseline.csv")

if __name__ == "__main__":
    collect_baseline()
