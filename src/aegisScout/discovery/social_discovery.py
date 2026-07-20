"""
Multi-platform social media discovery for aegisScout.

Finds social media profile URLs for businesses across:
- YouTube
- LinkedIn
- TikTok
- Facebook
- Telegram
- X / Twitter

Uses DuckDuckGo HTML search (keyless) by default to avoid ToS issues with
direct scraping of each platform. Optionally falls back to Google Custom Search
API when configured (re-uses InstagramFinder-style configuration).

The output is a SocialProfiles dataclass (or None) and the module exposes both
per-platform helpers (find_youtube, find_linkedin, ...) and a single
discover_all(business_name, location) entry point for the research pipeline.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional, Dict, List

import httpx
from bs4 import BeautifulSoup

from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.social_discovery")


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------
@dataclass
class SocialProfiles:
    """Container for all social media URLs found for a single lead."""
    youtube_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    facebook_url: Optional[str] = None
    telegram_url: Optional[str] = None
    twitter_url: Optional[str] = None

    def is_empty(self) -> bool:
        return not any([
            self.youtube_url, self.linkedin_url, self.tiktok_url,
            self.facebook_url, self.telegram_url, self.twitter_url,
        ])

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "youtube_url": self.youtube_url,
            "linkedin_url": self.linkedin_url,
            "tiktok_url": self.tiktok_url,
            "facebook_url": self.facebook_url,
            "telegram_url": self.telegram_url,
            "twitter_url": self.twitter_url,
        }

    def apply_to_lead(self, lead) -> None:
        """Apply these profiles to a SQLModel Lead instance (only sets fields that
        are currently None so we don't overwrite a known-good value)."""
        for field, value in self.to_dict().items():
            if value and getattr(lead, field, None) in (None, ""):
                setattr(lead, field, value)


# ---------------------------------------------------------------------------
# Platform-specific helpers (each tries site: query first, then a fallback)
# ---------------------------------------------------------------------------

# Per-platform structural pages to ignore when extracting handles.
_PLATFORM_IGNORE = {
    "youtube.com": {
        "watch", "results", "channel_switcher", "feed", "playlist",
        "premium", "movies", "gaming", "live", "trending", "music",
        "news", "sports", "learning", "creators", "kids", "about",
        "press", "copyright", "contact", "creators-for-change",
        "terms", "privacy", "policy", "safety", "howyoutubeworks",
    },
    "linkedin.com": {
        "feed", "messaging", "jobs", "games", "learning", "premium",
        "sales", "marketing", "talent", "publishing", "pulse",
        "posts", "company", "directory", "learning", "school",
        "in", "login", "signup", "about", "help", "legal",
    },
    "tiktok.com": {
        "foryou", "following", "live", "explore", "discover",
        "shop", "music", "newsroom", "about", "creators",
        "login", "signup", "embed", "discover", "search",
        "tiktok.com", "legal", "privacy", "terms",
    },
    "facebook.com": {
        "login", "signup", "recover", "help", "policies",
        "privacy", "terms", "cookies", "ads", "settings",
        "marketplace", "gaming", "watch", "groups", "events",
        "pages", "stories", "reels", "messages", "bookmarks",
        "fundraisers", "offers", "jobs", "memorial",
    },
    "t.me": set(),  # Telegram links are basically all just /s/ or /username
    "x.com": {
        "home", "explore", "notifications", "messages", "bookmarks",
        "lists", "profile", "more", "compose", "search",
        "i", "intent", "share",
    },
    "twitter.com": {
        "home", "explore", "notifications", "messages", "bookmarks",
        "lists", "profile", "more", "compose", "search",
        "i", "intent", "share",
    },
}


def _clean_url(url: str) -> str:
    """Strip utm params, trailing slashes, hash fragments."""
    if not url:
        return url
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return url
    # Drop tracking query params
    tracking = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                "utm_content", "fbclid", "gclid", "ref", "src"}
    if parsed.query:
        pairs = []
        for kv in parsed.query.split("&"):
            if "=" in kv:
                k = kv.split("=", 1)[0]
                if k.lower() in tracking:
                    continue
            pairs.append(kv)
        query = "&".join(pairs)
    else:
        query = ""
    cleaned = urllib.parse.urlunparse((
        parsed.scheme or "https",
        parsed.netloc,
        parsed.path.rstrip("/") if parsed.path != "/" else parsed.path,
        parsed.params, query, "",
    ))
    return cleaned


def _handle_slug(url: str) -> str:
    """Extract a normalized slug from a profile URL for cross-platform dedup.

    Strips separators and lowercases so e.g. ``acme-corp`` and ``acme.corp``
    and ``AcmeCorp`` collapse to the same key.
    """
    if not url:
        return ""
    try:
        path = urllib.parse.urlparse(url).path
    except Exception:
        return ""
    slug = path.strip("/").split("/")[-1] if path.strip("/") else ""
    slug = re.sub(r"^(in|company|pg|c|user|channel|s|@)", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "", slug.lower())
    return slug


def _duckduckgo_links(html: str) -> List[str]:
    """Extract the real destination URLs from a DuckDuckGo HTML results page.

    DuckDuckGo wraps results in a redirect URL like
    ``//duckduckgo.com/l/?uddg=https%3A%2F%2F...&...``. We decode those,
    filter to http(s) URLs, and return the de-duplicated list preserving order.
    """
    out: List[str] = []
    seen: set = set()
    for href in re.findall(r'href="([^"]+)"', html or ""):
        url = urllib.parse.unquote(href)
        # Convert DDG redirect URLs to the real destination.
        if "uddg=" in url:
            try:
                url = url.split("uddg=", 1)[1].split("&", 1)[0]
                url = urllib.parse.unquote(url)
            except Exception:
                pass
        if not url or not url.startswith(("http://", "https://")):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


def _domain_of(url: str) -> str:
    try:
        return (urllib.parse.urlparse(url).netloc or "").lower()
    except Exception:
        return ""


def _matches_platform(url: str, platform_domain: str) -> bool:
    """Return True if *url* is on *platform_domain* (handles www. prefix)."""
    dom = _domain_of(url)
    plat = platform_domain.lower()
    return dom == plat or dom.endswith("." + plat)


# Regex used to extract the slug / handle / ID for each platform.
_PLATFORM_HANDLE_PATTERNS: Dict[str, re.Pattern] = {
    "youtube.com": re.compile(r"youtube\.com/(?:@|c/|channel/|user/)?([A-Za-z0-9_\-]{2,})", re.IGNORECASE),
    "linkedin.com": re.compile(r"linkedin\.com/(?:in|company)/([A-Za-z0-9_\-]{2,})", re.IGNORECASE),
    "tiktok.com":   re.compile(r"tiktok\.com/(?:@)?([A-Za-z0-9_\-\.]{2,})", re.IGNORECASE),
    "facebook.com": re.compile(r"facebook\.com/(?:pg/)?([A-Za-z0-9_\-\.]{2,})", re.IGNORECASE),
    "t.me":         re.compile(r"t\.me/(?:s/)?([A-Za-z0-9_\-]{2,})", re.IGNORECASE),
    "x.com":        re.compile(r"(?:x|twitter)\.com/([A-Za-z0-9_\-]{2,})", re.IGNORECASE),
    "twitter.com":  re.compile(r"(?:x|twitter)\.com/([A-Za-z0-9_\-]{2,})", re.IGNORECASE),
}


def _is_valid_handle(platform: str, handle: str) -> bool:
    if not handle:
        return False
    handle = handle.strip().rstrip("/")
    if len(handle) < 2 or len(handle) > 80:
        return False
    bad = _PLATFORM_IGNORE.get(platform, set())
    base = handle.split("?")[0].split("/")[0].lower()
    if base in bad:
        return False
    # Reject anything that looks like a non-profile path fragment.
    if base in {"watch", "v", "embed", "share", "post", "posts",
                "video", "photo", "photos", "reel", "story",
                "stories", "status", "permalink", "events",
                "groups", "hashtag", "p"}:
        return False
    if not re.search(r"[A-Za-z_]", base):
        return False
    if re.search(r"\s", base):
        return False
    if base.startswith((".", "-", "_")) or base.endswith((".", "-", "_")):
        return False
    return True


def _normalize_url(platform: str, handle: str, business_name: str) -> str:
    """Build the canonical profile URL from a raw handle/URL."""
    handle = (handle or "").strip().rstrip("/")
    if not handle:
        return ""
    # If a full URL was already extracted, just clean it.
    if handle.startswith(("http://", "https://")):
        return _clean_url(handle)
    handle = handle.lstrip("@")
    if not handle:
        return ""

    pretty = platform
    if platform == "youtube.com":
        return _clean_url(f"https://www.youtube.com/@{handle}")
    if platform == "linkedin.com":
        # We can't tell from a slug alone if it's a person or a company;
        # the search helper will have set the right path already.
        if handle.startswith("in/") or handle.startswith("company/"):
            return _clean_url(f"https://www.linkedin.com/{handle}")
        return _clean_url(f"https://www.linkedin.com/in/{handle}")
    if platform == "tiktok.com":
        return _clean_url(f"https://www.tiktok.com/@{handle}")
    if platform == "facebook.com":
        return _clean_url(f"https://www.facebook.com/{handle}")
    if platform == "t.me":
        return _clean_url(f"https://t.me/{handle}")
    if platform in ("x.com", "twitter.com"):
        return _clean_url(f"https://x.com/{handle}")
    return _clean_url(f"https://www.{platform}/{handle}")


# ---------------------------------------------------------------------------
# DuckDuckGo / Google search helpers
# ---------------------------------------------------------------------------

def _build_query(business_name: str, location: str, platform: str) -> str:
    loc = (location or "").strip()
    if platform == "youtube.com":
        return f'site:youtube.com "{business_name}" {loc}'.strip()
    if platform == "linkedin.com":
        return f'site:linkedin.com "{business_name}" {loc}'.strip()
    if platform == "tiktok.com":
        return f'site:tiktok.com "{business_name}" {loc}'.strip()
    if platform == "facebook.com":
        return f'site:facebook.com "{business_name}" {loc}'.strip()
    if platform == "t.me":
        # Telegram doesn't have a great site: query — use t.me/<slug>
        return f'"{business_name}" {loc} t.me'.strip()
    if platform in ("x.com", "twitter.com"):
        return f'site:x.com OR site:twitter.com "{business_name}" {loc}'.strip()
    return f'site:{platform} "{business_name}" {loc}'.strip()


def _google_cse_search(query: str, num: int = 5) -> List[str]:
    """Run a Google Custom Search query and return the result URLs."""
    api_key = settings.google_custom_search_api_key
    cx = settings.google_custom_search_cx
    if not api_key or not cx:
        return []
    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {"key": str(api_key), "cx": str(cx), "q": query, "num": str(num)}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url, params=params)
        if r.status_code != 200:
            logger.debug(f"Google CSE returned {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
        return [item.get("link", "") for item in data.get("items", []) if item.get("link")]
    except Exception as e:
        logger.debug(f"Google CSE search failed for '{query}': {e}")
        return []


def _duckduckgo_search(query: str, num: int = 8) -> List[str]:
    """DuckDuckGo HTML search (no key required). Returns up to *num* URLs."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True, headers=headers) as client:
            r = client.get(url)
        if r.status_code != 200:
            logger.debug(f"DDG returned {r.status_code} for query: {query}")
            return []
        # Some responses use HTML5 parser; we just need hrefs.
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            # The redirect wrapper hrefs are in result__a tags.
            for a in soup.find_all("a", class_="result__a"):
                href = a.get("href", "")
                if href:
                    pass  # already extracted by regex below
        except Exception:
            pass
        return _duckduckgo_links(r.text)[:num]
    except Exception as e:
        logger.debug(f"DDG search failed for '{query}': {e}")
        return []


# ---------------------------------------------------------------------------
# Per-platform finders
# ---------------------------------------------------------------------------

class _BaseFinder:
    platform: str = ""
    pattern: Optional[re.Pattern] = None

    def __init__(self):
        if not self.pattern:
            self.pattern = _PLATFORM_HANDLE_PATTERNS.get(self.platform)

    # Subclasses may override the query to avoid site: when it doesn't work.
    def build_query(self, business_name: str, location: str) -> str:
        return _build_query(business_name, location, self.platform)

    def build_queries(self, business_name: str, location: str) -> List[str]:
        """Return a list of search query variants to try. Override in subclasses
        that want to broaden the search (e.g. add a "{name} {location} <platform>"
        fallback when site: doesn't yield results)."""
        return [self.build_query(business_name, location)]

    def matches(self, url: str) -> bool:
        return _matches_platform(url, self.platform)

    def extract_handle(self, url: str) -> Optional[str]:
        if not self.pattern:
            return None
        m = self.pattern.search(url)
        if not m:
            return None
        handle = m.group(1)
        if not _is_valid_handle(self.platform, handle):
            return None
        return handle

    def find(self, business_name: str, location: str) -> Optional[str]:
        if not business_name:
            return None
        queries = self.build_queries(business_name, location)
        seen_urls: set = set()

        for query in queries:
            candidates: List[str] = []
            try:
                candidates.extend(_google_cse_search(query))
            except Exception as e:
                logger.debug(f"Google CSE threw for platform {self.platform}: {e}")

            if not candidates:
                candidates.extend(_duckduckgo_search(query))

            for url in candidates:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                if not self.matches(url):
                    continue
                handle = self.extract_handle(url)
                if handle:
                    return _normalize_url(self.platform, handle, business_name)
        return None


class YouTubeFinder(_BaseFinder):
    platform = "youtube.com"

    def build_queries(self, business_name: str, location: str) -> List[str]:
        loc = (location or "").strip()
        return [
            f'site:youtube.com "{business_name}" {loc}'.strip(),
            f'site:youtube.com "{business_name}"',
            f'"{business_name}" {loc} youtube'.strip(),
        ]

    def extract_handle(self, url: str) -> Optional[str]:
        # YouTube sometimes exposes /channel/<id> (UCxxx) which is a real
        # channel but isn't a human-friendly handle. Prefer @handle when present.
        m = re.search(r"youtube\.com/@([A-Za-z0-9_\-\.]{2,})", url)
        if m and _is_valid_handle(self.platform, m.group(1)):
            return m.group(1)
        m = re.search(r"youtube\.com/(?:c|user)/([A-Za-z0-9_\-\.]{2,})", url, re.IGNORECASE)
        if m and _is_valid_handle(self.platform, m.group(1)):
            return m.group(1)
        m = re.search(r"youtube\.com/channel/([A-Za-z0-9_\-]{2,})", url, re.IGNORECASE)
        if m and _is_valid_handle(self.platform, m.group(1)):
            return m.group(1)
        return None


class LinkedInFinder(_BaseFinder):
    platform = "linkedin.com"

    def build_queries(self, business_name: str, location: str) -> List[str]:
        loc = (location or "").strip()
        return [
            f'site:linkedin.com "{business_name}" {loc}'.strip(),
            f'site:linkedin.com "{business_name}"',
            f'site:linkedin.com/company "{business_name}"',
            f'"{business_name}" {loc} linkedin'.strip(),
        ]

    def extract_handle(self, url: str) -> Optional[str]:
        # We accept /in/<slug> and /company/<slug>. Decide based on URL.
        m = re.search(r"linkedin\.com/(in|company)/([A-Za-z0-9_\-]{2,})", url, re.IGNORECASE)
        if not m:
            return None
        kind, slug = m.group(1).lower(), m.group(2)
        if not _is_valid_handle(self.platform, slug):
            return None
        return f"{kind}/{slug}"


class TikTokFinder(_BaseFinder):
    platform = "tiktok.com"

    def build_queries(self, business_name: str, location: str) -> List[str]:
        loc = (location or "").strip()
        return [
            f'site:tiktok.com "{business_name}" {loc}'.strip(),
            f'site:tiktok.com "{business_name}"',
            f'"{business_name}" {loc} tiktok'.strip(),
        ]

    def extract_handle(self, url: str) -> Optional[str]:
        m = re.search(r"tiktok\.com/@([A-Za-z0-9_\-\.]{2,})", url, re.IGNORECASE)
        if m and _is_valid_handle(self.platform, m.group(1)):
            return m.group(1)
        return None


class FacebookFinder(_BaseFinder):
    platform = "facebook.com"

    def build_queries(self, business_name: str, location: str) -> List[str]:
        loc = (location or "").strip()
        return [
            f'site:facebook.com "{business_name}" {loc}'.strip(),
            f'site:facebook.com "{business_name}"',
            f'"{business_name}" {loc} facebook'.strip(),
        ]

    def extract_handle(self, url: str) -> Optional[str]:
        # Reject non-profile paths
        bad_prefixes = (
            "login", "signup", "recover", "help", "policies", "privacy",
            "terms", "cookies", "ads", "settings", "marketplace",
            "gaming", "watch", "groups", "events", "pages", "stories",
            "reels", "messages", "bookmarks", "fundraisers", "offers",
            "jobs", "memorial", "share", "photo", "photo.php", "permalink",
        )
        m = re.search(r"facebook\.com/(?:pg/)?([A-Za-z0-9_\-\.]{2,})", url, re.IGNORECASE)
        if not m:
            return None
        slug = m.group(1)
        if slug.lower() in bad_prefixes or "/" in slug:
            return None
        if not _is_valid_handle(self.platform, slug):
            return None
        return slug


class TelegramFinder(_BaseFinder):
    platform = "t.me"

    def build_query(self, business_name: str, location: str) -> str:
        # Telegram doesn't expose a useful site: operator — use plain search
        # with a quoted business name and the t.me hint.
        return f'"{business_name}" {location or ""} t.me'.strip()

    def build_queries(self, business_name: str, location: str) -> List[str]:
        loc = (location or "").strip()
        return [
            f'"{business_name}" {loc} t.me'.strip(),
            f'"{business_name}" t.me telegram',
            f'"{business_name}" telegram',
        ]

    def extract_handle(self, url: str) -> Optional[str]:
        m = re.search(r"t\.me/(?:s/)?([A-Za-z0-9_]{4,})", url, re.IGNORECASE)
        if not m:
            return None
        slug = m.group(1)
        if not _is_valid_handle(self.platform, slug):
            return None
        return slug


class XTwitterFinder(_BaseFinder):
    platform = "x.com"

    def matches(self, url: str) -> bool:
        # Match both x.com and twitter.com since X posts still resolve there.
        return _matches_platform(url, "x.com") or _matches_platform(url, "twitter.com")

    def build_queries(self, business_name: str, location: str) -> List[str]:
        loc = (location or "").strip()
        return [
            f'site:x.com OR site:twitter.com "{business_name}" {loc}'.strip(),
            f'site:x.com "{business_name}"',
            f'"{business_name}" {loc} twitter'.strip(),
        ]

    def extract_handle(self, url: str) -> Optional[str]:
        m = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]{2,15})", url, re.IGNORECASE)
        if not m:
            return None
        handle = m.group(1)
        if not _is_valid_handle(self.platform, handle):
            return None
        return handle


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

class SocialDiscovery:
    """
    Coordinates per-platform finders.

    The orchestrator (research pipeline) calls ``discover_all()`` after
    scraping a lead's website, or as a stand-alone enrichment pass.
    """

    def __init__(self):
        self._finders = {
            "youtube_url": YouTubeFinder(),
            "linkedin_url": LinkedInFinder(),
            "tiktok_url": TikTokFinder(),
            "facebook_url": FacebookFinder(),
            "telegram_url": TelegramFinder(),
            "twitter_url": XTwitterFinder(),
        }

    # --- public ----------------------------------------------------------
    def find_one(self, platform: str, business_name: str, location: str) -> Optional[str]:
        """Look up a single platform. Returns a normalized URL or None."""
        for field, finder in self._finders.items():
            if field.endswith(platform + "_url") or platform in field:
                try:
                    return finder.find(business_name, location)
                except Exception as e:
                    logger.debug(f"finder for {platform} failed: {e}")
                    return None
        return None

    async def discover_all(
        self, business_name: str, location: str, existing: Optional[Dict[str, Optional[str]]] = None
    ) -> SocialProfiles:
        """
        Run every per-platform finder in sequence. Already-known URLs in
        *existing* are not re-fetched (saves time and avoids hammering the
        search engines). Returns a SocialProfiles populated with whatever
        the finders could resolve.
        """
        if not business_name:
            return SocialProfiles()
        existing = existing or {}
        results: Dict[str, Optional[str]] = {}

        for field, finder in self._finders.items():
            if existing.get(field):
                results[field] = existing[field]
                continue
            try:
                url = finder.find(business_name, location or "")
            except Exception as e:
                logger.debug(f"{field} discovery failed: {e}")
                url = None
            results[field] = url

        results = self._dedup_by_business(results)

        return SocialProfiles(
            youtube_url=results.get("youtube_url"),
            linkedin_url=results.get("linkedin_url"),
            tiktok_url=results.get("tiktok_url"),
            facebook_url=results.get("facebook_url"),
            telegram_url=results.get("telegram_url"),
            twitter_url=results.get("twitter_url"),
        )

    # Synchronous convenience for callers that don't want to await async.
    def discover_all_sync(
        self, business_name: str, location: str, existing: Optional[Dict[str, Optional[str]]] = None
    ) -> SocialProfiles:
        if not business_name:
            return SocialProfiles()
        existing = existing or {}
        results: Dict[str, Optional[str]] = {}
        for field, finder in self._finders.items():
            if existing.get(field):
                results[field] = existing[field]
                continue
            try:
                results[field] = finder.find(business_name, location or "")
            except Exception as e:
                logger.debug(f"{field} sync discovery failed: {e}")
                results[field] = None

        results = self._dedup_by_business(results)

        return SocialProfiles(
            youtube_url=results.get("youtube_url"),
            linkedin_url=results.get("linkedin_url"),
            tiktok_url=results.get("tiktok_url"),
            facebook_url=results.get("facebook_url"),
            telegram_url=results.get("telegram_url"),
            twitter_url=results.get("twitter_url"),
        )

    @staticmethod
    def _dedup_by_business(results: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """Drop profile URLs that share a normalized slug across different
        platforms. The first-encountered (in field iteration order) wins.
        This prevents e.g. ``facebook.com/acme-corp`` and ``twitter.com/acme``
        from both being reported when the search engine matched the same
        underlying business on two different platforms.
        """
        seen_slugs: set = set()
        for field, url in list(results.items()):
            if not url:
                continue
            slug = _handle_slug(url)
            if not slug:
                continue
            if slug in seen_slugs:
                logger.debug(
                    f"social_discovery dedup: dropping {field}={url} "
                    f"(slug '{slug}' already assigned to a previous platform)"
                )
                results[field] = None
                continue
            seen_slugs.add(slug)
        return results

    # --- helpers for callers that want one platform at a time -------------
    def find_youtube(self, business_name: str, location: str) -> Optional[str]:
        return self._finders["youtube_url"].find(business_name, location)

    def find_linkedin(self, business_name: str, location: str) -> Optional[str]:
        return self._finders["linkedin_url"].find(business_name, location)

    def find_tiktok(self, business_name: str, location: str) -> Optional[str]:
        return self._finders["tiktok_url"].find(business_name, location)

    def find_facebook(self, business_name: str, location: str) -> Optional[str]:
        return self._finders["facebook_url"].find(business_name, location)

    def find_telegram(self, business_name: str, location: str) -> Optional[str]:
        return self._finders["telegram_url"].find(business_name, location)

    def find_twitter(self, business_name: str, location: str) -> Optional[str]:
        return self._finders["twitter_url"].find(business_name, location)
