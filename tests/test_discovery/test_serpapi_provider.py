"""
Tests for SerpApi Google Maps & Local Pack Discovery Providers.
"""

import pytest
import respx
import httpx
from aegisScout.discovery.serpapi_provider import (
    SerpApiMapsDiscoveryProvider,
    SerpApiLocalPackDiscoveryProvider,
)
from aegisScout.core.config import settings


@pytest.mark.asyncio
async def test_serpapi_maps_provider_without_key(monkeypatch):
    """When no SerpApi key is provided, provider falls back gracefully to web search."""
    monkeypatch.setattr(settings, "serpapi_api_key", "", raising=False)
    provider = SerpApiMapsDiscoveryProvider()
    results = await provider.search("psikolog", "Kadıköy", radius_km=5)
    assert isinstance(results, list)


@pytest.mark.asyncio
@respx.mock
async def test_serpapi_maps_provider_with_key(monkeypatch):
    """When SerpApi key is provided, parses Google Maps results into LeadCandidate list."""
    monkeypatch.setattr(settings, "serpapi_api_key", "fake_serpapi_key_123", raising=False)

    mock_response = {
        "local_results": [
            {
                "title": "Dr. Ahmet Yılmaz Psikoloji Kliniği",
                "phone": "+90 216 555 0101",
                "website": "https://drahmet.com",
                "address": "Moda Cad. No:12 Kadıköy/İstanbul",
                "rating": 4.9,
                "reviews": 85,
                "user_reviews": [
                    {"text": "Harika bir terapist, çok ilgililer."}
                ],
                "thumbnail": "https://serpapi.com/thumb.jpg",
                "place_id": "ChIJ123456789"
            }
        ]
    }

    respx.get("https://serpapi.com/search.json").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    provider = SerpApiMapsDiscoveryProvider()
    results = await provider.search("psikolog", "Kadıköy", radius_km=5)

    assert len(results) == 1
    lead = results[0]
    assert lead.business_name == "Dr. Ahmet Yılmaz Psikoloji Kliniği"
    assert lead.phone == "+90 216 555 0101"
    assert lead.website_url == "https://drahmet.com"
    assert lead.address == "Moda Cad. No:12 Kadıköy/İstanbul"
    assert lead.rating == 4.9
    assert lead.review_count == 85
    assert lead.profile_image_url == "https://serpapi.com/thumb.jpg"
    assert lead.source == "serpapi_maps"
    assert "Harika bir terapist" in (lead.outreach_hook or "")


@pytest.mark.asyncio
@respx.mock
async def test_serpapi_local_pack_provider_with_key(monkeypatch):
    """Test SerpApi Google Local Pack parsing."""
    monkeypatch.setattr(settings, "serpapi_api_key", "fake_serpapi_key_123", raising=False)

    mock_response = {
        "local_results": [
            {
                "title": "Kadıköy Diş Kliniği",
                "phone": "+90 216 333 4455",
                "address": "Bahariye Cad. Kadıköy",
                "rating": 4.8,
                "reviews": 120,
                "links": {"website": "https://kadikoydis.com"}
            }
        ],
        "organic_results": [
            {
                "title": "İstanbul Diş Hekimleri Rehberi - En İyi Klinikler",
                "link": "https://disrehberi.com"
            }
        ]
    }

    respx.get("https://serpapi.com/search.json").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    provider = SerpApiLocalPackDiscoveryProvider()
    results = await provider.search("diş hekimi", "Kadıköy", radius_km=5)

    assert len(results) >= 1
    local_lead = results[0]
    assert local_lead.business_name == "Kadıköy Diş Kliniği"
    assert local_lead.phone == "+90 216 333 4455"
    assert local_lead.rating == 4.8
