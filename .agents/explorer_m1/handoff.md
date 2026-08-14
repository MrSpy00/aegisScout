# Handoff Report: Milestone M1 (Session & Anti-Blocking Resilience Infrastructure)

## 1. Observation
Direct codebase scan of `src/aegisScout/discovery/instagram_finder.py` (1,862 lines) and `src/aegisScout/core/config.py` (247 lines) revealed the following structural details:

1. **Unproxied `httpx.AsyncClient` Calls**:
   - `instagram_finder.py` instantiates `httpx.AsyncClient` directly across 25+ locations (e.g. lines 294, 342, 371, 438, 470, 500, 528, 556, 652, 757, 832, 848, 863, 1089, 1126, 1152, 1263, 1284, 1455, 1473, 1490, 1580, 1749, 1762, 1846).
   - Although line 228 sets `self.ig_proxy = getattr(settings, "instagram_proxy", None) or getattr(settings, "proxy_pool", None)`, this proxy is **not** passed into the `httpx.AsyncClient` calls across the fetching and search layers.

2. **Missing Guest Cookie Bootstrapping**:
   - Unauthenticated endpoints `/api/v1/users/web_profile_info/` (line 756) and `/web/search/topsearch/` (line 284) make HTTP requests without pre-harvested guest cookies (`mid`, `ig_did`, `csrftoken`), leading to instant HTTP 403/429 rate limiting by Instagram.

3. **Absence of Authenticated Session Storage**:
   - There is currently no module or class in `src/aegisScout` for loading, saving, or encrypting Instagram session cookies (`sessionid`, `ds_user_id`).
   - `src/aegisScout/utils/encryption.py` already exists with Fernet-backed `encrypt_json_file` and `decrypt_json_file` helpers, but it is not currently utilized for Instagram session persistence.

4. **Lack of Unified Retry & UA Rotation**:
   - HTTP requests are executed without unified backoff retries when receiving HTTP 429 (Too Many Requests) or HTTP 5xx errors.
   - User-Agents are selected randomly from a static inline array (`_USER_AGENTS`) without category management (desktop vs mobile app vs bots).

---

## 2. Logic Chain
1. **From Observation 1 (Unproxied clients)**: Centralizing all HTTP client creation into a single manager (`InstagramSessionManager.get_resilient_client()`) ensures `self.ig_proxy` is propagated to every outbound HTTP call across `InstagramFinder`.
2. **From Observation 2 (Missing guest cookies)**: Creating `InstagramSessionManager.get_guest_cookies()` that queries `https://www.instagram.com/` unauthenticated, extracts `mid`, `ig_did`, `csrftoken`, and caches them with a TTL ensures all unauthenticated REST/GraphQL requests include proper Instagram guest session cookies and `X-CSRFToken` headers.
3. **From Observation 3 (No session auth storage)**: Implementing `InstagramSessionManager.save_session()` and `load_session()` using `aegisScout.utils.encryption` provides secure, Fernet-encrypted session storage at `data/instagram_session.enc`, allowing `InstagramSessionManager.get_authenticated_session()` to supply an authenticated `httpx.AsyncClient` pre-loaded with `sessionid` and `ds_user_id` cookies.
4. **From Observation 4 (No unified retry/UA rotation)**: Adding `InstagramSessionManager.request_with_retry()` with exponential backoff (`backoff_factor ** attempt + random.uniform(0.1, 0.5)`), `Retry-After` header inspection, and User-Agent pool categorization guarantees global exception safety and anti-blocking resilience.

---

## 3. Caveats
- Instagram guest homepage HTML structure may vary; cookie extraction pairs HTTP Set-Cookie header parsing with regex extraction (`"csrf_token":"..."`) and synthetic token fallbacks so requests never fail due to missing cookie headers.
- Third-party libraries (`instaloader`, `instagrapi`) manage their own HTTP layers; proxy settings will be passed via library-specific methods (e.g., `cl.set_proxy(proxy)` for `instagrapi`).

---

## 4. Conclusion & Implementation Blueprint for Worker M1

Worker M1 must implement the following 3 files:

### File 1: Create `src/aegisScout/discovery/instagram_session.py`

#### Class Design: `InstagramSessionManager`
```python
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

USER_AGENTS = {
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

IG_APP_IDS = ["936619743392459", "1217981644879628", "195745249747", "124024574287414"]
DEFAULT_SESSION_FILE = Path("data/instagram_session.enc")


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
        self.proxy = (
            proxy
            or getattr(settings, "instagram_proxy", None)
            or getattr(settings, "proxy_pool", None)
        )
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
        agents = USER_AGENTS.get(category, USER_AGENTS["desktop"])
        return random.choice(agents)

    # --- Feature 1: Guest Cookie Bootstrapping ---
    async def get_guest_cookies(self, force_refresh: bool = False) -> Dict[str, str]:
        now = time.time()
        if not force_refresh and self._guest_cookies and (now - self._guest_cookies_updated_at < self.cookie_ttl):
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
        target_path = Path(storage_path) if storage_path else self.session_file
        session_data = {
            "sessionid": sessionid,
            "ds_user_id": ds_user_id or (sessionid.split("%")[0] if "%" in sessionid else ""),
            "custom_cookies": custom_cookies or {},
            "saved_at": time.time(),
        }
        encrypt_json_file(target_path, session_data)
        self._authenticated_session_data = session_data

    def load_session(self, storage_path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, str]]:
        if self._authenticated_session_data:
            return self._authenticated_session_data

        target_path = Path(storage_path) if storage_path else self.session_file
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

        return httpx.AsyncClient(
            proxy=proxy or self.proxy,
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
        proxy_to_use = proxy or self.proxy
        req_headers = {
            "User-Agent": self.get_random_user_agent("desktop"),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
            "Accept": "*/*",
        }
        if headers:
            req_headers.update(headers)

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
                        logger.warning(f"HTTP {response.status_code} on {url} (Attempt {attempt}/{max_retries}). Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                return response
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                if attempt < max_retries:
                    delay = (backoff_factor ** attempt) + random.uniform(0.1, 0.5)
                    logger.warning(f"Network error ({type(exc).__name__}) on {url} (Attempt {attempt}/{max_retries}). Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed request to {url} after {max_retries} attempts: {exc}")
                    return None
            except Exception as exc:
                logger.error(f"Unexpected exception during request to {url}: {exc}")
                return None
        return None
```

---

### File 2: Modify `src/aegisScout/discovery/instagram_finder.py`

1. Add import:
   ```python
   from aegisScout.discovery.instagram_session import InstagramSessionManager
   ```
2. Update `InstagramFinder.__init__`:
   ```python
   def __init__(self, session_manager: Optional[InstagramSessionManager] = None):
       # ... existing config assignments ...
       self.ig_proxy = getattr(settings, "instagram_proxy", None) or getattr(settings, "proxy_pool", None)
       self.session_manager = session_manager or InstagramSessionManager(proxy=self.ig_proxy)
   ```
3. Add helper contract method `_get_resilient_client`:
   ```python
   def _get_resilient_client(
       self,
       headers: Optional[Dict[str, str]] = None,
       proxy: Optional[str] = None,
       timeout: float = 10.0,
       follow_redirects: bool = True,
       use_guest_cookies: bool = True,
   ) -> httpx.AsyncClient:
       return self.session_manager.get_resilient_client(
           headers=headers,
           proxy=proxy or self.ig_proxy,
           timeout=timeout,
           follow_redirects=follow_redirects,
           use_guest_cookies=use_guest_cookies,
       )
   ```
4. Refactor all raw `httpx.AsyncClient(...)` blocks in `_instagram_topsearch`, `fetch_profile_details`, `fetch_anonymous_user_posts_and_stories`, `_fetch_via_meta_graph_api`, `_fetch_via_hikerapi`, `_fetch_via_apify`, search engine harvesters, etc. to use `self._get_resilient_client(...)` and `self.session_manager.request_with_retry(...)`.
5. Ensure `_instagram_topsearch` calls `await self.session_manager.get_guest_cookies()` before querying topsearch endpoints.

---

### File 3: Create `tests/test_discovery/test_instagram_session.py`

Implement unit tests verifying all 4 features:
1. `test_get_random_user_agent()`: verifies desktop, mobile_app, and bot categories return non-empty User-Agent strings.
2. `test_get_guest_cookies_bootstrapping()`: mocks `https://www.instagram.com/` response via `respx` and asserts returned dict contains `mid`, `ig_did`, and `csrftoken`.
3. `test_encrypted_session_save_and_load()`: saves session data to a temporary file via `tmp_path`, verifies disk content is Fernet-encrypted (not plaintext), and verifies `load_session()` returns the decrypted `sessionid` and `ds_user_id`.
4. `test_get_authenticated_session()`: verifies that when session is loaded, `get_authenticated_session()` returns an `httpx.AsyncClient` containing `sessionid` in its cookies.
5. `test_get_resilient_client_proxy_propagation()`: instantiates client with a custom proxy and verifies `client._transport` or proxy setting is configured.
6. `test_request_with_retry_backoff_on_429()`: mocks an endpoint returning HTTP 429 followed by HTTP 200, verifying retries succeed.
7. `test_request_with_retry_exception_safety()`: mocks an endpoint raising `httpx.ConnectTimeout`, verifying function handles exception safely without crashing and returns `None`.

---

## 5. Verification Method

To independently verify the implementation:

1. Execute the test suite:
   ```pwsh
   pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py -v
   ```
2. Invalidation conditions:
   - Any test failure in `test_instagram_session.py` or `test_instagram_finder.py`.
   - Any unhandled exception escaping `request_with_retry` or `InstagramFinder` methods.
   - Any raw `httpx.AsyncClient` instantiation in `instagram_finder.py` failing to propagate `self.ig_proxy`.
