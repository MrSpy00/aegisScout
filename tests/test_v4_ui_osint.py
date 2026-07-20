import pytest
from pathlib import Path
from sqlmodel import SQLModel, Session
from aegisScout.core import database as db_module
from aegisScout.core.config import settings
from aegisScout.core.models import Lead, UserSession
from aegisScout.core.screen_audit import capture_screenshot, generate_local_heuristic_audit
from aegisScout.core.deep_osint import DeepOSINTScanner
from aegisScout.gui_impl import GuiApi
from aegisScout.discovery.web_search_provider import WebSearchDiscoveryProvider


@pytest.fixture
def test_env():
    test_engine = db_module.make_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        us = UserSession(id=1, name="Varsayılan Oturum")
        session.add(us)
        session.commit()
    old_engine = db_module.engine
    db_module.engine = test_engine
    yield test_engine
    db_module.engine = old_engine


def test_default_theme_setting():
    """Verify default UI theme is set to Amethyst Purple."""
    assert settings.gui_theme == "theme-amethyst"
    assert settings.gui_language == "tr"


def test_screen_audit_heuristic_fallback(tmp_path):
    """Test local heuristic audit fallback logic."""
    lead = Lead(
        business_name="Test Kuaför",
        sector="berber",
        has_website=True,
        website_url="https://example.com",
        page_speed_mobile=40,
        has_broken_links=True,
        phone=None,
        session_id=1
    )
    audit = generate_local_heuristic_audit(lead)
    assert audit["quality_score"] < 80
    assert len(audit["errors"]) >= 2
    assert "hook" in audit


@pytest.mark.asyncio
async def test_deep_osint_scanner(tmp_path):
    """Test Deep OSINT scanner website metadata & social discovery aggregation."""
    scanner = DeepOSINTScanner()
    res = await scanner.scan_website("https://example.com")
    assert "cms" in res
    assert "has_ssl" in res
    assert "social_links" in res


def test_gui_api_deep_osint_scan(test_env):
    """Test GuiApi run_deep_osint_scan endpoint."""
    with Session(test_env) as session:
        lead = Lead(
            business_name="Scout Berber",
            sector="berber",
            has_website=True,
            website_url="https://example.com",
            session_id=1,
            status="new"
        )
        session.add(lead)
        session.commit()
        lead_id = lead.id

    api = GuiApi()
    res = api.run_deep_osint_scan(lead_id)
    assert res.get("success") is True
    assert "osint" in res


@pytest.mark.asyncio
async def test_web_search_high_yield():
    """Test high-yield query expansion in WebSearchDiscoveryProvider."""
    provider = WebSearchDiscoveryProvider()
    candidates = await provider.search("berber", "Kadıköy")
    assert isinstance(candidates, list)
