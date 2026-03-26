import pandas as pd
import os

def prepare_data(src_file, tgt_file, output_csv):
    print(f"Reading {src_file} and {tgt_file}...")
    with open(src_file, 'r', encoding='utf-8') as f:
        src_lines = [line.strip() for line in f.readlines()]
    with open(tgt_file, 'r', encoding='utf-8') as f:
        tgt_lines = [line.strip() for line in f.readlines()]
    
    # Ensure they have the same length
    min_len = min(len(src_lines), len(tgt_lines))
    src_lines = src_lines[:min_len]
    tgt_lines = tgt_lines[:min_len]
    
    df = pd.DataFrame({
        'tamil': tgt_lines, # Original data: .en is English, .ta is Tamil. 
        'english': src_lines
    })
    
    # Actually, let's check which is which. 
    # Based on train.en vs train.ta:
    # train.en: 1: Hello
    # train.ta: 1: வணக்கம்
    # So .ta is Tamil, .en is English.
    
    df.to_csv(output_csv, index=False)
    print(f"Saved {len(df)} rows to {output_csv}")

if __name__ == "__main__":
    prepare_data('data/train.en', 'data/train.ta', 'data/nllb_train.csv')
