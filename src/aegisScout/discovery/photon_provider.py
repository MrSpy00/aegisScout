"""
Photon Komoot Geocoding & Business Discovery Provider (Zero-Config / Keyless).
Uses https://photon.komoot.io/api/ to search OpenStreetMap POIs and locations with zero authentication.
"""

from typing import List, Optional
import httpx
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger, log_execution_time

logger = get_logger("discovery.photon")

_PHOTON_API_URL = "https://photon.komoot.io/api/"
_TIMEOUT = 12.0


class PhotonDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider leveraging Komoot's Photon OpenStreetMap search API.
    %100 Free, Zero API Key required.
    """

    def __init__(self):
        super().__init__()

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        query = f"{sector} {location}".strip()
        logger.info(f"Executing Photon Keyless OSM Search for '{query}'...")

        params = {
            "q": query,
            "limit": 30,
            "lang": "tr",
        }

        headers = {
            "User-Agent": "aegisScout/2.0 OSINT Engine (Open-Source Keyless)",
        }

        candidates: List[LeadCandidate] = []

        with log_execution_time(logger, f"Photon API HTTP request ({query})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                    resp = await client.get(_PHOTON_API_URL, params=params, headers=headers)
                    if resp.status_code != 200:
                        logger.warning(f"Photon API returned status {resp.status_code}")
                        return []

                    data = resp.json()
                    features = data.get("features", [])

                    for feature in features:
                        properties = feature.get("properties", {})
                        geometry = feature.get("geometry", {})

                        name = properties.get("name")
                        if not name or len(name.strip()) < 2:
                            continue

                        # Extract address components
                        street = properties.get("street")
                        housenumber = properties.get("housenumber")
                        district = properties.get("district") or properties.get("suburb")
                        city = properties.get("city") or properties.get("state")
                        country = properties.get("country")

                        addr_parts = [p for p in [street, housenumber, district, city, country] if p]
                        full_address = ", ".join(addr_parts) if addr_parts else location

                        # Extract coordinates if available
                        coords = geometry.get("coordinates", [])
                        lon, lat = (coords[0], coords[1]) if len(coords) >= 2 else (None, None)

                        phone = properties.get("phone") or properties.get("contact:phone")
                        website = properties.get("website") or properties.get("contact:website")

                        candidate = LeadCandidate(
                            business_name=name.strip(),
                            sector=sector,
                            address=full_address,
                            phone=phone,
                            website_url=website,
                            has_website=bool(website),
                            source="photon_komoot",
                        )
                        candidates.append(candidate)

            except Exception as e:
                logger.error(f"Photon Geocoding search failed for '{query}': {e}", exc_info=True)
                return []

        logger.info(f"Photon Keyless Search found {len(candidates)} candidates for '{query}'.")
        return candidates
