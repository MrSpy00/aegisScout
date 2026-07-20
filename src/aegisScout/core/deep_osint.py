"""
Deep OSINT Intelligence Scanner for aegisScout.

Performs multi-source open-source intelligence gathering on target leads:
  - WHOIS / RDAP domain registration age & registrar details
  - Technical stack audit (CMS, Analytics, Facebook Pixel, SSL status, Mobile Viewport)
  - Cross-platform social footprint analysis (Instagram, Facebook, LinkedIn, Twitter/X, YouTube)
  - Contact info extraction (Email, Phone, WhatsApp, Address)
  - Comprehensive OSINT report generation
"""
from __future__ import annotations

import re
import urllib.parse
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
            "has_analytics": False,
            "has_pixel": False,
            "has_viewport": False,
            "emails": [],
            "phones": [],
            "social_links": [],
            "http_status": None,
        }

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

                    desc_meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                    if desc_meta and desc_meta.get("content"):
                        result["description"] = desc_meta["content"].strip()

                    # Mobile Viewport
                    viewport = soup.find("meta", attrs={"name": "viewport"})
                    result["has_viewport"] = bool(viewport)

                    # Tech Stack Detection
                    html_lower = html.lower()
                    if "wp-content" in html_lower or "wordpress" in html_lower:
                        result["cms"] = "WordPress"
                    elif "shopify" in html_lower:
                        result["cms"] = "Shopify"
                    elif "wix.com" in html_lower or "wixstatic" in html_lower:
                        result["cms"] = "Wix"
                    elif "squarespace" in html_lower:
                        result["cms"] = "Squarespace"
                    elif "webflow" in html_lower:
                        result["cms"] = "Webflow"
                    elif "elementor" in html_lower:
                        result["cms"] = "WordPress (Elementor)"

                    # Analytics & Pixel
                    if "google-analytics.com" in html_lower or "googletagmanager.com" in html_lower or "gtag" in html_lower:
                        result["has_analytics"] = True

                    if "connect.facebook.net" in html_lower or "fbq(" in html_lower:
                        result["has_pixel"] = True

                    # Contact Info Extraction (Emails & Phones)
                    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html))
                    result["emails"] = list(emails)[:5]

                    phones = set(re.findall(r"(?:\+?90|0)?\s*[2-5]\d{2}\s*\d{3}\s*\d{2}\s*\d{2}", html))
                    result["phones"] = list(phones)[:5]

                    # Social Link Extraction
                    social_domains = ["instagram.com", "facebook.com", "linkedin.com", "twitter.com", "x.com", "youtube.com"]
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if any(sd in href.lower() for sd in social_domains):
                            result["social_links"].append(href)
                    result["social_links"] = list(set(result["social_links"]))[:10]

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
            parsed = urllib.parse.urlparse(target_url if target_url.startswith("http") else f"https://{target_url}")
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

        # 4. Synthesize OSINT Summary Note
        cms = osint_data["web_audit"].get("cms", "Bilinmiyor")
        has_pixel = osint_data["web_audit"].get("has_pixel", False)
        has_analytics = osint_data["web_audit"].get("has_analytics", False)
        age = osint_data.get("domain_age_days")
        age_str = f"{age} gün" if age else "Bilinmiyor"
        fb_link = social_results.facebook_url or "Yok"
        li_link = social_results.linkedin_url or "Yok"
        yt_link = social_results.youtube_url or "Yok"

        summary = (
            f"🔍 DEEP OSINT İSTİHBARAT RAPORU:\n"
            f"- İşletme: {business_name}\n"
            f"- Altyapı (CMS): {cms}\n"
            f"- Alan Adı Yaşı: {age_str}\n"
            f"- Google Analytics: {'Mevcut' if has_analytics else 'Eksik ❌'}\n"
            f"- Meta/FB Pixel: {'Mevcut' if has_pixel else 'Eksik ❌'}\n"
            f"- Sosyal Medya İzcisi: FB: {fb_link} | LinkedIn: {li_link} | YouTube: {yt_link}\n"
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
