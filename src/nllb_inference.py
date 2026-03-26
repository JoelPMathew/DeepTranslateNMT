import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
try:
    from peft import PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
import time
import logging
import argparse
import sys
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NLLBTranslator:
    def __init__(self, model_name="facebook/nllb-200-distilled-600M", adapter_path=None, device=None):
        self.model_name = model_name
        self.adapter_path = adapter_path
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # Define Style Tokens
        self.style_tokens = [
            "<style=formal>", "<style=casual>", "<style=literary>", 
            "<style=spoken>", "<style=chennai>", "<style=madurai>"
        ]
        
        logger.info(f"Loading tokenizer: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add special tokens to tokenizer
        self.tokenizer.add_special_tokens({"additional_special_tokens": self.style_tokens})
        
        logger.info(f"Loading model: {model_name} on {self.device}")
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name, 
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True
        ).to(self.device)
        
        # Resize model embeddings if new tokens were added
        if len(self.tokenizer) > self.model.config.vocab_size:
            self.model.resize_token_embeddings(len(self.tokenizer))
            
            # Neutralize new tokens by copying PAD embedding (prevents hallucination before fine-tuning)
            with torch.no_grad():
                pad_token_id = self.tokenizer.pad_token_id
                pad_embedding = self.model.get_input_embeddings().weight[pad_token_id].clone()
                for i in range(self.model.config.vocab_size, len(self.tokenizer)):
                    self.model.get_input_embeddings().weight[i] = pad_embedding
            logger.info("Neutralized new style tokens with PAD embeddings.")
        
        # Load Adapter if available
        if self.adapter_path and os.path.exists(self.adapter_path):
            if PEFT_AVAILABLE:
                logger.info(f"Loading LoRA adapter from: {self.adapter_path}")
                # Use low_cpu_mem_usage for adapter loading too
                self.model = PeftModel.from_pretrained(self.model, self.adapter_path, low_cpu_mem_usage=True).to(self.device)
            else:
                logger.warning("LoRA adapter path provided but 'peft' library is not available.")
        
        self.src_lang = "tam_Taml"
        self.tgt_lang = "eng_Latn"
        self.tokenizer.src_lang = self.src_lang

        # Load Cultural Data
        self.cultural_data = []
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cultural_data.json")
        if os.path.exists(data_path):
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    self.cultural_data = json.load(f).get("idioms", [])
                logger.info(f"Loaded {len(self.cultural_data)} cultural icons.")
            except Exception as e:
                logger.error(f"Failed to load cultural data: {e}")

    def translate(self, text, src_lang="tam_Taml", tgt_lang="eng_Latn", style="standard", max_length=128):
        if not text or not text.strip():
            logger.warning("Empty input received.")
            return ""

        # Prepend style token only if target is Tamil and NOT "standard"
        if tgt_lang == "tam_Taml" and style.lower() != "standard":
            style_token = f"<style={style}>"
            if style_token not in self.style_tokens:
                style_token = "<style=formal>"
            text = f"{style_token} {text}"

        logger.info(f"Translating ({src_lang} -> {tgt_lang}) [Style: {style}] text: {text[:50]}...")
        
        # Explicitly set src_lang for tokenization
        self.tokenizer.src_lang = src_lang
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        
        start_time = time.time()
        
        # Get language ID robustly
        tgt_lang_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        
        # Greed search (num_beams=1) is fastest on CPU.
        translated_tokens = self.model.generate(
            **inputs, 
            forced_bos_token_id=tgt_lang_id, 
            max_length=max_length,
            num_beams=1
        )
        
        translation = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        
        elapsed_time = time.time() - start_time
        logger.info(f"Translation completed in {elapsed_time:.4f}s")
        
        return translation

    def translate_batch(self, texts, src_lang="tam_Taml", tgt_lang="eng_Latn", style="formal", batch_size=8, max_length=128):
        if not texts:
            return []

        # Prepend style token to all texts in batch if target is Tamil
        if tgt_lang == "tam_Taml":
            style_token = f"<style={style}>"
            if style_token not in self.style_tokens:
                style_token = "<style=formal>"
            texts = [f"{style_token} {text}" for text in texts]

        results = []
        self.tokenizer.src_lang = src_lang
        tgt_lang_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=max_length).to(self.device)
            
            start_time = time.time()
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=tgt_lang_id,
                max_length=max_length,
                num_beams=1
            )
            batch_results = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            results.extend(batch_results)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Batch of {len(batch)} translated in {elapsed_time:.4f}s")
            
        return results

    def analyze_culture(self, text):
        """
        Analyzes the text for known Tamil idioms and returns cultural insights.
        """
        insights = []
        for item in self.cultural_data:
            if item["tamil"] in text:
                insights.append({
                    "term": item["tamil"],
                    "literal": item["english_literal"],
                    "metaphor": item["metaphor"],
                    "context": item["context"]
                })
        return insights

def main():
    parser = argparse.ArgumentParser(description="NLLB-200 Tamil-to-English Translator")
    parser.add_argument("--text", type=str, help="Single string to translate")
    parser.add_argument("--batch", nargs="+", help="Multiple strings to translate")
    parser.add_argument("--model", type=str, default="facebook/nllb-200-distilled-600M", help="HF Model ID")
    args = parser.parse_args()

    translator = NLLBTranslator(model_name=args.model)

    if args.text:
        print(f"Input: {args.text}")
        print(f"Translation: {translator.translate(args.text)}")
    elif args.batch:
        translations = translator.translate_batch(args.batch)
        for src, tgt in zip(args.batch, translations):
            print(f"---")
            print(f"Input: {src}")
            print(f"Translation: {tgt}")
    else:
        # Default example if no args provided
        example = "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"
        print(f"Example Translation:")
        print(f"Input: {example}")
        print(f"Translation: {translator.translate(example)}")

if __name__ == "__main__":
    main()
