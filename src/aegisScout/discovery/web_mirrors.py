"""
Public Web Mirror Pipeline Adapter for AegisScout.
Extracts profile details, stories, and highlights from zero-key public Instagram mirrors.

Supported Mirrors (tried in priority order):
  1. StoriesIg      — storiesig.com          (best anonymous story viewer, 2024-active)
  2. Picuki         — picuki.com             (profile + posts)
  3. Imginn         — imginn.com             (profile + stories)
  4. InstaNavigation— instanavigation.com    (profile + stories + highlights)
  5. InstaFinsta    — instafinsta.com        (stories fallback)
  6. Dumpor         — dumpor.com             (profile fallback)
  7. Greatfon       — greatfon.com           (profile fallback)
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


def _parse_count_local(text: str) -> int:
    """Parse human-readable counts like '12.5K', '2M', '450' into int."""
    if not text:
        return 0
    text = str(text).replace(",", ".").strip().upper()
    try:
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        if "K" in text or "B" in text:
            return int(float(text.replace("K", "").replace("B", "")) * 1_000)
        return int(float(re.sub(r"[^\d.]", "", text) or "0"))
    except (ValueError, OverflowError):
        return 0


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

    def _desktop_headers(self) -> Dict[str, str]:
        return {"User-Agent": self.session_manager.get_random_user_agent("desktop")}


class StoriesIgAdapter(WebMirrorAdapter):
    """
    Adapter for StoriesIG — storiesig.com.
    Best current (2024-2026) anonymous story viewer. No login required.
    """

    @property
    def name(self) -> str:
        return "StoriesIG"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        """StoriesIG does not expose profile stats — return None."""
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        stories: List[Dict] = []
        urls_to_try = [
            f"https://storiesig.info/stories/{username}",
            f"https://storiesig.app/stories/{username}",
            f"https://storiesig.com/stories/{username}",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0,
                    headers={
                        **self._desktop_headers(),
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://www.google.com/",
                    }
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200 and len(resp.text) > 500:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        # Multi-selector strategy for story items
                        selectors = [
                            ".story-item img",
                            ".stories-container img",
                            ".story-content img",
                            ".media-wrapper img",
                            "article img",
                            ".swiper-slide img",
                        ]
                        imgs: List = []
                        for sel in selectors:
                            imgs = soup.select(sel)
                            if imgs:
                                break

                        # Also look for video sources
                        videos = soup.select("video source, video[src]")
                        seen_urls: set = set()

                        for img in imgs[:15]:
                            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                            if src and len(src) > 20 and src not in seen_urls:
                                seen_urls.add(src)
                                stories.append({
                                    "id": f"storiesig_img_{len(stories)+1}",
                                    "media_type": "image",
                                    "media_url": src,
                                    "thumbnail_url": src,
                                    "taken_at": 0,
                                    "taken_at_iso": "",
                                    "source": self.name,
                                })

                        for vid in videos[:5]:
                            src = vid.get("src") or vid.parent.get("src") if vid.parent else ""
                            if src and src not in seen_urls:
                                seen_urls.add(src)
                                stories.append({
                                    "id": f"storiesig_vid_{len(stories)+1}",
                                    "media_type": "video",
                                    "media_url": src,
                                    "thumbnail_url": src,
                                    "taken_at": 0,
                                    "taken_at_iso": "",
                                    "source": self.name,
                                })

                        if stories:
                            logger.debug(f"{self.name}: found {len(stories)} stories for @{username}")
                            return stories
            except Exception as e:
                logger.debug(f"{self.name} stories fetch error @{username} [{url}]: {e}")
        return None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class PicukiAdapter(WebMirrorAdapter):
    """Adapter for Picuki mirror (picuki.com) — profile + posts."""

    @property
    def name(self) -> str:
        return "Picuki"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        urls_to_try = [
            f"https://www.picuki.com/profile/{username}",
            f"https://picuki.com/profile/{username}",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200 and len(resp.text) > 400:
                        soup = BeautifulSoup(resp.text, "html.parser")

                        # Full name — multiple selector strategies
                        full_name = username
                        for sel in [".profile-name-top h1", ".profile-name h1", "h1.name",
                                    ".user-name h1", ".profile-header h1", "h1"]:
                            el = soup.select_one(sel)
                            if el:
                                full_name = el.get_text(strip=True) or full_name
                                break

                        # Bio
                        bio = ""
                        for sel in [".profile-description", ".profile-bio", ".biography",
                                    ".bio-text", "[class*='description']"]:
                            el = soup.select_one(sel)
                            if el:
                                bio = el.get_text(strip=True)
                                break

                        # Profile pic
                        pic_url = None
                        for sel in [".profile-avatar img", ".avatar-image img",
                                    "img[class*='avatar']", ".profile-image img"]:
                            el = soup.select_one(sel)
                            if el:
                                pic_url = el.get("src") or el.get("data-src")
                                if pic_url:
                                    break

                        # Followers count
                        f_raw = 0
                        for sel in [".followed_by", ".followers-count", "[class*='follower']",
                                    ".count-followers"]:
                            el = soup.select_one(sel)
                            if el:
                                f_raw = _parse_count_local(el.get_text(strip=True))
                                if f_raw:
                                    break

                        # Also try og:description for stats
                        if not f_raw:
                            og_desc = soup.find("meta", property="og:description")
                            if og_desc and og_desc.get("content"):
                                m = re.search(r"([\d.,KMBkmb]+)\s+(?:Followers|Takipçi)", og_desc["content"], re.I)
                                if m:
                                    f_raw = _parse_count_local(m.group(1))

                        if full_name != username or bio or f_raw:
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
    """Adapter for Imginn mirror (imginn.com) — profile + stories."""

    @property
    def name(self) -> str:
        return "Imginn"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://imginn.com/{username}/"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=8.0, headers=self._desktop_headers()
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    full_name = username
                    for sel in [".user-name", "h1", ".name", ".username-heading"]:
                        el = soup.select_one(sel)
                        if el:
                            text = el.get_text(strip=True)
                            if text and text != f"@{username}":
                                full_name = text
                                break

                    bio = ""
                    for sel in [".user-bio", ".description", ".biography", ".bio"]:
                        el = soup.select_one(sel)
                        if el:
                            bio = el.get_text(strip=True)
                            break

                    pic_url = None
                    for sel in [".user-avatar img", ".avatar img", ".profile-pic img"]:
                        el = soup.select_one(sel)
                        if el:
                            pic_url = el.get("src") or el.get("data-src")
                            if pic_url:
                                break

                    f_raw = 0
                    for sel in [".count", ".followers", "[class*='follow']"]:
                        for el in soup.select(sel):
                            text = el.get_text(strip=True)
                            if "follower" in text.lower() or "takipçi" in text.lower():
                                f_raw = _parse_count_local(text)
                                if f_raw:
                                    break
                        if f_raw:
                            break

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
        stories: List[Dict] = []
        # Try multiple URL patterns (imginn changes paths occasionally)
        urls_to_try = [
            f"https://imginn.com/stories/{username}/",
            f"https://imginn.com/story/{username}/",
            f"https://imginn.org/stories/{username}/",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        selectors = [
                            ".story-item img", ".items img", ".swiper-slide img",
                            ".story-media img", ".stories img", "article img",
                        ]
                        imgs: List = []
                        for sel in selectors:
                            imgs = soup.select(sel)
                            if imgs:
                                break

                        seen: set = set()
                        for idx, img in enumerate(imgs[:15]):
                            src = img.get("src") or img.get("data-src")
                            if src and len(src) > 15 and src not in seen:
                                seen.add(src)
                                stories.append({
                                    "id": f"imginn_story_{idx+1}",
                                    "media_type": "image",
                                    "media_url": src,
                                    "thumbnail_url": src,
                                    "taken_at": 0,
                                    "taken_at_iso": "",
                                    "source": self.name,
                                })
                        if stories:
                            return stories
            except Exception as e:
                logger.debug(f"{self.name} stories fetch error @{username} [{url}]: {e}")
        return None if not stories else stories

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class InstaNavigationAdapter(WebMirrorAdapter):
    """Adapter for InstaNavigation mirror (instanavigation.com)."""

    @property
    def name(self) -> str:
        return "InstaNavigation"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        urls_to_try = [
            f"https://instanavigation.com/user-profile/{username}",
            f"https://www.instanavigation.com/@{username}",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200 and len(resp.text) > 400:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        title = soup.find("meta", property="og:title")
                        desc = soup.find("meta", property="og:description")
                        title_text = title["content"] if title and title.get("content") else ""
                        desc_text = desc["content"] if desc and desc.get("content") else ""

                        f_raw = 0
                        if desc_text:
                            m = re.search(r"([\d.,KMBkmb]+)\s+(?:Followers|Takipçi)", desc_text, re.I)
                            if m:
                                f_raw = _parse_count_local(m.group(1))

                        pic_url = None
                        for sel in [
                            "img[class*='avatar']", "img[class*='profile']",
                            ".profile-pic img", ".avatar img", ".user-photo img",
                        ]:
                            el = soup.select_one(sel)
                            if el:
                                pic_url = el.get("src") or el.get("data-src")
                                if pic_url:
                                    break

                        if not pic_url:
                            og_img = soup.find("meta", property="og:image")
                            if og_img and og_img.get("content"):
                                pic_url = og_img["content"]

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
        urls_to_try = [
            f"https://instanavigation.com/user-profile/{username}",
            f"https://instanavigation.com/stories/{username}",
        ]
        stories: List[Dict] = []
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        selectors = [
                            ".story-item img", ".story-item",
                            ".stories-list img", ".story-box img",
                            ".swiper-slide img", "[class*='story'] img",
                        ]
                        seen_urls: set = set()
                        for sel in selectors:
                            raw_items = soup.select(sel)
                            for raw_item in raw_items[:15]:
                                item = raw_item.find("img") if raw_item.name != "img" else raw_item
                                if not item:
                                    continue
                                src = item.get("src") or item.get("data-src")
                                if src and len(src) > 15 and src not in seen_urls:
                                    seen_urls.add(src)
                                    is_video = (
                                        "video" in (item.get("class") or []) or
                                        "video" in (raw_item.get("class") or []) or
                                        (src or "").endswith(".mp4")
                                    )
                                    stories.append({
                                        "id": f"instanav_story_{len(stories)+1}",
                                        "media_type": "video" if is_video else "image",
                                        "media_url": src,
                                        "thumbnail_url": src,
                                        "taken_at": 0,
                                        "taken_at_iso": "",
                                        "source": self.name,
                                    })
                        if stories:
                            return stories
            except Exception as e:
                logger.debug(f"{self.name} stories fetch error @{username}: {e}")
        return None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        urls_to_try = [
            f"https://instanavigation.com/user-profile/{username}",
            f"https://instanavigation.com/highlights/{username}",
        ]
        highlights: List[Dict] = []
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        hl_items = soup.select(
                            ".highlight-item, .highlights-list .item, [class*='highlight'] li"
                        )
                        for idx, item in enumerate(hl_items[:8]):
                            title_el = item.select_one(".title, .highlight-title, span")
                            img_el = item.select_one("img")
                            title = title_el.get_text(strip=True) if title_el else f"Highlight #{idx+1}"
                            cover_url = img_el.get("src") if img_el else None
                            if cover_url:
                                highlights.append({
                                    "id": f"instanav_hl_{idx+1}",
                                    "title": title,
                                    "cover_media_url": cover_url,
                                    "media_count": 1,
                                    "items": [],
                                    "source": self.name,
                                })
                        if highlights:
                            return highlights
            except Exception as e:
                logger.debug(f"{self.name} highlights fetch error @{username}: {e}")
        return None


class InstaFinstaAdapter(WebMirrorAdapter):
    """
    Adapter for InstaFinsta — instafinsta.com.
    Anonymous story viewer fallback.
    """

    @property
    def name(self) -> str:
        return "InstaFinsta"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        url = f"https://instafinsta.com/{username}/"
        try:
            async with self.session_manager.get_resilient_client(
                timeout=8.0, headers=self._desktop_headers()
            ) as client:
                resp = await self.session_manager.request_with_retry(client, "GET", url)
                if resp and resp.status_code == 200 and len(resp.text) > 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    og_title = soup.find("meta", property="og:title")
                    og_desc = soup.find("meta", property="og:description")
                    title_text = og_title["content"] if og_title and og_title.get("content") else ""
                    desc_text = og_desc["content"] if og_desc and og_desc.get("content") else ""
                    if title_text or desc_text:
                        return {
                            "username": username.lower(),
                            "full_name": title_text.split("(")[0].strip() or username,
                            "bio": desc_text[:400],
                            "source_api": self.name,
                        }
        except Exception as e:
            logger.debug(f"{self.name} profile fetch error @{username}: {e}")
        return None

    async def fetch_stories(self, username: str) -> Optional[List[Dict]]:
        stories: List[Dict] = []
        urls_to_try = [
            f"https://instafinsta.com/stories/{username}/",
            f"https://instafinsta.com/{username}/stories/",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
                ) as client:
                    resp = await self.session_manager.request_with_retry(client, "GET", url)
                    if resp and resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        imgs = soup.select(
                            ".story img, .stories img, .story-media img, "
                            ".item img, .slide img, article img"
                        )
                        seen: set = set()
                        for idx, img in enumerate(imgs[:15]):
                            src = img.get("src") or img.get("data-src")
                            if src and len(src) > 15 and src not in seen:
                                seen.add(src)
                                stories.append({
                                    "id": f"instafinsta_story_{idx+1}",
                                    "media_type": "image",
                                    "media_url": src,
                                    "thumbnail_url": src,
                                    "taken_at": 0,
                                    "taken_at_iso": "",
                                    "source": self.name,
                                })
                        if stories:
                            return stories
            except Exception as e:
                logger.debug(f"{self.name} stories fetch error @{username} [{url}]: {e}")
        return None

    async def fetch_highlights(self, username: str) -> Optional[List[Dict]]:
        return None


class DumporAdapter(WebMirrorAdapter):
    """Adapter for Dumpor mirror (dumpor.com) — profile fallback."""

    @property
    def name(self) -> str:
        return "Dumpor"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        urls_to_try = [
            f"https://dumpor.com/v/{username}",
            f"https://www.dumpor.com/v/{username}",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
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
    """Adapter for Greatfon mirror (greatfon.com) — profile fallback."""

    @property
    def name(self) -> str:
        return "Greatfon"

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        urls_to_try = [
            f"https://greatfon.com/v/{username}",
            f"https://www.greatfon.com/v/{username}",
        ]
        for url in urls_to_try:
            try:
                async with self.session_manager.get_resilient_client(
                    timeout=8.0, headers=self._desktop_headers()
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
    Runs adapters concurrently for profile fetching (fastest-wins),
    and sequentially for stories/highlights (preserving quality order).
    """

    def __init__(self, session_manager: InstagramSessionManager):
        self.session_manager = session_manager
        # Priority order: best story viewers first, then profile-only fallbacks
        self.story_adapters: List[WebMirrorAdapter] = [
            StoriesIgAdapter(session_manager),
            ImginnAdapter(session_manager),
            InstaNavigationAdapter(session_manager),
            InstaFinstaAdapter(session_manager),
        ]
        self.profile_adapters: List[WebMirrorAdapter] = [
            PicukiAdapter(session_manager),
            ImginnAdapter(session_manager),
            InstaNavigationAdapter(session_manager),
            DumporAdapter(session_manager),
            GreatfonAdapter(session_manager),
        ]
        # All adapters for unified access
        self.adapters: List[WebMirrorAdapter] = list({
            id(a): a for a in self.profile_adapters + self.story_adapters
        }.values())

    async def fetch_profile(self, username: str) -> Optional[Dict]:
        """
        Try all profile adapters concurrently; return first valid result.
        A result is valid if it has bio, followers, or a distinct full_name.
        """
        tasks = [adapter.fetch_profile(username) for adapter in self.profile_adapters]
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            results = []

        for adapter, res in zip(self.profile_adapters, results):
            if isinstance(res, dict) and (
                res.get("bio") or
                res.get("followers_raw", 0) > 0 or
                (res.get("full_name") and res["full_name"] != username)
            ):
                logger.info(f"Profile retrieved for @{username} via mirror {adapter.name}")
                return res
        return None

    async def fetch_stories(self, username: str) -> List[Dict]:
        """
        Try story adapters in priority order; return first non-empty result.
        """
        for adapter in self.story_adapters:
            try:
                res = await adapter.fetch_stories(username)
                if res:
                    logger.info(
                        f"Retrieved {len(res)} stories for @{username} via mirror {adapter.name}"
                    )
                    return res
            except Exception as e:
                logger.debug(f"Mirror {adapter.name} stories error for @{username}: {e}")
        return []

    async def fetch_highlights(self, username: str) -> List[Dict]:
        """
        Try highlight adapters in order; return first non-empty result.
        """
        highlight_adapters = [InstaNavigationAdapter(self.session_manager)]
        for adapter in highlight_adapters:
            try:
                res = await adapter.fetch_highlights(username)
                if res:
                    logger.info(f"Retrieved highlights for @{username} via mirror {adapter.name}")
                    return res
            except Exception as e:
                logger.debug(f"Mirror {adapter.name} highlights error for @{username}: {e}")
        return []
