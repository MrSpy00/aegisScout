import httpx
from typing import Optional
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.instagram_finder")

class InstagramFinder:
    """
    Finds Instagram handle using Google Custom Search API.
    Does not scrape Instagram directly to avoid ToS bans.
    """
    def __init__(self):
        self.api_key = settings.google_custom_search_api_key
        self.cx = settings.google_custom_search_cx

    async def find_instagram(self, business_name: str, location: str) -> Optional[str]:
        if not self.api_key or not self.cx:
            logger.warning("Google Custom Search API Key or CX is not set. Falling back to DuckDuckGo keyless search.")
            return await self._search_ddg_instagram(business_name, location)

        # Formulate query
        query = f'site:instagram.com "{business_name}" {location}'
        url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 3 # Look at top 3 results
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    for item in items:
                        link = item.get("link", "")
                        if "instagram.com" in link:
                            # Clean the link
                            # format: https://www.instagram.com/username/ or https://www.instagram.com/username
                            parts = link.split("instagram.com/")
                            if len(parts) > 1:
                                handle_part = parts[1].split("/")[0]
                                # Filter out common pages
                                if handle_part and handle_part not in ["p", "tv", "reel", "explore", "developer", "about"]:
                                    # Clean query parameters if any
                                    handle = handle_part.split("?")[0].strip().replace("@", "")
                                    return handle
                else:
                    logger.error(f"Google Custom Search API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error calling Google Custom Search API: {e}")

        logger.info("Google Custom Search failed or is unavailable. Trying DuckDuckGo keyless search...")
        return await self._search_ddg_instagram(business_name, location)

    async def _search_ddg_instagram(self, business_name: str, location: str) -> Optional[str]:
        import urllib.parse
        import re

        queries = [
            f'site:instagram.com "{business_name}" {location}',
            f'site:instagram.com {business_name} {location}'
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        for idx, query in enumerate(queries):
            logger.info(f"Searching Instagram handle via DuckDuckGo (Attempt {idx+1}/{len(queries)}): {query}")
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        # Parse out links matching instagram.com
                        urls = re.findall(r'href="([^"]*instagram\.com/[^"]*)"', response.text)
                        for link in urls:
                            link = urllib.parse.unquote(link)
                            # Extract redirect link if present
                            if "uddg=" in link:
                                try:
                                    link = link.split("uddg=")[1].split("&")[0]
                                    link = urllib.parse.unquote(link)
                                except Exception:
                                    pass
                            
                            parts = link.split("instagram.com/")
                            if len(parts) > 1:
                                handle_part = parts[1].split("/")[0]
                                if handle_part and handle_part not in ["p", "tv", "reel", "explore", "developer", "about", "tags"]:
                                    handle = handle_part.split("?")[0].strip().replace("@", "")
                                    if handle:
                                        logger.info(f"Found Instagram handle '{handle}' via DuckDuckGo fallback query {idx+1} for {business_name}")
                                        return handle
            except Exception as e:
                logger.error(f"Error scraping DuckDuckGo for Instagram on query '{query}': {e}")
        return None
