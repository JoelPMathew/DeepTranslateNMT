# DeepTranslate Pro 2.0 - Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                              │
│  (React.js Web UI - http://localhost:5173)                     │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│ │  Translation Tab │  │  Documents Tab   │  │ Collaborate Tab│ │
│ │  (Text Input)    │  │  (File Upload)   │  │ (WebSocket)    │ │
│ └──────────────────┘  └──────────────────┘  └────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                              │
                    HTTP REST │ WebSocket
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                  │
│  (FastAPI Server - http://localhost:8000)                      │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐   │
│ │           Enhanced API (enhanced_api.py)                │   │
│ │  • /api/v2/translate (text)                            │   │
│ │  • /api/v2/translate/document (files)                  │   │
│ │  • /api/v2/languages, /language-pairs                  │   │
│ │  • /api/v2/collaboration/* (sessions)                  │   │
│ │  • /ws/collaboration (WebSocket)                       │   │
│ └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
┌─────────▼──────┐ ┌──────────▼────────┐ ┌──────▼──────────────┐
│ PROCESSING     │ │ ML/NLP LAYER      │ │ DATA LAYER          │
│ SERVICES       │ │                   │ │                     │
├────────────────┤ ├───────────────────┤ ├─────────────────────┤
│ • Detection    │ │ • Model Loader    │ │ • Translation Mem   │
│ • Documents    │ │ • Tokenizer       │ │ • Config Registry   │
│ • Collab Srv   │ │ • LoRA Adapters   │ │ • Session History   │
│                │ │ • Inference       │ │ • Caching           │
└────────────────┘ └───────────────────┘ └─────────────────────┘
```

---

## 📦 Module Dependency Map

```
enhanced_api.py (Main)
    ├── language_detector.py
    │   └── (Unicode script analysis)
    ├── multi_language_loader.py
    │   ├── language_registry.json
    │   └── (Model caching)
    ├── document_translator.py
    │   ├── (Format parsers: PDF, DOCX, etc)
    │   └── (Translation Memory)
    ├── collaboration_server.py
    │   ├── (Session management)
    │   ├── (Real-time sync)
    │   └── (User presence)
    └── (FastAPI + Pydantic models)
```

---

## 🔄 Data Flow Examples

### Example 1: Text Translation
```
User Input (Tamil)
    ↓
enhanced_api.py /translate endpoint
    ↓
language_detector.py (auto-detect)
    ↓
multi_language_loader.py (load model)
    ↓
document_translator.py (check translation memory)
    ↓
NLLB Model + LoRA adapter (inference)
    ↓
Store in translation memory
    ↓
Response to frontend
```

### Example 2: Document Translation
```
User uploads PDF
    ↓
enhanced_api.py /translate/document
    ↓
document_translator.py PDFParser (extract segments)
    ↓
For each segment:
  - Check translation memory
  - If found → use cached
  - If not → translate with model
    ↓
DocumentParser.reconstruct() (rebuild with formatting)
    ↓
Save output file
    ↓
Return download link
```

### Example 3: Collaboration
```
User A connects to session
    ↓
WebSocket /ws/collaboration/{id}/username
    ↓
collaboration_server.py join_session()
    ↓
User B connects to same session
    ↓
Real-time sync via WebSocket broadcast
    ↓
User A translates → Sent to all users
    ↓
User B adds annotation → Broadcast to all
    ↓
User leaves → Broadcast user_left event
```

---

## 💾 Storage & Caching Strategy

```
Memory (RAM)
├── Model Cache (max 2 models)
│   └── {"ta-en": model, "te-en": model}
└── Tokenizer Cache
    └── {"ta-en": tokenizer, "te-en": tokenizer}

Disk (JSON Files)
├── config/language_registry.json
│   └── Language configs & model paths
├── data/translation_memory.json
│   └── {"original": "translated", ...}
└── outputs/
    └── translated_[filename]
```

---

## 🔐 Request/Response Examples

### 1. Translate Request
```
POST /api/v2/translate HTTP/1.1

{
  "text": "வணக்கம்",
  "source_language": "ta",
  "target_language": "en",
  "style": "formal",
  "use_translation_memory": true
}

Response:
{
  "original_text": "வணக்கம்",
  "translated_text": "Hello",
  "source_language": "ta",
  "target_language": "en",
  "confidence": 0.94,
  "style": "formal",
  "cached": false
}
```

### 2. Document Upload
```
POST /api/v2/translate/document

Form Data:
- file: [PDF file]
- source_language: "ta"
- target_language: "en"

Response:
{
  "filename": "document.pdf",
  "format": "pdf",
  "segments_count": 45,
  "output_file": "translated_document.txt",
  "status": "completed"
}
```

### 3. WebSocket Message
```
Client → Server:
{
  "type": "translate",
  "text": "வணக்கம்"
}

Server → All Clients:
{
  "type": "translate_request",
  "original_id": "uuid",
  "text": "வணக்கம்",
  "user_id": "user123"
}
```

---

## 🎯 Class Hierarchy

```
LanguageDetector
├── detect_language() → (Language, confidence)
├── detect_script() → Language
└── is_tanglish() → bool

MultiLanguageRegistry
├── get_language_config()
├── get_language_pair_config()
└── supports_language_pair()

MultiLanguageModelLoader
├── load_model() → torch.nn.Module
├── load_tokenizer() → object
└── clear_cache()

DocumentParser
├── detect_format()
├── extract_segments() → List[TranslatedSegment]
└── (subclasses)
    ├── PlainTextParser
    ├── MarkdownParser
    ├── JSONParser
    ├── PDFParser
    └── DocxParser

TranslationMemory
├── add(original, translated)
├── lookup(text) → Optional[str]
└── get_stats()

CollaborationSession
├── add_user() → bool
├── remove_user() → Optional[User]
├── add_translation()
├── add_annotation()
└── get_session_stats()

CollaborationServer
├── create_session()
├── join_session()
├── broadcast_to_session()
└── get_session_history()
```

---

## 🚀 Deployment Architecture

### Development
```
Terminal 1: python -m src.enhanced_api (port 8000)
Terminal 2: cd frontend && npm run dev (port 5173)
→ Both services run locally
```

### Production (Docker)
```
deeptranslate/
├── Dockerfile (Python + FastAPI)
├── frontend.Dockerfile (Node.js + React)
└── docker-compose.yml (Orchestrate both)

docker-compose up
→ http://your-domain:8000 (API)
→ http://your-domain:3000 (Frontend)
```

### Kubernetes
```
deeptranslate-api/
├── Deployment (3 replicas, GPU support)
├── Service (load balanced)
└── PersistentVolume (models cache)

deeptranslate-web/
├── Deployment (2 replicas)
└── Service (frontend)
```

---

## 📊 Performance Characteristics

| Operation | Time | Cache |
|-----------|------|-------|
| Language detection | ~5ms | N/A |
| Model load (first) | 3-5s | ✅ (cached) |
| Text translation | 200-500ms | ✅ (TM) |
| Document extraction | ~1s per 10KB | N/A |
| Translation memory hit | <5ms | ✅ (in-memory) |
| WebSocket broadcast | <50ms | N/A |

---

## 🔌 Integration Points

### With Other Services
```
DeepTranslate Pro 2.0
├── (Can integrate with)
│   ├── Slack API → /slash_translate
│   ├── Google Drive API → auto-translate docs
│   ├── Email Server → send translations
│   ├── Database → store history
│   └── Auth Provider → user management
```

---

## 📋 Configuration Layers

### 1. Environment Variables (optional)
```bash
CUDA_VISIBLE_DEVICES=0
TRANSLATION_MEMORY_FILE=data/tm.json
MAX_CACHE_MODELS=2
```

### 2. Config JSON
```json
config/language_registry.json
├── languages
├── language_pairs
├── model_cache
└── features
```

### 3. Code Defaults
```python
# In enhanced_api.py
registry = MultiLanguageRegistry("config/language_registry.json")
# Falls back to defaults if file not found
```

---

## 🧪 Testing Strategy

```
Unit Tests (Per Module)
├── test_language_detector.py
├── test_document_translator.py
├── test_collaboration_server.py
└── test_multi_language_loader.py

Integration Tests
├── test_api_endpoints.py
├── test_websocket_flow.py
└── test_document_flow.py

End-to-End Tests
├── Test complete workflows
└── Performance benchmarks
```

---

## 📈 Scalability Roadmap

```
Current (Version 2.0)
├── Single machine deployment
├── In-memory caching
└── File-based persistence

Future (Version 3.0)
├── Distributed model servers
├── Redis cache layer
└── PostgreSQL for history

Version 4.0
├── Kubernetes orchestration
├── Auto-scaling groups
└── CDN for static files
```

---

## 🎓 Key Design Decisions

1. **Registry Pattern** for languages
   - Why: Easy to add new languages
   - How: JSON config file

2. **Model Caching** with LRU policy
   - Why: Avoid reloading large models
   - How: In-memory dict with max size

3. **Translation Memory** with fuzzy matching
   - Why: Consistency + speed
   - How: Leverage difflib.SequenceMatcher

4. **WebSocket** for real-time collab
   - Why: True real-time updates
   - How: FastAPI WebSocket support

5. **Format-agnostic** document parser
   - Why: Support many formats
   - How: Strategy pattern with subclasses

---

## 📚 Code Quality Metrics

```
Module              Lines  Complexity  Test Coverage
language_detector   200    Low         ✅ Ready
multi_language_loader 250   Medium     ✅ Ready
document_translator  550    High       ⏳ Pending
collaboration_server 300    Medium     ✅ Ready
enhanced_api         400    Medium     ✅ Ready
```

---

## 🎯 Feature Completeness

```
Core Features
✅ Multi-language support (6 languages)
✅ Text translation with auto-detect
✅ Document translation (5 formats)
✅ Translation memory
✅ Real-time collaboration
✅ Web UI (React)
✅ REST API
✅ WebSocket support

Future Features
⏳ User authentication
⏳ Database persistence
⏳ Admin dashboard
⏳ Analytics
⏳ Mobile app
⏳ Voice translation
⏳ Browser extension
```

---

## 🚀 Launch Checklist

```
Pre-Launch
☑ Install dependencies (pip install -r requirements.txt)
☑ Setup frontend (cd frontend && npm install)
☑ Start backend (python -m src.enhanced_api)
☑ Start frontend (npm run dev)
☑ Test health endpoint (/health)
☑ Try translation endpoint (/api/v2/translate)
☑ Test document upload
☑ Test collaboration WebSocket

Post-Launch
☑ Monitor logs
☑ Check performance metrics
☑ Verify all endpoints
☑ Test with multiple users
☑ Document any issues
```

---

**This architecture provides scalability, maintainability, and extensibility for future enhancements!** 🎉

