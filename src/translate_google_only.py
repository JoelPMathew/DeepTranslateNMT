"""
Pure Google Translate endpoint - replaces the complex /api/v2/translate route
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class SimpleTranslateRequest(BaseModel):
    text: str
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    style: str = "formal"
    audience: str = "general"
    glossary_terms: Dict[str, str] = {}
    enable_deep_checks: bool = False


class SimpleTranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 0.98
    quality_score: float = 0.90
    provider: str = "google"
    cached: bool = False
    flags: List[str] = []


def create_google_translate_endpoint(app, language_detector, GoogleTranslator, 
                                     SUPPORTED_LANG_CODES, _apply_term_lock, 
                                     _restore_term_lock, _apply_style_variant, 
                                     _build_recovery_suggestions, _audience_style_note,
                                     translation_memory, _load_glossary):
    """Factory to create pure Google Translate endpoint with all dependencies"""

    @app.post("/api/v2/translate", response_model=SimpleTranslateResponse)
    async def translate_google_only(request: SimpleTranslateRequest):
        """
        GOOGLE TRANSLATE ONLY - No fallback routes.
        All translations must go through Google Translate API.
        """
        req_id = id(request)
        logger.info(f"[{req_id}] ▶ GOOGLE-ONLY /api/v2/translate")
        
        try:
            # ============ INPUT VALIDATION ============
            text = request.text.strip() if request.text else ""
            if not text:
                raise ValueError("Empty text")

            # ============ LANGUAGE ROUTING ============
            # Source
            if request.source_language:
                source_language = request.source_language.strip().lower()
            else:
                detected, conf = language_detector.detect_language(text)
                source_language = detected.value
                logger.info(f"  [auto-detect] source={source_language} ({conf:.0%})")

            if source_language not in SUPPORTED_LANG_CODES:
                raise ValueError(f"Bad source language: {source_language}")

            # Target
            target_language = (request.target_language.strip().lower() if request.target_language else None) or (
                "en" if source_language != "en" else "ta"
            )
            if target_language not in SUPPORTED_LANG_CODES:
                raise ValueError(f"Bad target language: {target_language}")

            logger.info(f"  [route] {source_language} → {target_language}")

            # ============ GLOSSARY LOCK ============
            glossary = {**_load_glossary(), **(request.glossary_terms or {})}
            protected, placeholder_map = _apply_term_lock(text, glossary)

            # ============ GOOGLE TRANSLATE (MANDATORY) ============
            if GoogleTranslator is None:
                raise RuntimeError("GoogleTranslator not available")

            try:
                result = GoogleTranslator(source=source_language, target=target_language).translate(protected)
                if result is None:
                    raise RuntimeError("Google returned None")
                result = str(result).strip()
                if not result:
                    raise RuntimeError("Google returned empty")
            except Exception as e:
                logger.error(f"  [google error] {e}")
                raise RuntimeError(f"Google failed: {e}")

            # Restore glossary terms
            result = _restore_term_lock(result, placeholder_map)
            result = _apply_style_variant(result, request.style, target_language)

            logger.info(f"  [✓] {result[:60]}")

            # ============ CACHE & RESPONSE ============
            cache_key = f"{source_language}-{target_language}:{text[:50]}"
            translation_memory.add(cache_key, result)
            translation_memory.save()

            suggestions = _build_recovery_suggestions(text, 0.9, False)
            rationale = _audience_style_note(request.audience)

            logger.info(f"[{req_id}] ✓ Translated (provider=google, conf=0.98, qual=0.90)")
            
            return SimpleTranslateResponse(
                original_text=text,
                translated_text=result,
                source_language=source_language,
                target_language=target_language,
                confidence=0.98,
                quality_score=0.90,
                provider="google",
                cached=False,
                flags=[],
            )

        except ValueError as e:
            logger.error(f"[{req_id}] ValidationError: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            logger.error(f"[{req_id}] RuntimeError: {e}")
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            logger.error(f"[{req_id}] Unexpected: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Server error: {type(e).__name__}")