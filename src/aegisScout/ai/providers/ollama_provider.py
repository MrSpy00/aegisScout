"""
Ollama (local LLM) provider.

Uses BaseLLMProvider._call_with_retry. The /api/chat endpoint supports
format="json" to force JSON output.

NOTE: No API key required for local Ollama.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from aegisScout.ai.base_provider import BaseLLMProvider, ProviderError
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.ollama")

OLLAMA_DEFAULT_MODEL: str = "llama3.2"
# Local models are typically slower than hosted APIs (no parallelism over internet).
# 2x timeout to avoid false-positive timeouts on bigger prompts.
OLLAMA_TIMEOUT_MULTIPLIER: float = 2.0


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    provider_name: str = "Ollama"
    api_key_env: str = ""  # No API key.

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/chat"
        # Local models: give them a 2x timeout margin.
        self.timeout_seconds = self._resolve_timeout() * OLLAMA_TIMEOUT_MULTIPLIER

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": kwargs.get("model", OLLAMA_DEFAULT_MODEL),
            "messages": messages,
            "stream": False,
            "options": {"temperature": kwargs.get("temperature", 0.7)},
            "format": "json",
        }

        async def _do_request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                return await client.post(self.api_url, json=payload)

        response = await self._call_with_retry(_do_request)
        data = response.json()
        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            logger.error(
                f"{self.provider_name}: unexpected response shape: {str(exc)[:200]}"
            )
            raise ProviderError(
                f"{self.provider_name}: unexpected response shape: {str(exc)[:200]}"
            ) from exc

        if kwargs.get("validate_json"):
            self._validate_json_output(content)
        return content
