"""
PDF discovery and link extraction tool.
Finds PDF links from search results and web pages for exam papers and resources.
"""

import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class PDFDownloaderTool:
    """
    Discovers and validates PDF links from search results and page content.
    Does not store or parse PDF content; only collects links for the user.
    """

    # Common patterns for PDF URLs
    PDF_EXTENSION = re.compile(r"\.pdf(\?|$)", re.IGNORECASE)
    PDF_IN_PATH = re.compile(r"/[^/]*\.pdf", re.IGNORECASE)

    def __init__(self, scraper: Optional[WebScraperTool] = None):
        self.scraper = scraper or WebScraperTool()

    def is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF."""
        if not url or not url.startswith(("http://", "https://")):
            return False
        return bool(self.PDF_EXTENSION.search(url) or self.PDF_IN_PATH.search(url))

    def filter_pdf_links(self, urls: List[str]) -> List[str]:
        """
        From a list of URLs, return only those that look like PDFs.

        Args:
            urls: List of URLs (e.g., from search results)

        Returns:
            Filtered list of PDF-like URLs
        """
        return list({u for u in urls if self.is_pdf_url(u)})

    def extract_pdf_links_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Extract all PDF links from an HTML string.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute PDF URLs
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if self.PDF_EXTENSION.search(href) or "pdf" in href.lower():
                full = urljoin(base_url, href)
                if full.startswith(("http://", "https://")):
                    links.append(full)
        return list(dict.fromkeys(links))

    def get_pdf_links_from_search_results(self, search_results: List[dict]) -> List[dict]:
        """
        From search result items (with 'url' and optionally 'title'), extract PDF links
        and return list of {title, url} for PDFs only.

        Args:
            search_results: List of dicts with keys like title, url, snippet
                           (e.g., from WebSearchTool - use .__dict__ or same shape)

        Returns:
            List of {"title": str, "url": str} for PDF links
        """
        pdfs = []
        for item in search_results:
            # Support both dict and object with attributes (e.g. SearchResult)
            if hasattr(item, "url"):
                url = getattr(item, "url", "") or getattr(item, "href", "") or getattr(item, "link", "")
                title = getattr(item, "title", "") or getattr(item, "snippet", "") or url
            else:
                url = item.get("url") or item.get("href") or item.get("link") or ""
                title = item.get("title") or item.get("snippet") or url
            if not url:
                continue
            if self.is_pdf_url(url):
                if isinstance(title, str) and len(title) > 200:
                    title = title[:200] + "..."
                pdfs.append({"title": title, "url": url})
        return pdfs
