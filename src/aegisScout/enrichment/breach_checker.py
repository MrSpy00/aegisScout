"""
Breach Checker Module for aegisScout.

Checks email addresses against known data breach databases:
  - XposedOrNot: Free alternative to HIBP, no API key required
  - HIBP Pwned Passwords: K-anonymity model, completely free and unlimited
  - Google dorking patterns for breach data

NO API KEY REQUIRED for any of these services.
"""
from __future__ import annotations

import hashlib
from typing import Dict, Any, List, Optional

import httpx
from aegisScout.utils.logger import get_logger

logger = get_logger("enrichment.breach_checker")


async def check_xposedornot(email: str) -> Dict[str, Any]:
    """
    Check if an email appears in known data breaches via XposedOrNot.
    Free API, no key required.
    
    Returns: breached (bool), breach_count (int), breaches (list of dicts)
    """
    result = {
        "breached": False,
        "breach_count": 0,
        "breaches": [],
        "exposures": [],
        "error": None,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.xposedornot.com/v1/check-email/{email}",
                headers={"Accept": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                breaches = data.get("breaches", [])
                if breaches:
                    result["breached"] = True
                    result["breach_count"] = len(breaches)
                    result["breaches"] = breaches
            elif resp.status_code == 404:
                # Not found in any breach
                result["breached"] = False
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"XposedOrNot check failed for {email}: {e}")
    
    return result


async def check_hibp_password(password: str) -> Dict[str, Any]:
    """
    Check if a password has been seen in data breaches via HIBP Pwned Passwords.
    Uses k-anonymity model (only first 5 chars of SHA1 hash sent).
    Completely free, unlimited, no API key required.
    
    Args:
        password: Plain text password to check
    
    Returns: pwned (bool), count (int) - number of times seen in breaches
    """
    result = {"pwned": False, "count": 0, "error": None}
    try:
        # SHA1 hash of password
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"Add-Padding": "true"}
            )
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2 and parts[0].upper() == suffix:
                        count = int(parts[1].strip())
                        result["pwned"] = count > 0
                        result["count"] = count
                        break
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"HIBP password check failed: {e}")
    
    return result


def generate_breach_summary(email: str, xon_result: Dict[str, Any]) -> str:
    """
    Generate a human-readable breach report summary.
    """
    if xon_result.get("error"):
        return f"🔍 Sızıntı kontrolü yapılamadı: {xon_result['error']}"
    
    if not xon_result.get("breached"):
        return f"✅ {email} — Bilinen veri sızıntılarında bulunmadı"
    
    breach_count = xon_result.get("breach_count", 0)
    breaches = xon_result.get("breaches", [])
    
    lines = [
        f"⚠️ {email} — {breach_count} veri sızıntısında tespit edildi!",
    ]
    
    if breaches:
        lines.append("  Sızıntılar:")
        for breach in breaches[:5]:  # Show max 5
            if isinstance(breach, str):
                lines.append(f"    • {breach}")
            elif isinstance(breach, dict):
                name = breach.get("breach", breach.get("name", "Bilinmiyor"))
                lines.append(f"    • {name}")
    
    return "\n".join(lines)


async def full_breach_check(email: str) -> Dict[str, Any]:
    """
    Run all available breach checks on an email address.
    Returns comprehensive breach intelligence report.
    """
    import asyncio
    
    logger.info(f"Running breach check for: {email}")
    
    xon_result = await check_xposedornot(email)
    
    return {
        "email": email,
        "xposedornot": xon_result,
        "breached": xon_result.get("breached", False),
        "total_breaches": xon_result.get("breach_count", 0),
        "summary": generate_breach_summary(email, xon_result),
    }


__all__ = [
    "check_xposedornot",
    "check_hibp_password",
    "full_breach_check",
    "generate_breach_summary",
]
