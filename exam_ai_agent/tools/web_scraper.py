"""
Web scraping tool using BeautifulSoup and Requests.
Fetches page content and extracts text from HTML for analysis.
"""

import re
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
    Respects timeout and user-agent from settings.
    """

    def __init__(
        self,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        max_content_length: int = 100_000,
    ):
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.user_agent = user_agent or settings.USER_AGENT
        self.max_content_length = max_content_length
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch raw HTML from a URL.

        Args:
            url: Full URL to fetch

        Returns:
            HTML string or None on failure
        """
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            # Limit size to avoid huge pages
            content = resp.text
            if len(content) > self.max_content_length:
                content = content[: self.max_content_length]
            return content
        except requests.RequestException as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return None

    def extract_text(self, html: str, url: str = "") -> str:
        """
        Extract main text from HTML, strip scripts/styles, normalize whitespace.

        Args:
            html: Raw HTML string
            url: Optional base URL for resolving links

        Returns:
            Cleaned plain text
        """
        if not html or not html.strip():
            return ""

        soup = BeautifulSoup(html, "html.parser")

        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Normalize whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        # Collapse multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def scrape_page(self, url: str) -> Optional[dict]:
        """
        Fetch a URL and return extracted text content along with raw HTML.

        Args:
            url: Full URL to scrape

        Returns:
            Dict containing 'html' and 'text', or None if fetch failed
        """
        html = self.fetch_url(url)
        if html is None:
            return None
        return {"html": html, "text": self.extract_text(html, url)}

    def scrape_urls(self, urls: List[str], max_pages: Optional[int] = None) -> List[dict]:
        """
        Scrape multiple URLs and return list of {url, text} dicts.

        Args:
            urls: List of URLs to scrape
            max_pages: Max number of pages to scrape (default from settings)

        Returns:
            List of {"url": str, "text": str}
        """
        limit = max_pages or settings.MAX_SCRAPE_PAGES
        results = []
        for i, url in enumerate(urls):
            if i >= limit:
                break
            page_data = self.scrape_page(url)
            if page_data:
                results.append({"url": url, "text": page_data["text"], "html": page_data["html"]})
                logger.debug("Scraped %s (%d chars)", url, len(page_data["text"]))
        return results
