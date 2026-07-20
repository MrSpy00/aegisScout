import re
import urllib.parse
from bs4 import BeautifulSoup
from typing import List
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.http_client import get_async_client
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.sahibinden_sarisayfalar")

class SahibindenSariSayfalarDiscoveryProvider(BaseDiscoveryProvider):
    """
    Turkish local business provider targeting Yellow Pages (Sarı Sayfalar) and Sahibinden
    via search engine snippet extraction for 100% keyless independent operation.
    """
    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Starting Yellow Pages & Sahibinden scrape for '{sector}' in '{location}'...")
        candidates = []
        
        # Query yellow pages fallback
        try:
            yp_candidates = await self._search_yellow_pages(sector, location)
            candidates.extend(yp_candidates)
        except Exception as e:
            logger.error(f"Sarı Sayfalar scrape failed: {e}")
            
        # Query sahibinden fallback
        try:
            sh_candidates = await self._search_sahibinden(sector, location)
            candidates.extend(sh_candidates)
        except Exception as e:
            logger.error(f"Sahibinden search failed: {e}")
            
        # Deduplicate
        seen = set()
        merged = []
        for c in candidates:
            key = c.business_name.lower().strip()
            if key not in seen:
                seen.add(key)
                merged.append(c)
                
        return merged

    async def _search_yellow_pages(self, sector: str, location: str) -> List[LeadCandidate]:
        # Yellow Pages direct search or DDG search site:sarisayfalar.com.tr
        query = f"site:sarisayfalar.com.tr {sector} {location}"
        return await self._ddg_scrape_fallback(query, sector, location, "sarisayfalar")

    async def _search_sahibinden(self, sector: str, location: str) -> List[LeadCandidate]:
        # Sahibinden blocks direct requests immediately. Use DDG search index to extract listings.
        query = f"site:sahibinden.com {sector} {location}"
        return await self._ddg_scrape_fallback(query, sector, location, "sahibinden")

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
                        if "sahibinden" in name.lower():
                            name = re.sub(r"\s*-\s*sahibinden\.com.*", "", name, flags=re.IGNORECASE)
                        if "sarı sayfalar" in name.lower():
                            name = re.sub(r"\s*-\s*sarı sayfalar.*", "", name, flags=re.IGNORECASE)
                        name = re.sub(r"^\d+\.\s*", "", name) # remove number
                        
                        snippet_elem = r.find("a", class_="result__snippet")
                        snippet = snippet_elem.text.strip() if snippet_elem else ""
                        
                        # Look for phone/website in the snippet
                        phone = None
                        phone_match = re.search(r"(\+?\d[\d\s-]{8,}\d)", snippet)
                        if phone_match:
                            phone = phone_match.group(1).strip()
                            
                        website = None
                        web_match = re.search(r"(https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})", snippet)
                        if web_match:
                            website = web_match.group(1).strip()
                            
                        if len(name) > 3 and not any(k in name.lower() for k in ["sahibinden", "sarı sayfalar", "üye girişi", "kayıt"]):
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
            logger.error(f"Sarı Sayfalar / Sahibinden fallback search failed: {e}")
            
        return candidates
