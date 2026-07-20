import pytest
import respx
import httpx
from aegisScout.ai.providers.openrouter_provider import OpenRouterProvider
from aegisScout.ai.providers.gemini_provider import GeminiProvider
from aegisScout.ai.providers.groq_provider import GroqProvider
from aegisScout.ai.providers.mistral_provider import MistralProvider
from aegisScout.ai.provider_router import build_provider
from aegisScout.core.config import settings

@pytest.mark.asyncio
async def test_openrouter_provider(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "mock-openrouter-key")
    provider = build_provider("openrouter")
    assert isinstance(provider, OpenRouterProvider)

    with respx.mock:
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "openrouter-response"}}]}
            )
        )
        res = await provider.generate("hello")
        assert res == "openrouter-response"

@pytest.mark.asyncio
async def test_gemini_provider(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "mock-gemini-key")
    provider = build_provider("gemini")
    assert isinstance(provider, GeminiProvider)

    with respx.mock:
        # SECURITY: Gemini uses X-Goog-Api-Key header, NOT ?key= in URL.
        route = respx.post(
            url__regex=r"https://generativelanguage\.googleapis\.com/v1beta/models/gemini-2\.5-flash:generateContent$"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "gemini-response"}]}}]}
            )
        )
        res = await provider.generate("hello")
        assert res == "gemini-response"
        # Confirm: no key in URL
        assert "key=" not in str(route.calls.last.request.url)
        # And: key in header
        assert route.calls.last.request.headers.get("x-goog-api-key") == "mock-gemini-key"

@pytest.mark.asyncio
async def test_groq_provider(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "mock-groq-key")
    provider = build_provider("groq")
    assert isinstance(provider, GroqProvider)

    with respx.mock:
        respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "groq-response"}}]}
            )
        )
        res = await provider.generate("hello")
        assert res == "groq-response"

@pytest.mark.asyncio
async def test_mistral_provider(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "mock-mistral-key")
    provider = build_provider("mistral")
    assert isinstance(provider, MistralProvider)

    with respx.mock:
        respx.post("https://api.mistral.ai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "mistral-response"}}]}
            )
        )
        res = await provider.generate("hello")
        assert res == "mistral-response"


def test_gui_activity_logs_and_radius():
    from aegisScout.gui import GuiApi
    from aegisScout.core.database import init_db, engine
    init_db(engine)
    api = GuiApi()

    # 1. Create activity log
    res = api.create_activity_log("test_action", "This is a test details message.")
    assert res.get("success") is True
    
    # 2. List logs
    logs = api.get_activity_logs()
    assert isinstance(logs, list)
    found = [l for l in logs if l["action"] == "test_action"]
    assert len(found) == 1
    assert found[0]["details"] == "This is a test details message."
    
    # 3. Clear logs
    clear_res = api.clear_activity_logs()
    assert clear_res.get("success") is True
    
    # Check that it cleared and inserted session_start
    logs_after = api.get_activity_logs()
    assert len(logs_after) == 1
    assert logs_after[0]["action"] == "session_start"

    # 4. Test Sessions endpoints
    sessions = api.get_sessions()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1
    
    new_sess_res = api.create_session("Test Workspace")
    assert new_sess_res.get("success") is True
    new_id = new_sess_res["session_id"]
    
    assert api.active_session_id == new_id
    
    sessions2 = api.get_sessions()
    active_s = [s for s in sessions2 if s["id"] == new_id][0]
    assert active_s["is_active"] is True
    assert active_s["name"] == "Test Workspace"
    
    # Switch back to default
    switch_res = api.switch_session(1)
    assert switch_res.get("success") is True
    assert api.active_session_id == 1

    # 5. Test deletion endpoints
    # Delete inactive session
    del_sess_res = api.delete_session(new_id)
    assert del_sess_res.get("success") is True
    
    # Try deleting default session (should fail)
    del_def_res = api.delete_session(1)
    assert del_def_res.get("error") is not None


def test_gui_clear_leads():
    from aegisScout.gui import GuiApi
    from aegisScout.core.models import Lead
    from sqlmodel import Session
    from aegisScout.core.database import engine, init_db
    
    init_db(engine)
    api = GuiApi()
    
    # Add a dummy lead directly to DB
    with Session(engine) as session:
        lead = Lead(
            business_name="Test Cleaning Business",
            sector="cleaning",
            status="new",
            session_id=api.active_session_id
        )
        session.add(lead)
        session.commit()
        lead_id = lead.id

    # Check it exists
    leads = api.get_leads()
    assert any(l["id"] == lead_id for l in leads)

    # Test clear by filter (sector mismatch first, should not delete)
    res_filter_fail = api.clear_leads_by_filter(status="new", sector="other_sector")
    assert res_filter_fail.get("success") is True
    assert res_filter_fail.get("deleted_count") == 0
    
    # Test clear by filter (correct sector and status)
    res_filter_ok = api.clear_leads_by_filter(status="new", sector="cleaning")
    assert res_filter_ok.get("success") is True
    assert res_filter_ok.get("deleted_count") == 1
    
    # Check it was deleted
    leads2 = api.get_leads()
    assert not any(l["id"] == lead_id for l in leads2)
    
    # Re-insert lead to test clear all
    with Session(engine) as session:
        lead = Lead(
            business_name="Test Clear All Business",
            sector="cleaning",
            status="new",
            session_id=api.active_session_id
        )
        session.add(lead)
        session.commit()
        lead_id2 = lead.id
        
    # Test clear all leads
    res_clear_all = api.clear_all_leads()
    assert res_clear_all.get("success") is True
    
    # Check everything is gone
    leads3 = api.get_leads()
    assert len(leads3) == 0
