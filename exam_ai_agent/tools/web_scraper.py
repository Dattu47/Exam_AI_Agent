"""
Web scraping tool using BeautifulSoup and Requests.
Scrapes pages in parallel threads to avoid sequential blocking waits.
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class WebScraperTool:
    """
    Scrapes web pages and extracts clean text content.
    Uses thread-parallel fetching to avoid sequential blocking.
    """

    def __init__(
        self,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        max_content_length: int = 80_000,
    ):
        # Use a shorter timeout (8s) — slow sites aren't worth waiting for
        self.timeout = timeout or min(settings.REQUEST_TIMEOUT, 8)
        self.user_agent = user_agent or settings.USER_AGENT
        self.max_content_length = max_content_length
        # Thread-safe: create a session per instance, headers set once
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch raw HTML from a URL. Returns None on any error."""
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
            content = resp.text
            if len(content) > self.max_content_length:
                content = content[: self.max_content_length]
            return content
        except requests.RequestException as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return None

    def extract_text(self, html: str, url: str = "") -> str:
        """Extract clean readable text from HTML."""
        if not html or not html.strip():
            return ""

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def scrape_page(self, url: str) -> Optional[dict]:
        """Fetch a URL and return extracted text + raw HTML dict."""
        html = self.fetch_url(url)
        if html is None:
            return None
        return {"html": html, "text": self.extract_text(html, url)}

    def _scrape_one(self, url: str) -> Optional[dict]:
        """Worker for parallel scraping."""
        result = self.scrape_page(url)
        if result:
            logger.debug("Scraped %s (%d chars)", url, len(result["text"]))
            return {"url": url, "text": result["text"], "html": result["html"]}
        return None

    def scrape_urls(self, urls: List[str], max_pages: Optional[int] = None) -> List[dict]:
        """
        Scrape multiple URLs IN PARALLEL (thread pool).
        Returns list of {url, text, html} dicts for successful fetches.
        """
        limit = max_pages or settings.MAX_SCRAPE_PAGES
        target = urls[:limit]

        results = []
        with ThreadPoolExecutor(max_workers=min(len(target), 6)) as executor:
            futures = {executor.submit(self._scrape_one, url): url for url in target}
            for future in as_completed(futures, timeout=30):
                try:
                    data = future.result(timeout=12)
                    if data:
                        results.append(data)
                except Exception as e:
                    logger.warning("Scrape future failed for %s: %s", futures[future], e)

        # Preserve original URL order for consistent processing
        url_order = {url: i for i, url in enumerate(target)}
        results.sort(key=lambda x: url_order.get(x["url"], 999))
        return results
