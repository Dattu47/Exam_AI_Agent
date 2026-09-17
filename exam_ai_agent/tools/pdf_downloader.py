"""
PDF discovery and link extraction tool.
Finds PDF links from search results and web pages for exam papers and resources.
"""

import re
import urllib3
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from exam_ai_agent.config import settings
from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class PDFDownloaderTool:
    """
    Discovers and validates PDF links from search results and page content.
    Does not download full PDF content unnecessarily; collects verified links.
    """

    PDF_EXTENSION = re.compile(r"\.pdf([?#]|$)", re.IGNORECASE)
    PDF_INDICATOR = re.compile(r"(\.pdf|/pdf/|format=pdf|filetype=pdf|export=download)", re.IGNORECASE)

    def __init__(self, scraper: Optional[WebScraperTool] = None):
        self.scraper = scraper or WebScraperTool()
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
        }

    def is_pdf_url(self, url: str) -> bool:
        """Return True if the URL points or redirects to a PDF document."""
        if not url or not url.startswith(("http://", "https://")):
            return False
        return bool(self.PDF_EXTENSION.search(url) or self.PDF_INDICATOR.search(url))

    def filter_pdf_links(self, urls: List[str]) -> List[str]:
        """Return only PDF-like URLs from a list, deduplicated."""
        seen = set()
        result = []
        for u in urls:
            if u and self.is_pdf_url(u) and u not in seen:
                seen.add(u)
                result.append(u)
        return result

    def _resolve_redirect(self, redirect_url: str) -> Optional[str]:
        """Check if a download/paper link redirects directly to a PDF."""
        try:
            res = requests.head(redirect_url, headers=self.headers, timeout=4, allow_redirects=True)
            ct = res.headers.get("Content-Type", "").lower()
            if "application/pdf" in ct or self.is_pdf_url(res.url):
                return res.url
        except Exception:
            pass
        return None

    def extract_pdf_links_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Parse HTML and return absolute PDF URLs.
        Concurrently checks candidate redirect links to discover hidden PDFs.
        """
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        links: List[str] = []
        possible_redirects: List[str] = []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(base_url, href)
            if not full.startswith(("http://", "https://")):
                continue

            link_text = a.get_text(strip=True).lower()
            href_lower = href.lower()

            if self.is_pdf_url(full):
                links.append(full)
            elif any(k in href_lower or k in link_text for k in ("download", "question paper", "solved paper", "pyq")):
                possible_redirects.append(full)

        # Resolve up to 4 candidate download links concurrently
        candidates = list(dict.fromkeys(possible_redirects))[:4]
        if candidates:
            with ThreadPoolExecutor(max_workers=min(len(candidates), 4)) as executor:
                futures = [executor.submit(self._resolve_redirect, url) for url in candidates]
                for f in as_completed(futures, timeout=6):
                    try:
                        resolved = f.result()
                        if resolved:
                            links.append(resolved)
                    except Exception:
                        pass

        # Deduplicate preserving order
        return list(dict.fromkeys(links))

    def get_pdf_links_from_search_results(self, search_results: List[Any]) -> List[Dict[str, str]]:
        """
        From search result items, extract verified PDF links and return
        [{title, url}] for PDF URLs only.
        """
        pdfs = []
        seen = set()

        for item in search_results:
            if isinstance(item, dict):
                url = item.get("url") or item.get("href") or item.get("link") or ""
                title = item.get("title") or item.get("snippet") or url
            else:
                url = getattr(item, "url", "") or getattr(item, "href", "") or getattr(item, "link", "")
                title = getattr(item, "title", "") or getattr(item, "snippet", "") or url

            if not url or not self.is_pdf_url(url) or url in seen:
                continue

            seen.add(url)
            clean_title = (title or "Question Paper PDF").strip()
            if len(clean_title) > 200:
                clean_title = clean_title[:200] + "..."

            pdfs.append({"title": clean_title, "url": url})

        return pdfs
