import os
import re
import httpx
import urllib.parse
from typing import List, Optional
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.osm")

__all__ = ["OSMDiscoveryProvider", "_build_user_agent", "SECTOR_OSM_TAGS"]


def _build_user_agent() -> str:
    """
    Build a Nominatim/Overpass-compliant User-Agent string.

    Per OSM policy, the UA MUST identify the application and a contact channel.
    Format: "App/Version (<contact>)"
    Override the contact by setting the AEGIS_CONTACT_EMAIL environment variable.
    The default contact is the project URL; an email address is automatically
    wrapped with the ``mailto:`` scheme.
    """
    app_name = "aegisScout"
    app_version = "1.0"
    contact = os.environ.get("AEGIS_CONTACT_EMAIL", "github.com/MrSpy00/aegisScout")
    if "@" in contact and not contact.startswith("mailto:"):
        contact_value = f"mailto:{contact}"
    else:
        contact_value = contact
    return f"{app_name}/{app_version} ({contact_value})"

# Türkçe sektör → OSM etiket eşleştirme tablosu
# Birden fazla etiket belirtilebilir; hepsi OR mantığıyla sorgulanır.
SECTOR_OSM_TAGS: dict[str, list[tuple[str, str]]] = {
    # --- Güzellik & Bakım ---
    "kuaför": [("shop", "hairdresser"), ("shop", "beauty")],
    "berber": [("shop", "hairdresser"), ("shop", "barber")],
    "güzellik salonu": [("shop", "beauty"), ("shop", "hairdresser"), ("leisure", "beauty")],
    "güzellik merkezi": [("shop", "beauty"), ("leisure", "beauty")],
    "nail salon": [("shop", "beauty"), ("shop", "nail_salon")],
    "tırnak": [("shop", "beauty"), ("shop", "nail_salon")],
    "masaj": [("leisure", "massage"), ("shop", "massage"), ("amenity", "massage")],
    "spa": [("leisure", "spa"), ("amenity", "spa"), ("shop", "beauty")],
    "solaryum": [("leisure", "tanning_salon"), ("shop", "beauty")],
    "epilasyon": [("shop", "beauty"), ("healthcare", "beauty")],
    "estetik": [("shop", "beauty"), ("amenity", "clinic"), ("healthcare", "aesthetic")],
    "dövme": [("shop", "tattoo")],
    "tattoo": [("shop", "tattoo")],
    "piercing": [("shop", "piercing"), ("shop", "tattoo")],
    "hamam": [("amenity", "bath_house"), ("leisure", "bath_house")],
    "sauna": [("leisure", "sauna")],
    # --- Yiyecek & İçecek ---
    "kafe": [("amenity", "cafe")],
    "kahvehane": [("amenity", "cafe")],
    "kahve": [("amenity", "cafe"), ("shop", "coffee")],
    "restoran": [("amenity", "restaurant")],
    "lokanta": [("amenity", "restaurant")],
    "fast food": [("amenity", "fast_food")],
    "burger": [("amenity", "fast_food"), ("amenity", "restaurant")],
    "pizza": [("amenity", "fast_food"), ("amenity", "restaurant")],
    "kebap": [("amenity", "restaurant"), ("amenity", "fast_food")],
    "döner": [("amenity", "fast_food"), ("amenity", "restaurant")],
    "pide": [("amenity", "restaurant")],
    "börek": [("amenity", "restaurant"), ("shop", "bakery")],
    "bar": [("amenity", "bar")],
    "pub": [("amenity", "pub")],
    "gece kulübü": [("amenity", "nightclub"), ("amenity", "bar")],
    "fırın": [("shop", "bakery")],
    "pasta": [("shop", "pastry"), ("shop", "confectionery")],
    "tatlıcı": [("shop", "confectionery"), ("shop", "pastry")],
    "dondurma": [("amenity", "ice_cream"), ("shop", "ice_cream")],
    "çay": [("amenity", "cafe")],
    "nargile": [("amenity", "hookah_lounge"), ("amenity", "cafe")],
    # --- Sağlık & Tıp ---
    "diş kliniği": [("amenity", "dentist"), ("healthcare", "dentist")],
    "diş hekimi": [("amenity", "dentist"), ("healthcare", "dentist")],
    "doktor": [("amenity", "doctors"), ("healthcare", "doctor")],
    "aile hekimi": [("amenity", "doctors"), ("healthcare", "general_practitioner")],
    "eczane": [("amenity", "pharmacy")],
    "hastane": [("amenity", "hospital")],
    "klinik": [("amenity", "clinic"), ("healthcare", "clinic")],
    "laboratuvar": [("amenity", "clinic"), ("healthcare", "laboratory")],
    "fizik tedavi": [("healthcare", "physiotherapy"), ("amenity", "clinic")],
    "psikolog": [
        ("healthcare", "psychotherapist"),
        ("healthcare", "psychologist"),
        ("healthcare", "psychiatrist"),
        ("office", "therapist"),
        ("office", "psychologist"),
        ("amenity", "doctors"),
        ("amenity", "clinic")
    ],
    "psikoloji": [
        ("healthcare", "psychotherapist"),
        ("healthcare", "psychologist"),
        ("healthcare", "psychiatrist"),
        ("office", "therapist"),
        ("amenity", "clinic")
    ],
    "terapist": [
        ("healthcare", "psychotherapist"),
        ("healthcare", "psychologist"),
        ("office", "therapist"),
        ("amenity", "clinic")
    ],
    "diyetisyen": [("healthcare", "nutritionist"), ("office", "therapist")],
    "göz doktoru": [("healthcare", "ophthalmologist"), ("amenity", "doctors")],
    "ortopedi": [("healthcare", "orthopaedist"), ("amenity", "doctors")],
    "kardiyolog": [("healthcare", "cardiologist"), ("amenity", "doctors")],
    "veteriner": [("amenity", "veterinary")],
    # --- Eğitim ---
    "okul": [("amenity", "school")],
    "ilkokul": [("amenity", "school")],
    "lise": [("amenity", "school")],
    "üniversite": [("amenity", "university"), ("amenity", "college")],
    "dershane": [("amenity", "school"), ("amenity", "training")],
    "kurs": [("amenity", "training"), ("amenity", "school")],
    "anaokulu": [("amenity", "kindergarten")],
    "kreş": [("amenity", "kindergarten"), ("amenity", "childcare")],
    "özel okul": [("amenity", "school")],
    "dil okulu": [("amenity", "language_school"), ("amenity", "school")],
    "müzik okulu": [("amenity", "music_school")],
    "dans okulu": [("amenity", "dance_school"), ("amenity", "school")],
    # --- Spor & Fitness ---
    "spor salonu": [("leisure", "fitness_centre"), ("leisure", "sports_centre")],
    "gym": [("leisure", "fitness_centre")],
    "jimnastik": [("leisure", "fitness_centre")],
    "yüzme havuzu": [("leisure", "swimming_pool")],
    "havuz": [("leisure", "swimming_pool")],
    "tenis kortu": [("leisure", "tennis")],
    "futbol sahası": [("leisure", "pitch"), ("leisure", "sports_centre")],
    "yoga": [("leisure", "fitness_centre"), ("amenity", "yoga_studio")],
    "pilates": [("leisure", "fitness_centre"), ("amenity", "pilates_studio")],
    "boks": [("leisure", "sports_centre"), ("leisure", "fitness_centre")],
    "crossfit": [("leisure", "fitness_centre")],
    "bisiklet": [("shop", "bicycle"), ("leisure", "track")],
    # --- Perakende ---
    "market": [("shop", "supermarket"), ("shop", "convenience")],
    "süpermarket": [("shop", "supermarket")],
    "bakkal": [("shop", "convenience")],
    "manav": [("shop", "greengrocer")],
    "kasap": [("shop", "butcher")],
    "balıkçı": [("shop", "seafood")],
    "çiçekçi": [("shop", "florist")],
    "kuyumcu": [("shop", "jewelry"), ("shop", "jewellery")],
    "optik": [("shop", "optician")],
    "fotoğrafçı": [("shop", "photo")],
    "terzi": [("shop", "tailor")],
    "temizlik": [("shop", "dry_cleaning"), ("shop", "laundry")],
    "kuru temizleme": [("shop", "dry_cleaning")],
    "çamaşırhane": [("shop", "laundry")],
    "matbaa": [("shop", "printing"), ("shop", "copyshop")],
    "kitabevi": [("shop", "books")],
    "kırtasiye": [("shop", "stationery")],
    "elektronik": [("shop", "electronics")],
    "telefon": [("shop", "mobile_phone"), ("shop", "electronics")],
    "bilgisayar": [("shop", "computer"), ("shop", "electronics")],
    "giyim": [("shop", "clothes")],
    "ayakkabı": [("shop", "shoes")],
    "oyuncak": [("shop", "toys")],
    "mobilya": [("shop", "furniture")],
    "yapı market": [("shop", "doityourself"), ("shop", "hardware")],
    "hırdavat": [("shop", "hardware")],
    "boya": [("shop", "paint")],
    # --- Otomotiv ---
    "oto servis": [("shop", "car_repair")],
    "oto yıkama": [("amenity", "car_wash")],
    "benzinlik": [("amenity", "fuel")],
    "oto galeri": [("shop", "car")],
    "lastikçi": [("shop", "tyres")],
    "oto elektrik": [("shop", "car_repair")],
    "oto boya": [("shop", "car_repair")],
    # --- Mesleki & Ofis ---
    "mimar": [("office", "architect")],
    "hukuk bürosu": [("office", "lawyer")],
    "avukat": [("office", "lawyer")],
    "muhasebeci": [("office", "accountant")],
    "mali müşavir": [("office", "accountant"), ("office", "financial")],
    "emlakçı": [("office", "estate_agent")],
    "gayrimenkul": [("office", "estate_agent")],
    "sigorta": [("office", "insurance")],
    "banka": [("amenity", "bank")],
    "döviz": [("amenity", "bureau_de_change")],
    "noter": [("office", "notary"), ("amenity", "notary")],
    "yazılım": [("office", "it"), ("office", "software")],
    "teknoloji": [("office", "it"), ("office", "technology")],
    "ajans": [("office", "advertising"), ("office", "marketing")],
    "reklam": [("office", "advertising"), ("office", "marketing")],
    "medya": [("office", "media"), ("office", "advertising")],
    "tasarım": [("office", "design"), ("office", "architect")],
    "muhasebe": [("office", "accountant")],
    "danışmanlık": [("office", "consulting")],
    # --- Turizm & Konaklama ---
    "otel": [("tourism", "hotel"), ("tourism", "guest_house")],
    "pansiyon": [("tourism", "guest_house"), ("tourism", "hostel")],
    "hostel": [("tourism", "hostel")],
    "apart": [("tourism", "apartment"), ("tourism", "guest_house")],
    "tur": [("tourism", "travel_agency")],
    "seyahat acentesi": [("tourism", "travel_agency"), ("office", "travel_agent")],
    # --- Diğer ---
    "kutu ofis": [("office", "coworking"), ("amenity", "coworking_space")],
    "çocuk parkı": [("leisure", "playground")],
    "kütüphane": [("amenity", "library")],
    "ibadethane": [("amenity", "place_of_worship")],
    "cami": [("amenity", "place_of_worship"), ("religion", "muslim")],
    "kilise": [("amenity", "place_of_worship"), ("religion", "christian")],
    "petshop": [("shop", "pet")],
    "hayvan": [("shop", "pet"), ("amenity", "veterinary")],
    "kargo": [("amenity", "post_office"), ("shop", "courier_point")],
    "posta": [("amenity", "post_office")],
    "atm": [("amenity", "atm")],
    "otopark": [("amenity", "parking")],
    "sergi": [("tourism", "gallery")],
    "müze": [("tourism", "museum")],
    "sinema": [("amenity", "cinema")],
    "tiyatro": [("amenity", "theatre")],
    "konser": [("amenity", "music_venue"), ("amenity", "theatre")],
    "düğün salonu": [("amenity", "events_venue"), ("amenity", "hall")],
    "organizasyon": [("amenity", "events_venue")],
    "fotoğraf stüdyo": [("shop", "photo"), ("office", "photographer")],
    "stüdyo": [("shop", "photo"), ("office", "photographer")],
    "çocuk giyim": [("shop", "clothes"), ("shop", "baby_goods")],
    "bebek": [("shop", "baby_goods"), ("shop", "children")],
}


class OSMDiscoveryProvider(BaseDiscoveryProvider):
    """
    OpenStreetMap (OSM) Discovery Provider using Overpass API.
    Uses a sector-to-OSM-tag mapping for precise queries.
    Falls back to name regex search when no mapping exists.
    """
    def __init__(self):
        # Overpass query internal timeout (seconds) - optimized for reliability
        self.overpass_timeout_sec = 20
        # httpx network timeout must be > Overpass internal timeout
        self.http_timeout_sec = self.overpass_timeout_sec + 8

    def _resolve_sector_tags(self, sector: str) -> list[tuple[str, str]]:
        sector_lower = sector.lower().strip()
        if not sector_lower:
            return []

        if sector_lower in SECTOR_OSM_TAGS:
            return SECTOR_OSM_TAGS[sector_lower]

        sector_tokens = [token for token in re.split(r"[\s,;/\\-]+", sector_lower) if token]
        for token in sector_tokens:
            if token in SECTOR_OSM_TAGS:
                return SECTOR_OSM_TAGS[token]

        return []

    async def _get_geocode(self, location: str) -> Optional[dict]:
        """
        Geocode location string to coordinates and details using Nominatim (OSM free geocoder).
        """
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location)}&format=json&addressdetails=1&limit=1"
        headers = {"User-Agent": _build_user_agent()}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        first = data[0]
                        addresstype = first.get("addresstype", "")
                        if not addresstype:
                            addresstype = first.get("class", "")
                        return {
                            "lat": float(first["lat"]),
                            "lon": float(first["lon"]),
                            "osm_type": first.get("osm_type"),
                            "osm_id": first.get("osm_id"),
                            "addresstype": addresstype,
                            "display_name": first.get("display_name", "")
                        }
        except Exception as e:
            logger.error(f"Error geocoding location '{location}': {e}")
        return None

    def _build_overpass_query(self, sector: str, radius_meters: int, lat: float, lon: float) -> str:
        """
        Build an Overpass QL query around a coordinate.
        """
        osm_tags = self._resolve_sector_tags(sector)

        union_blocks = []
        if osm_tags:
            # Targeted query: only fetch nodes/ways/relations with matching tags
            for tag_key, tag_value in osm_tags:
                for element_type in ("node", "way", "relation"):
                    union_blocks.append(
                        f'  {element_type}["{tag_key}"="{tag_value}"](around:{radius_meters},{lat},{lon});'
                    )
        else:
            # Fallback: search by name regex (less precise but covers unknown sectors)
            logger.info(
                f"No OSM tag mapping found for sector '{sector}'. "
                f"Falling back to name regex search."
            )
            sector_pattern = re.escape(sector.strip())
            for element_type in ("node", "way", "relation"):
                union_blocks.append(
                    f'  {element_type}["name"~"{sector_pattern}",i](around:{radius_meters},{lat},{lon});'
                )

        union_str = "\n".join(union_blocks)
        return f"""
[out:json][timeout:{self.overpass_timeout_sec}];
(
{union_str}
);
out body;
"""

    def _build_overpass_query_area(self, sector: str, area_id: int) -> str:
        """
        Build an Overpass QL query inside a named area boundary.
        """
        osm_tags = self._resolve_sector_tags(sector)

        union_blocks = []
        if osm_tags:
            for tag_key, tag_value in osm_tags:
                for element_type in ("node", "way", "relation"):
                    union_blocks.append(
                        f'  {element_type}["{tag_key}"="{tag_value}"](area.searchArea);'
                    )
        else:
            logger.info(f"No OSM tag mapping found for sector '{sector}'. Falling back to name regex search in area.")
            sector_pattern = re.escape(sector.strip())
            for element_type in ("node", "way", "relation"):
                union_blocks.append(
                    f'  {element_type}["name"~"{sector_pattern}",i](area.searchArea);'
                )

        union_str = "\n".join(union_blocks)
        return f"""
[out:json][timeout:{self.overpass_timeout_sec}];
area({area_id})->.searchArea;
(
{union_str}
);
out body center;
"""

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        geo = await self._get_geocode(location)
        if not geo:
            msg = f"Nominatim '{location}' konumunu koordinata dönüştüremedi. Lütfen konumu doğru yazın (örn. 'Kadıköy, İstanbul')."
            logger.error(msg)
            raise RuntimeError(msg)

        lat = geo["lat"]
        lon = geo["lon"]
        osm_type = geo["osm_type"]
        osm_id = geo["osm_id"]
        addresstype = geo["addresstype"]

        # Determine if we should perform an area-based boundary query
        use_area = False
        area_id = None
        if osm_type in ("relation", "way") and osm_id:
            if radius_km == 0 or radius_km >= 50 or addresstype in ("country", "state", "province", "region", "county"):
                if osm_type == "relation":
                    area_id = 3600000000 + int(osm_id)
                elif osm_type == "way":
                    area_id = 2400000000 + int(osm_id)
                
                if area_id:
                    use_area = True

        if use_area and area_id is not None:
            logger.info(f"Using Overpass AREA query for '{location}' (type: {addresstype}, area_id: {area_id}) instead of coordinate radius.")
            query = self._build_overpass_query_area(sector, area_id)
        else:
            # coordinate-based search
            if radius_km == 0:
                logger.info("Radius is 0 (unlimited) but no OSM area ID available. Using default 50km coordinate radius.")
                radius_km = 50
            elif radius_km > 100:
                logger.warning(f"OSM Overpass radius of {radius_km}km is too large and will cause timeouts. Capping to 100km.")
                radius_km = 100
            radius_meters = radius_km * 1000
            query = self._build_overpass_query(sector, radius_meters, lat, lon)

        candidates = []
        overpass_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass.osm.ch/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
        ]
        headers = {
            "User-Agent": _build_user_agent()
        }
        response = None

        for url in overpass_urls:
            try:
                logger.info(f"Connecting to Overpass instance: {url}...")
                async with httpx.AsyncClient(timeout=self.http_timeout_sec) as client:
                    resp = await client.post(url, data={"data": query}, headers=headers)
                    if resp.status_code == 200:
                        response = resp
                        break
                    else:
                        logger.warning(f"Overpass instance {url} returned status {resp.status_code}. Trying next...")
            except Exception as e:
                logger.warning(f"Overpass instance {url} failed: {e}. Trying next...")

        if not response or response.status_code != 200:
            msg = "Tüm Overpass (OSM) sunucuları yanıt vermedi veya zaman aşımına uğradı. Lütfen daha sonra tekrar deneyin."
            logger.error(msg)
            raise RuntimeError(msg)

        try:
            data = response.json()
            elements = data.get("elements", [])
            for elem in elements:
                tags = elem.get("tags", {})
                name = tags.get("name")
                if not name:
                    continue

                # Extract contact details
                phone = (
                    tags.get("phone")
                    or tags.get("contact:phone")
                    or tags.get("phone:mobile")
                )
                if phone:
                    phone = phone.strip()
                    if phone.lower() in ["", "-", "n/a", "none", "null", "undefined"]:
                        phone = None

                website = (
                    tags.get("website")
                    or tags.get("contact:website")
                    or tags.get("url")
                )
                if website:
                    website = website.strip()
                    if website.lower() in ["", "-", "n/a", "none", "null", "undefined"]:
                        website = None

                # Direct Instagram tag detection (cleanest source)
                instagram = tags.get("contact:instagram") or tags.get("instagram")
                instagram_handle = None
                instagram_url = None
                if instagram:
                    instagram_handle = instagram.strip().split("/")[-1].replace("@", "")
                    instagram_url = f"https://instagram.com/{instagram_handle}"

                # Build address from OSM addr:* tags
                address_parts = []
                street = tags.get("addr:street")
                housenumber = tags.get("addr:housenumber")
                district = tags.get("addr:district") or tags.get("addr:suburb")
                city = tags.get("addr:city")
                postcode = tags.get("addr:postcode")
                if street:
                    part = street
                    if housenumber:
                        part += f" No: {housenumber}"
                    address_parts.append(part)
                if district:
                    address_parts.append(district)
                if city:
                    address_parts.append(city)
                if postcode:
                    address_parts.append(postcode)

                address = ", ".join(address_parts) if address_parts else None

                candidate = LeadCandidate(
                    business_name=name,
                    sector=sector,
                    phone=phone,
                    address=address,
                    website_url=website,
                    has_website=bool(website),
                    instagram_handle=instagram_handle,
                    instagram_url=instagram_url,
                    source="osm",
                )
                candidates.append(candidate)
        except Exception as e:
            logger.error(f"Error parsing Overpass API response: {e}")

        logger.info(f"OSM discovery: found {len(candidates)} candidates for '{sector}' in '{location}'")
        return candidates

