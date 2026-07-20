"""
Tests for BaseProvider hardening:
- Exponential backoff with jitter (±0.3s)
- Sanitized error messages (no API key, no stack trace, no full body)
- JSON output validation helper
- ProviderResponseError raised on bad JSON when validate_json=True
"""
import asyncio
import time

import httpx
import pytest
import respx

from aegisScout.ai.base_provider import (
    BaseLLMProvider,
    ProviderError,
    ProviderResponseError,
)


class DummyProvider(BaseLLMProvider):
    provider_name = "Dummy"
    api_key_env = "DUMMY_API_KEY"

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    async def generate(
        self,
        prompt: str,
        system_prompt=None,
        **kwargs,
    ):
        response = await self._call_with_retry(
            lambda: self._do_request(),
            max_retries=3,
            base_delay=0.0,  # tests inject deterministic behavior below
            provider_name="Dummy",
        )
        # Per-provider responsibility: extract text and validate JSON if asked.
        text = response.text
        if kwargs.get("validate_json"):
            self._validate_json_output(text)
        return text

    async def _do_request(self):
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.get("https://example.test/dummy")


# ---------------------------------------------------------------------------
# Jitter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_backoff_includes_jitter(monkeypatch):
    """Backoff should add ±0.3s jitter on top of the base exponential delay.

    We monkey-patch asyncio.sleep to record the actual delays the base
    provider computes and pass through with a small fixed value so the
    loop continues. We then assert that those recorded delays diverge
    from the deterministic exponential schedule, proving jitter is
    applied.
    """
    sleep_calls: list[float] = []

    async def fake_sleep(d):
        sleep_calls.append(d)
        # No actual sleep — keeps test fast.

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    # Monkey-patch random.uniform to a deterministic value so we can compare.
    import aegisScout.ai.base_provider as bp

    monkeypatch.setattr(bp.random, "uniform", lambda lo, hi: 0.1)  # always +0.1

    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        # 429, 429, 429, 200 — should produce 3 sleeps before success
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0"}, text="x"),
            httpx.Response(429, headers={"Retry-After": "0"}, text="x"),
            httpx.Response(429, headers={"Retry-After": "0"}, text="x"),
            httpx.Response(200, text="ok"),
        ]
        result = await provider.generate("hi")
    assert result == "ok"
    # 3 retry sleeps (we don't sleep on the final successful attempt).
    assert len(sleep_calls) == 3
    # base_delay was 0; but we also have a `base_delay` argument of 0 in generate,
    # so the deterministic schedule would be 0*1, 0*2, 0*4 = 0,0,0.
    # With our +0.1 jitter, every sleep should be 0.1 (or -0.3 to +0.3 with a
    # different seed). At minimum, NOT all zeros — proving jitter is active.
    assert any(s != 0.0 for s in sleep_calls), (
        f"Expected at least one non-zero delay due to jitter, got {sleep_calls}"
    )


# ---------------------------------------------------------------------------
# Sanitized errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_error_message_excludes_full_body_and_status_body(monkeypatch):
    """Final failure must not include the response body, the API key,
    or the env-var name. Only the exception class and a short safe prefix."""
    provider = DummyProvider()
    with respx.mock:
        # 4x 500 with a body that contains a fake API key to verify it's
        # NOT echoed back.
        respx.get("https://example.test/dummy").mock(
            return_value=httpx.Response(
                500,
                text=(
                    "internal error: invalid_token="
                    "SECRETKEYABCDEFGHIJKLMNOPQRSTUV"
                ),
            )
        )
        with pytest.raises(ProviderError) as exc:
            await provider.generate("hi")
    msg = str(exc.value)
    assert "SECRETKEYABCDEFGHIJKLMNOPQRSTUV" not in msg
    assert "DUMMY_API_KEY" not in msg
    # Exception class name should be present (sanitized label).
    assert "Dummy" in msg
    # No traceback in message.
    assert "Traceback" not in msg


# ---------------------------------------------------------------------------
# JSON output validation
# ---------------------------------------------------------------------------


def test_validate_json_output_pure_json():
    provider = DummyProvider()
    out = provider._validate_json_output('{"ok": true}')
    assert out == {"ok": True}


def test_validate_json_output_markdown_fenced():
    provider = DummyProvider()
    out = provider._validate_json_output('```json\n{"k": 1}\n```')
    assert out == {"k": 1}


def test_validate_json_output_markdown_fenced_no_lang():
    provider = DummyProvider()
    out = provider._validate_json_output('```\n{"k": 2}\n```')
    assert out == {"k": 2}


def test_validate_json_output_malformed_raises_ProviderResponseError():
    provider = DummyProvider()
    with pytest.raises(ProviderResponseError) as exc:
        provider._validate_json_output("definitely not JSON")
    msg = str(exc.value)
    # Excerpt is bounded to 200 chars.
    assert "definitely not JSON" in msg
    assert len(msg) < 1000  # well under any leaky threshold
    # No API key, no env-var name in the error.
    assert "DUMMY_API_KEY" not in msg
    assert "SECRET" not in msg


def test_validate_json_output_array_top_level():
    provider = DummyProvider()
    assert provider._validate_json_output("[1, 2, 3]") == [1, 2, 3]


def test_validate_json_output_empty_raises():
    provider = DummyProvider()
    with pytest.raises(ProviderResponseError):
        provider._validate_json_output("")


# ---------------------------------------------------------------------------
# Integration: validate_json=True on a provider raises ProviderResponseError
# on a 200 response that isn't valid JSON.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_provider_raises_response_error_on_invalid_json(monkeypatch):
    provider = DummyProvider()
    with respx.mock:
        respx.get("https://example.test/dummy").mock(
            return_value=httpx.Response(200, text="not json at all"),
        )
        with pytest.raises(ProviderResponseError):
            await provider.generate("hi", validate_json=True)
