"""
Omnichannel Browser Automation Module.
Uses Playwright to automate WhatsApp Web and LinkedIn actions using persistent browser profiles.
"""

from __future__ import annotations

import os
import urllib.parse
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from sqlmodel import Session

from playwright.sync_api import sync_playwright
from aegisScout.core.database import engine
from aegisScout.core.models import Lead, Message
from aegisScout.utils.paths import get_data_dir
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.browser_automation")

# Profile paths
WHATSAPP_PROFILE_DIR = get_data_dir() / "browser_profiles/whatsapp"
LINKEDIN_PROFILE_DIR = get_data_dir() / "browser_profiles/linkedin"

WHATSAPP_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
LINKEDIN_PROFILE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# WhatsApp Web Session & Automation
# ---------------------------------------------------------------------------

def launch_whatsapp_session() -> None:
    """Launch a headful Chromium window to web.whatsapp.com so the user can scan QR code and log in."""
    logger.info("Launching headful WhatsApp Web login session...")
    def run():
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(WHATSAPP_PROFILE_DIR),
                    headless=False,
                    viewport={"width": 1024, "height": 768}
                )
                page = context.new_page()
                page.goto("https://web.whatsapp.com")
                logger.info("WhatsApp Web window opened. Waiting for user interaction/close...")
                
                # Keep open until page is closed by user
                while True:
                    try:
                        page.wait_for_timeout(1000)
                        if page.is_closed():
                            break
                    except Exception:
                        break
                context.close()
                logger.info("WhatsApp Web session closed.")
        except Exception as e:
            logger.error(f"Error in WhatsApp login session: {e}")

    threading.Thread(target=run, daemon=True).start()


def send_whatsapp_message_auto(phone: str, message: str) -> Dict[str, Any]:
    """
    Open Playwright persistent Chromium, navigate to WhatsApp Web send link,
    and automatically send the message.
    """
    clean_phone = "".join(filter(str.isdigit, phone))
    if len(clean_phone) == 10 and clean_phone.startswith("5"):
        clean_phone = "90" + clean_phone  # Default to Turkey country code if local

    logger.info(f"Automatically sending WhatsApp message to {clean_phone}...")
    try:
        with sync_playwright() as p:
            # We launch headful here because WhatsApp Web frequently blocks headless browsers
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(WHATSAPP_PROFILE_DIR),
                headless=False,
                viewport={"width": 1024, "height": 768}
            )
            page = context.new_page()
            
            # Go directly to WhatsApp send API url with text pre-populated
            encoded_text = urllib.parse.quote(message)
            wa_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"
            page.goto(wa_url)
            
            logger.info("Waiting for WhatsApp Web to load the conversation...")
            
            # We wait for the textbox to appear
            # Common selectors for the WhatsApp Web textbox:
            # - div[contenteditable="true"]
            # - div[role="textbox"]
            textbox_selector = 'div[contenteditable="true"]'
            page.wait_for_selector(textbox_selector, timeout=40000)
            
            # Let it settle for a couple of seconds so text is loaded
            page.wait_for_timeout(4000)
            
            # Focus textbox and simulate pressing Enter to send
            page.focus(textbox_selector)
            page.keyboard.press("Enter")
            
            # Wait a few seconds to ensure the socket actually sends it
            page.wait_for_timeout(4000)
            
            context.close()
            logger.info("WhatsApp message sent successfully via Playwright.")
            return {"success": True, "details": "WhatsApp mesajı başarıyla gönderildi."}
            
    except Exception as e:
        logger.error(f"WhatsApp auto-send failed: {e}")
        return {"success": False, "error": f"WhatsApp otomatik gönderim hatası: {str(e)}"}


# ---------------------------------------------------------------------------
# LinkedIn Web Session & Automation
# ---------------------------------------------------------------------------

def launch_linkedin_session() -> None:
    """Launch a headful Chromium window to LinkedIn login so the user can authenticate."""
    logger.info("Launching headful LinkedIn login session...")
    def run():
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(LINKEDIN_PROFILE_DIR),
                    headless=False,
                    viewport={"width": 1024, "height": 768}
                )
                page = context.new_page()
                page.goto("https://www.linkedin.com/login")
                logger.info("LinkedIn window opened. Waiting for user interaction/close...")
                
                # Keep open until page is closed by user
                while True:
                    try:
                        page.wait_for_timeout(1000)
                        if page.is_closed():
                            break
                    except Exception:
                        break
                context.close()
                logger.info("LinkedIn session closed.")
        except Exception as e:
            logger.error(f"Error in LinkedIn login session: {e}")

    threading.Thread(target=run, daemon=True).start()


def send_linkedin_connection_auto(profile_url: str, message: str) -> Dict[str, Any]:
    """
    Open Playwright persistent Chromium, go to target profile page,
    and send a connection request with a personalized note, or send a direct message if already connected.
    """
    logger.info(f"Automating LinkedIn action on profile: {profile_url}...")
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(LINKEDIN_PROFILE_DIR),
                headless=False,  # Headful is much safer for LinkedIn anti-bot detection
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            page.goto(profile_url, timeout=30000)
            page.wait_for_timeout(4000)  # Wait for page elements to load
            
            # Check if we can find a "Connect" button
            # We look for buttons containing "Connect" or "Bağlantı kur" or "Bağlantı Kur"
            # LinkedIn DOM has buttons in the main profile card
            buttons = page.query_selector_all("button")
            connect_btn = None
            message_btn = None
            more_btn = None
            
            for btn in buttons:
                text = (btn.inner_text() or "").strip()
                if "Connect" in text or "Bağlantı kur" in text or "Bağlantı Kur" in text:
                    connect_btn = btn
                elif "Message" in text or "Mesaj gönder" in text or "Mesaj Gönder" in text:
                    message_btn = btn
                elif "More" in text or "Daha fazla" in text:
                    more_btn = btn

            # Case 1: Connect button found directly
            if connect_btn:
                logger.info("Connect button found directly. Clicking...")
                connect_btn.click()
                page.wait_for_timeout(2000)
                
                # Check for "Add a note" modal
                # Look for button with text "Add a note" or "Not ekleyin"
                add_note_btn = None
                modal_buttons = page.query_selector_all("button")
                for btn in modal_buttons:
                    t = (btn.inner_text() or "").strip()
                    if "Add a note" in t or "Not ekle" in t:
                        add_note_btn = btn
                        break
                        
                if add_note_btn:
                    add_note_btn.click()
                    page.wait_for_timeout(1000)
                    
                    # Fill note textbox
                    # The note textbox usually is a textarea with id="custom-message"
                    page.fill("textarea#custom-message", message[:300]) # LinkedIn limit is 300 chars
                    page.wait_for_timeout(1000)
                    
                    # Click send
                    send_btn = None
                    for btn in page.query_selector_all("button"):
                        t = (btn.inner_text() or "").strip()
                        if "Send" in t or "Gönder" in t:
                            send_btn = btn
                            break
                    if send_btn:
                        send_btn.click()
                        page.wait_for_timeout(3000)
                        context.close()
                        return {"success": True, "details": "Bağlantı isteği not ile birlikte gönderildi."}
                else:
                    # Just send connection without note if we couldn't find "Add a note"
                    send_now_btn = None
                    for btn in page.query_selector_all("button"):
                        t = (btn.inner_text() or "").strip()
                        if "Send without a note" in t or "Notsuz gönder" in t or "Gönder" in t:
                            send_now_btn = btn
                            break
                    if send_now_btn:
                        send_now_btn.click()
                        page.wait_for_timeout(3000)
                        context.close()
                        return {"success": True, "details": "Bağlantı isteği notsuz gönderildi."}

            # Case 2: If we are already connected, send a direct message
            elif message_btn:
                logger.info("Already connected. Clicking 'Message' button...")
                message_btn.click()
                page.wait_for_timeout(3000)
                
                # Focus message field in the chat overlay
                # Selector: div[role="textbox"] or div.msg-form__contenteditable
                chat_box_selector = 'div[role="textbox"]'
                page.wait_for_selector(chat_box_selector, timeout=10000)
                page.focus(chat_box_selector)
                page.keyboard.type(message)
                page.wait_for_timeout(1000)
                
                # Click send in chat form
                # Selector for send button: button.msg-form__send-button
                send_chat_btn = page.query_selector("button.msg-form__send-button")
                if send_chat_btn:
                    send_chat_btn.click()
                else:
                    page.keyboard.press("Control+Enter") # Send fallback
                
                page.wait_for_timeout(3000)
                context.close()
                return {"success": True, "details": "LinkedIn mesajı başarıyla gönderildi."}

            # Case 3: Connect is hidden inside the "More" dropdown
            elif more_btn:
                logger.info("Connect button not found on page. Checking 'More' dropdown...")
                more_btn.click()
                page.wait_for_timeout(1500)
                
                # Search inside the dropdown for Connect
                dropdown_connect = None
                dropdown_elements = page.query_selector_all(".artdeco-dropdown__item")
                for el in dropdown_elements:
                    t = (el.inner_text() or "").strip()
                    if "Connect" in t or "Bağlantı kur" in t or "Bağlantı Kur" in t:
                        dropdown_connect = el
                        break
                        
                if dropdown_connect:
                    dropdown_connect.click()
                    page.wait_for_timeout(2000)
                    # Handle the note modal
                    add_note_btn = None
                    for btn in page.query_selector_all("button"):
                        t = (btn.inner_text() or "").strip()
                        if "Add a note" in t or "Not ekle" in t:
                            add_note_btn = btn
                            break
                    if add_note_btn:
                        add_note_btn.click()
                        page.wait_for_timeout(1000)
                        page.fill("textarea#custom-message", message[:300])
                        page.wait_for_timeout(1000)
                        send_btn = None
                        for btn in page.query_selector_all("button"):
                            t = (btn.inner_text() or "").strip()
                            if "Send" in t or "Gönder" in t:
                                send_btn = btn
                                break
                        if send_btn:
                            send_btn.click()
                            page.wait_for_timeout(3000)
                            context.close()
                            return {"success": True, "details": "Bağlantı isteği not ile birlikte gönderildi (Daha fazla menüsü üzerinden)."}
                
            context.close()
            return {"success": False, "error": "Bağlantı Kur veya Mesaj Gönder butonu tespit edilemedi."}
            
    except Exception as e:
        logger.error(f"LinkedIn auto action failed: {e}")
        return {"success": False, "error": f"LinkedIn otomatik işlem hatası: {str(e)}"}
