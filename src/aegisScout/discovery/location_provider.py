"""
Location & IP Geolocation Provider (Zero-Config / Keyless).
Provides client-side reverse geocoding via BigDataCloud API and IP country resolution via Country.is API.
"""

from typing import Dict, Any, Optional
import httpx
from aegisScout.utils.logger import get_logger, log_execution_time

logger = get_logger("discovery.location_provider")

_BIGDATACLOUD_REVERSE_GEO_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"
_COUNTRY_IS_URL = "https://api.country.is/"
_IPIFY_URL = "https://api.ipify.org?format=json"
_TIMEOUT = 10.0


class ZeroConfigLocationProvider:
    """
    Keyless location and geolocation services for lead and user location resolution.
    """

    @staticmethod
    async def reverse_geocode_client(latitude: float, longitude: float, lang: str = "tr") -> Dict[str, Any]:
        """
        Reverse geocode latitude & longitude to city, district, and country via BigDataCloud.
        %100 Free, Zero API Key required.
        """
        logger.info(f"Reverse geocoding coordinates ({latitude}, {longitude}) via BigDataCloud...")
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": lang,
        }

        result = {
            "latitude": latitude,
            "longitude": longitude,
            "country": None,
            "country_code": None,
            "city": None,
            "locality": None,
            "principal_subdivision": None,
        }

        with log_execution_time(logger, f"BigDataCloud Reverse Geocode ({latitude},{longitude})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_BIGDATACLOUD_REVERSE_GEO_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        result["country"] = data.get("countryName")
                        result["country_code"] = data.get("countryCode")
                        result["city"] = data.get("city") or data.get("locality")
                        result["locality"] = data.get("locality")
                        result["principal_subdivision"] = data.get("principalSubdivision")
                        logger.info(f"BigDataCloud resolved ({latitude},{longitude}) -> {result['city']}, {result['country']}")
                    else:
                        logger.warning(f"BigDataCloud returned status {resp.status_code}")
            except Exception as e:
                logger.error(f"BigDataCloud reverse geocoding failed: {e}")

        return result

    @staticmethod
    async def get_ip_country(ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve country code for a given IP address (or current client IP if None) via Country.is.
        %100 Free, Zero API Key required.
        """
        target_url = f"{_COUNTRY_IS_URL}{ip_address.strip()}" if ip_address and ip_address.strip() else _COUNTRY_IS_URL
        logger.info(f"Resolving IP country for '{ip_address or 'client'}' via Country.is...")

        result = {
            "ip": ip_address,
            "country_code": None,
        }

        with log_execution_time(logger, f"Country.is IP lookup ({ip_address or 'self'})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(target_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        result["ip"] = data.get("ip")
                        result["country_code"] = data.get("country")
                        logger.info(f"Country.is resolved IP {result['ip']} -> Country: {result['country_code']}")
                    else:
                        logger.warning(f"Country.is returned status {resp.status_code}")
            except Exception as e:
                logger.error(f"Country.is lookup failed: {e}")

        return result

    @staticmethod
    async def get_public_ip() -> Optional[str]:
        """
        Fetch public IP address via Ipify.
        %100 Free, Zero API Key required.
        """
        logger.info("Fetching public IP address via Ipify...")
        with log_execution_time(logger, "Ipify Public IP Fetch"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_IPIFY_URL)
                    if resp.status_code == 200:
                        ip = resp.json().get("ip")
                        logger.info(f"Public IP retrieved via Ipify: {ip}")
                        return ip
            except Exception as e:
                logger.error(f"Ipify public IP fetch failed: {e}")

        return None
