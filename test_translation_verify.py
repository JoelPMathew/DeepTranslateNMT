#!/usr/bin/env python3
"""Verify translation is working correctly by testing both directions."""
import requests
import json

BASE_URL = "http://127.0.0.1:6000"

def test_translation(text, source_lang, target_lang):
    """Test a single translation request."""
    payload = {
        "text": text,
        "source_language": source_lang,
        "target_language": target_lang,
        "style": "formal"
    }
    
    print(f"\n{'='*60}")
    print(f"Test: {source_lang} → {target_lang}")
    print(f"Input: {repr(text)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v2/translate", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Provider: {data.get('provider', 'N/A')}")
        print(f"Cached: {data.get('cached', 'N/A')}")
        print(f"Translated: {repr(data.get('translated_text', 'ERROR'))}")
        print(f"Confidence: {data.get('confidence', 'N/A')}")
        
        # Verify provider is Google
        if data.get('provider') != 'google':
            print(f"⚠️  WARNING: Provider is '{data.get('provider')}', not 'google'!")
        else:
            print(f"✓ Using Google Translate provider")
            
        return data
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

# Test Cases
print("TRANSLATION VERIFICATION TEST")
print("Testing English ↔ Tamil translations")

# Test 1: English → Tamil (should return Tamil script)
print("\n[Test 1] English → Tamil")
result1 = test_translation("Hello my friend", "en", "ta")

# Test 2: Tamil → English (should return English)
print("\n[Test 2] Tamil → English")
result2 = test_translation("வணக்கம்", "ta", "en")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
if result1 and result2:
    trans_text_1 = result1.get('translated_text', '')
    trans_text_2 = result2.get('translated_text', '')
    
    # Check that Tamil→English returns English (roughly)
    if any(char in trans_text_2 for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        print("✓ Tamil → English: Returns English text")
    else:
        print("❌ Tamil → English: Does NOT return English text")
    
    # Check that English→Tamil returns Tamil (roughly Unicode range for Tamil)
    tamil_check = any(ord(char) >= 0x0B80 and ord(char) <= 0x0BFF for char in trans_text_1)
    if tamil_check:
        print("✓ English → Tamil: Returns Tamil script")
    else:
        print("❌ English → Tamil: Does NOT return Tamil script")
    
    if result1.get('provider') == 'google' and result2.get('provider') == 'google':
        print("✓ Both translations used Google provider")
    else:
        print("❌ Not all translations used Google provider")
else:
    print("❌ Tests failed - see errors above")
