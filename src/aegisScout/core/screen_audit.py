"""
Multimodal Website Screen-Audit Module.
Uses Playwright to capture target website screenshots and Gemini Vision API to detect design flaws.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any
from sqlmodel import Session

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None  # type: ignore[assignment]
from aegisScout.core.database import engine
from aegisScout.core.models import Lead
from aegisScout.ai.providers.gemini_provider import GeminiProvider
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger
from aegisScout.utils.paths import get_data_dir

logger = get_logger("core.screen_audit")

# Ensure screenshot directory exists
SCREENSHOTS_DIR = get_data_dir() / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def capture_screenshot(url: str, output_path: Path) -> bool:
    """Capture a screenshot of the given URL and save it to output_path using Playwright with cross-platform flags."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright is not installed. Run: pip install playwright && playwright install chromium")
        return False
    logger.info(f"Capturing screenshot of {url} to {output_path}...")
    try:
        with sync_playwright() as p:
            # Cross-platform chromium launch flags
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Go to URL with robust domcontentloaded condition & timeout
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1000)
            
            # Capture viewport screenshot
            page.screenshot(path=str(output_path), full_page=False)
            browser.close()
            logger.info("Screenshot captured successfully.")
            return True
    except Exception as e:
        logger.error(f"Failed to capture screenshot for {url} via Playwright: {e}")
        return False


def get_base64_image(image_path: Path) -> str:
    """Read image file and return its base64 string representation."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_local_heuristic_audit(lead: Lead) -> Dict[str, Any]:
    """
    Fallback visual audit generator when Gemini API is not available.
    Uses basic attributes to simulate a realistic design analysis.
    """
    logger.info("Gemini API key missing. Generating local heuristic screen-audit fallback...")
    
    # Analyze domain features and rating if available
    quality_score = 75
    errors = []
    
    if lead.page_speed_mobile and lead.page_speed_mobile < 50:
        errors.append("Mobil yüklenme hızı oldukça düşük (Dönüşüm oranlarını olumsuz etkiler).")
        quality_score -= 15
    else:
        errors.append("Mobil yüklenme hızı ve resim optimizasyonları iyileştirilebilir.")
        quality_score -= 5

    if lead.has_broken_links:
        errors.append("Web sitesinde kırık linkler tespit edildi (Güven zedeleyici bir unsur).")
        quality_score -= 10

    if not lead.phone:
        errors.append("Ana sayfada doğrudan tıklanabilir bir Harekete Geçirici Mesaj (CTA) veya telefon butonu eksik.")
        quality_score -= 10
        
    if len(errors) == 0:
        errors.append("Menü kontrast oranı ve okunabilirlik mobil cihazlarda optimize edilmeli.")
        quality_score = 85

    notes = f"Yerel analiz sonucu: Sitenin mobil uyumluluk ve performans skorları incelendi. Bulunan hatalar: {', '.join(errors)}"
    
    # Create the outreach hook in Turkish
    hook = (
        f"Sitenizi mobil cihazlarda incelediğimizde, "
        f"{errors[0].replace('oldukça düşük (Dönüşüm oranlarını olumsuz etkiler).', 'optimize edilmesi gerektiğini').lower()} "
        f"fark ettik. Bu durum dönüşüm oranlarınızı ve müşteri kazanımınızı düşürüyor olabilir. "
        f"Sizin için bu konuda hızlı bir çalışma hazırlayabiliriz. Düzeltmemizi ister misiniz?"
    )

    return {
        "quality_score": max(20, quality_score),
        "errors": errors,
        "notes": notes,
        "hook": hook
    }


async def run_website_screen_audit(lead_id: int) -> dict:
    """
    Perform a complete screen audit for the lead:
      1. Capture screenshot of lead's website
      2. Call Gemini Vision API to analyze design flaws (or fallback to local heuristics)
      3. Save the screenshot path, analysis notes, and personalized hook to database.
    """
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            return {"error": "Aday bulunamadı."}
        if not lead.website_url:
            return {"error": "Adayın web sitesi adresi bulunamadı."}

        screenshot_filename = f"lead_{lead.id}.png"
        screenshot_path = SCREENSHOTS_DIR / screenshot_filename

        # 1. Capture screenshot (with graceful fallback if Playwright is missing or fails)
        success = capture_screenshot(lead.website_url, screenshot_path)
        if success:
            lead.screenshot_path = f"data/screenshots/{screenshot_filename}"
            session.add(lead)
            session.commit()
            session.refresh(lead)
        else:
            logger.warning("Screenshot capture unavailable or failed. Using heuristic screen audit fallback.")

        # 2. Analyze design using Gemini Vision or local fallback
        if success and settings.gemini_api_key:
            try:
                img_b64 = get_base64_image(screenshot_path)
                provider = GeminiProvider()
                
                system_prompt = (
                    "You are a professional UX/UI auditor and growth marketing expert. "
                    "Analyze website screenshots to find design flaws and generate highly converting outreach hooks."
                )
                
                prompt = (
                    "Analyze the attached website screenshot for visual design, mobile responsiveness, layout errors, and usability issues. "
                    "You must output a JSON object with the following fields: "
                    "{\n"
                    '  "quality_score": <int between 0 and 100>,\n'
                    '  "errors": [\n'
                    '     "Mistake 1 (e.g. Mobile menu overlaps with logo)",\n'
                    '     "Mistake 2 (e.g. Contrast makes it hard to read the text)"\n'
                    "  ],\n"
                    '  "notes": "A brief overall design summary including specific visual flaws.",\n'
                    '  "hook": "A highly personalized email outreach hook starting by mentioning the visual flaws observed in the screenshot (e.g., \'Sitenizi mobil cihazlarda analiz ettiğimizde, mobil menünün logonuzun üzerine bindiğini fark ettik...\') in Turkish."\n'
                    "}"
                )

                logger.info("Calling Gemini Vision API...")
                raw_response = await provider.generate_vision(
                    prompt=prompt,
                    image_bytes_base64=img_b64,
                    mime_type="image/png",
                    system_prompt=system_prompt,
                    validate_json=True
                )
                
                analysis = json.loads(raw_response)
                quality_score = int(analysis.get("quality_score", 70))
                errors = analysis.get("errors", [])
                notes = analysis.get("notes", "")
                hook = analysis.get("hook", "")
                
            except Exception as e:
                logger.error(f"Gemini Vision API call failed: {e}. Falling back to heuristics.")
                fallback = generate_local_heuristic_audit(lead)
                quality_score = fallback["quality_score"]
                notes = f"Vision Hatası Fallback: {fallback['notes']}"
                hook = fallback["hook"]
        else:
            fallback = generate_local_heuristic_audit(lead)
            quality_score = fallback["quality_score"]
            notes = fallback["notes"]
            hook = fallback["hook"]

        # 3. Update DB
        lead.website_quality_score = quality_score
        lead.visual_audit_notes = notes
        lead.outreach_hook = hook
        lead.status = "researched"  # Mark as researched
        
        session.add(lead)
        session.commit()
        session.refresh(lead)

        return {
            "success": True,
            "quality_score": quality_score,
            "notes": notes,
            "hook": hook,
            "screenshot_path": lead.screenshot_path
        }
