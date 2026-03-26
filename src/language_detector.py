"""
Language Detection Module
Automatically detects the source language and maps to appropriate models.
"""
import re
from typing import Tuple, Dict
from enum import Enum


class Language(Enum):
    """Supported languages with ISO-639 codes"""
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"
    HINDI = "hi"
    ENGLISH = "en"


class LanguageScript(Enum):
    """Script types for language families"""
    INDIC = "indic"  # All Indian scripts
    LATIN = "latin"  # Roman script (Tanglish)
    ENGLISH = "english"


# Unicode ranges for Indian scripts
SCRIPT_RANGES = {
    Language.TAMIL: (0x0B80, 0x0BFF),
    Language.TELUGU: (0x0C60, 0x0C7F),
    Language.KANNADA: (0x0C80, 0x0CFF),
    Language.MALAYALAM: (0x0D00, 0x0D7F),
    Language.HINDI: (0x0900, 0x097F),
}

# Language name mappings
LANGUAGE_NAMES = {
    Language.TAMIL: "Tamil",
    Language.TELUGU: "Telugu",
    Language.KANNADA: "Kannada",
    Language.MALAYALAM: "Malayalam",
    Language.HINDI: "Hindi",
    Language.ENGLISH: "English",
}


class LanguageDetector:
    """Detects language from text using script analysis and heuristics"""

    @staticmethod
    def detect_language(text: str) -> Tuple[Language, float]:
        """
        Detect the language of the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (Language, confidence_score)
        """
        if not text or not text.strip():
            return Language.ENGLISH, 0.0

        # Calculate script distribution
        script_counts = LanguageDetector._count_scripts(text)
        
        if not script_counts:
            return Language.ENGLISH, 0.5

        # Find dominant language
        dominant_lang = max(script_counts.items(), key=lambda x: x[1])
        lang, count = dominant_lang
        
        # Calculate confidence (percentage of detected script)
        total_chars = sum(script_counts.values())
        confidence = count / total_chars if total_chars > 0 else 0.0

        return lang, confidence

    @staticmethod
    def _count_scripts(text: str) -> Dict[Language, int]:
        """Count occurrences of each language script"""
        counts = {lang: 0 for lang in Language}
        
        for char in text:
            char_code = ord(char)
            for lang, (start, end) in SCRIPT_RANGES.items():
                if start <= char_code <= end:
                    counts[lang] += 1
                    break
        
        # Remove zero counts
        return {lang: count for lang, count in counts.items() if count > 0}

    @staticmethod
    def is_tanglish(text: str) -> bool:
        """Detect if text is Tanglish (Tamil in Roman script)"""
        # Common Tanglish patterns
        tamil_patterns = [
            r'\b(naan|nee|avarkal)\b',  # Tamil pronouns in Latin
            r'\b(enna|yaaru|enna)\b',  # Common Tamil words
            r'(aiya|da|pa|maama)\b',  # Tamil suffixes
            r'(thambi|thangai|machan)\b',  # Tamil relationship words
        ]
        
        for pattern in tamil_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    @staticmethod
    def get_target_language(source_lang: Language) -> Language:
        """
        Get the default target language for translation.
        For now, all Indian languages translate to English.
        """
        if source_lang == Language.ENGLISH:
            return Language.TAMIL  # Default: English to Tamil
        return Language.ENGLISH

    @staticmethod
    def get_language_name(lang: Language) -> str:
        """Get human-readable language name"""
        return LANGUAGE_NAMES.get(lang, "Unknown")


# Example usage
if __name__ == "__main__":
    test_texts = [
        ("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", Language.TAMIL),
        ("నమస్కారం, మీరు ఎలా ఉన్నారు?", Language.TELUGU),
        ("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?", Language.KANNADA),
        ("നമസ്കാരം, നിങ്ങൾ എങ്ങനെ ഉണ്ട്?", Language.MALAYALAM),
        ("नमस्ते, आप कैसे हैं?", Language.HINDI),
        ("Hello, how are you?", Language.ENGLISH),
    ]

    detector = LanguageDetector()
    for text, expected in test_texts:
        detected, confidence = detector.detect_language(text)
        print(f"Text: {text[:30]}...")
        print(f"Expected: {expected.name}, Detected: {detected.name}, Confidence: {confidence:.2%}\n")
