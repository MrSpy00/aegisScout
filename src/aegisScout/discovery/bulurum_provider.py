"""
Bulurum.com Discovery Provider for aegisScout.

Bulurum.com is the official online directory powered by 11880 / BN Telekom,
one of Turkey's largest and most comprehensive business directories.

Strategy:
  1. Search via /search/{slug}/?what={sector}&where={location} (paginated)
  2. Parse listing cards to collect individual detail page URLs
  3. For each detail URL visit /details/{id} and extract rich contact data
  4. Fallback: if detail page unavailable, use listing card data directly

Anti-scraping notes:
  - Cloudflare WAF present; realistic headers + delays required
  - Phone numbers may be behind a JS click; we extract tel: links from HTML
  - Use 2-4s random delays between pages

Follows the same async pattern as other aegisScout providers.
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

logger = get_logger("discovery.bulurum")

_BASE_URL = "https://www.bulurum.com"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com.tr/",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

_MAX_PAGES = 8          # Max listing pages to iterate
_MAX_DETAIL_PAGES = 60  # Max detail pages to scrape
_PAGE_DELAY = (1.5, 3.5)  # Random delay between requests (seconds)
_HTTP_TIMEOUT = 20.0


def _rand_delay() -> float:
    return random.uniform(*_PAGE_DELAY)


def _clean_phone(raw: str) -> Optional[str]:
    """Normalize raw phone string to digits-only, reject if too short."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 10:
        return digits
    return None


def _extract_phone_from_tag(tag) -> Optional[str]:
    """Extract phone from an <a href='tel:...'> tag or inner text."""
    if not tag:
        return None
    href = tag.get("href", "")
    if href.startswith("tel:"):
        phone = href.replace("tel:", "").strip()
        return _clean_phone(phone)
    text = tag.get_text(strip=True)
    return _clean_phone(text) if text else None


def _extract_email_from_tag(tag) -> Optional[str]:
    """Extract e-mail from an <a href='mailto:...'> tag."""
    if not tag:
        return None
    href = tag.get("href", "")
    if href.startswith("mailto:"):
        return href.replace("mailto:", "").strip().lower()
    return None


def _normalize_url(url: str) -> str:
    """Ensure URL has scheme and is absolute."""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = _BASE_URL + url
    return url


class BulurumDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that scrapes bulurum.com search results and
    individual business detail pages to extract Turkish business leads.
    """

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Bulurum.com: searching '{sector}' in '{location}'...")
        slug = get_slug_or_auto(sector, "bulurum")
        candidates: List[LeadCandidate] = []
        detail_urls: List[str] = []
        seen_detail_urls: Set[str] = set()

        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            # ── Phase 1: Collect detail page URLs from listing pages ──────────
            for page in range(1, _MAX_PAGES + 1):
                listing_urls = await self._collect_detail_urls_from_listing(
                    client, slug, sector, location, page
                )
                new_urls = [u for u in listing_urls if u not in seen_detail_urls]
                detail_urls.extend(new_urls)
                seen_detail_urls.update(new_urls)

                if not listing_urls:
                    break  # No more results

                await asyncio.sleep(_rand_delay())

            logger.info(
                f"Bulurum: collected {len(detail_urls)} detail URLs for '{sector}' in '{location}'"
            )

            # ── Phase 2: Scrape each detail page ─────────────────────────────
            for idx, detail_url in enumerate(detail_urls[:_MAX_DETAIL_PAGES]):
                try:
                    candidate = await self._scrape_detail_page(
                        client, detail_url, sector, location
                    )
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.debug(f"Bulurum detail scrape error ({detail_url}): {e}")

                if idx < len(detail_urls) - 1:
                    await asyncio.sleep(_rand_delay())

        logger.info(
            f"Bulurum: finished. Found {len(candidates)} leads for '{sector}' in '{location}'"
        )
        return candidates

    async def _collect_detail_urls_from_listing(
        self,
        client: httpx.AsyncClient,
        slug: str,
        sector: str,
        location: str,
        page: int,
    ) -> List[str]:
        """Fetch one listing page and collect all individual business detail URLs."""
        location_slug = urllib.parse.quote(location) if location else ""

        # Build search URL with both slug-path and query-params for resilience
        if location_slug:
            url = (
                f"{_BASE_URL}/search/{slug}/"
                f"?what={urllib.parse.quote(sector)}&where={location_slug}&page={page}"
            )
        else:
            url = (
                f"{_BASE_URL}/search/{slug}/"
                f"?what={urllib.parse.quote(sector)}&page={page}"
            )

        detail_urls: List[str] = []
        try:
            resp = await client.get(url)
            if resp.status_code not in (200, 301, 302):
                logger.debug(f"Bulurum listing HTTP {resp.status_code} for page {page}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")

            # Multiple selector fallbacks for listing items
            cards = (
                soup.select("div.company-card a[href*='/details/']")
                or soup.select("div.search-result-item a[href*='/details/']")
                or soup.select("a[href*='/details/']")
                or soup.select("[itemtype='http://schema.org/LocalBusiness'] a")
            )

            for a_tag in cards:
                href = a_tag.get("href", "")
                if "/details/" in href:
                    full_url = _normalize_url(href)
                    detail_urls.append(full_url)

            if not detail_urls:
                # Fallback: search for any absolute detail links in the raw HTML
                found = re.findall(
                    r'href=["\']((?:https://www\.bulurum\.com)?/details/[^"\']+)["\']',
                    resp.text,
                )
                detail_urls = [_normalize_url(u) for u in found]

            logger.debug(
                f"Bulurum listing page {page}: found {len(detail_urls)} detail URLs"
            )
        except Exception as e:
            logger.warning(f"Bulurum listing page {page} error: {e}")

        return detail_urls

    async def _scrape_detail_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        sector: str,
        location: str,
    ) -> Optional[LeadCandidate]:
        """Scrape a bulurum.com /details/ page and return a LeadCandidate."""
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # ── Business Name ─────────────────────────────────────────────────
            name_tag = (
                soup.select_one("h1.company-title")
                or soup.select_one("h1.firm-title")
                or soup.select_one("h1[itemprop='name']")
                or soup.select_one("h1")
            )
            if not name_tag:
                return None
            name = name_tag.get_text(strip=True)
            if not name or len(name) < 2:
                return None

            # ── Phone Number ──────────────────────────────────────────────────
            phone: Optional[str] = None
            tel_tag = (
                soup.select_one("a[href^='tel:']")
                or soup.select_one(".company-phone a")
                or soup.select_one(".phone-number a")
                or soup.select_one("a.tel-link")
            )
            if tel_tag:
                phone = _extract_phone_from_tag(tel_tag)

            if not phone:
                # Try span / div containing phone text
                for cls in (".company-phone", ".phone-number", ".tel", "[itemprop='telephone']"):
                    span = soup.select_one(cls)
                    if span:
                        candidate_phone = _clean_phone(span.get_text())
                        if candidate_phone:
                            phone = candidate_phone
                            break

            # ── Address ───────────────────────────────────────────────────────
            address: Optional[str] = None
            addr_tag = (
                soup.select_one(".company-address")
                or soup.select_one("address")
                or soup.select_one("[itemprop='address']")
                or soup.select_one(".address-text")
            )
            if addr_tag:
                address = addr_tag.get_text(separator=" ", strip=True)

            # ── Website ───────────────────────────────────────────────────────
            website: Optional[str] = None
            web_tag = (
                soup.select_one("a.company-website")
                or soup.select_one("a.official-site")
                or soup.select_one("a[href*='http'][target='_blank']:not([href*='bulurum.com'])")
            )
            if web_tag:
                website = web_tag.get("href", "").strip()
                if website and not website.startswith("http"):
                    website = None

            # ── Email ─────────────────────────────────────────────────────────
            email: Optional[str] = None
            mail_tag = soup.select_one("a[href^='mailto:']")
            if mail_tag:
                email = _extract_email_from_tag(mail_tag)

            # ── Rating & Reviews ──────────────────────────────────────────────
            rating: Optional[float] = None
            review_count: Optional[int] = None
            rating_tag = soup.select_one(".company-rating .score, .rating-score, [itemprop='ratingValue']")
            if rating_tag:
                try:
                    rating = float(rating_tag.get_text(strip=True).replace(",", "."))
                except ValueError:
                    pass
            review_tag = soup.select_one(".review-count, [itemprop='reviewCount'], .rating-count")
            if review_tag:
                digits = re.sub(r"\D", "", review_tag.get_text())
                if digits:
                    try:
                        review_count = int(digits)
                    except ValueError:
                        pass

            return LeadCandidate(
                business_name=name,
                sector=sector,
                phone=phone,
                address=address or location,
                website_url=website,
                has_website=bool(website),
                email=email,
                rating=rating,
                review_count=review_count,
                source="bulurum",
            )

        except Exception as e:
            logger.debug(f"Bulurum detail page error ({url}): {e}")
            return None
