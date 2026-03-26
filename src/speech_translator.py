"""
Speech Translation Module
Handles real-time speech-to-speech translation with support for multiple languages.
Includes speech recognition, translation, and text-to-speech synthesis.
"""
import os
from typing import Optional, Dict, Tuple, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
import tempfile
from pathlib import Path


class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"


@dataclass
class SpeechSegment:
    """Represents a speech segment with timing and language info"""
    text: str
    confidence: float  # 0.0 to 1.0
    language: str
    duration: float  # in seconds
    start_time: float
    end_time: float


@dataclass
class TranslatedSpeech:
    """Represents translated speech output"""
    original_text: str
    original_language: str
    translated_text: str
    target_language: str
    original_audio: bytes
    translated_audio: bytes
    confidence: float


class SpeechRecognizer:
    """Speech recognition using multiple backends"""

    def __init__(self, language: str = "en-US"):
        self.language = language
        self.backend = self._init_backend()

    def _init_backend(self):
        """Initialize speech recognition backend"""
        try:
            import speech_recognition as sr  # type: ignore[reportMissingImports]
            return sr.Recognizer()
        except ImportError:
            raise ImportError(
                "speech_recognition required for speech features. "
                "Install with: pip install SpeechRecognition"
            )

    def recognize_from_audio_file(self, file_path: str) -> Tuple[str, float]:
        """
        Recognize speech from audio file
        
        Args:
            file_path: Path to audio file (WAV, MP3, etc.)
            
        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        try:
            import speech_recognition as sr  # type: ignore[reportMissingImports]
        except ImportError:
            raise ImportError("speech_recognition required")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        recognizer = sr.Recognizer()
        
        # Detect audio format and load accordingly
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext in ['.wav', '.flac']:
                with sr.AudioFile(file_path) as source:
                    audio_data = recognizer.record(source)
            elif file_ext == '.mp3':
                # Convert MP3 to WAV first
                audio_data = self._convert_mp3_to_wav(file_path)
            else:
                raise ValueError(f"Unsupported audio format: {file_ext}")

            # Perform recognition
            try:
                text = recognizer.recognize_google(audio_data, language=self.language)
                confidence = 0.95  # Google API doesn't expose confidence directly
                return text, confidence
            except sr.UnknownValueError:
                return "", 0.0
            except sr.RequestError as e:
                raise RuntimeError(f"Speech recognition service error: {e}")
                
        except Exception as e:
            raise RuntimeError(f"Error processing audio file: {e}")

    def recognize_from_microphone(self, timeout: int = 10) -> Tuple[str, float]:
        """
        Recognize speech from microphone input
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        try:
            import speech_recognition as sr  # type: ignore[reportMissingImports]
        except ImportError:
            raise ImportError("speech_recognition required")

        recognizer = sr.Recognizer()
        
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio_data = recognizer.listen(source, timeout=timeout)
                
            print("Processing...")
            text = recognizer.recognize_google(audio_data, language=self.language)
            return text, 0.95
            
        except sr.UnknownValueError:
            return "", 0.0
        except sr.RequestError as e:
            raise RuntimeError(f"Speech recognition service error: {e}")
        except sr.WaitTimeoutError:
            return "", 0.0

    @staticmethod
    def _convert_mp3_to_wav(mp3_path: str) -> Any:
        """Convert MP3 to WAV format for processing"""
        try:
            from pydub import AudioSegment  # type: ignore[reportMissingImports]
            import speech_recognition as sr  # type: ignore[reportMissingImports]
        except ImportError:
            raise ImportError("pydub required for MP3 support. Install with: pip install pydub")

        audio = AudioSegment.from_mp3(mp3_path)
        
        # Export to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            audio.export(temp_wav.name, format="wav")
            
            # Load the WAV file
            with sr.AudioFile(temp_wav.name) as source:
                recognizer = sr.Recognizer()
                audio_data = recognizer.record(source)
            
            # Clean up temp file
            os.unlink(temp_wav.name)
            
        return audio_data

    def detect_language(self, audio_file: str) -> str:
        """
        Detect language from audio file
        
        Returns:
            Detected language code (e.g., 'en', 'es', 'fr')
        """
        # Placeholder implementation. Full language ID requires configured cloud backend.
        return self.language.split('-')[0]


class TextToSpeech:
    """Text-to-speech synthesis"""

    def __init__(self, language: str = "en", voice: str = "default"):
        self.language = language
        self.voice = voice
        self.engine = self._init_engine()

    def _init_engine(self):
        """Initialize TTS engine"""
        try:
            import pyttsx3  # type: ignore[reportMissingImports]
            engine = pyttsx3.init()
            
            # Set language/voice properties
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)  # Volume
            
            return engine
        except ImportError:
            raise ImportError(
                "pyttsx3 required for TTS features. "
                "Install with: pip install pyttsx3"
            )

    def synthesize_to_file(self, text: str, output_file: str) -> str:
        """
        Synthesize text to speech and save to file
        
        Args:
            text: Text to synthesize
            output_file: Path to output audio file
            
        Returns:
            Path to generated audio file
        """
        try:
            import pyttsx3  # type: ignore[reportMissingImports]
        except ImportError:
            raise ImportError("pyttsx3 required")

        engine = pyttsx3.init()
        engine.save_to_file(text, output_file)
        engine.runAndWait()
        
        return output_file

    def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Synthesize text to speech and return as bytes
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as bytes
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            self.synthesize_to_file(text, temp_path)
            
            # Read the file into bytes
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
            
            return audio_bytes
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def list_voices(self) -> Dict[str, str]:
        """List available voices"""
        try:
            import pyttsx3  # type: ignore[reportMissingImports]
        except ImportError:
            raise ImportError("pyttsx3 required")

        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        voice_dict = {}
        for voice in voices:
            voice_dict[voice.id] = {
                'name': voice.name,
                'languages': voice.languages,
                'gender': voice.gender if hasattr(voice, 'gender') else 'unknown'
            }
        
        return voice_dict


class SpeechTranslationPipeline:
    """Complete speech-to-speech translation pipeline"""

    def __init__(self, source_language: str = "en-US", target_language: str = "es"):
        self.source_language = source_language
        self.target_language = target_language
        self.recognizer = SpeechRecognizer(source_language)
        self.tts = TextToSpeech(target_language)
        self.translator: Optional[Callable[[str], str]] = None  # Will be injected from main app

    def set_translator(self, translator_func: Callable[[str], str]):
        """Set the translation function"""
        self.translator = translator_func

    def translate_audio_file(self, audio_file: str) -> TranslatedSpeech:
        """
        Complete pipeline: audio -> speech recognition -> translation -> synthesis
        
        Args:
            audio_file: Path to input audio file
            
        Returns:
            TranslatedSpeech object with original and translated audio
        """
        if not self.translator:
            raise RuntimeError("Translator not set. Call set_translator() first.")

        # Step 1: Recognize speech
        original_text, confidence = self.recognizer.recognize_from_audio_file(audio_file)
        
        if not original_text:
            raise RuntimeError("Could not recognize speech from audio")

        # Step 2: Translate text
        translated_text = self.translator(original_text)

        # Step 3: Synthesize translated text
        translated_audio = self.tts.synthesize_to_bytes(translated_text)

        # Read original audio
        with open(audio_file, 'rb') as f:
            original_audio = f.read()

        return TranslatedSpeech(
            original_text=original_text,
            original_language=self.source_language,
            translated_text=translated_text,
            target_language=self.target_language,
            original_audio=original_audio,
            translated_audio=translated_audio,
            confidence=confidence
        )

    def translate_from_microphone(self, timeout: int = 10) -> TranslatedSpeech:
        """
        Real-time speech translation from microphone
        
        Args:
            timeout: Listening timeout in seconds
            
        Returns:
            TranslatedSpeech object
        """
        if not self.translator:
            raise RuntimeError("Translator not set. Call set_translator() first.")

        # Step 1: Recognize speech from microphone
        original_text, confidence = self.recognizer.recognize_from_microphone(timeout)
        
        if not original_text:
            raise RuntimeError("Could not recognize speech from microphone")

        # Step 2: Translate text
        translated_text = self.translator(original_text)

        # Step 3: Synthesize translated text
        translated_audio = self.tts.synthesize_to_bytes(translated_text)

        return TranslatedSpeech(
            original_text=original_text,
            original_language=self.source_language,
            translated_text=translated_text,
            target_language=self.target_language,
            original_audio=b"",  # No original audio from microphone
            translated_audio=translated_audio,
            confidence=confidence
        )

    def batch_translate_directory(self, directory: str, output_dir: str) -> List[TranslatedSpeech]:
        """
        Translate all audio files in a directory
        
        Args:
            directory: Directory containing audio files
            output_dir: Directory to save translated audio
            
        Returns:
            List of TranslatedSpeech results
        """
        results = []
        audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
        
        os.makedirs(output_dir, exist_ok=True)
        
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)
            
            if os.path.isfile(file_path) and Path(file_path).suffix.lower() in audio_extensions:
                try:
                    result = self.translate_audio_file(file_path)
                    
                    # Save translated audio
                    base_name = Path(file_path).stem
                    output_path = os.path.join(output_dir, f"{base_name}_translated.wav")
                    
                    with open(output_path, 'wb') as f:
                        f.write(result.translated_audio)
                    
                    results.append(result)
                    print(f"✓ Translated: {file_name}")
                    
                except Exception as e:
                    print(f"✗ Error processing {file_name}: {e}")
        
        return results

    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages for translation"""
        # This would typically come from your translation engine
        return {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'ta': 'Tamil',
        }


if __name__ == "__main__":
    # Example usage
    print("Speech Translation Module loaded successfully")
    
    # Example: Initialize pipeline
    # pipeline = SpeechTranslationPipeline(
    #     source_language="en-US",
    #     target_language="es"
    # )
    # 
    # # Translate from file
    # result = pipeline.translate_audio_file("input_audio.wav")
    # print(f"Original: {result.original_text}")
    # print(f"Translated: {result.translated_text}")
