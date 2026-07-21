"""
SerpApi Google Maps, Local 3-Pack & Review Hook Discovery Provider for aegisScout.

Features:
1. SerpApi Google Maps (`engine=google_maps`) structured business discovery.
2. SerpApi Google Local 3-Pack (`engine=google`) local business extraction.
3. Multi-API key rotation via settings.get_next_api_key("serpapi_api_key").
4. Fallback web search scraper when no API key is provided.
5. Customer review extraction for hyper-personalized AI outreach hooks.
"""

import urllib.parse
import httpx
from typing import List, Dict, Any, Optional
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.discovery.web_search_provider import WebSearchDiscoveryProvider
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.serpapi")

_SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
_TIMEOUT = 15.0


class SerpApiMapsDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider leveraging SerpApi Google Maps Engine (`engine=google_maps`).
    """

    def __init__(self):
        super().__init__()
        self.fallback_provider = WebSearchDiscoveryProvider()

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        api_key = settings.get_next_api_key("serpapi_api_key") or getattr(settings, "serpapi_api_key", None)

        if not api_key:
            logger.info("SerpApi API key not found. Using free fallback web search discovery...")
            return await self.fallback_provider.search(sector, location, radius_km)

        query = f"{sector} {location}".strip()
        logger.info(f"Executing SerpApi Google Maps search for '{query}'...")

        params = {
            "engine": "google_maps",
            "q": query,
            "api_key": api_key,
            "hl": "tr",
            "gl": "tr",
        }

        candidates: List[LeadCandidate] = []
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(_SERPAPI_ENDPOINT, params=params)
                if resp.status_code != 200:
                    logger.warning(f"SerpApi returned status {resp.status_code}: {resp.text[:200]}")
                    return await self.fallback_provider.search(sector, location, radius_km)

                data = resp.json()
                results = data.get("local_results", [])
                if not results and "place_results" in data:
                    results = [data["place_results"]]

                for item in results:
                    title = item.get("title") or item.get("name")
                    if not title or len(title.strip()) < 2:
                        continue

                    phone = item.get("phone")
                    website = item.get("website")
                    address = item.get("address")
                    rating = item.get("rating")
                    
                    # Review count safe resolution
                    raw_reviews = item.get("reviews")
                    review_count = item.get("user_review_count") or item.get("reviews_count")
                    if review_count is None and isinstance(raw_reviews, (int, float)):
                        review_count = raw_reviews

                    thumbnail = item.get("thumbnail") or item.get("photo")

                    candidate = LeadCandidate(
                        business_name=title.strip(),
                        sector=sector,
                        address=address,
                        phone=phone,
                        website_url=website,
                        has_website=bool(website),
                        rating=float(rating) if rating is not None else None,
                        review_count=int(review_count) if review_count is not None else None,
                        profile_image_url=thumbnail,
                        source="serpapi_maps",
                    )

                    # Extract top review snippet for AI hook if present
                    reviews_list = item.get("user_reviews") or item.get("reviews_list") or (raw_reviews if isinstance(raw_reviews, list) else None)
                    if isinstance(reviews_list, list) and len(reviews_list) > 0 and isinstance(reviews_list[0], dict):
                        top_rev = reviews_list[0].get("snippet") or reviews_list[0].get("text")
                        if top_rev:
                            candidate.outreach_hook = f"Google Yorumu: \"{top_rev[:140]}...\""

                    candidates.append(candidate)

        except Exception as e:
            logger.error(f"SerpApi Google Maps search failed for '{query}': {e}")
            return await self.fallback_provider.search(sector, location, radius_km)

        logger.info(f"SerpApi Google Maps found {len(candidates)} candidates for '{query}'.")
        return candidates


class SerpApiLocalPackDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider leveraging SerpApi Google Organic & Local 3-Pack (`engine=google`).
    """

    def __init__(self):
        super().__init__()
        self.fallback_provider = WebSearchDiscoveryProvider()

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        api_key = settings.get_next_api_key("serpapi_api_key") or getattr(settings, "serpapi_api_key", None)

        if not api_key:
            logger.info("SerpApi API key not found. Using free fallback web search discovery...")
            return await self.fallback_provider.search(sector, location, radius_km)

        query = f"{sector} {location}".strip()
        logger.info(f"Executing SerpApi Google Local 3-Pack search for '{query}'...")

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "hl": "tr",
            "gl": "tr",
        }

        candidates: List[LeadCandidate] = []
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(_SERPAPI_ENDPOINT, params=params)
                if resp.status_code != 200:
                    logger.warning(f"SerpApi returned status {resp.status_code}: {resp.text[:200]}")
                    return await self.fallback_provider.search(sector, location, radius_km)

                data = resp.json()
                
                # 1. Parse Google Local Pack (3-pack)
                local_data = data.get("local_results")
                if isinstance(local_data, dict):
                    local_results = local_data.get("places", [])
                elif isinstance(local_data, list):
                    local_results = local_data
                else:
                    local_results = []

                for item in local_results:
                    title = item.get("title") or item.get("name")
                    if not title or len(title.strip()) < 2:
                        continue

                    phone = item.get("phone")
                    website = item.get("links", {}).get("website") or item.get("website")
                    address = item.get("address")
                    rating = item.get("rating")
                    reviews = item.get("reviews")

                    candidates.append(
                        LeadCandidate(
                            business_name=title.strip(),
                            sector=sector,
                            address=address,
                            phone=phone,
                            website_url=website,
                            has_website=bool(website),
                            rating=float(rating) if rating is not None else None,
                            review_count=int(reviews) if isinstance(reviews, (int, float)) else None,
                            source="serpapi_local_pack",
                        )
                    )

                # 2. Parse Organic Web Results
                organic = data.get("organic_results", [])
                for org in organic:
                    title = org.get("title")
                    link = org.get("link")

                    if not title or not link:
                        continue

                    candidates.append(
                        LeadCandidate(
                            business_name=title.split("-")[0].split("|")[0].strip(),
                            sector=sector,
                            website_url=link,
                            has_website=True,
                            source="serpapi_organic",
                        )
                    )

        except Exception as e:
            logger.error(f"SerpApi Google Local search failed for '{query}': {e}")
            return await self.fallback_provider.search(sector, location, radius_km)

        logger.info(f"SerpApi Google Local found {len(candidates)} candidates for '{query}'.")
        return candidates
