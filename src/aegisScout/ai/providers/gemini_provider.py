"""
Google Gemini API LLM provider.

SECURITY: The API key is sent in the `X-Goog-Api-Key` HEADER, never in the
URL query string. The URL has no `?key=...` parameter.

Uses BaseLLMProvider._call_with_retry for resilient 429 / 5xx handling.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from aegisScout.ai.base_provider import BaseLLMProvider, ProviderError
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.gemini")

GEMINI_DEFAULT_MODEL: str = "gemini-2.5-flash"


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider using models:generateContent."""

    provider_name: str = "Gemini"
    api_key_env: str = "GEMINI_API_KEY"

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.timeout_seconds = self._resolve_timeout()

    def _build_url(self, model: str) -> str:
        # SECURITY: No `?key=` query param. The key goes in the header.
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )

    def _build_headers(self, api_key: Optional[str] = None) -> dict[str, str]:
        key = api_key or settings.get_next_api_key("gemini_api_key") or self.api_key or ""
        return {
            "X-Goog-Api-Key": key,
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        return payload

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        active_key = settings.get_next_api_key("gemini_api_key") or self.api_key
        if not active_key:
            raise ProviderError(
                f"{self.provider_name}: API key not configured "
                f"(set {self.api_key_env})."
            )

        model = kwargs.get("model", GEMINI_DEFAULT_MODEL)
        temperature = kwargs.get("temperature", 0.7)
        url = self._build_url(model)
        headers = self._build_headers(active_key)
        payload = self._build_payload(prompt, system_prompt, temperature)

        async def _do_request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                return await client.post(url, headers=headers, json=payload)

        response = await self._call_with_retry(_do_request)
        data = response.json()
        # Standard Gemini success path
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error(
                f"{self.provider_name}: unexpected response shape: {str(exc)[:200]}"
            )
            raise ProviderError(
                f"{self.provider_name}: unexpected response shape: {str(exc)[:200]}"
            ) from exc

        if kwargs.get("validate_json"):
            self._validate_json_output(content)
        return content

    async def generate_vision(
        self,
        prompt: str,
        image_bytes_base64: str,
        mime_type: str = "image/png",
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        if not self.api_key:
            raise ProviderError(
                f"{self.provider_name}: API key not configured "
                f"(set {self.api_key_env})."
            )

        model = kwargs.get("model", GEMINI_DEFAULT_MODEL)
        temperature = kwargs.get("temperature", 0.7)
        url = self._build_url(model)
        headers = self._build_headers()

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": image_bytes_base64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": temperature,
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async def _do_request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                return await client.post(url, headers=headers, json=payload)

        response = await self._call_with_retry(_do_request)
        data = response.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error(
                f"{self.provider_name}: unexpected response shape: {str(exc)[:200]}"
            )
            raise ProviderError(
                f"{self.provider_name}: unexpected response shape: {str(exc)[:200]}"
            ) from exc

        if kwargs.get("validate_json"):
            self._validate_json_output(content)
        return content

