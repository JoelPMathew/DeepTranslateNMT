import sacrebleu
from .nllb_inference import NLLBTranslator
import pandas as pd

def evaluate_nllb(csv_path):
    df = pd.read_csv(csv_path)
    translator = NLLBTranslator()
    
    references = df["english"].tolist()
    sources = df["tamil"].tolist()
    
    print(f"Translating {len(sources)} sentences for evaluation...")
    predictions = translator.translate_batch(sources)
    
    bleu = sacrebleu.corpus_bleu(predictions, [references])
    chrf = sacrebleu.corpus_chrf(predictions, [references])
    
    print(f"--- Evaluation Results ---")
    print(f"BLEU: {bleu.score:.2f}")
    print(f"chrF: {chrf.score:.2f}")
    
    return bleu.score

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    evaluate_nllb(args.csv)
