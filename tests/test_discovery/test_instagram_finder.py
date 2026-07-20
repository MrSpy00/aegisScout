import pytest
import respx
import httpx
from unittest.mock import patch


class TestInstagramFinder:
    """
    InstagramFinder icin Google Custom Search API mock testleri.
    API key ve CX, mock ile inject edilir.
    """

    @pytest.fixture(autouse=True)
    def mock_settings(self):
        """Her testte settings mock'la: API key ve CX'i sahte degerlerle doldur."""
        with patch("aegisScout.discovery.instagram_finder.settings") as mock_cfg:
            mock_cfg.google_custom_search_api_key = "FAKE_API_KEY"
            mock_cfg.google_custom_search_cx = "FAKE_CX"
            yield mock_cfg

    @pytest.mark.asyncio
    async def test_find_instagram_success(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()
        mock_response = {
            "items": [
                {
                    "link": "https://www.instagram.com/test_business_handle/",
                    "title": "Test Business on Instagram",
                }
            ]
        }

        with respx.mock:
            respx.get(
                url__regex=r".*/customsearch/v1.*"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            handle = await finder.find_instagram("Test Business", "Istanbul")

        assert handle == "test_business_handle"

    @pytest.mark.asyncio
    async def test_find_instagram_no_results(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()
        mock_response = {"items": []}

        with respx.mock:
            respx.get(
                url__regex=r".*/customsearch/v1.*"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            handle = await finder.find_instagram("Nonexistent Business", "Nowhere")

        assert handle is None

    @pytest.mark.asyncio
    async def test_find_instagram_api_error(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        with respx.mock:
            respx.get(
                url__regex=r".*/customsearch/v1.*"
            ).mock(return_value=httpx.Response(403, json={"error": "quota exceeded"}))

            handle = await finder.find_instagram("Test Business", "Istanbul")

        assert handle is None
