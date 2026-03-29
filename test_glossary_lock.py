#!/usr/bin/env python3
"""Test glossary lock functionality"""
import requests
import json

BASE_URL = "http://127.0.0.1:6000"

def test_glossary_lock():
    """Test that glossary lock protects terms from translation"""
    
    # Test 1: With glossary lock
    print("=" * 60)
    print("TEST 1: Translation WITH glossary lock")
    print("=" * 60)
    
    payload = {
        "text": "Azure is a cloud platform by Microsoft",
        "source_language": "en",
        "target_language": "ta",
        "glossary_terms": {
            "Azure": "Azure",
            "Microsoft": "Microsoft"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/translate", json=payload)
    data = response.json()
    
    print(f"Input: {payload['text']}")
    print(f"Glossary: {payload['glossary_terms']}")
    print(f"Output: {data['translated_text']}")
    print(f"Provider: {data['provider']}")
    
    # Check if glossary terms are preserved
    if "Azure" in data['translated_text'] and "Microsoft" in data['translated_text']:
        print("✓ Glossary lock WORKING - terms preserved")
    else:
        print("✗ Glossary lock NOT WORKING - terms were modified")
    
    # Test 2: Without glossary lock
    print("\n" + "=" * 60)
    print("TEST 2: Translation WITHOUT glossary lock")
    print("=" * 60)
    
    payload2 = {
        "text": "Azure is a cloud platform by Microsoft",
        "source_language": "en",
        "target_language": "ta",
        "glossary_terms": {}  # Empty glossary
    }
    
    response2 = requests.post(f"{BASE_URL}/api/v2/translate", json=payload2)
    data2 = response2.json()
    
    print(f"Input: {payload2['text']}")
    print(f"Glossary: (empty)")
    print(f"Output: {data2['translated_text']}")
    print(f"Provider: {data2['provider']}")
    
    if "Azure" in data2['translated_text'] and "Microsoft" in data2['translated_text']:
        print("✗ Terms preserved even without glossary (unexpected)")
    else:
        print("✓ Terms modified without glossary (expected)")
    
    # Test 3: Tamil source with glossary lock
    print("\n" + "=" * 60)
    print("TEST 3: Tamil → English WITH glossary lock")
    print("=" * 60)
    
    tamil_text = "நான் Google Workspace ஐ பயன்படுத்துகிறேன்"
    payload3 = {
        "text": tamil_text,
        "source_language": "ta",
        "target_language": "en",
        "glossary_terms": {
            "Google Workspace": "Google Workspace"
        }
    }
    
    response3 = requests.post(f"{BASE_URL}/api/v2/translate", json=payload3)
    data3 = response3.json()
    
    print(f"Input: {tamil_text}")
    print(f"Glossary: {payload3['glossary_terms']}")
    print(f"Output: {data3['translated_text']}")
    
    if "Google Workspace" in data3['translated_text']:
        print("✓ Brand name preserved in translation")
    else:
        print("✗ Brand name was translated/modified")

if __name__ == "__main__":
    try:
        test_glossary_lock()
    except Exception as e:
        print(f"Error: {e}")
