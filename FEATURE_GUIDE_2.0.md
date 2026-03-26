# DeepTranslate Pro 2.0 - Complete Feature Guide

## 🎯 New Features Overview

DeepTranslate has been expanded from a Tamil-English translator to a **comprehensive multi-language translation platform** with real-time collaboration, document processing, and enterprise-grade features.

### Features Added

#### 1. **Multi-Language Support** ✨
- **Tamil (தமிழ்)** - Full support with cultural intelligence
- **Telugu (తెలుగు)** - Regional Indian language
- **Kannada (ಕನ್ನಡ)** - South Indian support
- **Malayalam (മലയാളം)** - Kerala language
- **Hindi (हिन्दी)** - Hindi to English
- **English** - Bidirectional with all languages

Automatic language detection using Unicode script analysis ensures seamless translation without manual language selection.

#### 2. **Document Translation** 📄
Translate entire documents while preserving formatting:
- **PDF**: Extract and translate text with layout preservation
- **DOCX**: Maintain styles, tables, and document structure
- **TXT**: Plain text with paragraph detection
- **Markdown**: Preserve formatting (headings, lists, blockquotes)
- **JSON**: Translate values while keeping structure

Features:
- Batch processing for multiple segments
- Translation memory for consistency
- Automatic format detection
- Layout-aware reconstruction

#### 3. **Real-Time Collaboration** 👥
Multi-user translation sessions with live synchronization:
- **Live Sessions**: Multiple users translate simultaneously
- **Shared History**: Access to all translations in session
- **Annotations**: Add comments and feedback to translations
- **User Presence**: See who's currently in the session
- **Cursor Tracking**: Real-time cursor position updates

#### 4. **Translation Memory** 💾
Intelligent caching system:
- Automatic consistency across documents
- Fuzzy matching for similar strings
- Session-based history
- Export/import capability
- Statistical tracking

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- CUDA 11+ (optional, for GPU acceleration)
- 8GB RAM minimum

### 1. Backend Setup

```bash
# Navigate to project directory
cd DeepTranslateNMT

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import torch; print(torch.__version__)"
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build frontend (optional for development)
npm run build
```

### 3. Configuration

Update `config/language_registry.json` with your model paths:

```json
{
  "language_pairs": {
    "ta-en": {
      "model": "facebook/nllb-200-distilled-600M",
      "adapter_path": "nllb_lora_refined/best_model",
      "supported": true
    }
  }
}
```

---

## 🔧 Running the Application

### Option 1: Development Mode (Recommended for Learning)

**Terminal 1 - Start Backend Server:**
```bash
python -m src.enhanced_api
# Server runs at http://localhost:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
# UI available at http://localhost:5173
```

**Terminal 3 (Optional) - Monitor Translation Memory:**
```python
from src.document_translator import TranslationMemory
tm = TranslationMemory()
print(tm.get_stats())
```

### Option 2: Production Mode

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Run with Gunicorn (production WSGI server)
gunicorn -w 4 -b 0.0.0.0:8000 src.enhanced_api:app
```

---

## 📌 API Documentation

### 1. Text Translation

**Endpoint:** `POST /api/v2/translate`

**Request:**
```json
{
  "text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
  "source_language": "ta",
  "target_language": "en",
  "style": "formal",
  "use_translation_memory": true
}
```

**Response:**
```json
{
  "original_text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
  "translated_text": "Hello, how are you?",
  "source_language": "ta",
  "target_language": "en",
  "confidence": 0.94,
  "style": "formal",
  "cached": false
}
```

**Auto-Detection Example:**
```bash
curl -X POST http://localhost:8000/api/v2/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "نمسكارام"}'
# Automatically detects Hindi!
```

### 2. Document Translation

**Endpoint:** `POST /api/v2/translate/document`

**Request (Form Data):**
- `file`: PDF/DOCX/TXT file
- `source_language`: "ta", "te", "kn", "ml", "hi", "en"
- `target_language`: Target language code
- `preserve_formatting`: true/false

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/v2/translate/document \
  -F "file=@document.pdf" \
  -F "source_language=ta" \
  -F "target_language=en"
```

**Response:**
```json
{
  "filename": "document.pdf",
  "format": "pdf",
  "segments_count": 45,
  "output_file": "translated_document.txt",
  "status": "completed"
}
```

### 3. Language Support

**Endpoint:** `GET /api/v2/languages`

**Response:**
```json
{
  "languages": {
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "hi": "Hindi",
    "en": "English"
  }
}
```

### 4. Collaboration Sessions

**Create Session:**
```bash
curl -X POST http://localhost:8000/api/v2/collaboration/session/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Project Alpha Translation"}'
```

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "name": "Project Alpha Translation",
  "status": "created"
}
```

**List Sessions:**
```bash
curl http://localhost:8000/api/v2/collaboration/sessions
```

### 5. WebSocket Connection (Real-Time)

**URL:** `ws://localhost:8000/ws/collaboration/{session_id}/{username}`

**Event: Translate Request**
```json
{
  "type": "translate",
  "text": "வணக்கம்",
  "original_id": "uuid"
}
```

**Event: Annotation**
```json
{
  "type": "annotation",
  "translation_id": "uuid",
  "text": "Great translation!"
}
```

**Event: User Feedback**
```json
{
  "type": "feedback",
  "feedback": {
    "rating": 5,
    "comments": "Perfect!"
  }
}
```

---

## 💻 Frontend Usage Guide

### Translation Tab
1. Select source and target languages (auto-detects if not selected)
2. Type or paste text
3. Click "Translate"
4. View confidence score
5. Copy translated text

### Documents Tab
1. Click "Choose File"
2. Select PDF, DOCX, TXT, Markdown, or JSON
3. Choose language pair
4. Click "Translate Document"
5. Download translated file

### Collaboration Tab
1. Click "Create Collaboration Session"
2. Get session ID
3. Share with team members
4. Click "Join" and enter username
5. Real-time translation with annotations

---

## 🔌 Integration Examples

### Python Usage

```python
from src.language_detector import LanguageDetector
from src.multi_language_loader import MultiLanguageRegistry, MultiLanguageModelLoader

# Initialize
detector = LanguageDetector()
registry = MultiLanguageRegistry()
loader = MultiLanguageModelLoader(registry)

# Detect language
text = "నమస్కారం"
lang, conf = detector.detect_language(text)
print(f"Detected: {lang.name} ({conf:.2%})")

# Load model
model = loader.load_model("te", "en")
tokenizer = loader.load_tokenizer("te", "en")

# Translate
inputs = tokenizer(text, return_tensors="pt")
outputs = model.generate(**inputs)
translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### JavaScript/Node.js Usage

```javascript
// Connect to collaboration session
const ws = new WebSocket('ws://localhost:8000/ws/collaboration/abc123/Alice');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Send translation request
ws.send(JSON.stringify({
  type: 'translate',
  text: 'வணக்கம்'
}));
```

### REST API with Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v2'
});

// Translate text
async function translate(text, srcLang, tgtLang) {
  const response = await api.post('/translate', {
    text,
    source_language: srcLang,
    target_language: tgtLang
  });
  return response.data;
}

// Translate document
async function translateDoc(file, srcLang, tgtLang) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_language', srcLang);
  formData.append('target_language', tgtLang);
  
  const response = await api.post('/translate/document', formData);
  return response.data;
}
```

---

## 📊 Performance Optimization

### Model Caching
Models are cached in memory to avoid reloading:
```python
# Check cached models
from src.enhanced_api import model_loader
print(model_loader.list_cached_models())
# Output: ['ta-en', 'te-en']

# Clear cache if needed
model_loader.clear_cache()
```

### Batch Processing
For multiple documents:
```python
from src.document_translator import DocumentParser

files = ['doc1.pdf', 'doc2.docx', 'doc3.txt']
for file in files:
    segments = DocumentParser.extract_segments(file)
    # Process in parallel for better performance
```

### Translation Memory Optimization
```python
from src.document_translator import TranslationMemory

tm = TranslationMemory()
stats = tm.get_stats()
print(f"Memory Size: {stats['total_entries']} entries")
```

---

## 🐛 Troubleshooting

### Issue: "Model not found"
**Solution:**
```bash
python -c "from transformers import AutoModel; AutoModel.from_pretrained('facebook/nllb-200-distilled-600M')"
# Downloads model automatically
```

### Issue: CUDA out of memory
**Solution:**
```bash
# Use CPU instead
export CUDA_VISIBLE_DEVICES=""
python -m src.enhanced_api
```

### Issue: WebSocket connection failing
**Solution:**
```bash
# Check if server is running
curl http://localhost:8000/health

# Check CORS settings in enhanced_api.py
```

---

## 📈 Scaling & Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "src.enhanced_api"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deeptranslate-pro
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: deeptranslate:2.0.0
        ports:
        - containerPort: 8000
        resources:
          limits:
            memory: "8Gi"
            nvidia.com/gpu: "1"
```

---

## 🎓 Learning Resources

### Key Modules to Study
1. **language_detector.py** - Unicode script analysis
2. **multi_language_loader.py** - Model caching strategy
3. **document_translator.py** - Format-specific parsing
4. **collaboration_server.py** - Real-time sync patterns

### Advanced Topics
- LoRA adapter architecture (low-rank adaptation)
- WebSocket connection pooling
- Translation memory fuzzy matching algorithms
- ONNX export for edge deployment

---

## 📝 Project Structure

```
DeepTranslateNMT/
├── config/
│   └── language_registry.json          # Language & model configurations
├── src/
│   ├── language_detector.py           # Auto-detection engine
│   ├── multi_language_loader.py       # Model management
│   ├── document_translator.py         # Format support
│   ├── collaboration_server.py        # Real-time sync
│   └── enhanced_api.py               # FastAPI server
├── frontend/
│   ├── src/
│   │   ├── App.jsx                   # Main React component
│   │   └── App.css                   # Styling
│   └── package.json
├── data/
│   └── translation_memory.json       # Cached translations
└── outputs/
    └── translated_[filename]         # Generated documents
```

---

## 🎉 What's New in 2.0

| Feature | 1.0 | 2.0 |
|---------|-----|-----|
| Languages | Tamil only | 6 languages |
| Document Support | ❌ | ✅ (PDF/DOCX/etc) |
| Real-Time Collab | ❌ | ✅ |
| Translation Memory | ❌ | ✅ |
| Web UI | Basic API | Full-featured React |
| Model Cache | ❌ | ✅ |
| Batch Processing | ❌ | ✅ |
| WebSocket Support | ❌ | ✅ |
| Language Detection | Manual | Automatic |

---

## 📞 Support & Contributing

For issues or feature requests:
1. Check troubleshooting section
2. Review API documentation
3. Check logs in terminal
4. Open GitHub issue with details

---

**Version**: 2.0.0 | **Last Updated**: March 2026 | **License**: MIT
