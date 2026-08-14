"""
Empirical Stress Test Harness for Milestone M1 (Session & Anti-Blocking Resilience Infrastructure).
Executed by Challenger 1 M1.
"""
import asyncio
import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import respx
import httpx

from aegisScout.discovery.instagram_session import InstagramSessionManager
from aegisScout.discovery.instagram_finder import InstagramFinder
from aegisScout.core.config import settings


class TestM1ResilienceStress:
    """Adversarial stress-test suite covering the 5 key failure dimensions."""

    # -----------------------------------------------------------------------
    # Dimension 1: Network Timeouts Resilience
    # -----------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_stress_network_timeouts_get_guest_cookies(self):
        """Test guest cookie bootstrapping under ReadTimeout, ConnectTimeout, and PoolTimeout."""
        manager = InstagramSessionManager()

        for timeout_exc in [
            httpx.ConnectTimeout("Connect timeout"),
            httpx.ReadTimeout("Read timeout"),
            httpx.WriteTimeout("Write timeout"),
            httpx.PoolTimeout("Pool timeout"),
        ]:
            with respx.mock:
                respx.get("https://www.instagram.com/").mock(side_effect=timeout_exc)
                cookies = await manager.get_guest_cookies(force_refresh=True)

                assert isinstance(cookies, dict)
                assert "mid" in cookies and len(cookies["mid"]) > 0
                assert "ig_did" in cookies and len(cookies["ig_did"]) > 0
                assert "csrftoken" in cookies and len(cookies["csrftoken"]) > 0

    @pytest.mark.asyncio
    async def test_stress_network_timeouts_request_with_retry(self):
        """Test request_with_retry under repeated network timeouts exceeding max_retries."""
        manager = InstagramSessionManager()
        client = manager.get_resilient_client()

        with respx.mock:
            respx.get("https://api.instagram.com/timeout").mock(
                side_effect=httpx.ReadTimeout("Read timeout occurred")
            )
            with patch("asyncio.sleep", return_value=None) as mock_sleep:
                resp = await manager.request_with_retry(
                    client, "GET", "https://api.instagram.com/timeout", max_retries=3
                )
                assert resp is None
                assert mock_sleep.call_count == 2

    # -----------------------------------------------------------------------
    # Dimension 2: HTTP 429 Rate-Limiting Spikes & Headers
    # -----------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_stress_http_429_numeric_retry_after(self):
        """Test 429 handling with valid integer Retry-After header."""
        manager = InstagramSessionManager()
        client = manager.get_resilient_client()

        with respx.mock:
            route = respx.get("https://api.instagram.com/rate_limit")
            route.side_effect = [
                httpx.Response(429, headers={"Retry-After": "5"}),
                httpx.Response(200, json={"status": "ok"}),
            ]
            sleep_delays = []
            async def mock_sleep_fn(delay):
                sleep_delays.append(delay)

            with patch("asyncio.sleep", side_effect=mock_sleep_fn):
                resp = await manager.request_with_retry(
                    client, "GET", "https://api.instagram.com/rate_limit", max_retries=3
                )
                assert resp is not None
                assert resp.status_code == 200
                assert len(sleep_delays) == 1
                assert sleep_delays[0] == 5.0

    @pytest.mark.asyncio
    async def test_stress_http_429_invalid_retry_after(self):
        """Test 429 handling with non-digit / malformed Retry-After header (e.g. HTTP date or text)."""
        manager = InstagramSessionManager()
        client = manager.get_resilient_client()

        for invalid_header in [
            "Wed, 21 Oct 2026 07:28:00 GMT",
            "Too Many Requests",
            "invalid_number",
            "-10",
            "3.14",
        ]:
            with respx.mock:
                route = respx.get("https://api.instagram.com/rate_limit_bad")
                route.side_effect = [
                    httpx.Response(429, headers={"Retry-After": invalid_header}),
                    httpx.Response(200, json={"status": "ok"}),
                ]
                sleep_delays = []
                async def mock_sleep_fn(delay):
                    sleep_delays.append(delay)

                with patch("asyncio.sleep", side_effect=mock_sleep_fn):
                    resp = await manager.request_with_retry(
                        client, "GET", "https://api.instagram.com/rate_limit_bad", max_retries=3
                    )
                    assert resp is not None
                    assert resp.status_code == 200
                    assert len(sleep_delays) == 1
                    # Should fallback to backoff calculation, not crash or raise ValueError
                    assert sleep_delays[0] > 0

    @pytest.mark.asyncio
    async def test_stress_http_429_persistent_exhaustion(self):
        """Test 429 rate limit spike that exhausts all retries."""
        manager = InstagramSessionManager()
        client = manager.get_resilient_client()

        with respx.mock:
            respx.get("https://api.instagram.com/rate_limit_persistent").mock(
                return_value=httpx.Response(429, text="Rate limit exceeded")
            )
            with patch("asyncio.sleep", return_value=None):
                resp = await manager.request_with_retry(
                    client, "GET", "https://api.instagram.com/rate_limit_persistent", max_retries=3
                )
                assert resp is not None
                assert resp.status_code == 429

    # -----------------------------------------------------------------------
    # Dimension 3: Corrupt Encrypted Session Files
    # -----------------------------------------------------------------------
    def test_stress_corrupt_session_file_random_bytes(self, tmp_path):
        """Test load_session when session file contains random corrupted binary data."""
        session_file = tmp_path / "corrupt_session.enc"
        session_file.write_bytes(os.urandom(256))

        manager = InstagramSessionManager(session_file=session_file)

        # Clear env vars if present
        with patch.dict(os.environ, {}, clear=True):
            session_data = manager.load_session()
            assert session_data is None

        # Should not crash get_authenticated_session
        assert manager.get_authenticated_session() is None

    def test_stress_corrupt_session_file_empty(self, tmp_path):
        """Test load_session when session file is empty (0 bytes)."""
        session_file = tmp_path / "empty_session.enc"
        session_file.write_bytes(b"")

        manager = InstagramSessionManager(session_file=session_file)
        with patch.dict(os.environ, {}, clear=True):
            session_data = manager.load_session()
            assert session_data is None

    def test_stress_corrupt_session_file_invalid_json(self, tmp_path):
        """Test load_session when session file decrypts to invalid JSON or missing required fields."""
        session_file = tmp_path / "bad_json.enc"
        # Save valid key structure but corrupted inner contents
        from aegisScout.utils.encryption import encrypt_bytes
        encrypted = encrypt_bytes(b"{this is not json}")
        session_file.write_bytes(encrypted)

        manager = InstagramSessionManager(session_file=session_file)
        with patch.dict(os.environ, {}, clear=True):
            session_data = manager.load_session()
            assert session_data is None

    def test_stress_corrupt_session_file_with_env_fallback(self, tmp_path):
        """Test corrupted session file gracefully falls back to INSTAGRAM_SESSIONID env var."""
        session_file = tmp_path / "corrupt.enc"
        session_file.write_bytes(b"invalid corrupt token data")

        manager = InstagramSessionManager(session_file=session_file)
        with patch.dict(os.environ, {"INSTAGRAM_SESSIONID": "env_session_999", "INSTAGRAM_DS_USER_ID": "888"}):
            session_data = manager.load_session()
            assert session_data is not None
            assert session_data["sessionid"] == "env_session_999"
            assert session_data["ds_user_id"] == "888"

    # -----------------------------------------------------------------------
    # Dimension 4: Missing & Invalid Proxy Parameters
    # -----------------------------------------------------------------------
    def test_stress_missing_and_invalid_proxy_types(self):
        """Test InstagramSessionManager instantiation with various invalid proxy inputs."""
        invalid_proxies = [
            None,
            "",
            "   ",
            12345,
            ["http://proxy.org:8080"],
            {"proxy": "http://proxy.org:8080"},
            MagicMock(name="proxy_mock"),
        ]

        for p in invalid_proxies:
            manager = InstagramSessionManager(proxy=p)
            assert manager.proxy is None, f"Expected None for proxy input {p!r}, got {manager.proxy!r}"
            client = manager.get_resilient_client()
            assert isinstance(client, httpx.AsyncClient)

    def test_stress_resilient_client_proxy_override(self):
        """Test get_resilient_client with invalid proxy override types."""
        manager = InstagramSessionManager(proxy="http://valid-proxy.com:8080")

        # Invalid overrides should fall back to self.proxy
        for invalid_override in [None, "", "   ", 12345, MagicMock()]:
            client = manager.get_resilient_client(proxy=invalid_override)
            assert isinstance(client, httpx.AsyncClient)

    # -----------------------------------------------------------------------
    # Dimension 5: Invalid Cookie Headers & Malformed Header Inputs
    # -----------------------------------------------------------------------
    def test_stress_invalid_headers_dict_handling(self):
        """Test get_resilient_client handles invalid header dict values without crashing."""
        mock_val = MagicMock()
        headers = {
            "User-Agent": "CustomUA/1.0",
            "X-Custom-Header": 12345,
            "X-Mock-Header": mock_val,
            "X-None-Header": None,
        }
        manager = InstagramSessionManager()
        client = manager.get_resilient_client(headers=headers)

        assert isinstance(client, httpx.AsyncClient)
        assert client.headers["User-Agent"] == "CustomUA/1.0"
        assert client.headers["X-Custom-Header"] == "12345"
        assert "X-None-Header" not in client.headers
        assert "X-Mock-Header" not in client.headers

    def test_stress_custom_cookies_in_save_load_session(self, tmp_path):
        """Test save_session and load_session with custom cookies."""
        session_file = tmp_path / "custom_cookies.enc"
        manager = InstagramSessionManager(session_file=session_file)

        manager.save_session(
            sessionid="valid_sess_id",
            ds_user_id="12345",
            custom_cookies={"csrftoken": "tok123", "rur": "PRN"},
        )

        loaded = manager.load_session()
        assert loaded is not None
        assert loaded["custom_cookies"] == {"csrftoken": "tok123", "rur": "PRN"}

        client = manager.get_authenticated_session()
        assert client is not None
        assert client.cookies.get("csrftoken") == "tok123"
        assert client.cookies.get("rur") == "PRN"

    # -----------------------------------------------------------------------
    # Integration & Concurrency Stress
    # -----------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_stress_concurrent_guest_cookie_bootstrapping(self):
        """Test 20 concurrent tasks requesting guest cookies simultaneously under network failure."""
        manager = InstagramSessionManager()

        with respx.mock:
            respx.get("https://www.instagram.com/").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            tasks = [manager.get_guest_cookies(force_refresh=True) for _ in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            assert len(results) == 20
            for r in results:
                assert isinstance(r, dict)
                assert "mid" in r and "ig_did" in r and "csrftoken" in r

    @pytest.mark.asyncio
    async def test_stress_none_response_safety(self):
        """
        Verify that InstagramFinder methods handle None responses from request_with_retry
        safely without unhandled AttributeError exceptions.
        """
        finder = InstagramFinder()

        # Mock request_with_retry to return None (simulating network error/timeout failure)
        with patch.object(finder.session_manager, "request_with_retry", return_value=None):
            # All operations should return gracefully (empty results, None, or empty list) without crashing
            auto = await finder._harvest_google_autocomplete_suggestions("test_query", "istanbul")
            assert isinstance(auto, (set, list, dict))

            bing = await finder._search_bing_instagram("test_query", "istanbul")
            assert bing is None or isinstance(bing, str)

            apify = await finder._fetch_via_apify("test_user")
            assert apify is None or isinstance(apify, dict)
