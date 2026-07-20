"""
P2P Email Warmup Module.
Simulates natural email interactions between configured SMTP/IMAP accounts.
Rescues emails from Spam, marks them as read, stars them, and replies with AI-generated text.
"""

from __future__ import annotations

import json
import random
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from sqlmodel import Session, select

from aegisScout.core.database import engine
from aegisScout.core.models import SmtpAccount, Message
from aegisScout.utils.encryption import decrypt_string
from aegisScout.ai.provider_router import ProviderRouter
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

from aegisScout.utils.paths import get_data_dir

logger = get_logger("outreach.warmup")

STATS_FILE = get_data_dir() / "warmup_stats.json"


def _load_stats() -> Dict[str, int]:
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sent": 0, "replied": 0, "spam_rescued": 0, "starred": 0}


def _save_stats(stats: Dict[str, int]) -> None:
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save warmup stats: {e}")


def _increment_stat(key: str) -> None:
    stats = _load_stats()
    stats[key] = stats.get(key, 0) + 1
    _save_stats(stats)


# Offline natural templates to generate random email threads if no LLM API key exists
SUBJECT_TEMPLATES = [
    "İş Ortaklığı ve Sinerji Hakkında",
    "Hızlı Bir Soru - Dijital Süreçler",
    "Buluşma ve Kahve Talebi",
    "Hizmet Detayları ve Fiyat Teklifi",
    "Proje Yönetimi ve İş Akışları",
    "Geri Bildirim Alışverişi",
    "Sektörel Trendler Üzerine Bir Soru"
]

BODY_TEMPLATES = [
    "Merhaba, şirketinizin sektörel çalışmalarını takip ediyoruz. Ortak bir sinerji oluşturmak adına haftaya kısa bir kahve toplantısı planlayabilir miyiz?",
    "Selamlar, web sitenizdeki servis detaylarını inceledim. Hizmetlerinizin fiyatlandırma politikası ve kurumsal paketleriniz hakkında detaylı bilgi alabilir miyim?",
    "Merhaba, dijital pazarlama ve otomasyon süreçlerinizi hangi sistemlerle yönetiyorsunuz? Bizim kullandığımız yöntemler hakkında deneyimlerinizi paylaşmak isterim.",
    "İyi çalışmalar, projemizin teknik entegrasyon süreçlerinde dışarıdan destek almayı düşünüyoruz. Müsait bir zamanınızda detayları konuşabilir miyiz?",
    "Selamlar, sektörel iş birlikleri ve potansiyel ortak projeler için ekiplerimizi bir araya getirmeyi teklif ediyorum. Konu hakkında ne düşünürsünüz?"
]

REPLY_TEMPLATES = [
    "Merhaba, mailiniz için teşekkürler. Teklifiniz oldukça ilgimizi çekti, haftaya Salı günü öğleden sonra görüşmek üzere planlama yapabiliriz.",
    "Selamlar, detaylı geri dönüşünüz için teşekkür ederim. Gönderdiğiniz dokümanları inceleyip en kısa sürede size bir toplantı daveti ileteceğim.",
    "İyi çalışmalar, bahsettiğiniz ortaklık fırsatı bizim yol haritamızla eşleşiyor. Perşembe günü saat 14:00 sizin için de uygun mudur?",
    "Merhaba, sorunuz için teşekkürler. Şu anda iş yoğunluğumuz sebebiyle yeni entegrasyonlara başlayamıyoruz fakat önümüzdeki ay detaylı konuşabiliriz.",
    "Selamlar, kahve davetiniz için teşekkür ederim. Gelecek hafta Çarşamba günü saat 10:00'da Zoom üzerinden görüşebiliriz, iyi haftalar dilerim."
]


_router: Optional[ProviderRouter] = None


def _get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


async def generate_warmup_email() -> Tuple[str, str]:
    """Generate a natural email subject and body using Gemini, or fallback to offline templates."""
    if settings.gemini_api_key:
        try:
            router = _get_router()
            prompt = (
                "Write a short, realistic, 2-3 sentence business email in Turkish. "
                "The email should sound like a natural inquiry, partnership request, or scheduling request. "
                "Provide a subject line as well. "
                "Output ONLY in the following format:\n"
                "Subject: [Subject Line]\n\n"
                "[Email Body]"
            )
            response = await router.generate(prompt=prompt, system_prompt="You are writing a natural business email to keep mailboxes active.")
            
            subject = "İş Birliği Hakkında"
            body = response.strip()
            
            # Extract Subject
            match = re.search(r"Subject:\s*(.*)", response, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                # Remove subject prefix from body
                body = re.sub(r"Subject:.*\n*", "", response, flags=re.IGNORECASE).strip()
                
            return subject, body
        except Exception as e:
            logger.error(f"LLM warmup generation failed: {e}. Falling back to templates.")
            
    # Template Fallback
    return random.choice(SUBJECT_TEMPLATES), random.choice(BODY_TEMPLATES)


async def generate_warmup_reply(original_body: str) -> str:
    """Generate a realistic reply to an email using Gemini, or fallback to templates."""
    if settings.gemini_api_key:
        try:
            router = _get_router()
            prompt = (
                f"Write a short, natural, 1-2 sentence reply in Turkish to this email:\n"
                f"'{original_body}'\n\n"
                f"Output only the reply text. Do not include any greeting or signature placeholders."
            )
            response = await router.generate(prompt=prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"LLM warmup reply generation failed: {e}. Falling back to templates.")
            
    return random.choice(REPLY_TEMPLATES)


def _send_email_via_smtp(account: SmtpAccount, to_email: str, subject: str, body: str) -> bool:
    """Send SMTP email using the given SmtpAccount credentials."""
    try:
        password = decrypt_string(account.smtp_pass)
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = account.smtp_user
        msg["To"] = to_email
        
        # Connect to SMTP
        server = smtplib.SMTP(account.smtp_host, account.smtp_port or 587, timeout=10.0)
        server.ehlo()
        if (account.smtp_port or 587) in (587, 25, 465):
            server.starttls()
            server.ehlo()
        server.login(account.smtp_user, password)
        server.sendmail(account.smtp_user, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Warmup mail sent from {account.smtp_user} to {to_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP Warmup send failed for {account.smtp_user}: {e}")
        return False


def _process_imap_inbox(account: SmtpAccount, sender_email: str) -> List[Tuple[str, str, str]]:
    """
    Connect to IMAP, search for emails from sender_email,
    mark them as read, move from Spam to Inbox if necessary, star them,
    and return list of (uid, subject, body).
    """
    found_messages = []
    try:
        password = decrypt_string(account.imap_pass or account.smtp_pass)
        host = account.imap_host or account.smtp_host.replace("smtp", "imap")
        port = account.imap_port or 993
        
        mail = imaplib.IMAP4_SSL(host, port, timeout=10.0)
        mail.login(account.imap_user or account.smtp_user, password)
        
        # 1. First search Spam/Junk folders
        spam_folders = ["spam", "junk", "spambox", "junk mail"]
        # Try to locate a spam folder and scan it
        all_folders = []
        status, folder_list = mail.list()
        if status == "OK" and folder_list:
            for folder_bytes in folder_list:
                if isinstance(folder_bytes, bytes):
                    parts = folder_bytes.decode("utf-8", errors="ignore").split()
                    if parts:
                        all_folders.append(parts[-1].strip('"'))
        target_spam_folder = None
        for folder in all_folders:
            folder_lower = folder.lower()
            if any(s in folder_lower for s in spam_folders):
                target_spam_folder = folder
                break
                
        if target_spam_folder:
            try:
                mail.select(f'"{target_spam_folder}"')
                status, search_data = mail.search(None, f'FROM "{sender_email}"')
                if status == "OK" and search_data[0]:
                    for msg_id in search_data[0].split():
                        logger.info(f"Rescuing warmup email from Spam folder: {target_spam_folder} for {account.smtp_user}")
                        # Copy to Inbox
                        mail.copy(msg_id, "INBOX")
                        # Delete from Spam
                        mail.store(msg_id, "+FLAGS", "\\Deleted")
                        _increment_stat("spam_rescued")
                    mail.expunge()
            except Exception as e:
                logger.warning(f"Error checking spam folder {target_spam_folder}: {e}")

        # 2. Select Gelen Kutusu (INBOX)
        mail.select("INBOX")
        status, search_data = mail.search(None, f'(UNSEEN FROM "{sender_email}")')
        if status == "OK" and search_data[0]:
            for msg_id in search_data[0].split():
                # Fetch message details
                status, fetch_data = mail.fetch(msg_id, "(RFC822)")
                if status == "OK" and fetch_data[0] and isinstance(fetch_data[0], tuple):
                    raw_email = fetch_data[0][1]
                    if isinstance(raw_email, (bytes, bytearray)):
                        msg = email.message_from_bytes(raw_email)
                        subject = str(msg.get("Subject", ""))
                        
                        # Extract body text
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if isinstance(payload, bytes):
                                        body = payload.decode("utf-8", errors="ignore")
                                    break
                        else:
                            payload = msg.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                body = payload.decode("utf-8", errors="ignore")
                            
                        found_messages.append((msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id), subject, body))
                    
                    # Mark as read/seen
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    # Star/Flag message
                    mail.store(msg_id, "+FLAGS", "\\Flagged")
                    _increment_stat("starred")
                    
        mail.close()
        mail.logout()
    except Exception as e:
        logger.error(f"IMAP process failed for {account.smtp_user}: {e}")
        
    return found_messages


async def run_p2p_warmup_cycle() -> Dict[str, Any]:
    """
    Orchestrate a single P2P Warmup step:
      1. Pick two random active SMTP accounts.
      2. Sender sends a natural email to Receiver.
      3. Receiver processes Inbox/Spam (marks read, stars, rescues if needed).
      4. Receiver sends a reply back.
      5. Sender processes reply (marks read, stars).
    """
    logger.info("Initializing P2P Email Warmup Cycle...")
    
    with Session(engine) as session:
        accounts = session.exec(select(SmtpAccount).where(SmtpAccount.is_active == True)).all()
        if len(accounts) < 2:
            return {
                "success": False,
                "error": "P2P Warmup için en az 2 aktif SMTP/IMAP hesabı eklenmelidir."
            }
            
        # Select two different random accounts
        sender = random.choice(accounts)
        remaining = [acc for acc in accounts if acc.id != sender.id]
        receiver = random.choice(remaining)
        
        # 1. Generate Content
        subject, body = await generate_warmup_email()
        
        # 2. Sender -> SMTP -> Receiver
        send_success = _send_email_via_smtp(sender, receiver.smtp_user, subject, body)
        if not send_success:
            return {"success": False, "error": f"Gönderici ({sender.smtp_user}) e-posta gönderemedi."}
            
        _increment_stat("sent")
        
        # Wait a few seconds for mail delivery
        import asyncio
        await asyncio.sleep(5)
        
        # 3. Receiver IMAP check
        inbound_mails = _process_imap_inbox(receiver, sender.smtp_user)
        if not inbound_mails:
            logger.info("Email sent, but not yet indexed or received by Receiver's IMAP server.")
            return {
                "success": True,
                "details": f"E-posta gönderildi ({sender.smtp_user} -> {receiver.smtp_user}), ancak alıcı henüz dizine eklemedi."
            }
            
        # 4. Receiver -> Reply -> Sender
        for uid, sub, bdy in inbound_mails:
            reply_body = await generate_warmup_reply(bdy)
            reply_subject = f"Re: {sub}"
            
            reply_success = _send_email_via_smtp(receiver, sender.smtp_user, reply_subject, reply_body)
            if reply_success:
                _increment_stat("replied")
                
                # Wait for delivery of reply
                await asyncio.sleep(5)
                # 5. Sender IMAP check to mark reply as read and star it
                _process_imap_inbox(sender, receiver.smtp_user)

        stats = _load_stats()
        return {
            "success": True,
            "details": f"Warmup döngüsü tamamlandı: {sender.smtp_user} <-> {receiver.smtp_user}",
            "stats": stats
        }
