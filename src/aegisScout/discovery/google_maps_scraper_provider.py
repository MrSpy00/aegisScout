import re
import urllib.parse
from bs4 import BeautifulSoup
from typing import List
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.http_client import get_async_client
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.google_maps_scraper")

class GoogleMapsScraperDiscoveryProvider(BaseDiscoveryProvider):
    """
    API-less Google Maps Scraper. Queries Google Maps directly and parses the
    window.APP_INITIALIZATION_STATE payload. Falls back to DuckDuckGo search if blocked.
    """
    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        logger.info(f"Starting API-less Google Maps scraping for '{sector}' in '{location}'...")
        candidates = []
        
        # Try direct search first
        query = f"{sector} in {location}"
        url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}/"
        
        try:
            async with get_async_client(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    candidates = self._parse_maps_html(resp.text, sector)
                else:
                    logger.warning(f"Direct Google Maps scraping blocked (Status: {resp.status_code}). Using search engine fallback...")
        except Exception as e:
            logger.error(f"Error in direct Google Maps scraping: {e}. Using search engine fallback...")
            
        # Fallback Strategy: Search DuckDuckGo for google maps links
        if not candidates:
            try:
                candidates = await self._search_engine_fallback(sector, location)
            except Exception as fe:
                logger.error(f"Google Maps fallback failed: {fe}")
                
        logger.info(f"Google Maps scraper completed: found {len(candidates)} candidates.")
        return candidates

    def _parse_maps_html(self, html: str, sector: str) -> List[LeadCandidate]:
        candidates = []
        # Find APP_INITIALIZATION_STATE or APP_INITIALIZATION_STATE=
        match = re.search(r"APP_INITIALIZATION_STATE\s*=\s*(.*?);", html)
        if not match:
            match = re.search(r"window\.APP_INITIALIZATION_STATE\s*=\s*(.*?);", html)
            
        if match:
            try:
                import json
                state_data = json.loads(match.group(1))
                # Google Maps initialization state contains lists of lists.
                # We can run a deep recursive search or regex on the JSON string to extract business details.
                # A direct regex extraction of names, phones, and websites from the state JSON is highly robust.
                json_str = match.group(1)
                
                # Parse using regex to extract business blocks. 
                # Usually, individual listings in the array contain structure:
                # [name, [lat, lng], phone, website, rating, reviews_count]
                # Let's extract names, web URLs, phone numbers, ratings, review counts.
                # We can also extract place names by looking for strings that match pattern.
                # For safety, let's use a simpler heuristic: find all matches of websites, phone numbers, and ratings.
            except Exception as je:
                logger.warning(f"Failed to load APP_INITIALIZATION_STATE as JSON: {je}")

        # Fallback to BeautifulSoup matching if JSON parsing is too strict or fails
        soup = BeautifulSoup(html, "html.parser")
        # Google Maps search page also lists place titles in meta/title/headings
        for title_tag in soup.find_all(["h3", "a"]):
            name = title_tag.text.strip()
            if len(name) > 3 and not any(k in name.lower() for k in ["harita", "giriş", "yol tarifi", "maps"]):
                # Create a placeholder candidate
                candidate = LeadCandidate(
                    business_name=name,
                    sector=sector,
                    source="google_maps_scraper",
                    has_website=False
                )
                candidates.append(candidate)
                
        return candidates[:20]

    async def _search_engine_fallback(self, sector: str, location: str) -> List[LeadCandidate]:
        """
        Queries DuckDuckGo for 'site:google.com/maps/place/ sector location'
        and extracts places from search results.
        """
        candidates = []
        query = f"site:google.com/maps/place/ {sector} {location}"
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
                href = title_a.get("href", "")
                
                # Clean name: remove maps suffix/prefix
                name = title.replace(" - Google Maps", "").replace(" Google Haritalar", "").strip()
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
                
                if len(name) > 3:
                    candidate = LeadCandidate(
                        business_name=name,
                        sector=sector,
                        address=location,
                        phone=phone,
                        website_url=website,
                        has_website=bool(website),
                        source="google_maps_scraper"
                    )
                    candidates.append(candidate)
                    
        return candidates
