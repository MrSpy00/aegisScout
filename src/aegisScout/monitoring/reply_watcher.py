import asyncio
from datetime import datetime, timezone
from sqlmodel import Session, select, func

from aegisScout.core.database import engine
from aegisScout.core.models import Lead, Message, ActivityLog
from aegisScout.monitoring.notifier import Notifier
from aegisScout.outreach.email_client import check_imap_replies
from aegisScout.outreach.followup_manager import check_and_send_followups
from aegisScout.utils.logger import get_logger

logger = get_logger("monitoring.reply_watcher")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ReplyWatcher:
    """
    Background daemon/process to poll Instagram and IMAP for new replies,
    match them with existing outreach leads, auto-pause follow-ups, and trigger
    scheduled campaign follow-up emails.
    """
    def __init__(self):
        self.notifier = Notifier()
        self.ig_client = None

    def _get_ig_client(self):
        if self.ig_client is None:
            try:
                from aegisScout.outreach.instagram_client import InstagramClient
                self.ig_client = InstagramClient()
            except ImportError:
                raise RuntimeError(
                    "Mod B (Instagram otomasyonu) için 'instagrapi' kurulu olmalı.\n"
                    "Kurmak için: pip install 'aegisScout[mod-b]' veya pip install instagrapi"
                )
        return self.ig_client

    async def watch_loop(self, poll_interval_seconds: int = 300):
        """
        Periodically polls Instagram and IMAP inbox, updates lead status,
        and triggers follow-up email sequences.
        """
        logger.info("Starting aegisScout Unified Watcher Daemon...")
        
        try:
            while True:
                # 1. Instagram polling (best-effort, Mod B)
                try:
                    ig = self._get_ig_client()
                    logger.info("Polling Instagram direct messages for replies...")
                    new_messages = await asyncio.to_thread(ig.check_new_messages)
                    
                    if new_messages:
                        logger.info(f"Retrieved {len(new_messages)} potential Instagram replies.")
                        with Session(engine) as session:
                            for msg in new_messages:
                                username = msg["username"]
                                content = msg["content"]
                                
                                statement = select(Lead).where(
                                    (Lead.instagram_handle == username) & 
                                    (Lead.status == "contacted")
                                )
                                lead = session.exec(statement).first()
                                
                                if lead:
                                    logger.info(f"Match found! Lead '{lead.business_name}' replied via Instagram.")
                                    lead.status = "replied"
                                    session.add(lead)
                                    
                                    inbound_msg = Message(
                                        lead_id=lead.id,
                                        direction="inbound",
                                        channel="instagram_auto",
                                        content=content,
                                        status="sent",
                                        sent_at=_utcnow()
                                    )
                                    session.add(inbound_msg)
                                    
                                    log_entry = ActivityLog(
                                        action="reply_received",
                                        details=f"Lead {lead.business_name} (@{username}) replied: '{content[:50]}...'"
                                    )
                                    session.add(log_entry)
                                    session.commit()
                                    
                                    title = f"Yeni Yanıt (Instagram): {lead.business_name}"
                                    body = f"İşletme: {lead.business_name}\nInstagram: @{username}\n\nYanıt:\n{content}"
                                    await self.notifier.notify_all(title, body)
                except RuntimeError as re:
                    # Mod B is not installed or configured, skip Instagram polling
                    logger.debug(f"Instagram polling skipped: {re}")
                except Exception as e:
                    err_cls = e.__class__.__name__
                    if err_cls == "PrivateError":
                        logger.warning(f"Instagram DM thread is not inspectable (PrivateError): {e}")
                    elif err_cls == "LoginRequired":
                        logger.critical(f"Instagram session expired (LoginRequired). Stopping Instagram watcher checks.")
                        break
                    else:
                        logger.error(f"Error in Instagram Watcher poll cycle: {e}")

                # 2. E-mail IMAP Polling
                try:
                    logger.info("Polling IMAP mailboxes for email replies...")
                    replied_emails = await asyncio.to_thread(check_imap_replies)
                    if replied_emails:
                        logger.info(f"Retrieved {len(replied_emails)} email replies.")
                        with Session(engine) as session:
                            for reply_info in replied_emails:
                                email_addr = reply_info["email"]
                                subject = reply_info["subject"]
                                body_content = reply_info["body"]
                                
                                statement = select(Lead).where(
                                    (func.lower(Lead.email) == email_addr.lower()) &
                                    (Lead.status == "contacted")
                                )
                                leads = session.exec(statement).all()
                                for lead in leads:
                                    logger.info(f"Match found! Lead '{lead.business_name}' replied via Email.")
                                    lead.status = "replied"
                                    session.add(lead)
                                    
                                    inbound_msg = Message(
                                        lead_id=lead.id,
                                        direction="inbound",
                                        channel="email",
                                        content=body_content,
                                        status="sent",
                                        sent_at=_utcnow()
                                    )
                                    session.add(inbound_msg)
                                    
                                    log_entry = ActivityLog(
                                        action="reply_received",
                                        details=f"Lead {lead.business_name} ({email_addr}) replied via email: '{body_content[:50]}...'"
                                    )
                                    session.add(log_entry)
                                    session.commit()
                                    
                                    title = f"Yeni Yanıt (E-posta): {lead.business_name}"
                                    body_alert = f"İşletme: {lead.business_name}\nE-posta: {email_addr}\n\nKonu: {subject}\nYanıt:\n{body_content}"
                                    await self.notifier.notify_all(title, body_alert)
                except Exception as e:
                    logger.error(f"Error in IMAP Watcher poll cycle: {e}")

                # 3. Campaign follow-ups check
                try:
                    logger.info("Checking and triggering scheduled follow-up emails...")
                    followup_stats = await check_and_send_followups()
                    if followup_stats["emails_sent"] > 0:
                        logger.info(f"Triggered {followup_stats['emails_sent']} follow-up emails.")
                    if followup_stats["errors"]:
                        logger.warning(f"Errors during follow-up sequence: {followup_stats['errors']}")
                except Exception as e:
                    logger.error(f"Error in Follow-up Manager cycle: {e}")

                # 4. P2P Email Warmup Check
                try:
                    from aegisScout.core.config import settings
                    if getattr(settings, "email_warmup_active", False):
                        logger.info("Email warmup is active. Running P2P warmup cycle...")
                        from aegisScout.outreach.warmup import run_p2p_warmup_cycle
                        warmup_res = await run_p2p_warmup_cycle()
                        logger.info(f"P2P Warmup cycle result: {warmup_res}")
                except Exception as e:
                    logger.error(f"Error in P2P Warmup cycle: {e}")

                logger.info(f"Pacing: sleeping for {poll_interval_seconds} seconds before next poll...")
                await asyncio.sleep(poll_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Reply Watcher stopped by user (KeyboardInterrupt).")
        except asyncio.CancelledError:
            logger.info("Reply Watcher task cancelled.")
            raise
        finally:
            logger.info("Cleaning up Reply Watcher resources...")
            if self.ig_client:
                for method_name in ("save_session", "shutdown", "release", "close"):
                    if hasattr(self.ig_client, method_name):
                        try:
                            method = getattr(self.ig_client, method_name)
                            if callable(method):
                                method()
                        except Exception as cleanup_err:
                            logger.warning(f"Error calling {method_name} during cleanup: {cleanup_err}")

