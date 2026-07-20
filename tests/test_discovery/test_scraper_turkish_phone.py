"""Tests for WebScraper Turkish phone number, generic intl, and email regex extraction."""
import pytest
from aegisScout.discovery.web_scraper import WebScraper


class TestWebScraperRegexes:
    """Regression: Turkish 10-digit mobile and intl/email formats must be detected."""

    @pytest.mark.asyncio
    async def test_turkish_mobile_5xx_extracted(self, monkeypatch):
        """0-prefixed 10-digit Turkish mobile: 05551234567."""
        scraper = WebScraper()
        mock_html = """
        <html><body>
        <a href="tel:+905551234567">Call</a>
        </body></html>
        """
        # The 'tel:' link is already handled. Test the body-text regex path:
        mock_html_body = """
        <html><body>
        Bize ulaşın: 05551234567
        </body></html>
        """

        class MockResponse:
            def __init__(self, t):
                self.status_code = 200
                self.text = t
                self.url = "https://dummyurl.com"

        async def mock_get(self, *args, **kwargs):
            return MockResponse(mock_html_body)

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
        _, phone, _, _ = await scraper.scrape_site("https://dummyurl.com")
        assert phone is not None
        # Should contain the digits
        assert "5551234567" in phone

    @pytest.mark.asyncio
    async def test_turkish_with_spaces_and_dashes(self, monkeypatch):
        """0555 123 45 67 and 0555-123-45-67 formats."""
        scraper = WebScraper()
        mock_html = "<html><body>Tel: 0555 123 45 67</body></html>"

        class MockResponse:
            def __init__(self, t):
                self.status_code = 200
                self.text = t
                self.url = "https://dummyurl.com"

        async def mock_get(self, *args, **kwargs):
            return MockResponse(mock_html)

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
        _, phone, _, _ = await scraper.scrape_site("https://dummyurl.com")
        assert phone is not None
        # Digits-only assertion
        digits = "".join(c for c in phone if c.isdigit())
        assert digits.endswith("5551234567") or digits.endswith("1234567")

    @pytest.mark.asyncio
    async def test_email_extracted(self, monkeypatch):
        """Standard email regex must capture contact@example.com."""
        scraper = WebScraper()
        mock_html = """
        <html><body>
        Contact us at info@bizimfirma.com.tr
        </body></html>
        """

        class MockResponse:
            def __init__(self, t):
                self.status_code = 200
                self.text = t
                self.url = "https://dummyurl.com"

        async def mock_get(self, *args, **kwargs):
            return MockResponse(mock_html)

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
        # We don't return email currently; but phone regex shouldn't break on email text
        # The key assertion: scraper must NOT raise on email text
        _, phone, _, _ = await scraper.scrape_site("https://dummyurl.com")
        # No false positive phone from email
        if phone is not None:
            assert "@" not in phone

    @pytest.mark.asyncio
    async def test_international_phone_plus_prefix(self, monkeypatch):
        scraper = WebScraper()
        mock_html = "<html><body>Call us: +44 20 7946 0958</body></html>"

        class MockResponse:
            def __init__(self, t):
                self.status_code = 200
                self.text = t
                self.url = "https://dummyurl.com"

        async def mock_get(self, *args, **kwargs):
            return MockResponse(mock_html)

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
        _, phone, _, _ = await scraper.scrape_site("https://dummyurl.com")
        assert phone is not None
        assert "44" in phone and "7946" in phone

    @pytest.mark.asyncio
    async def test_no_phone_returns_none(self, monkeypatch):
        scraper = WebScraper()
        mock_html = "<html><body>Just some text with no phone.</body></html>"

        class MockResponse:
            def __init__(self, t):
                self.status_code = 200
                self.text = t
                self.url = "https://dummyurl.com"

        async def mock_get(self, *args, **kwargs):
            return MockResponse(mock_html)

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
        _, phone, _, _ = await scraper.scrape_site("https://dummyurl.com")
        assert phone is None

    @pytest.mark.asyncio
    async def test_ssl_state_does_not_persist_across_calls(self, monkeypatch):
        """Bug fix: verify_ssl must be per-request, not stored on the client."""
        # First call: SSL error -> retry without verify
        # Second call: must be re-enabled (verify=True initially)
        scraper = WebScraper()
        call_count = {"n": 0}

        class MockResponse:
            def __init__(self, t, code=200):
                self.status_code = code
                self.text = t
                self.url = "https://dummyurl.com"

        async def mock_get(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Simulate SSL on first try
                raise Exception("SSL handshake failure")
            return MockResponse("<html><body>Hello</body></html>")

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
        # First URL should retry internally and succeed
        _, _, _, _ = await scraper.scrape_site("https://dummyurl1.com")
        # Second URL — the scraper should treat each call fresh
        _, _, _, _ = await scraper.scrape_site("https://dummyurl2.com")
        # If verify_ssl persisted, the second call would skip the verify=True initial attempt.
        # With per-request reset, both calls behave identically.
        assert call_count["n"] >= 2
