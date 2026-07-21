"""
Media, Logo, Avatar & Web Screenshot Resolver (Zero-Config / Keyless).
Provides keyless high-res domain logos, multi-social avatars, colorful UI-Avatars, and instant web screenshot thumbnails.
"""

from typing import Optional
import urllib.parse
from aegisScout.enrichment.domain_audit import extract_clean_domain
from aegisScout.utils.logger import get_logger

logger = get_logger("enrichment.media_resolver")


class ZeroConfigMediaResolver:
    """
    Zero-config image and media resolver for lead cards, avatars, and website screenshots.
    """

    @staticmethod
    def get_domain_logo_url(domain_or_url: str, size: int = 128) -> Optional[str]:
        """
        Fetch high-res domain logo via Google Favicon Public API.
        %100 Free, Zero API key required.
        """
        domain = extract_clean_domain(domain_or_url)
        if not domain:
            return None
        return f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"

    @staticmethod
    def get_unavatar_url(query_or_domain: str) -> Optional[str]:
        """
        Fetch multi-social profile avatar (Gravatar, Twitter, Telegram, YouTube) via Unavatar.
        %100 Free, Zero API key required.
        """
        if not query_or_domain or not isinstance(query_or_domain, str):
            return None
        clean = query_or_domain.strip().lower()
        if clean.startswith("@"):
            clean = clean[1:]
        encoded = urllib.parse.quote(clean)
        return f"https://unavatar.io/{encoded}"

    @staticmethod
    def get_initials_avatar_url(name: str, background_color: str = "4f46e5", color: str = "ffffff") -> str:
        """
        Generate dynamic SVG/PNG initials avatar for leads without photo or logo.
        %100 Free, Zero API key required.
        """
        clean_name = name.strip() if name else "Lead"
        encoded = urllib.parse.quote(clean_name)
        return f"https://ui-avatars.com/api/?name={encoded}&background={background_color}&color={color}&bold=true&size=128"

    @staticmethod
    def get_web_screenshot_thumbnail(url: str, width: int = 1200, crop: int = 800) -> Optional[str]:
        """
        Generate instant website screenshot thumbnail via Thum.io public endpoint.
        %100 Free, Zero API key required.
        """
        if not url:
            return None
        raw_url = url.strip()
        if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
            raw_url = "https://" + raw_url
        return f"https://image.thum.io/get/width/{width}/crop/{crop}/{raw_url}"

    @staticmethod
    def resolve_best_avatar(
        business_name: str,
        domain_or_url: Optional[str] = None,
        existing_avatar: Optional[str] = None
    ) -> str:
        """
        Fallback chain for lead profile image:
        1. Explicit existing avatar (if non-empty)
        2. Google Favicon logo (if domain/url exists)
        3. UI-Avatars colorful initials avatar (fallback guarantee)
        """
        if existing_avatar and existing_avatar.strip():
            return existing_avatar.strip()

        if domain_or_url:
            logo = ZeroConfigMediaResolver.get_domain_logo_url(domain_or_url)
            if logo:
                return logo

        return ZeroConfigMediaResolver.get_initials_avatar_url(business_name)
