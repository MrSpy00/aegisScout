"""
Unit tests for InstagramSessionManager (Milestone M1).
"""
from pathlib import Path
import pytest
import respx
import httpx
from unittest.mock import patch

from aegisScout.discovery.instagram_session import (
    InstagramSessionManager,
    USER_AGENTS,
    DEFAULT_SESSION_FILE,
)


class TestInstagramSessionManager:
    """Comprehensive test suite for InstagramSessionManager."""

    def test_get_random_user_agent(self):
        """Verify user agent rotation for all supported categories."""
        manager = InstagramSessionManager()
        for cat in ["desktop", "mobile_app", "bot"]:
            ua = manager.get_random_user_agent(cat)
            assert isinstance(ua, str)
            assert len(ua) > 10
            assert ua in USER_AGENTS[cat]

        # Fallback to desktop for unknown categories
        unknown_ua = manager.get_random_user_agent("unknown_category")
        assert unknown_ua in USER_AGENTS["desktop"]

    @pytest.mark.asyncio
    async def test_get_guest_cookies_bootstrapping(self):
        """Verify guest cookie harvesting from Instagram home page HTML/headers."""
        manager = InstagramSessionManager()

        with respx.mock:
            respx.get("https://www.instagram.com/").mock(
                return_value=httpx.Response(
                    200,
                    text='<html><head><script>var x = {"csrf_token":"extracted_csrf_123"};</script></head></html>',
                    headers={"set-cookie": "mid=Y12345A678; Path=/"},
                )
            )
            cookies = await manager.get_guest_cookies(force_refresh=True)

        assert "mid" in cookies
        assert "ig_did" in cookies
        assert "csrftoken" in cookies
        assert cookies["csrftoken"] == "extracted_csrf_123"

    @pytest.mark.asyncio
    async def test_get_guest_cookies_fallback_on_error(self):
        """Verify fallback synthetic cookies are generated when network request fails."""
        manager = InstagramSessionManager()

        with respx.mock:
            respx.get("https://www.instagram.com/").mock(
                side_effect=httpx.ConnectTimeout("Connection timed out")
            )
            cookies = await manager.get_guest_cookies(force_refresh=True)

        assert "mid" in cookies
        assert "ig_did" in cookies
        assert "csrftoken" in cookies
        assert len(cookies["mid"]) > 0
        assert len(cookies["ig_did"]) > 0
        assert len(cookies["csrftoken"]) > 0

    def test_encrypted_session_save_and_load(self, tmp_path):
        """Verify session credentials are saved as Fernet-encrypted JSON and load properly."""
        session_file = tmp_path / "test_session.enc"
        manager = InstagramSessionManager(session_file=session_file)

        # Save session
        manager.save_session(
            sessionid="12345%3Aabcde",
            ds_user_id="12345",
            custom_cookies={"test_cookie": "value123"},
        )

        assert session_file.exists()
        raw_content = session_file.read_bytes()
        # Verify file on disk is NOT plaintext JSON
        assert b"sessionid" not in raw_content
        assert b"12345%3Aabcde" not in raw_content

        # Create new manager instance pointing to same file and load
        loaded_manager = InstagramSessionManager(session_file=session_file)
        session_data = loaded_manager.load_session()

        assert session_data is not None
        assert session_data["sessionid"] == "12345%3Aabcde"
        assert session_data["ds_user_id"] == "12345"
        assert session_data["custom_cookies"] == {"test_cookie": "value123"}

    def test_get_authenticated_session(self, tmp_path):
        """Verify get_authenticated_session returns an httpx.AsyncClient with cookies loaded."""
        session_file = tmp_path / "auth_session.enc"
        manager = InstagramSessionManager(session_file=session_file)

        # Before saving session, should return None
        assert manager.get_authenticated_session() is None

        # Save session
        manager.save_session(sessionid="session_val_xyz", ds_user_id="99999")

        client = manager.get_authenticated_session()
        assert isinstance(client, httpx.AsyncClient)
        assert client.cookies.get("sessionid") == "session_val_xyz"
        assert client.cookies.get("ds_user_id") == "99999"

    def test_get_resilient_client_proxy_propagation(self):
        """Verify proxy is properly propagated to resilient client."""
        custom_proxy = "http://proxy.example.com:8080"
        manager = InstagramSessionManager(proxy=custom_proxy)

        client = manager.get_resilient_client()
        assert isinstance(client, httpx.AsyncClient)
        # Verify User-Agent header is set
        assert "User-Agent" in client.headers

    @pytest.mark.asyncio
    async def test_request_with_retry_backoff_on_429(self):
        """Verify request_with_retry retries on HTTP 429 rate limit."""
        manager = InstagramSessionManager()
        client = manager.get_resilient_client()

        with respx.mock:
            route = respx.get("https://api.instagram.com/test_endpoint")
            route.side_effect = [
                httpx.Response(429, headers={"Retry-After": "1"}),
                httpx.Response(200, json={"status": "ok"}),
            ]
            with patch("asyncio.sleep", return_value=None) as mock_sleep:
                resp = await manager.request_with_retry(
                    client, "GET", "https://api.instagram.com/test_endpoint", max_retries=3
                )
                assert mock_sleep.called
                assert resp is not None
                assert resp.status_code == 200
                assert resp.json() == {"status": "ok"}
                assert route.call_count == 2

    @pytest.mark.asyncio
    async def test_request_with_retry_exception_safety(self):
        """Verify network exceptions are caught safely and return None without raising."""
        manager = InstagramSessionManager()
        client = manager.get_resilient_client()

        with respx.mock:
            respx.get("https://api.instagram.com/failing_endpoint").mock(
                side_effect=httpx.ConnectTimeout("Timeout connecting to server")
            )
            with patch("asyncio.sleep", return_value=None):
                resp = await manager.request_with_retry(
                    client, "GET", "https://api.instagram.com/failing_endpoint", max_retries=2
                )

        assert resp is None
