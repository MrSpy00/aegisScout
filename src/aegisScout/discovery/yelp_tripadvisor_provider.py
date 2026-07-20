import re
import urllib.parse
from bs4 import BeautifulSoup
from typing import List
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.http_client import get_async_client
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.yelp_tripadvisor")

class YelpTripAdvisorDiscoveryProvider(BaseDiscoveryProvider):
    """
    Scrapes Yelp & TripAdvisor for business leads. Uses direct HTTP parsing with
    DuckDuckGo search fallback for optimal anti-blocking.
    """
    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Starting Yelp & TripAdvisor search for '{sector}' in '{location}'...")
        candidates = []
        
        # 1. Yelp Scraping
        try:
            yelp_candidates = await self._search_yelp(sector, location)
            candidates.extend(yelp_candidates)
        except Exception as e:
            logger.error(f"Yelp search failed: {e}")
            
        # 2. TripAdvisor Scraping
        try:
            ta_candidates = await self._search_tripadvisor(sector, location)
            candidates.extend(ta_candidates)
        except Exception as e:
            logger.error(f"TripAdvisor search failed: {e}")
            
        # 3. Deduplicate
        seen = set()
        merged = []
        for c in candidates:
            key = c.business_name.lower().strip()
            if key not in seen:
                seen.add(key)
                merged.append(c)
                
        return merged

    async def _search_yelp(self, sector: str, location: str) -> List[LeadCandidate]:
        candidates = []
        query = f"{sector} {location}"
        
        # Try direct search first
        url = f"https://www.yelp.com/search?find_desc={urllib.parse.quote(sector)}&find_loc={urllib.parse.quote(location)}"
        try:
            async with get_async_client(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Yelp titles are usually inside h3/h4/a tags
                    for a in soup.find_all("a", href=True):
                        if "/biz/" in a["href"]:
                            name = a.text.strip()
                            if name and len(name) > 2 and not name.isdigit():
                                candidates.append(LeadCandidate(
                                    business_name=name,
                                    sector=sector,
                                    address=location,
                                    source="yelp"
                                ))
        except Exception as e:
            logger.warning(f"Yelp direct page scrape blocked/failed: {e}. Trying fallback...")
            
        if not candidates:
            # Fallback via DuckDuckGo
            fallback_query = f"site:yelp.com/biz/ {sector} {location}"
            candidates = await self._ddg_scrape_fallback(fallback_query, sector, location, "yelp")
            
        return candidates

    async def _search_tripadvisor(self, sector: str, location: str) -> List[LeadCandidate]:
        # TripAdvisor direct pages are heavily protected by Cloudflare.
        # Therefore we immediately use the search engine snippet extraction fallback for maximum speed and robustness.
        fallback_query = f"site:tripadvisor.com {sector} {location}"
        return await self._ddg_scrape_fallback(fallback_query, sector, location, "tripadvisor")

    async def _ddg_scrape_fallback(self, query: str, sector: str, location: str, source: str) -> List[LeadCandidate]:
        candidates = []
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        try:
            async with get_async_client(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("div", class_="result")
                    for r in results:
                        title_a = r.find("a", class_="result__a")
                        if not title_a:
                            continue
                        title = title_a.text.strip()
                        
                        # Clean name
                        name = title
                        if "|" in name:
                            name = name.split("|")[0].strip()
                        if "-" in name:
                            name = name.split("-")[0].strip()
                        name = re.sub(r"^\d+\.\s*", "", name) # remove number prefix
                        
                        snippet_elem = r.find("a", class_="result__snippet")
                        snippet = snippet_elem.text.strip() if snippet_elem else ""
                        
                        # Extract website if present in snippet
                        website = None
                        web_match = re.search(r"(https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})", snippet)
                        if web_match:
                            website = web_match.group(1).strip()
                            
                        # Extract phone if present
                        phone = None
                        phone_match = re.search(r"(\+?\d[\d\s-]{8,}\d)", snippet)
                        if phone_match:
                            phone = phone_match.group(1).strip()
                            
                        if len(name) > 3 and not any(k in name.lower() for k in ["en iyi", "top 10", "tripadvisor", "yelp"]):
                            candidates.append(LeadCandidate(
                                business_name=name,
                                sector=sector,
                                address=location,
                                website_url=website,
                                has_website=bool(website),
                                phone=phone,
                                source=source
                            ))
        except Exception as e:
            logger.error(f"DuckDuckGo fallback search failed for {source}: {e}")
            
        return candidates
