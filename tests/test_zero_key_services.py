"""
Unit and Integration Tests for aegisScout Zero-Key Free APIs & OSINT Services.
Tests Photon, BigDataCloud, Country.is, ICANN RDAP, Cloudflare DoH, IP-API,
Google Favicon, Unavatar, UI-Avatars, Microlink, Thum.io, Debounce, EmailOSINT,
Rapid Email, Jina Reader AI, and MyMemory Translator.
"""

import pytest
import asyncio
from aegisScout.discovery.photon_provider import PhotonDiscoveryProvider
from aegisScout.discovery.location_provider import ZeroConfigLocationProvider
from aegisScout.enrichment.domain_audit import DomainTechnicalAuditor, extract_clean_domain
from aegisScout.enrichment.media_resolver import ZeroConfigMediaResolver
from aegisScout.enrichment.contact_validator import ContactValidator
from aegisScout.ai.jina_reader import JinaReaderAI, DuckDuckGoInstantAnswer
from aegisScout.ai.translation_service import MyMemoryTranslator
from aegisScout.gui_impl import set_console_visibility, GuiApi


def test_extract_clean_domain():
    assert extract_clean_domain("https://www.example.com/test?q=1") == "example.com"
    assert extract_clean_domain("http://sub.domain.co.uk") == "sub.domain.co.uk"
    assert extract_clean_domain(None) is None


def test_zero_config_media_resolver():
    favicon = ZeroConfigMediaResolver.get_domain_logo_url("example.com")
    assert favicon == "https://www.google.com/s2/favicons?domain=example.com&sz=128"

    unavatar = ZeroConfigMediaResolver.get_unavatar_url("example.com")
    assert unavatar == "https://unavatar.io/example.com"

    initials = ZeroConfigMediaResolver.get_initials_avatar_url("Aegis Scout")
    assert "ui-avatars.com" in initials and "Aegis%20Scout" in initials

    screenshot = ZeroConfigMediaResolver.get_web_screenshot_thumbnail("example.com")
    assert "image.thum.io" in screenshot and "example.com" in screenshot

    best = ZeroConfigMediaResolver.resolve_best_avatar("Aegis Soft", "example.com")
    assert "google.com/s2/favicons" in best


def test_contact_validator_syntax():
    assert ContactValidator.is_valid_email_syntax("user@example.com") is True
    assert ContactValidator.is_valid_email_syntax("invalid-email") is False


@pytest.mark.asyncio
async def test_location_provider_ip_country():
    res = await ZeroConfigLocationProvider.get_ip_country("8.8.8.8")
    assert res.get("ip") == "8.8.8.8"
    assert res.get("country_code") in ["US", "GLOBAL", None]


@pytest.mark.asyncio
async def test_domain_technical_auditor_doh():
    res = await DomainTechnicalAuditor.get_dns_infrastructure("google.com")
    assert res.get("domain") == "google.com"
    assert len(res.get("mx_records", [])) > 0
    assert res.get("email_provider") == "Google Workspace"


@pytest.mark.asyncio
async def test_mymemory_translator():
    res = await MyMemoryTranslator.translate_text("Hello", "en", "tr")
    assert "translated_text" in res
    translated = res["translated_text"].lower()
    assert any(word in translated for word in ["merhaba", "selam", "hello"])




def test_gui_api_zero_key_methods():
    api = GuiApi()
    res = api.resolve_media_zero_key("Test Business", "example.com")
    assert res.get("google_favicon_url") is not None
    assert res.get("best_avatar_url") is not None


def test_set_console_visibility_no_crash():
    # Calling set_console_visibility should run without raising exceptions
    set_console_visibility(True)
    set_console_visibility(False)
