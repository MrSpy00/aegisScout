"""
LLM ProviderRouter with:
  * Lazy provider build
  * Primary -> Fallback failover
  * JSON-aware helpers: chat_json() and chat_outreach_message()
  * extract_json() that handles plain / fenced / conversational JSON output
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from aegisScout.ai.base_provider import BaseLLMProvider, ProviderError
from aegisScout.ai.providers.deepseek_provider import DeepSeekProvider
from aegisScout.ai.providers.openai_provider import OpenAIProvider
from aegisScout.ai.providers.anthropic_provider import AnthropicProvider
from aegisScout.ai.providers.ollama_provider import OllamaProvider
from aegisScout.ai.providers.openrouter_provider import OpenRouterProvider
from aegisScout.ai.providers.gemini_provider import GeminiProvider
from aegisScout.ai.providers.groq_provider import GroqProvider
from aegisScout.ai.providers.mistral_provider import MistralProvider
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.router")


class ProviderParseError(Exception):
    """Raised when an LLM response cannot be parsed as expected."""

    def __init__(self, message: str, raw: str = ""):
        super().__init__(message)
        # Truncate raw to a safe size; never include the original prompt.
        self.raw = (raw or "")[:500]


def extract_json(text: str):
    """
    Extract a JSON object OR array from an LLM response.

    Tries (in order):
      1. Direct json.loads(text)
      2. Fenced ```json ... ``` block, json.loads
      3. Fenced ``` ... ``` block (no lang), json.loads
      4. Top-level structure (object or array) chosen by first non-fence
         delimiter, with the OPPOSITE structure as fallback
      5. First balanced `{...}` block, json.loads
      6. First balanced `[...]` block, json.loads

    Returns the parsed JSON (dict OR list).
    Raises ProviderParseError on failure, with the truncated raw (no prompt).
    """
    if not text or not text.strip():
        raise ProviderParseError(
            "Empty response from LLM — cannot parse JSON.", raw=""
        )
    cleaned = text.strip()

    # 1) Direct parse.
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2) Fenced ```json ... ``` block.
    fenced = _extract_fenced(cleaned, prefer_lang="json")
    if fenced is not None:
        try:
            return json.loads(fenced)
        except (json.JSONDecodeError, ValueError):
            pass

    # 3) Fenced ``` ... ``` (no language) block.
    fenced = _extract_fenced(cleaned, prefer_lang=None)
    if fenced is not None:
        try:
            return json.loads(fenced)
        except (json.JSONDecodeError, ValueError):
            pass

    # 4) Pick the structure based on the first meaningful non-fence delimiter.
    first_open = _first_meaningful_delimiter(cleaned)
    if first_open == "[":
        arr = _first_balanced_block(cleaned, "[", "]")
        if arr is not None:
            try:
                return json.loads(arr)
            except (json.JSONDecodeError, ValueError):
                pass
    elif first_open == "{":
        obj = _first_balanced_block(cleaned, "{", "}")
        if obj is not None:
            try:
                return json.loads(obj)
            except (json.JSONDecodeError, ValueError):
                pass

    # 5) Try the OPPOSITE structure (covers cases where LLM starts with
    #    conversational text before the JSON, e.g. "Here's the list: [...]").
    if first_open != "[":
        arr = _first_balanced_block(cleaned, "[", "]")
        if arr is not None:
            try:
                return json.loads(arr)
            except (json.JSONDecodeError, ValueError):
                pass
    if first_open != "{":
        obj = _first_balanced_block(cleaned, "{", "}")
        if obj is not None:
            try:
                return json.loads(obj)
            except (json.JSONDecodeError, ValueError):
                pass

    raise ProviderParseError(
        f"No valid JSON structure found in LLM response. Raw: {text[:200]!r}",
        raw=text,
    )


def _first_balanced_block(text: str, open_ch: str, close_ch: str) -> Optional[str]:
    """Find the first balanced block of open_ch/close_ch starting from the first
    open_ch occurrence. Returns the substring (inclusive) or None.
    Respects string quoting and backslash escapes.
    """
    start = text.find(open_ch)
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _first_meaningful_delimiter(text: str) -> Optional[str]:
    """Return '[' or '{' for the first non-whitespace bracket in text.
    Skips brackets that appear inside strings. Returns None if neither
    bracket appears before any other non-whitespace token.
    """
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in (" ", "\t", "\n", "\r"):
            continue
        if ch == "[":
            return "["
        if ch == "{":
            return "{"
        # Other non-whitespace character — caller can still fall back to
        # the regex/fence extraction.
        return None
    return None


_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+-]*)\s*\n(.*?)```", re.DOTALL)


def _extract_fenced(text: str, prefer_lang: Optional[str] = None) -> Optional[str]:
    """Return the content of the first fenced code block. If prefer_lang is
    set, prefer blocks whose info string matches that language.
    """
    matches = list(_FENCE_RE.finditer(text))
    if not matches:
        return None
    if prefer_lang is not None:
        for m in matches:
            lang = (m.group(1) or "").strip().lower()
            if lang == prefer_lang:
                return m.group(2).strip()
    # Fallback: first fenced block of any language.
    return matches[0].group(2).strip()


def build_provider(provider_name: str) -> BaseLLMProvider:
    name = provider_name.lower().strip()
    if name == "deepseek":
        return DeepSeekProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "ollama":
        return OllamaProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    elif name == "gemini":
        return GeminiProvider()
    elif name == "groq":
        return GroqProvider()
    elif name == "mistral":
        return MistralProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")


class ProviderRouter:
    """
    Router that routes LLM queries to the configured primary provider,
    and falls back to fallback provider if the primary one fails.
    """

    def __init__(self):
        self.primary_name = settings.llm_primary_provider
        self.fallback_name = settings.llm_fallback_provider

        try:
            self.primary = build_provider(self.primary_name)
        except Exception as e:
            logger.error(f"Failed to initialize primary provider {self.primary_name}: {e}")
            self.primary = None

        self.fallback = None
        if self.fallback_name:
            try:
                self.fallback = build_provider(self.fallback_name)
            except Exception as e:
                logger.error(f"Failed to initialize fallback provider {self.fallback_name}: {e}")

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.primary:
            if self.fallback:
                logger.warning(
                    "Primary provider not initialized. Falling over to fallback provider."
                )
                return await self.fallback.generate(prompt, system_prompt=system_prompt, **kwargs)
            raise ProviderError("No LLM providers are initialized or available.")

        try:
            return await self.primary.generate(prompt, system_prompt=system_prompt, **kwargs)
        except Exception as e:
            logger.warning(
                f"Primary provider {self.primary_name} failed: {e}. Attempting failover."
            )
            if self.fallback:
                try:
                    return await self.fallback.generate(
                        prompt, system_prompt=system_prompt, **kwargs
                    )
                except Exception as fe:
                    logger.error(f"Fallback provider {self.fallback_name} failed: {fe}")
                    raise ProviderError(
                        f"Both primary and fallback providers failed: {e} | {fe}"
                    )
            raise ProviderError(f"Primary provider failed and no fallback configured: {e}")

    async def chat_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Send a prompt and return the parsed JSON (dict OR list).
        Uses failover across providers, then extract_json to handle markdown
        wrappers, conversational text, or bare JSON.
        """
        text = await self.generate(prompt, system_prompt=system_prompt, **kwargs)
        try:
            return extract_json(text)
        except ProviderParseError:
            logger.warning("Primary parse failed; attempting fallback if available.")
            if self.fallback is not None and self.primary is not None:
                try:
                    fb_text = await self.fallback.generate(
                        prompt, system_prompt=system_prompt, **kwargs
                    )
                    return extract_json(fb_text)
                except Exception as fe:
                    logger.error(f"Fallback provider parse failed: {fe}")
                    raise
            raise

    async def chat_outreach_message(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Specialized JSON helper for outreach message generation.
        Returns a dict with at least {"opening_message": str, "analysis": str}.
        Falls back to a deterministic safe envelope if JSON parsing fails
        after the primary AND fallback (so callers can always proceed).
        """
        try:
            parsed = await self.chat_json(prompt, system_prompt=system_prompt, **kwargs)
            if isinstance(parsed, dict):
                return parsed
            # Top-level array — wrap it.
            return {"items": parsed, "opening_message": "", "analysis": ""}
        except ProviderParseError as e:
            logger.error(f"Outreach message parse error: {e}")
            return {
                "opening_message": "",
                "analysis": "LLM parse failed; caller must provide fallback.",
                "raw": e.raw,
            }
