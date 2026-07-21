"""
DoktorSitesi.com Discovery Provider.

Scrapes doktorsitesi.com — a major Turkish directory of doctors, dentists,
psychologists, and healthcare specialists — to discover individual professional
leads with complete contact details, addresses, ratings, and avatar profile photos.
"""
import re
import urllib.parse
import httpx
from typing import List, Optional, Set
from bs4 import BeautifulSoup

from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.doktorsitesi")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

_BASE_URL = "https://www.doktorsitesi.com"
_MAX_RESULTS = 30
_MAX_DETAIL_FETCHES = 15
_HTTP_TIMEOUT_SEC = 20.0


class DoktorSitesiDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that scrapes doktorsitesi.com search results
    and individual doctor/specialist profile pages.
    """

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        if not sector or not sector.strip():
            logger.warning("DoktorSitesi search skipped: empty sector.")
            return []

        search_query = f"{sector} {location}".strip()
        logger.info(f"Starting DoktorSitesi discovery for '{search_query}'")

        detail_urls = await self._collect_profile_urls(search_query)
        if not detail_urls:
            logger.info(f"DoktorSitesi: no profile links found for '{search_query}'.")
            return []

        candidates: List[LeadCandidate] = []
        for url in list(detail_urls)[:_MAX_DETAIL_FETCHES]:
            try:
                candidate = await self._parse_profile(url, sector)
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                logger.warning(f"DoktorSitesi: error parsing profile '{url}': {e}")
                continue

        logger.info(f"DoktorSitesi discovery finished: found {len(candidates)} leads.")
        return candidates

    async def _collect_profile_urls(self, query: str) -> Set[str]:
        urls: Set[str] = set()
        encoded = urllib.parse.quote(query)
        search_target = f"{_BASE_URL}/ara?q={encoded}"

        try:
            async with httpx.AsyncClient(
                headers=_HEADERS, timeout=_HTTP_TIMEOUT_SEC, follow_redirects=True
            ) as client:
                resp = await client.get(search_target)
                if resp.status_code != 200:
                    logger.warning(f"DoktorSitesi search returned HTTP {resp.status_code}")
                    return urls

                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    # Matches doctor/specialist profile URLs on doktorsitesi.com
                    if re.search(r"/(uzman|doktor|psikolog|danisman|dr-[a-z0-9-]+|prof-[a-z0-9-]+)/", href) or (
                        href.startswith("/") and len(href.split("/")) == 2 and not href.startswith("/ara")
                    ):
                        full_url = urllib.parse.urljoin(_BASE_URL, href)
                        if full_url != _BASE_URL and "uzmanlik-alanlari" not in full_url:
                            urls.add(full_url)
        except Exception as e:
            logger.warning(f"DoktorSitesi URL collection error: {e}")

        return urls

    async def _parse_profile(self, url: str, sector: str) -> Optional[LeadCandidate]:
        try:
            async with httpx.AsyncClient(
                headers=_HEADERS, timeout=_HTTP_TIMEOUT_SEC, follow_redirects=True
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")

                # Name
                name_elem = soup.find("h1") or soup.find("meta", property="og:title")
                if not name_elem:
                    return None

                if name_elem.name == "meta":
                    name = name_elem.get("content", "").split("-")[0].strip()
                else:
                    name = name_elem.get_text(strip=True)

                if not name or len(name) < 3:
                    return None

                # Profile Image / Avatar
                avatar_url = None
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    avatar_url = og_image["content"]
                else:
                    img_elem = soup.find("img", class_=re.compile(r"avatar|profile|doctor|img"))
                    if img_elem and img_elem.get("src"):
                        avatar_url = urllib.parse.urljoin(_BASE_URL, img_elem["src"])

                # Address
                address = None
                addr_elem = soup.find(class_=re.compile(r"address|location|adres"))
                if addr_elem:
                    address = addr_elem.get_text(strip=True)

                # Phone
                phone = None
                phone_match = re.search(r"(?:0|\+90)?\s*([2-5]\d{2}\s*\d{3}\s*\d{2}\s*\d{2})", resp.text)
                if phone_match:
                    phone = "0" + re.sub(r"\D", "", phone_match.group(0))[-10:]

                # Bio / Description
                bio = None
                desc_meta = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
                if desc_meta:
                    bio = desc_meta.get("content", "").strip()

                # Rating / Reviews
                rating = None
                review_count = 0
                rating_elem = soup.find(class_=re.compile(r"rating|point|score"))
                if rating_elem:
                    m = re.search(r"(\d+(?:[.,]\d+)?)", rating_elem.get_text())
                    if m:
                        try:
                            rating = float(m.group(1).replace(",", "."))
                        except ValueError:
                            pass

                return LeadCandidate(
                    business_name=name,
                    sector=sector,
                    address=address or "",
                    phone=phone,
                    website_url=url,
                    instagram_bio=bio,
                    profile_image_url=avatar_url,
                    rating=rating,
                    review_count=review_count,
                    raw_source="doktorsitesi",
                )
        except Exception as e:
            logger.warning(f"Failed to parse DoktorSitesi profile at {url}: {e}")
            return None
