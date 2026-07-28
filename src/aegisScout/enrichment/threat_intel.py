"""
Threat Intelligence Module for aegisScout.

Gathers threat intelligence from multiple FREE, no-API-key sources:
  - AlienVault OTX: Free API key, threat feeds, IOC lookup
  - AbuseIPDB: Free tier (1000 req/day), IP reputation
  - URLScan.io: Public scans (no key for public), sandbox results
  - GreyNoise Community: Free, scanner/noise/riot classification
  - PhishTank: Free, phishing URL checking
  - ThreatFox (abuse.ch): Free, malware/C2 IOC database
"""
from __future__ import annotations

import json
from typing import Dict, Any, List, Optional

import httpx
from aegisScout.utils.logger import get_logger

logger = get_logger("enrichment.threat_intel")


async def _safe_get(client: httpx.AsyncClient, url: str, headers: dict = None, **kwargs) -> Optional[httpx.Response]:
    try:
        h = headers or {}
        resp = await client.get(url, headers=h, timeout=12.0, **kwargs)
        if resp.status_code == 200:
            return resp
    except Exception as e:
        logger.debug(f"GET {url} failed: {e}")
    return None


# ---------------------------------------------------------------------------
# 1. GreyNoise Community API (FREE, no key required)
# ---------------------------------------------------------------------------

async def check_greynoise(ip: str) -> Dict[str, Any]:
    """
    Check an IP address against GreyNoise Community API.
    No API key required for community tier (50 requests/day).
    
    Returns: noise (bool), riot (bool), classification, name, message
    """
    result = {
        "ip": ip,
        "noise": False,
        "riot": False, 
        "classification": "unknown",
        "name": None,
        "message": None,
        "error": None
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await _safe_get(
                client,
                f"https://api.greynoise.io/v3/community/{ip}",
                headers={"Accept": "application/json"}
            )
            if resp:
                data = resp.json()
                result["noise"] = data.get("noise", False)
                result["riot"] = data.get("riot", False)
                result["classification"] = data.get("classification", "unknown")
                result["name"] = data.get("name")
                result["message"] = data.get("message")
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"GreyNoise check failed for {ip}: {e}")
    return result


# ---------------------------------------------------------------------------
# 2. ThreatFox (abuse.ch) - Malware/C2 IOC Database (FREE)
# ---------------------------------------------------------------------------

async def check_threatfox(ioc: str, ioc_type: str = "url") -> Dict[str, Any]:
    """
    Check an IOC (IP, domain, URL, hash) against ThreatFox database.
    Completely free, no API key required.
    
    Args:
        ioc: The indicator to check (IP, domain, URL, or file hash)
        ioc_type: Type hint - 'url', 'domain', 'ip:port', 'md5_hash', 'sha1_hash', 'sha256_hash'
    """
    result = {"ioc": ioc, "found": False, "malware": None, "threat_type": None, "confidence": 0, "tags": []}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = json.dumps({"query": "search_ioc", "search_term": ioc})
            resp = await client.post(
                "https://threatfox-api.abuse.ch/api/v1/",
                content=payload,
                headers={"Content-Type": "application/json"},
                timeout=15.0
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("query_status") == "ok" and data.get("data"):
                    items = data["data"]
                    if items:
                        item = items[0]
                        result["found"] = True
                        result["malware"] = item.get("malware") or item.get("malware_printable")
                        result["threat_type"] = item.get("threat_type")
                        result["confidence"] = item.get("confidence_level", 0)
                        result["tags"] = item.get("tags") or []
    except Exception as e:
        logger.debug(f"ThreatFox check failed for {ioc}: {e}")
    return result


# ---------------------------------------------------------------------------
# 3. PhishTank - Phishing URL Check (FREE)
# ---------------------------------------------------------------------------

async def check_phishtank(url: str) -> Dict[str, Any]:
    """
    Check if a URL is in PhishTank's phishing database.
    Free, limited API - checks against known phishing database.
    """
    result = {"url": url, "in_database": False, "valid": False, "phish_id": None}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://checkurl.phishtank.com/checkurl/",
                data={"url": url, "format": "json"},
                headers={"User-Agent": "phishtank/aegisScout"},
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", {})
                result["in_database"] = results.get("in_database", False)
                result["valid"] = results.get("valid", False)
                result["phish_id"] = results.get("phish_id")
    except Exception as e:
        logger.debug(f"PhishTank check failed for {url}: {e}")
    return result


# ---------------------------------------------------------------------------
# 4. URLScan.io - Website Sandbox (FREE public scans)
# ---------------------------------------------------------------------------

async def search_urlscan(domain: str) -> Dict[str, Any]:
    """
    Search URLScan.io for existing public scan results of a domain.
    No API key required for reading public scans.
    Returns up to 3 most recent scan results.
    """
    result = {"domain": domain, "scans": [], "screenshot_url": None, "score": None, "error": None}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await _safe_get(
                client,
                f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=3",
                headers={"Content-Type": "application/json"}
            )
            if resp:
                data = resp.json()
                results = data.get("results", [])
                for r in results[:3]:
                    scan = {
                        "scan_id": r.get("_id"),
                        "url": r.get("page", {}).get("url"),
                        "screenshot": r.get("screenshot"),
                        "score": r.get("verdicts", {}).get("overall", {}).get("score"),
                        "malicious": r.get("verdicts", {}).get("overall", {}).get("malicious", False),
                        "tags": r.get("verdicts", {}).get("overall", {}).get("tags", []),
                        "timestamp": r.get("task", {}).get("time"),
                    }
                    result["scans"].append(scan)
                
                if result["scans"]:
                    result["screenshot_url"] = result["scans"][0].get("screenshot")
                    result["score"] = result["scans"][0].get("score")
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"URLScan search failed for {domain}: {e}")
    return result


# ---------------------------------------------------------------------------
# 5. AbuseIPDB (FREE tier: 1000/day, API key required but free to get)
# ---------------------------------------------------------------------------

async def check_abuseipdb(ip: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Check IP reputation via AbuseIPDB.
    Free tier: 1000 requests/day. API key required (free at abuseipdb.com).
    If no API key provided, returns empty result gracefully.
    """
    result = {"ip": ip, "abuse_confidence": 0, "total_reports": 0, "country": None, "isp": None, "is_public": True}
    if not api_key:
        result["error"] = "AbuseIPDB API key not configured"
        return result
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await _safe_get(
                client,
                "https://api.abuseipdb.com/api/v2/check",
                headers={"Accept": "application/json", "Key": api_key},
                params={"ipAddress": ip, "maxAgeInDays": 90}
            )
            if resp:
                data = resp.json().get("data", {})
                result["abuse_confidence"] = data.get("abuseConfidenceScore", 0)
                result["total_reports"] = data.get("totalReports", 0)
                result["country"] = data.get("countryCode")
                result["isp"] = data.get("isp")
                result["is_public"] = data.get("isPublic", True)
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"AbuseIPDB check failed for {ip}: {e}")
    return result


# ---------------------------------------------------------------------------
# 6. AlienVault OTX (FREE key required, free to register)
# ---------------------------------------------------------------------------

async def check_otx(indicator: str, indicator_type: str = "domain", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Check an indicator against AlienVault OTX threat intelligence.
    Free API key available at otx.alienvault.com.
    If no key provided, returns empty result gracefully.
    
    indicator_type: 'domain', 'IPv4', 'IPv6', 'URL', 'hostname'
    """
    result = {"indicator": indicator, "pulse_count": 0, "sections": [], "reputation": 0, "malware_families": []}
    if not api_key:
        result["error"] = "OTX API key not configured"
        return result
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await _safe_get(
                client,
                f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{indicator}/general",
                headers={"X-OTX-API-KEY": api_key}
            )
            if resp:
                data = resp.json()
                result["pulse_count"] = data.get("pulse_info", {}).get("count", 0)
                result["reputation"] = data.get("reputation", 0)
                result["sections"] = data.get("sections", [])
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"OTX check failed for {indicator}: {e}")
    return result


# ---------------------------------------------------------------------------
# 7. Full Threat Intelligence Report
# ---------------------------------------------------------------------------

async def get_threat_intel_report(
    domain: str,
    ip: Optional[str] = None,
    otx_key: Optional[str] = None,
    abuseipdb_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive threat intelligence gathering from all available free sources.
    
    Args:
        domain: Target domain name
        ip: Optional resolved IP address
        otx_key: Optional AlienVault OTX API key (free)
        abuseipdb_key: Optional AbuseIPDB API key (free)
    """
    import asyncio
    
    logger.info(f"Running threat intel for: {domain}")
    
    report: Dict[str, Any] = {
        "domain": domain,
        "ip": ip,
        "threatfox": {},
        "phishtank": {},
        "urlscan": {},
        "greynoise": {},
        "abuseipdb": {},
        "otx": {},
        "overall_risk": "clean",
        "risk_reasons": [],
        "summary": ""
    }
    
    tasks = [
        check_threatfox(domain, "domain"),
        search_urlscan(domain),
    ]
    if ip:
        tasks.extend([
            check_greynoise(ip),
            check_abuseipdb(ip, abuseipdb_key) if abuseipdb_key else asyncio.coroutine(lambda: {})(),
        ])
    if otx_key:
        tasks.append(check_otx(domain, "domain", otx_key))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    idx = 0
    report["threatfox"] = results[idx] if not isinstance(results[idx], Exception) else {}
    idx += 1
    report["urlscan"] = results[idx] if not isinstance(results[idx], Exception) else {}
    idx += 1
    if ip:
        report["greynoise"] = results[idx] if not isinstance(results[idx], Exception) else {}
        idx += 1
        if abuseipdb_key:
            report["abuseipdb"] = results[idx] if not isinstance(results[idx], Exception) else {}
            idx += 1
    if otx_key and idx < len(results):
        report["otx"] = results[idx] if not isinstance(results[idx], Exception) else {}
    
    # Calculate overall risk
    risk_reasons = []
    
    if report.get("threatfox", {}).get("found"):
        risk_reasons.append(f"ThreatFox: {report['threatfox'].get('malware', 'malware')} IOC")
    
    gn = report.get("greynoise", {})
    if gn.get("noise") and not gn.get("riot"):
        risk_reasons.append("GreyNoise: Kötü amaçlı tarayıcı/scanner")
    
    abuse = report.get("abuseipdb", {})
    if abuse.get("abuse_confidence", 0) > 50:
        risk_reasons.append(f"AbuseIPDB: {abuse['abuse_confidence']}% confidence")
    
    urlscan = report.get("urlscan", {})
    for scan in urlscan.get("scans", []):
        if scan.get("malicious"):
            risk_reasons.append("URLScan: Kötü amaçlı içerik tespit edildi")
            break
    
    if risk_reasons:
        report["overall_risk"] = "high" if len(risk_reasons) >= 2 else "medium"
    report["risk_reasons"] = risk_reasons
    
    # Build summary
    risk_emoji = {"clean": "✅", "medium": "⚠️", "high": "🚨"}
    emoji = risk_emoji.get(report["overall_risk"], "❓")
    summary_parts = [
        f"{emoji} TEHDİT İSTİHBARATI: {domain}",
        f"Genel Risk: {report['overall_risk'].upper()}"
    ]
    if risk_reasons:
        summary_parts.append("Risk Nedenleri:")
        for reason in risk_reasons:
            summary_parts.append(f"  • {reason}")
    else:
        summary_parts.append("🟢 Bilinen tehdit veri tabanlarında risk tespit edilmedi")
    
    report["summary"] = "\n".join(summary_parts)
    return report


__all__ = [
    "check_greynoise",
    "check_threatfox",
    "check_phishtank",
    "search_urlscan",
    "check_abuseipdb",
    "check_otx",
    "get_threat_intel_report",
]
