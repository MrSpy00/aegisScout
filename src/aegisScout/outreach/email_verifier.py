"""
Zero-Cost Local Email Verifier for aegisScout.

Provides offline/local email validation without external API fees:
  1. Syntax & Regex validation.
  2. Role account detection (admin@, info@, support@, etc.).
  3. Disposable email provider matching against an in-memory blacklist.
  4. DNS MX record lookup (via dnspython or socket fallback).
  5. Non-intrusive SMTP handshake simulation (EHLO, MAIL FROM, RCPT TO, QUIT).
"""

import re
import socket
from typing import Dict, Any, List, Optional
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.email_verifier")

# Common syntax regex for email addresses
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# Common role-based prefixes
ROLE_PREFIXES = {
    "admin", "administrator", "info", "support", "sales", "contact",
    "help", "office", "marketing", "billing", "jobs", "careers",
    "enquiries", "inquiries", "team", "postmaster", "hostmaster", "webmaster"
}

# Known disposable email domains (built-in offline database)
DISPOSABLE_DOMAINS = {
    "10minutemail.com", "10minutemail.net", "tempmail.com", "temp-mail.org",
    "guerrillamail.com", "guerrillamail.net", "mailinator.com", "throwawaymail.com",
    "yopmail.com", "sharklasers.com", "dispostable.com", "getairmail.com",
    "maildrop.cc", "trashmail.com", "binkmail.com", "safetymail.info",
    "nada.ltd", "tempmail.net", "crazymailing.com", "mytemp.email"
}


def is_valid_syntax(email: str) -> bool:
    """Check if the email matches standard email regex format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_disposable(email: str) -> bool:
    """Check if the email belongs to a known disposable domain."""
    if not email or "@" not in email:
        return False
    domain = email.strip().split("@")[-1].lower()
    return domain in DISPOSABLE_DOMAINS


def is_role_account(email: str) -> bool:
    """Check if the local part is a role-based address (e.g., info@, admin@)."""
    if not email or "@" not in email:
        return False
    local_part = email.strip().split("@")[0].lower()
    return local_part in ROLE_PREFIXES


def get_mx_records(domain: str) -> List[str]:
    """Retrieve MX records for a domain using dnspython with socket fallback."""
    mx_records: List[str] = []

    # 1. Try dnspython if installed
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5.0)
        for rdata in sorted(answers, key=lambda r: r.preference):
            mx_records.append(str(rdata.exchange).rstrip("."))
        if mx_records:
            return mx_records
    except Exception as e:
        logger.debug(f"dnspython MX lookup failed for {domain}: {e}")

    # 2. Fallback: socket getaddrinfo for host resolution
    try:
        addr = socket.gethostbyname(domain)
        if addr:
            mx_records.append(domain)
    except Exception as e:
        logger.debug(f"Socket fallback lookup failed for {domain}: {e}")

    return mx_records


def simulate_smtp_handshake(
    email: str,
    mx_host: str,
    timeout: float = 6.0,
    from_email: str = "verify@aegisscout-local.org"
) -> Dict[str, Any]:
    """
    Simulate an SMTP handshake without actually sending an email:
      CONNECT -> EHLO -> MAIL FROM -> RCPT TO -> QUIT
    Returns dict with success status, response code, and message.
    """
    try:
        sock = socket.create_connection((mx_host, 25), timeout=timeout)
        sock.settimeout(timeout)

        def receive_line() -> str:
            data = sock.recv(1024).decode("utf-8", errors="ignore")
            return data.strip()

        def send_cmd(cmd: str) -> str:
            sock.sendall((cmd + "\r\n").encode("utf-8"))
            return receive_line()

        banner = receive_line()
        if not banner.startswith("220"):
            sock.close()
            return {"success": False, "code": banner[:3], "msg": banner, "status": "connect_failed"}

        ehlo_resp = send_cmd("EHLO aegisscout-local.org")
        if not ehlo_resp.startswith("250"):
            ehlo_resp = send_cmd("HELO aegisscout-local.org")

        mail_resp = send_cmd(f"MAIL FROM:<{from_email}>")
        rcpt_resp = send_cmd(f"RCPT TO:<{email}>")

        try:
            send_cmd("QUIT")
        except Exception:
            pass
        sock.close()

        if rcpt_resp.startswith("250"):
            return {"success": True, "code": "250", "msg": rcpt_resp, "status": "valid"}
        elif rcpt_resp.startswith("550") or rcpt_resp.startswith("551") or rcpt_resp.startswith("553"):
            return {"success": False, "code": rcpt_resp[:3], "msg": rcpt_resp, "status": "invalid"}
        elif rcpt_resp.startswith("450") or rcpt_resp.startswith("451") or rcpt_resp.startswith("452"):
            return {"success": False, "code": rcpt_resp[:3], "msg": rcpt_resp, "status": "catch_all_or_greylisted"}
        else:
            return {"success": False, "code": rcpt_resp[:3], "msg": rcpt_resp, "status": "unknown"}

    except socket.timeout:
        return {"success": False, "code": "TIMEOUT", "msg": "Connection timed out", "status": "timeout"}
    except Exception as e:
        return {"success": False, "code": "ERROR", "msg": str(e), "status": "connection_error"}


class EmailVerifier:
    """High-level local email verification manager."""

    def __init__(self, check_smtp: bool = True, timeout: float = 6.0):
        self.check_smtp = check_smtp
        self.timeout = timeout

    def verify(self, email: str) -> Dict[str, Any]:
        """
        Full verification pipeline for a given email address.
        """
        if not email or not isinstance(email, str):
            return {
                "email": email,
                "valid": False,
                "status": "invalid_syntax",
                "reason": "Email string is empty or invalid type",
                "is_disposable": False,
                "is_role_account": False,
                "mx_records": []
            }

        clean_email = email.strip()

        # Step 1: Syntax check
        if not is_valid_syntax(clean_email):
            return {
                "email": clean_email,
                "valid": False,
                "status": "invalid_syntax",
                "reason": "Email format violates RFC 5322 syntax",
                "is_disposable": False,
                "is_role_account": False,
                "mx_records": []
            }

        disp = is_disposable(clean_email)
        role = is_role_account(clean_email)

        if disp:
            return {
                "email": clean_email,
                "valid": False,
                "status": "disposable",
                "reason": "Email domain is a known temporary/disposable service",
                "is_disposable": True,
                "is_role_account": role,
                "mx_records": []
            }

        domain = clean_email.split("@")[-1].lower()

        # Step 2: DNS MX lookup
        mx_records = get_mx_records(domain)
        if not mx_records:
            return {
                "email": clean_email,
                "valid": False,
                "status": "no_mx",
                "reason": f"No valid MX records found for domain '{domain}'",
                "is_disposable": False,
                "is_role_account": role,
                "mx_records": []
            }

        # Step 3: Optional SMTP handshake check
        if self.check_smtp:
            primary_mx = mx_records[0]
            smtp_result = simulate_smtp_handshake(clean_email, primary_mx, timeout=self.timeout)
            is_valid = smtp_result.get("status") == "valid"
            return {
                "email": clean_email,
                "valid": is_valid,
                "status": smtp_result.get("status", "unknown"),
                "reason": smtp_result.get("msg", "SMTP check performed"),
                "is_disposable": False,
                "is_role_account": role,
                "mx_records": mx_records,
                "smtp_details": smtp_result
            }

        return {
            "email": clean_email,
            "valid": True,
            "status": "valid_syntax_and_mx",
            "reason": "Syntax and MX records verified",
            "is_disposable": False,
            "is_role_account": role,
            "mx_records": mx_records
        }
