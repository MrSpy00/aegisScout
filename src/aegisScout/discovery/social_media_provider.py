"""
Social Media OSINT Discovery Provider for aegisScout.
Discovers business leads directly from social media platforms:
- Instagram
- TikTok
- Facebook
- LinkedIn
- Twitter / X
- GitHub
"""
import asyncio
import re
import urllib.parse
from typing import Dict, List, Optional, Set

import httpx
from bs4 import BeautifulSoup

from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.social_media")


class SocialMediaDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery Provider that harvests business leads directly from social platforms
    (Instagram, TikTok, Facebook, LinkedIn, Twitter/X, GitHub).
    Uses public endpoints, web scraping, and OSINT techniques.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.instagram_api_headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 290.0.0.16.117"
            ),
            "X-IG-App-ID": "936619743392459",
            "Accept": "*/*",
        }
        self.nitter_instances = [
            "https://nitter.poast.org",
            "https://nitter.cz",
            "https://nitter.privacydev.net",
        ]

    def _generate_keywords_and_hashtags(
        self, sector: str, location: str
    ) -> Dict[str, List[str]]:
        """Generate targeted keyword list and hashtags from sector and location."""
        sec_clean = sector.strip().lower()
        loc_clean = location.strip().lower()
        loc_words = [w for w in loc_clean.replace(",", " ").split() if len(w) > 2]
        main_loc = loc_words[0] if loc_words else ""

        # Turkish character to ascii mapping for tags
        tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGISOU")
        sec_tag = sec_clean.translate(tr_map).replace(" ", "")
        loc_tag = main_loc.translate(tr_map).replace(" ", "")

        hashtags = [
            sec_tag,
            f"{sec_tag}{loc_tag}",
            f"{loc_tag}{sec_tag}",
        ]
        if " " in sec_clean:
            # e.g., "diş kliniği" -> "disklinigi"
            hashtags.append(sec_clean.split()[0].translate(tr_map))

        query_phrases = [
            f"{sector} {location}",
            f"{sector} kliniği {location}" if "klinik" not in sec_clean else f"{sector} {location}",
            f"{sector} danışmanlık {location}",
            f"{sector} ofisi {location}",
            f"{sector} firması {location}",
        ]

        return {
            "hashtags": list(set([h for h in hashtags if len(h) >= 3])),
            "phrases": list(set(query_phrases)),
        }

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        if not text:
            return None
        match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if match:
            email = match.group(0).lower()
            ignored = {"example.com", "domain.com", "sentry.io", "wix.com"}
            if not any(i in email for i in ignored):
                return email
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract Turkish / International phone number from text."""
        if not text:
            return None
        patterns = [
            r"\+?90\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}",
            r"\b0\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}\b",
            r"\b\d{3}\s*\d{3}\s*\d{2}\s*\d{2}\b",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                raw = m.group(0)
                digits = re.sub(r"\D", "", raw)
                if len(digits) == 10 and digits.startswith("5"):
                    return f"+90{digits}"
                elif len(digits) == 11 and digits.startswith("05"):
                    return f"+90{digits[1:]}"
                elif len(digits) == 12 and digits.startswith("90"):
                    return f"+{digits}"
                elif len(digits) == 10:
                    return f"0{digits}"
        return None

    def _extract_whatsapp(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract WhatsApp phone number and direct wa.me URL if present."""
        if not text:
            return None, None
        m_url = re.search(r"https?://(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)", text)
        if m_url:
            digits = m_url.group(1)
            return f"+{digits}", f"https://wa.me/{digits}"
        m_wp = re.search(r"(?:whatsapp|wp|wa)\s*:?\s*(\+?90\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}|\b0?5\d{9}\b)", text, re.IGNORECASE)
        if m_wp:
            raw = m_wp.group(1)
            digits = re.sub(r"\D", "", raw)
            if len(digits) == 10 and digits.startswith("5"):
                return f"+90{digits}", f"https://wa.me/90{digits}"
            elif len(digits) == 11 and digits.startswith("05"):
                return f"+90{digits[1:]}", f"https://wa.me/90{digits[1:]}"
            elif len(digits) == 12 and digits.startswith("90"):
                return f"+{digits}", f"https://wa.me/{digits}"
        return None, None

    def _is_likely_business(self, profile: dict, sector: str) -> bool:
        """Determine whether a profile represents a business / professional service."""
        bio = str(profile.get("bio", "")).lower()
        name = str(profile.get("name", "")).lower()
        sector_words = sector.lower().split()

        # Sector word match in name or bio
        if any(w in bio or w in name for w in sector_words if len(w) > 2):
            return True

        # Business indicator keywords
        business_signals = [
            "ltd",
            "a.ş.",
            "inc",
            "corp",
            "kliniği",
            "merkezi",
            "ofisi",
            "hizmetleri",
            "firması",
            "şirketi",
            "®",
            "™",
            "randevu",
            "seans",
            "terapi",
            "danışmanlık",
            "iletişim",
            "adres",
            "tel:",
            "sipariş",
            "booking",
            "official",
            "resmi",
            "studio",
            "stüdyosu",
            "salon",
            "salonu",
            "atolye",
            "atölye",
        ]
        if any(s in bio or s in name for s in business_signals):
            return True

        # Has email or phone or website link
        if profile.get("phone") or profile.get("email") or profile.get("website"):
            return True

        return False

    # ---------------------------------------------------------------------------
    # Platform 1: Instagram
    # ---------------------------------------------------------------------------
    async def _search_instagram(
        self, hashtags: List[str], phrases: List[str], sector: str, client: httpx.AsyncClient
    ) -> List[LeadCandidate]:
        candidates: List[LeadCandidate] = []
        found_users: Set[str] = set()

        for tag in hashtags[:3]:
            try:
                url = f"https://www.instagram.com/api/v1/tags/web_info/?tag_name={urllib.parse.quote(tag)}"
                resp = await client.get(url, headers=self.instagram_api_headers, timeout=6.0)
                if resp.status_code == 200:
                    data = resp.json()
                    sections = data.get("data", {}).get("top", {}).get("sections", [])
                    for sec in sections:
                        medias = sec.get("layout_content", {}).get("medias", [])
                        for m in medias:
                            user = m.get("media", {}).get("user", {})
                            username = user.get("username")
                            if username and username not in found_users:
                                found_users.add(username)
            except Exception as e:
                logger.debug(f"Instagram tag search failed for #{tag}: {e}")

        # Fallback to search query for Instagram usernames via keyless DDG JSON/HTML
        for phrase in phrases[:2]:
            try:
                q = f"site:instagram.com {phrase}"
                ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(q)}&format=json"
                resp = await client.get(ddg_url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    text = resp.text
                    handles = re.findall(r"instagram\.com/([a-zA-Z0-9_.-]{3,30})", text)
                    for h in handles:
                        if h.lower() not in {"p", "explore", "reels", "stories", "about", "terms", "legal"}:
                            found_users.add(h.lower())
            except Exception:
                pass

        # Fetch profile metadata for discovered usernames
        for username in list(found_users)[:12]:
            try:
                profile_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
                resp = await client.get(profile_url, headers=self.instagram_api_headers, timeout=6.0)
                if resp.status_code == 200:
                    user_data = resp.json().get("data", {}).get("user")
                    if not user_data:
                        continue
                    full_name = user_data.get("full_name") or username
                    biography = user_data.get("biography") or ""
                    external_url = user_data.get("external_url")
                    profile_pic = user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url")
                    category = user_data.get("category_name") or ""

                    full_bio = f"{category} {biography}".strip()
                    email = self._extract_email(full_bio)
                    phone = self._extract_phone(full_bio)

                    profile_info = {
                        "name": full_name,
                        "bio": full_bio,
                        "email": email,
                        "phone": phone,
                        "website": external_url,
                    }

                    wp_phone, wp_url = self._extract_whatsapp(full_bio)
                    if not phone and wp_phone:
                        phone = wp_phone

                    if self._is_likely_business(profile_info, sector):
                        candidate = LeadCandidate(
                            business_name=full_name,
                            sector=sector,
                            instagram_handle=username,
                            instagram_url=f"https://instagram.com/{username}",
                            instagram_bio=biography,
                            website_url=external_url,
                            has_website=bool(external_url),
                            phone=phone,
                            email=email,
                            whatsapp_url=wp_url,
                            profile_image_url=profile_pic,
                            source="social_media",
                            _osint_data={"platform": "instagram", "category": category, "bio": biography, "username": username},
                        )
                        candidates.append(candidate)
            except Exception as e:
                logger.debug(f"Instagram profile fetch error for @{username}: {e}")

        return candidates

    # ---------------------------------------------------------------------------
    # Platform 2: TikTok
    # ---------------------------------------------------------------------------
    async def _search_tiktok(
        self, phrases: List[str], sector: str, client: httpx.AsyncClient
    ) -> List[LeadCandidate]:
        candidates: List[LeadCandidate] = []
        found_users: Set[str] = set()

        for phrase in phrases[:2]:
            try:
                q = f"site:tiktok.com/@ {phrase}"
                url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    handles = re.findall(r"tiktok\.com/@([a-zA-Z0-9_.-]{3,30})", resp.text)
                    for h in handles:
                        found_users.add(h.lower())
            except Exception:
                pass

        for username in list(found_users)[:8]:
            try:
                url = f"https://www.tiktok.com/@{username}"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    title_elem = soup.find("h1") or soup.find("h2") or soup.find("title")
                    name = title_elem.get_text(strip=True) if title_elem else username
                    name = re.sub(r"\s*\(?@.*", "", name).strip()

                    meta_desc = soup.find("meta", attrs={"name": "description"})
                    bio = meta_desc.get("content", "") if meta_desc else ""

                    email = self._extract_email(bio)
                    phone = self._extract_phone(bio)
                    wp_phone, wp_url = self._extract_whatsapp(bio)
                    if not phone and wp_phone:
                        phone = wp_phone

                    profile_info = {"name": name, "bio": bio, "email": email, "phone": phone}

                    if self._is_likely_business(profile_info, sector):
                        candidates.append(
                            LeadCandidate(
                                business_name=name or f"@{username}",
                                sector=sector,
                                tiktok_url=f"https://www.tiktok.com/@{username}",
                                instagram_bio=bio[:300] if bio else None,
                                email=email,
                                phone=phone,
                                whatsapp_url=wp_url,
                                source="social_media",
                                _osint_data={"platform": "tiktok", "username": username, "bio": bio},
                            )
                        )
            except Exception:
                pass

        return candidates

    # ---------------------------------------------------------------------------
    # Platform 3: Facebook Pages
    # ---------------------------------------------------------------------------
    async def _search_facebook(
        self, phrases: List[str], sector: str, client: httpx.AsyncClient
    ) -> List[LeadCandidate]:
        candidates: List[LeadCandidate] = []
        found_pages: Set[str] = set()

        for phrase in phrases[:2]:
            try:
                q = f"site:facebook.com {phrase}"
                url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    urls = re.findall(r"https?://(?:www\.)?facebook\.com/([a-zA-Z0-9_.-]{4,50})", resp.text)
                    ignored = {"groups", "events", "people", "watch", "story", "login", "pages", "help", "privacy"}
                    for p in urls:
                        if p.lower() not in ignored and not p.isdigit():
                            found_pages.add(p.lower())
            except Exception:
                pass

        for slug in list(found_pages)[:8]:
            try:
                url = f"https://www.facebook.com/{slug}?locale=tr_TR"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    og_title = soup.find("meta", property="og:title")
                    og_desc = soup.find("meta", property="og:description")
                    title = og_title.get("content") if og_title else slug
                    bio = og_desc.get("content") if og_desc else ""

                    clean_name = re.sub(r"\s*[-|•]\s*Home.*", "", title, flags=re.I).strip()
                    clean_name = re.sub(r"\s*[-|•]\s*Ana Sayfa.*", "", clean_name, flags=re.I).strip()

                    email = self._extract_email(bio)
                    phone = self._extract_phone(bio)
                    wp_phone, wp_url = self._extract_whatsapp(bio)
                    if not phone and wp_phone:
                        phone = wp_phone

                    profile_info = {"name": clean_name, "bio": bio, "email": email, "phone": phone}

                    if self._is_likely_business(profile_info, sector):
                        candidates.append(
                            LeadCandidate(
                                business_name=clean_name,
                                sector=sector,
                                facebook_url=f"https://www.facebook.com/{slug}",
                                instagram_bio=bio[:300] if bio else None,
                                email=email,
                                phone=phone,
                                whatsapp_url=wp_url,
                                source="social_media",
                                _osint_data={"platform": "facebook", "slug": slug, "bio": bio},
                            )
                        )
            except Exception:
                pass

        return candidates

    # ---------------------------------------------------------------------------
    # Platform 4: LinkedIn Companies
    # ---------------------------------------------------------------------------
    async def _search_linkedin(
        self, phrases: List[str], sector: str, client: httpx.AsyncClient
    ) -> List[LeadCandidate]:
        candidates: List[LeadCandidate] = []
        found_companies: Set[str] = set()

        for phrase in phrases[:2]:
            try:
                q = f"site:linkedin.com/company {phrase}"
                url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    slugs = re.findall(r"linkedin\.com/company/([a-zA-Z0-9_.-]{3,50})", resp.text)
                    for s in slugs:
                        found_companies.add(s.lower())
            except Exception:
                pass

        for slug in list(found_companies)[:8]:
            try:
                url = f"https://www.linkedin.com/company/{slug}"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    og_title = soup.find("meta", property="og:title")
                    og_desc = soup.find("meta", property="og:description")
                    title = og_title.get("content") if og_title else slug
                    bio = og_desc.get("content") if og_desc else ""

                    clean_name = re.sub(r"\s*:\s*Overview.*", "", title, flags=re.I)
                    clean_name = re.sub(r"\s*\|\s*LinkedIn.*", "", clean_name, flags=re.I).strip()

                    email = self._extract_email(bio)
                    phone = self._extract_phone(bio)
                    wp_phone, wp_url = self._extract_whatsapp(bio)

                    candidates.append(
                        LeadCandidate(
                            business_name=clean_name,
                            sector=sector,
                            linkedin_url=f"https://www.linkedin.com/company/{slug}",
                            instagram_bio=bio[:300] if bio else None,
                            email=email,
                            phone=phone or wp_phone,
                            whatsapp_url=wp_url,
                            source="social_media",
                            _osint_data={"platform": "linkedin", "slug": slug, "bio": bio},
                        )
                    )
            except Exception:
                pass

        return candidates

    # ---------------------------------------------------------------------------
    # Platform 5: Twitter / X
    # ---------------------------------------------------------------------------
    async def _search_twitter(
        self, phrases: List[str], sector: str, client: httpx.AsyncClient
    ) -> List[LeadCandidate]:
        candidates: List[LeadCandidate] = []
        found_users: Set[str] = set()

        for phrase in phrases[:2]:
            try:
                q = f"site:twitter.com OR site:x.com {phrase}"
                url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
                resp = await client.get(url, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    handles = re.findall(r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{3,20})", resp.text)
                    ignored = {"home", "explore", "notifications", "messages", "search", "settings", "i", "tos", "privacy"}
                    for h in handles:
                        if h.lower() not in ignored:
                            found_users.add(h.lower())
            except Exception:
                pass

        for username in list(found_users)[:6]:
            for instance in self.nitter_instances[:2]:
                try:
                    url = f"{instance}/{username}"
                    resp = await client.get(url, headers=self.headers, timeout=4.0)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        fullname_elem = soup.find("a", class_="profile-card-fullname")
                        bio_elem = soup.find("div", class_="profile-bio")
                        name = fullname_elem.get_text(strip=True) if fullname_elem else username
                        bio = bio_elem.get_text(strip=True) if bio_elem else ""

                        email = self._extract_email(bio)
                        phone = self._extract_phone(bio)
                        wp_phone, wp_url = self._extract_whatsapp(bio)

                        profile_info = {"name": name, "bio": bio, "email": email, "phone": phone}

                        if self._is_likely_business(profile_info, sector):
                            candidates.append(
                                LeadCandidate(
                                    business_name=name,
                                    sector=sector,
                                    twitter_url=f"https://x.com/{username}",
                                    instagram_bio=bio[:300] if bio else None,
                                    email=email,
                                    phone=phone or wp_phone,
                                    whatsapp_url=wp_url,
                                    source="social_media",
                                    _osint_data={"platform": "twitter", "username": username, "bio": bio},
                                )
                            )
                        break
                except Exception:
                    continue

        return candidates

    # ---------------------------------------------------------------------------
    # Platform 6: GitHub Organizations
    # ---------------------------------------------------------------------------
    async def _search_github(
        self, phrases: List[str], sector: str, client: httpx.AsyncClient
    ) -> List[LeadCandidate]:
        candidates: List[LeadCandidate] = []
        found_orgs: Set[str] = set()

        for phrase in phrases[:2]:
            try:
                kw = urllib.parse.quote(phrase)
                url = f"https://api.github.com/search/users?q={kw}+type:org"
                resp = await client.get(
                    url,
                    headers={"User-Agent": "aegisScout-OSINT/1.0", "Accept": "application/vnd.github.v3+json"},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    for item in items:
                        login = item.get("login")
                        if login:
                            found_orgs.add(login)
            except Exception:
                pass

        for org in list(found_orgs)[:6]:
            try:
                url = f"https://api.github.com/orgs/{org}"
                resp = await client.get(
                    url,
                    headers={"User-Agent": "aegisScout-OSINT/1.0", "Accept": "application/vnd.github.v3+json"},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    name = data.get("name") or org
                    bio = data.get("description") or ""
                    email = data.get("email")
                    blog = data.get("blog")
                    location_val = data.get("location")
                    avatar = data.get("avatar_url")

                    if blog and not blog.startswith("http"):
                        blog = f"https://{blog}"

                    wp_phone, wp_url = self._extract_whatsapp(bio)

                    candidates.append(
                        LeadCandidate(
                            business_name=name,
                            sector=sector,
                            address=location_val,
                            website_url=blog,
                            has_website=bool(blog),
                            email=email,
                            github_url=f"https://github.com/{org}",
                            whatsapp_url=wp_url,
                            profile_image_url=avatar,
                            instagram_bio=bio[:300] if bio else None,
                            source="social_media",
                            _osint_data={"platform": "github", "org": org, "bio": bio},
                        )
                    )
            except Exception:
                pass

        return candidates
                pass

        return candidates

    # ---------------------------------------------------------------------------
    # Main Search Entry Point
    # ---------------------------------------------------------------------------
    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Main entry point for multi-platform Social Media OSINT discovery.
        Harvests profiles from Instagram, TikTok, Facebook, LinkedIn, Twitter/X, and GitHub.
        """
        logger.info(f"Starting Social Media OSINT discovery for '{sector}' in '{location}'...")

        kw_data = self._generate_keywords_and_hashtags(sector, location)
        hashtags = kw_data["hashtags"]
        phrases = kw_data["phrases"]

        all_candidates: List[LeadCandidate] = []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [
                self._search_instagram(hashtags, phrases, sector, client),
                self._search_tiktok(phrases, sector, client),
                self._search_facebook(phrases, sector, client),
                self._search_linkedin(phrases, sector, client),
                self._search_twitter(phrases, sector, client),
                self._search_github(phrases, sector, client),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    all_candidates.extend(res)

        # Deduplicate candidates by business name or handle/URL
        seen_keys: Set[str] = set()
        deduped: List[LeadCandidate] = []

        for c in all_candidates:
            key = None
            if c.instagram_handle:
                key = f"insta:{c.instagram_handle}"
            elif c.website_url:
                key = f"web:{c.website_url.lower().rstrip('/')}"
            elif c.facebook_url:
                key = f"fb:{c.facebook_url.lower()}"
            elif c.linkedin_url:
                key = f"li:{c.linkedin_url.lower()}"
            elif c.twitter_url:
                key = f"tw:{c.twitter_url.lower()}"
            elif c.tiktok_url:
                key = f"tt:{c.tiktok_url.lower()}"
            else:
                key = f"name:{c.business_name.strip().lower()}"

            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(c)

        logger.info(
            f"Social Media OSINT discovery finished: harvested {len(deduped)} unique leads from {len(all_candidates)} total hits."
        )
        return deduped
