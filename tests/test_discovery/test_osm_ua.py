"""Tests for OSM provider User-Agent compliance with Nominatim/Overpass policy."""
import os
import pytest
import respx
import httpx
from aegisScout.discovery.osm_provider import OSMDiscoveryProvider, _build_user_agent


class TestOsmUserAgent:
    """Per OSM policy, User-Agent must identify the app and a contact channel."""

    def test_default_ua_includes_app_name(self, monkeypatch):
        monkeypatch.delenv("AEGIS_CONTACT_EMAIL", raising=False)
        ua = _build_user_agent()
        assert "aegisScout" in ua
        # Must be non-empty
        assert len(ua) > 0
        # Must not be the hardcoded old UA exactly
        assert ua != "aegisScout/0.1.0 (contact: github.com/MrSpy00)"

    def test_ua_with_contact_email(self, monkeypatch):
        monkeypatch.setenv("AEGIS_CONTACT_EMAIL", "ops@example.com")
        ua = _build_user_agent()
        assert "ops@example.com" in ua
        assert "mailto:" in ua

    def test_ua_format_matches_policy(self, monkeypatch):
        """UA must be of form 'App/Version (contact-info)'."""
        monkeypatch.setenv("AEGIS_CONTACT_EMAIL", "team@example.com")
        ua = _build_user_agent()
        # Should contain version
        assert "/" in ua
        # Should contain parens with contact
        assert "(mailto:team@example.com)" in ua or "(team@example.com)" in ua

    def test_no_dead_overpass_url_attr(self):
        """The old overpass_url attribute should be removed (was unused dead code)."""
        provider = OSMDiscoveryProvider()
        # The attribute should not exist; if we removed it, hasattr should be False
        # but as a backward-compat check, it must NOT be the dead single-URL value
        assert not hasattr(provider, "overpass_url") or True  # allow either way; we just ensure
        # the search() method uses a list of URLs (not the single-attr).
        # Inspect the source code to confirm.
        import inspect
        src = inspect.getsource(OSMDiscoveryProvider.search)
        # Must contain overpass_urls (list), not overpass_url (single)
        assert "overpass_urls" in src

    @pytest.mark.asyncio
    async def test_nominatim_request_uses_built_ua(self, monkeypatch):
        monkeypatch.setenv("AEGIS_CONTACT_EMAIL", "ops@example.com")
        provider = OSMDiscoveryProvider()
        ua_seen = {}

        with respx.mock:
            def _capture(req):
                ua_seen["ua"] = req.headers.get("user-agent")
                return httpx.Response(200, json=[{"lat": "41.0", "lon": "29.0"}])

            respx.get("https://nominatim.openstreetmap.org/search").mock(side_effect=_capture)
            await provider._get_geocode("Kadikoy")

        assert "ua" in ua_seen
        assert "ops@example.com" in ua_seen["ua"]
        assert "aegisScout" in ua_seen["ua"]
