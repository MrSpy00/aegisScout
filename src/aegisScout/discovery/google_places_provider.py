import json
import httpx
from typing import List, Optional
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.core.config import settings
from aegisScout.core import database as db_module
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.google_places")

# ---------------------------------------------------------------------------
# POST-FILTER: Business types that Google Places may return but are not
# valid sales targets. Applied after the API response.
# ---------------------------------------------------------------------------
POST_FILTER_EXCLUDED_KEYWORDS = [
    "ATM", "Durak", "İstasyon", "Istasyon", "Gar", "Metro",
    "Park ", "Otopark", "Açık Alan",
    "Cami", "Camii", "Kilise", "Katedral", "Sinagog", "Türbe", "Dini",
    "Mezarlık", "Mezarligi",
    "Belediye", "Muhtarlık", "Kaymakamlık", "Valilik",
    "Emniyet", "Karakol", "İtfaiye",
    "PTT", "Posta",
    "Okul", "İlkokul", "Ortaokul", "Lise", "Üniversite", "Universite", "Kolej",
    "Anaokullu", "Anaokulu",
    "Kütüphane", "Kutuphane",
    "Hastane", "Acil Servis",
]

POST_FILTER_EXCLUDED_TYPES = [
    "transit_station", "bus_station", "train_station", "subway_station",
    "airport", "light_rail_station",
    "park", "natural_feature", "cemetery",
    "place_of_worship",
    "local_government_office", "city_hall", "courthouse", "police",
    "fire_station", "post_office",
    "primary_school", "secondary_school", "university", "library",
]


def _is_filtered(place_name: str, place_types: list) -> bool:
    """Return True if this place should be excluded from lead results."""
    # Type-based filter
    for pt in place_types:
        if pt in POST_FILTER_EXCLUDED_TYPES:
            return True
    # Keyword-based filter (name matching)
    name_lower = place_name.lower()
    for kw in POST_FILTER_EXCLUDED_KEYWORDS:
        if kw.lower() in name_lower:
            return True
    return False


class GooglePlacesDiscoveryProvider(BaseDiscoveryProvider):
    """
    Google Places Discovery Provider using Text Search and Nearby Search (New API).

    Improvements over the original:
    - place_id fetching to prevent duplicate imports
    - rankPreference=DISTANCE so nearby small businesses come first
    - languageCode=tr for Turkish results
    - reviews (originalText) stored as JSON snippets
    - Two-stage noise filtering (POST_FILTER_EXCLUDED_TYPES + keyword list)
    - API usage tracked via increment_usage()
    """
    def __init__(self):
        self.api_key = settings.google_places_api_key

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        if not self.api_key:
            raise ValueError(
                "Google Places API Anahtarı (.env dosyasında GOOGLE_PLACES_API_KEY) ayarlanmamış."
            )

        # Use Text Search (New API) — works with any text query
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # Field mask: only request necessary fields to minimise cost.
            # places.id          → Basic Data class (free)
            # places.displayName → Basic Data class (free)
            # places.formattedAddress → Basic Data class (free)
            # places.nationalPhoneNumber → Basic Data class (free)
            # places.websiteUri  → Basic Data class (free)
            # places.rating      → Atmosphere class (paid)
            # places.userRatingCount → Atmosphere class (paid)
            # places.types       → Basic Data class (free)
            # places.location    → Basic Data class (free)
            # places.reviews     → Atmosphere class (paid) — first 3, originalText
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.nationalPhoneNumber,places.websiteUri,"
                "places.rating,places.userRatingCount,"
                "places.types,places.location,"
                "places.reviews,nextPageToken"
            ),
        }

        # Build radius in meters (clamp to Google's 50 000 m max)
        radius_meters = min(radius_km * 1000, 50000) if radius_km > 0 else 50000

        payload = {
            "textQuery": f"{sector} in {location}",
            "languageCode": "tr",
            "rankPreference": "DISTANCE",
            "maxResultCount": 20,
        }

        candidates = []
        next_page_token: Optional[str] = None
        api_calls = 0

        async with httpx.AsyncClient(timeout=25.0) as client:
            for page in range(3):  # Up to 3 pages = 60 results max
                if next_page_token:
                    payload = {
                        "textQuery": f"{sector} in {location}",
                        "languageCode": "tr",
                        "rankPreference": "DISTANCE",
                        "maxResultCount": 20,
                        "pageToken": next_page_token,
                    }

                response = await client.post(url, headers=headers, json=payload)
                api_calls += 1

                if response.status_code != 200:
                    msg = f"Google Places API error (Code {response.status_code}): {response.text}"
                    logger.error(msg)
                    if page == 0:
                        raise RuntimeError(msg)
                    break

                data = response.json()
                places = data.get("places", [])

                for place in places:
                    name_obj = place.get("displayName", {})
                    name = name_obj.get("text") if isinstance(name_obj, dict) else None
                    if not name:
                        continue

                    # Type-based and keyword-based noise filter
                    place_types = place.get("types", [])
                    if _is_filtered(name, place_types):
                        logger.debug(f"Filtered out: {name} (types={place_types})")
                        continue

                    place_id: Optional[str] = place.get("id")

                    address = place.get("formattedAddress")

                    phone = place.get("nationalPhoneNumber")
                    if phone:
                        phone = phone.strip()
                        if phone.lower() in ["", "-", "n/a", "none", "null", "undefined"]:
                            phone = None

                    website = place.get("websiteUri")
                    if website:
                        website = website.strip()
                        if website.lower() in ["", "-", "n/a", "none", "null", "undefined"]:
                            website = None

                    rating = place.get("rating")
                    review_count = place.get("userRatingCount")

                    # Geographic coordinates (lat/lon)
                    location_data = place.get("location", {})
                    lat: Optional[float] = location_data.get("latitude")
                    lon: Optional[float] = location_data.get("longitude")

                    # Reviews — store originalText (not Google's auto-translated text)
                    reviews_json: Optional[str] = None
                    raw_reviews = place.get("reviews", [])
                    if raw_reviews:
                        review_snippets = []
                        for rv in raw_reviews[:3]:
                            author = rv.get("authorAttribution", {}).get("displayName", "")
                            star = rv.get("rating")
                            # Prefer original (untranslated) text
                            orig = rv.get("originalText", {})
                            text_obj = rv.get("text", {})
                            rv_text = (
                                orig.get("text", "") if isinstance(orig, dict) else ""
                            ) or (
                                text_obj.get("text", "") if isinstance(text_obj, dict) else ""
                            )
                            if rv_text:
                                review_snippets.append({
                                    "author": author,
                                    "rating": star,
                                    "text": rv_text[:500],
                                })
                        if review_snippets:
                            reviews_json = json.dumps(review_snippets, ensure_ascii=False)

                    candidate = LeadCandidate(
                        business_name=name,
                        sector=sector,
                        phone=phone,
                        address=address,
                        website_url=website,
                        has_website=bool(website),
                        rating=float(rating) if rating is not None else None,
                        review_count=int(review_count) if review_count is not None else None,
                        source="google_places",
                        # Extra fields stored as metadata — resolved in commands.py
                        _place_id=place_id,
                        _lat=lat,
                        _lon=lon,
                        _reviews_json=reviews_json,
                    )
                    candidates.append(candidate)

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

        # Track API usage (fire-and-forget, never raises)
        try:
            db_module.increment_usage("google_places", "discovery", count=api_calls)
        except Exception:
            pass

        logger.info(
            f"Google Places discovery finished: {len(candidates)} candidates "
            f"for '{sector}' in '{location}' ({api_calls} API calls)."
        )
        return candidates

    async def search_nearby(
        self,
        sector: str,
        lat: float,
        lon: float,
        radius_km: int = 10,
    ) -> List[LeadCandidate]:
        """
        Nearby Search (New API) — use when lat/lon coordinates are known.

        More accurate and cheaper than searchText for coordinate-based searches.
        """
        if not self.api_key:
            raise ValueError(
                "Google Places API Anahtarı (.env dosyasında GOOGLE_PLACES_API_KEY) ayarlanmamış."
            )

        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.nationalPhoneNumber,places.websiteUri,"
                "places.rating,places.userRatingCount,"
                "places.types,places.location,"
                "places.reviews,nextPageToken"
            ),
        }

        radius_meters = min(radius_km * 1000, 50000) if radius_km > 0 else 50000

        payload = {
            "includedKeywords": [sector],
            "languageCode": "tr",
            "rankPreference": "DISTANCE",
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_meters,
                }
            },
        }

        candidates = []
        api_calls = 0

        async with httpx.AsyncClient(timeout=25.0) as client:
            for _page in range(3):
                response = await client.post(url, headers=headers, json=payload)
                api_calls += 1

                if response.status_code != 200:
                    msg = f"Google Places Nearby API error ({response.status_code}): {response.text}"
                    logger.error(msg)
                    break

                data = response.json()
                places = data.get("places", [])

                for place in places:
                    name_obj = place.get("displayName", {})
                    name = name_obj.get("text") if isinstance(name_obj, dict) else None
                    if not name:
                        continue

                    place_types = place.get("types", [])
                    if _is_filtered(name, place_types):
                        continue

                    place_id = place.get("id")
                    address = place.get("formattedAddress")
                    phone = place.get("nationalPhoneNumber")
                    if phone:
                        phone = phone.strip()
                        if phone.lower() in ["", "-", "n/a", "none", "null"]:
                            phone = None
                    website = place.get("websiteUri")
                    if website:
                        website = website.strip()
                        if website.lower() in ["", "-", "n/a", "none", "null"]:
                            website = None

                    rating = place.get("rating")
                    review_count = place.get("userRatingCount")
                    loc = place.get("location", {})
                    p_lat = loc.get("latitude")
                    p_lon = loc.get("longitude")

                    # Review snippets
                    reviews_json = None
                    raw_reviews = place.get("reviews", [])
                    if raw_reviews:
                        snippets = []
                        for rv in raw_reviews[:3]:
                            author = rv.get("authorAttribution", {}).get("displayName", "")
                            star = rv.get("rating")
                            orig = rv.get("originalText", {})
                            text_obj = rv.get("text", {})
                            rv_text = (
                                orig.get("text", "") if isinstance(orig, dict) else ""
                            ) or (
                                text_obj.get("text", "") if isinstance(text_obj, dict) else ""
                            )
                            if rv_text:
                                snippets.append({"author": author, "rating": star, "text": rv_text[:500]})
                        if snippets:
                            reviews_json = json.dumps(snippets, ensure_ascii=False)

                    candidate = LeadCandidate(
                        business_name=name,
                        sector=sector,
                        phone=phone,
                        address=address,
                        website_url=website,
                        has_website=bool(website),
                        rating=float(rating) if rating is not None else None,
                        review_count=int(review_count) if review_count is not None else None,
                        source="google_places",
                        _place_id=place_id,
                        _lat=p_lat,
                        _lon=p_lon,
                        _reviews_json=reviews_json,
                    )
                    candidates.append(candidate)

                if not data.get("nextPageToken"):
                    break

        try:
            db_module.increment_usage("google_places", "discovery", count=api_calls)
        except Exception:
            pass

        logger.info(
            f"Google Places Nearby: {len(candidates)} candidates "
            f"for '{sector}' near ({lat:.4f}, {lon:.4f}) ({api_calls} API calls)."
        )
        return candidates
