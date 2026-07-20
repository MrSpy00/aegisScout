import os
import json
from pathlib import Path
from typing import Optional, List
try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        ClientError, LoginRequired, TwoFactorRequired, ChallengeRequired, FeedbackRequired
    )
    HAS_INSTAGRAPI = True
except ImportError:
    HAS_INSTAGRAPI = False
    Client = None
    # Dummy exception classes to avoid NameErrors
    class ClientError(Exception): pass  # type: ignore[no-redef]
    class LoginRequired(Exception): pass  # type: ignore[no-redef]
    class TwoFactorRequired(Exception): pass  # type: ignore[no-redef]
    class ChallengeRequired(Exception): pass  # type: ignore[no-redef]
    class FeedbackRequired(Exception): pass  # type: ignore[no-redef]

from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger
from aegisScout.utils.encryption import encrypt_json_file, decrypt_json_file
from aegisScout.outreach.rate_limiter import RateLimiter

from aegisScout.utils.paths import get_data_dir

logger = get_logger("outreach.instagram_client")

SESSION_DIR = get_data_dir() / "sessions"
SESSION_FILE = SESSION_DIR / "session.json"

class InstagramClient:
    """
    Instagram Private API Client wrapper using instagrapi.
    Uses cryptography encrypted storage for session.json.
    Paces requests strictly via RateLimiter.
    """
    def __init__(self):
        if not HAS_INSTAGRAPI:
            raise ImportError(
                "Mod B (Instagram DM Otomasyonu) için 'instagrapi' paketi kurulu olmalıdır. "
                "Lütfen 'pip install instagrapi' komutuyla yükleyin veya [mod-b] ekstra bağımlılıklarını kurun."
            )
        self.cl = Client()
        self.rate_limiter = RateLimiter()
        self.is_logged_in = False

    def load_session(self) -> bool:
        if not SESSION_FILE.exists():
            return False
        try:
            logger.info("Attempting to load encrypted Instagram session...")
            session_data = decrypt_json_file(SESSION_FILE)
            if session_data:
                self.cl.set_settings(session_data)
                # Test login status with a cheap call or trust session settings
                self.is_logged_in = True
                logger.info("Instagram session loaded successfully.")
                return True
        except Exception as e:
            logger.error(f"Failed to load Instagram session: {e}")
        return False

    def save_session(self):
        try:
            logger.info("Saving encrypted Instagram session...")
            session_data = self.cl.get_settings()
            encrypt_json_file(SESSION_FILE, session_data)
            logger.info("Instagram session saved and encrypted.")
        except Exception as e:
            logger.error(f"Failed to save Instagram session: {e}")

    def login(self) -> bool:
        username = settings.instagram_username
        password = settings.instagram_password

        if not username or not password:
            logger.error("Instagram username or password not set in .env. Cannot login.")
            return False

        # Try to load session first to avoid logging in with credentials every time (reduces flag risk)
        if self.load_session():
            try:
                # Validate session status
                self.cl.get_timeline_feed() # test call
                logger.info("Existing session is valid. Login skipped.")
                return True
            except LoginRequired:
                logger.warning("Session expired. Logging in with credentials...")
            except Exception as e:
                logger.warning(f"Session test call failed: {e}. Re-logging in...")

        # Credentials login
        try:
            logger.info(f"Logging in to Instagram as {username}...")
            self.rate_limiter.sleep_random()
            self.cl.login(username, password)
            self.is_logged_in = True
            logger.info("Instagram login successful.")
            self.save_session()
            return True
        except TwoFactorRequired as e:
            logger.critical("Two-factor authentication is required on this account.")
            print("[CRITICAL] Two-Factor Authentication is enabled on your Instagram account.")
            print("Please temporarily disable 2FA or configure a 2FA flow to proceed.")
            return False
        except ChallengeRequired as e:
            logger.critical(f"Instagram Login Challenge required: {e}")
            print("[CRITICAL] Instagram checkpoint challenge triggered (ChallengeRequired).")
            print("Please log in to this account via a browser or mobile device, solve the challenge, and try again.")
            return False
        except FeedbackRequired as e:
            logger.error(f"Instagram action blocked (FeedbackRequired): {e}")
            print("[ERROR] Instagram action is blocked due to bot/spam detection. Please wait or use a different account.")
            return False
        except Exception as e:
            logger.error(f"Instagram credentials login failed: {e}")
            return False

    def send_direct_message(self, username: str, text: str) -> bool:
        """
        Send direct message to a user.
        Enforces daily and hourly rate limits before sending.
        Records the send event in activity_log on success.
        """
        if not self.is_logged_in:
            if not self.login():
                return False

        # --- Rate limit check (PRD §3.3: günlük ≤15-20 yeni mesaj) ---
        can_send, reason = self.rate_limiter.can_send()
        if not can_send:
            logger.warning(f"Rate limit aşıldı, gönderi iptal edildi: {reason}")
            print(f"[UYARI] {reason}")
            return False

        try:
            self.rate_limiter.sleep_random()
            # Resolve username to user ID
            user_id = self.cl.user_id_from_username(username)
            self.rate_limiter.sleep_random()
            # Send message
            self.cl.direct_send(text, user_ids=[user_id])
            logger.info(f"Successfully sent automated DM to {username}.")
            # Record send for limit enforcement
            self.rate_limiter.record_send(lead_name=username)
            return True
        except Exception as e:
            logger.error(f"Failed to send Instagram DM to {username}: {e}")
            return False

    def check_new_messages(self) -> List[dict]:
        """
        Checks for new unread messages in the inbox.
        """
        if not self.is_logged_in:
            if not self.login():
                return []

        try:
            self.rate_limiter.sleep_random()
            # Get inbox threads
            threads = self.cl.direct_threads()
            unread_messages = []
            
            for thread in threads:
                # Check if there are unread messages or check the latest message
                if thread.read_state == 1: # 1 means unread in some versions, or check manually
                    # Check messages
                    messages = thread.messages
                    if messages:
                        latest_msg = messages[0]
                        # If the message is inbound and we haven't seen it
                        if latest_msg.user_id != self.cl.user_id:
                            unread_messages.append({
                                "username": thread.users[0].username if thread.users else "unknown",
                                "content": latest_msg.text,
                                "timestamp": latest_msg.timestamp
                            })
            return unread_messages
        except Exception as e:
            logger.error(f"Failed to check Instagram inbox: {e}")
            return []
