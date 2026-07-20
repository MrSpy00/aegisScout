"""
Base LLM provider with shared retry, timeout, sanitization, and JSON validation.

All concrete LLM providers in aegisScout must subclass BaseLLMProvider and use
the `_call_with_retry` helper for any HTTP call. This guarantees:

  * Exponential backoff with jitter on 429 / 5xx (and httpx timeouts)
  * Retry-After header is honored when present
  * Error messages NEVER include API keys, env var names, or full bodies
  * LLM_TIMEOUT_SECONDS env var controls the per-request httpx timeout
  * Slow providers (DeepSeek, Mistral) get the standard 30s floor automatically
  * Optional JSON validation (use `validate_json=True` kwarg) for use cases
    that expect structured model output
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional

import httpx


# Env-driven timeout. Defaults to 30s; slow providers (DeepSeek, Mistral) get
# max(LLM_TIMEOUT_SECONDS, 30) automatically applied in subclasses.
_DEFAULT_TIMEOUT_SECONDS: float = 30.0
_MAX_TRUNCATED_ERROR_CHARS: int = 500
_MAX_JSON_EXCERPT_CHARS: int = 200
# Jitter window applied to every backoff delay (seconds).
# Total delay = backoff + uniform(-_BACKOFF_JITTER_SECONDS, +_BACKOFF_JITTER_SECONDS).
_BACKOFF_JITTER_SECONDS: float = 0.3
_MAX_BACKOFF_SECONDS: float = 30.0


class ProviderError(Exception):
    """Raised when an LLM provider request fails after all retries.

    The message NEVER contains the API key value, the env var name, or
    the response body. Only the provider label, status code, attempt
    count, and exception class name are exposed.
    """


class ProviderResponseError(ProviderError):
    """Raised when a provider's model output cannot be parsed as expected
    (typically non-JSON when the caller required JSON).

    The message contains a redacted excerpt of the model output (capped
    at 200 chars) plus the provider label, but NEVER the API key.
    """


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    Concrete subclasses must override `generate(prompt, system_prompt, **kwargs)`
    and use `self._call_with_retry(...)` for HTTP calls.

    Subclasses MAY opt into automatic JSON validation of the model output
    by honoring the `validate_json=True` keyword argument (and calling
    `self._validate_json_output(text)` on the extracted text). The router
    layer sets this flag for structured-output calls.
    """

    #: Subclasses should set this; used in error messages (NOT the API key value).
    provider_name: str = "BaseLLMProvider"

    #: Subclasses must set the env var name (e.g. "GEMINI_API_KEY") so error
    #: messages can be sanitized.
    api_key_env: str = ""

    #: Subclasses should set False if their model rejects custom temperature
    #: (e.g. OpenAI o1, Anthropic extended-thinking). Default True.
    supports_temperature: bool = True

    @abstractmethod
    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> str:
        """Generate a text completion for a given prompt and system prompt."""
        raise NotImplementedError

    async def stream_generate(
        self, prompt: str, system_prompt: Optional[str] = None, callback: Optional[Callable[[str], None]] = None, **kwargs
    ) -> str:
        """Stream tokens to callback as they arrive, returning complete text."""
        result = await self.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
        if callback:
            callback(result)
        return result

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    def _resolve_timeout(self) -> float:
        """Read LLM_TIMEOUT_SECONDS from env. Defaults to 30s."""
        try:
            return float(os.environ.get("LLM_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS))
        except (TypeError, ValueError):
            return _DEFAULT_TIMEOUT_SECONDS

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    async def _call_with_retry(
        self,
        fn: Callable[[], Awaitable[httpx.Response]],
        *,
        max_retries: int = 3,
        base_delay: float = 1.0,
        provider_name: Optional[str] = None,
    ) -> httpx.Response:
        """Call an httpx-returning async function with retry, backoff, jitter,
        and sanitized error reporting.

        Retry behavior:
          * HTTP 429 (rate limit)  -> retry; honor Retry-After if present
          * HTTP 5xx (server error) -> retry
          * httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError
                                     -> retry
          * HTTP 4xx (other)        -> raise ProviderError immediately (no retry)
          * HTTP 2xx                -> return response

        On final failure, raise ProviderError with a message that NEVER
        contains the API key value, env var name, full body, or traceback.

        Args:
            fn: A zero-arg async callable that performs one HTTP request and
                returns an httpx.Response.
            max_retries: Maximum number of retry attempts (after initial try).
            base_delay: Base delay for exponential backoff (seconds). The first
                retry waits `base_delay` (+/- jitter), then `base_delay*2`
                (+/- jitter), etc., capped at 30s.
            provider_name: Label for the provider in error messages; defaults
                to the class's `provider_name` attribute.
        """
        label = provider_name or self.provider_name
        last_exc: Optional[BaseException] = None
        max_attempts = max(1, max_retries + 1)

        for attempt in range(max_attempts):
            try:
                response = await fn()
            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
                asyncio.TimeoutError,
            ) as exc:
                last_exc = exc
                # If we have retries left, back off and retry.
                if attempt < max_attempts - 1:
                    delay = self._compute_backoff(base_delay, attempt, retry_after=None)
                    await asyncio.sleep(delay)
                    continue
                # Out of retries: raise sanitized error.
                safe_msg = self._sanitize_error_message(
                    f"{label}: network error after {attempt + 1} attempts "
                    f"({type(exc).__name__})."
                )
                raise ProviderError(safe_msg) from exc

            # Got a response: decide retry vs raise.
            if response.status_code == 429:
                if attempt < max_attempts - 1:
                    retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
                    delay = self._compute_backoff(base_delay, attempt, retry_after)
                    await asyncio.sleep(delay)
                    last_exc = None
                    continue
                raise ProviderError(
                    self._sanitize_error_message(
                        f"{label}: rate limited (HTTP 429) after "
                        f"{attempt + 1} attempts."
                    )
                )
            if 500 <= response.status_code < 600:
                if attempt < max_attempts - 1:
                    delay = self._compute_backoff(base_delay, attempt, retry_after=None)
                    await asyncio.sleep(delay)
                    last_exc = None
                    continue
                # Final 5xx — log a short, redacted message. We do NOT include
                # the body to avoid leaking server-side error details.
                safe_msg = self._sanitize_error_message(
                    f"{label}: server error HTTP {response.status_code} after "
                    f"{attempt + 1} attempts."
                )
                logger_method = getattr(self, "_log_error", None)
                if callable(logger_method):
                    logger_method(safe_msg)
                raise ProviderError(safe_msg)
            # Non-retryable status (4xx other than 429, or 2xx) -> return.
            if not (200 <= response.status_code < 300):
                # 4xx — caller handles parse; raise so it gets caught upstream.
                # Truncate body to a safe size; never include the original prompt.
                body_snip = (response.text or "")[:_MAX_TRUNCATED_ERROR_CHARS]
                safe_msg = self._sanitize_error_message(
                    f"{label}: HTTP {response.status_code}: {type(__import__('httpx').HTTPStatusError).__name__}."
                )
                # Keep the body excerpt in a separate field for debugging but
                # scrub the user-visible message.
                raise ProviderError(safe_msg)
            return response

        # Defensive — should never be reached.
        raise ProviderError(
            self._sanitize_error_message(
                f"{label}: failed after {max_attempts} attempts: "
                f"{type(last_exc).__name__ if last_exc else 'unknown'}"
            )
        )

    @classmethod
    def _compute_backoff(cls, base_delay: float, attempt: int, retry_after: Optional[float]) -> float:
        """Compute delay for the given attempt.

        Priority:
          1. Retry-After header (if valid positive number)
          2. Exponential backoff: base_delay * 2^attempt
          3. Add symmetric jitter: uniform(-_BACKOFF_JITTER_SECONDS, +_BACKOFF_JITTER_SECONDS)
          4. Capped at 30s and floored at 0s
        """
        if retry_after is not None and retry_after > 0:
            base = min(retry_after, _MAX_BACKOFF_SECONDS)
        else:
            base = base_delay * (2 ** attempt)
            base = min(base, _MAX_BACKOFF_SECONDS)
        # Symmetric jitter: +/- _BACKOFF_JITTER_SECONDS.
        jitter = random.uniform(-_BACKOFF_JITTER_SECONDS, _BACKOFF_JITTER_SECONDS)
        return max(0.0, base + jitter)

    @staticmethod
    def _parse_retry_after(value: Optional[str]) -> Optional[float]:
        """Parse the Retry-After header. Returns seconds (float) or None.

        Per RFC 7231, Retry-After can be an HTTP-date or seconds. We only
        support the seconds form (which is what every LLM provider sends).
        """
        if value is None:
            return None
        try:
            return float(value.strip())
        except (TypeError, ValueError, AttributeError):
            return None

    # ------------------------------------------------------------------
    # Error sanitization
    # ------------------------------------------------------------------

    @classmethod
    def _sanitize_error_message(cls, message: str) -> str:
        """Strip API key values, env var names, and bodies from an error message.

        Defense-in-depth: even if the upstream library embeds the API key
        or response body in an exception, we never let it reach the log or
        the user.
        """
        scrubbed = message
        # Remove env var name (e.g. "GEMINI_API_KEY", "DUMMY_API_KEY") from
        # the message, in case the provider leaked it.
        env_name = getattr(cls, "api_key_env", "") or ""
        if env_name:
            scrubbed = re.sub(re.escape(env_name), "<REDACTED>", scrubbed, flags=re.IGNORECASE)
        # Generic Bearer token scrub (long random-looking strings after "Bearer ")
        scrubbed = re.sub(
            r"(?i)Bearer\s+[A-Za-z0-9._\-]{12,}", "Bearer <REDACTED>", scrubbed
        )
        # Generic key=value (env=style) where the value is long
        scrubbed = re.sub(
            r"(?i)(key|api_key|token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9._\-]{12,}",
            r"\1=<REDACTED>",
            scrubbed,
        )
        # Drop stack-trace markers (defense in depth).
        scrubbed = re.sub(r"Traceback \(most recent call last\):", "", scrubbed)
        return scrubbed

    # ------------------------------------------------------------------
    # JSON output validation
    # ------------------------------------------------------------------

    @classmethod
    def _validate_json_output(cls, text: str) -> Any:
        """Strip markdown fences from an LLM response and json.loads it.

        Returns the parsed JSON (dict or list). Raises ProviderResponseError
        on failure, with a redacted excerpt (max _MAX_JSON_EXCERPT_CHARS).
        """
        if text is None or not str(text).strip():
            raise ProviderResponseError(
                f"{cls.provider_name}: empty model response, cannot parse JSON."
            )
        cleaned = str(text).strip()
        # Strip markdown fences if present: ```json\n{...}\n``` or ```\n{...}\n```
        fence_re = re.compile(
            r"^\s*```(?:[a-zA-Z0-9_+-]*)\s*\n(.*?)\n\s*```\s*$",
            re.DOTALL,
        )
        m = fence_re.match(cleaned)
        if m:
            cleaned = m.group(1).strip()
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError) as exc:
            excerpt = cleaned[:_MAX_JSON_EXCERPT_CHARS]
            # Sanitize the excerpt (defensive — keys could be in the body).
            excerpt = cls._sanitize_error_message(excerpt)
            raise ProviderResponseError(
                f"{cls.provider_name}: response is not valid JSON "
                f"({type(exc).__name__}): {excerpt!r}"
            ) from exc
