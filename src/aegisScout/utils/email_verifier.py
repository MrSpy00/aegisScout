"""
Local Email Verifier module.
Performs format check, disposable domain check, DNS MX resolution,
and socket-based SMTP handshake simulation.
"""

from __future__ import annotations

import re
import socket
import dns.resolver
from pathlib import Path
from aegisScout.utils.logger import get_logger

logger = get_logger("utils.email_verifier")

# A list of common disposable email services
DEFAULT_DISPOSABLE_DOMAINS = {
    "10minutemail.co.za", "10minutemail.com", "yopmail.com", "mailinator.com",
    "tempmail.com", "guerrillamail.com", "dispostable.com", "getairmail.com",
    "throwawaymail.com", "temp-mail.org", "sharklasers.com", "guerillamail.info",
    "guerillamailblock.com", "guerillamail.net", "guerillamail.org",
    "guerillamail.biz", "spam4.me", "grr.la", "guerillamail.de", "trashmail.com",
    "maildrop.cc", "mintemail.com", "mailnesia.com", "mailcatch.com",
    "harakirimail.com", "mytrashmail.com", "anonymousspeech.com", "tempemail.co"
}

def load_disposable_domains() -> set[str]:
    """Load disposable domains from file if it exists, otherwise return default set."""
    from aegisScout.utils.paths import get_data_dir
    file_path = get_data_dir() / "disposable_domains.txt"
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                domains = {line.strip().lower() for line in f if line.strip()}
                if domains:
                    return domains
        except Exception as e:
            logger.warning(f"Disposable domain file could not be read: {e}")
    return DEFAULT_DISPOSABLE_DOMAINS

DISPOSABLE_DOMAINS = load_disposable_domains()

def verify_email(email: str, sender_email: str = "verify@aegisScout.local") -> dict:
    """
    Verify email address locally:
      1. Regex format check
      2. Disposable domain check
      3. DNS MX check
      4. SMTP handshake simulation
      
    Returns a dict:
      {
         "success": bool,
         "status": "valid" | "invalid" | "unknown" | "mx_only",
         "details": str
      }
    """
    email = email.strip()
    if not email:
        return {"success": False, "status": "invalid", "details": "Boş e-posta adresi."}

    # 1. Regex Match
    # Matches typical standard email format
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return {"success": False, "status": "invalid", "details": "E-posta formatı geçersiz."}

    parts = email.split("@")
    if len(parts) != 2:
        return {"success": False, "status": "invalid", "details": "E-posta formatı geçersiz (Eksik @ veya çoklu @)."}
    
    local_part, domain = parts[0], parts[1].lower()

    # 2. Disposable check
    if domain in DISPOSABLE_DOMAINS:
        return {"success": False, "status": "invalid", "details": "Geçici (disposable) e-posta adresi."}

    # 3. DNS MX Lookup
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_servers = [str(r.exchange).rstrip(".") for r in answers]
        if not mx_servers:
            return {"success": False, "status": "invalid", "details": "Domain için MX kaydı bulunamadı."}
    except Exception as e:
        logger.warning(f"DNS MX lookup failed for {domain}: {e}")
        return {"success": False, "status": "invalid", "details": f"DNS MX sorgusu başarısız: {str(e)}"}

    # Sort MX servers by priority (lower priority values come first in DNS answers)
    # dnspython answers are sorted by preference by default.
    mx_server = mx_servers[0]

    # 4. SMTP Handshake simulation
    logger.info(f"Simulating SMTP handshake for {email} on {mx_server}...")
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(7.0) # 7 seconds timeout
        sock.connect((mx_server, 25))
        
        # Read SMTP banner
        banner = sock.recv(1024).decode("utf-8", errors="ignore")
        
        # Send HELO
        sock.sendall(b"HELO aegisScout.local\r\n")
        helo_resp = sock.recv(1024).decode("utf-8", errors="ignore")
        
        # Send MAIL FROM
        sock.sendall(f"MAIL FROM:<{sender_email}>\r\n".encode("utf-8"))
        mail_resp = sock.recv(1024).decode("utf-8", errors="ignore")
        
        # Send RCPT TO
        sock.sendall(f"RCPT TO:<{email}>\r\n".encode("utf-8"))
        rcpt_resp = sock.recv(1024).decode("utf-8", errors="ignore")
        
        # Send QUIT and close
        sock.sendall(b"QUIT\r\n")
        sock.close()
        
        # Check RCPT TO response
        if rcpt_resp.startswith("250") or rcpt_resp.startswith("251"):
            return {
                "success": True,
                "status": "valid",
                "details": f"SMTP Doğrulama Başarılı: {rcpt_resp.strip()}"
            }
        elif rcpt_resp.startswith("550") or rcpt_resp.startswith("551") or rcpt_resp.startswith("552") or rcpt_resp.startswith("553") or rcpt_resp.startswith("554"):
            return {
                "success": False,
                "status": "invalid",
                "details": f"Adres bulunamadı (SMTP Sunucu Reddi): {rcpt_resp.strip()}"
            }
        else:
            return {
                "success": True,
                "status": "unknown",
                "details": f"Belirsiz SMTP Yanıt Kodu: {rcpt_resp.strip()}"
            }
            
    except (socket.timeout, ConnectionRefusedError, OSError) as sock_err:
        logger.warning(f"SMTP Handshake connection error for {email}: {sock_err}")
        # Workaround for local ISP blocks: return mx_only (indicating MX is active, but handshake couldn't complete)
        return {
            "success": True,
            "status": "mx_only",
            "details": f"SMTP bağlantısı kurulamadı (Port 25 blokeli olabilir). Ancak MX kaydı mevcut: {mx_server} ({sock_err})"
        }
