import torch
from .tokenizer import NMTTokenizer
from .model import TransformerModel
from .translate import translate_sentence
import os

class EnTaTranslator:
    def __init__(self, model_path, src_spm, tgt_spm, device=None):
        self.device = device if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.src_tokenizer = NMTTokenizer(src_spm)
        self.tgt_tokenizer = NMTTokenizer(tgt_spm)
        
        self.model = TransformerModel(
            src_vocab_size=self.src_tokenizer.get_vocab_size(),
            tgt_vocab_size=self.tgt_tokenizer.get_vocab_size()
        ).to(self.device)
        
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def translate(self, text, src='en', tgt='ta'):
        """
        Translates text between English and Tamil.
        Note: The current model is trained for a specific direction (e.g., en -> ta).
        In a production system, this would handle routing or use a multilingual model.
        """
        # For this implementation, we assume the model is en -> ta
        return translate_sentence(self.model, text, self.src_tokenizer, self.tgt_tokenizer, self.device)

def translate(text: str, src: str, tgt: str, model_path: str, src_spm: str, tgt_spm: str) -> str:
    translator = EnTaTranslator(model_path, src_spm, tgt_spm)
    return translator.translate(text, src, tgt)
