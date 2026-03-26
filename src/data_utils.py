import unicodedata
import re
import os

def normalize_tamil(text):
    """
    Performs Unicode normalization (NFC) for Tamil text and basic cleaning.
    """
    # Unicode normalization to NFC
    text = unicodedata.normalize('NFC', text)
    
    # Remove redundant whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_english(text):
    """
    Basic preprocessing for English text.
    """
    text = text.lower()
    # Remove redundant whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_parallel_data(src_file, tgt_file, out_src, out_tgt, src_lang='en', tgt_lang='ta'):
    """
    Cleans and normalizes parallel data.
    """
    with open(src_file, 'r', encoding='utf-8') as f_src, \
         open(tgt_file, 'r', encoding='utf-8') as f_tgt, \
         open(out_src, 'w', encoding='utf-8') as o_src, \
         open(out_tgt, 'w', encoding='utf-8') as o_tgt:
        
        for src_line, tgt_line in zip(f_src, f_tgt):
            src_line = src_line.strip()
            tgt_line = tgt_line.strip()
            
            if not src_line or not tgt_line:
                continue
            
            if src_lang == 'en':
                src_line = preprocess_english(src_line)
            elif src_lang == 'ta':
                src_line = normalize_tamil(src_line)
                
            if tgt_lang == 'ta':
                tgt_line = normalize_tamil(tgt_line)
            elif tgt_lang == 'en':
                tgt_line = preprocess_english(tgt_line)
                
            o_src.write(src_line + '\n')
            o_tgt.write(tgt_line + '\n')

if __name__ == "__main__":
    # Example usage / debug
    sample_tamil = "தமிழ் மொழி"
    normalized = normalize_tamil(sample_tamil)
    print(f"Original: {sample_tamil}, Normalized: {normalized}")
