"""
Multi-Language Model Loader
Handles dynamic loading of models for different language pairs with caching.
"""
import json
import os
import torch
from typing import Dict, Optional, Tuple
from pathlib import Path
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel


class MultiLanguageRegistry:
    """Registry for managing multiple language models and configurations"""

    def __init__(self, config_path: str = "config/language_registry.json"):
        """Initialize the language registry"""
        self.config_path = config_path
        self.config = self._load_config()
        self.model_cache: Dict[str, torch.nn.Module] = {}
        self.tokenizer_cache: Dict[str, object] = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _load_config(self) -> Dict:
        """Load language configuration from JSON"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_language_pair_config(self, src_lang: str, tgt_lang: str) -> Dict:
        """Get configuration for a specific language pair"""
        pair_key = f"{src_lang}-{tgt_lang}"
        if pair_key not in self.config["language_pairs"]:
            raise ValueError(f"Language pair not supported: {pair_key}")
        
        return self.config["language_pairs"][pair_key]

    def get_language_config(self, lang_code: str) -> Dict:
        """Get configuration for a specific language"""
        if lang_code not in self.config["languages"]:
            raise ValueError(f"Language not supported: {lang_code}")
        
        return self.config["languages"][lang_code]

    def supports_language_pair(self, src_lang: str, tgt_lang: str) -> bool:
        """Check if a language pair is supported"""
        pair_key = f"{src_lang}-{tgt_lang}"
        pair_config = self.config["language_pairs"].get(pair_key, {})
        return pair_config.get("supported", False)

    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return {
            code: config["name"]
            for code, config in self.config["languages"].items()
            if config.get("is_supported", True)
        }

    def get_supported_language_pairs(self) -> Dict[str, Dict]:
        """Get all supported language pairs"""
        return {
            pair: config
            for pair, config in self.config["language_pairs"].items()
            if config.get("supported", False)
        }

    def clear_model_cache(self):
        """Clear cached models to free memory"""
        for model in self.model_cache.values():
            del model
        self.model_cache.clear()
        torch.cuda.empty_cache()


class MultiLanguageModelLoader:
    """Loads and manages multi-language translation models"""

    def __init__(self, registry: MultiLanguageRegistry):
        """Initialize the model loader"""
        self.registry = registry
        self.model_cache: Dict[str, torch.nn.Module] = {}
        self.tokenizer_cache: Dict[str, object] = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def load_model(self, src_lang: str, tgt_lang: str) -> torch.nn.Module:
        """
        Load a translation model for the given language pair.
        Uses caching to avoid reloading models.
        """
        cache_key = f"{src_lang}-{tgt_lang}"
        
        if cache_key in self.model_cache:
            return self.model_cache[cache_key]

        pair_config = self.registry.get_language_pair_config(src_lang, tgt_lang)
        model_name = pair_config["model"]
        adapter_path = pair_config.get("adapter_path")

        print(f"Loading model for {src_lang} → {tgt_lang}...")
        
        # Load base model
        try:
            base_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            raise

        # Load LoRA adapter if specified
        if adapter_path and os.path.exists(adapter_path):
            print(f"Loading LoRA adapter from {adapter_path}...")
            try:
                model = PeftModel.from_pretrained(base_model, adapter_path)
            except Exception as e:
                print(f"Warning: Could not load adapter: {e}. Using base model.")
                model = base_model
        else:
            model = base_model

        model = model.to(self.device)
        model.eval()

        # Cache the model
        self.model_cache[cache_key] = model

        # Manage cache size
        max_cached = self.registry.config["model_cache"]["max_cached_models"]
        if len(self.model_cache) > max_cached:
            # Remove oldest model
            oldest_key = next(iter(self.model_cache))
            del self.model_cache[oldest_key]
            print(f"Removed cached model: {oldest_key}")

        return model

    def load_tokenizer(self, src_lang: str, tgt_lang: str) -> object:
        """Load tokenizer for the language pair"""
        cache_key = f"{src_lang}-{tgt_lang}"
        
        if cache_key in self.tokenizer_cache:
            return self.tokenizer_cache[cache_key]

        pair_config = self.registry.get_language_pair_config(src_lang, tgt_lang)
        model_name = pair_config["model"]

        print(f"Loading tokenizer for {src_lang} → {tgt_lang}...")
        
        try:
            # For M2M models, use specific tokenizer
            if "m2m" in model_name.lower():
                tokenizer = M2M100Tokenizer.from_pretrained(model_name)
            else:
                from transformers import AutoTokenizer
                tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            self.tokenizer_cache[cache_key] = tokenizer
            return tokenizer
        except Exception as e:
            print(f"Error loading tokenizer: {e}")
            raise

    def get_cached_model(self, src_lang: str, tgt_lang: str) -> Optional[torch.nn.Module]:
        """Get cached model if available"""
        cache_key = f"{src_lang}-{tgt_lang}"
        return self.model_cache.get(cache_key)

    def get_cached_tokenizer(self, src_lang: str, tgt_lang: str) -> Optional[object]:
        """Get cached tokenizer if available"""
        cache_key = f"{src_lang}-{tgt_lang}"
        return self.tokenizer_cache.get(cache_key)

    def list_cached_models(self) -> list:
        """List all currently cached models"""
        return list(self.model_cache.keys())

    def clear_cache(self):
        """Clear all caches"""
        for model in self.model_cache.values():
            del model
        self.model_cache.clear()
        self.tokenizer_cache.clear()
        torch.cuda.empty_cache()


if __name__ == "__main__":
    # Example usage
    registry = MultiLanguageRegistry()
    print("Supported languages:", registry.get_supported_languages())
    print("\nSupported language pairs:")
    for pair in registry.get_supported_language_pairs():
        print(f"  - {pair}")
