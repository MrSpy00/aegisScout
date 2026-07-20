import pytest
import respx
import httpx
from aegisScout.ai.provider_router import ProviderRouter, ProviderError
from aegisScout.core.config import settings

@pytest.mark.asyncio
async def test_provider_router_success(monkeypatch):
    # Set settings for test
    monkeypatch.setattr(settings, "deepseek_api_key", "mock-ds-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "mock-anthropic-key")
    monkeypatch.setattr(settings, "llm_primary_provider", "deepseek")
    monkeypatch.setattr(settings, "llm_fallback_provider", "anthropic")
    
    router = ProviderRouter()
    
    with respx.mock:
        # Mock DeepSeek success response
        respx.post("https://api.deepseek.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200, 
                json={"choices": [{"message": {"content": '{"analysis": "ok", "opening_message": "hi"}'}}]}
            )
        )
        
        result = await router.generate("test prompt")
        assert "analysis" in result

@pytest.mark.asyncio
async def test_provider_router_failover(monkeypatch):
    # Set settings for test
    monkeypatch.setattr(settings, "deepseek_api_key", "mock-ds-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "mock-anthropic-key")
    monkeypatch.setattr(settings, "llm_primary_provider", "deepseek")
    monkeypatch.setattr(settings, "llm_fallback_provider", "anthropic")
    
    router = ProviderRouter()
    
    with respx.mock:
        # Mock DeepSeek failure (500)
        respx.post("https://api.deepseek.com/v1/chat/completions").mock(
            return_value=httpx.Response(500)
        )
        
        # Mock Anthropic success response
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                200, 
                json={"content": [{"text": '{"analysis": "fallback-ok", "opening_message": "hi-fallback"}'}]}
            )
        )
        
        result = await router.generate("test prompt")
        assert "fallback-ok" in result

@pytest.mark.asyncio
async def test_provider_router_all_fail(monkeypatch):
    # Set settings for test
    monkeypatch.setattr(settings, "deepseek_api_key", "mock-ds-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "mock-anthropic-key")
    monkeypatch.setattr(settings, "llm_primary_provider", "deepseek")
    monkeypatch.setattr(settings, "llm_fallback_provider", "anthropic")
    
    router = ProviderRouter()
    
    with respx.mock:
        # Mock DeepSeek failure
        respx.post("https://api.deepseek.com/v1/chat/completions").mock(
            return_value=httpx.Response(500)
        )
        # Mock Anthropic failure
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(500)
        )
        
        with pytest.raises(ProviderError):
            await router.generate("test prompt")
