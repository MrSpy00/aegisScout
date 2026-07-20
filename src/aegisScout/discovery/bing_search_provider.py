"""
Enhanced Bing Search Discovery Provider for aegisScout.
Scrapes Bing HTML search results to discover business leads.
Complements DuckDuckGo with additional result diversity and broader coverage.
Uses multiple query strategies and parallel execution for maximum yield.
"""
import urllib.parse
import re
import httpx
import asyncio
from typing import List, Optional, Set
from bs4 import BeautifulSoup
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.bing_search")


class BingSearchDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery Provider that searches Bing (HTML interface) to discover
    potential leads (websites and Instagram handles) without using Map APIs.
    Complements DuckDuckGo with additional result diversity.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        self.base_url = "https://www.bing.com/search"
        self._aggregate_patterns = [
            r"\b(en\s+iyi|top\s+\d+|sıralama|liste|listesi|rehber|directory)\b",
            r"\b(fiyatları|karşılaştırma|compare|blog|haber|article)\b",
        ]
        self._ignored_domains = [
            "bing.com", "microsoft.com", "yelp.com", "foursquare.com",
            "tripadvisor.com", "sahibinden.com", "hepsiemlak.com",
            "trendyol.com", "facebook.com", "twitter.com", "x.com",
            "linkedin.com", "youtube.com", "pinterest.com",
            "wikipedia.org", "wikimedia.org",
        ]

    def _clean_business_name(self, title: str) -> str:
        """Clean search result title to extract a neat business name."""
        name = title
        name = re.sub(r"^\d+\.\s*", "", name)
        name = re.sub(r"^[-\*\•]\s*", "", name)
        name = re.sub(r"\s*\(?@[\w_.-]+\)?", "", name)
        name = re.sub(
            r"\s*[|•-]\s*(Instagram|Facebook|Twitter|TikTok|LinkedIn|Web sitesi|Website|Yelp|Foursquare).*",
            "", name, flags=re.IGNORECASE
        )
        name = re.sub(
            r"\s*(photos and videos|Home|Profile|Giriş Yap|Giriş|Kaydol|Üye Ol|Ara).*$",
            "", name, flags=re.IGNORECASE
        )
        name = name.strip().strip("-|•_ ")
        return name

    def _extract_instagram_handle(self, url: str) -> Optional[str]:
        """Extract Instagram handle from an Instagram URL if valid."""
        match = re.match(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)", url)
        if match:
            handle = match.group(1).strip().lower()
            ignored = {
                "p", "explore", "stories", "reel", "reels", "developer",
                "about", "legal", "terms", "privacy", "accounts", "emails"
            }
            if handle and handle not in ignored:
                return handle
        return None

    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extract Turkish or international phone number from text."""
        patterns = [
            r"(\+?90\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2})",
            r"(0\s*[2-5]\d{2}\s*\d{3}\s*\d{2}\s*\d{2})",
            r"(\+?\d[\d\s\-\.]{8,}\d)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                phone = m.group(1).strip()
                if len(re.sub(r"\D", "", phone)) >= 10:
                    return phone
        return None

    def _extract_email_from_text(self, text: str) -> Optional[str]:
        """Extract email from text."""
        m = re.search(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text)
        return m.group(1).strip() if m else None

    async def _search_query(self, query: str, sector: str) -> List[LeadCandidate]:
        """Execute a single Bing search query and parse results."""
        candidates = []
        params = {
            "q": query,
            "count": "50",
            "setlang": "tr-TR",
            "mkt": "tr-TR",
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"Bing search returned status {resp.status_code} for query: {query}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")

                # Bing result items are in li.b_algo
                results = soup.find_all("li", class_="b_algo")
                if not results:
                    # Fallback: try h2 > a links
                    results = soup.find_all("h2")

                for r in results:
                    # Find the main link
                    link_tag = r.find("a") if r.name != "a" else r
                    if not link_tag:
                        continue

                    title = link_tag.get_text(strip=True)
                    href = link_tag.get("href", "")

                    if not href or not href.startswith("http"):
                        continue

                    # Ignore common directory/noise domains
                    url_lower = href.lower()
                    if "instagram.com" not in url_lower:
                        if any(domain in url_lower for domain in self._ignored_domains):
                            continue

                    # Filter aggregate/list pages
                    title_lower = title.lower()
                    if any(re.search(p, title_lower) for p in self._aggregate_patterns):
                        continue

                    business_name = self._clean_business_name(title)
                    if not business_name or len(business_name) < 3:
                        continue

                    instagram_handle = self._extract_instagram_handle(href)
                    is_instagram_page = "instagram.com" in href.lower()

                    candidate = LeadCandidate(
                        business_name=business_name,
                        sector=sector,
                        source="bing_search",
                        has_website=not is_instagram_page,
                    )

                    if is_instagram_page:
                        if instagram_handle:
                            candidate.instagram_handle = instagram_handle
                            candidate.instagram_url = f"https://instagram.com/{instagram_handle}"
                    else:
                        candidate.website_url = href
                        candidate.has_website = True
                        if instagram_handle:
                            candidate.instagram_handle = instagram_handle
                            candidate.instagram_url = f"https://instagram.com/{instagram_handle}"

                    # Extract snippet for phone/email
                    snippet_elem = r.find(class_="b_caption") or r.find("p") or r.find(class_="b_descript")
                    if snippet_elem:
                        snippet_text = snippet_elem.get_text(separator=" ", strip=True)
                        phone = self._extract_phone_from_text(snippet_text)
                        if phone:
                            candidate.phone = phone
                        email = self._extract_email_from_text(snippet_text)
                        if email:
                            candidate.email = email

                    candidates.append(candidate)

        except Exception as e:
            logger.error(f"Error executing Bing search query '{query}': {e}")

        return candidates

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Execute multiple Bing searches for maximum lead discovery:
        - General, contact, Instagram, phone, service, price list queries
        - Parallel execution with rate-limiting safeguards
        """
        logger.info(f"Starting Bing search discovery for '{sector}' in '{location}'...")

        queries = [
            f"{sector} {location}",
            f"{sector} {location} iletişim",
            f"{sector} {location} site:instagram.com",
            f"{sector} {location} telefon numarası",
            f"{sector} hizmetleri {location}",
            f"{sector} {location} fiyat listesi",
            f"{sector} firmaları {location}",
            f"{sector} işletmeleri {location}",
            f"{sector} {location} randevu",
            f"{sector} {location} web sitesi",
        ]

        if len(sector.split()) >= 2:
            queries.append(f'"{sector}" {location}')
            queries.append(f'"{sector}" {location} iletişim')

        all_candidates: List[LeadCandidate] = []
        chunk_size = 3  # More conservative for Bing
        for i in range(0, len(queries), chunk_size):
            chunk = queries[i:i + chunk_size]
            tasks = [self._search_query(q, sector) for q in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, list):
                    all_candidates.extend(r)
            if i + chunk_size < len(queries):
                await asyncio.sleep(0.5)  # Slightly longer delay for Bing

        # Deduplicate by URL or instagram handle
        seen_sites: Set[str] = set()
        seen_instas: Set[str] = set()
        merged: List[LeadCandidate] = []

        for c in all_candidates:
            if c.instagram_handle:
                if c.instagram_handle in seen_instas:
                    continue
                seen_instas.add(c.instagram_handle)
            elif c.website_url:
                clean_url = c.website_url.split("?")[0].rstrip("/").lower()
                clean_url = re.sub(r"^https?://www\.", "https://", clean_url)
                if clean_url in seen_sites:
                    continue
                seen_sites.add(clean_url)
            else:
                name_key = c.business_name.lower().strip()
                if name_key in seen_sites:
                    continue
                seen_sites.add(name_key)

            merged.append(c)

        logger.info(f"Bing search discovery finished: found {len(merged)} unique leads from {len(all_candidates)} raw results.")
        return merged
