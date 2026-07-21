"""
Jina Reader AI & DuckDuckGo Instant Answer Provider (Zero-Config / Keyless).
Provides keyless instant Markdown extraction from websites (via r.jina.ai) and entity descriptions (via DuckDuckGo API).
"""

from typing import Dict, Any, Optional
import urllib.parse
import httpx
from aegisScout.utils.logger import get_logger, log_execution_time

logger = get_logger("ai.jina_reader")

_JINA_READER_ENDPOINT = "https://r.jina.ai/"
_DUCKDUCKGO_API_ENDPOINT = "https://api.duckduckgo.com/"
_TIMEOUT = 12.0


class JinaReaderAI:
    """
    Zero-config web content reader converting any URL to clean Markdown for LLM analysis without headless browser overhead.
    """

    @staticmethod
    async def read_url_markdown(url: str) -> Optional[str]:
        """Convert webpage content directly into LLM-ready clean Markdown via Jina Reader."""
        if not url:
            return None

        clean_url = url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url

        target_url = f"{_JINA_READER_ENDPOINT}{clean_url}"
        logger.info(f"Reading webpage via Jina Reader AI for '{clean_url}'...")

        headers = {
            "Accept": "text/event-stream, text/markdown, text/plain",
            "User-Agent": "aegisScout/2.0 OSINT Engine",
        }

        with log_execution_time(logger, f"Jina Reader Markdown Fetch ({clean_url})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                    resp = await client.get(target_url, headers=headers)
                    if resp.status_code == 200:
                        text = resp.text
                        logger.info(f"Successfully retrieved {len(text)} characters of Markdown from '{clean_url}'")
                        return text
                    else:
                        logger.warning(f"Jina Reader returned status {resp.status_code} for {clean_url}")
            except Exception as e:
                logger.error(f"Jina Reader fetch failed for {clean_url}: {e}")

        return None


class DuckDuckGoInstantAnswer:
    """
    Zero-config background entity and business description lookup.
    """

    @staticmethod
    async def get_instant_answer(query: str) -> Dict[str, Any]:
        """Query DuckDuckGo Instant Answer API for background abstract and Wikipedia summaries."""
        if not query or not query.strip():
            return {}

        clean_q = query.strip()
        logger.info(f"Querying DuckDuckGo Instant Answer for '{clean_q}'...")

        params = {
            "q": clean_q,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }

        with log_execution_time(logger, f"DuckDuckGo Instant Answer ({clean_q})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_DUCKDUCKGO_API_ENDPOINT, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        abstract = data.get("AbstractText") or data.get("Heading", "")
                        source = data.get("AbstractSource", "DuckDuckGo")
                        url = data.get("AbstractURL", "")

                        return {
                            "query": clean_q,
                            "abstract": abstract,
                            "source": source,
                            "url": url,
                        }
            except Exception as e:
                logger.warning(f"DuckDuckGo Instant Answer query failed for '{clean_q}': {e}")

        return {}
