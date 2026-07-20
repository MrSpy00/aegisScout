import httpx
from typing import List, Optional
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.google_places")

class GooglePlacesDiscoveryProvider(BaseDiscoveryProvider):
    """
    Google Places Discovery Provider using Text Search (New/Old API) and Nearby Search.
    Uses strict field masking to minimize costs as per PRD specifications.
    """
    def __init__(self):
        self.api_key = settings.google_places_api_key

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        if not self.api_key:
            raise ValueError("Google Places API Anahtarı (.env dosyasında GOOGLE_PLACES_API_KEY) ayarlanmamış.")

        # Google Places API Text Search endpoint
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # CRITICAL: Field mask to only request basic & essential details to save costs.
            # Avoid expensive fields like atmosphere (reviews/rating) unless explicitly needed.
            # But the PRD asks for rating/review_count to be loaded, which are 'Atmosphere' class.
            # Make sure we only ask for those if we really want to pay for them, or stick to basic fields.
            # We'll request names, addresses, phone numbers, websites, rating, and userRatingCount.
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount"
        }
        
        payload = {
            "textQuery": f"{sector} in {location}"
        }
        
        candidates = []
        next_page_token = None
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            for page in range(3):  # Fetch up to 3 pages (max 60 results)
                payload = {
                    "textQuery": f"{sector} in {location}"
                }
                if next_page_token:
                    payload["pageToken"] = next_page_token

                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    msg = f"Google Places API error (Code {response.status_code}): {response.text}"
                    logger.error(msg)
                    if page == 0:
                        raise RuntimeError(msg)
                    break
                
                data = response.json()
                places = data.get("places", [])
                for place in places:
                    name = place.get("displayName", {}).get("text")
                    if not name:
                        continue
                    
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
                    
                    candidate = LeadCandidate(
                        business_name=name,
                        sector=sector,
                        phone=phone,
                        address=address,
                        website_url=website,
                        has_website=bool(website),
                        rating=float(rating) if rating is not None else None,
                        review_count=int(review_count) if review_count is not None else None,
                        source="google_places"
                    )
                    candidates.append(candidate)

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break
            
        logger.info(f"Google Places discovery finished: found {len(candidates)} candidates.")
        return candidates
