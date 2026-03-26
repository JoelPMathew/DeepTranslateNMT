# src/nllb_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .nllb_inference import NLLBTranslator
import uvicorn

app = FastAPI(title="NLLB-200 NMT API")
translator = None

class TranslationRequest(BaseModel):
    text: str
    src_lang: str = "tam_Taml"
    tgt_lang: str = "eng_Latn"
    style: str = "standard"
    use_enhanced: bool = False

class BatchTranslationRequest(BaseModel):
    texts: list[str]
    src_lang: str = "tam_Taml"
    tgt_lang: str = "eng_Latn"
    style: str = "formal"

@app.on_event("startup")
async def load_model():
    global translator
    # Check for refined adapter first
    adapter_path = "./nllb_lora_refined/best_model"
    if not os.path.exists(adapter_path):
        adapter_path = "./nllb_lora_results/best_model"
    
    # Load with adapter if it exists
    if os.path.exists(adapter_path):
        translator = NLLBTranslator(adapter_path=adapter_path)
    else:
        translator = NLLBTranslator()

@app.post("/translate")
async def translate(request: TranslationRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    translation = translator.translate(
        request.text, 
        src_lang=request.src_lang, 
        tgt_lang=request.tgt_lang, 
        style=request.style
    )
    
    # Analyze culture
    insights = translator.analyze_culture(request.text if request.src_lang == "tam_Taml" else translation)
    
    return {
        "translation": translation,
        "cultural_insights": insights
    }

@app.post("/translate_batch")
async def translate_batch(request: BatchTranslationRequest):
    return {"translations": translator.translate_batch(request.texts, src_lang=request.src_lang, tgt_lang=request.tgt_lang, style=request.style)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# --- Separator (I'll write files separately but grouping for speed) ---
