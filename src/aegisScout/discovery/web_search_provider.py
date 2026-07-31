"""
Enhanced Web Search Discovery Provider for aegisScout.
Searches multi-engine web endpoints (Bing, DuckDuckGo, Yandex, Brave, Google CS)
with rapid fallback mechanisms to maximize unique business lead discovery.
"""
import asyncio
import re
import urllib.parse
from typing import List, Optional, Set

import httpx
from bs4 import BeautifulSoup

from aegisScout.core.config import settings
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.web_search")


class WebSearchDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery Provider that performs web searches across multi-engine providers
    (Bing, DuckDuckGo JSON/HTML, Yandex, Brave, Google Custom Search)
    to discover potential leads (websites, phone numbers, and Instagram handles).
    """

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

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

        self._ignored_domains = [
            "yelp.com",
            "foursquare.com",
            "tripadvisor.com",
            "sahibinden.com",
            "hepsiemlak.com",
            "trendyol.com",
            "facebook.com",
            "twitter.com",
            "linkedin.com",
            "youtube.com",
            "pinterest.com",
            "wikipedia.org",
            "wikimedia.org",
            "yandex.com",
            "google.com",
            "bing.com",
            "duckduckgo.com",
        ]

        self._directory_listing_patterns = [
            r"bulurum\.com/dir/",
            r"bulurum\.com/search/[^?]+/?$",
            r"haritane\.com/kategori/?",
            r"tikla\.com\.tr/sektorler/[^/]+/?$",
            r"find\.com\.tr/Search/[A-Z]+",
            r"find\.com\.tr/Kategori/",
            r"sitelike\.org/similar/",
        ]

    def _clean_business_name(self, title: str) -> str:
        """Clean search result title to extract a neat business name."""
        name = title
        name = re.sub(r"^\d+\.\s*", "", name)
        name = re.sub(r"^[-\*\•]\s*", "", name)
        name = re.sub(r"\s*\(?@[\w_.-]+\)?", "", name)
        name = re.sub(
            r"\s*[|•-]\s*(Instagram|Facebook|Twitter|TikTok|LinkedIn|Web sitesi|Website|Yelp|Foursquare).*",
            "",
            name,
            flags=re.IGNORECASE,
        )
        name = re.sub(
            r"\s*(photos and videos|Home|Profile|Giriş Yap|Giriş|Kaydol|Üye Ol).*$",
            "",
            name,
            flags=re.IGNORECASE,
        )
        name = name.strip().strip("-|•_ ")
        return name

    def _extract_instagram_handle(self, url: str) -> Optional[str]:
        """Extract Instagram handle from an Instagram URL if valid."""
        match = re.match(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)", url)
        if match:
            handle = match.group(1).strip().lower()
            ignored = {
                "p",
                "explore",
                "stories",
                "reel",
                "reels",
                "developer",
                "about",
                "legal",
                "terms",
                "privacy",
                "accounts",
                "emails",
            }
            if handle and handle not in ignored:
                return handle
        return None

    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extract phone number from snippet text."""
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
        """Return True if URL should be filtered out (never filter Instagram)."""
        url_lower = url.lower()
        if "instagram.com" in url_lower:
            return False
        if any(domain in url_lower for domain in self._ignored_domains):
            return True
        return self._is_directory_listing_url(url)

    def _is_directory_listing_url(self, url: str) -> bool:
        """Return True if the URL is a category/listing page."""
        url_lower = url.lower()
        for pattern in self._directory_listing_patterns:
            if re.search(pattern, url_lower):
                return True
        return False

    async def _search_query(self, query: str, sector: str) -> List[LeadCandidate]:
        """Execute web search query across Bing, DDG, Yandex, Brave, Google CS."""
        candidates: List[LeadCandidate] = []
        raw_items = []  # List of dicts: {"title": ..., "url": ..., "snippet": ...}

        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            # -------------------------------------------------------------------
            # Engine 1: Bing Search HTML (Most resilient keyless engine)
            # -------------------------------------------------------------------
            try:
                bing_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&count=20"
                resp = await client.get(bing_url, headers=self.headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.select("li.b_algo, div.b_algo")
                    for r in results:
                        a = r.find("a")
                        if not a or not a.get("href"):
                            continue
                        actual_url = a.get("href", "")
                        title = a.get_text(strip=True)
                        snippet_elem = r.find("p") or r.find("div", class_="b_caption")
                        snippet = snippet_elem.get_text(separator=" ", strip=True) if snippet_elem else ""
                        if actual_url.startswith("http"):
                            raw_items.append({"title": title, "url": actual_url, "snippet": snippet})
            except Exception as e:
                logger.debug(f"Bing search error for '{query}': {e}")

            # -------------------------------------------------------------------
            # Engine 2: DuckDuckGo JSON API
            # -------------------------------------------------------------------
            if not raw_items:
                try:
                    ddg_json_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
                    resp = await client.get(ddg_json_url, headers=self.headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        related = data.get("RelatedTopics", [])
                        for item in related:
                            if "Text" in item and "FirstURL" in item:
                                raw_items.append({
                                    "title": item.get("Text", "").split(" - ")[0],
                                    "url": item.get("FirstURL", ""),
                                    "snippet": item.get("Text", ""),
                                })
                except Exception as e:
                    logger.debug(f"DDG JSON search error for '{query}': {e}")

            # -------------------------------------------------------------------
            # Engine 3: DuckDuckGo HTML GET / Lite
            # -------------------------------------------------------------------
            if not raw_items:
                try:
                    ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                    resp = await client.get(ddg_url, headers=self.headers)
                    if resp.status_code == 200 and "result__a" in resp.text:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        results = soup.find_all("div", class_="result")
                        for r in results:
                            title_a = r.find("a", class_="result__a")
                            if title_a:
                                title = title_a.text.strip()
                                href = str(title_a.get("href", ""))
                                parsed = urllib.parse.urlparse(href)
                                queries_qs = urllib.parse.parse_qs(parsed.query)
                                actual_url = str(queries_qs.get("uddg", [href])[0])
                                snippet_elem = r.find("a", class_="result__snippet")
                                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                                if actual_url.startswith("http"):
                                    raw_items.append({"title": title, "url": actual_url, "snippet": snippet})
                except Exception as e:
                    logger.debug(f"DDG HTML search error for '{query}': {e}")

            # -------------------------------------------------------------------
            # Engine 4: Yandex Search HTML
            # -------------------------------------------------------------------
            if not raw_items:
                try:
                    yandex_url = f"https://yandex.com.tr/search/?text={urllib.parse.quote(query)}&lr=11508"
                    resp = await client.get(yandex_url, headers=self.headers)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        items = soup.select("li.serp-item, div.organic")
                        for r in items:
                            a = r.find("a")
                            if not a or not a.get("href"):
                                continue
                            actual_url = a.get("href", "")
                            title = a.get_text(strip=True)
                            snippet_elem = r.find("div", class_="organic__content-text") or r.find("span", class_="extended-text")
                            snippet = snippet_elem.get_text(separator=" ", strip=True) if snippet_elem else ""
                            if actual_url.startswith("http"):
                                raw_items.append({"title": title, "url": actual_url, "snippet": snippet})
                except Exception as e:
                    logger.debug(f"Yandex search error for '{query}': {e}")

            # -------------------------------------------------------------------
            # Engine 5: Brave Search HTML
            # -------------------------------------------------------------------
            if not raw_items:
                try:
                    brave_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}&source=web"
                    resp = await client.get(brave_url, headers=self.headers)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        results = soup.select("div.snippet")
                        for r in results:
                            a = r.find("a", class_="title") or r.find("a")
                            if not a or not a.get("href"):
                                continue
                            actual_url = a.get("href", "")
                            title = a.get_text(strip=True)
                            snippet_elem = r.find("p", class_="snippet-description")
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                            if actual_url.startswith("http"):
                                raw_items.append({"title": title, "url": actual_url, "snippet": snippet})
                except Exception as e:
                    logger.debug(f"Brave search error for '{query}': {e}")

            # -------------------------------------------------------------------
            # Engine 6: Google Custom Search JSON API Fallback (if API key & CX set)
            # -------------------------------------------------------------------
            if not raw_items and settings.google_custom_search_api_key and settings.google_custom_search_cx:
                try:
                    cs_url = "https://customsearch.googleapis.com/customsearch/v1"
                    params = {
                        "key": settings.google_custom_search_api_key,
                        "cx": settings.google_custom_search_cx,
                        "q": query,
                        "num": 10,
                    }
                    resp = await client.get(cs_url, params=params)
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        for item in items:
                            raw_items.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                            })
                except Exception as e:
                    logger.debug(f"Google CS API search error for '{query}': {e}")

        # Process gathered raw items into LeadCandidates
        for item in raw_items:
            title = item["title"]
            actual_url = item["url"]
            snippet_text = item["snippet"]

            if self._is_ignored_domain(actual_url) or self._is_aggregate_page(title):
                continue

            business_name = self._clean_business_name(title)
            if not business_name or len(business_name) < 3:
                continue

            instagram_handle = self._extract_instagram_handle(actual_url)
            if not instagram_handle and snippet_text:
                ig_match = re.search(r"(?:instagram\.com/|@)([a-zA-Z0-9_.\-]{3,30})", snippet_text)
                if ig_match:
                    cand_handle = ig_match.group(1).strip().lower()
                    if cand_handle not in {
                        "p",
                        "explore",
                        "stories",
                        "reel",
                        "reels",
                        "developer",
                        "about",
                        "legal",
                        "terms",
                        "privacy",
                        "accounts",
                        "emails",
                    }:
                        instagram_handle = cand_handle

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

        return candidates

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Execute multiple web searches for maximum discovery coverage across
        Bing, DDG, Yandex, Brave, and Google CS.
        """
        logger.info(f"Starting multi-engine web search discovery for '{sector}' in '{location}'...")

        queries = [
            f"{sector} {location}",
            f"{sector} {location} iletişim",
            f"{sector} {location} telefon",
            f"{sector} {location} adresi",
            f"{sector} {location} site:instagram.com",
            f"{sector} {location} instagram",
        ]

        secondary = [
            f"{sector} firmaları {location}",
            f"{sector} merkezleri {location}",
            f"{sector} hizmetleri {location}",
            f"{sector} işletmeleri {location}",
            f"{sector} {location} web sitesi",
            f"{sector} {location} randevu",
        ]

        if len(sector.split()) >= 2:
            queries.append(f'"{sector}" {location}')
            queries.append(f'"{sector}" {location} iletişim')

        directory_queries = [
            f"site:bulurum.com/details {sector} {location}",
            f"site:haritane.com {sector} {location}",
            f"site:tikla.com.tr/firma {sector} {location}",
            f"site:find.com.tr/Firma {sector} {location}",
            f"site:sarisayfalar.com.tr {sector} {location}",
            f"{sector} {location} site:doktortakvimi.com",
        ]

        all_queries = queries + secondary + directory_queries

        all_candidates: List[LeadCandidate] = []
        chunk_size = 3
        for i in range(0, len(all_queries), chunk_size):
            chunk = all_queries[i : i + chunk_size]
            tasks = [self._search_query(q, sector) for q in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, list):
                    all_candidates.extend(r)
            if i + chunk_size < len(all_queries):
                await asyncio.sleep(0.2)

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

        logger.info(
            f"Web search discovery finished: found {len(merged)} unique leads from {len(all_candidates)} raw results."
        )
        return merged
