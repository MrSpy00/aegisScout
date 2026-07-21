"""
Unit tests for Zero-Config Keyless Intelligence Suite:
1. Photon Discovery Provider
2. ICANN RDAP WHOIS & Cloudflare DoH DNS Auditor
3. Contact & Email Validator (Debounce)
4. Zero-Config Media Resolver (Google Favicon, UI-Avatars)
5. Jina Reader AI & DuckDuckGo Instant Answer
"""

import pytest
import respx
import httpx
from aegisScout.discovery.photon_provider import PhotonDiscoveryProvider
from aegisScout.enrichment.domain_audit import DomainTechnicalAuditor, extract_clean_domain
from aegisScout.enrichment.contact_validator import ContactValidator
from aegisScout.enrichment.media_resolver import ZeroConfigMediaResolver
from aegisScout.ai.jina_reader import JinaReaderAI, DuckDuckGoInstantAnswer


def test_extract_clean_domain():
    """Verify URL cleaner extracts hostname accurately."""
    assert extract_clean_domain("https://www.example.com/path?q=1") == "example.com"
    assert extract_clean_domain("http://sub.domain.co.uk") == "sub.domain.co.uk"
    assert extract_clean_domain("invalid_url_without_dots") is None


def test_media_resolver():
    """Verify zero-config logo, avatar, and screenshot URL generation."""
    logo_url = ZeroConfigMediaResolver.get_domain_logo_url("example.com")
    assert logo_url == "https://www.google.com/s2/favicons?domain=example.com&sz=128"

    initials_url = ZeroConfigMediaResolver.get_initials_avatar_url("Kadıköy Psikoloji")
    assert "ui-avatars.com" in initials_url
    assert "Kad%C4%B1k%C3%B6y" in initials_url

    screenshot_url = ZeroConfigMediaResolver.get_web_screenshot_thumbnail("https://example.com")
    assert "thum.io" in screenshot_url

    resolved = ZeroConfigMediaResolver.resolve_best_avatar("Diş Kliniği", "kadikoydis.com")
    assert "google.com/s2/favicons" in resolved


def test_contact_syntax_validator():
    """Verify email syntax regex."""
    assert ContactValidator.is_valid_email_syntax("info@example.com") is True
    assert ContactValidator.is_valid_email_syntax("invalid-email-at-domain.com") is False


@pytest.mark.asyncio
@respx.mock
async def test_photon_discovery_provider():
    """Test Photon keyless geocoding provider parsing."""
    mock_resp = {
        "features": [
            {
                "properties": {
                    "name": "Kadıköy Özel Diş Sağlığı Merkezi",
                    "street": "Bahariye Cad.",
                    "housenumber": "No:45",
                    "district": "Kadıköy",
                    "city": "İstanbul",
                    "country": "Türkiye",
                    "phone": "+90 216 111 2233",
                    "website": "https://kadikoydis.com.tr"
                },
                "geometry": {
                    "coordinates": [29.025, 40.99]
                }
            }
        ]
    }

    respx.get("https://photon.komoot.io/api/").mock(
        return_value=httpx.Response(200, json=mock_resp)
    )

    provider = PhotonDiscoveryProvider()
    results = await provider.search("diş hekimi", "Kadıköy", radius_km=5)

    assert len(results) == 1
    lead = results[0]
    assert lead.business_name == "Kadıköy Özel Diş Sağlığı Merkezi"
    assert lead.phone == "+90 216 111 2233"
    assert lead.website_url == "https://kadikoydis.com.tr"
    assert lead.source == "photon_komoot"


@pytest.mark.asyncio
@respx.mock
async def test_domain_technical_auditor_rdap():
    """Test ICANN RDAP WHOIS parsing."""
    mock_rdap = {
        "events": [
            {"eventAction": "registration", "eventDate": "2020-01-15T10:00:00Z"},
            {"eventAction": "expiration", "eventDate": "2028-01-15T10:00:00Z"}
        ],
        "entities": [
            {
                "roles": ["registrar"],
                "vcardArray": ["vcard", [["fn", {}, "text", "GoDaddy.com, LLC"]]]
            }
        ]
    }

    respx.get("https://rdap.org/domain/example.com").mock(
        return_value=httpx.Response(200, json=mock_rdap)
    )

    audit = await DomainTechnicalAuditor.get_rdap_whois("example.com")
    assert audit["domain"] == "example.com"
    assert audit["registration_date"] == "2020-01-15T10:00:00Z"
    assert audit["registrar"] == "GoDaddy.com, LLC"


@pytest.mark.asyncio
@respx.mock
async def test_contact_validator_debounce():
    """Test Debounce disposable email check."""
    respx.get("https://disposable.debounce.io/").mock(
        return_value=httpx.Response(200, json={"disposable": "true"})
    )

    is_disp = await ContactValidator.is_disposable_email("temp@mailinator.com")
    assert is_disp is True


@pytest.mark.asyncio
@respx.mock
async def test_jina_reader_ai():
    """Test Jina Reader AI Markdown fetcher."""
    respx.get("https://r.jina.ai/https://example.com").mock(
        return_value=httpx.Response(200, text="# Example Header\n\nThis is scraped markdown.")
    )

    md = await JinaReaderAI.read_url_markdown("example.com")
    assert md is not None
    assert "# Example Header" in md
