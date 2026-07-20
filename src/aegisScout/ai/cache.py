"""
AI Response Caching Module for aegisScout (A3).
Caches LLM completions by prompt hash to avoid duplicate API calls and reduce latency.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class AIResponseCache:
    """In-memory AI response cache with configurable TTL."""
    def __init__(self, ttl_hours: int = 24):
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, Tuple[str, datetime]] = {}

    def _hash(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        content = f"{system_prompt or ''}::{prompt}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        h = self._hash(prompt, system_prompt)
        if h in self._cache:
            response, cached_at = self._cache[h]
            if datetime.now() - cached_at < self.ttl:
                return response
            else:
                del self._cache[h]
        return None

    def set(self, prompt: str, response: str, system_prompt: Optional[str] = None) -> None:
        h = self._hash(prompt, system_prompt)
        self._cache[h] = (response, datetime.now())

    def clear(self) -> None:
        self._cache.clear()
