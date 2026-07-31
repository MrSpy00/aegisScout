"""
Tikla.com.tr Discovery Provider for aegisScout.

Tikla.com.tr is a large Turkish directory with 4,500+ categories covering
healthcare, restaurants, retail, local services and more.

URL patterns:
  - Category listing: https://www.tikla.com.tr/sektorler/{slug}
  - Paginated:        https://www.tikla.com.tr/sektorler/{slug}?sayfa={N}
  - Search:           https://www.tikla.com.tr/arama?q={keyword}&il={city}
  - Detail:           https://www.tikla.com.tr/firma/{slug}-{id}

Anti-scraping notes:
  - Low/medium protection — standard httpx + BeautifulSoup works
  - HTTP 429 on rapid fire; use 1.5-3s delays
  - Static HTML rendering; no JS required
"""
from __future__ import annotations

import asyncio
import random
import re
from typing import List, Optional, Set

import httpx
from bs4 import BeautifulSoup

from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.discovery.sector_mapper import get_slug_or_auto
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.tikla")

_BASE_URL = "https://www.tikla.com.tr"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com.tr/",
}

_MAX_PAGES = 8
_PAGE_DELAY = (1.5, 3.0)
_HTTP_TIMEOUT = 18.0


def _rand_delay() -> float:
    return random.uniform(*_PAGE_DELAY)


def _clean_phone(raw: str) -> Optional[str]:
    digits = re.sub(r"\D", "", raw)
    return digits if len(digits) >= 10 else None


class TiklaDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that scrapes tikla.com.tr category and search pages
    to extract Turkish business leads across thousands of sectors.
    """

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Tikla.com.tr: searching '{sector}' in '{location}'...")
        slug = get_slug_or_auto(sector, "tikla")
        candidates: List[LeadCandidate] = []
        seen: Set[str] = set()

        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            # Strategy 1: Category listing pages
            for page in range(1, _MAX_PAGES + 1):
                page_cands = await self._scrape_category_page(
                    client, slug, sector, location, page
                )
                if not page_cands:
                    break
                for c in page_cands:
                    key = c.business_name.lower().strip()
                    if key not in seen:
                        seen.add(key)
                        candidates.append(c)
                await asyncio.sleep(_rand_delay())

            # Strategy 2: Search with keyword + city
            if location and location.lower() not in ("türkiye", "turkey", ""):
                search_cands = await self._scrape_search_results(
                    client, sector, location
                )
                for c in search_cands:
                    key = c.business_name.lower().strip()
                    if key not in seen:
                        seen.add(key)
                        candidates.append(c)

        logger.info(
            f"Tikla: finished. Found {len(candidates)} leads for '{sector}' in '{location}'"
        )
        return candidates

    async def _scrape_category_page(
        self,
        client: httpx.AsyncClient,
        slug: str,
        sector: str,
        location: str,
        page: int,
    ) -> List[LeadCandidate]:
        """Scrape a category listing page."""
        if page == 1:
            url = f"{_BASE_URL}/sektorler/{slug}"
        else:
            url = f"{_BASE_URL}/sektorler/{slug}?sayfa={page}"

        return await self._parse_listing_page(client, url, sector, location)

    async def _scrape_search_results(
        self,
        client: httpx.AsyncClient,
        sector: str,
        location: str,
    ) -> List[LeadCandidate]:
        """Search by keyword and city."""
        import urllib.parse
        url = (
            f"{_BASE_URL}/arama?"
            f"q={urllib.parse.quote(sector)}&il={urllib.parse.quote(location)}"
        )
        return await self._parse_listing_page(client, url, sector, location)

    async def _parse_listing_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        sector: str,
        location: str,
    ) -> List[LeadCandidate]:
        """Parse a single tikla.com.tr listing page."""
        candidates: List[LeadCandidate] = []
        try:
            resp = await client.get(url)
            if resp.status_code == 429:
                logger.warning("Tikla: rate limited (429). Waiting extra 5s...")
                await asyncio.sleep(5)
                return []
            if resp.status_code != 200:
                logger.debug(f"Tikla HTTP {resp.status_code}: {url}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")

            # Multiple container selectors
            items = (
                soup.select(".firma-card")
                or soup.select(".sector-item")
                or soup.select("article.business-entry")
                or soup.select(".firm-item")
                or soup.select(".listing-item")
                or soup.select(".card.firma")
            )

            if not items:
                logger.debug(f"Tikla: no items found at {url}")
                return []

            for item in items:
                c = self._parse_item(item, sector, location)
                if c:
                    candidates.append(c)

        except Exception as e:
            logger.warning(f"Tikla listing error ({url}): {e}")

        return candidates

    def _parse_item(self, item, sector: str, location: str) -> Optional[LeadCandidate]:
        """Parse a single business listing card."""
        # ── Name ──────────────────────────────────────────────────────────────
        name_tag = (
            item.select_one("h3.firma-title a")
            or item.select_one(".business-name a")
            or item.select_one("h3 a")
            or item.select_one("h2 a")
            or item.select_one("a.firma-link")
            or item.select_one(".title a")
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
            or item.select_one("a.phone-btn")
            or item.select_one(".tel-no")
        )
        if tel_tag:
            href = tel_tag.get("href", "")
            if href.startswith("tel:"):
                phone = _clean_phone(href.replace("tel:", ""))
            if not phone:
                phone = _clean_phone(tel_tag.get_text())

        # ── Address ───────────────────────────────────────────────────────────
        address: Optional[str] = None
        addr_tag = (
            item.select_one(".firma-address")
            or item.select_one(".location-text")
            or item.select_one("address")
            or item.select_one(".adres")
        )
        if addr_tag:
            address = addr_tag.get_text(separator=" ", strip=True)

        # ── Website ───────────────────────────────────────────────────────────
        website: Optional[str] = None
        web_tag = (
            item.select_one("a.web-site-link")
            or item.select_one("a[href*='http'][rel='nofollow']:not([href*='tikla.com.tr'])")
        )
        if web_tag:
            website = web_tag.get("href", "").strip()
            if website and not website.startswith("http"):
                website = None

        return LeadCandidate(
            business_name=name,
            sector=sector,
            phone=phone,
            address=address or location,
            website_url=website,
            has_website=bool(website),
            source="tikla",
        )
