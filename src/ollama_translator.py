"""
Ollama-based translator for free local LLM translation.
"""
from __future__ import annotations

from typing import Tuple
import requests


LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "hi": "Hindi",
}


class OllamaTranslator:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen2.5:0.5b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def model_is_installed(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False
            models = resp.json().get("models", [])
            names = {m.get("name", "") for m in models}
            return self.model in names
        except requests.RequestException:
            return False

    def translate(self, text: str, source_language: str, target_language: str, style: str = "formal") -> Tuple[str, float]:
        src = LANGUAGE_NAMES.get(source_language, source_language)
        tgt = LANGUAGE_NAMES.get(target_language, target_language)

        prompt = (
            "You are a professional machine translation engine. "
            f"Translate from {src} to {tgt}. "
            f"Style: {style}. "
            "Rules: preserve meaning, do not explain, do not add notes, output only translated text.\n\n"
            f"Input:\n{text}\n\nOutput:"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            },
        }

        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        translated = (data.get("response") or "").strip()
        if not translated:
            raise RuntimeError("Empty translation from Ollama")

        # Trim common wrappers if the model still adds them.
        translated = translated.replace("Output:", "").strip()
        return translated, 0.9
