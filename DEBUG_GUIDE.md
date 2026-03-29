# DeepTranslate - JSON Parsing Error Fix Guide

## Problem Summary

**Error**: "Failed to execute 'json' on 'Response': Unexpected end of JSON input"

This occurred because:
1. **Frontend** was calling `response.json()` twice without proper error handling
2. **Backend** had multiple code paths that could return incomplete or missing responses
3. **No logging** made it impossible to debug what was actually being sent/received
4. **Vite proxy** didn't handle backend connection failures gracefully

---

## Changes Made

### 1. Frontend (React/App.jsx)

**Problem**: 
```javascript
// ❌ OLD CODE - Unsafe
if (!response.ok) {
  const errData = await response.json();  // May fail if response is empty
  throw new Error(errData.detail || 'Translation failed');
}
const data = await response.json();  // Parsing same response twice
```

**Solution**:
- Added `parseJSON()` helper function that:
  - Checks Content-Type header before parsing
  - Reads response body ONCE and validates it
  - Handles empty responses (204 status)
  - Provides detailed error messages with response preview
  - Logs all network details for debugging

- Enhanced error logging:
  - Logs request body sent to backend
  - Logs HTTP status codes
  - Shows raw response preview (first 200 chars)
  - Includes recovery suggestions

**Key Code**:
```javascript
const parseJSON = async (response) => {
  const contentType = response.headers.get('content-type');
  const statusText = `${response.status} ${response.statusText}`;
  
  // Handle empty responses (204, etc.)
  if (response.status === 204) {
    throw new Error('Server returned empty response (204 No Content)');
  }

  if (!contentType || !contentType.includes('application/json')) {
    const text = await response.text();
    console.error(`[DEBUG] Non-JSON Content-Type: ${contentType || 'none'}`);
    console.error(`[DEBUG] Raw response body (${text.length} chars):`, text.slice(0, 500));
    throw new Error(`Server returned ${contentType || 'non-JSON'} (${statusText})`);
  }

  const text = await response.text();
  if (!text || text.trim() === '') {
    console.error(`[DEBUG] Empty JSON body with status ${statusText}`);
    throw new Error(`Unexpected empty response (${statusText})`);
  }

  try {
    return JSON.parse(text);
  } catch (parseError) {
    console.error(`[DEBUG] JSON parse failed on: ${text.slice(0, 200)}`);
    throw new Error(`Invalid JSON from server (${statusText}): ${parseError.message}`);
  }
};
```

### 2. Backend (FastAPI/enhanced_api.py)

**Problem**:
```python
# ❌ OLD CODE - Multiple return paths, no logging
@app.post("/api/v2/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    try:
        # ... Many different code paths ...
        return TranslateResponse(...)  # Might not execute if exception occurs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Solution**:
- Added request ID tracking for distributed logging
- Added try/catch blocks with specific error types
- Ensures ALL code paths return valid `TranslateResponse` object
- Logs success/failure with provider info and quality scores
- Validates response object before returning

**Key Code**:
```python
@app.post("/api/v2/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    log_request_id = id(request)
    logger.info(f"[{log_request_id}] POST /api/v2/translate - Starting translation request")
    
    try:
        # ... translation logic ...
        
        response = TranslateResponse(
            original_text=text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=target_language,
            confidence=confidence,
            quality_score=quality_score,
            # ... all required fields ...
        )
        
        logger.info(f"[{log_request_id}] ✓ Translation successful (provider={provider}, confidence={confidence:.2f})")
        return response

    except ValueError as ve:
        logger.error(f"[{log_request_id}] Input validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[{log_request_id}] ✗ Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Vite Proxy (vite.config.js)

**Problem**:
```javascript
// ❌ OLD CODE - No error handling
proxy: {
  '/api': {
    target: 'http://127.0.0.1:6000',
    changeOrigin: true,
  }
}
```

**Solution**:
- Added proxy error event handler
- Returns JSON error response instead of HTML
- Logs proxy errors to console
- Detects backend connection failures early

**Key Code**:
```javascript
proxy: {
  '/api': {
    target: 'http://127.0.0.1:6000',
    configure: (proxy, options) => {
      proxy.on('error', (err, req, res) => {
        console.error('[PROXY ERROR]', err.message);
        res.writeHead(503, {
          'Content-Type': 'application/json',
        });
        res.end(JSON.stringify({
          detail: `Backend connection failed: ${err.message}`,
        }));
      });
    },
  }
}
```

### 4. Backend Diagnostics

- **Added Logging Middleware**: Logs every request with HTTP status and response time
- **Enhanced Health Check**: Shows:
  - Python version
  - Available translation providers
  - Supported language pairs
  - Debug flags

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api_url": "http://127.0.0.1:6000",
        "providers": {
            "google": GoogleTranslator is not None,
            "cloud_llm": cloud_llm_translator.is_configured(),
            "ollama": ollama_translator.is_available(),
        },
    }
```

---

## How to Debug Issues Now

### 1. Check Backend Health
```bash
curl http://127.0.0.1:6000/health | jq .
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "api_url": "http://127.0.0.1:6000",
  "providers": {
    "google": true,
    "cloud_llm": false,
    "ollama": false
  }
}
```

### 2. Monitor Backend Logs
All translation requests are now logged with:
- Request ID (for tracking)
- HTTP status code
- Provider used (google, ollama, cloud_llm)
- Confidence/quality scores
- Processing time

Example log output:
```
[123456789] POST /api/v2/translate - Starting translation request
[123456789] ✓ Translation successful (provider=google, confidence=0.98, quality=0.95)
```

### 3. Check Browser Console
Look for `[DEBUG]` prefixed logs:
```
[DEBUG] POST /api/v2/translate {text: "வணக்கம்", ...}
[DEBUG] Response status: 200 OK
[DEBUG] Translation successful: {provider: "google", confidence: 0.98, ...}
```

### 4. Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| "Backend connection failed" | Backend not running | `python run_api.py` or `python -m src.enhanced_api` |
| "Non-JSON Content-Type" | Proxy returned HTML error | Check backend logs, verify port 6000 is correct |
| "Empty JSON body" | Backend crashed silently | Check server_log.txt for exceptions |
| "Invalid JSON" | Malformed response | Add logging to backend translate() function |

### 5. Testing the API Directly
```bash
# Test with curl
curl -X POST http://127.0.0.1:6000/api/v2/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "வணக்கம்", "target_language": "en"}' \
  | jq .

# Expected response structure:
{
  "original_text": "வணக்கம்",
  "translated_text": "Hello",
  "source_language": "ta",
  "target_language": "en",
  "confidence": 0.99,
  "quality_score": 0.99,
  "provider": "dictionary",
  "cached": false,
  "translated_text": "Hello",
  ...
}
```

---

## Files Modified

1. **frontend/src/App.jsx**
   - Added `parseJSON()` helper for safe JSON parsing
   - Enhanced logging with `[DEBUG]` tags
   - Better error handling and user feedback

2. **src/enhanced_api.py**
   - Added request ID tracking in translate endpoint
   - Added logging middleware for all HTTP requests
   - Enhanced health check endpoint
   - Better error handling with specific exception types
   - Validates response object before returning

3. **frontend/vite.config.js**
   - Added proxy error handler
   - Returns JSON errors instead of HTML
   - Better debugging feedback

4. **NEW: DEBUG_GUIDE.md** (this file)
   - Comprehensive debugging reference

---

## Testing the Fixes

### Restart Services
```bash
# Terminal 1: Backend
python -m src.enhanced_api

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Try a Translation
1. Open http://localhost:5173
2. Enter Tamil text: "வணக்கம்"
3. Check browser console for `[DEBUG]` logs
4. Check backend logs for request tracking

### Test Error Handling
1. Stop backend: `Ctrl+C` on backend terminal
2. Try translation in frontend
3. Should see: "Backend connection failed"
4. Restart backend
5. Try again - should work

---

## Key Improvements

✅ **Safe JSON Parsing**: Never crashes on invalid/empty responses  
✅ **Detailed Logging**: Every request tracked with status codes  
✅ **Error Messages**: Clear explanations of what went wrong  
✅ **Backend Stability**: All code paths return valid JSON  
✅ **Debugging Tools**: Health check endpoint and detailed logs  
✅ **Proxy Resilience**: Handles connection failures gracefully  

---

## Quick Reference

| Endpoint | Purpose | Debug Command |
|----------|---------|---------------|
| `/health` | Server status | `curl http://127.0.0.1:6000/health` |
| `/api/v2/translate` | Translate text | See curl example above |
| Browser DevTools | Frontend logs | Press F12, check Console |
| `server_log.txt` | Backend logs | `tail -f server_log.txt` |

