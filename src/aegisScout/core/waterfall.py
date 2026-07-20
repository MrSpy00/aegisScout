"""
Waterfall Enrichment Cascade Module.
Orchestrates sequential steps (website scraping, search queries, Instagram bio scraping)
to find and verify lead email addresses.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session
from datetime import datetime

from aegisScout.core.database import engine
from aegisScout.core.models import Lead, ResearchNote, ActivityLog
from aegisScout.utils.email_verifier import verify_email
from aegisScout.utils.logger import get_logger
from aegisScout.core.config import settings

logger = get_logger("core.waterfall")

CONFIG_FILE = Path("data/waterfall_config.json")

DEFAULT_CONFIG = [
    {
        "step_id": "website_scrape",
        "enabled": True,
        "name": "Web Sitesi İçerik Taraması",
        "description": "Adayın web sitesini tarayarak doğrudan e-posta ve sosyal medya adreslerini bulur."
    },
    {
        "step_id": "search_query",
        "enabled": True,
        "name": "Google / DuckDuckGo Arama Sorgusu",
        "description": "E-posta bulunamazsa web üzerinde arama yaparak iletişim e-postalarını sorgular.",
        "query_template": '"{business_name}" iletişim e-posta'
    },
    {
        "step_id": "instagram_bio",
        "enabled": True,
        "name": "Instagram Biyografi Kazıma",
        "description": "Instagram adresi varsa profil biyografisini kazıyarak e-posta arar."
    },
    {
        "step_id": "email_verify",
        "enabled": True,
        "name": "Yerel E-posta Doğrulama (Local Email Verifier)",
        "description": "Bulunan e-postayı format, disposable domain, DNS MX ve SMTP handshake ile doğrular."
    }
]


def load_waterfall_config() -> List[Dict[str, Any]]:
    """Load waterfall configuration from data folder or return default config."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Waterfall configuration could not be read: {e}")
    return DEFAULT_CONFIG


def save_waterfall_config(config: List[Dict[str, Any]]) -> None:
    """Save waterfall configuration to data folder."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save waterfall config: {e}")


async def free_duckduckgo_search_emails(query: str) -> List[str]:
    """
    Perform a free API-key-less DuckDuckGo search to extract emails from search result snippets.
    Provides a robust backup if Google Custom Search keys are not configured.
    """
    logger.info(f"Performing free DuckDuckGo search for: {query}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    emails = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        async with httpx.AsyncClient(headers=headers, timeout=12.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # DuckDuckGo HTML results snippets are in result__snippet class
                snippets = soup.find_all("a", class_="result__snippet")
                for snip in snippets:
                    text = snip.get_text()
                    found = re.findall(r"[\w.-]+@[\w.-]+\.\w+", text)
                    emails.extend(found)
    except Exception as e:
        logger.error(f"Free DuckDuckGo search failed: {e}")
        
    return list(set(emails))


async def google_custom_search_emails(query: str) -> List[str]:
    """Search emails using Google Custom Search API if API key and CX are configured."""
    api_key = settings.google_custom_search_api_key
    cx = settings.google_custom_search_cx
    if not api_key or not cx:
        return []
        
    logger.info(f"Performing Google Custom Search for: {query}")
    emails = []
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                for item in items:
                    snippet = item.get("snippet", "")
                    title = item.get("title", "")
                    found = re.findall(r"[\w.-]+@[\w.-]+\.\w+", snippet + " " + title)
                    emails.extend(found)
    except Exception as e:
        logger.error(f"Google Custom Search failed: {e}")
        
    return list(set(emails))


async def run_waterfall_enrichment(lead_id: int) -> Dict[str, Any]:
    """
    Run the dynamic waterfall enrichment cascade for a specific lead.
    Executes steps sequentially based on data/waterfall_config.json.
    """
    config = load_waterfall_config()
    steps_map = {step["step_id"]: step for step in config}

    logger.info(f"Starting Waterfall Cascade for Lead ID {lead_id}...")

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            return {"error": "Aday bulunamadı."}

        steps_executed = []
        email_found = lead.email
        
        # Helper log
        def log_activity(action: str, details: str):
            act = ActivityLog(
                action=action,
                details=details,
                session_id=lead.session_id
            )
            session.add(act)

        # -------------------------------------------------------------------
        # Step 1: Website Scrape
        # -------------------------------------------------------------------
        step_web = steps_map.get("website_scrape")
        if step_web and step_web.get("enabled") and lead.website_url:
            steps_executed.append("website_scrape")
            logger.info("Waterfall Step: website_scrape...")
            try:
                from aegisScout.discovery.web_scraper import WebScraper
                scraper = WebScraper()
                audit = await scraper.audit_site(lead.website_url)
                
                # Update details if found
                if audit.get("email") and not email_found:
                    email_found = audit["email"]
                    lead.email = email_found
                    log_activity("waterfall_step", f"Web taramasında e-posta bulundu: {email_found}")
                
                if audit.get("instagram_handle") and not lead.instagram_handle:
                    lead.instagram_handle = audit["instagram_handle"]
                    lead.instagram_url = f"https://instagram.com/{lead.instagram_handle}"
                if audit.get("phone") and not lead.phone:
                    lead.phone = audit["phone"]
                if audit.get("quality_score") is not None:
                    lead.website_quality_score = audit["quality_score"]
                
                note = ResearchNote(
                    lead_id=lead.id,
                    source="website",
                    content=f"Waterfall Web Scrape: Quality Score: {audit.get('quality_score')}/100. Email: {audit.get('email')}"
                )
                session.add(note)
            except Exception as e:
                logger.error(f"Waterfall Web Scrape failed: {e}")

        # -------------------------------------------------------------------
        # Step 2: Search Query (Google / DuckDuckGo)
        # -------------------------------------------------------------------
        step_search = steps_map.get("search_query")
        if step_search and step_search.get("enabled") and not email_found:
            steps_executed.append("search_query")
            template = step_search.get("query_template", '"{business_name}" iletişim e-posta')
            query = template.replace("{business_name}", lead.business_name)
            
            logger.info(f"Waterfall Step: search_query -> {query}")
            found_emails = []
            
            # Try Google first if API is configured, otherwise fallback to free DuckDuckGo
            if settings.google_custom_search_api_key and settings.google_custom_search_cx:
                found_emails = await google_custom_search_emails(query)
            
            if not found_emails:
                # Free API-key-less fallback
                found_emails = await free_duckduckgo_search_emails(query)

            if found_emails:
                email_found = found_emails[0]
                lead.email = email_found
                log_activity("waterfall_step", f"Arama sorgusu ile e-posta bulundu: {email_found}")
                
                note = ResearchNote(
                    lead_id=lead.id,
                    source="google_custom_search",
                    content=f"Waterfall Search Found: {', '.join(found_emails)}"
                )
                session.add(note)

        # -------------------------------------------------------------------
        # Step 3: Instagram Bio Scrape
        # -------------------------------------------------------------------
        step_ig = steps_map.get("instagram_bio")
        if step_ig and step_ig.get("enabled") and not email_found and lead.instagram_handle:
            steps_executed.append("instagram_bio")
            logger.info(f"Waterfall Step: instagram_bio for @{lead.instagram_handle}...")
            try:
                from aegisScout.discovery.social_finder import SocialDiscovery
                social = SocialDiscovery()
                bio_info = await social.scrape_instagram_bio(lead.instagram_handle)
                if bio_info and bio_info.get("email"):
                    email_found = bio_info["email"]
                    lead.email = email_found
                    log_activity("waterfall_step", f"Instagram biyografisinde e-posta bulundu: {email_found}")
                    
                    note = ResearchNote(
                        lead_id=lead.id,
                        source="instagram_bio",
                        content=f"Waterfall Instagram Bio Scrape Email: {email_found}. Bio: {bio_info.get('biography')}"
                    )
                    session.add(note)
            except Exception as e:
                logger.warning(f"Waterfall Instagram Bio Scrape failed: {e}")

        # -------------------------------------------------------------------
        # Step 4: Email Verify (Local Verifier)
        # -------------------------------------------------------------------
        step_verify = steps_map.get("email_verify")
        verification_result = None
        if step_verify and step_verify.get("enabled") and email_found:
            steps_executed.append("email_verify")
            logger.info(f"Waterfall Step: email_verify for {email_found}...")
            
            verification_result = verify_email(email_found)
            lead.email_verification_status = verification_result["status"]
            lead.email_verification_details = verification_result["details"]
            
            log_activity("waterfall_step", f"E-posta doğrulama sonucu: {verification_result['status']} ({verification_result['details']})")
            
            # Automatically update Lead status based on verification result
            if verification_result["status"] in ("valid", "mx_only"):
                lead.status = "researched"
            elif verification_result["status"] == "invalid":
                lead.status = "rejected"
            else:
                lead.status = "researched" # fallback to researched if unknown

        lead.updated_at = datetime.now()
        session.add(lead)
        session.commit()
        session.refresh(lead)

        return {
            "success": True,
            "lead_id": lead.id,
            "email": lead.email,
            "verification_status": lead.email_verification_status,
            "verification_details": lead.email_verification_details,
            "steps_executed": steps_executed,
            "status": lead.status
        }
