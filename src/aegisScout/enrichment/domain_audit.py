"""
Domain Technical & OSINT Auditor (Zero-Config / Keyless).
Uses ICANN RDAP (rdap.org) and Cloudflare DNS-over-HTTPS (1.1.1.1) to audit domain age, registrar, MX records, and security headers.
"""

from typing import Dict, Any, Optional, List
import urllib.parse
import httpx
from aegisScout.utils.logger import get_logger, log_execution_time

logger = get_logger("enrichment.domain_audit")

_RDAP_ENDPOINT = "https://rdap.org/domain/"
_CLOUDFLARE_DOH_ENDPOINT = "https://1.1.1.1/dns-query"
_TIMEOUT = 10.0


def extract_clean_domain(url_or_domain: str) -> Optional[str]:
    """Clean URL or domain input to extract pure hostname (e.g. 'https://example.com/page' -> 'example.com')."""
    if not url_or_domain:
        return None
    raw = url_or_domain.strip().lower()
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = "http://" + raw
    try:
        parsed = urllib.parse.urlparse(raw)
        hostname = parsed.hostname
        if hostname and "." in hostname:
            if hostname.startswith("www."):
                hostname = hostname[4:]
            return hostname
    except Exception:
        pass
    return None


class DomainTechnicalAuditor:
    """
    Zero-config auditor for domain WHOIS registration age and DNS infrastructure.
    """

    @staticmethod
    async def get_rdap_whois(domain: str) -> Dict[str, Any]:
        """Fetch ICANN RDAP WHOIS records without API keys."""
        clean = extract_clean_domain(domain)
        if not clean:
            return {"error": "Invalid domain"}

        logger.info(f"Querying ICANN RDAP WHOIS for domain '{clean}'...")
        result = {
            "domain": clean,
            "registration_date": None,
            "expiration_date": None,
            "registrar": None,
            "status": [],
        }

        with log_execution_time(logger, f"RDAP WHOIS Lookup ({clean})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                    resp = await client.get(f"{_RDAP_ENDPOINT}{clean}", headers={"Accept": "application/rdap+json, application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        # Extract events (creation, expiration)
                        events = data.get("events", [])
                        for event in events:
                            action = event.get("eventAction")
                            date_val = event.get("eventDate")
                            if action in ("registration", "transfer"):
                                result["registration_date"] = date_val
                            elif action == "expiration":
                                result["expiration_date"] = date_val

                        # Extract registrar entities
                        entities = data.get("entities", [])
                        for entity in entities:
                            roles = entity.get("roles", [])
                            if "registrar" in roles:
                                vcard = entity.get("vcardArray", [])
                                if len(vcard) >= 2:
                                    for prop in vcard[1]:
                                        if prop[0] == "fn":
                                            result["registrar"] = prop[3]
                                            break

                        result["status"] = data.get("status", [])
                    else:
                        logger.debug(f"RDAP lookup returned HTTP {resp.status_code} for {clean}")
            except Exception as e:
                logger.warning(f"RDAP WHOIS lookup failed for {clean}: {e}")

        return result

    @staticmethod
    async def get_dns_infrastructure(domain: str) -> Dict[str, Any]:
        """Query Cloudflare DNS over HTTPS for MX records, SPF, and DMARC."""
        clean = extract_clean_domain(domain)
        if not clean:
            return {"error": "Invalid domain"}

        logger.info(f"Querying Cloudflare DoH for domain '{clean}'...")
        result = {
            "domain": clean,
            "mx_records": [],
            "email_provider": "Unknown",
            "has_spf": False,
            "has_dmarc": False,
        }

        headers = {"Accept": "application/dns-json"}

        with log_execution_time(logger, f"Cloudflare DoH Query ({clean})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    # 1. Fetch MX Records
                    mx_resp = await client.get(_CLOUDFLARE_DOH_ENDPOINT, params={"name": clean, "type": "MX"}, headers=headers)
                    if mx_resp.status_code == 200:
                        answers = mx_resp.json().get("Answer", [])
                        for ans in answers:
                            mx_data = ans.get("data", "").lower()
                            if mx_data:
                                result["mx_records"].append(mx_data)
                                if "google" in mx_data or "gmail" in mx_data:
                                    result["email_provider"] = "Google Workspace"
                                elif "outlook" in mx_data or "microsoft" in mx_data:
                                    result["email_provider"] = "Microsoft 365"
                                elif "yandex" in mx_data:
                                    result["email_provider"] = "Yandex Mail"
                                elif "protonmail" in mx_data:
                                    result["email_provider"] = "ProtonMail"
                                elif "zoho" in mx_data:
                                    result["email_provider"] = "Zoho Mail"
                                elif result["email_provider"] == "Unknown":
                                    result["email_provider"] = "Custom / cPanel Webmail"

                    # 2. Fetch TXT Records (SPF check)
                    txt_resp = await client.get(_CLOUDFLARE_DOH_ENDPOINT, params={"name": clean, "type": "TXT"}, headers=headers)
                    if txt_resp.status_code == 200:
                        answers = txt_resp.json().get("Answer", [])
                        for ans in answers:
                            txt_data = ans.get("data", "")
                            if "v=spf1" in txt_data:
                                result["has_spf"] = True
                                break

                    # 3. Fetch DMARC Record
                    dmarc_resp = await client.get(_CLOUDFLARE_DOH_ENDPOINT, params={"name": f"_dmarc.{clean}", "type": "TXT"}, headers=headers)
                    if dmarc_resp.status_code == 200:
                        answers = dmarc_resp.json().get("Answer", [])
                        for ans in answers:
                            if "v=dmarc1" in ans.get("data", "").lower():
                                result["has_dmarc"] = True
                                break

            except Exception as e:
                logger.warning(f"Cloudflare DoH DNS query failed for {clean}: {e}")

        return result

    @staticmethod
    async def get_ip_geolocation(domain_or_ip: str) -> Dict[str, Any]:
        """
        Query IP-API.com for domain/IP hosting provider, server location, ISP, and ASN.
        %100 Free, Zero API Key required.
        """
        clean = extract_clean_domain(domain_or_ip) or domain_or_ip.strip()
        if not clean:
            return {"error": "Invalid domain or IP"}

        logger.info(f"Querying IP-API Geolocation for '{clean}'...")
        endpoint = f"http://ip-api.com/json/{clean}"
        result = {
            "query": clean,
            "status": "fail",
            "country": None,
            "city": None,
            "isp": None,
            "org": None,
            "as": None,
            "hosting": False,
        }

        with log_execution_time(logger, f"IP-API Geolocation ({clean})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(endpoint)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "success":
                            result.update({
                                "status": "success",
                                "country": data.get("country"),
                                "country_code": data.get("countryCode"),
                                "city": data.get("city"),
                                "isp": data.get("isp"),
                                "org": data.get("org"),
                                "as": data.get("as"),
                                "lat": data.get("lat"),
                                "lon": data.get("lon"),
                                "hosting": data.get("hosting", False),
                            })
                            logger.info(f"IP-API resolved '{clean}' -> ISP: {result['isp']}, Location: {result['city']}, {result['country']}")
            except Exception as e:
                logger.warning(f"IP-API Geolocation lookup failed for {clean}: {e}")

        return result

    @staticmethod
    async def audit_domain_full(domain: str) -> Dict[str, Any]:
        """
        Run complete technical domain audit combining RDAP WHOIS, Cloudflare DoH, and IP-API Geolocation.
        """
        clean = extract_clean_domain(domain)
        if not clean:
            return {"error": "Invalid domain"}

        whois_info = await DomainTechnicalAuditor.get_rdap_whois(clean)
        dns_info = await DomainTechnicalAuditor.get_dns_infrastructure(clean)
        geo_info = await DomainTechnicalAuditor.get_ip_geolocation(clean)

        return {
            "domain": clean,
            "whois": whois_info,
            "dns": dns_info,
            "hosting_geo": geo_info,
        }

