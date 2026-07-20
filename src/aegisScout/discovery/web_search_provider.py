"""
Enhanced Web Search Discovery Provider for aegisScout.
Searches DuckDuckGo (HTML interface) and supports multiple query strategies
to maximize unique business lead discovery.
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

logger = get_logger("discovery.web_search")


class WebSearchDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery Provider that searches DuckDuckGo (HTML interface) to discover
    potential leads (websites and Instagram handles) without using Map APIs.
    Uses multiple parallel query strategies to maximize result diversity.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        # Aggregate/directory page patterns to filter out
        self._aggregate_patterns = [
            r"\b(en\s+iyi|en\s+ucuz|top\s+\d+|top\s+rated|top\s+list|\d+\s+en\s+iyi|\d+\s+top|popüler)\b",
            r"\b(sıralama|sıralaması|sıralandı|önerilen|öneriler|tavsiye|tavsiyeler)\b",
            r"\b(liste|listesi|listeler|best|recommended|ranking|rankings)\b",
            r"\b(rehberi|rehber|guide|directory|dizin)\b",
            r"\b(nerede\s+bul|nasıl\s+bul|hangi\s+\w+\s+seç|nerede|nasıl|neden|hangi)\b",
            r"\b(\w+\s+fiyatları|\w+\s+ücretleri|\w+\s+maliyeti|fiyat|ücret|maliyet)\b",
            r"\b(karşılaştırma|compare|comparison|blog|makale|yazı|haber|article|news)\b",
            r"\b(kurumsal|hakkımızda|hizmetlerimiz|iletişim|bize\s+ulaşın)\b",
        ]
        # Common directory/noise domains to exclude (Instagram allowed)
        self._ignored_domains = [
            "yelp.com", "foursquare.com", "tripadvisor.com", "sahibinden.com",
            "hepsiemlak.com", "trendyol.com", "facebook.com", "twitter.com",
            "linkedin.com", "youtube.com", "pinterest.com", "wikipedia.org",
            "wikimedia.org", "yandex.com", "google.com",
        ]

    def _clean_business_name(self, title: str) -> str:
        """Clean search result title to extract a neat business name."""
        name = title
        # Remove numeric list prefixes like "1. ", "2. "
        name = re.sub(r"^\d+\.\s*", "", name)
        # Remove leading bullet markers
        name = re.sub(r"^[-\*\•]\s*", "", name)
        # Remove username patterns like (@username) or @username
        name = re.sub(r"\s*\(?@[\w_.-]+\)?", "", name)
        # Remove common social media prefixes/suffixes
        name = re.sub(
            r"\s*[|•-]\s*(Instagram|Facebook|Twitter|TikTok|LinkedIn|Web sitesi|Website|Yelp|Foursquare).*",
            "", name, flags=re.IGNORECASE
        )
        name = re.sub(
            r"\s*(photos and videos|Home|Profile|Giriş Yap|Giriş|Kaydol|Üye Ol).*$",
            "", name, flags=re.IGNORECASE
        )
        # Remove trailing/leading punctuation
        name = name.strip().strip("-|•_ ")
        return name

    def _extract_instagram_handle(self, url: str) -> Optional[str]:
        """Extract Instagram handle from an Instagram URL if valid."""
        match = re.match(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)", url)
        if match:
            handle = match.group(1).strip().lower()
            # Ignore structural Instagram pages
            ignored = {
                "p", "explore", "stories", "reel", "reels", "developer",
                "about", "legal", "terms", "privacy", "accounts", "emails"
            }
            if handle and handle not in ignored:
                return handle
        return None

    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extract phone number from snippet text."""
        # Turkish phone patterns
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
        """Extract email address from snippet text."""
        m = re.search(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text)
        return m.group(1).strip() if m else None

    def _is_aggregate_page(self, title: str) -> bool:
        """Return True if this appears to be a directory/list page."""
        title_lower = title.lower()
        return any(re.search(p, title_lower) for p in self._aggregate_patterns)

    def _is_ignored_domain(self, url: str) -> bool:
        """Return True if URL should be filtered out (but never Instagram)."""
        url_lower = url.lower()
        if "instagram.com" in url_lower:
            return False
        return any(domain in url_lower for domain in self._ignored_domains)

    async def _search_query(self, query: str, sector: str) -> List[LeadCandidate]:
        """Execute a single DuckDuckGo HTML search query and parse results."""
        candidates = []
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"DuckDuckGo returned status {resp.status_code} for query: {query}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                results = soup.find_all("div", class_="result")

                for r in results:
                    title_a = r.find("a", class_="result__a")
                    if not title_a:
                        continue

                    title = title_a.text.strip()
                    href = title_a.get("href", "")

                    # Decode DuckDuckGo redirect URLs
                    parsed = urllib.parse.urlparse(href)
                    queries_qs = urllib.parse.parse_qs(parsed.query)
                    actual_url = queries_qs.get("uddg", [href])[0]

                    if not actual_url or not actual_url.startswith("http"):
                        continue

                    if self._is_ignored_domain(actual_url):
                        continue

                    if self._is_aggregate_page(title):
                        continue

                    business_name = self._clean_business_name(title)
                    if not business_name or len(business_name) < 3:
                        continue

                    # Extract snippet for contact info
                    snippet_text = ""
                    snippet_elem = r.find("a", class_="result__snippet") or r.find("div", class_="result__snippet")
                    if snippet_elem:
                        snippet_text = snippet_elem.get_text(separator=" ", strip=True)

                    instagram_handle = self._extract_instagram_handle(actual_url)

                    # Also look for Instagram handles in snippets
                    if not instagram_handle and snippet_text:
                        ig_match = re.search(
                            r"(?:instagram\.com/|@)([a-zA-Z0-9_.\-]{3,30})",
                            snippet_text,
                        )
                        if ig_match:
                            candidate_handle = ig_match.group(1).strip().lower()
                            if candidate_handle not in {
                                "p", "explore", "stories", "reel", "reels",
                                "developer", "about", "legal", "terms",
                                "privacy", "accounts", "emails",
                            }:
                                instagram_handle = candidate_handle

                    is_instagram_page = "instagram.com" in actual_url.lower()

                    candidate = LeadCandidate(
                        business_name=business_name,
                        sector=sector,
                        source="web_search",
                        has_website=not is_instagram_page,
                    )

                    if is_instagram_page:
                        if instagram_handle:
                            candidate.instagram_handle = instagram_handle
                            candidate.instagram_url = f"https://instagram.com/{instagram_handle}"
                    else:
                        candidate.website_url = actual_url
                        candidate.has_website = True
                        if instagram_handle:
                            candidate.instagram_handle = instagram_handle
                            candidate.instagram_url = f"https://instagram.com/{instagram_handle}"

                    if snippet_text:
                        phone = self._extract_phone_from_text(snippet_text)
                        if phone:
                            candidate.phone = phone
                        email = self._extract_email_from_text(snippet_text)
                        if email:
                            candidate.email = email

                    candidates.append(candidate)

        except Exception as e:
            logger.error(f"Error executing web search query '{query}': {e}")

        return candidates

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Execute multiple web searches for maximum discovery coverage.
        Uses 14+ query variations covering:
        - General business listings
        - Contact info pages (telefon, iletişim)
        - Instagram profiles
        - Sector-specific terms (hizmetleri, merkezi, firmaları)
        - Address and pricing pages
        - Quoted exact-match for multi-word sectors
        """
        logger.info(f"Starting high-yield web search discovery for '{sector}' in '{location}'...")

        # Core queries — highest signal
        queries = [
            f"{sector} {location}",
            f"{sector} {location} iletişim",
            f"{sector} {location} telefon",
            f"{sector} {location} adresi",
            f"{sector} {location} site:instagram.com",
            f"{sector} {location} instagram",
        ]

        # Secondary queries — broader coverage
        secondary = [
            f"{sector} firmaları {location}",
            f"{sector} merkezleri {location}",
            f"{sector} hizmetleri {location}",
            f"{sector} işletmeleri {location}",
            f"{sector} {location} web sitesi",
            f"{sector} {location} randevu",
            f"{sector} {location} fiyat",
            f"en iyi {sector} {location}",
            f"{sector} {location} nerede",
        ]

        # Exact-match for multi-word sectors (e.g., "diş kliniği")
        if len(sector.split()) >= 2:
            queries.append(f'"{sector}" {location}')
            queries.append(f'"{sector}" {location} iletişim')
            secondary.append(f'"{sector}" {location} telefon')

        all_queries = queries + secondary

        # Execute queries with small concurrency to avoid rate limiting
        all_candidates: List[LeadCandidate] = []
        chunk_size = 4  # Process 4 queries in parallel batches
        for i in range(0, len(all_queries), chunk_size):
            chunk = all_queries[i:i + chunk_size]
            tasks = [self._search_query(q, sector) for q in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, list):
                    all_candidates.extend(r)
            # Small delay between batches to avoid being rate-limited
            if i + chunk_size < len(all_queries):
                await asyncio.sleep(0.3)

        # Deduplicate by URL (normalized) or Instagram handle
        seen_sites: Set[str] = set()
        seen_instas: Set[str] = set()
        merged: List[LeadCandidate] = []

        for c in all_candidates:
            if c.instagram_handle:
                if c.instagram_handle in seen_instas:
                    continue
                seen_instas.add(c.instagram_handle)
            elif c.website_url:
                # Normalize URL for dedup: strip query params, trailing slashes, www
                clean_url = c.website_url.split("?")[0].rstrip("/").lower()
                clean_url = re.sub(r"^https?://www\.", "https://", clean_url)
                if clean_url in seen_sites:
                    continue
                seen_sites.add(clean_url)
            else:
                # No URL and no Instagram — deduplicate by business name
                name_key = c.business_name.lower().strip()
                if name_key in seen_sites:
                    continue
                seen_sites.add(name_key)

            merged.append(c)

        logger.info(f"Web search discovery finished: found {len(merged)} unique leads from {len(all_candidates)} raw results.")
        return merged
