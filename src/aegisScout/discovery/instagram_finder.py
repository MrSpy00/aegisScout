import httpx
from typing import Optional
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.instagram_finder")

def _clean_location_for_search(location: str) -> str:
    """Extract clean district/city from detailed address strings for search queries."""
    if not location:
        return ""
    import re
    loc = location.strip()
    # Remove quotes
    loc = loc.replace('"', '').replace("'", "")
    # Remove 5-digit postal codes
    loc = re.sub(r"\b\d{5}\b", "", loc)
    # Remove No: X or No X patterns
    loc = re.sub(r"\bNo:\s*\d+\w*", "", loc, flags=re.IGNORECASE)
    loc = re.sub(r"\bNo\s*\d+\w*", "", loc, flags=re.IGNORECASE)
    # Remove street / avenue / district keywords
    loc = re.sub(r"\b(Caddesi|Cad\.|Sokak|Sok\.|Mahallesi|Mah\.|Bulvarı|Bulv\.|Avenue|Street|St\.|Rd\.|Road)\b", "", loc, flags=re.IGNORECASE)
    # Split by comma, semicolon or newline and take last 2 non-empty parts (usually district, city)
    parts = [p.strip() for p in re.split(r"[\n,;]+", loc) if p.strip()]
    if parts:
        cleaned = " ".join(parts[-2:])
        cleaned = re.sub(r"\b\d+\b", "", cleaned).strip()
        return cleaned if cleaned else location.strip()
    return location.strip()


class InstagramFinder:
    """
    Finds Instagram handle using Google Custom Search API, DuckDuckGo, or Bing.
    Does not scrape Instagram directly to avoid ToS bans.
    """
    def __init__(self):
        self.api_key = settings.google_custom_search_api_key
        self.cx = settings.google_custom_search_cx

    async def find_instagram(self, business_name: str, location: str) -> Optional[str]:
        clean_loc = _clean_location_for_search(location)
        clean_bname = (business_name or "").replace('"', '').replace("'", "").strip()

        if self.api_key and self.cx:
            # Formulate query with cleaned location
            query = f'site:instagram.com "{clean_bname}" {clean_loc}'.strip()
            url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": 3
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
                                parts = link.split("instagram.com/")
                                if len(parts) > 1:
                                    handle_part = parts[1].split("/")[0]
                                    if handle_part and handle_part not in ["p", "tv", "reel", "explore", "developer", "about"]:
                                        handle = handle_part.split("?")[0].strip().replace("@", "")
                                        if handle:
                                            return handle
                    else:
                        logger.error(f"Google Custom Search API returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error calling Google Custom Search API: {e}")

        logger.info("Trying DuckDuckGo keyless search for Instagram handle...")
        handle = await self._search_ddg_instagram(clean_bname, clean_loc)
        if handle:
            return handle

        logger.info("Trying Bing keyless search for Instagram handle...")
        return await self._search_bing_instagram(clean_bname, clean_loc)

    async def _search_ddg_instagram(self, business_name: str, location: str) -> Optional[str]:
        import urllib.parse
        import re

        queries = [
            f'site:instagram.com "{business_name}" {location}'.strip(),
            f'site:instagram.com {business_name} {location}'.strip()
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
                        urls = re.findall(r'href="([^"]*instagram\.com/[^"]*)"', response.text)
                        for link in urls:
                            link = urllib.parse.unquote(link)
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
                logger.error(f"Error scraping DuckDuckGo for Instagram on query '{query}': {type(e).__name__}: {e}")
        return None

    async def _search_bing_instagram(self, business_name: str, location: str) -> Optional[str]:
        import urllib.parse
        import re

        query = f'site:instagram.com "{business_name}" {location}'.strip()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8"
        }
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    matches = re.findall(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)', response.text)
                    ignored = {"p", "tv", "reel", "reels", "explore", "developer", "about", "tags", "legal", "terms", "privacy"}
                    for handle in matches:
                        handle_clean = handle.strip().lower()
                        if handle_clean and handle_clean not in ignored:
                            logger.info(f"Found Instagram handle '{handle_clean}' via Bing search for {business_name}")
                            return handle_clean
        except Exception as e:
            logger.error(f"Error scraping Bing for Instagram on query '{query}': {type(e).__name__}: {e}")
        return None
