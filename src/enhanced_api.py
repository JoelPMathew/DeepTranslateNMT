"""
Enhanced FastAPI Server with Multi-Language and Document Translation.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import asyncio
import logging
import os
from pathlib import Path
import json
import re
from difflib import SequenceMatcher
try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class LightweightRegistry:
    """Lightweight language registry that avoids model-framework imports at API startup."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def supports_language_pair(self, src_lang: str, tgt_lang: str) -> bool:
        pair_key = f"{src_lang}-{tgt_lang}"
        pair_config = self.config.get("language_pairs", {}).get(pair_key, {})
        return pair_config.get("supported", False)

    def get_supported_languages(self) -> dict:
        return {
            code: cfg.get("name", code)
            for code, cfg in self.config.get("languages", {}).items()
            if cfg.get("is_supported", True)
        }

    def get_supported_language_pairs(self) -> dict:
        return {
            pair: cfg
            for pair, cfg in self.config.get("language_pairs", {}).items()
            if cfg.get("supported", False)
        }

    def get_language_config(self, lang_code: str) -> dict:
        if lang_code not in self.config.get("languages", {}):
            raise ValueError(f"Language not supported: {lang_code}")
        return self.config["languages"][lang_code]


class NoopModelLoader:
    """No-op model loader for API management endpoints."""

    def list_cached_models(self) -> List[str]:
        return []

    def clear_cache(self):
        return None

try:
    from .language_detector import LanguageDetector, Language
    from .document_translator import DocumentParser, TranslationMemory, DocumentFormat
    from .ollama_translator import OllamaTranslator
    from .cloud_llm_translator import CloudLLMTranslator
except ImportError:
    # Fallback for direct execution
    from language_detector import LanguageDetector, Language
    from document_translator import DocumentParser, TranslationMemory, DocumentFormat
    from ollama_translator import OllamaTranslator
    from cloud_llm_translator import CloudLLMTranslator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DeepTranslate Pro",
    description="Multi-language Neural Machine Translation with Collaboration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
BASE_DIR = Path(__file__).resolve().parent.parent
registry = LightweightRegistry(str(BASE_DIR / "config" / "language_registry.json"))
model_loader = NoopModelLoader()
language_detector = LanguageDetector()
translation_memory = TranslationMemory()
cloud_llm_translator = CloudLLMTranslator(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
    model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
)
ollama_translator = OllamaTranslator(
    base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
    model=os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"),
)

GLOSSARY_FILE = BASE_DIR / "data" / "custom_glossary.json"


def _load_glossary() -> Dict[str, str]:
    if not GLOSSARY_FILE.exists():
        return {}
    try:
        with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if str(k).strip() and str(v).strip()}
    except Exception as e:
        logger.warning(f"Failed to load glossary file: {e}")
    return {}


def _save_glossary(glossary: Dict[str, str]) -> None:
    GLOSSARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GLOSSARY_FILE, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False, indent=2)


def _apply_term_lock(text: str, glossary: Dict[str, str]) -> tuple[str, Dict[str, str]]:
    placeholder_map: Dict[str, str] = {}
    protected_text = text
    for idx, (src_term, tgt_term) in enumerate(glossary.items()):
        src_term = src_term.strip()
        tgt_term = tgt_term.strip()
        if not src_term or not tgt_term:
            continue
        token = f"ZXTERM{idx}ZX"
        pattern = re.compile(rf"\b{re.escape(src_term)}\b", re.IGNORECASE)
        if pattern.search(protected_text):
            protected_text = pattern.sub(token, protected_text)
            placeholder_map[token] = tgt_term
    return protected_text, placeholder_map


def _restore_term_lock(text: str, placeholder_map: Dict[str, str]) -> str:
    restored = text
    for token, target_term in placeholder_map.items():
        restored = restored.replace(token, target_term)
    return restored


def _detect_ambiguity_hints(text: str) -> List[str]:
    ambiguous_words = {
        "bank": "Could mean financial institution or river bank.",
        "bat": "Could mean an animal or a sports bat.",
        "lead": "Could mean to guide or the metal lead.",
        "light": "Could mean brightness or not heavy.",
        "right": "Could mean direction or correct/moral right.",
        "fair": "Could mean just/equal or an event.",
        "charge": "Could mean price, electrical charge, or legal accusation.",
    }
    lower_text = text.lower()
    suggestions: List[str] = []
    for word, hint in ambiguous_words.items():
        if re.search(rf"\b{re.escape(word)}\b", lower_text):
            suggestions.append(f"Ambiguous term '{word}' detected. {hint} Add context and retry.")
    return suggestions


def _build_recovery_suggestions(
    original_text: str,
    quality_score: float,
    used_cache: bool,
    low_quality_reason: Optional[str] = None,
) -> List[str]:
    suggestions = _detect_ambiguity_hints(original_text)
    if quality_score < 0.65:
        suggestions.append("Low confidence detected. Try shorter sentences and avoid idioms.")
    if used_cache:
        suggestions.append("Result came from translation memory. Disable cache if you want a fresh translation.")
    if low_quality_reason:
        suggestions.append(low_quality_reason)
    if not suggestions:
        suggestions.append("If output sounds off, add audience mode and glossary terms for stricter control.")
    return suggestions


def _audience_style_note(audience: str) -> str:
    audience_notes = {
        "general": "Balanced phrasing for everyday use.",
        "student": "Simplified tone for learning contexts.",
        "professional": "Formal and workplace-appropriate tone.",
        "marketing": "More engaging and persuasive wording.",
        "technical": "Terminology-preserving, precision-first style.",
    }
    return audience_notes.get(audience, "Audience mode applied.")


def _apply_style_variant(text: str, style: str, target_language: str) -> str:
    """Apply deterministic style rewrite so formal/casual/neutral produce distinct outputs."""
    normalized_style = (style or "formal").strip().lower()
    if normalized_style not in {"formal", "neutral", "casual"}:
        normalized_style = "formal"

    output = text.strip()
    if not output:
        return output

    # Apply language-aware tone markers for non-English targets.
    if target_language != "en":
        output = re.sub(r"\s+", " ", output).strip()

        greeting_map = {
            "ta": {
                "formal": [("ஹலோ", "வணக்கம்"), ("ஹாய்", "வணக்கம்")],
                "casual": [("வணக்கம்", "ஹாய்")],
            },
            "te": {
                "formal": [("హలో", "నమస్కారం"), ("హాయ్", "నమస్కారం")],
                "casual": [("నమస్కారం", "హాయ్")],
            },
            "kn": {
                "formal": [("ಹಲೋ", "ನಮಸ್ಕಾರ"), ("ಹಾಯ್", "ನಮಸ್ಕಾರ")],
                "casual": [("ನಮಸ್ಕಾರ", "ಹಾಯ್")],
            },
            "ml": {
                "formal": [("ഹലോ", "നമസ്കാരം"), ("ഹായ്", "നമസ്കാരം")],
                "casual": [("നമസ്കാരം", "ഹായ്")],
            },
            "hi": {
                "formal": [("हेलो", "नमस्कार"), ("हाय", "नमस्कार")],
                "casual": [("नमस्कार", "हाय")],
            },
        }

        lang_rules = greeting_map.get(target_language, {})
        if normalized_style in {"formal", "casual"}:
            for src_term, dst_term in lang_rules.get(normalized_style, []):
                output = output.replace(src_term, dst_term)

        if normalized_style == "formal":
            output = output.rstrip("!")
            if output and output[-1] not in ".!?":
                output += "."
            return output

        if normalized_style == "casual":
            output = output.rstrip(".")
            if output and output[-1] not in "!?":
                output += "!"
            return output

        # Neutral preserves lexical choices and uses light punctuation.
        output = output.rstrip()
        if output.endswith("!"):
            output = output[:-1]
        return output

    # Keep punctuation stable first.
    output = re.sub(r"\s+", " ", output).strip()

    if normalized_style == "formal":
        formal_rules = [
            (r"\bcan't\b", "cannot"),
            (r"\bwon't\b", "will not"),
            (r"\bdon't\b", "do not"),
            (r"\bdoesn't\b", "does not"),
            (r"\bi'm\b", "I am"),
            (r"\bit's\b", "it is"),
            (r"\bthanks\b", "thank you"),
            (r"\bokay\b", "acceptable"),
            (r"\bok\b", "acceptable"),
            (r"\bhi\b", "hello"),
        ]
        for pattern, replacement in formal_rules:
            output = re.sub(pattern, replacement, output, flags=re.IGNORECASE)
        if output and output[-1] not in ".!?":
            output += "."
        output = output[:1].upper() + output[1:]
        return output

    if normalized_style == "casual":
        casual_rules = [
            (r"\bcannot\b", "can't"),
            (r"\bdo not\b", "don't"),
            (r"\bdoes not\b", "doesn't"),
            (r"\bI am\b", "I'm"),
            (r"\bit is\b", "it's"),
            (r"\bhello\b", "hey"),
            (r"\bthank you\b", "thanks"),
            (r"\bacceptable\b", "ok"),
        ]
        for pattern, replacement in casual_rules:
            output = re.sub(pattern, replacement, output, flags=re.IGNORECASE)
        output = output.rstrip(".")
        if output and output[-1] not in "!?":
            output += "!"
        return output

    # Neutral style: keep content plain and avoid extra formality markers.
    output = output.rstrip()
    if output.endswith("."):
        output = output[:-1]
    output = output[:1].upper() + output[1:]
    return output

# Pydantic models
class TranslateRequest(BaseModel):
    text: str
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    style: str = "formal"
    use_translation_memory: bool = True
    audience: str = "general"
    glossary_terms: Dict[str, str] = Field(default_factory=dict)
    return_alternatives: bool = False
    enable_deep_checks: bool = False


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    quality_score: float
    style: str
    audience: str = "general"
    provider: str = "unknown"
    cached: bool = False
    alternatives: List[str] = Field(default_factory=list)
    rationale: str = ""
    back_translation: Optional[str] = None
    recovery_suggestions: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)


class DocumentTranslateRequest(BaseModel):
    filename: str
    format: str
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    preserve_formatting: bool = True


# ============================================================================
# CORE TRANSLATION ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "supported_languages": registry.get_supported_languages(),
        "supported_pairs": list(registry.get_supported_language_pairs().keys())
    }


@app.post("/api/v2/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """
    Translate text with automatic language detection
    """
    try:
        text = request.text.strip()
        if not text:
            raise ValueError("Empty text provided")

        # Auto-detect language if not provided
        if not request.source_language:
            detected_lang, confidence = language_detector.detect_language(text)
            source_language = detected_lang.value
            logger.info(f"Auto-detected language: {source_language} (confidence: {confidence:.2%})")
        else:
            source_language = request.source_language

        # Determine target language
        target_language = request.target_language or (
            "en" if source_language != "en" else "ta"
        )
        audience = (request.audience or "general").strip().lower()
        style = (request.style or "formal").strip().lower()

        persisted_glossary = _load_glossary()
        runtime_glossary = {**persisted_glossary, **(request.glossary_terms or {})}

        protected_input, placeholder_map = _apply_term_lock(text, runtime_glossary)

        # Check if language pair is supported; continue with graceful fallback when unsupported.
        if not registry.supports_language_pair(source_language, target_language):
            logger.warning(
                f"Language pair {source_language}-{target_language} not in registry; using fallback translation path"
            )

        # Build language-aware cache key and canonical form for slang/variant matching
        normalized_text = " ".join(text.lower().split())
        canonical_text = re.sub(r"[^a-z0-9\s]", "", normalized_text)
        canonical_text = " ".join(canonical_text.split())

        # Common slang/variant normalizations
        slang_map = {
            "whats up": "how are you",
            "whatsup": "how are you",
            "watsup": "how are you",
            "wassup": "how are you",
            "sup": "how are you",
            "hey whats up": "how are you",
            "hey whatsup": "how are you",
            "hello whatsup": "how are you",
            "hows it going": "how are you",
            "hows going": "how are you",
        }
        lower_text = slang_map.get(canonical_text, canonical_text)
        glossary_sig = "|".join(sorted(f"{k}:{v}" for k, v in runtime_glossary.items()))
        cache_key = f"{source_language}->{target_language}::{audience}::{style}::{lower_text}::{glossary_sig}"

        alternatives: List[str] = []
        flags: List[str] = []
        provider = "unknown"
        back_translation: Optional[str] = None
        quality_score = 0.6
        rationale = _audience_style_note(audience)

        # Primary provider: Google Translate module
        if GoogleTranslator is not None:
            try:
                translated_text = GoogleTranslator(source=source_language, target=target_language).translate(protected_input)
                translated_text = _restore_term_lock(translated_text, placeholder_map)
                translated_text = _apply_style_variant(translated_text, style, target_language)
                if translated_text and translated_text.strip():
                    provider = "google"

                    if request.enable_deep_checks and request.return_alternatives and cloud_llm_translator.is_configured():
                        try:
                            alt_text, _ = cloud_llm_translator.translate(
                                text=text,
                                source_language=source_language,
                                target_language=target_language,
                                style=style,
                            )
                            alt_text = _restore_term_lock(alt_text, placeholder_map)
                            alt_text = _apply_style_variant(alt_text, style, target_language)
                            if alt_text and alt_text.strip() and alt_text.strip() != translated_text.strip():
                                alternatives.append(alt_text.strip())
                        except Exception as alt_err:
                            logger.info(f"Alternative translation skipped: {alt_err}")

                    similarity_score = 0.75
                    if request.enable_deep_checks and GoogleTranslator is not None:
                        try:
                            back_translation = GoogleTranslator(source=target_language, target=source_language).translate(translated_text)
                            similarity_score = SequenceMatcher(
                                None,
                                text.lower().strip(),
                                (back_translation or "").lower().strip(),
                            ).ratio()
                        except Exception as back_err:
                            logger.info(f"Back-translation check unavailable: {back_err}")

                    confidence = 0.98
                    quality_score = round((confidence * 0.7) + (similarity_score * 0.3), 3)
                    if similarity_score < 0.55:
                        flags.append("meaning_drift_risk")

                    translation_memory.add(cache_key, translated_text)
                    translation_memory.save()
                    recovery_suggestions = _build_recovery_suggestions(
                        original_text=text,
                        quality_score=quality_score,
                        used_cache=False,
                        low_quality_reason="Try adding domain-specific glossary terms to lock critical terms." if similarity_score < 0.55 else None,
                    )
                    return TranslateResponse(
                        original_text=text,
                        translated_text=translated_text,
                        source_language=source_language,
                        target_language=target_language,
                        confidence=confidence,
                        quality_score=quality_score,
                        style=style,
                        audience=audience,
                        provider=provider,
                        cached=False,
                        alternatives=alternatives,
                        rationale=rationale,
                        back_translation=back_translation,
                        recovery_suggestions=recovery_suggestions,
                        flags=flags,
                    )
            except Exception as google_error:
                logger.warning(f"GoogleTranslate failed, falling back: {google_error}")

        # Reliable phrase overrides for common expressions.
        # These are applied before cache/LLM to avoid bad generations for key phrases.
        BASIC_DICT = {
            "hello": {"ta": "வணக்கம்", "te": "హలో", "kn": "ನಮಸ್ಕಾರ", "ml": "ഹലോ", "hi": "नमस्ते"},
            "hi": {"ta": "வணக்கம்", "te": "హాయ్", "kn": "ಹಾಯ್", "ml": "ഹായ്", "hi": "नमस्ते"},
            "how are you": {"ta": "நீ எப்படி இருக்கிறாய்", "te": "నీవు ఎలా ఉన్నావు", "kn": "ನೀವು ಹೇಗಿದ್ದೀರಿ", "ml": "നിങ്ങൾ എങ്ങനെ ഇരിക്കുന്നു", "hi": "आप कैसे हो"},
            "good morning": {"ta": "காலை வணக்கம்", "te": "శుభోదయం", "kn": "ಶುಭೋದಯ", "ml": "സുപ്രഭാതം", "hi": "शुभ प्रभात"},
            "thank you": {"ta": "நன்றி", "te": "ధన్యవాదాలు", "kn": "ಧನ್ಯವಾದ", "ml": "നന്ദി", "hi": "धन्यवाद"},
            "yes": {"ta": "ஆம்", "te": "అవును", "kn": "ಹೌದು", "ml": "അതെ", "hi": "हाँ"},
            "no": {"ta": "இல்லை", "te": "లేదు", "kn": "ಇಲ್ಲ", "ml": "ഇല്ല", "hi": "नहीं"},
        }

        if lower_text in BASIC_DICT and target_language in BASIC_DICT[lower_text]:
            translated_text = BASIC_DICT[lower_text][target_language]
            translated_text = _apply_style_variant(translated_text, style, target_language)
            translation_memory.add(cache_key, translated_text)
            translation_memory.save()
            return TranslateResponse(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.99,
                quality_score=0.99,
                style=style,
                audience=audience,
                provider="dictionary",
                cached=False,
                rationale="High-confidence phrase override from curated dictionary.",
                recovery_suggestions=_build_recovery_suggestions(text, 0.99, False),
            )

        # Check translation memory first
        if request.use_translation_memory:
            cached_translation = translation_memory.lookup(cache_key)
            if cached_translation:
                logger.info("Found in translation memory")
                cached_translation = _apply_style_variant(cached_translation, style, target_language)
                return TranslateResponse(
                    original_text=text,
                    translated_text=cached_translation,
                    source_language=source_language,
                    target_language=target_language,
                    confidence=1.0,
                    quality_score=0.9,
                    style=style,
                    audience=audience,
                    provider="translation_memory",
                    cached=True,
                    rationale="Returned from translation memory for consistency.",
                    recovery_suggestions=_build_recovery_suggestions(text, 0.9, True),
                )

        # Preferred path: LLM translation for non-overridden phrases
        
        translated_text = ""
        confidence = 0.6

        used_llm = False
        if cloud_llm_translator.is_configured():
            try:
                translated_text, confidence = cloud_llm_translator.translate(
                    text=protected_input,
                    source_language=source_language,
                    target_language=target_language,
                    style=style,
                )
                translated_text = _restore_term_lock(translated_text, placeholder_map)
                translated_text = _apply_style_variant(translated_text, style, target_language)
                used_llm = True
                provider = "cloud_llm"
                logger.info("Translated using cloud LLM")
            except Exception as cloud_error:
                logger.warning(f"Cloud LLM translation failed, falling back: {cloud_error}")

        if not used_llm and ollama_translator.is_available() and ollama_translator.model_is_installed():
            try:
                translated_text, confidence = ollama_translator.translate(
                    text=protected_input,
                    source_language=source_language,
                    target_language=target_language,
                    style=style,
                )
                translated_text = _restore_term_lock(translated_text, placeholder_map)
                translated_text = _apply_style_variant(translated_text, style, target_language)
                used_llm = True
                provider = "ollama"
                logger.info("Translated using Ollama LLM")
            except Exception as llm_error:
                logger.warning(f"Ollama translation failed, falling back: {llm_error}")

        if not used_llm:
            if lower_text in BASIC_DICT and target_language in BASIC_DICT[lower_text]:
                translated_text = BASIC_DICT[lower_text][target_language]
                confidence = 0.95
                provider = "dictionary"
                logger.info(f"Dictionary match: {text} -> {translated_text}")
            else:
                # Fallback: simple character mapping or echo
                translated_text = f"[{text}]"
                confidence = 0.5
                provider = "echo_fallback"
                flags.append("fallback_used")
                logger.info(f"No dictionary match, using echo: {translated_text}")

        if not translated_text:
            translated_text = f"[{text}]"
            provider = "echo_fallback"
            flags.append("empty_translation_guard")

        translated_text = _apply_style_variant(translated_text, style, target_language)

        similarity_score = 0.7
        if request.enable_deep_checks and GoogleTranslator is not None and translated_text and provider != "echo_fallback":
            try:
                back_translation = GoogleTranslator(source=target_language, target=source_language).translate(translated_text)
                similarity_score = SequenceMatcher(
                    None,
                    text.lower().strip(),
                    (back_translation or "").lower().strip(),
                ).ratio()
                if similarity_score < 0.55:
                    flags.append("meaning_drift_risk")
            except Exception as back_err:
                logger.info(f"Back-translation check unavailable: {back_err}")

        quality_score = round((confidence * 0.7) + (similarity_score * 0.3), 3)

        # Add to translation memory
        translation_memory.add(cache_key, translated_text)
        translation_memory.save()

        if request.enable_deep_checks and request.return_alternatives and provider != "echo_fallback":
            alt_variants = [
                translated_text.replace("?", ""),
                translated_text.replace("!", "."),
            ]
            alternatives = [a for a in dict.fromkeys(v.strip() for v in alt_variants) if a and a != translated_text][:2]

        recovery_suggestions = _build_recovery_suggestions(
            original_text=text,
            quality_score=quality_score,
            used_cache=False,
            low_quality_reason="Try setting audience to 'technical' and pass glossary terms for domain words." if quality_score < 0.65 else None,
        )

        return TranslateResponse(
            original_text=text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=target_language,
            confidence=confidence,
            quality_score=quality_score,
            style=style,
            audience=audience,
            provider=provider,
            cached=False,
            alternatives=alternatives,
            rationale=rationale,
            back_translation=back_translation,
            recovery_suggestions=recovery_suggestions,
            flags=flags,
        )

    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DOCUMENT TRANSLATION ENDPOINTS
# ============================================================================

@app.post("/api/v2/translate/document")
async def translate_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_language: Optional[str] = None,
    target_language: Optional[str] = None,
    audience: str = "general",
):
    """
    Translate a document (PDF, DOCX, TXT, JSON, Markdown)
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        safe_input_name = Path(file.filename).name
        file_path = upload_dir / safe_input_name

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Detect format
        fmt = DocumentParser.detect_format(str(file_path))
        logger.info(f"Processing {fmt.value} document: {safe_input_name}")

        # Extract segments
        segments = DocumentParser.extract_segments(str(file_path))
        logger.info(f"Extracted {len(segments)} segments")

        # Translate each segment using the same translation pipeline as text mode.
        for seg in segments:
            segment_text = (seg.original or "").strip()
            if not segment_text:
                seg.translated = ""
                continue

            try:
                seg_result = await translate(
                    TranslateRequest(
                        text=segment_text,
                        source_language=source_language,
                        target_language=target_language,
                        style="formal",
                        use_translation_memory=True,
                        audience=audience,
                    )
                )
                seg.translated = seg_result.translated_text
            except Exception as seg_error:
                logger.warning(f"Segment translation failed; keeping original segment. Error: {seg_error}")
                seg.translated = seg.original

        # Reconstruct document
        output_filename = f"translated_{Path(safe_input_name).stem}.txt"
        output_path = f"outputs/{output_filename}"
        
        os.makedirs("outputs", exist_ok=True)
        
        # Save output as text for all source formats so download always works.
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(seg.translated for seg in segments))

        return {
            "filename": safe_input_name,
            "format": fmt.value,
            "segments_count": len(segments),
            "output_file": output_filename,
            "output_path": output_path,
            "download_url": f"/api/v2/outputs/{output_filename}",
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Document translation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v2/outputs/{filename}")
async def download_output_file(filename: str):
    """Download translated output file generated by document translation."""
    safe_name = Path(filename).name
    file_path = Path("outputs") / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename=safe_name, media_type="text/plain")


@app.get("/api/v2/translation-memory/stats")
async def get_translation_memory_stats():
    """Get translation memory statistics"""
    return {
        "stats": translation_memory.get_stats(),
        "memory_file": translation_memory.memory_file
    }


@app.get("/api/v2/translation-memory/lookup")
async def lookup_translation(text: str):
    """Lookup text in translation memory"""
    result = translation_memory.lookup(text)
    return {
        "query": text,
        "found": result is not None,
        "translation": result
    }


@app.get("/api/v2/translation/backend")
async def get_translation_backend_status():
    """Get active translation backend status."""
    return {
        "provider": "google" if GoogleTranslator is not None else ("cloud_llm" if cloud_llm_translator.is_configured() else "ollama"),
        "google_available": GoogleTranslator is not None,
        "cloud_llm_configured": cloud_llm_translator.is_configured(),
        "cloud_llm_model": cloud_llm_translator.model,
        "ollama_url": ollama_translator.base_url,
        "ollama_model": ollama_translator.model,
        "ollama_reachable": ollama_translator.is_available(),
        "model_installed": ollama_translator.model_is_installed(),
        "fallback": "dictionary"
    }


@app.get("/api/v2/glossary")
async def get_glossary():
    """Fetch custom glossary entries used for term lock."""
    return {
        "entries": _load_glossary(),
        "count": len(_load_glossary()),
    }


class GlossaryUpsertRequest(BaseModel):
    entries: Dict[str, str] = Field(default_factory=dict)


@app.post("/api/v2/glossary")
async def upsert_glossary(request: GlossaryUpsertRequest):
    """Add or update glossary entries."""
    glossary = _load_glossary()
    for k, v in request.entries.items():
        key = str(k).strip()
        value = str(v).strip()
        if key and value:
            glossary[key] = value
    _save_glossary(glossary)
    return {
        "status": "updated",
        "count": len(glossary),
        "entries": glossary,
    }


# ============================================================================
# LANGUAGE REGISTRY ENDPOINTS
# ============================================================================

@app.get("/api/v2/languages")
async def get_languages():
    """Get all supported languages"""
    return {
        "languages": registry.get_supported_languages()
    }


@app.get("/api/v2/language-pairs")
async def get_language_pairs():
    """Get all supported language pairs"""
    return {
        "language_pairs": registry.get_supported_language_pairs()
    }


@app.get("/api/v2/language/{lang_code}")
async def get_language_config(lang_code: str):
    """Get configuration for a specific language"""
    try:
        config = registry.get_language_config(lang_code)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v2/models/cache")
async def get_model_cache():
    """Get cached models"""
    return {
        "cached_models": model_loader.list_cached_models()
    }


@app.post("/api/v2/models/cache/clear")
async def clear_model_cache():
    """Clear model cache"""
    model_loader.clear_cache()
    return {"status": "cache cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
