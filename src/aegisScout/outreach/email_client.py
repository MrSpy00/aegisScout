import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
from sqlmodel import Session, select, func

from aegisScout.core.config import settings
from aegisScout.core.database import engine
from aegisScout.core.models import SmtpAccount, Message
from aegisScout.utils.encryption import decrypt_string
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.email_client")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_available_smtp_account() -> Tuple[Optional[SmtpAccount], Optional[str]]:
    """
    Selects the next active SmtpAccount to use for sending, ensuring:
      1. The account is active.
      2. The account has sent < 5 emails in the last 1 hour.
      3. Accounts are rotated evenly (ordered by last_used_at ascending, nulls first).
    
    Returns (account, None) if found, (None, error_reason) otherwise.
    """
    with Session(engine) as session:
        # Load all active SMTP accounts
        accounts = session.exec(select(SmtpAccount).where(SmtpAccount.is_active == True)).all()
        if not accounts:
            return None, "no_accounts"

        one_hour_ago = _utcnow() - timedelta(hours=1)
        candidates = []

        for acc in accounts:
            # Count emails sent with this account in the last hour
            sent_count = session.exec(
                select(func.count(Message.id)).where(
                    (Message.smtp_account_id == acc.id) &
                    (Message.sent_at >= one_hour_ago)
                )
            ).one()

            if sent_count < 5:
                # Add to candidates: tuple of (last_used_at or epoch, account)
                last_used = acc.last_used_at or datetime.min
                candidates.append((last_used, acc))

        if not candidates:
            return None, "limit_reached"

        # Sort by last_used_at ascending, so the least recently used account is selected
        candidates.sort(key=lambda x: x[0])
        selected_account = candidates[0][1]
        
        # Touch last_used_at
        selected_account.last_used_at = _utcnow()
        session.add(selected_account)
        session.commit()
        session.refresh(selected_account)
        return selected_account, None


def send_cold_email(to_email: str, subject: str, body: str, smtp_account_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
    """
    Sends a cold email.
    If smtp_account_id is provided, uses that specific account.
    If not, rotates through active SMTP accounts subject to rate limits.
    Falls back to global settings if no SmtpAccount is configured in the database.
    
    Returns: (success, message, used_smtp_account_id)
    """
    acc: Optional[SmtpAccount] = None
    
    with Session(engine) as session:
        if smtp_account_id is not None:
            acc = session.get(SmtpAccount, smtp_account_id)
            if not acc or not acc.is_active:
                return False, f"Belirtilen SMTP hesabı (ID: {smtp_account_id}) bulunamadı veya pasif.", None
        else:
            # Look for rotated active account
            acc, err = get_available_smtp_account()
            if err == "limit_reached":
                return False, "Tüm SMTP hesaplarının saatlik gönderim limiti (max 5) doldu.", None
            # If err == "no_accounts", we fall back to global settings below

    if acc is not None:
        # Use database SMTP account
        host = acc.smtp_host
        port = acc.smtp_port or 587
        user = acc.smtp_user
        try:
            password = decrypt_string(acc.smtp_pass)
        except Exception as dec_err:
            return False, f"SMTP şifresi deşifre edilemedi: {dec_err}", acc.id
    else:
        # Fallback to global settings
        host = settings.notify_email_smtp_host
        port = settings.notify_email_smtp_port or 587
        user = settings.notify_email_username or settings.notify_email_smtp_user
        password = settings.notify_email_password or settings.notify_email_smtp_pass

    if not host or not user or not password:
        return False, "SMTP Ayarları eksik. Lütfen ayarlar panelinden e-posta hesabı ekleyin.", None

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email
        
        # Connect and send
        server = smtplib.SMTP(host, port, timeout=10.0)
        server.ehlo()
        if port in (587, 25, 465):
            server.starttls()
            server.ehlo()
        server.login(user, password)
        server.sendmail(user, [to_email], msg.as_string())
        server.quit()
        
        logger.info(f"Email successfully sent to {to_email} using {user}")
        return True, "Başarıyla gönderildi.", (acc.id if acc else None)
    except Exception as e:
        msg = f"SMTP Mail gönderim hatası ({user}): {str(e)}"
        logger.error(msg)
        return False, msg, (acc.id if acc else None)


def _extract_email_body(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="ignore")
                        break
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="ignore")
        except Exception:
            pass
    return body.strip()


def check_imap_replies() -> List[dict[str, str]]:
    """
    Checks all configured IMAP servers (including global fallback) for replies.
    Returns a list of dicts with keys: 'email', 'subject', 'body'.
    """
    replied_emails = []
    
    # 1. Gather all IMAP accounts to watch
    accounts_to_check = []
    
    with Session(engine) as session:
        db_accounts = session.exec(select(SmtpAccount).where(SmtpAccount.is_active == True)).all()
        for acc in db_accounts:
            imap_host = acc.imap_host or acc.smtp_host.replace("smtp", "imap")
            imap_port = acc.imap_port or 993
            imap_user = acc.imap_user or acc.smtp_user
            imap_pass = acc.imap_pass or acc.smtp_pass
            
            try:
                decrypted_pass = decrypt_string(imap_pass)
                accounts_to_check.append((imap_host, imap_port, imap_user, decrypted_pass))
            except Exception as e:
                logger.error(f"Failed to decrypt IMAP password for {acc.name}: {e}")

    # Add global fallback if configured
    g_host = settings.notify_email_imap_host
    g_port = settings.notify_email_imap_port or 993
    g_user = settings.notify_email_imap_username or settings.notify_email_username
    g_pass = settings.notify_email_imap_password or settings.notify_email_password
    if g_host and g_user and g_pass:
        accounts_to_check.append((g_host, g_port, g_user, g_pass))

    for host, port, user, password in accounts_to_check:
        logger.info(f"Polling IMAP for {user} on {host}:{port}...")
        try:
            mail = imaplib.IMAP4_SSL(host, port, timeout=10.0)
            mail.login(user, password)
            mail.select("inbox")
            
            status, messages = mail.search(None, "UNSEEN")
            if status == "OK" and messages[0]:
                mail_ids = messages[0].split()
                for m_id in mail_ids:
                    status, data = mail.fetch(m_id, "(RFC822)")
                    if status == "OK":
                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        from_header = msg.get("From", "")
                        import re
                        email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", from_header)
                        if email_match:
                            sender_email = email_match.group(0).lower().strip()
                            subject = msg.get("Subject", "")
                            body = _extract_email_body(msg)
                            replied_emails.append({
                                "email": sender_email,
                                "subject": subject,
                                "body": body or "E-posta üzerinden yanıt alındı."
                            })
            mail.close()
            mail.logout()
        except Exception as e:
            logger.error(f"IMAP check replies failed for {user}: {e}")
            
    # Deduplicate by email address
    seen = set()
    deduped = []
    for item in replied_emails:
        if item["email"] not in seen:
            seen.add(item["email"])
            deduped.append(item)
    return deduped


