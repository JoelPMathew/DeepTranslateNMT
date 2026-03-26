"""
Speech Translation API Integration
Endpoints for real-time and batch speech translation
"""
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import StreamingResponse
import tempfile
import os
from typing import Callable, List, Optional

try:
    from .speech_translator import (
        SpeechTranslationPipeline,
        SpeechRecognizer,
        TextToSpeech,
        TranslatedSpeech,
    )
except ImportError:
    from speech_translator import (
        SpeechTranslationPipeline,
        SpeechRecognizer,
        TextToSpeech,
        TranslatedSpeech,
    )

# Create router for speech endpoints
speech_router = APIRouter(prefix="/api/v2/speech", tags=["speech"])


class SpeechTranslationService:
    """Service to manage speech translation pipelines"""
    
    def __init__(self):
        self.pipelines = {}

    def get_pipeline(self, source_lang: str, target_lang: str) -> SpeechTranslationPipeline:
        """Get or create a pipeline for language pair"""
        key = f"{source_lang}-{target_lang}"
        
        if key not in self.pipelines:
            self.pipelines[key] = SpeechTranslationPipeline(
                source_language=source_lang,
                target_language=target_lang
            )
        
        return self.pipelines[key]


# Global service instance
speech_service = SpeechTranslationService()


def _safe_suffix(file: UploadFile) -> str:
    """Return a safe file suffix even when filename is missing."""
    name = file.filename or "audio.wav"
    return os.path.splitext(name)[1] or ".wav"


@speech_router.post("/recognize")
async def recognize_speech(
    file: UploadFile = File(...),
    language: str = Query("en-US", description="Language code (e.g., en-US, es-ES)")
):
    """
    Recognize speech from audio file
    
    Supported formats: WAV, MP3, FLAC, OGG
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=_safe_suffix(file)) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Recognize speech
            recognizer = SpeechRecognizer(language)
            text, confidence = recognizer.recognize_from_audio_file(temp_path)
            
            return {
                "status": "success",
                "text": text,
                "confidence": confidence,
                "language": language
            }
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Speech recognition failed: {str(e)}")


@speech_router.post("/translate")
async def translate_speech(
    file: UploadFile = File(...),
    source_language: str = Query("en-US"),
    target_language: str = Query("es-ES"),
    translator_func: Optional[Callable[[str], str]] = None  # Injected from main app
):
    """
    Complete speech translation: recognize -> translate -> synthesize
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=_safe_suffix(file)) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Get or create pipeline
            pipeline = speech_service.get_pipeline(source_language, target_language)
            
            # Set translator function
            if translator_func:
                pipeline.set_translator(translator_func)
            else:
                # Fallback: use deep-translator
                from deep_translator import GoogleTranslator
                def default_translate(text):
                    trans = GoogleTranslator(
                        source='auto',
                        target=target_language.split('-')[0]
                    )
                    return trans.translate(text)
                
                pipeline.set_translator(default_translate)
            
            # Translate
            result: TranslatedSpeech = pipeline.translate_audio_file(temp_path)
            
            return {
                "status": "success",
                "original_text": result.original_text,
                "original_language": result.original_language,
                "translated_text": result.translated_text,
                "target_language": result.target_language,
                "confidence": result.confidence,
                "audio_available": True
            }
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Speech translation failed: {str(e)}")


@speech_router.post("/synthesize")
async def synthesize_speech(
    text: str = Query(..., min_length=1),
    language: str = Query("en", description="Target language code")
):
    """
    Convert text to speech (TTS)
    """
    try:
        tts = TextToSpeech(language=language)
        audio_bytes = tts.synthesize_to_bytes(text)
        
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=synthesized.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Speech synthesis failed: {str(e)}")


@speech_router.get("/voices")
async def list_available_voices():
    """Get list of available voices for TTS"""
    try:
        tts = TextToSpeech()
        voices = tts.list_voices()
        
        return {
            "status": "success",
            "voices": voices,
            "count": len(voices)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to list voices: {str(e)}")


@speech_router.post("/batch-translate")
async def batch_translate_speeches(
    files: List[UploadFile] = File(...),
    source_language: str = Query("en-US"),
    target_language: str = Query("es-ES")
):
    """
    Translate multiple audio files in batch
    """
    try:
        # Create temporary directory for batch processing
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "output")
        
        try:
            results = []
            
            for file in files:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=_safe_suffix(file),
                    dir=temp_dir
                ) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_path = temp_file.name

                try:
                    # Get pipeline
                    pipeline = speech_service.get_pipeline(source_language, target_language)
                    
                    # Set translator
                    from deep_translator import GoogleTranslator
                    def translate_func(text):
                        trans = GoogleTranslator(
                            source='auto',
                            target=target_language.split('-')[0]
                        )
                        return trans.translate(text)
                    
                    pipeline.set_translator(translate_func)
                    
                    # Translate
                    result = pipeline.translate_audio_file(temp_path)
                    results.append({
                        "filename": file.filename or "unknown",
                        "original_text": result.original_text,
                        "translated_text": result.translated_text,
                        "confidence": result.confidence
                    })
                except Exception as e:
                    results.append({
                        "filename": file.filename or "unknown",
                        "error": str(e)
                    })
                finally:
                    os.unlink(temp_path)
            
            return {
                "status": "success",
                "processed": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r]),
                "results": results
            }
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch translation failed: {str(e)}")


@speech_router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for speech translation"""
    pipeline = SpeechTranslationPipeline()
    languages = pipeline.get_supported_languages()
    
    return {
        "status": "success",
        "languages": languages,
        "count": len(languages)
    }


# Export router for integration into main app
__all__ = ['speech_router', 'SpeechTranslationService', 'speech_service']
