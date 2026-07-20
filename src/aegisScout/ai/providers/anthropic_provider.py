"""
Anthropic Claude API LLM provider.

Uses BaseLLMProvider._call_with_retry for resilient 429 / 5xx handling.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from aegisScout.ai.base_provider import BaseLLMProvider, ProviderError
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.anthropic")

ANTHROPIC_DEFAULT_MODEL: str = "claude-3-5-haiku-20241022"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Messages API provider."""

    provider_name: str = "Anthropic"
    api_key_env: str = "ANTHROPIC_API_KEY"

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.timeout_seconds = self._resolve_timeout()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        if not self.api_key:
            raise ProviderError(
                f"{self.provider_name}: API key not configured "
                f"(set {self.api_key_env})."
            )

        headers = {
            "content-type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        payload: dict[str, Any] = {
            "model": kwargs.get("model", ANTHROPIC_DEFAULT_MODEL),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7),
        }
        if system_prompt:
            payload["system"] = system_prompt

        async def _do_request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                return await client.post(self.api_url, headers=headers, json=payload)

        response = await self._call_with_retry(_do_request)
        data = response.json()
        try:
            content = data["content"][0]["text"]
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
