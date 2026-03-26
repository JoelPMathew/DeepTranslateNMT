# 🚀 Quick Start Guide - DeepTranslate Pro 2.0

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend
python -m src.enhanced_api

# 3. Start frontend (in another terminal)
cd frontend && npm install && npm run dev

# Done! Visit http://localhost:5173
```

---

## ✨ 5 Key Features to Try

### 1️⃣ Auto-Detect Language
Just paste text in any language - it auto-detects!
```bash
curl -X POST http://localhost:8000/api/v2/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "నమస్కారం"}'
# Automatically detects Telugu!
```

### 2️⃣ Translate Documents
Upload PDF, DOCX, or TXT files:
```bash
curl -X POST http://localhost:8000/api/v2/translate/document \
  -F "file=@my_document.pdf" \
  -F "source_language=ta" \
  -F "target_language=en"
# Get translated document back!
```

### 3️⃣ Real-Time Collaboration
Start a session and invite team members:
```
1. Go to "Collaborate" tab
2. Click "Create Session"  
3. Share session ID with team
4. Join with your name
5. Translate together in real-time!
```

### 4️⃣ Translation Memory
Automatic consistency across documents:
- First translation: Translated by AI
- Same text later: Pulled from memory instantly
- No more inconsistencies!

### 5️⃣ Multi-Language Support
**Supported languages:**
- 🇮🇳 Tamil (தமிழ்)
- 🇮🇳 Telugu (తెలుగు)
- 🇮🇳 Kannada (ಕನ್ನಡ)
- 🇮🇳 Malayalam (മലയാളം)
- 🇮🇳 Hindi (हिन्दी)
- 🇬🇧 English

---

## 🎯 Common Tasks

### Translate Tamil Text
```python
from src.enhanced_api import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.post("/api/v2/translate", json={
    "text": "வணக்கம்",
    "source_language": "ta",
    "target_language": "en"
})
print(response.json())
```

### Get Language Statistics
```bash
# Check which languages are supported
curl http://localhost:8000/api/v2/languages

# Check available language pairs
curl http://localhost:8000/api/v2/language-pairs
```

### Join Collaboration Session
```bash
# Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/v2/collaboration/session/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Team Meeting"}' | jq -r '.session_id')

# Get session details
curl http://localhost:8000/api/v2/collaboration/session/$SESSION_ID
```

---

## 🗂️ Project Structure

**New Files Added:**
```
✅ src/language_detector.py          - Auto language detection
✅ src/multi_language_loader.py      - Model management for 6 languages
✅ src/document_translator.py        - PDF/DOCX/JSON translation
✅ src/collaboration_server.py       - Real-time multi-user sessions
✅ src/enhanced_api.py              - Enhanced FastAPI server
✅ config/language_registry.json    - Language configurations
✅ frontend/src/App.jsx             - React UI with 3 tabs
✅ frontend/src/App.css             - Modern styling
✅ FEATURE_GUIDE_2.0.md             - Complete documentation
```

---

## 📊 API Endpoints Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/translate` | Translate text |
| POST | `/api/v2/translate/document` | Translate files |
| GET | `/api/v2/languages` | List languages |
| GET | `/api/v2/language-pairs` | List language pairs |
| POST | `/api/v2/collaboration/session/create` | Create collab session |
| GET | `/api/v2/collaboration/sessions` | List all sessions |
| WS | `/ws/collaboration/{id}/{username}` | Join session (WebSocket) |

---

## 🎨 UI Features

**3 Main Tabs:**

1. **📝 Translate** - Text translation with auto-detection
2. **📄 Documents** - Upload files, get translated output
3. **👥 Collaborate** - Create sessions, translate with team

---

## ⚡ Performance Tips

✅ **First run** - Models download automatically (2-3 min)  
✅ **Subsequent runs** - Models cached in memory (instant)  
✅ **Batch documents** - Parallel processing improves speed  
✅ **Translation memory** - Identical text requests return instantly  

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -i :8000` then `kill -9 <PID>` |
| No models downloading | Check internet connection, try `pip install emoji` |
| Frontend won't load | Check `npm run dev` output, ensure port 5173 free |
| WebSocket errors | Ensure backend is running on port 8000 |
| Out of memory | Use CPU: `export CUDA_VISIBLE_DEVICES=""` |

---

## 🎓 Learning Path

1. ✅ Start the app (5 minutes)
2. ✅ Try text translation (2 minutes)
3. ✅ Upload a document (3 minutes)
4. ✅ Create collaboration session (2 minutes)
5. ✅ Read FEATURE_GUIDE_2.0.md (15 minutes)
6. ✅ Explore code (30 minutes)

---

## 💡 Next Steps

**To impress your teacher:**
- ✅ Show multi-language support (6 languages!)
- ✅ Demonstrate document translation (layout preserved!)
- ✅ Share real-time collaboration (live updates!)
- ✅ Show translation memory consistency
- ✅ Display model caching optimization

**Code to highlight:**
- Language detection algorithm (Unicode script analysis)
- Model cache management (efficient memory usage)
- WebSocket real-time sync patterns
- Document format support (PDF/DOCX/JSON)
- Translation memory fuzzy matching

---

**Ready? Start with:** `python -m src.enhanced_api` 🎉

