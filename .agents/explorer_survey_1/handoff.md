# Handoff Report — Phase 0 Survey for Requirements R1 & R3 (Instagram Finder)

## Executive Summary
This survey provides a comprehensive investigation of **Requirements R1 (Anonymous Story & Profile Viewing Fixes)** and **R3 (Session & Anti-Blocking Resilience)** for the `aegisScout` Instagram Finder system (`src/aegisScout/discovery/instagram_finder.py`).

The investigation revealed that while `instagram_finder.py` contains a sophisticated 7-layer architecture and multiple fallback tiers, anonymous viewing and guest endpoints currently fail due to **Instagram guest API lockdowns**, **uninitialized guest session cookies**, **complete absence of proxy passing in `httpx` clients**, **unimplemented story/highlight fetching logic**, and **missing session authentication integration**.

---

## 1. Observation

### 1.1 Source Code Findings (`src/aegisScout/discovery/instagram_finder.py`)
1. **Unauthenticated Instagram Endpoints Fail Without Guest Cookies**:
   - `_instagram_topsearch()` (`instagram_finder.py:278-330`): Calls `https://www.instagram.com/web/search/topsearch/?context=blended&query=...` and `https://www.instagram.com/api/v1/users/search/?q=...`.
   - `fetch_profile_details()` Tier 0 (`instagram_finder.py:754-825`): Calls `https://www.instagram.com/api/v1/users/web_profile_info/?username=...`.
   - *Direct observation*: Requests are sent via fresh `httpx.AsyncClient` instances without first fetching or initializing Instagram guest session cookies (`mid`, `ig_did`, `csrftoken`). Instagram responds with HTTP 302 redirects to `https://www.instagram.com/accounts/login/`, HTTP 401 Unauthorized, or HTTP 429 Too Many Requests.

2. **Broken & Missing Story / Highlight Viewing Logic**:
   - `fetch_anonymous_user_posts_and_stories()` (`instagram_finder.py:1075-1194`):
     - Method 1 (`:1088-1117`) inspects the public `/embed/` HTML endpoint and checks if `"story" in html.lower()`.
     - Method 2 (`:1120-1146`) scrapes Picuki (`picuki.com`).
     - Method 3 (`:1148-1172`) scrapes Imginn (`imginn.com`).
   - *Direct observation*: The `/embed/` endpoint HTML does not serve story or highlight media items. In all code paths, `story_urls` is hardcoded to return an empty list `[]` (`:1193`). There is zero logic to fetch Instagram highlight trays (`highlights_tray`), highlight items, or story video/photo URLs.

3. **Proxy Pool Configured but Ignored in `httpx` Clients**:
   - `__init__()` (`instagram_finder.py:228-229`):
     ```python
     self.ig_proxy = getattr(settings, "instagram_proxy", None) or getattr(settings, "proxy_pool", None)
     ```
   - *Direct observation*: `self.ig_proxy` is passed ONLY to `instagrapi` in `_fetch_via_instagrapi_guest` (`:583-585`). All 10+ `httpx.AsyncClient` instances throughout `instagram_finder.py` (topsearch, profile details, web mirrors, search engines, autocomplete) instantiate `httpx.AsyncClient` WITHOUT passing `proxy=self.ig_proxy` or `mounts`. All anonymous traffic routes directly through the local host IP address, triggering rapid rate-limiting.

4. **Unused Session Credentials & Cookie Authentication**:
   - `config.py` (`src/aegisScout/core/config.py:69-72` & `:178-208`): Defines `instagram_username`, `instagram_password`, `instagram_session_encryption_key`, and `get_encryption_key()`.
   - `__init__()` (`instagram_finder.py:227`): Reads `self.ig_login_token = getattr(settings, "instagram_login_access_token", None)`.
   - *Direct observation*: `self.ig_login_token` is never referenced anywhere else in `instagram_finder.py`. There is no session cookie storage, cookie loading, Fernet session state encryption/decryption, or session-authenticated GraphQL/REST client in `instagram_finder.py`.

5. **Lack of Rate Limiting & Retry Throttling**:
   - `_search_by_username_direct()` (`:1338-1344`) and `search_profiles_by_sector()` (`:1528-1533`):
     ```python
     sem = asyncio.Semaphore(40)
     ```
   - *Direct observation*: Concurrency is capped at 40 requests, but there is no token bucket rate limiter, exponential backoff, retry handler for 429/503 status codes, or random jitter between requests.

6. **Web Mirrors Vulnerable to Cloudflare & Domain Shifts**:
   - `_fetch_via_web_mirrors()` (`:642-678`): Scrapes `Greatfon`, `AnonIGViewer`, `Instanavigation`, `Dumpor`.
   - *Direct observation*: Performs a single HTTP GET per mirror using basic headers. When mirrors present Cloudflare Turnstile/DDoS-Guard challenges or change URL paths, GET requests fail silently (`except Exception: pass`) without failover reporting or fallback parsing.

---

## 2. Logic Chain

1. **Why direct guest profile and topsearch endpoints fail**:
   - *Observation*: `_instagram_topsearch()` and `fetch_profile_details()` make unauthenticated GET requests to IG's `/api/v1/users/web_profile_info/` and `/web/search/topsearch/` without `Cookie` headers containing `mid`, `ig_did`, or `csrftoken`.
   - *Reasoning*: Modern Instagram web endpoints enforce guest session initialization. When `httpx` sends requests without guest session cookies or CSRF headers, Instagram's API gateway rejects the request with HTTP 401 or redirects to `/accounts/login/`.
   - *Conclusion*: A guest session cookie manager must be introduced to perform an initial cookie-bootstrap GET (to `https://www.instagram.com/`) to collect `mid`, `ig_did`, `csrftoken` cookies before querying IG REST/GraphQL endpoints.

2. **Why story and highlight viewing is broken**:
   - *Observation*: `fetch_anonymous_user_posts_and_stories()` checks for `"story"` in `/embed/` HTML and returns `story_urls: []`.
   - *Reasoning*: `/embed/` is an iframe snippet meant for post embeds. Instagram does not expose story media in embed HTML. Since no direct story/highlight reel API call (or web mirror story scraper) is executed, story media links are never populated.
   - *Conclusion*: Real story and highlight viewing requires integrating either authenticated reel endpoints (`/api/v1/feed/reels_media/`, `/api/v1/highlights/{user_id}/highlights_tray/`) OR public story mirror web scrapers (e.g. InstaNavigation, SaveInsta, FastDl) when unauthenticated.

3. **Why IP rate-limiting and blocking occur quickly**:
   - *Observation*: `self.ig_proxy` is defined in `__init__` but not supplied to `httpx.AsyncClient`. Semaphore limit is 40.
   - *Reasoning*: All 40 concurrent HTTP requests originate from the same unproxied IP address without request delays. Instagram and search engines detect high-frequency automated scraping from single IPs and issue HTTP 429 rate limit blocks.
   - *Conclusion*: Every `httpx.AsyncClient` instantiation must be wrapped in a centralized HTTP client helper that respects `self.ig_proxy`, enforces rate-limiting delays with jitter, rotates User-Agents, and retries on 429/5xx status codes.

4. **Why session cookie fallback is missing**:
   - *Observation*: `config.py` contains Fernet encryption helpers and IG credentials, but `instagram_finder.py` only implements guest/unauthenticated logic.
   - *Reasoning*: The codebase lacks a session authentication manager to persist `sessionid` cookies, decrypt saved sessions using `settings.get_encryption_key()`, and attach `sessionid` headers to IG requests.
   - *Conclusion*: Adding a dual-mode engine (Authenticated Session Mode with fallback to Anonymous Guest / Web Mirror Mode) will fulfill R3 requirements.

---

## 3. Caveats
- **Instagram API Stability**: Instagram frequently updates its front-end JavaScript bundles, GraphQL query hashes (`doc_id`), and internal headers. Web mirror structures can also change without notice.
- **Mod-B Safety Acknowledgment**: Per `config.py`, full Instagram automation operating in Mod-B must respect the `mod_b_acknowledged` flag and default to dry-run when configured.
- **Proxy Availability**: If no `proxy_pool` or `instagram_proxy` is specified in `.env`, the system relies entirely on public web mirror fallbacks and guest session throttling.

---

## 4. Conclusion & Recommendations

### 4.1 Summary of Findings
- **R1 Anonymous Profile Fetching**: Direct IG guest endpoints fail due to missing guest cookies (`mid`/`ig_did`/`csrftoken`). Profile fetching currently relies heavily on secondary tiers (Googlebot OpenGraph, embed, SaaS APIs, mirrors).
- **R1 Anonymous Story & Highlight Viewing**: Completely broken / missing. `story_urls` returns empty lists `[]`, and highlight tray extraction is not implemented.
- **R3 Session Cookie Authentication**: Missing from `instagram_finder.py`. Credentials in `.env` are unused.
- **R3 Anti-Blocking Resilience**: `self.ig_proxy` is omitted from `httpx` calls. Request retries, backoff throttling, UA consistency, and proxy pool integration are absent.

### 4.2 Architectural Recommendations for Implementation Phase
1. **Guest & Session Cookie Manager**:
   - Implement `InstagramSessionManager` in `instagram_finder.py` or a dedicated helper module (`instagram_session.py`).
   - Support both **Session Cookie Mode** (authenticated via `sessionid`, `ds_user_id`, `csrftoken` stored in encrypted `data/sessions/ig_session.enc` via Fernet) and **Guest Cookie Mode** (auto-bootstrapping `mid` and `csrftoken` from `https://www.instagram.com/`).

2. **Centralized Resilient HTTP Client**:
   - Create an async helper `_get_resilient_client(headers, proxy, timeout)` that configures `httpx.AsyncClient` with:
     - Configured HTTP/HTTPS proxy (`self.ig_proxy`).
     - Automated retries (3 attempts) with exponential backoff and random jitter for HTTP 429, 502, 503, 504, and network timeouts.
     - Rotating headers & consistent User-Agent matching (Sec-CH-UA platform consistency).

3. **Public Web Mirror Fallback Engine**:
   - Build a structured adapter pattern for public story & profile mirrors:
     - `InstaNavigationAdapter` (Profile, Stories, Highlights)
     - `ImginnAdapter` (Profile, Posts, Gallery)
     - `PicukiAdapter` (Profile, Posts)
     - `DumporAdapter` (Profile, Stories)
   - Implement a fallback pipeline: Direct IG API (Session/Guest) → Public Web Mirrors → Web Search Scrapers.

4. **Story & Highlight Extraction Pipeline**:
   - Implement `fetch_anonymous_user_posts_and_stories` and `fetch_user_highlights` to return structured media objects:
     - `stories`: list of `{id, media_url, media_type, timestamp, thumbnail}`
     - `highlights`: list of `{highlight_id, title, cover_url, items: [...]}`

---

## 5. Verification Method

To verify the findings and test future implementations:

1. **Run Unit Tests**:
   ```powershell
   pytest tests/test_discovery/test_instagram_finder.py -v
   ```
2. **Inspect File Locations**:
   - `src/aegisScout/discovery/instagram_finder.py`
   - `src/aegisScout/core/config.py`
   - `tests/test_discovery/test_instagram_finder.py`
3. **Invalidation Conditions**:
   - If unauthenticated `web_profile_info` GET requests succeed without guest session cookies, or if `/embed/` returns story media items, the failure mechanism assumptions are invalidated.
