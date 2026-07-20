"""
DeepSeek API LLM provider.

DeepSeek is known to be slow on cold start. LLM_TIMEOUT_SECONDS env var
floors at 30s automatically via _resolve_timeout (max(_, 30)).
Uses BaseLLMProvider._call_with_retry for resilient 429 / 5xx handling.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from aegisScout.ai.base_provider import BaseLLMProvider, ProviderError
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.deepseek")

DEEPSEEK_DEFAULT_MODEL: str = "deepseek-chat"
DEEPSEEK_FLOOR_TIMEOUT_SECONDS: float = 30.0


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek Chat Completions API provider."""

    provider_name: str = "DeepSeek"
    api_key_env: str = "DEEPSEEK_API_KEY"

    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        # DeepSeek cold start: enforce a 30s floor.
        self.timeout_seconds = max(self._resolve_timeout(), DEEPSEEK_FLOOR_TIMEOUT_SECONDS)

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
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": kwargs.get("model", DEEPSEEK_DEFAULT_MODEL),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        if kwargs.get("response_format") is not None:
            payload["response_format"] = kwargs["response_format"]

        async def _do_request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                return await client.post(self.api_url, headers=headers, json=payload)

        response = await self._call_with_retry(_do_request)
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
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
