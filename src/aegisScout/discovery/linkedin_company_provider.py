import re
import urllib.parse
from bs4 import BeautifulSoup
from typing import List
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.core.config import settings
from aegisScout.utils.http_client import get_async_client
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.linkedin_company")

class LinkedinCompanyDiscoveryProvider(BaseDiscoveryProvider):
    """
    LinkedIn Company Discovery Provider.
    If session cookie is provided, uses authenticated API calls/searches.
    Otherwise, uses public search engine queries to pull public LinkedIn profiles.
    """
    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        cookie = settings.linkedin_session_cookie
        candidates = []
        
        if cookie:
            try:
                candidates = await self._search_with_cookie(sector, location, cookie)
            except Exception as e:
                logger.error(f"LinkedIn authenticated search failed: {e}. Falling back to public search...")
                
        if not candidates:
            # Public Web search fallback (Keyless & Cookieless)
            try:
                candidates = await self._search_public(sector, location)
            except Exception as e:
                logger.error(f"LinkedIn public search fallback failed: {e}")
                
        return candidates

    async def _search_with_cookie(self, sector: str, location: str, cookie: str) -> List[LeadCandidate]:
        candidates = []
        # LinkedIn session cookie is usually 'li_at'
        headers = {
            "Cookie": f"li_at={cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Fetching LinkedIn Search company list
        # https://www.linkedin.com/voyager/api/search/hits?q=companies&query=...
        # For simplicity and anti-bot protection, we can query LinkedIn's search URL directly
        # and pull details, or fallback to public search if it gets redirected to login.
        url = f"https://www.linkedin.com/search/results/companies/?keywords={urllib.parse.quote(sector)}&origin=GLOBAL_SEARCH_HEADER"
        async with get_async_client(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Parse listing items
                for tag in soup.find_all("span", class_="entity-result__title-text"):
                    a = tag.find("a")
                    if a:
                        name = a.text.strip()
                        href = str(a.get("href", ""))
                        candidates.append(LeadCandidate(
                            business_name=name,
                            sector=sector,
                            linkedin_url=href,
                            source="linkedin"
                        ))
        return candidates

    async def _search_public(self, sector: str, location: str) -> List[LeadCandidate]:
        candidates = []
        query = f"site:linkedin.com/company/ {sector} {location}"
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        async with get_async_client(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
                
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("div", class_="result")
            for r in results:
                title_a = r.find("a", class_="result__a")
                if not title_a:
                    continue
                title = title_a.text.strip()
                href = str(title_a.get("href", ""))
                
                # Decrypt redirect URL if it contains linkedin.com/company/
                parsed = urllib.parse.urlparse(href)
                queries = urllib.parse.parse_qs(parsed.query)
                actual_url = str(queries["uddg"][0]) if "uddg" in queries else href
                
                if "linkedin.com/company/" not in actual_url:
                    continue
                
                # Clean title to get company name
                name = title
                if ":" in name:
                    name = name.split(":")[0].strip()
                if "|" in name:
                    name = name.split("|")[0].strip()
                if "LinkedIn" in name:
                    name = re.sub(r"\s*-\s*LinkedIn.*", "", name, flags=re.IGNORECASE)
                name = re.sub(r"^\d+\.\s*", "", name) # remove number
                
                if len(name) > 2:
                    candidates.append(LeadCandidate(
                        business_name=name,
                        sector=sector,
                        address=location,
                        linkedin_url=actual_url,
                        source="linkedin"
                    ))
        return candidates
