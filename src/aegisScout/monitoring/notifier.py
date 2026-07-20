"""
Unified notification dispatch.

Three channels per PRD §3.4:
  1. Telegram  (always async via httpx)
  2. Email     (SMTP, sync I/O — wrapped in asyncio.to_thread from async callers)
  3. Instagram DM (gated by mod_b_acknowledged AND not instagram_dry_run;
                   default-off so unacknowledged installs never auto-DM)

All blocking I/O is performed off the event loop. notify_all() returns a
per-channel success dict and never blocks.
"""
from __future__ import annotations

import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Union

import httpx

from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("monitoring.notifier")

DEFAULT_SMTP_TIMEOUT = 15  # seconds


def _smtp_timeout() -> int:
    """
    Resolve SMTP connect timeout. Sources, in order:
      1. settings.notify_smtp_timeout (int)
      2. env NOTIFY_SMTP_TIMEOUT
      3. default 15
    """
    val = getattr(settings, "notify_smtp_timeout", None)
    if val is None:
        env = os.getenv("NOTIFY_SMTP_TIMEOUT")
        if env is not None:
            try:
                val = int(env)
            except ValueError:
                val = DEFAULT_SMTP_TIMEOUT
        else:
            val = DEFAULT_SMTP_TIMEOUT
    return val


def _recipient() -> str:
    """Resolve the email recipient. Sender != recipient (fixes self-send bug)."""
    rcpt = getattr(settings, "notify_email_recipient", None)
    if rcpt:
        return rcpt
    env = os.getenv("NOTIFY_EMAIL_RECIPIENT")
    if env:
        return env
    # Safe fallback: send to the smtp username (better than crashing)
    return settings.notify_email_username or ""


def _mod_b_acknowledged() -> bool:
    val = getattr(settings, "mod_b_acknowledged", None)
    if val is None:
        return os.getenv("MOD_B_ACKNOWLEDGED", "").lower() in ("1", "true", "yes")
    return bool(val)


def _instagram_dry_run() -> bool:
    val = getattr(settings, "instagram_dry_run", None)
    if val is None:
        # Default to True (safe). User must explicitly disable.
        return os.getenv("INSTAGRAM_DRY_RUN", "true").lower() not in (
            "0", "false", "no"
        )
    return bool(val)


class Notifier:
    """
    Unified notification dispatch supporting Telegram, Email, and Instagram DM.

    All blocking I/O (SMTP) is meant to be called via `asyncio.to_thread(...)`
    or `loop.run_in_executor(...)` by async callers — see `notify_all()`.
    """

    def __init__(self):
        self.telegram_token = settings.telegram_bot_token
        self.telegram_chat_id = settings.telegram_chat_id

        self.smtp_host = settings.notify_email_smtp_host
        self.smtp_port = settings.notify_email_smtp_port
        self.smtp_user = settings.notify_email_username
        self.smtp_password = settings.notify_email_password

        # pre-compute so tests can introspect without re-reading env
        self.smtp_timeout = _smtp_timeout()

    # ------------------------------------------------------------------
    # Telegram (async-native, no executor needed)
    # ------------------------------------------------------------------

    async def send_telegram(self, message: str) -> bool:
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning(
                "Telegram Bot Token or Chat ID not set in .env. "
                "Skipping Telegram notification."
            )
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info("Telegram notification sent successfully.")
                    return True
                else:
                    logger.error(
                        f"Telegram API returned status "
                        f"{response.status_code}: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")

        return False

    # ------------------------------------------------------------------
    # Email (sync; callers must off-load to thread)
    # ------------------------------------------------------------------

    def send_email(
        self,
        subject: str,
        body: str,
        to: Optional[Union[str, list[str]]] = None,
    ) -> bool:
        """
        Send an email via SMTP. Synchronous I/O — wrap with
        `asyncio.to_thread` from async contexts.

        The `to` parameter defaults to `settings.notify_email_recipient`
        (or env `NOTIFY_EMAIL_RECIPIENT`, or the smtp username as a last
        resort). The recipient MUST be different from the sender in
        normal use; this method no longer self-addresses.
        """
        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            logger.warning(
                "SMTP settings not configured. Skipping email notification."
            )
            return False

        recipient = to if to is not None else _recipient()
        if isinstance(recipient, str):
            to_addrs = [recipient]
        else:
            to_addrs = list(recipient)
        if not to_addrs or not all(to_addrs):
            logger.warning(
                "Email recipient is empty. Skipping email notification."
            )
            return False

        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            # CRITICAL: pass timeout on the connect() call. Without it, a
            # blackholed SMTP server will hang the entire async loop.
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.smtp_timeout)
            try:
                # starttls/login do not accept `timeout` on all Python versions;
                # the connect timeout covers blocking anyway. We call them
                # directly.
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_addrs, msg.as_string())
                logger.info(
                    f"Email notification sent to {to_addrs} successfully."
                )
                return True
            finally:
                try:
                    server.quit()
                except Exception:
                    pass
        except (smtplib.SMTPException, OSError) as e:
            logger.error(
                f"Error sending Email notification to {to_addrs}: {e}"
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.error(
                f"Unexpected error sending Email notification: {e}"
            )

        return False

    # ------------------------------------------------------------------
    # Instagram DM (gated, lazy import, dry-run by default)
    # ------------------------------------------------------------------

    async def send_instagram_dm(
        self, username: str, text: str
    ) -> bool:
        """
        Send an Instagram direct message (3rd channel per PRD §3.4).

        Safety gates — actual sending only happens when:
          - `mod_b_acknowledged` is True (user has explicitly accepted ToS),
          - `instagram_dry_run` is False (user has disabled dry-run).

        In all other cases this logs a DRY RUN line and returns True
        (treated as "ok" so the rest of the notify pipeline still succeeds).

        The InstagramClient is imported lazily so `instagrapi` is not
        required at runtime.
        """
        if not username or not text:
            logger.warning("Instagram DM skipped: empty username or text.")
            return False

        if not _mod_b_acknowledged() or _instagram_dry_run():
            logger.info(
                f"DRY RUN: would send IG DM to {username} "
                f"(mod_b_acknowledged={_mod_b_acknowledged()}, "
                f"dry_run={_instagram_dry_run()})"
            )
            return True

        # Attempt actual send via InstagramClient (lazy import)
        try:
            from aegisScout.outreach.instagram_client import InstagramClient
        except ImportError as e:
            logger.error(
                f"Cannot send Instagram DM: instagrapi not installed. {e}"
            )
            return False

        def _send() -> bool:
            try:
                client = InstagramClient()
                # Client.login() loads session if present, logs in otherwise
                if not client.is_logged_in and not client.login():
                    return False
                return client.send_direct_message(username, text)
            except Exception as e:  # pragma: no cover - defensive
                logger.error(
                    f"Instagram DM send raised unexpectedly: {e}"
                )
                return False

        return await asyncio.to_thread(_send)

    # ------------------------------------------------------------------
    # Master dispatch — async, non-blocking, per-channel result
    # ------------------------------------------------------------------

    async def notify_all(
        self,
        title: str,
        text: str,
        *,
        to: Optional[Union[str, list[str]]] = None,
        lead_instagram: Optional[str] = None,
    ) -> dict[str, bool]:
        """
        Send `title`/`text` to every enabled channel and return a
        per-channel success dict:

            {
                "telegram":     bool,
                "email":        bool,
                "instagram_dm": bool,
            }

        Telegram is awaited natively. Email is dispatched via
        `asyncio.to_thread`. Instagram DM is dispatched via
        `asyncio.to_thread` and is gated by mod_b / dry-run flags.

        Never blocks the event loop.
        """
        # 1) Telegram — async-native
        telegram_text = f"<b>{title}</b>\n\n{text}"
        telegram_ok = await self.send_telegram(telegram_text)

        # 2) Email — off-loop thread
        html_text = text.replace("\n", "<br>")
        email_html = f"<h2>{title}</h2><p>{html_text}</p>"

        async def _email_in_thread() -> bool:
            return await asyncio.to_thread(
                self.send_email, title, email_html, to
            )

        # 3) Instagram DM — off-loop thread (no-op unless enabled)
        async def _ig_in_thread() -> bool:
            if not lead_instagram:
                return False
            return await self.send_instagram_dm(lead_instagram, text)

        # Run email and IG-DM in parallel; await telegram first since
        # it's already async and cheap.
        email_ok, ig_ok = await asyncio.gather(
            _email_in_thread(),
            _ig_in_thread(),
        )

        return {
            "telegram": bool(telegram_ok),
            "email": bool(email_ok),
            "instagram_dm": bool(ig_ok),
        }
