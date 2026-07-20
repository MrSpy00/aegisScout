"""
Security utilities for aegisScout.
Includes SSRF (Server-Side Request Forgery) protection and URL validation.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from aegisScout.utils.logger import get_logger

logger = get_logger("utils.security")

FORBIDDEN_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_safe_url(url: str) -> bool:
    """
    Validate URL to ensure it does not target local/private IP ranges or loopback (SSRF protection).
    """
    if not url:
        return False
    
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False

        # Reject direct localhost names
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            logger.warning(f"SSRF blocked: local hostname attempt '{hostname}'")
            return False

        # Resolve IP addresses for the hostname
        ip_addresses = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in ip_addresses:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved:
                logger.warning(f"SSRF blocked: '{url}' resolved to private/reserved IP {ip_str}")
                return False

            for network in FORBIDDEN_NETWORKS:
                if ip_obj in network:
                    logger.warning(f"SSRF blocked: '{url}' IP {ip_str} in forbidden network {network}")
                    return False

        return True
    except Exception as e:
        logger.debug(f"SSRF check failed/blocked for '{url}': {e}")
        return False
