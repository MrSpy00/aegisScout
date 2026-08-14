"""
Instagram Session & Anti-Blocking Resilience Infrastructure.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import secrets
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx

from aegisScout.core.config import settings
from aegisScout.utils.encryption import decrypt_json_file, encrypt_json_file
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.instagram_session")

USER_AGENTS: Dict[str, List[str]] = {
    "desktop": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    ],
    "mobile_app": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 334.0.0.23.111",
        "Instagram 295.0.0.32.119 Android (31/12; 420dpi; 1080x2190; Google/Google; Pixel 5; redfin; google; en_TR; 508052647)",
    ],
    "bot": [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    ],
}

IG_APP_IDS: List[str] = [
    "936619743392459",
    "1217981644879628",
    "195745249747",
    "124024574287414",
]
DEFAULT_SESSION_FILE: Path = Path("data/instagram_session.enc")


class InstagramSessionManager:
    """
    Manages Instagram guest cookies, encrypted session authentication,
    resilient proxies, and HTTP clients.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        session_file: Optional[Union[str, Path]] = None,
        cookie_ttl: int = 3600,
    ):
        raw_proxy = (
            proxy
            or getattr(settings, "instagram_proxy", None)
            or getattr(settings, "proxy_pool", None)
        )
        if isinstance(raw_proxy, str) and raw_proxy.strip():
            self.proxy: Optional[str] = raw_proxy.strip()
        else:
            self.proxy = None

        self.session_file = Path(session_file) if session_file else DEFAULT_SESSION_FILE
        self.cookie_ttl = cookie_ttl

        self._guest_cookies: Dict[str, str] = {}
        self._guest_cookies_updated_at: float = 0.0
        self._authenticated_session_data: Optional[Dict[str, str]] = None
        self._limits = httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=10.0,
        )

    def get_random_user_agent(self, category: str = "desktop") -> str:
        """Return a random User-Agent string for the specified category."""
        agents = USER_AGENTS.get(category, USER_AGENTS["desktop"])
        return random.choice(agents)

    # --- Feature 1: Guest Cookie Bootstrapping ---
    async def get_guest_cookies(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Fetch or return cached guest cookies (mid, ig_did, csrftoken).
        Guaranteed to return non-empty cookies even if network fails.
        """
        now = time.time()
        if (
            not force_refresh
            and self._guest_cookies
            and (now - self._guest_cookies_updated_at < self.cookie_ttl)
        ):
            return self._guest_cookies

        cookies: Dict[str, str] = {}
        try:
            headers = {
                "User-Agent": self.get_random_user_agent("desktop"),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            }
            async with httpx.AsyncClient(
                proxy=self.proxy,
                timeout=8.0,
                follow_redirects=True,
                limits=self._limits,
                headers=headers,
            ) as client:
                resp = await client.get("https://www.instagram.com/")
                for k, v in resp.cookies.items():
                    cookies[k] = v

                mid = cookies.get("mid")
                ig_did = cookies.get("ig_did")
                csrftoken = cookies.get("csrftoken")

                if not csrftoken and resp.status_code == 200:
                    match = re.search(r'"csrf_token":"([^"]+)"', resp.text)
                    if match:
                        csrftoken = match.group(1)

                if not mid:
                    mid = f"Y{random.randint(100000, 999999)}A{random.randint(100, 999)}"
                if not ig_did:
                    ig_did = str(uuid.uuid4()).upper()
                if not csrftoken:
                    csrftoken = secrets.token_hex(16)

                cookies["mid"] = mid
                cookies["ig_did"] = ig_did
                cookies["csrftoken"] = csrftoken

                self._guest_cookies = cookies
                self._guest_cookies_updated_at = time.time()
        except Exception as e:
            logger.warning(f"Guest cookie bootstrapping notice: {e}")
            if not self._guest_cookies:
                self._guest_cookies = {
                    "mid": f"Y{random.randint(100000, 999999)}A{random.randint(100, 999)}",
                    "ig_did": str(uuid.uuid4()).upper(),
                    "csrftoken": secrets.token_hex(16),
                }
                self._guest_cookies_updated_at = time.time()

        return self._guest_cookies

    # --- Feature 2: Encrypted Session Cookie Auth ---
    def save_session(
        self,
        sessionid: str,
        ds_user_id: Optional[str] = None,
        custom_cookies: Optional[Dict[str, str]] = None,
        storage_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Encrypt and save session credentials (sessionid, ds_user_id) to disk.
        """
        target_path = Path(storage_path) if storage_path else self.session_file
        session_data = {
            "sessionid": sessionid,
            "ds_user_id": ds_user_id or (sessionid.split("%")[0] if "%" in sessionid else ""),
            "custom_cookies": custom_cookies or {},
            "saved_at": time.time(),
        }
        encrypt_json_file(target_path, session_data)
        self._authenticated_session_data = session_data

    def load_session(
        self, storage_path: Optional[Union[str, Path]] = None
    ) -> Optional[Dict[str, str]]:
        """
        Load and decrypt session credentials from disk or environment settings.
        """
        target_path = Path(storage_path) if storage_path else self.session_file

        if storage_path is None and self._authenticated_session_data:
            return self._authenticated_session_data

        session_data = None
        if target_path.exists():
            try:
                session_data = decrypt_json_file(target_path)
            except Exception as e:
                logger.warning(f"Failed to decrypt session file at {target_path}: {e}")

        if not session_data or not session_data.get("sessionid"):
            env_sessionid = getattr(settings, "instagram_sessionid", None) or os.environ.get("INSTAGRAM_SESSIONID")
            env_ds_user_id = getattr(settings, "instagram_ds_user_id", None) or os.environ.get("INSTAGRAM_DS_USER_ID")
            if env_sessionid:
                session_data = {
                    "sessionid": env_sessionid,
                    "ds_user_id": env_ds_user_id or "",
                    "saved_at": time.time(),
                }

        if session_data and session_data.get("sessionid"):
            self._authenticated_session_data = session_data
            return session_data

        return None

    def get_authenticated_session(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
    ) -> Optional[httpx.AsyncClient]:
        """
        Return an authenticated httpx.AsyncClient pre-loaded with session cookies,
        or None if no session credentials exist.
        """
        session_data = self.load_session()
        if not session_data or not session_data.get("sessionid"):
            return None

        req_headers = {
            "User-Agent": self.get_random_user_agent("desktop"),
            "X-IG-App-ID": random.choice(IG_APP_IDS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        }
        if headers:
            req_headers.update(headers)

        cookies = {"sessionid": session_data["sessionid"]}
        if session_data.get("ds_user_id"):
            cookies["ds_user_id"] = session_data["ds_user_id"]
        if session_data.get("custom_cookies"):
            cookies.update(session_data["custom_cookies"])

        proxy_to_use = proxy if (isinstance(proxy, str) and proxy.strip()) else self.proxy
        return httpx.AsyncClient(
            proxy=proxy_to_use,
            headers=req_headers,
            cookies=cookies,
            timeout=10.0,
            follow_redirects=True,
            limits=self._limits,
        )

    # --- Feature 3: Resilient Proxy & Client Manager ---
    def get_resilient_client(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: float = 10.0,
        follow_redirects: bool = True,
        use_guest_cookies: bool = True,
    ) -> httpx.AsyncClient:
        """
        Return a pre-configured AsyncClient with proxy, rotated UA, and guest cookies.
        """
        proxy_to_use = proxy if (isinstance(proxy, str) and proxy.strip()) else self.proxy
        req_headers = {
            "User-Agent": self.get_random_user_agent("desktop"),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
            "Accept": "*/*",
        }
        if headers:
            for k, v in headers.items():
                if isinstance(v, (str, bytes)):
                    req_headers[k] = v
                elif v is not None and not hasattr(v, "_mock_name"):
                    req_headers[k] = str(v)

        cookies = {}
        if use_guest_cookies and self._guest_cookies:
            cookies.update(self._guest_cookies)
            if "csrftoken" in cookies and "X-CSRFToken" not in req_headers:
                req_headers["X-CSRFToken"] = cookies["csrftoken"]

        return httpx.AsyncClient(
            proxy=proxy_to_use,
            headers=req_headers,
            cookies=cookies if cookies else None,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=self._limits,
        )

    # --- Feature 4: Global Retries & Exponential Backoff ---
    async def request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """
        Execute an HTTP request using `client` with automatic retries on
        429 (rate limited) and 5xx errors, handling Retry-After header and
        network exceptions safely.
        """
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.request(method, url, **kwargs)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < max_retries:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            delay = float(retry_after)
                        else:
                            delay = (backoff_factor ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning(
                            f"HTTP {response.status_code} on {url} (Attempt {attempt}/{max_retries}). "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                return response
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                if attempt < max_retries:
                    delay = (backoff_factor ** attempt) + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"Network error ({type(exc).__name__}) on {url} (Attempt {attempt}/{max_retries}). "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed request to {url} after {max_retries} attempts: {exc}")
                    return None
            except Exception as exc:
                logger.error(f"Unexpected exception during request to {url}: {exc}")
                return None
        return None
