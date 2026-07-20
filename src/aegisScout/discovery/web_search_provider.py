import urllib.parse
import re
import httpx
from typing import List, Optional
from bs4 import BeautifulSoup
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.web_search")

class WebSearchDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery Provider that searches DuckDuckGo (HTML interface) to discover
    potential leads (websites and Instagram handles) without using Map APIs.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

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
        name = re.sub(r"\s*[|•-]\s*(Instagram|Facebook|Twitter|TikTok|LinkedIn|Web sitesi|Website|Yelp|Foursquare).*", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s*(photos and videos|Home|Profile|Giriş Yap|Giriş|Kaydol|Üye Ol).*$", "", name, flags=re.IGNORECASE)
        # Remove trailing/leading punctuation
        name = name.strip().strip("-|•_ ")
        return name

    def _extract_instagram_handle(self, url: str) -> Optional[str]:
        """Extract Instagram handle from an Instagram URL if valid."""
        match = re.match(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)", url)
        if match:
            handle = match.group(1).strip().lower()
            # Ignore structural Instagram pages
            ignored = {"p", "explore", "stories", "reel", "developer", "about", "legal", "terms", "privacy", "accounts", "emails"}
            if handle and handle not in ignored:
                return handle
        return None

    async def _search_query(self, query: str, sector: str) -> List[LeadCandidate]:
        candidates = []
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"DuckDuckGo search returned status {resp.status_code} for query: {query}")
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
                    queries = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in queries:
                        actual_url = queries["uddg"][0]
                    else:
                        actual_url = href
                    
                    if not actual_url or not actual_url.startswith("http"):
                        continue

                    # Ignore major search directory results to avoid listing directories as leads
                    ignored_domains = [
                        "yelp.com", "foursquare.com", "tripadvisor.com", "sahibinden.com", 
                        "hepsiemlak.com", "trendyol.com", "facebook.com", "twitter.com", 
                        "linkedin.com", "youtube.com", "pinterest.com", "wikipedia.org"
                    ]
                    if any(domain in actual_url.lower() for domain in ignored_domains):
                        # But do not ignore Instagram!
                        if "instagram.com" not in actual_url.lower():
                            continue

                    aggregate_patterns = [
                        r"\b(en\s+iyi|en\s+ucuz|en\s+iyi\s+\d+|top\s+\d+|top\s+rated|top\s+list|\d+\s+en\s+iyi|\d+\s+top|popüler)\b",
                        r"\b(sıralama|sıralaması|sıralandı|önerilen|öneriler|tavsiye|tavsiyeler)\b",
                        r"\b(liste|listesi|listeler|best|recommended|ranking|rankings)\b",
                        r"\b(rehberi|rehber|guide|directory|dizin)\b",
                        r"\b(nerede\s+bul|nasıl\s+bul|hangi\s+\w+\s+seç|nerede|nasıl|neden|hangi)\b",
                        r"\b(\w+\s+fiyatları|\w+\s+ücretleri|\w+\s+maliyeti|fiyat|ücret|maliyet)\b",
                        r"\b(karşılaştırma|compare|comparison|blog|makale|yazı|haber|article|news)\b",
                        r"\b(kurumsal|hakkımızda|hizmetlerimiz|iletişim|bize\s+ulaşın)\b",
                    ]
                    title_lower = title.lower()
                    if any(re.search(p, title_lower) for p in aggregate_patterns):
                        continue

                    business_name = self._clean_business_name(title)
                    if not business_name or len(business_name) < 3:
                        continue

                    instagram_handle = self._extract_instagram_handle(actual_url)
                    snippet_text = ""

                    # Extract snippet details (e.g. check for phone number patterns)
                    snippet_elem = r.find("a", class_="result__snippet")
                    if snippet_elem:
                        snippet_text = snippet_elem.text.strip()

                    # Fallback: also look for an Instagram link in the snippet text
                    # when the page itself was not an Instagram URL.
                    if not instagram_handle and snippet_text:
                        ig_match = re.search(
                            r"(?:instagram\.com/|@)([a-zA-Z0-9_.\-]{3,30})",
                            snippet_text,
                        )
                        if ig_match:
                            candidate_handle = ig_match.group(1).strip().lower()
                            if candidate_handle and candidate_handle not in {
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
                        phone_match = re.search(r"(\+?\d[\d\s-]{8,}\d)", snippet_text)
                        if phone_match:
                            candidate.phone = phone_match.group(1).strip()
                            
                    candidates.append(candidate)
        except Exception as e:
            logger.error(f"Error executing web search query '{query}': {e}")
            
        return candidates

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Execute parallel web searches:
        1. General search: '{sector} {location}'
        2. Target Instagram search: '{sector} {location} site:instagram.com'
        3. Backup Instagram search: '{sector} {location} instagram'
        4. (multi-word sectors) Quoted exact-match search
        """
        logger.info(f"Starting high-yield web search discovery for '{sector}' in '{location}'...")
        
        # High-yield query variations to uncover 100s of business websites & social profiles
        queries = [
            f"{sector} {location}",
            f"{sector} {location} firmaları",
            f"{sector} {location} merkezleri",
            f"{sector} {location} iletişim",
            f"{sector} {location} site:instagram.com",
            f"{sector} {location} instagram",
            f"{sector} {location} telefon",
        ]
        
        if len(sector.split()) >= 2:
            queries.append(f'"{sector}" {location}')

        all_candidates = []
        for q in queries:
            c_list = await self._search_query(q, sector)
            all_candidates.extend(c_list)
        
        # Merge and deduplicate candidates by website_url or instagram_handle
        seen_sites = set()
        seen_instas = set()
        merged = []
        
        for c in all_candidates:
            if c.instagram_handle:
                if c.instagram_handle in seen_instas:
                    continue
                seen_instas.add(c.instagram_handle)
            elif c.website_url:
                clean_url = c.website_url.split("?")[0].rstrip("/")
                if clean_url in seen_sites:
                    continue
                seen_sites.add(clean_url)
            
            merged.append(c)
            
        logger.info(f"Web search discovery finished: found {len(merged)} unique leads.")
        return merged
