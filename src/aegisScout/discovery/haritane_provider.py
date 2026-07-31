"""
Haritane.com Discovery Provider for aegisScout.

Haritane.com is a Turkish map-focused business directory ("Nerede Ne Aramıştınız?")
that provides business listings WITH GPS coordinates — making it the best source
for populating the aegisScout interactive map.

URL patterns:
  - Category: https://haritane.com/kategori/{slug}
  - Paginated: https://haritane.com/kategori/?utm_content={slug}-page-{N}
  - Location+sector: https://haritane.com/{city-slug}/{sector-slug}
  - Detail: https://haritane.com/{business-slug}-{id}.html

Anti-scraping notes:
  - ModSecurity / WAF present; realistic headers with tr-TR Accept-Language required
  - Static HTML — no JS rendering needed for listing pages
  - 2-3s delays between requests
"""
from __future__ import annotations

import asyncio
import random
import re
import urllib.parse
from typing import List, Optional, Set, Tuple

import httpx
from bs4 import BeautifulSoup

from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.discovery.sector_mapper import get_slug_or_auto, auto_slugify
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.haritane")

_BASE_URL = "https://haritane.com"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com.tr/",
    "Connection": "keep-alive",
}

_MAX_PAGES = 10
_PAGE_DELAY = (1.5, 3.0)
_HTTP_TIMEOUT = 20.0

# Regex to pull lat/lon from embedded Google Maps iframes or data attributes
_LAT_LON_RE = re.compile(
    r'(?:lat|latitude)["\s:=]+([+-]?\d{1,3}\.\d+)[^|]*'
    r'(?:lng|lon|longitude)["\s:=]+([+-]?\d{1,3}\.\d+)',
    re.IGNORECASE,
)
_GMAPS_RE = re.compile(
    r"maps\.google\.com/maps\?.*?q=([+-]?\d{1,3}\.\d+),([+-]?\d{1,3}\.\d+)",
    re.IGNORECASE,
)
_EMBED_RE = re.compile(
    r"!2d([+-]?\d{1,3}\.\d+)!3d([+-]?\d{1,3}\.\d+)",
    re.IGNORECASE,
)


def _rand_delay() -> float:
    return random.uniform(*_PAGE_DELAY)


def _clean_phone(raw: str) -> Optional[str]:
    digits = re.sub(r"\D", "", raw)
    return digits if len(digits) >= 10 else None


def _extract_lat_lon(html: str) -> Tuple[Optional[float], Optional[float]]:
    """Try to extract GPS coordinates from various embedded map patterns."""
    for pattern in (_LAT_LON_RE, _EMBED_RE, _GMAPS_RE):
        m = pattern.search(html)
        if m:
            try:
                lat = float(m.group(1))
                lon = float(m.group(2))
                # Sanity check: Turkey bounding box
                if 36.0 <= lat <= 42.5 and 26.0 <= lon <= 45.0:
                    return lat, lon
            except (ValueError, IndexError):
                pass
    return None, None


def _city_to_slug(location: str) -> str:
    """Convert a city/district name to URL-safe slug."""
    return auto_slugify(location).replace("-", "-")


class HaritaneDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that scrapes haritane.com for Turkish business leads,
    including GPS coordinates for use in the interactive map view.
    """

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Haritane.com: searching '{sector}' in '{location}'...")
        slug = get_slug_or_auto(sector, "haritane")
        candidates: List[LeadCandidate] = []
        seen_names: Set[str] = set()

        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            # Strategy 1: Category page with location prefix
            if location and location.lower() not in ("türkiye", "turkey", ""):
                city_slug = _city_to_slug(location)
                loc_candidates = await self._scrape_location_category(
                    client, city_slug, slug, sector, location
                )
                for c in loc_candidates:
                    key = c.business_name.lower().strip()
                    if key not in seen_names:
                        seen_names.add(key)
                        candidates.append(c)

            # Strategy 2: General category pages (Turkey-wide)
            for page in range(1, _MAX_PAGES + 1):
                page_candidates = await self._scrape_category_page(
                    client, slug, sector, location, page
                )
                if not page_candidates:
                    break
                for c in page_candidates:
                    key = c.business_name.lower().strip()
                    if key not in seen_names:
                        seen_names.add(key)
                        candidates.append(c)
                await asyncio.sleep(_rand_delay())

        logger.info(
            f"Haritane: finished. Found {len(candidates)} leads for '{sector}' in '{location}'"
        )
        return candidates

    async def _scrape_location_category(
        self,
        client: httpx.AsyncClient,
        city_slug: str,
        sector_slug: str,
        sector: str,
        location: str,
    ) -> List[LeadCandidate]:
        """Scrape location-specific category: haritane.com/{city}/{sector}"""
        url = f"{_BASE_URL}/{city_slug}-{sector_slug}"
        return await self._parse_listing_page(client, url, sector, location)

    async def _scrape_category_page(
        self,
        client: httpx.AsyncClient,
        slug: str,
        sector: str,
        location: str,
        page: int,
    ) -> List[LeadCandidate]:
        """Scrape a category listing page with pagination."""
        if page == 1:
            url = f"{_BASE_URL}/kategori/{slug}"
        else:
            url = f"{_BASE_URL}/kategori/?utm_content={slug}-page-{page}"

        return await self._parse_listing_page(client, url, sector, location)

    async def _parse_listing_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        sector: str,
        location: str,
    ) -> List[LeadCandidate]:
        """Parse a single haritane.com listing page and return candidates."""
        candidates: List[LeadCandidate] = []
        try:
            resp = await client.get(url)
            if resp.status_code not in (200,):
                logger.debug(f"Haritane HTTP {resp.status_code}: {url}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")

            # Try multiple container selectors
            items = (
                soup.select(".place-item")
                or soup.select(".harita-card")
                or soup.select(".listing-row")
                or soup.select("article.business-entry")
                or soup.select(".firm-box")
                or soup.select(".card")
            )

            if not items:
                logger.debug(f"Haritane: no listing items found at {url}")
                return []

            for item in items:
                candidate = self._parse_listing_item(item, sector, location, resp.text)
                if candidate:
                    candidates.append(candidate)

        except Exception as e:
            logger.warning(f"Haritane listing error ({url}): {e}")

        return candidates

    def _parse_listing_item(
        self,
        item,
        sector: str,
        location: str,
        full_html: str,
    ) -> Optional[LeadCandidate]:
        """Parse a single listing card."""
        # ── Name ──────────────────────────────────────────────────────────────
        name_tag = (
            item.select_one(".place-title a")
            or item.select_one("h2.entry-title")
            or item.select_one("h3 a")
            or item.select_one(".firm-name a")
            or item.select_one("a.title-link")
        )
        if not name_tag:
            return None
        name = name_tag.get_text(strip=True)
        if not name or len(name) < 2:
            return None

        # ── Phone ─────────────────────────────────────────────────────────────
        phone: Optional[str] = None
        tel_tag = (
            item.select_one("a[href^='tel:']")
            or item.select_one(".place-phone a")
            or item.select_one(".phone a")
        )
        if tel_tag:
            href = tel_tag.get("href", "")
            if href.startswith("tel:"):
                phone = re.sub(r"\D", "", href.replace("tel:", ""))
                if len(phone) < 10:
                    phone = None
        if not phone:
            phone_span = item.select_one(".place-phone, .tel-no, .phone")
            if phone_span:
                raw = phone_span.get_text(strip=True)
                cleaned = re.sub(r"\D", "", raw)
                if len(cleaned) >= 10:
                    phone = cleaned

        # ── Address ───────────────────────────────────────────────────────────
        address: Optional[str] = None
        addr_tag = (
            item.select_one(".place-address")
            or item.select_one("span.address")
            or item.select_one(".location-text")
            or item.select_one("address")
        )
        if addr_tag:
            address = addr_tag.get_text(separator=" ", strip=True)

        # ── Website ───────────────────────────────────────────────────────────
        website: Optional[str] = None
        web_tag = (
            item.select_one("a.place-website")
            or item.select_one("a.website-link")
            or item.select_one("a[href*='http'][target='_blank']:not([href*='haritane.com'])")
        )
        if web_tag:
            website = web_tag.get("href", "").strip()
            if website and not website.startswith("http"):
                website = None

        # ── GPS Coordinates ───────────────────────────────────────────────────
        lat: Optional[float] = None
        lon: Optional[float] = None

        # Try data attributes first (fastest)
        for attr in ("data-lat", "data-latitude", "data-lng", "data-lon"):
            val = item.get(attr) or item.select_one(f"[{attr}]")
            if val:
                try:
                    if attr in ("data-lat", "data-latitude"):
                        lat = float(val if isinstance(val, str) else val.get(attr, ""))
                    else:
                        lon = float(val if isinstance(val, str) else val.get(attr, ""))
                except (ValueError, AttributeError):
                    pass

        # Try embedded map URL in item HTML
        if lat is None or lon is None:
            item_html = str(item)
            lat, lon = _extract_lat_lon(item_html)

        candidate = LeadCandidate(
            business_name=name,
            sector=sector,
            phone=phone,
            address=address or location,
            website_url=website,
            has_website=bool(website),
            source="haritane",
        )
        # Store coordinates via extra fields
        if lat is not None:
            candidate.__dict__["_lat"] = lat
        if lon is not None:
            candidate.__dict__["_lon"] = lon

        return candidate
