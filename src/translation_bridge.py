"""
Translation Bridge - Provides working translations for the API
Uses existing models or dictionary fallback for common phrases
"""
import os
import torch
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Translation dictionary for common phrases
TRANSLATION_DICTIONARY = {
    "how are you": {
        "ta": "நீ எப்படி இருக்கிறாய்",
        "te": "నీవు ఎలా ఉన్నావు",
        "kn": "ನೀವು ಹೇಗಿದ್ದೀರಿ",
        "ml": "നിങ്ങൾ എപ്പോൾ ഉണ്ടായിരുന്നു",
        "hi": "आप कैसे हो"
    },
    "hello": {
        "ta": "வணக்கம்",
        "te": "హలో",
        "kn": "ನಮಸ್ಕಾರ",
        "ml": "ഹലോ",
        "hi": "नमस्ते"
    },
    "good morning": {
        "ta": "நல்லை காலை",
        "te": "శుభోదయం",
        "kn": "ಶುಭೋದಯೋ",
        "ml": "സുപ്രഭാതം",
        "hi": "शुभ प्रभात"
    },
    "thank you": {
        "ta": "நன்றி",
        "te": "ధన్యవాదాలు",
        "kn": "ಧನ್ಯವಾದ",
        "ml": "നന്ദി",
        "hi": "धन्यवाद"
    },
    "welcome": {
        "ta": "வரவேற்க",
        "te": "స్వాగతం",
        "kn": "ಸ್ವಾಗತ",
        "ml": "സ്വാഗതം",
        "hi": "स्वागत है"
    },
    "yes": {
        "ta": "ஆம்",
        "te": "అవును",
        "kn": "ಹೌದು",
        "ml": "അതെ",
        "hi": "हाँ"
    },
    "no": {
        "ta": "இல்லை",
        "te": "లేదు",
        "kn": "ಇಲ್ಲ",
        "ml": "ഇല്ല",
        "hi": "नहीं"
    },
}

class TranslationBridge:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.src_tokenizer = None
        self.tgt_tokenizer = None
        self.model_loaded = False
        # Don't load model during init - do it lazily on first translation
        logger.info("TranslationBridge initialized (model will be loaded on first use)")
    
    def _load_model_lazy(self):
        """Load the trained transformer model if available (lazy loading)"""
        if self.model_loaded:
            return
        
        try:
            base_path = os.path.dirname(__file__)
            model_path = os.path.join(base_path, "..", "models", "best_model.pt")
            src_spm = os.path.join(base_path, "..", "models", "src_spm")
            tgt_spm = os.path.join(base_path, "..", "models", "tgt_spm")
            
            if os.path.exists(model_path):
                try:
                    from .tokenizer import NMTTokenizer
                    from .model import TransformerModel
                except ImportError:
                    from tokenizer import NMTTokenizer
                    from model import TransformerModel
                
                self.src_tokenizer = NMTTokenizer(src_spm)
                self.tgt_tokenizer = NMTTokenizer(tgt_spm)
                
                self.model = TransformerModel(
                    src_vocab_size=self.src_tokenizer.get_vocab_size(),
                    tgt_vocab_size=self.tgt_tokenizer.get_vocab_size(),
                    d_model=512,
                    nhead=8,
                    num_encoder_layers=6,
                    num_decoder_layers=6
                ).to(self.device)
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                logger.info("Loaded transformer model successfully")
            else:
                logger.warning(f"Model not found at {model_path}, will use dictionary translations only")
                self.model = None
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}, will use dictionary translations only")
            self.model = None
        finally:
            self.model_loaded = True
    
    def translate(self, text: str, source_lang: str = "en", target_lang: str = "ta", style: str = "formal") -> str:
        """
        Translate text from source to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (en, ta, te, kn, ml, hi)
            target_lang: Target language code
            style: Translation style (formal, casual, etc.)
        
        Returns:
            Translated text or best attempt
        """
        text = text.strip()
        if not text:
            return ""
        
        # Try dictionary first
        lower_text = text.lower()
        if lower_text in TRANSLATION_DICTIONARY:
            if target_lang in TRANSLATION_DICTIONARY[lower_text]:
                translated = TRANSLATION_DICTIONARY[lower_text][target_lang]
                logger.info(f"Dictionary match: {text} -> {translated}")
                return translated
        
        # Try transformer model (lazy load on first use)
        if not self.model_loaded:
            self._load_model_lazy()
        
        if self.model and source_lang == "en" and target_lang in ["ta", "te", "kn", "ml", "hi"]:
            try:
                try:
                    from .translate import translate_sentence
                except ImportError:
                    from translate import translate_sentence
                
                result = translate_sentence(
                    self.model, 
                    text, 
                    self.src_tokenizer, 
                    self.tgt_tokenizer, 
                    self.device
                )
                logger.info(f"Model translation: {text} -> {result}")
                return result
            except Exception as e:
                logger.warning(f"Model translation failed: {e}")
        
        # Fallback: Generate response with confidence note
        logger.info(f"Using fallback translation for: {text}")
        return f"[Translation of '{text}' not available - confidence: low]"

# Initialize global translation bridge
_translation_bridge = None

def get_translation_bridge() -> TranslationBridge:
    global _translation_bridge
    if _translation_bridge is None:
        _translation_bridge = TranslationBridge()
    return _translation_bridge
