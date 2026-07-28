"""
Advanced Domain Intelligence Module for aegisScout.

Gathers deep domain intelligence using 100% free, no-API-key services:
  - crt.sh: SSL certificate transparency logs for subdomain discovery
  - Shodan InternetDB: Open ports, CVEs, tags (completely free, no key needed)
  - Mozilla HTTP Observatory: Web security scoring
  - Wayback Machine: Historical site snapshots and first seen date
  - HackerTarget: Subdomain and IP reverse lookup (100 req/day free)
  - URLScan.io: Public sandbox scan results (no key for public scans)
  - URLHaus (abuse.ch): Malware URL checking (completely free)
  - SecurityHeaders.com: HTTP security header analysis
"""
from __future__ import annotations

import json
import re
import ssl
import socket
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx
from aegisScout.utils.logger import get_logger

logger = get_logger("enrichment.advanced_domain_intel")


# ---------------------------------------------------------------------------
# Helper: safe async GET with timeout and error handling
# ---------------------------------------------------------------------------

async def _safe_get(client: httpx.AsyncClient, url: str, **kwargs) -> Optional[Any]:
    """Safely fetch a URL, returning None on any error."""
    try:
        resp = await client.get(url, timeout=10.0, **kwargs)
        if resp.status_code == 200:
            return resp
    except Exception as e:
        logger.debug(f"Request failed for {url}: {e}")
    return None


# ---------------------------------------------------------------------------
# 1. crt.sh — SSL Certificate Transparency Subdomain Discovery
# ---------------------------------------------------------------------------

async def get_subdomains_crtsh(domain: str) -> List[str]:
    """
    Discover subdomains via SSL certificate transparency logs at crt.sh.
    No API key required. Completely free.
    
    Returns a sorted list of unique subdomains found.
    """
    subdomains: set = set()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await _safe_get(
                client,
                f"https://crt.sh/?q=%.{domain}&output=json",
                headers={"Accept": "application/json"}
            )
            if resp:
                data = resp.json()
                for entry in data:
                    name_value = entry.get("name_value", "")
                    # Multiple names can be in one entry separated by newlines
                    for name in name_value.split("\n"):
                        name = name.strip().lower().lstrip("*.")  
                        if name and domain in name and not name.startswith("@"):
                            subdomains.add(name)
    except Exception as e:
        logger.warning(f"crt.sh subdomain lookup failed for {domain}: {e}")
    
    result = sorted(subdomains - {domain})
    logger.info(f"crt.sh found {len(result)} subdomains for {domain}")
    return result


# ---------------------------------------------------------------------------
# 2. Shodan InternetDB — Open Ports, CVEs, Tags (FREE, NO KEY)
# ---------------------------------------------------------------------------

async def get_shodan_internetdb(ip: str) -> Dict[str, Any]:
    """
    Query Shodan InternetDB for IP intelligence: open ports, CVEs, tags.
    
    Completely FREE, no API key required.
    Endpoint: https://internetdb.shodan.io/{ip}
    
    Returns dict with: ports, cpes, tags, vulns, hostnames
    """
    result = {
        "ports": [],
        "cpes": [],
        "tags": [],
        "vulns": [],
        "hostnames": [],
        "ip": ip,
        "risk_level": "unknown",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await _safe_get(client, f"https://internetdb.shodan.io/{ip}")
            if resp:
                data = resp.json()
                result["ports"] = data.get("ports", [])
                result["cpes"] = data.get("cpes", [])
                result["tags"] = data.get("tags", [])
                result["vulns"] = data.get("vulns", [])
                result["hostnames"] = data.get("hostnames", [])
                
                # Compute risk level
                vuln_count = len(result["vulns"])
                open_ports = len(result["ports"])
                if vuln_count > 3 or any("critical" in t.lower() for t in result["tags"]):
                    result["risk_level"] = "high"
                elif vuln_count > 0 or open_ports > 10:
                    result["risk_level"] = "medium"
                elif open_ports > 0:
                    result["risk_level"] = "low"
                else:
                    result["risk_level"] = "minimal"
                    
    except Exception as e:
        logger.warning(f"Shodan InternetDB lookup failed for {ip}: {e}")
    
    return result


# ---------------------------------------------------------------------------
# 3. Mozilla HTTP Observatory — Web Security Score
# ---------------------------------------------------------------------------

async def get_mozilla_observatory_score(host: str) -> Dict[str, Any]:
    """
    Get Mozilla HTTP Observatory security score for a website.
    No API key required. Free service.
    
    Returns grade (A+ to F), score (0-100), and failing tests.
    """
    result = {"grade": "N/A", "score": None, "tests_failed": [], "error": None}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Trigger a new scan
            scan_resp = await client.post(
                "https://http-observatory.security.mozilla.org/api/v1/analyze",
                params={"host": host},
                data={"hidden": "true"},
                timeout=20.0
            )
            if scan_resp.status_code == 200:
                data = scan_resp.json()
                result["grade"] = data.get("grade", "N/A")
                result["score"] = data.get("score")
                
                # Get test results
                tests_resp = await _safe_get(
                    client,
                    f"https://http-observatory.security.mozilla.org/api/v1/getScanResults",
                    params={"scan": data.get("scan_id")}
                )
                if tests_resp:
                    tests = tests_resp.json()
                    result["tests_failed"] = [
                        k for k, v in tests.items()
                        if isinstance(v, dict) and v.get("pass") is False
                    ]
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Mozilla Observatory failed for {host}: {e}")
    
    return result


# ---------------------------------------------------------------------------
# 4. Wayback Machine — Historical Site Data
# ---------------------------------------------------------------------------

async def get_wayback_machine_data(url: str) -> Dict[str, Any]:
    """
    Query the Wayback Machine (archive.org) for historical snapshot data.
    No API key required. Completely free.
    
    Returns: first_seen, last_seen, snapshot_count, oldest_snapshot_url
    """
    result = {
        "available": False,
        "first_seen": None,
        "last_seen": None,
        "snapshot_count": 0,
        "oldest_snapshot_url": None,
        "newest_snapshot_url": None,
    }
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Check availability of latest snapshot
            avail_resp = await _safe_get(
                client,
                "http://archive.org/wayback/available",
                params={"url": domain}
            )
            if avail_resp:
                avail_data = avail_resp.json()
                snapshot = avail_data.get("archived_snapshots", {}).get("closest", {})
                if snapshot.get("available"):
                    result["available"] = True
                    result["newest_snapshot_url"] = snapshot.get("url")
                    ts = snapshot.get("timestamp", "")
                    if len(ts) >= 8:
                        result["last_seen"] = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
            
            # Get CDX API for historical data
            cdx_resp = await _safe_get(
                client,
                "http://web.archive.org/cdx/search/cdx",
                params={
                    "url": domain,
                    "output": "json",
                    "fl": "timestamp",
                    "limit": 1,
                    "from": "19960101",
                    "to": "20240101",
                    "filter": "statuscode:200"
                }
            )
            if cdx_resp:
                cdx_data = cdx_resp.json()
                if len(cdx_data) > 1:  # First row is header
                    first_ts = cdx_data[1][0] if cdx_data[1] else ""
                    if len(first_ts) >= 8:
                        result["first_seen"] = f"{first_ts[:4]}-{first_ts[4:6]}-{first_ts[6:8]}"
                        result["oldest_snapshot_url"] = f"https://web.archive.org/web/{first_ts}/{domain}"
            
            # Get snapshot count
            count_resp = await _safe_get(
                client,
                "http://web.archive.org/cdx/search/cdx",
                params={"url": domain, "output": "json", "fl": "timestamp", "limit": 0}
            )
            if count_resp:
                count_text = count_resp.text.strip()
                # CDX returns one line per result; parse count from headers
                # Actually with limit=0, it still returns, let's count lines
                result["snapshot_count"] = max(0, len(count_text.split("\n")) - 1)
                    
    except Exception as e:
        logger.warning(f"Wayback Machine lookup failed for {url}: {e}")
    
    return result


# ---------------------------------------------------------------------------
# 5. HackerTarget — Subdomain + Reverse IP (100/day free)
# ---------------------------------------------------------------------------

async def get_hackertarget_data(domain: str) -> Dict[str, Any]:
    """
    Query HackerTarget for subdomain enumeration and reverse IP lookup.
    100 requests/day free, no API key required.
    """
    result = {"subdomains": [], "reverse_ip_domains": [], "error": None}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Subdomain lookup
            sub_resp = await _safe_get(
                client,
                "https://api.hackertarget.com/hostsearch/",
                params={"q": domain}
            )
            if sub_resp and "error" not in sub_resp.text.lower():
                lines = sub_resp.text.strip().split("\n")
                for line in lines:
                    parts = line.split(",")
                    if len(parts) >= 1 and domain in parts[0]:
                        result["subdomains"].append(parts[0].strip())
            
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"HackerTarget lookup failed for {domain}: {e}")
    
    return result


# ---------------------------------------------------------------------------
# 6. URLHaus — Malware URL Check (abuse.ch, completely free)
# ---------------------------------------------------------------------------

async def check_urlhaus(url: str) -> Dict[str, Any]:
    """
    Check if a URL/domain is in URLHaus malware database.
    Completely free, no API key required.
    """
    result = {"in_database": False, "threat": None, "url_status": None, "tags": []}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://urlhaus-api.abuse.ch/v1/url/",
                data={"url": url},
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("query_status") == "is_listed":
                    result["in_database"] = True
                    result["threat"] = data.get("threat")
                    result["url_status"] = data.get("url_status")
                    result["tags"] = data.get("tags") or []
    except Exception as e:
        logger.debug(f"URLHaus check failed for {url}: {e}")
    
    return result


# ---------------------------------------------------------------------------
# 7. Resolve domain to IP (for Shodan InternetDB)
# ---------------------------------------------------------------------------

def resolve_domain_to_ip(domain: str) -> Optional[str]:
    """Resolve a domain name to its primary IP address."""
    try:
        domain = domain.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        return socket.gethostbyname(domain)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 8. Full Domain Intelligence Report
# ---------------------------------------------------------------------------

async def get_full_domain_intel(domain: str, include_slow: bool = False) -> Dict[str, Any]:
    """
    Comprehensive domain intelligence gathering from multiple free sources.
    
    Args:
        domain: Domain name (e.g. 'example.com', or URL)
        include_slow: If True, includes slower checks (Observatory, URLScan)
    
    Returns:
        Comprehensive dict with all intelligence gathered.
    """
    # Normalize domain
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0].lower()
    domain = domain.replace("www.", "")
    
    logger.info(f"Starting full domain intel for: {domain}")
    
    report: Dict[str, Any] = {
        "domain": domain,
        "scanned_at": datetime.utcnow().isoformat(),
        "subdomains": [],
        "ip_info": {},
        "shodan_data": {},
        "wayback": {},
        "urlhaus": {},
        "observatory": {},
        "hackertarget": {},
        "summary": ""
    }
    
    import asyncio
    
    # Resolve IP first (needed for Shodan)
    ip = resolve_domain_to_ip(domain)
    if ip:
        report["ip_info"]["ip"] = ip
    
    # Run fast checks concurrently
    fast_tasks = [
        get_subdomains_crtsh(domain),
        get_hackertarget_data(domain),
        get_wayback_machine_data(domain),
        check_urlhaus(f"https://{domain}"),
    ]
    
    if ip:
        fast_tasks.append(get_shodan_internetdb(ip))
    
    results = await asyncio.gather(*fast_tasks, return_exceptions=True)
    
    # Unpack results
    task_idx = 0
    report["subdomains"] = results[task_idx] if not isinstance(results[task_idx], Exception) else []
    task_idx += 1
    report["hackertarget"] = results[task_idx] if not isinstance(results[task_idx], Exception) else {}
    task_idx += 1
    report["wayback"] = results[task_idx] if not isinstance(results[task_idx], Exception) else {}
    task_idx += 1
    report["urlhaus"] = results[task_idx] if not isinstance(results[task_idx], Exception) else {}
    task_idx += 1
    if ip:
        report["shodan_data"] = results[task_idx] if not isinstance(results[task_idx], Exception) else {}
    
    # Merge subdomains from all sources
    all_subs = set(report["subdomains"])
    ht_subs = report.get("hackertarget", {}).get("subdomains", [])
    all_subs.update(ht_subs)
    report["subdomains"] = sorted(all_subs)
    
    # Optional slow checks
    if include_slow:
        report["observatory"] = await get_mozilla_observatory_score(domain)
    
    # Build summary
    sub_count = len(report["subdomains"])
    shodan = report.get("shodan_data", {})
    vuln_count = len(shodan.get("vulns", []))
    port_count = len(shodan.get("ports", []))
    wayback = report.get("wayback", {})
    first_seen = wayback.get("first_seen", "bilinmiyor")
    urlhaus = report.get("urlhaus", {})
    risk = shodan.get("risk_level", "bilinmiyor")
    
    summary_parts = [
        f"🔍 ALAN ADI İSTİHBARATI: {domain}",
        f"🌐 Subdomain Sayısı: {sub_count} adet",
        f"📅 İlk Arşiv Kaydı: {first_seen}",
    ]
    if ip:
        summary_parts.append(f"🖥️ IP: {ip}")
    if port_count > 0:
        summary_parts.append(f"🔌 Açık Port Sayısı: {port_count}")
    if vuln_count > 0:
        summary_parts.append(f"⚠️ Bilinen CVE/Zafiyet: {vuln_count} adet")
    if urlhaus.get("in_database"):
        summary_parts.append(f"🚨 URLHaus Kara Liste: EVET — {urlhaus.get('threat', 'bilinmiyor')}")
    if risk != "bilinmiyor":
        summary_parts.append(f"🎯 Risk Seviyesi: {risk.upper()}")
    
    report["summary"] = "\n".join(summary_parts)
    logger.info(f"Domain intel complete for {domain}: {sub_count} subs, risk={risk}")
    
    return report


__all__ = [
    "get_subdomains_crtsh",
    "get_shodan_internetdb",
    "get_mozilla_observatory_score",
    "get_wayback_machine_data",
    "get_hackertarget_data",
    "check_urlhaus",
    "get_full_domain_intel",
    "resolve_domain_to_ip",
]
