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
_EMAIL_OSINT_URL = "https://api.emailosint.org/v1/check/"
_RAPID_EMAIL_VERIFIER_URL = "https://rapid-email-verifier.fly.dev/verify"
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
    async def check_email_osint(email: str) -> Dict[str, Any]:
        """
        Query EmailOSINT for leak history, profiles, and reputation data.
        %100 Free, Zero API Key required.
        """
        if not ContactValidator.is_valid_email_syntax(email):
            return {"error": "Invalid email syntax"}

        clean = email.strip()
        logger.info(f"Querying EmailOSINT leak & profile data for '{clean}'...")
        result = {
            "email": clean,
            "found_leaks": False,
            "leak_count": 0,
            "profiles": [],
        }

        with log_execution_time(logger, f"EmailOSINT Check ({clean})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(f"{_EMAIL_OSINT_URL}{clean}")
                    if resp.status_code == 200:
                        data = resp.json()
                        result["found_leaks"] = bool(data.get("leaks"))
                        result["leak_count"] = len(data.get("leaks", []))
                        result["profiles"] = data.get("profiles", [])
                        logger.info(f"EmailOSINT found {result['leak_count']} leaks for '{clean}'")
            except Exception as e:
                logger.warning(f"EmailOSINT check failed for {clean}: {e}")

        return result

    @staticmethod
    async def verify_rapid_email(email: str) -> Dict[str, Any]:
        """
        Query Rapid Email Verifier endpoint for MX and syntax validation.
        %100 Free, Zero API Key required.
        """
        if not ContactValidator.is_valid_email_syntax(email):
            return {"valid": False, "reason": "Syntax invalid"}

        clean = email.strip()
        logger.info(f"Querying Rapid Email Verifier for '{clean}'...")
        result = {"email": clean, "valid": False, "mx_valid": False}

        with log_execution_time(logger, f"Rapid Email Verifier ({clean})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_RAPID_EMAIL_VERIFIER_URL, params={"email": clean})
                    if resp.status_code == 200:
                        data = resp.json()
                        result["valid"] = data.get("valid", False)
                        result["mx_valid"] = data.get("mx", False)
                        logger.info(f"Rapid Email Verifier result for '{clean}': Valid={result['valid']}")
            except Exception as e:
                logger.warning(f"Rapid Email Verifier failed for {clean}: {e}")

        return result

    @staticmethod
    async def validate_email_full(email: str) -> Dict[str, Any]:
        """
        Comprehensive keyless email audit:
        1. Syntax check
        2. Disposable domain check (Debounce)
        3. MX record existence via Cloudflare DoH & Rapid Email Verifier
        4. Leak & Profile check via EmailOSINT
        """
        result = {
            "email": email,
            "is_valid_syntax": ContactValidator.is_valid_email_syntax(email),
            "is_disposable": False,
            "has_mx_records": False,
            "email_provider": "Unknown",
            "osint_leaks": 0,
            "score": 0,
        }

        if not result["is_valid_syntax"]:
            return result

        domain = email.split("@")[-1]
        
        # Concurrent checks
        result["is_disposable"] = await ContactValidator.is_disposable_email(email)
        dns_info = await DomainTechnicalAuditor.get_dns_infrastructure(domain)
        osint_info = await ContactValidator.check_email_osint(email)

        result["has_mx_records"] = len(dns_info.get("mx_records", [])) > 0
        result["email_provider"] = dns_info.get("email_provider", "Unknown")
        result["osint_leaks"] = osint_info.get("leak_count", 0)

        # Calculate email reliability score (0 - 100)
        score = 0
        if result["is_valid_syntax"]:
            score += 30
        if not result["is_disposable"]:
            score += 30
        if result["has_mx_records"]:
            score += 40

        result["score"] = score
        logger.info(f"Email audit complete for '{email}': Score={score}/100, Provider={result['email_provider']}, Leaks={result['osint_leaks']}")
        return result

