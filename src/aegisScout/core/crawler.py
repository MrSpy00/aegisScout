"""
Crawler utilities and Playwright browser lifecycle manager for aegisScout.
Provides Windows-safe event loop execution and SSRF-aware web fetching.
"""
import asyncio
import sys
from typing import Optional, Dict, Any
from aegisScout.utils.security import is_safe_url
from aegisScout.utils.logger import get_logger

logger = get_logger("core.crawler")

class PlaywrightCrawler:
    """Windows-safe Playwright browser instance launcher & manager."""

    def __init__(self, headless: bool = True, timeout_ms: int = 15000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def fetch_page_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Safely fetch web page title, HTML content, and metadata."""
        if not is_safe_url(url):
            logger.warning(f"Crawling blocked for unsafe URL: {url}")
            return None

        # Fix Proactor / Selector loop policies on Windows background threads
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()
                page = await context.new_page()
                
                response = await page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                status = response.status if response else 0
                title = await page.title()
                content = await page.content()
                
                await context.close()
                await browser.close()
                return {
                    "url": url,
                    "status": status,
                    "title": title,
                    "content_length": len(content),
                }
        except Exception as e:
            logger.error(f"Playwright crawling failed for {url}: {e}")
            return None
