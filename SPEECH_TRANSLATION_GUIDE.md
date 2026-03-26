# Speech Translation Feature Guide

## Overview

The Speech Translation module adds real-time and batch speech-to-speech translation capabilities to DeepTranslate Pro. It combines:

- **Speech Recognition** — Convert audio to text using Google Speech Recognition
- **Translation** — Translate recognized text to target language
- **Text-to-Speech** — Synthesize translated text back to audio

## Installation

The required dependencies are included in `requirements.txt`:

```bash
pip install SpeechRecognition pyttsx3 pydub google-cloud-speech librosa
```

### Optional: For MP3 Support
```bash
pip install pydub
# Also requires ffmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)
```

## Architecture

### Core Components

#### 1. SpeechRecognizer
Handles speech-to-text conversion from audio files or microphone:

```python
from speech_translator import SpeechRecognizer

recognizer = SpeechRecognizer(language="en-US")

# From audio file
text, confidence = recognizer.recognize_from_audio_file("audio.wav")

# From microphone
text, confidence = recognizer.recognize_from_microphone(timeout=10)
```

#### 2. TextToSpeech
Converts text to speech output:

```python
from speech_translator import TextToSpeech

tts = TextToSpeech(language="es", voice="default")

# Save to file
tts.synthesize_to_file("Hola mundo", "output.wav")

# Get as bytes
audio_bytes = tts.synthesize_to_bytes("Hola mundo")
```

#### 3. SpeechTranslationPipeline
Complete end-to-end speech translation:

```python
from speech_translator import SpeechTranslationPipeline
from deep_translator import GoogleTranslator

pipeline = SpeechTranslationPipeline(
    source_language="en-US",
    target_language="es"
)

# Set translation function
def translate(text):
    translator = GoogleTranslator(source='auto', target='es')
    return translator.translate(text)

pipeline.set_translator(translate)

# Translate audio file
result = pipeline.translate_audio_file("input.wav")
print(result.original_text)      # "Hello world"
print(result.translated_text)    # "Hola mundo"
```

## API Endpoints

### 1. Speech Recognition
**POST** `/api/v2/speech/recognize`

Recognize speech from audio file.

```bash
curl -X POST http://localhost:6000/api/v2/speech/recognize \
  -F "file=@audio.wav" \
  -F "language=en-US"
```

Response:
```json
{
  "status": "success",
  "text": "Hello, how are you?",
  "confidence": 0.95,
  "language": "en-US"
}
```

### 2. Complete Speech Translation
**POST** `/api/v2/speech/translate`

Recognize → Translate → Synthesize all in one step.

```bash
curl -X POST http://localhost:6000/api/v2/speech/translate \
  -F "file=@english_audio.wav" \
  -F "source_language=en-US" \
  -F "target_language=es-ES"
```

Response:
```json
{
  "status": "success",
  "original_text": "Hello, how are you?",
  "original_language": "en-US",
  "translated_text": "Hola, ¿cómo estás?",
  "target_language": "es-ES",
  "confidence": 0.95,
  "audio_available": true
}
```

### 3. Text-to-Speech Synthesis
**POST** `/api/v2/speech/synthesize`

Convert text to speech audio.

```bash
curl -X POST "http://localhost:6000/api/v2/speech/synthesize?text=Hola%20mundo&language=es" \
  --output output.wav
```

### 4. List Available Voices
**GET** `/api/v2/speech/voices`

Get available TTS voices.

```bash
curl http://localhost:6000/api/v2/speech/voices
```

Response:
```json
{
  "status": "success",
  "voices": {
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0": {
      "name": "Microsoft David Desktop - English (United States)",
      "languages": ["en-US"],
      "gender": "male"
    }
  },
  "count": 1
}
```

### 5. Batch Speech Translation
**POST** `/api/v2/speech/batch-translate`

Translate multiple audio files in one request.

```bash
curl -X POST http://localhost:6000/api/v2/speech/batch-translate \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "source_language=en-US" \
  -F "target_language=es-ES"
```

### 6. Supported Languages
**GET** `/api/v2/speech/languages`

Get list of supported languages.

```bash
curl http://localhost:6000/api/v2/speech/languages
```

Response:
```json
{
  "status": "success",
  "languages": {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ta": "Tamil"
  },
  "count": 13
}
```

## Usage Examples

### Python Integration

```python
from speech_translator import SpeechTranslationPipeline
from deep_translator import GoogleTranslator

# Initialize pipeline
pipeline = SpeechTranslationPipeline(
    source_language="en-US",
    target_language="es-ES"
)

# Set translator
def translate(text):
    translator = GoogleTranslator(source='auto', target='es')
    return translator.translate(text)

pipeline.set_translator(translate)

# Translate from file
result = pipeline.translate_audio_file("meeting_recording.wav")

# Save translated audio
with open("translated_audio.wav", "wb") as f:
    f.write(result.translated_audio)

print(f"Original: {result.original_text}")
print(f"Translation: {result.translated_text}")
print(f"Confidence: {result.confidence}")
```

### Real-Time Translation

```python
# Translate from microphone
result = pipeline.translate_from_microphone(timeout=10)

# Play translated audio
import playsound
with open("temp.wav", "wb") as f:
    f.write(result.translated_audio)
playsound.playsound("temp.wav")
```

### Batch Processing

```python
# Translate all audio files in a directory
results = pipeline.batch_translate_directory(
    directory="./audio_files",
    output_dir="./translated_audio"
)

for result in results:
    print(f"✓ {result.original_text} → {result.translated_text}")
```

## Supported Audio Formats

- **WAV** — Recommended format
- **MP3** — Requires ffmpeg
- **FLAC** — Good compression
- **OGG** — Open format
- **M4A** — iTunes format

## Language Support

### Speech Recognition (via Google API)
Supports 125+ languages. Use language codes like:
- `en-US` — English (US)
- `es-ES` — Spanish (Spain)
- `fr-FR` — French (France)
- `de-DE` — German (Germany)
- `ta-IN` — Tamil (India)
- `hi-IN` — Hindi (India)
- `zh-CN` — Mandarin Chinese
- `ja-JP` — Japanese
- `ar-SA` — Arabic

### Text-to-Speech (via pyttsx3)
Supported by system voices (typically 5-10 voices per OS).

### Translation (via GoogleTranslator)
Supports 100+ languages.

## Performance Considerations

### Optimization Tips

1. **Use appropriate audio quality**
   - 16-bit, 16kHz for optimal recognition
   - Higher bitrate = better quality but larger file size

2. **Language specification**
   - Specify language code for faster recognition
   - Auto-detection is slower

3. **Caching**
   - Reuse pipelines for same language pairs
   - Connection pooling for API calls

4. **Batch processing**
   - Use batch endpoint for multiple files
   - Parallel processing with threading

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Could not recognize speech" | Check audio quality, use clearer speech, specify language |
| "Service error" | Check internet connection, Google API quotas |
| "FFmpeg not found" | Install ffmpeg: `brew install ffmpeg` (macOS) |
| "No microphone detected" | Check system audio settings, use file input instead |

## Error Handling

```python
from speech_translator import SpeechTranslationPipeline

try:
    pipeline = SpeechTranslationPipeline()
    result = pipeline.translate_audio_file("audio.wav")
except FileNotFoundError:
    print("Audio file not found")
except RuntimeError as e:
    print(f"Translation error: {e}")
except ImportError:
    print("Required libraries not installed")
```

## Advanced Configuration

### Custom TTS Voice

```python
from speech_translator import TextToSpeech

tts = TextToSpeech(language="es", voice="custom_voice_id")

# Set speech rate
tts.engine.setProperty('rate', 200)  # 200 words per minute

# Set volume
tts.engine.setProperty('volume', 0.8)  # 0-1.0
```

### Custom Translator Function

```python
from speech_translator import SpeechTranslationPipeline
from transformers import pipeline as hf_pipeline

# Use local NMT model
nmt_pipeline = hf_pipeline(
    "translation_en_to_es",
    model="Helsinki-NLP/opus-mt-en-es"
)

pipeline = SpeechTranslationPipeline()

def custom_translate(text):
    result = nmt_pipeline(text)
    return result[0]['translation_text']

pipeline.set_translator(custom_translate)
```

## License & Attribution

- Speech Recognition: Google Speech API (requires internet)
- Text-to-Speech: pyttsx3 (offline, uses system voices)
- Translation: Multiple backends supported

## Future Enhancements

- [ ] Offline speech recognition
- [ ] Real-time streaming translation
- [ ] Speaker diarization
- [ ] Speech emotion detection
- [ ] Custom neural voice synthesis
- [ ] Multiple speaker support
