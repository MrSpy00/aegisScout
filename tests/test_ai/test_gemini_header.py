"""Tests for Gemini provider: API key must be sent as X-Goog-Api-Key header, never in URL."""
import pytest
import httpx
import respx
from aegisScout.ai.providers.gemini_provider import GeminiProvider
from aegisScout.core.config import settings


@pytest.mark.asyncio
async def test_gemini_api_key_in_header_not_url(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "FAKE_KEY_DO_NOT_LEAK")
    monkeypatch.setattr(settings, "llm_timeout", 30.0)
    provider = GeminiProvider()

    with respx.mock:
        # Use a regex so we capture the actual URL the provider built
        # If the provider appended ?key=... this would not match (URL has extra query)
        route = respx.post(
            url__regex=r"https://generativelanguage\.googleapis\.com/v1beta/models/[^:]+:generateContent$"
        ).mock(return_value=httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        ))

        result = await provider.generate("hi")

    assert result == "ok"
    # Inspect that no ?key= was on the request URL
    request_url = str(route.calls.last.request.url)
    assert "key=" not in request_url, f"API key leaked in URL: {request_url}"
    # And the header MUST carry the key
    assert route.calls.last.request.headers.get("x-goog-api-key") == "FAKE_KEY_DO_NOT_LEAK"
    # Content type
    assert route.calls.last.request.headers.get("content-type") == "application/json"


@pytest.mark.asyncio
async def test_gemini_request_body_shape(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "k")
    monkeypatch.setattr(settings, "llm_timeout", 30.0)
    provider = GeminiProvider()

    with respx.mock:
        route = respx.post(
            url__regex=r"https://generativelanguage\.googleapis\.com/v1beta/models/[^:]+:generateContent$"
        ).mock(return_value=httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        ))

        await provider.generate("hi", system_prompt="sys")

    import json
    body = json.loads(route.calls.last.request.content)
    assert "contents" in body
    assert "systemInstruction" in body
    assert body["systemInstruction"]["parts"][0]["text"] == "sys"
    assert body["contents"][0]["parts"][0]["text"] == "hi"


@pytest.mark.asyncio
async def test_gemini_default_model(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "k")
    monkeypatch.setattr(settings, "llm_timeout", 30.0)
    provider = GeminiProvider()
    with respx.mock:
        route = respx.post(
            url__regex=r"https://generativelanguage\.googleapis\.com/v1beta/models/([^:]+):generateContent$"
        ).mock(return_value=httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        ))
        await provider.generate("hi")
    import re
    m = re.search(r"/models/([^:]+):", str(route.calls.last.request.url))
    assert m is not None
    # Default model should be a known good one
    assert m.group(1) in {"gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"}


def test_gemini_no_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    provider = GeminiProvider()
    import asyncio
    with pytest.raises(Exception):
        asyncio.run(provider.generate("hi"))


@pytest.mark.asyncio
async def test_gemini_custom_model_uses_custom(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "k")
    monkeypatch.setattr(settings, "llm_timeout", 30.0)
    provider = GeminiProvider()
    with respx.mock:
        route = respx.post(
            url__regex=r"https://generativelanguage\.googleapis\.com/v1beta/models/gemini-1.5-pro:generateContent$"
        ).mock(return_value=httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        ))
        await provider.generate("hi", model="gemini-1.5-pro")
    assert route.call_count == 1
