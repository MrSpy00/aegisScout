"""
Find.com.tr Discovery Provider for aegisScout.

Find.com.tr is a Turkish business and professional directory with strong
coverage of healthcare providers, legal services, and local businesses.

URL patterns:
  - Search: https://www.find.com.tr/Search/{KEYWORD}
  - Search with city: https://www.find.com.tr/Search/{KEYWORD}?sehir={city}
  - Paginated: https://www.find.com.tr/Search/{KEYWORD}?page={N}
  - Detail: https://www.find.com.tr/Firma/{slug}-{id}

Anti-scraping notes:
  - Medium protection (IP rate limits, standard User-Agent filtering)
  - Static HTML — standard httpx + BeautifulSoup works
  - Use 2s+ delays to avoid HTTP 403/503
"""
from __future__ import annotations

import asyncio
import random
import re
import urllib.parse
from typing import List, Optional, Set

import httpx
from bs4 import BeautifulSoup

from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.discovery.sector_mapper import get_slug_or_auto
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.findcomtr")

_BASE_URL = "https://www.find.com.tr"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.find.com.tr/",
}

_MAX_PAGES = 6
_PAGE_DELAY = (2.0, 4.0)
_HTTP_TIMEOUT = 18.0


def _rand_delay() -> float:
    return random.uniform(*_PAGE_DELAY)


def _clean_phone(raw: str) -> Optional[str]:
    digits = re.sub(r"\D", "", raw)
    return digits if len(digits) >= 10 else None


class FindComTrDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that scrapes find.com.tr search results pages
    for Turkish business leads.
    """

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Find.com.tr: searching '{sector}' in '{location}'...")
        slug = get_slug_or_auto(sector, "find").upper()
        candidates: List[LeadCandidate] = []
        seen: Set[str] = set()

        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            for page in range(1, _MAX_PAGES + 1):
                page_cands = await self._scrape_page(
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

        logger.info(
            f"Find.com.tr: finished. Found {len(candidates)} leads for '{sector}' in '{location}'"
        )
        return candidates

    async def _scrape_page(
        self,
        client: httpx.AsyncClient,
        slug: str,
        sector: str,
        location: str,
        page: int,
    ) -> List[LeadCandidate]:
        """Fetch and parse one results page."""
        params: dict = {}
        if page > 1:
            params["page"] = page
        if location and location.lower() not in ("türkiye", "turkey", ""):
            params["sehir"] = location

        url = f"{_BASE_URL}/Search/{slug}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        candidates: List[LeadCandidate] = []
        try:
            resp = await client.get(url)
            if resp.status_code in (403, 503):
                logger.warning(f"Find.com.tr: blocked ({resp.status_code}) at {url}")
                return []
            if resp.status_code != 200:
                logger.debug(f"Find.com.tr HTTP {resp.status_code}: {url}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")

            # Multiple container selectors
            items = (
                soup.select(".search-item")
                or soup.select(".firma-kart")
                or soup.select(".list-group-item")
                or soup.select(".firm-card")
                or soup.select(".result-item")
            )

            if not items:
                logger.debug(f"Find.com.tr: no items at {url}")
                return []

            for item in items:
                c = self._parse_item(item, sector, location)
                if c:
                    candidates.append(c)

        except Exception as e:
            logger.warning(f"Find.com.tr page error ({url}): {e}")

        return candidates

    def _parse_item(self, item, sector: str, location: str) -> Optional[LeadCandidate]:
        """Parse a single search result card."""
        # ── Name ──────────────────────────────────────────────────────────────
        name_tag = (
            item.select_one(".firma-adi a")
            or item.select_one("h3.title")
            or item.select_one("h3 a")
            or item.select_one("a.firma-link")
            or item.select_one(".firm-name a")
            or item.select_one("a[href*='/Firma/']")
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
            or item.select_one(".firma-telefon a")
            or item.select_one(".phone-box span")
        )
        if tel_tag:
            href = tel_tag.get("href", "")
            if href.startswith("tel:"):
                phone = _clean_phone(href.replace("tel:", ""))
            if not phone:
                phone = _clean_phone(tel_tag.get_text())

        if not phone:
            phone_div = item.select_one(".firma-telefon, .phone-box")
            if phone_div:
                phone = _clean_phone(phone_div.get_text())

        # ── Address ───────────────────────────────────────────────────────────
        address: Optional[str] = None
        addr_tag = (
            item.select_one(".firma-adres")
            or item.select_one(".address-box")
            or item.select_one("address")
        )
        if addr_tag:
            address = addr_tag.get_text(separator=" ", strip=True)

        # ── Website ───────────────────────────────────────────────────────────
        website: Optional[str] = None
        web_tag = (
            item.select_one("a.firma-web")
            or item.select_one(".website-link")
            or item.select_one("a[href*='http'][target='_blank']:not([href*='find.com.tr'])")
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
            source="findcomtr",
        )
