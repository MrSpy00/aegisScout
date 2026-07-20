import pytest
import respx
import httpx
from unittest.mock import patch
from aegisScout.discovery.google_places_provider import GooglePlacesDiscoveryProvider


class TestGooglePlacesDiscoveryProvider:
    """
    GooglePlacesDiscoveryProvider icin API mock testleri.
    """

    @pytest.fixture(autouse=True)
    def mock_settings(self):
        with patch("aegisScout.discovery.google_places_provider.settings") as mock_cfg:
            mock_cfg.google_places_api_key = "FAKE_PLACES_KEY"
            yield mock_cfg

    @pytest.mark.asyncio
    async def test_search_success(self):
        provider = GooglePlacesDiscoveryProvider()
        mock_response = {
            "places": [
                {
                    "displayName": {"text": "Istanbul Barber"},
                    "formattedAddress": "Kadikoy, Istanbul",
                    "nationalPhoneNumber": "02161234567",
                    "websiteUri": "https://istanbulbarber.com",
                    "rating": 4.5,
                    "userRatingCount": 120,
                }
            ]
        }

        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchText").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            results = await provider.search("barber", "Kadikoy")

        assert len(results) == 1
        res = results[0]
        assert res.business_name == "Istanbul Barber"
        assert res.address == "Kadikoy, Istanbul"
        assert res.phone == "02161234567"
        assert res.website_url == "https://istanbulbarber.com"
        assert res.rating == 4.5
        assert res.review_count == 120
        assert res.source == "google_places"
        assert res.has_website is True

    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        with patch("aegisScout.discovery.google_places_provider.settings") as mock_cfg:
            mock_cfg.google_places_api_key = None
            provider = GooglePlacesDiscoveryProvider()
            with pytest.raises(ValueError, match="Google Places API"):
                await provider.search("barber", "Kadikoy")

    @pytest.mark.asyncio
    async def test_search_api_error(self):
        provider = GooglePlacesDiscoveryProvider()

        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchText").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

            # Match the actual English error message from the provider
            with pytest.raises(RuntimeError, match=r"Google Places API error"):
                await provider.search("barber", "Kadikoy")
