"""
Cloud LLM translator using OpenRouter free-tier models.
Requires OPENROUTER_API_KEY in environment.
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


class CloudLLMTranslator:
    def __init__(
        self,
        api_key: str,
        model: str = "meta-llama/llama-3.1-8b-instruct:free",
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _discover_free_model(self) -> str:
        """Pick an available free model from OpenRouter."""
        resp = requests.get("https://openrouter.ai/api/v1/models", headers=self._headers(), timeout=20)
        resp.raise_for_status()
        models = resp.json().get("data", [])
        free_models = [m.get("id", "") for m in models if m.get("id", "").endswith(":free")]

        # Prefer chat/instruct-style free models for translation quality.
        preferred_keywords = ["instruct", "chat", "qwen", "llama", "gemma", "mistral"]
        for kw in preferred_keywords:
            for mid in free_models:
                if kw in mid.lower():
                    return mid

        if free_models:
            return free_models[0]
        raise RuntimeError("No free models available in OpenRouter account")

    @staticmethod
    def _looks_like_target(text: str, target_language: str) -> bool:
        if target_language == "en":
            return any("a" <= ch.lower() <= "z" for ch in text)
        if target_language == "hi":
            return any("\u0900" <= ch <= "\u097F" for ch in text)
        if target_language == "ta":
            return any("\u0B80" <= ch <= "\u0BFF" for ch in text)
        if target_language == "te":
            return any("\u0C00" <= ch <= "\u0C7F" for ch in text)
        if target_language == "kn":
            return any("\u0C80" <= ch <= "\u0CFF" for ch in text)
        if target_language == "ml":
            return any("\u0D00" <= ch <= "\u0D7F" for ch in text)
        return len(text.strip()) > 0

    def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        headers = self._headers()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 404:
            # Model is unavailable for this account; auto-switch to an available free model.
            self.model = self._discover_free_model()
            payload["model"] = self.model
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("No choices returned from cloud LLM")

        translated = (
            choices[0].get("message", {}).get("content", "").strip().replace("Output:", "").strip()
        )
        if not translated:
            raise RuntimeError("Empty translation from cloud LLM")
        return translated

    def translate(self, text: str, source_language: str, target_language: str, style: str = "formal") -> Tuple[str, float]:
        src = LANGUAGE_NAMES.get(source_language, source_language)
        tgt = LANGUAGE_NAMES.get(target_language, target_language)

        sys_prompt = (
            "You are a high-quality neural machine translation engine. "
            "Return only translated text. No explanation, no markdown, no quotes."
        )
        user_prompt = (
            f"Translate from {src} to {tgt}. Style: {style}.\n"
            f"Input: {text}\n"
            "Output:"
        )

        translated = self._call_model(sys_prompt, user_prompt)

        # Retry once with stricter instruction if model returns wrong language/script.
        if not self._looks_like_target(translated, target_language):
            strict_sys_prompt = (
                "You are a strict translation engine. "
                f"Output ONLY {tgt} text in its native script. "
                "No English explanation. No transliteration."
            )
            strict_user_prompt = (
                f"Translate this text from {src} to {tgt}.\n"
                f"Text: {text}\n"
                "Return only translated text in the target language script."
            )
            translated_retry = self._call_model(strict_sys_prompt, strict_user_prompt)
            if self._looks_like_target(translated_retry, target_language):
                translated = translated_retry

        return translated, 0.92
