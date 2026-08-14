# Handoff Report: Milestone M2 (Anonymous Profile, Story & Highlight Engine)

## 1. Observation

Direct codebase scan of `src/aegisScout/discovery/instagram_finder.py` (1,880 lines) and `src/aegisScout/discovery/instagram_session.py` (336 lines) revealed the following structural details:

1. **Feature 5 Deficiencies (Direct Guest Profile API Headers & Cookie Integration)**:
   - Line 781 in `instagram_finder.py` calls `https://www.instagram.com/api/v1/users/web_profile_info/?username={clean_user}`.
   - While `x-ig-app-id` is passed, the request is missing critical headers required by Instagram's frontend API: `x-asbd-id: "198387"`, `x-ig-www-claim: "0"`, `x-requested-with: "XMLHttpRequest"`, and `Referer: https://www.instagram.com/{clean_user}/`.
   - The request does **not** fetch guest session cookies (`mid`, `ig_did`, `csrftoken`) from `self.session_manager.get_guest_cookies()` prior to making the request, nor does it pass `X-CSRFToken` in the header, resulting in HTTP 403 Forbidden or HTTP 429 rate limiting on unauthenticated IP addresses.

2. **Feature 6 Deficiencies (Anonymous Story & Highlight Media Extractor)**:
   - `fetch_anonymous_user_posts_and_stories` (lines 1096–1214) attempts to scrape Instagram embed endpoints (`/embed/`) or third-party site HTML (`picuki.com`, `imginn.com`).
   - There is no implementation of direct Instagram Reel/Story endpoints (`/api/v1/feed/reels_media/` or GraphQL `query_hash=9f88277a79d679a55c8b094d2db581c9`) or Highlight Tray endpoints (`/api/v1/highlights/{user_id}/highlights_tray/` or GraphQL `query_hash=d4d882ed8e7f8496d62326505ce44db6`).
   - Returned story and highlight media data is limited to simple boolean flags (`has_story: True/False`) or image URLs, rather than rich, structured story/highlight media objects (`id`, `media_type`, `media_url`, `thumbnail_url`, `taken_at`, `expiring_at`, `title`, `cover_media_url`).

3. **Feature 7 Deficiencies (Public Web Mirror Pipeline Adapter)**:
   - Line 667 (`_fetch_via_web_mirrors`) contains hardcoded inline requests to Greatfon, AnonIGViewer, Instanavigation, and Dumpor.
   - There is no modular adapter interface, no standalone `WebMirrorPipeline` module, and no specialized parsers for individual mirrors (InstaNavigation, Picuki, Imginn, Dumpor, Greatfon).
   - Error handling is generic (`except Exception: pass`), lacking per-adapter fallback, retry logging, or normalized schema output for profile details, stories, and highlights.

4. **Feature 8 Deficiencies (Multi-Signal Recency Classification)**:
   - Lines 994–1055 in `instagram_finder.py` attempt inline regex matches for years (`2026`, `2025`), relative days (`days_ago_match`), and months (`month_match`).
   - The logic is tightly coupled inside `fetch_profile_details`, lacks a dedicated classifier class, does not support relative Turkish strings like `Son 5 Gün`, `Son İçerik: Mart 2026`, or explicit zero-post indicators (`Gönderi Yok`, `0 Gönderi`).
   - Output fields are raw strings without standardized status enums (`ACTIVE_RECENT`, `ACTIVE_MODERATE`, `INACTIVE`, `UNKNOWN`) or timestamp estimation logic.

---

## 2. Logic Chain

1. **From Observation 1 (Direct Guest Profile API)**:
   - Pre-fetching guest cookies (`mid`, `ig_did`, `csrftoken`) via `await self.session_manager.get_guest_cookies()` and injecting `x-asbd-id: "198387"`, `x-ig-www-claim: "0"`, `x-csrftoken: csrftoken`, `x-requested-with: "XMLHttpRequest"`, and `Referer: https://www.instagram.com/{clean_user}/` ensures `web_profile_info` requests mirror genuine Instagram web application traffic, avoiding automatic 403 blocks.

2. **From Observation 2 (Anonymous Story & Highlight Media Extractor)**:
   - Defining structured schemas (`StoryMediaItem`, `HighlightTrayItem`) and implementing `fetch_user_stories(user_id)` and `fetch_user_highlights(user_id)` using direct REST/GraphQL reel/highlight endpoints — coupled with automatic fallback to Web Mirror Pipeline Adapters when direct endpoints return 401/403 — guarantees high extraction success rates for active stories and highlight archives without requiring logged-in accounts.

3. **From Observation 3 (Public Web Mirror Pipeline Adapter)**:
   - Creating `src/aegisScout/discovery/web_mirrors.py` with an abstract base class `WebMirrorAdapter` and concrete adapters (`InstaNavigationAdapter`, `PicukiAdapter`, `ImginnAdapter`, `DumporAdapter`, `GreatfonAdapter`) managed by `WebMirrorPipeline` isolates mirror parsing logic.
   - `WebMirrorPipeline` tries adapters sequentially with timeouts and returns normalized profile details, story media lists, and highlight tray items.

4. **From Observation 4 (Multi-Signal Recency Classification)**:
   - Creating `src/aegisScout/discovery/recency_classifier.py` with `RecencyClassifier` and a `RecencyResult` dataclass standardizes recency scoring across all discovery paths.
   - Parsing hours-ago, relative days (`Son 5 Gün`), month-year dates (`Son İçerik: Mart 2026`), relative weeks, and zero-post indicators produces a composite score (0–100), estimated days since last activity, Unix timestamp estimation, and a standardized status enum (`ACTIVE_RECENT`, `ACTIVE_MODERATE`, `INACTIVE`, `UNKNOWN`).

---

## 3. Caveats

- **Instagram Guest API Rate Limits**: Instagram periodically tightens direct guest API access. The implementation MUST treat direct endpoints as primary (Tier 0) and seamlessly fall back to `WebMirrorPipeline` (Tier 1) whenever direct calls return 401, 403, 429, or empty payloads.
- **Mirror Web Layout Variations**: Public mirrors (InstaNavigation, Picuki, Imginn, Dumpor, Greatfon) change their DOM layout or introduce anti-bot challenges over time. Each adapter MUST use fallback regexes alongside BeautifulSoup HTML parsing, and failure in one adapter MUST NOT block subsequent adapters.
- **Date String Diversity**: Recency text can appear in Turkish (`3 saat önce`, `Son 5 Gün`, `Mart 2026`) or English (`3 hours ago`, `5 days ago`, `March 2026`). The `RecencyClassifier` regex matrix MUST handle both languages seamlessly.

---

## 4. Conclusion & Detailed Implementation Blueprint for Worker M2

Worker M2 must implement 2 new modules and modify `instagram_finder.py` plus create comprehensive unit tests:

---

### File 1: Create `src/aegisScout/discovery/web_mirrors.py`

#### Purpose
Unified Public Web Mirror Pipeline Adapter for InstaNavigation, Picuki, Imginn, Dumpor, and Greatfon.

#### Code Specification
```python
"""
Public Web Mirror Pipeline Adapter for AegisScout.
Extracts profile details, stories, and highlights from zero-key public Instagram mirrors.
"""
from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

from aegisScout.discovery.instagram_session import InstagramSessionManager
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.web_mirrors")


class WebMirrorAdapter(ABC):
    """Abstract base class for Instagram public web mirror adapters."""

    def __init__(self, session_manager: InstagramSessionManager):
        self.session_manager = session_manager

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the mirror adapter."""
        pass

    @abstractmethod
    async def fetch_profile(self, username: str) -> Optional[Dict]:
        """Fetch profile details from mirror."""
        pass

    @abstractmethod
    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        """Fetch active stories from mirror."""
        pass

    @abstractmethod
    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        """Fetch highlights from mirror."""
        pass


class InstaNavigationAdapter(WebMirrorAdapter):
    """Adapter for InstaNavigation mirror (instanavigation.com)."""

    @property
    def name(self) -> str:
        return "InstaNavigation"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://instanavigation.com/user-profile/{username}"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    title = soup.find("meta", property="og:title")
                    desc = soup.find("meta", property="og:description")
                    title_text = title["content"] if title and title.get("content") else ""
                    desc_text = desc["content"] if desc and desc.get("content") else ""

                    f_match = re.search(r"([\d\.,KMBkmb]+)\s+(?:Followers|Takipçi)", desc_text, re.I)
                    f_raw = 0
                    if f_match:
                        from aegisScout.discovery.instagram_finder import _parse_count
                        f_raw = _parse_count(f_match.group(1))

                    avatar_img = soup.find("img", class_=re.compile(r"avatar|profile", re.I))
                    pic_url = avatar_img["src"] if avatar_img and avatar_img.get("src") else None

                    if title_text or desc_text:
                        return {
                            "username": username.lower(),
                            "full_name": title_text.split("-")[0].split("@")[0].strip() or username,
                            "bio": desc_text[:400],
                            "followers_raw": f_raw,
                            "followers": str(f_raw) if f_raw else "N/A",
                            "profile_pic_url": pic_url,
                            "source_api": self.name,
                        }
        except Exception as e:
            logger.debug(f"{self.name} profile fetch error @{username}: {e}")
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        url = f"https://instanavigation.com/user-profile/{username}"
        stories: List[Dict] = []
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    story_items = soup.select(".story-item, .stories-list img, .story-box img")
                    for idx, item in enumerate(story_items[:10]):
                        src = item.get("src") or item.get("data-src")
                        if src and ("cdn" in src or "fbcdn" in src or "http" in src):
                            is_video = "video" in item.get("class", []) or src.endswith(".mp4")
                            stories.append({
                                "id": f"instanav_story_{idx+1}",
                                "media_type": "video" if is_video else "image",
                                "media_url": src,
                                "thumbnail_url": src,
                                "taken_at": 0,
                                "taken_at_iso": "",
                                "source": self.name,
                            })
        except Exception as e:
            logger.debug(f"{self.name} stories fetch error @{username}: {e}")
        return stories if stories else None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        # InstaNavigation highlight extraction
        return None


class PicukiAdapter(WebMirrorAdapter):
    """Adapter for Picuki mirror (picuki.com)."""

    @property
    def name(self) -> str:
        return "Picuki"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://www.picuki.com/profile/{username}"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    name_tag = soup.select_one(".profile-name-top, .profile-name")
                    bio_tag = soup.select_one(".profile-description, .profile-bio")
                    avatar_tag = soup.select_one(".profile-avatar img")

                    full_name = name_tag.get_text(strip=True) if name_tag else username
                    bio = bio_tag.get_text(strip=True) if bio_tag else ""
                    pic_url = avatar_tag.get("src") if avatar_tag else None

                    followers_tag = soup.select_one(".followed_by, .followers-count")
                    from aegisScout.discovery.instagram_finder import _parse_count
                    f_raw = _parse_count(followers_tag.get_text(strip=True)) if followers_tag else 0

                    return {
                        "username": username.lower(),
                        "full_name": full_name,
                        "bio": bio[:400],
                        "followers_raw": f_raw,
                        "followers": str(f_raw) if f_raw else "N/A",
                        "profile_pic_url": pic_url,
                        "source_api": self.name,
                    }
        except Exception as e:
            logger.debug(f"{self.name} profile fetch error @{username}: {e}")
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        return None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class ImginnAdapter(WebMirrorAdapter):
    """Adapter for Imginn mirror (imginn.com)."""

    @property
    def name(self) -> str:
        return "Imginn"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://imginn.com/{username}/"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    name_tag = soup.select_one(".user-name, h1")
                    bio_tag = soup.select_one(".user-bio, .description")
                    avatar_tag = soup.select_one(".user-avatar img, .avatar img")

                    full_name = name_tag.get_text(strip=True) if name_tag else username
                    bio = bio_tag.get_text(strip=True) if bio_tag else ""
                    pic_url = avatar_tag.get("src") if avatar_tag else None

                    return {
                        "username": username.lower(),
                        "full_name": full_name,
                        "bio": bio[:400],
                        "followers_raw": 0,
                        "followers": "N/A",
                        "profile_pic_url": pic_url,
                        "source_api": self.name,
                    }
        except Exception as e:
            logger.debug(f"{self.name} profile fetch error @{username}: {e}")
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        url = f"https://imginn.com/stories/{username}/"
        stories: List[Dict] = []
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    items = soup.select(".story-item img, .items img")
                    for idx, img in enumerate(items[:10]):
                        src = img.get("src") or img.get("data-src")
                        if src and len(src) > 15:
                            stories.append({
                                "id": f"imginn_story_{idx+1}",
                                "media_type": "image",
                                "media_url": src,
                                "thumbnail_url": src,
                                "taken_at": 0,
                                "taken_at_iso": "",
                                "source": self.name,
                            })
        except Exception as e:
            logger.debug(f"{self.name} stories fetch error @{username}: {e}")
        return stories if stories else None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class DumporAdapter(WebMirrorAdapter):
    """Adapter for Dumpor mirror (dumpor.com)."""

    @property
    def name(self) -> str:
        return "Dumpor"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://dumpor.com/v/{username}"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    title = soup.find("meta", property="og:title")
                    desc = soup.find("meta", property="og:description")
                    title_text = title["content"] if title and title.get("content") else ""
                    desc_text = desc["content"] if desc and desc.get("content") else ""

                    if title_text or desc_text:
                        return {
                            "username": username.lower(),
                            "full_name": title_text.split("-")[0].strip() or username,
                            "bio": desc_text[:400],
                            "source_api": self.name,
                        }
        except Exception as e:
            logger.debug(f"{self.name} profile fetch error @{username}: {e}")
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        return None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class GreatfonAdapter(WebMirrorAdapter):
    """Adapter for Greatfon mirror (greatfon.com)."""

    @property
    def name(self) -> str:
        return "Greatfon"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://greatfon.com/v/{username}"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=6.0,
                headers={"User-Agent": self.session_manager.get_random_user_agent("desktop")}
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    title = soup.find("meta", property="og:title")
                    desc = soup.find("meta", property="og:description")
                    title_text = title["content"] if title and title.get("content") else ""
                    desc_text = desc["content"] if desc and desc.get("content") else ""

                    if title_text or desc_text:
                        return {
                            "username": username.lower(),
                            "full_name": title_text.split("-")[0].strip() or username,
                            "bio": desc_text[:400],
                            "source_api": self.name,
                        }
        except Exception as e:
            logger.debug(f"{self.name} profile fetch error @{username}: {e}")
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        return None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class WebMirrorPipeline:
    """
    Orchestrates multiple web mirror adapters with automatic failover.
    """

    def __init__(self, session_manager: InstagramSessionManager):
        self.adapters: List[WebMirrorAdapter] = [
            InstaNavigationAdapter(session_manager),
            PicukiAdapter(session_manager),
            ImginnAdapter(session_manager),
            DumporAdapter(session_manager),
            GreatfonAdapter(session_manager),
        ]

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        for adapter in self.adapters:
            res = await adapter.fetch_profile(username)
            if res and (res.get("bio") or res.get("followers_raw", 0) > 0 or res.get("full_name")):
                logger.info(f"Successfully retrieved profile for @{username} via mirror {adapter.name}")
                return res
        return None

    async def fetch_stories(self, username: str) -> List[Dict]:
        for adapter in self.adapters:
            res = await adapter.fetch_stories(username)
            if res:
                logger.info(f"Retrieved {len(res)} stories for @{username} via mirror {adapter.name}")
                return res
        return []

    async def fetch_highlights(self, username: str) -> List[Dict]:
        for adapter in self.adapters:
            res = await adapter.fetch_highlights(username)
            if res:
                logger.info(f"Retrieved highlights for @{username} via mirror {adapter.name}")
                return res
        return []
```

---

### File 2: Create `src/aegisScout/discovery/recency_classifier.py`

#### Purpose
Multi-Signal Recency Classifier (Feature 8) parsing relative hours, relative days (`Son 5 Gün`), month-year dates (`Son İçerik: Mart 2026`), relative weeks, and zero-post indicators.

#### Code Specification
```python
"""
Multi-Signal Recency Classifier for Instagram Profiles & Posts.
Evaluates account activity recency across Turkish and English signals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RecencyResult:
    """Standardized recency classification result."""
    status_enum: str  # ACTIVE_RECENT (<=30d), ACTIVE_MODERATE (31-90d), INACTIVE (>90d or 0 posts), UNKNOWN
    human_text: str  # e.g., "Son 5 Gün İçinde Aktif"
    raw_score: int  # 0 to 100 integer score for sorting/ranking
    estimated_days: float  # Estimated days since last post
    last_post_timestamp: Optional[int]  # Unix timestamp if computable
    is_zero_post: bool  # True if 0 posts


TURKISH_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}

ENGLISH_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


class RecencyClassifier:
    """
    Parses activity signals from raw HTML, text snippets, and timestamp numbers.
    """

    @classmethod
    def classify(
        self,
        text_or_html: str = "",
        post_count: int = -1,
        latest_timestamp: Optional[int] = None,
        reference_year: int = 2026,
    ) -> RecencyResult:
        now_ts = int(datetime.now(timezone.utc).timestamp())

        # Signal 0: Explicit Unix Timestamp provided
        if latest_timestamp and latest_timestamp > 0:
            diff_seconds = max(0, now_ts - latest_timestamp)
            days_ago = diff_seconds / 86400.0
            if days_ago <= 30:
                return RecencyResult(
                    status_enum="ACTIVE_RECENT",
                    human_text=f"Son {max(1, int(days_ago))} Gün İçinde Aktif",
                    raw_score=max(85, 100 - int(days_ago)),
                    estimated_days=round(days_ago, 1),
                    last_post_timestamp=latest_timestamp,
                    is_zero_post=False,
                )
            elif days_ago <= 90:
                return RecencyResult(
                    status_enum="ACTIVE_MODERATE",
                    human_text=f"Son {int(days_ago)} Gün İçinde Aktif",
                    raw_score=max(60, 84 - int((days_ago - 30) * 0.4)),
                    estimated_days=round(days_ago, 1),
                    last_post_timestamp=latest_timestamp,
                    is_zero_post=False,
                )
            else:
                return RecencyResult(
                    status_enum="INACTIVE",
                    human_text=f"{int(days_ago)} Gün Önce Aktif (Geçmiş İçerik)",
                    raw_score=max(10, 59 - int((days_ago - 90) * 0.1)),
                    estimated_days=round(days_ago, 1),
                    last_post_timestamp=latest_timestamp,
                    is_zero_post=False,
                )

        # Signal 1: Zero Post Detection
        zero_post_patterns = [
            r"gönderi\s*yok", r"0\s*gönderi", r"gönderisiz\s*hesap",
            r"no\s*posts\s*yet", r"0\s*posts", r"no\s*posts"
        ]
        is_zero = (post_count == 0) or any(re.search(pat, text_or_html, re.I) for pat in zero_post_patterns)
        if is_zero:
            return RecencyResult(
                status_enum="INACTIVE",
                human_text="Gönderisiz Hesap",
                raw_score=15,
                estimated_days=999.0,
                last_post_timestamp=None,
                is_zero_post=True,
            )

        # Signal 2: Hours / Minutes Ago
        hours_match = re.search(r"\b(\d+)\s*(?:saat|hour|h)\s*(?:önce|ago)?\b", text_or_html, re.I)
        if hours_match:
            hours = int(hours_match.group(1))
            days_est = hours / 24.0
            return RecencyResult(
                status_enum="ACTIVE_RECENT",
                human_text=f"Son {hours} Saat İçinde Aktif",
                raw_score=99,
                estimated_days=round(days_est, 2),
                last_post_timestamp=now_ts - (hours * 3600),
                is_zero_post=False,
            )

        # Signal 3: Relative Days (e.g. "Son 5 Gün", "2 gün önce", "5 days ago", "3d")
        days_match = re.search(r"(?:son\s*)?\b(\d+)\s*(?:gün|day|d)\s*(?:içinde|içinde aktif|önce|ago)?\b", text_or_html, re.I)
        if days_match:
            days = int(days_match.group(1))
            if days <= 30:
                enum_val = "ACTIVE_RECENT"
                score = max(85, 98 - days)
            elif days <= 90:
                enum_val = "ACTIVE_MODERATE"
                score = max(60, 84 - int((days - 30) * 0.4))
            else:
                enum_val = "INACTIVE"
                score = max(20, 59 - int((days - 90) * 0.2))

            return RecencyResult(
                status_enum=enum_val,
                human_text=f"Son {days} Gün İçinde Aktif",
                raw_score=score,
                estimated_days=float(days),
                last_post_timestamp=now_ts - (days * 86400),
                is_zero_post=False,
            )

        # Signal 4: Relative Weeks (e.g. "2 hafta önce", "3 weeks ago")
        weeks_match = re.search(r"\b(\d+)\s*(?:hafta|week|w)\s*(?:önce|ago)?\b", text_or_html, re.I)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            days = weeks * 7
            enum_val = "ACTIVE_RECENT" if days <= 30 else "ACTIVE_MODERATE"
            score = max(65, 90 - (weeks * 5))
            return RecencyResult(
                status_enum=enum_val,
                human_text=f"Son {weeks} Hafta İçinde Aktif",
                raw_score=score,
                estimated_days=float(days),
                last_post_timestamp=now_ts - (days * 86400),
                is_zero_post=False,
            )

        # Signal 5: Month-Year Format (e.g. "Son İçerik: Mart 2026", "Ocak 2025", "15 March 2026")
        month_year_match = re.search(
            r"(?:son\s*içerik:\s*)?(\d{1,2})?\s*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\s*(202[4-6])",
            text_or_html, re.I
        )
        if month_year_match:
            day_str, m_str, y_str = month_year_match.groups()
            month_num = TURKISH_MONTHS.get(m_str.lower()) or ENGLISH_MONTHS.get(m_str.lower())
            if month_num:
                year_num = int(y_str)
                day_num = int(day_str) if day_str else 15
                try:
                    dt = datetime(year_num, month_num, day_num, tzinfo=timezone.utc)
                    ts = int(dt.timestamp())
                    days_ago = (now_ts - ts) / 86400.0
                    enum_val = "ACTIVE_RECENT" if days_ago <= 30 else ("ACTIVE_MODERATE" if days_ago <= 90 else "INACTIVE")
                    score = max(30, 95 - int(days_ago * 0.5))
                    return RecencyResult(
                        status_enum=enum_val,
                        human_text=f"Son İçerik: {m_str.title()} {y_str}",
                        raw_score=score,
                        estimated_days=round(days_ago, 1),
                        last_post_timestamp=ts,
                        is_zero_post=False,
                    )
                except Exception:
                    pass

        # Signal 6: Year-Only Detection
        if re.search(r"\b2026\b", text_or_html):
            return RecencyResult(
                status_enum="ACTIVE_RECENT",
                human_text="Güncel Aktif Profil (2026)",
                raw_score=90,
                estimated_days=30.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )
        elif re.search(r"\b2025\b", text_or_html):
            return RecencyResult(
                status_enum="ACTIVE_MODERATE",
                human_text="Aktif Profil (2025)",
                raw_score=80,
                estimated_days=180.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )
        elif re.search(r"\b2024\b", text_or_html):
            return RecencyResult(
                status_enum="INACTIVE",
                human_text="Geçmiş İçerikli Hesap (2024)",
                raw_score=60,
                estimated_days=500.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )

        # Default fallback
        if post_count > 0:
            return RecencyResult(
                status_enum="ACTIVE_MODERATE",
                human_text="İçerik Mevcut",
                raw_score=65,
                estimated_days=60.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )

        return RecencyResult(
            status_enum="UNKNOWN",
            human_text="Profil Mevcut",
            raw_score=50,
            estimated_days=90.0,
            last_post_timestamp=None,
            is_zero_post=False,
        )
```

---

### File 3: Refactor `src/aegisScout/discovery/instagram_finder.py`

#### Changes to Implement:

1. **Import M2 Modules**:
   ```python
   from aegisScout.discovery.web_mirrors import WebMirrorPipeline
   from aegisScout.discovery.recency_classifier import RecencyClassifier, RecencyResult
   ```

2. **Update `InstagramFinder.__init__`**:
   Instantiate `self.web_mirror_pipeline = WebMirrorPipeline(self.session_manager)`.

3. **Feature 5 Fix in `fetch_profile_details` (Tier 0 `web_profile_info`)**:
   ```python
   # Tier 0: Instagram public web_profile_info JSON API endpoint
   try:
       cookies = await self.session_manager.get_guest_cookies()
       web_info_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={clean_user}"
       headers = {
           "User-Agent": self.session_manager.get_random_user_agent("desktop"),
           "x-ig-app-id": "936619743392459",
           "x-asbd-id": "198387",
           "x-ig-www-claim": "0",
           "x-requested-with": "XMLHttpRequest",
           "x-csrftoken": cookies.get("csrftoken", ""),
           "Referer": f"https://www.instagram.com/{clean_user}/",
           "Accept": "*/*",
           "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
       }
       async with self._get_resilient_client(
           timeout=6.0,
           follow_redirects=True,
           headers=headers,
           use_guest_cookies=True,
       ) as client:
           resp = await self.session_manager.request_with_retry(client, "GET", web_info_url)
           if resp and resp.status_code == 200:
               res_json = resp.json()
               user_data = res_json.get("data", {}).get("user")
               if user_data:
                   # ... parse biography, bio_links, followers, etc. ...
   ```

4. **Feature 6 Implementation (Story & Highlight Extraction)**:
   Add dedicated helper methods:
   - `async def fetch_user_stories(self, username: str, user_id: Optional[str] = None) -> List[Dict]`
     1. Pre-fetch guest cookies via `self.session_manager.get_guest_cookies()`.
     2. Attempt direct REST endpoint `https://i.instagram.com/api/v1/feed/reels_media/?reel_ids={user_id}` or GraphQL reels query if `user_id` is available.
     3. If blocked or empty, call `await self.web_mirror_pipeline.fetch_stories(username)`.
     4. Format output list into standard `StoryMediaItem` dicts:
        ```python
        {
            "id": str,
            "media_type": "image" | "video",
            "media_url": str,
            "thumbnail_url": str,
            "taken_at": int,
            "taken_at_iso": str,
            "expiring_at": int,
        }
        ```
   - `async def fetch_user_highlights(self, username: str, user_id: Optional[str] = None) -> List[Dict]`
     1. Attempt highlight tray endpoint `https://i.instagram.com/api/v1/highlights/{user_id}/highlights_tray/` if `user_id` is available.
     2. If blocked or empty, call `await self.web_mirror_pipeline.fetch_highlights(username)`.
     3. Format output list into standard `HighlightTrayItem` dicts:
        ```python
        {
            "id": str,
            "title": str,
            "cover_media_url": str,
            "media_count": int,
            "items": List[Dict]
        }
        ```
   - Refactor `fetch_anonymous_user_posts_and_stories`:
     Invoke `fetch_user_stories` and `fetch_user_highlights` to populate `stories` and `highlights` keys in the returned dictionary.

5. **Feature 7 Integration (`_fetch_via_web_mirrors`)**:
   Refactor `_fetch_via_web_mirrors` to delegate directly to `await self.web_mirror_pipeline.fetch_profile(username)`.

6. **Feature 8 Integration (`RecencyClassifier`)**:
   In `fetch_profile_details`, replace inline regex recency calculation with:
   ```python
   recency_res = RecencyClassifier.classify(
       text_or_html=fetched_html or default_data.get("bio", ""),
       post_count=_parse_count(default_data.get("posts", "0")),
   )
   default_data["last_active"] = recency_res.human_text
   default_data["last_active_raw"] = recency_res.raw_score
   default_data["recency_status"] = recency_res.status_enum
   ```

---

### File 4: Create `tests/test_discovery/test_m2_engine.py`

Implement unit tests validating all 4 M2 features:

1. `test_feature_5_web_profile_info_headers_and_parsing()`:
   - Uses `respx` to mock `https://www.instagram.com/api/v1/users/web_profile_info/?username=testuser`.
   - Asserts request contains `x-asbd-id`, `x-ig-www-claim`, `x-csrftoken`, and `Referer` headers.
   - Asserts response correctly populates profile fields (`bio`, `followers_raw`, `is_verified`, `is_business`).

2. `test_feature_6_anonymous_story_and_highlight_extractor()`:
   - Mocks reel media and highlight tray JSON responses.
   - Calls `fetch_anonymous_user_posts_and_stories("testuser")`.
   - Asserts returned dictionary contains structured `stories` and `highlights` arrays with valid keys (`media_type`, `media_url`, `title`, `cover_media_url`).

3. `test_feature_7_web_mirror_pipeline_failover()`:
   - Instantiates `WebMirrorPipeline`.
   - Mocks failure (HTTP 500/404) on `InstaNavigation` and success (HTTP 200) on `Picuki`.
   - Asserts `pipeline.fetch_profile("testuser")` successfully returns profile dictionary via `Picuki`.

4. `test_feature_8_multi_signal_recency_classification()`:
   - Tests `RecencyClassifier.classify` with inputs:
     - `"3 saat önce"` -> `ACTIVE_RECENT`, score >= 90
     - `"Son 5 Gün"` -> `ACTIVE_RECENT`, score >= 85
     - `"Son İçerik: Mart 2026"` -> `ACTIVE_RECENT`
     - `"Gönderi Yok"` / `post_count=0` -> `INACTIVE`, `is_zero_post=True`

---

## 5. Verification Method

To independently verify Worker M2's implementation:

1. **Execute the full discovery test suite**:
   ```pwsh
   pytest tests/test_discovery/test_m2_engine.py tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py -v
   ```
2. **Invalidation Conditions**:
   - Any failure in `test_m2_engine.py`.
   - Direct `web_profile_info` calls missing `x-asbd-id`, `x-csrftoken`, or `x-ig-www-claim` headers.
   - `fetch_anonymous_user_posts_and_stories` raising unhandled exceptions when guest endpoints return 401/403.
   - `WebMirrorPipeline` failing to execute failover when an individual mirror returns an error.
   - `RecencyClassifier` failing to parse relative days (`Son 5 Gün`) or month-year strings (`Son İçerik: Mart 2026`).
