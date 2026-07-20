"""
Website Screenshot Gallery & Comparison Engine for aegisScout (N9).
Manages screenshots and side-by-side design comparisons for leads.
"""
from pathlib import Path
from typing import Dict, Any, List
from aegisScout.core.screen_audit import SCREENSHOTS_DIR, capture_screenshot
from aegisScout.utils.logger import get_logger

logger = get_logger("core.screen_gallery")

def get_lead_screenshot(lead_id: int, website_url: str) -> Dict[str, Any]:
    """Ensure screenshot exists for lead and return path."""
    file_name = f"lead_{lead_id}.png"
    out_path = SCREENSHOTS_DIR / file_name

    if not out_path.exists() and website_url:
        logger.info(f"Generating screenshot for lead {lead_id} at {website_url}...")
        try:
            capture_screenshot(website_url, out_path)
        except Exception as e:
            logger.error(f"Screenshot capture failed for lead {lead_id}: {e}")

    return {
        "lead_id": lead_id,
        "exists": out_path.exists(),
        "path": str(out_path) if out_path.exists() else None,
        "url": website_url
    }

def get_gallery_comparison(lead_id: int, website_url: str) -> Dict[str, Any]:
    """Get side-by-side comparison data between current lead and reference modern design."""
    current = get_lead_screenshot(lead_id, website_url)
    reference_samples = [
        {"name": "Modern Minimalist Agency", "path": str(SCREENSHOTS_DIR / "ref_modern.png")},
        {"name": "High-Converting E-Commerce", "path": str(SCREENSHOTS_DIR / "ref_ecom.png")}
    ]

    return {
        "current_lead": current,
        "reference_designs": reference_samples,
        "comparison_highlights": [
            "Mobil uyumluluk optimizasyonu gerekli",
            "CTA (Call to Action) butonları belirgin değil",
            "Sayfa yüklenme süresi optimize edilebilir"
        ]
    }
