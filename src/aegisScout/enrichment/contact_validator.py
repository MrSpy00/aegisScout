"""
Contact & Email Validator (Zero-Config / Keyless).
Validates email syntax, checks for disposable/temporary domains via Debounce Free API, and performs keyless MX validation.
"""

from typing import Dict, Any, Optional
import re
import httpx
from aegisScout.enrichment.domain_audit import DomainTechnicalAuditor
from aegisScout.utils.logger import get_logger, log_execution_time

logger = get_logger("enrichment.contact_validator")

_DEBOUNCE_DISPOSABLE_URL = "https://disposable.debounce.io/"
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_TIMEOUT = 8.0


class ContactValidator:
    """
    Zero-config email and contact validation suite.
    """

    @staticmethod
    def is_valid_email_syntax(email: str) -> bool:
        """Check email syntax against regex."""
        if not email or not isinstance(email, str):
            return False
        return bool(_EMAIL_REGEX.match(email.strip()))

    @staticmethod
    async def is_disposable_email(email: str) -> bool:
        """Check if an email domain belongs to a known temporary/disposable mail service."""
        if not ContactValidator.is_valid_email_syntax(email):
            return False

        logger.info(f"Checking disposable status for email '{email}' via Debounce API...")
        with log_execution_time(logger, f"Debounce Disposable Check ({email})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_DEBOUNCE_DISPOSABLE_URL, params={"email": email.strip()})
                    if resp.status_code == 200:
                        data = resp.json()
                        # Returns {"disposable": "true" | "false"}
                        disposable_val = str(data.get("disposable", "")).lower()
                        return disposable_val == "true"
            except Exception as e:
                logger.warning(f"Debounce disposable check failed for {email}: {e}")

        return False

    @staticmethod
    async def validate_email_full(email: str) -> Dict[str, Any]:
        """
        Comprehensive keyless email audit:
        1. Syntax check
        2. Disposable domain check
        3. MX record existence via Cloudflare DoH
        """
        result = {
            "email": email,
            "is_valid_syntax": ContactValidator.is_valid_email_syntax(email),
            "is_disposable": False,
            "has_mx_records": False,
            "email_provider": "Unknown",
            "score": 0,
        }

        if not result["is_valid_syntax"]:
            return result

        domain = email.split("@")[-1]
        
        # Concurrent checks
        result["is_disposable"] = await ContactValidator.is_disposable_email(email)
        dns_info = await DomainTechnicalAuditor.get_dns_infrastructure(domain)

        result["has_mx_records"] = len(dns_info.get("mx_records", [])) > 0
        result["email_provider"] = dns_info.get("email_provider", "Unknown")

        # Calculate email reliability score (0 - 100)
        score = 0
        if result["is_valid_syntax"]:
            score += 30
        if not result["is_disposable"]:
            score += 30
        if result["has_mx_records"]:
            score += 40

        result["score"] = score
        logger.info(f"Email audit complete for '{email}': Score={score}/100, Provider={result['email_provider']}")
        return result
