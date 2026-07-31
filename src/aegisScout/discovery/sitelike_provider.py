"""
Sitelike.org Discovery & OSINT Provider for aegisScout.

Sitelike.org provides domain similarity, competitor discovery, and website network mapping.
Used to discover similar business domains, alternative service providers, and related OSINT targets.

URL pattern:
  - https://www.sitelike.org/similar/{domain}/
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
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.sitelike")

_BASE_URL = "https://www.sitelike.org"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.sitelike.org/",
}

_HTTP_TIMEOUT = 15.0


def _clean_domain(raw_url: str) -> str:
    """Extract clean domain name from URL or raw string."""
    raw = raw_url.strip().lower()
    raw = re.sub(r"^https?://", "", raw)
    raw = re.sub(r"^www\.", "", raw)
    return raw.split("/")[0]


class SitelikeDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that queries sitelike.org for similar domain targets
    and competitor websites based on target domain or sector keywords.
    """

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Sitelike.org OSINT: searching related domains for sector '{sector}'...")
        candidates: List[LeadCandidate] = []
        target_domains: List[str] = []

        # If sector looks like a domain, search directly; otherwise check sector keywords
        if "." in sector and " " not in sector:
            target_domains.append(_clean_domain(sector))
        else:
            # Common Turkish directory & service seeds based on sector
            target_domains.extend([
                "bulurum.com",
                "find.com.tr",
                "tikla.com.tr",
                "haritane.com",
                "doktortakvimi.com",
                "doktorsitesi.com",
            ])

        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            for domain in target_domains[:2]:  # Limit query count
                try:
                    sitelike_url = f"{_BASE_URL}/similar/{domain}/"
                    resp = await client.get(sitelike_url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Extract list of similar sites
                    site_blocks = soup.select(".similar-site, .site-card, div[data-domain]")
                    for block in site_blocks:
                        domain_attr = block.get("data-domain") or ""
                        title_elem = block.select_one(".site-title, h3, a.title")
                        desc_elem = block.select_one(".site-desc, p.description")

                        rel_domain = domain_attr.strip() or (title_elem.get_text(strip=True) if title_elem else "")
                        if not rel_domain or "." not in rel_domain:
                            continue

                        rel_domain = _clean_domain(rel_domain)
                        desc = desc_elem.get_text(strip=True) if desc_elem else ""

                        # Check if description matches Turkish location or sector
                        c = LeadCandidate(
                            business_name=rel_domain.capitalize(),
                            sector=sector,
                            website_url=f"https://{rel_domain}",
                            has_website=True,
                            address=location if location else "Türkiye",
                        )
                        candidates.append(c)
                except Exception as e:
                    logger.debug(f"Sitelike scrape error for '{domain}': {e}")

        logger.info(f"Sitelike.org OSINT: discovered {len(candidates)} candidates.")
        return candidates
