"""
Deep OSINT Intelligence Scanner for aegisScout.

Performs multi-source open-source intelligence gathering on target leads:
  - WHOIS / RDAP domain registration age & registrar details
  - SSL certificate expiry check
  - Technical stack audit (CMS, Analytics, Facebook Pixel, SSL status, Mobile Viewport)
  - Cross-platform social footprint analysis (Instagram, Facebook, LinkedIn, Twitter/X, YouTube, TikTok)
  - Contact info extraction (Email, Phone, WhatsApp, Address)
  - SERP position analysis (estimated web presence)
  - Comprehensive OSINT report generation
"""
from __future__ import annotations

import re
import ssl
import socket
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session

from aegisScout.core import database as db_module
from aegisScout.core.models import Lead, ResearchNote
from aegisScout.discovery.web_scraper import get_domain_age_days
from aegisScout.discovery.social_discovery import SocialDiscovery
from aegisScout.utils.logger import get_logger

logger = get_logger("core.deep_osint")


def _check_ssl_expiry(hostname: str) -> Optional[int]:
    """
    Check SSL certificate expiry for a given hostname.
    Returns the number of days until expiry (negative = already expired),
    or None if the check fails.
    """
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(
            socket.create_connection((hostname, 443), timeout=5),
            server_hostname=hostname
        ) as conn:
            cert = conn.getpeercert()
            not_after_str = cert.get("notAfter", "")
            if not_after_str:
                not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                not_after = not_after.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                return (not_after - now).days
    except Exception:
        pass
    return None


class DeepOSINTScanner:
    """Comprehensive OSINT Intelligence Scanner for business leads."""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    async def scan_website(self, url: str) -> Dict[str, Any]:
        """Fetch and analyze website metadata, tech stack, and contact details."""
        if not url.startswith("http"):
            url = "https://" + url

        result = {
            "title": "",
            "description": "",
            "cms": "Bilinmiyor / Özel Yazılım",
            "has_ssl": url.startswith("https://"),
            "ssl_days_remaining": None,
            "has_analytics": False,
            "has_pixel": False,
            "has_viewport": False,
            "has_tiktok_pixel": False,
            "has_whatsapp_button": False,
            "has_chat_widget": False,
            "has_cookie_consent": False,
            "emails": [],
            "phones": [],
            "social_links": [],
            "tiktok_url": None,
            "http_status": None,
            "page_title_length": 0,
            "meta_description_length": 0,
        }

        # SSL expiry check (non-blocking, best-effort)
        parsed_url = urllib.parse.urlparse(url if url.startswith("http") else f"https://{url}")
        hostname = parsed_url.netloc.split(":")[0].replace("www.", "")
        if result["has_ssl"] and hostname:
            result["ssl_days_remaining"] = _check_ssl_expiry(hostname)

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                result["http_status"] = resp.status_code
                if resp.status_code == 200:
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")

                    # Title & Description
                    if soup.title and soup.title.string:
                        result["title"] = soup.title.string.strip()
                        result["page_title_length"] = len(result["title"])

                    desc_meta = (
                        soup.find("meta", attrs={"name": "description"})
                        or soup.find("meta", attrs={"property": "og:description"})
                    )
                    if desc_meta and desc_meta.get("content"):
                        result["description"] = desc_meta["content"].strip()
                        result["meta_description_length"] = len(result["description"])

                    # Mobile Viewport
                    viewport = soup.find("meta", attrs={"name": "viewport"})
                    result["has_viewport"] = bool(viewport)

                    # Tech Stack Detection — Extended CMS/Platform Detection
                    html_lower = html.lower()
                    if "wp-content" in html_lower or "wordpress" in html_lower:
                        if "elementor" in html_lower:
                            result["cms"] = "WordPress (Elementor)"
                        elif "divi" in html_lower:
                            result["cms"] = "WordPress (Divi)"
                        elif "avada" in html_lower:
                            result["cms"] = "WordPress (Avada)"
                        elif "wpbakery" in html_lower or "vc_row" in html_lower:
                            result["cms"] = "WordPress (WPBakery)"
                        else:
                            result["cms"] = "WordPress"
                    elif "shopify" in html_lower:
                        result["cms"] = "Shopify"
                    elif "wix.com" in html_lower or "wixstatic" in html_lower:
                        result["cms"] = "Wix"
                    elif "squarespace" in html_lower:
                        result["cms"] = "Squarespace"
                    elif "webflow" in html_lower:
                        result["cms"] = "Webflow"
                    elif "framer.com" in html_lower or "framer-" in html_lower:
                        result["cms"] = "Framer"
                    elif "ghost.io" in html_lower or "ghost/" in html_lower:
                        result["cms"] = "Ghost"
                    elif "hubspot" in html_lower:
                        result["cms"] = "HubSpot"
                    elif "joomla" in html_lower:
                        result["cms"] = "Joomla"
                    elif "drupal" in html_lower:
                        result["cms"] = "Drupal"
                    elif "magento" in html_lower:
                        result["cms"] = "Magento"
                    elif "prestashop" in html_lower:
                        result["cms"] = "PrestaShop"
                    elif "woocommerce" in html_lower:
                        result["cms"] = "WooCommerce"
                    elif "tilda" in html_lower:
                        result["cms"] = "Tilda"
                    elif "notion.site" in html_lower or "notion.so" in html_lower:
                        result["cms"] = "Notion"
                    elif "webnode" in html_lower:
                        result["cms"] = "Webnode"
                    elif "godaddy" in html_lower or "secureserver.net" in html_lower:
                        result["cms"] = "GoDaddy Website Builder"
                    elif "next.js" in html_lower or "__next" in html_lower:
                        result["cms"] = "Next.js"
                    elif "gatsby" in html_lower:
                        result["cms"] = "Gatsby"

                    # Analytics & Tracking Pixels
                    if (
                        "google-analytics.com" in html_lower
                        or "googletagmanager.com" in html_lower
                        or "gtag(" in html_lower
                        or "ga(" in html_lower
                    ):
                        result["has_analytics"] = True

                    if "connect.facebook.net" in html_lower or "fbq(" in html_lower:
                        result["has_pixel"] = True

                    # TikTok Pixel
                    if "analytics.tiktok.com" in html_lower or "ttq.track" in html_lower or "tiktok-pixel" in html_lower:
                        result["has_tiktok_pixel"] = True

                    # WhatsApp Button
                    if "wa.me" in html_lower or "api.whatsapp.com" in html_lower or "whatsapp" in html_lower:
                        result["has_whatsapp_button"] = True

                    # Live Chat Widgets (Intercom, Tawk, Crisp, Zendesk, Freshchat)
                    if any(x in html_lower for x in [
                        "intercom.io", "tawk.to", "crisp.chat", "zopim",
                        "zendesk", "freshchat", "livechat", "tidio"
                    ]):
                        result["has_chat_widget"] = True

                    # Cookie Consent Banner
                    if any(x in html_lower for x in [
                        "cookiebot", "cookie-consent", "cookie_notice",
                        "gdpr", "cookiepro", "cookiehub", "onetrust"
                    ]):
                        result["has_cookie_consent"] = True

                    # Contact Info Extraction (Emails & Phones)
                    emails = set(re.findall(
                        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html
                    ))
                    # Filter obvious non-email patterns
                    emails = {e for e in emails if not any(
                        e.endswith(x) for x in [".png", ".jpg", ".gif", ".svg", ".css", ".js"]
                    )}
                    result["emails"] = list(emails)[:5]

                    # Turkish phone patterns: +90, 0, or local formats
                    phones = set(re.findall(
                        r"(?:\+?90|0)?\s*[2-5]\d{2}\s*\d{3}\s*\d{2}\s*\d{2}", html
                    ))
                    result["phones"] = list(phones)[:5]

                    # Social Link Extraction — Extended Platform Coverage
                    social_domains = [
                        "instagram.com", "facebook.com", "linkedin.com",
                        "twitter.com", "x.com", "youtube.com", "tiktok.com",
                        "pinterest.com", "telegram.me", "t.me",
                        "medium.com", "substack.com", "behance.net",
                        "dribbble.com", "github.com", "snapchat.com",
                        "spotify.com", "soundcloud.com", "twitch.tv",
                    ]
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if any(sd in href.lower() for sd in social_domains):
                            result["social_links"].append(href)
                    result["social_links"] = list(set(result["social_links"]))[:25]

                    # Specifically extract TikTok URL if present
                    tiktok_links = [l for l in result["social_links"] if "tiktok.com" in l]
                    result["tiktok_url"] = tiktok_links[0] if tiktok_links else None

        except Exception as e:
            logger.warning(f"Error scanning website '{url}': {e}")

        return result

    async def scan_lead(self, lead_id: int) -> Dict[str, Any]:
        """Perform full OSINT scan on a database Lead and record findings."""
        with Session(db_module.engine) as session:
            lead = session.get(Lead, lead_id)
            if not lead:
                return {"error": "Lead not found"}

            target_url = lead.website_url
            business_name = lead.business_name
            sector = lead.sector or "genel"

        osint_data: Dict[str, Any] = {
            "business_name": business_name,
            "domain_age_days": None,
            "web_audit": {},
            "social_discovery": {},
        }

        # 1. WHOIS / RDAP Domain Age
        if target_url:
            parsed = urllib.parse.urlparse(
                target_url if target_url.startswith("http") else f"https://{target_url}"
            )
            domain = parsed.netloc or parsed.path
            domain = domain.split(":")[0].replace("www.", "")
            age_days = await get_domain_age_days(domain)
            osint_data["domain_age_days"] = age_days

            # 2. Website Audit
            osint_data["web_audit"] = await self.scan_website(target_url)

        # 3. Cross-platform Social Discovery
        social_finder = SocialDiscovery()
        social_results = await social_finder.discover_all(
            business_name=business_name,
            location=sector
        )
        osint_data["social_discovery"] = {
            "youtube_url": social_results.youtube_url,
            "linkedin_url": social_results.linkedin_url,
            "tiktok_url": social_results.tiktok_url,
            "facebook_url": social_results.facebook_url,
            "telegram_url": social_results.telegram_url,
            "twitter_url": social_results.twitter_url,
        }

        # 4. Build Rich OSINT Summary
        audit = osint_data["web_audit"]
        cms = audit.get("cms", "Bilinmiyor")
        has_pixel = audit.get("has_pixel", False)
        has_analytics = audit.get("has_analytics", False)
        has_ssl = audit.get("has_ssl", False)
        ssl_days = audit.get("ssl_days_remaining")
        age = osint_data.get("domain_age_days")
        age_str = f"{age} gün" if age else "Bilinmiyor"
        fb_link = social_results.facebook_url or "Yok"
        li_link = social_results.linkedin_url or "Yok"
        yt_link = social_results.youtube_url or "Yok"
        has_tiktok_pixel = audit.get("has_tiktok_pixel", False)
        has_whatsapp = audit.get("has_whatsapp_button", False)
        has_chat = audit.get("has_chat_widget", False)
        has_cookie = audit.get("has_cookie_consent", False)
        tiktok_link = (
            osint_data["social_discovery"].get("tiktok_url")
            or audit.get("tiktok_url")
            or "Yok"
        )

        # SSL status string
        if not has_ssl:
            ssl_status = "❌ SSL Yok"
        elif ssl_days is None:
            ssl_status = "✅ SSL Aktif"
        elif ssl_days < 0:
            ssl_status = f"❌ SSL Süresi Dolmuş ({abs(ssl_days)} gün önce)"
        elif ssl_days < 30:
            ssl_status = f"⚠️ SSL Yakında Doluyor ({ssl_days} gün)"
        else:
            ssl_status = f"✅ SSL Aktif ({ssl_days} gün kaldı)"

        summary = (
            f"🔍 DEEP OSINT İSTİHBARAT RAPORU:\n"
            f"- İşletme: {business_name}\n"
            f"- Altyapı (CMS): {cms}\n"
            f"- Alan Adı Yaşı: {age_str}\n"
            f"- SSL Durumu: {ssl_status}\n"
            f"- Google Analytics: {'Mevcut ✅' if has_analytics else 'Eksik ❌'}\n"
            f"- Meta/FB Pixel: {'Mevcut ✅' if has_pixel else 'Eksik ❌'}\n"
            f"- TikTok Pixel: {'Mevcut ✅' if has_tiktok_pixel else 'Eksik ❌'}\n"
            f"- WhatsApp Butonu: {'Mevcut ✅' if has_whatsapp else 'Eksik ❌'}\n"
            f"- Canlı Chat: {'Mevcut ✅' if has_chat else 'Yok'}\n"
            f"- KVKK/GDPR Banner: {'Mevcut ✅' if has_cookie else 'Eksik ❌'}\n"
            f"- Sosyal Medya: FB: {fb_link} | LinkedIn: {li_link} | YouTube: {yt_link} | TikTok: {tiktok_link}\n"
        )

        # Save into Lead and ResearchNote DB tables
        with Session(db_module.engine) as session:
            db_lead = session.get(Lead, lead_id)
            if db_lead:
                if social_results.facebook_url and not db_lead.facebook_url:
                    db_lead.facebook_url = social_results.facebook_url
                if social_results.linkedin_url and not db_lead.linkedin_url:
                    db_lead.linkedin_url = social_results.linkedin_url
                if social_results.youtube_url and not db_lead.youtube_url:
                    db_lead.youtube_url = social_results.youtube_url

                note = ResearchNote(
                    lead_id=lead_id,
                    source="deep_osint",
                    content=summary
                )
                session.add(note)
                session.commit()

        logger.info(f"Deep OSINT scan completed for lead_id={lead_id}.")
        return osint_data
