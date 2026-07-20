"""
Proxy Pool Manager for aegisScout.

Manages HTTP / SOCKS5 proxy rotation, health checks, latency measurement,
and anti-bot protection during web scraping and API requests.
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any, List, Optional
import httpx

from aegisScout.utils.logger import get_logger

logger = get_logger("utils.proxy_pool")


class ProxyPoolManager:
    """Singleton proxy pool for round-robin rotation and health checking."""

    _instance: Optional['ProxyPoolManager'] = None

    @classmethod
    def get_instance(cls) -> 'ProxyPoolManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.proxies: List[str] = []
        self._index: int = 0
        self.active_proxies: List[str] = []

    def set_proxies(self, proxy_list: List[str]) -> None:
        """Set or update the list of proxy URLs (e.g. http://user:pass@host:port)."""
        cleaned = [p.strip() for p in proxy_list if p and p.strip()]
        self.proxies = cleaned
        self.active_proxies = list(cleaned)
        self._index = 0
        logger.info(f"ProxyPool updated with {len(cleaned)} proxy addresses.")

    def get_next_proxy(self) -> Optional[str]:
        """Get the next healthy proxy in round-robin order."""
        if not self.active_proxies:
            if not self.proxies:
                return None
            self.active_proxies = list(self.proxies)

        proxy = self.active_proxies[self._index % len(self.active_proxies)]
        self._index += 1
        return proxy

    async def check_proxy_health(self, proxy_url: str, test_target: str = "https://api.ipify.org?format=json", timeout: float = 5.0) -> Dict[str, Any]:
        """Test a proxy connection for latency and working status."""
        try:
            start_time = asyncio.get_event_loop().time()
            async with httpx.AsyncClient(proxies=proxy_url, timeout=timeout) as client:
                resp = await client.get(test_target)
                latency_ms = round((asyncio.get_event_loop().time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return {
                        "proxy": proxy_url,
                        "healthy": True,
                        "status_code": resp.status_code,
                        "latency_ms": latency_ms,
                        "ip_response": resp.json().get("ip", "")
                    }
                return {"proxy": proxy_url, "healthy": False, "status_code": resp.status_code, "latency_ms": latency_ms}
        except Exception as e:
            return {"proxy": proxy_url, "healthy": False, "error": str(e)}

    async def refresh_active_pool(self) -> List[Dict[str, Any]]:
        """Health check all proxies in pool and keep only healthy ones in active_proxies."""
        results = []
        healthy_list = []
        for proxy in self.proxies:
            res = await self.check_proxy_health(proxy)
            results.append(res)
            if res.get("healthy"):
                healthy_list.append(proxy)

        self.active_proxies = healthy_list
        logger.info(f"ProxyPool health check completed: {len(healthy_list)}/{len(self.proxies)} healthy.")
        return results
