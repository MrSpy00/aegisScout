import asyncio
import base64
import re
import unicodedata
import urllib.parse
from typing import Dict, List, Optional, Set
import httpx
from bs4 import BeautifulSoup

from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.instagram_finder")

IGNORED_HANDLES = {
    "p", "tv", "reel", "reels", "explore", "developer", "about", "tags",
    "legal", "terms", "privacy", "accounts", "directory", "stories",
    "challenge", "api", "static", "embed", "login", "create", "press", "jobs",
    "instagram", "facebook", "twitter", "youtube", "tiktok", "whatsapp", "help"
}

TURKEY_MAJOR_CITIES = [
    "", "istanbul", "ankara", "izmir", "bursa", "antalya", "adana",
    "gaziantep", "konya", "kocaeli", "mersin", "diyarbakir", "kayseri",
    "eskisehir", "sanliurfa", "samsun", "denizli", "sakarya", "trabzon"
]


def _slugify_tr(text: str) -> str:
    """Normalize Turkish characters to clean ASCII slug string."""
    if not text:
        return ""
    cleaned = text.replace("ı", "i").replace("İ", "I").replace("i̇", "i")
    nfkd = unicodedata.normalize("NFKD", cleaned)
    ascii_str = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return ascii_str.lower().strip()


def _clean_location_for_search(location: str) -> str:
    """Extract clean district/city from detailed address strings for search queries."""
    if not location:
        return ""
    loc = location.strip()
    loc = loc.replace('"', '').replace("'", "")
    loc = re.sub(r"\b\d{5}\b", "", loc)
    loc = re.sub(r"\bNo:\s*\d+\w*", "", loc, flags=re.IGNORECASE)
    loc = re.sub(r"\bNo\s*\d+\w*", "", loc, flags=re.IGNORECASE)
    loc = re.sub(r"\b(Caddesi|Cad\.|Sokak|Sok\.|Mahallesi|Mah\.|Bulvarı|Bulv\.|Avenue|Street|St\.|Rd\.|Road)\b", "", loc, flags=re.IGNORECASE)
    parts = [p.strip() for p in re.split(r"[\n,;]+", loc) if p.strip()]
    if parts:
        cleaned = " ".join(parts[-2:])
        cleaned = re.sub(r"\b\d+\b", "", cleaned).strip()
        return cleaned if cleaned else location.strip()
    return location.strip()


def _decode_bing_url(bing_url: str) -> Optional[str]:
    """Decode Bing redirect URL (u=a1aHR0c...) to original target URL."""
    try:
        if "u=a1" in bing_url:
            raw_b64 = bing_url.split("u=a1")[1].split("&")[0]
            padded = raw_b64 + "=" * (-len(raw_b64) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            return decoded_bytes.decode("utf-8", errors="ignore")
    except Exception:
        pass
    return None


def _extract_handles_from_content(text_content: str) -> Set[str]:
    """
    Extract all Instagram handles from raw HTML, Bing Base64 redirects, DuckDuckGo URLs,
    and text snippets containing @username or instagram.com/username.
    """
    handles: Set[str] = set()
    if not text_content:
        return handles

    direct_matches = re.findall(r"instagram\.com/([a-zA-Z0-9_.-]{3,30})", text_content, re.IGNORECASE)
    for m in direct_matches:
        h = m.strip().lower()
        if h not in IGNORED_HANDLES and not h.isdigit():
            handles.add(h)

    at_matches = re.findall(r"@([a-zA-Z0-9_.-]{3,30})", text_content)
    for m in at_matches:
        h = m.strip().lower()
        if h not in IGNORED_HANDLES and not h.isdigit() and len(h) >= 3:
            handles.add(h)

    bing_redirects = re.findall(r'href="([^"]*bing\.com/ck/a[^"]*)"', text_content, re.IGNORECASE)
    for b_link in bing_redirects:
        decoded = _decode_bing_url(b_link)
        if decoded and "instagram.com/" in decoded:
            parts = decoded.split("instagram.com/")
            if len(parts) > 1:
                h = parts[1].split("/")[0].split("?")[0].strip().lower().replace("@", "")
                if h and h not in IGNORED_HANDLES and not h.isdigit():
                    handles.add(h)

    ddg_links = re.findall(r'href="([^"]*uddg=[^"]*)"', text_content, re.IGNORECASE)
    for d_link in ddg_links:
        try:
            unquoted = urllib.parse.unquote(d_link)
            if "uddg=" in unquoted:
                target = unquoted.split("uddg=")[1].split("&")[0]
                target = urllib.parse.unquote(target)
                if "instagram.com/" in target:
                    parts = target.split("instagram.com/")
                    if len(parts) > 1:
                        h = parts[1].split("/")[0].split("?")[0].strip().lower().replace("@", "")
                        if h and h not in IGNORED_HANDLES and not h.isdigit():
                            handles.add(h)
        except Exception:
            pass

    return handles


SECTOR_SYNONYMS_MAP = {
    "kuaför": [
        "kuafor", "berber", "guzellik", "guzelliksalonu", "hair", "hairstylist",
        "hairdesign", "hairdresser", "coiffure", "hairart", "hairclinic", "hairsalon",
        "saloon", "makeup", "nail", "estetik", "bayankuaforu", "erkekkuaforu",
        "sac_tasarim", "guzellikmerkezi"
    ],
    "güzellik": [
        "guzellik", "guzelliksalonu", "estetik", "ciltbakimi", "lazer", "epilasyon",
        "nail", "proteztirnak", "makeup", "makyaj", "beauty", "beautystudio", "spa"
    ],
    "yazılım": [
        "yazilim", "dijitalajans", "webtasarim", "mobiluygulama", "seoajansi",
        "sosyalmedya", "software", "tech", "code", "dev", "agency"
    ],
    "avukat": [
        "avukat", "hukuk", "hukukburosu", "dava", "danismanlik", "arabulucu",
        "law", "lawyer", "legal", "attorney"
    ],
    "diş": [
        "dis", "dishekimi", "disklinigi", "dentist", "dental", "ortodonti",
        "implant", "agizvedissagligi"
    ],
    "restoran": [
        "restoran", "restaurant", "kafe", "cafe", "lokanta", "bistro", "pastane",
        "lezzet", "gastronomi", "kitchen", "food"
    ]
}


class InstagramFinder:
    """
    Advanced 5-Layer Hybrid Instagram Profile Finder & OSINT Engine.
    Generates 3000+ candidate handles across Turkish sectors, harvests from directory providers,
    and extracts unredacted profile metadata using Googlebot & Bingbot headers.
    """
    def __init__(self):
        self.api_key = settings.google_custom_search_api_key
        self.cx = settings.google_custom_search_cx
        self.browser_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.bingbot_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.instagram_api_headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 320.0.0.16.117"
            ),
            "X-IG-App-ID": "936619743392459",
            "Accept": "*/*",
        }

    async def find_instagram(self, business_name: str, location: str) -> Optional[str]:
        """Legacy helper: find a single handle by business name & location."""
        clean_loc = _clean_location_for_search(location)
        clean_bname = (business_name or "").replace('"', '').replace("'", "").strip()

        if self.api_key and self.cx:
            query = f'site:instagram.com "{clean_bname}" {clean_loc}'.strip()
            url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {"key": self.api_key, "cx": self.cx, "q": query, "num": 3}
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("items", []):
                            link = item.get("link", "")
                            if "instagram.com" in link:
                                parts = link.split("instagram.com/")
                                if len(parts) > 1:
                                    handle_part = parts[1].split("/")[0].split("?")[0].strip().replace("@", "")
                                    if handle_part and handle_part.lower() not in IGNORED_HANDLES:
                                        return handle_part.lower()
            except Exception as e:
                logger.error(f"Error calling Google Custom Search API: {e}")

        handle = await self._search_ddg_instagram(clean_bname, clean_loc)
        if handle:
            return handle

        return await self._search_bing_instagram(clean_bname, clean_loc)

    async def search_profiles_by_sector(
        self, sector_keywords: str, location: str = "", limit: int = 20
    ) -> List[Dict]:
        """
        Deep Sector Search: Discover and extract rich Instagram profiles based on sector keywords & location.
        Uses 5-Layer Hybrid Harvesting + Strict 4-Tier Priority Ranking.
        """
        sec_clean = sector_keywords.strip()
        loc_clean = _clean_location_for_search(location)
        if not sec_clean:
            return []

        target_limit = 50000 if (limit <= 0 or limit >= 50000) else limit
        logger.info(f"Starting 5-Layer Hybrid Instagram sector search for keywords='{sec_clean}', loc='{loc_clean}', target_limit={target_limit}")

        found_handles: Set[str] = set()

        # -------------------------------------------------------------------
        # LAYER 1: Expanded Sector & Dictionary Handle Generator Engine (3000+ candidates)
        # -------------------------------------------------------------------
        sec_ascii = _slugify_tr(sec_clean)
        loc_ascii = _slugify_tr(loc_clean) if loc_clean else ""

        sec_words = [w for w in re.split(r"\s+", sec_ascii) if len(w) >= 3]
        main_sec = sec_words[0] if sec_words else sec_ascii

        # Find matching synonyms or build term list
        synonyms = [main_sec]
        for key, syn_list in SECTOR_SYNONYMS_MAP.items():
            if key in sec_clean.lower() or _slugify_tr(key) in sec_ascii:
                synonyms.extend(syn_list)
        synonyms = list(set(synonyms))

        cities_to_use = [loc_ascii] if loc_ascii else TURKEY_MAJOR_CITIES[:15]
        prefixes = ["", "salon_", "studio_", "official_", "resmi_", "vip_", "butik_", "center_", "uzman_", "pro_", "akademisi_"]
        suffixes = [
            "", "_salonu", "_randevu", "_studio", "_hair", "_beauty", "_center",
            "_design", "_official", "_turkiye", "_ofisi", "_uzmani", "_atolyeyi",
            "_boutique", "_guzellik", "_tr", "_vip", "_pro"
        ]

        for term in synonyms[:8]:
            for p in prefixes:
                for s in suffixes:
                    h = f"{p}{term}{s}".strip("_")
                    if len(h) >= 3 and h not in IGNORED_HANDLES:
                        found_handles.add(h)

            for city in cities_to_use:
                if city:
                    found_handles.add(f"{term}_{city}")
                    found_handles.add(f"{city}_{term}")
                    found_handles.add(f"salon_{term}_{city}")

        # -------------------------------------------------------------------
        # LAYER 2: Social Media OSINT Harvest Provider Integration
        # -------------------------------------------------------------------
        try:
            from aegisScout.discovery.social_media_provider import SocialMediaDiscoveryProvider
            sm_provider = SocialMediaDiscoveryProvider()
            sm_leads = await sm_provider.search(sec_clean, loc_clean)
            for lead in sm_leads:
                h_candidate = getattr(lead, "instagram_handle", None) or getattr(lead, "instagram_url", None) or ""
                if h_candidate:
                    clean_h = str(h_candidate).split("/")[-1].split("?")[0].strip().lower().replace("@", "")
                    if clean_h and clean_h not in IGNORED_HANDLES:
                        found_handles.add(clean_h)
        except Exception as e:
            logger.debug(f"SocialMediaDiscoveryProvider harvest notice: {e}")

        # -------------------------------------------------------------------
        # LAYER 3: Turkish Directory Providers Integration (Bulurum, Haritane, FindComTr)
        # -------------------------------------------------------------------
        try:
            from aegisScout.discovery.bulurum_provider import BulurumDiscoveryProvider
            from aegisScout.discovery.haritane_provider import HaritaneDiscoveryProvider
            from aegisScout.discovery.findcomtr_provider import FindComTrDiscoveryProvider

            for ProvClass in [BulurumDiscoveryProvider, HaritaneDiscoveryProvider, FindComTrDiscoveryProvider]:
                try:
                    prov_inst = ProvClass()
                    p_leads = await prov_inst.search(sec_clean, loc_clean)
                    for lead in p_leads:
                        h_cand = getattr(lead, "instagram_handle", None) or getattr(lead, "instagram_url", None) or ""
                        if h_cand:
                            clean_h = str(h_cand).split("/")[-1].split("?")[0].strip().lower().replace("@", "")
                            if clean_h and clean_h not in IGNORED_HANDLES:
                                found_handles.add(clean_h)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Directory providers harvest notice: {e}")

        # -------------------------------------------------------------------
        # LAYER 4: Search Engine Snippet Harvesting (Bing & DuckDuckGo)
        # -------------------------------------------------------------------
        queries = [
            f'"{sec_clean}" instagram',
            f'{sec_clean} instagram',
            f'{sec_clean} randevu instagram',
            f'{sec_clean} whatsapp instagram',
        ]

        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True, headers=self.browser_headers) as client:
            for q in queries[:2]:
                for page in range(1, 3):
                    first_p = (page - 1) * 10 + 1
                    try:
                        url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}&first={first_p}"
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            found_handles.update(_extract_handles_from_content(resp.text))
                    except Exception:
                        pass

        sec_words_clean = [w for w in re.split(r"\s+", _slugify_tr(sec_clean)) if len(w) >= 3]
        loc_words_clean = [w for w in re.split(r"\s+", _slugify_tr(loc_clean)) if len(w) >= 3]

        def candidate_sort_key(h: str) -> tuple:
            score = 0
            for w in sec_words_clean:
                if w in h:
                    score += 10
            for w in loc_words_clean:
                if w in h:
                    score += 5
            return (score, -len(h))

        sorted_handles = sorted(list(found_handles), key=candidate_sort_key, reverse=True)
        handles_to_fetch = sorted_handles[:target_limit]
        logger.info(f"Found {len(found_handles)} total candidate handles, fetching detailed profiles for {len(handles_to_fetch)} handles...")

        # -------------------------------------------------------------------
        # LAYER 5: OpenGraph Profile Extraction & Detail Enrichment
        # -------------------------------------------------------------------
        results: List[Dict] = []
        batch_size = 10
        for i in range(0, len(handles_to_fetch), batch_size):
            batch = handles_to_fetch[i:i + batch_size]
            tasks = [self.fetch_profile_details(handle, sec_clean) for handle in batch]
            fetched = await asyncio.gather(*tasks, return_exceptions=True)
            for res in fetched:
                if isinstance(res, dict) and res.get("username"):
                    results.append(res)
            await asyncio.sleep(0.1)

        # -------------------------------------------------------------------
        # STRICT 4-TIER PRIORITY RANKING & SORTING ALGORITHM
        # User Specification:
        # Rank 1: Sector keyword is inside Username (@handle)
        # Rank 2: Sector keyword is inside Full Name / Title
        # Rank 3: Sector keyword is inside Bio / Description
        # Rank 4: Other matching business candidates
        # -------------------------------------------------------------------
        def calculate_priority_tuple(p: Dict) -> tuple:
            u_name = p.get("username", "").lower()
            f_name = p.get("full_name", "").lower()
            bio_t = p.get("bio", "").lower()
            
            sec_terms = [w.lower() for w in sec_clean.split() if len(w) >= 3]
            sec_ascii_terms = [w for w in re.split(r"\s+", _slugify_tr(sec_clean)) if len(w) >= 3]

            rank = 4
            if any(st in u_name for st in sec_ascii_terms):
                rank = 1
            elif any(st in f_name for st in sec_terms):
                rank = 2
            elif any(st in bio_t for st in sec_terms):
                rank = 3

            contact_score = 0
            if p.get("email"):
                contact_score += 2
            if p.get("phone") or p.get("whatsapp_link"):
                contact_score += 2

            verified_score = 1 if p.get("is_verified") else 0
            followers_score = p.get("followers_raw", 0)

            # Sort tuple: (-rank [1 comes first], contact_score, verified_score, relevance_score, followers_score)
            return (-rank, contact_score, verified_score, p.get("relevance_score", 0), followers_score)

        results.sort(key=calculate_priority_tuple, reverse=True)
        return results

    async def fetch_profile_details(self, username: str, target_sector: str = "") -> Dict:
        """
        Extract detailed metadata for a single Instagram profile using Googlebot/Bingbot headers.
        Parses both English & Turkish OpenGraph tags (Takipçi, Takip, Gönderi / Followers, Following, Posts).
        """
        clean_user = username.strip().lower().replace("@", "")
        default_data = {
            "username": clean_user,
            "full_name": clean_user.replace("_", " ").title(),
            "profile_url": f"https://www.instagram.com/{clean_user}/",
            "profile_pic_url": "",
            "bio": "",
            "followers": "N/A",
            "followers_raw": 0,
            "following": "N/A",
            "posts": "N/A",
            "is_verified": False,
            "is_business": True,
            "category": target_sector or "İşletme / Hizmet",
            "email": None,
            "phone": None,
            "whatsapp_link": None,
            "website": None,
            "relevance_score": 75,
        }

        if not clean_user or clean_user in IGNORED_HANDLES:
            return default_data

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                page_url = f"https://www.instagram.com/{clean_user}/"
                resp = await client.get(page_url, headers=self.browser_headers)

                if resp.status_code == 200:
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")

                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        default_data["profile_pic_url"] = og_image["content"]

                    og_title = soup.find("meta", property="og:title")
                    if og_title and og_title.get("content"):
                        title_val = og_title["content"]
                        name_match = re.search(r"^(.*?)\s*\(@", title_val)
                        if name_match:
                            default_data["full_name"] = name_match.group(1).strip()
                        else:
                            default_data["full_name"] = title_val.split("•")[0].split("-")[0].strip()

                    og_desc = soup.find("meta", property="og:description")
                    if og_desc and og_desc.get("content"):
                        desc_val = og_desc["content"]
                        
                        # Match both English & Turkish OpenGraph stats format
                        stats_match = re.search(
                            r"([\d\.,KMBkmb]+)\s+(?:Followers|Takipçi),\s+([\d\.,KMBkmb]+)\s+(?:Following|Takip),\s+([\d\.,KMBkmb]+)\s+(?:Posts|Gönderi|Gonderi)",
                            desc_val,
                            re.IGNORECASE,
                        )
                        if stats_match:
                            default_data["followers"] = stats_match.group(1)
                            default_data["following"] = stats_match.group(2)
                            default_data["posts"] = stats_match.group(3)
                            default_data["followers_raw"] = self._parse_count(stats_match.group(1))

                        # Extract bio text
                        if " - " in desc_val:
                            bio_part = desc_val.split(" - ", 1)[-1]
                            if ":" in bio_part:
                                default_data["bio"] = bio_part.split(":", 1)[-1].strip().strip('"').strip("'")
                            elif "@" in bio_part:
                                default_data["bio"] = bio_part.strip()

                    if "verified" in html.lower() or "doğrulanmış" in html.lower():
                        default_data["is_verified"] = True

        except Exception as e:
            logger.debug(f"Profile fetch exception for @{clean_user}: {e}")

        full_text = f"{default_data['full_name']} {default_data['bio']} {default_data.get('website', '')}"
        default_data["email"] = self._extract_email(full_text)
        phone, wp_link = self._extract_phone_and_whatsapp(full_text)
        default_data["phone"] = phone
        default_data["whatsapp_link"] = wp_link
        if not default_data["website"]:
            default_data["website"] = self._extract_website(full_text)

        default_data["relevance_score"] = self._calculate_relevance_score(default_data, target_sector)

        return default_data

    async def find_similar_profiles(
        self, username: str, category: str = "", location: str = "", limit: int = 10
    ) -> List[Dict]:
        """
        Semantic Benzer Bul Algorithm: Resolves category synonyms and sub-sectors instead of naive keyword suffixing.
        """
        sec_term = (category or username).lower().strip()
        synonyms = [sec_term]
        for k, v in SECTOR_SYNONYMS_MAP.items():
            if k in sec_term or sec_term in k:
                synonyms.extend(v[:3])

        expanded_query = " ".join(list(set(synonyms))[:3])
        logger.info(f"Semantic Benzer Bul running for @{username} with expanded query '{expanded_query}'")
        return await self.search_profiles_by_sector(expanded_query, location, limit)

    def _parse_count(self, text: str) -> int:
        if not text:
            return 0
        text = text.replace(",", ".").strip().upper()
        try:
            if "M" in text:
                return int(float(text.replace("M", "")) * 1_000_000)
            if "K" in text or "B" in text:
                return int(float(text.replace("K", "").replace("B", "")) * 1_000)
            return int(float(text))
        except ValueError:
            return 0

    def _format_count(self, num: int) -> str:
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M".replace(".0M", "M")
        if num >= 1_000:
            return f"{num / 1_000:.1f}K".replace(".0K", "K")
        return str(num)

    def _extract_email(self, text: str) -> Optional[str]:
        if not text:
            return None
        m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        if m:
            email = m.group(0).lower()
            ignored = {"example.com", "domain.com", "instagram.com"}
            if not any(i in email for i in ignored):
                return email
        return None

    def _extract_phone_and_whatsapp(self, text: str) -> tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        wp_match = re.search(r"https?://(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)", text)
        if wp_match:
            d = wp_match.group(1)
            return f"+{d}", f"https://wa.me/{d}"

        p_patterns = [
            r"\+?90\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}",
            r"\b0\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}\b",
            r"\b\d{3}\s*\d{3}\s*\d{2}\s*\d{2}\b",
        ]
        for p in p_patterns:
            m = re.search(p, text)
            if m:
                raw = m.group(0)
                digits = re.sub(r"\D", "", raw)
                if len(digits) == 10 and digits.startswith("5"):
                    return f"+90{digits}", f"https://wa.me/90{digits}"
                elif len(digits) == 11 and digits.startswith("05"):
                    return f"+90{digits[1:]}", f"https://wa.me/90{digits[1:]}"
                elif len(digits) == 12 and digits.startswith("90"):
                    return f"+{digits}", f"https://wa.me/{digits}"
                elif len(digits) == 10:
                    return f"0{digits}", None
        return None, None

    def _extract_website(self, text: str) -> Optional[str]:
        if not text:
            return None
        m = re.search(r"https?://[^\s<\"']+", text)
        if m:
            url = m.group(0).rstrip(".,;")
            if "instagram.com" not in url and "facebook.com" not in url:
                return url
        return None

    def _calculate_relevance_score(self, profile: Dict, target_sector: str) -> int:
        score = 60
        if not target_sector:
            return score
        
        keywords = [w.lower() for w in target_sector.split() if len(w) > 2]
        text = f"{profile.get('full_name', '')} {profile.get('bio', '')} {profile.get('category', '')}".lower()
        
        match_count = sum(1 for k in keywords if k in text)
        score += min(match_count * 12, 35)

        if profile.get("email"):
            score += 5
        if profile.get("phone"):
            score += 5
        if profile.get("is_verified"):
            score += 5
            
        return min(score, 99)

    async def _search_ddg_instagram(self, business_name: str, location: str) -> Optional[str]:
        queries = [
            f'site:instagram.com "{business_name}" {location}'.strip(),
            f'site:instagram.com {business_name} {location}'.strip()
        ]
        for idx, query in enumerate(queries):
            try:
                encoded_query = urllib.parse.quote(query)
                url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                async with httpx.AsyncClient(timeout=3.5, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.browser_headers)
                    if response.status_code == 200:
                        handles = _extract_handles_from_content(response.text)
                        if handles:
                            return list(handles)[0]
            except Exception as e:
                logger.error(f"Error scraping DuckDuckGo for Instagram on query '{query}': {e}")
        return None

    async def _search_bing_instagram(self, business_name: str, location: str) -> Optional[str]:
        query = f'site:instagram.com "{business_name}" {location}'.strip()
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        try:
            async with httpx.AsyncClient(timeout=3.5, follow_redirects=True) as client:
                response = await client.get(url, headers=self.browser_headers)
                if response.status_code == 200:
                    handles = _extract_handles_from_content(response.text)
                    if handles:
                        return list(handles)[0]
        except Exception as e:
            logger.error(f"Error scraping Bing for Instagram on query '{query}': {e}")
        return None



