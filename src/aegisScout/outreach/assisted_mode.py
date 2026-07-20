"""
Multichannel Assisted Outreach Module for aegisScout.

Provides assisted (Mod A) manual-click / clipboard-copy dispatch for:
  - Instagram DM (profile link + clipboard)
  - WhatsApp Web (wa.me direct link + optional Playwright launcher)
  - LinkedIn (Profile / Company search & direct connect helper)
"""

import urllib.parse
import webbrowser
import pyperclip
from typing import Dict, Any, Optional

from aegisScout.core.models import Lead
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.assisted")


def send_assisted_message(lead: Lead, draft_message: str) -> bool:
    """
    Assisted Mode (Mod A) for Instagram DM:
      Copies message to clipboard and opens Instagram profile in browser.
    """
    try:
        pyperclip.copy(draft_message)
        logger.info(f"Draft message copied to clipboard for {lead.business_name}")

        if lead.instagram_handle:
            profile_url = f"https://www.instagram.com/{lead.instagram_handle}/"
            logger.info(f"Opening Instagram profile: {profile_url}")
            try:
                webbrowser.open(profile_url)
            except Exception as w_err:
                logger.warning(f"Browser open warning: {w_err}")
        else:
            google_query = urllib.parse.quote(f"{lead.business_name} Instagram")
            google_url = f"https://www.google.com/search?q={google_query}"
            logger.warning(f"No instagram handle for {lead.business_name}. Opening Google search.")
            try:
                webbrowser.open(google_url)
            except Exception as w_err:
                logger.warning(f"Browser open warning: {w_err}")

        return True
    except Exception as e:
        logger.error(f"Error in assisted Instagram outreach for lead {lead.id}: {e}")
        return False


def send_whatsapp_assisted(phone_number: str, message: str) -> Dict[str, Any]:
    """
    WhatsApp Web Assisted Outreach (Mod A):
      Formats phone number, copies message to clipboard, and opens wa.me URL.
    """
    try:
        if not phone_number:
            return {"success": False, "error": "Telefon numarası bulunamadı."}

        # Clean non-digit characters except leading plus
        clean_phone = "".join(c for c in phone_number if c.isdigit())
        if clean_phone.startswith("0"):
            clean_phone = "90" + clean_phone[1:]
        elif not clean_phone.startswith("90") and len(clean_phone) == 10:
            clean_phone = "90" + clean_phone

        try:
            pyperclip.copy(message)
        except Exception as clip_err:
            logger.warning(f"Clipboard copy warning: {clip_err}")

        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

        logger.info(f"Opening WhatsApp Web URL for {clean_phone}")
        try:
            webbrowser.open(wa_url)
        except Exception as w_err:
            logger.warning(f"Browser open warning: {w_err}")

        return {
            "success": True,
            "phone": clean_phone,
            "wa_url": wa_url,
            "message": "WhatsApp Web açıldı ve mesaj panoya kopyalandı."
        }
    except Exception as e:
        logger.error(f"WhatsApp assisted outreach failed: {e}")
        return {"success": False, "error": str(e)}


def send_linkedin_assisted(business_name: str, message: str, linkedin_url: Optional[str] = None) -> Dict[str, Any]:
    """
    LinkedIn Assisted Outreach (Mod A):
      Copies outreach pitch to clipboard and opens LinkedIn Profile / Search page.
    """
    try:
        try:
            pyperclip.copy(message)
        except Exception as clip_err:
            logger.warning(f"Clipboard copy warning: {clip_err}")

        if linkedin_url and "linkedin.com" in linkedin_url:
            target_url = linkedin_url
        else:
            query = urllib.parse.quote(f"{business_name} LinkedIn")
            target_url = f"https://www.google.com/search?q={query}"

        logger.info(f"Opening LinkedIn target URL for {business_name}")
        try:
            webbrowser.open(target_url)
        except Exception as w_err:
            logger.warning(f"Browser open warning: {w_err}")

        return {
            "success": True,
            "target_url": target_url,
            "message": "LinkedIn hedef sayfası açıldı ve mesaj panoya kopyalandı."
        }
    except Exception as e:
        logger.error(f"LinkedIn assisted outreach failed: {e}")
        return {"success": False, "error": str(e)}
