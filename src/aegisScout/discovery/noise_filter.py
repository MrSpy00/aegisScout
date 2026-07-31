"""
Noise Filter Module for aegisScout.

Filters out non-business POI results from discovery scans:
  - Public transit stops, bus/metro stations
  - ATMs, banks (standalone), gas stations
  - Religious buildings (mosques, churches, temples)
  - Parks, playgrounds, cemeteries
  - Government offices (unless specifically targeted)
  - Parking lots, toll booths

Inspired by Gropector's DEFAULT_EXCLUDED_TYPES and POST_FILTER_EXCLUDED_TYPES.
"""
from __future__ import annotations

from typing import List, Optional
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.noise_filter")

# OpenStreetMap / Google Places category types to EXCLUDE by default
DEFAULT_EXCLUDED_OSM_TAGS = {
    # Transit & Transportation
    "bus_stop", "bus_station", "tram_stop", "subway_entrance", "subway_station",
    "ferry_terminal", "taxi", "car_sharing", "bicycle_rental", "parking",
    "parking_entrance", "parking_space", "toll_booth", "fuel", "charging_station",
    # Financial (standalone)
    "atm", "bureau_de_change",
    # Religious
    "place_of_worship", "mosque", "church", "cathedral", "synagogue",
    "temple", "shrine", "monastery",
    # Public facilities
    "park", "playground", "garden", "cemetery", "grave_yard",
    "recycling", "waste_disposal", "bench", "post_box", "telephone",
    "drinking_water", "fountain", "vending_machine",
    # Government / Emergency (unless targeted)
    "police", "fire_station", "ambulance_station",
    # Infrastructure
    "power", "tower", "mast", "water_tower", "reservoir",
}

# Google Places types to exclude
DEFAULT_EXCLUDED_GOOGLE_TYPES = {
    "bus_station", "transit_station", "subway_station",
    "atm", "gas_station", "parking",
    "place_of_worship", "cemetery", "park",
}

# Business name patterns that indicate non-businesses
# Business name patterns that indicate non-businesses or non-target entities (public/government/infrastructure/directories)
NOISE_NAME_PATTERNS = [
    # Infrastructure & Transit
    "otopark", "durağı", "durak", "istasyonu", "istasyon",
    "ATM", "akaryakıt", "benzin istasyonu",
    "cami", "kilise", "mosque", "church",
    "mezarlık", "park ve bahçe",
    "bus stop", "metro station", "subway",
    "parking lot", "toll booth",

    # Directory/Listing site names when appearing as business candidates
    "bulurum", "bulurumcom", "bulurum.com", "yellowpages", "sarı sayfalar", "sarisayfalar",
    "firma rehberi", "firmarehberi", "dizin", "find.com.tr", "haritane",

    # Public Health / State Institutions (Non-target institutional entities)
    "aile sağlığı merkezi", "aile sagligi merkezi", "sağlık ocağı", "saglik ocagi", "asm ", " asm",
    "toplum sağlığı merkezi", "ilçe sağlık müdürlüğü", "il sağlık müdürlüğü",
    "devlet hastanesi", "şehir hastanesi", "sehir hastanesi", "üniversite hastanesi", "fakülte hastanesi",
    "kamu hastanesi", "ağız ve diş sağlığı merkezi", "adsm ", " adsm",

    # State / Government / Municipal Institutions
    "valiliği", "valilik", "kaymakamlığı", "kaymakamlık",
    "belediyesi", "belediye başkanlığı", "belediye baskanligi",
    "emniyet müdürlüğü", "ilçe emniyet", "polis merkezi", "polis karakolu", "jandarma",
    "sosyal güvenlik kurumu", "sgk", "ptt", "işkur", "iskur", "vergi dairesi",
    "nüfus müdürlüğü", "nufus mudurlugu", "tapu müdürlüğü", "tapu mudurlugu",
    "muhtarlığı", "muhtarlık", "muhtarlik",

    # Public Education & Training Institutions
    "ilkokulu", "ortaokulu", "anadolu lisesi", "fen lisesi", "mesleki ve teknik",
    "üniversitesi", "fakültesi", "rektörlüğü", "yüksekokulu",
    "kültür merkezi", "gençlik merkezi", "halk eğitim merkezi", "halk egitim",
]


def is_noise(place: dict, excluded_types: Optional[set] = None) -> bool:
    """
    Determine if a place result is 'noise' (not a real business lead).
    
    Args:
        place: Dict with keys like 'name', 'types', 'category', 'amenity', etc.
        excluded_types: Optional custom set of types to exclude.
    
    Returns:
        True if the place should be filtered out as noise.
    """
    excluded = excluded_types or DEFAULT_EXCLUDED_OSM_TAGS
    
    # Check OSM amenity/shop/leisure tags
    for tag_key in ("amenity", "shop", "leisure", "landuse", "natural", "highway", "public_transport"):
        tag_val = str(place.get(tag_key, "")).lower()
        if tag_val and tag_val in excluded:
            logger.debug(f"Noise filter: removing '{place.get('name', 'N/A')}' (tag={tag_key}:{tag_val})")
            return True
    
    # Check Google Places types list
    types = place.get("types", place.get("place_types", []))
    if isinstance(types, list):
        for t in types:
            if str(t).lower() in excluded | DEFAULT_EXCLUDED_GOOGLE_TYPES:
                logger.debug(f"Noise filter: removing '{place.get('name', 'N/A')}' (type={t})")
                return True
    
    # Check business name patterns
    name = str(place.get("name", place.get("business_name", ""))).lower()
    for pattern in NOISE_NAME_PATTERNS:
        if pattern.lower() in name:
            logger.debug(f"Noise filter: removing '{name}' (name pattern: {pattern})")
            return True

    # Check if the website_url is a directory listing page
    url = str(place.get("website_url", place.get("url", ""))).lower()
    if url and is_directory_url(url):
        logger.debug(f"Noise filter: removing '{name}' (directory URL: {url[:80]})")
        return True

    return False


# Directory/listing URL patterns — pages that list MANY businesses, not a single one
_DIRECTORY_URL_BLACKLIST_PATTERNS = [
    r"bulurum\.com",
    r"yellowpages\.com\.tr",
    r"firmasec\.com",
    r"turkfirmalar\.com",
    r"haritane\.com/kategori",
    r"haritane\.com/sektor",
    r"tikla\.com\.tr/sektor",
    r"tikla\.com\.tr/kategori",
    r"find\.com\.tr/Search",
    r"find\.com\.tr/Kategori",
    r"find\.com\.tr/sehir=",
    r"sarisayfalar\.com\.tr",
    r"doktorsitesi\.com/arama",
    r"doktorsitesi\.com/doktorlar",
    r"doktortakvimi\.com/sehir",
    r"firmarehberi\.com",
    r"11880\.com\.tr",
    r"sitelike\.org",
    r"firmasayfasi\.com",
    r"facebook\.com/pages/category",
    r"facebook\.com/places",
    r"sahibinden\.com",
    r"n11\.com",
    r"trendyol\.com",
    r"hepsiburada\.com",
]


def is_directory_url(url: str) -> bool:
    """
    Return True if the URL is a directory listing / category page,
    not a specific business profile or detail page.
    """
    if not url:
        return False
    import re as _re
    url_lower = url.lower()
    for pattern in _DIRECTORY_URL_BLACKLIST_PATTERNS:
        if _re.search(pattern, url_lower):
            return True
    return False




def filter_noise(places: List[dict], excluded_types: Optional[set] = None) -> List[dict]:
    """
    Filter a list of place results, removing noise entries.
    
    Args:
        places: List of place dicts from any discovery provider
        excluded_types: Optional additional types to exclude
    
    Returns:
        Filtered list with noise removed.
    """
    before_count = len(places)
    filtered = [p for p in places if not is_noise(p, excluded_types)]
    removed = before_count - len(filtered)
    if removed > 0:
        logger.info(f"Noise filter: removed {removed} of {before_count} results ({removed/before_count*100:.1f}%)")
    return filtered


def get_opportunity_score(place: dict) -> float:
    """
    Score a business for 'opportunity' (how likely they are to need digital services).
    Higher score = better prospect.
    
    Scoring factors:
    - No website: +30 points (BIG opportunity)
    - Low rating (<3.5): +15 points (needs improvement)
    - Few reviews (<10): +10 points (new business)
    - Has phone but no email: +10 points
    - Has social media but no website: +20 points
    """
    score = 50.0  # Base score
    
    # No website = biggest opportunity
    has_website = bool(place.get("website") or place.get("website_url"))
    if not has_website:
        score += 30.0
    
    # Low Google rating = needs improvement
    rating = place.get("rating") or place.get("google_rating")
    if rating is not None:
        try:
            r = float(rating)
            if r < 3.5:
                score += 15.0
            elif r < 4.0:
                score += 7.0
        except (ValueError, TypeError):
            pass
    
    # Few reviews = newer business
    reviews = place.get("reviews_count") or place.get("google_reviews_count") or 0
    try:
        rc = int(reviews)
        if rc < 10:
            score += 10.0
        elif rc < 50:
            score += 5.0
    except (ValueError, TypeError):
        pass
    
    # Has phone but no email
    has_phone = bool(place.get("phone"))
    has_email = bool(place.get("email"))
    if has_phone and not has_email:
        score += 10.0
    
    # Has Instagram but no website (uses social as main presence)
    has_instagram = bool(place.get("instagram_url") or place.get("instagram_username"))
    if has_instagram and not has_website:
        score += 20.0
    
    return min(score, 100.0)  # Cap at 100


__all__ = [
    "is_noise",
    "filter_noise",
    "get_opportunity_score",
    "DEFAULT_EXCLUDED_OSM_TAGS",
    "DEFAULT_EXCLUDED_GOOGLE_TYPES",
]
