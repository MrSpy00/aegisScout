"""
Persistent HTTP connection pool and enrichment engine for aegisScout.
Optimizes WHOIS, social discovery, and website auditing latency via shared httpx.AsyncClient.
"""
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from aegisScout.utils.security import is_safe_url
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.enrichers")

class SharedEnrichmentPool:
    """Shared HTTP client pool with connection recycling and concurrency control."""

    def __init__(self, max_connections: int = 20, max_keepalive_connections: int = 10, timeout_sec: float = 8.0):
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=30.0,
        )
        self._timeout = httpx.Timeout(timeout_sec)
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> httpx.AsyncClient:
        """Retrieve or initialize shared AsyncClient session."""
        if self._client is None or self._client.is_closed:
            async with self._lock:
                if self._client is None or self._client.is_closed:
                    self._client = httpx.AsyncClient(
                        limits=self._limits,
                        timeout=self._timeout,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AegisScout/4.0"
                        },
                        follow_redirects=True,
                    )
        return self._client

    async def close(self) -> None:
        """Close shared HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_head_status(self, url: str) -> Optional[int]:
        """Fast HEAD/GET check for site availability using pool."""
        if not is_safe_url(url):
            return None
        try:
            client = await self.get_client()
            response = await client.head(url)
            return response.status_code
        except Exception:
            try:
                client = await self.get_client()
                response = await client.get(url)
                return response.status_code
            except Exception as e:
                logger.debug(f"Fetch status failed for {url}: {e}")
                return None

# Singleton instance
enrichment_pool = SharedEnrichmentPool()
