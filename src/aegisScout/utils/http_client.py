import random
import httpx
from typing import Optional
from aegisScout.core.config import settings
from aegisScout.utils.logger import get_logger

logger = get_logger("utils.http_client")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

def get_random_proxy() -> Optional[str]:
    """Parse settings.proxy_pool and return a random proxy url if available."""
    pool = settings.proxy_pool
    if not pool:
        return None
    proxies = [p.strip() for p in pool.split(",") if p.strip()]
    if not proxies:
        return None
    selected = random.choice(proxies)
    if not selected.startswith("http://") and not selected.startswith("https://") and not selected.startswith("socks5://"):
        # Default to http proxy
        selected = f"http://{selected}"
    return selected

def get_async_client(timeout: float = 15.0, verify: bool = True, follow_redirects: bool = True) -> httpx.AsyncClient:
    """
    Returns an httpx.AsyncClient with a random User-Agent and a random proxy from settings.proxy_pool if configured.
    Supports ScraperAPI, ZenRows, or Crawlbase integration as fallback or direct proxy.
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "tr,en-US;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1"
    }
    
    proxy_url = get_random_proxy()
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    
    # If the user has configured ZenRows/ScraperAPI, we can use their API endpoints
    # but to keep it simple, we construct a client.
    client_args = {
        "headers": headers,
        "timeout": timeout,
        "verify": verify,
        "follow_redirects": follow_redirects,
        "limits": limits
    }
    if proxy_url:
        logger.info(f"Using proxy: {proxy_url}")
        client_args["proxies"] = proxy_url
        
    return httpx.AsyncClient(**client_args)
