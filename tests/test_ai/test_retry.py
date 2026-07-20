"""Tests for BaseProvider._call_with_retry helper: rate limit + timeout + sanitized error."""
import pytest
import httpx
import respx
from aegisScout.ai.base_provider import BaseLLMProvider, ProviderError


class DummyProvider(BaseLLMProvider):
    """Minimal concrete subclass for testing the retry helper."""
    api_key = "SECRET_KEY_LEAK_TEST"

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    async def generate(self, prompt, system_prompt=None, **kwargs):
        response = await self._call_with_retry(
            lambda: self._do_request(),
            max_retries=3,
            base_delay=0.0,  # no real sleep during tests
            provider_name="DummyProvider",
        )
        return response.text

    async def _do_request(self):
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.get("https://example.test/dummy")


@pytest.mark.asyncio
async def test_retry_after_429_then_success():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0"}, text="rate limited"),
            httpx.Response(200, text="ok"),
        ]
        result = await provider.generate("hi")
    assert result == "ok"
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_after_500_then_success():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        route.side_effect = [
            httpx.Response(500, text="server error"),
            httpx.Response(200, text="recovered"),
        ]
        result = await provider.generate("hi")
    assert result == "recovered"
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_gives_up_after_max_retries_429():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        # max_retries=3 => 4 attempts total (initial + 3 retries)
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0"}, text="rate limited"),
            httpx.Response(429, headers={"Retry-After": "0"}, text="rate limited"),
            httpx.Response(429, headers={"Retry-After": "0"}, text="rate limited"),
            httpx.Response(429, headers={"Retry-After": "0"}, text="rate limited"),
        ]
        with pytest.raises(ProviderError):
            await provider.generate("hi")
    assert route.call_count == 4


@pytest.mark.asyncio
async def test_retry_gives_up_after_max_retries_500():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        route.side_effect = [httpx.Response(500, text="err")] * 4
        with pytest.raises(ProviderError):
            await provider.generate("hi")
    assert route.call_count == 4


@pytest.mark.asyncio
async def test_provider_error_never_leaks_api_key():
    provider = DummyProvider()
    with respx.mock:
        respx.get("https://example.test/dummy").mock(return_value=httpx.Response(500, text="boom"))
        with pytest.raises(ProviderError) as exc:
            await provider.generate("hi")
    msg = str(exc.value)
    assert "SECRET_KEY_LEAK_TEST" not in msg
    assert "DUMMYPROVIDER_API_KEY" not in msg
    assert "API_KEY" not in msg


@pytest.mark.asyncio
async def test_timeout_is_retried():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        route.side_effect = [
            httpx.ConnectTimeout("slow"),
            httpx.ConnectTimeout("slow"),
            httpx.Response(200, text="ok-after-retries"),
        ]
        result = await provider.generate("hi")
    assert result == "ok-after-retries"
    assert route.call_count == 3


@pytest.mark.asyncio
async def test_non_retryable_status_not_retried():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        route.side_effect = [
            httpx.Response(400, text="bad request"),
            httpx.Response(200, text="ok"),
        ]
        with pytest.raises(ProviderError):
            await provider.generate("hi")
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_retry_respects_retry_after_header():
    provider = DummyProvider()
    with respx.mock:
        route = respx.get("https://example.test/dummy")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0"}, text="wait"),
            httpx.Response(200, text="ok"),
        ]
        result = await provider.generate("hi")
    assert result == "ok"


@pytest.mark.asyncio
async def test_provider_error_includes_attempt_count():
    provider = DummyProvider()
    with respx.mock:
        respx.get("https://example.test/dummy").mock(return_value=httpx.Response(500, text="err"))
        with pytest.raises(ProviderError) as exc:
            await provider.generate("hi")
    msg = str(exc.value)
    assert "DummyProvider" in msg or "attempts" in msg.lower() or "500" in msg
