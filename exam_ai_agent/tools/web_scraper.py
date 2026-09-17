"""
Web scraping tool using BeautifulSoup, lxml, and Requests.
Scrapes pages in parallel threads with pooled connections and SSL fallback.
"""

import re
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict

import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class WebScraperTool:
    """
    Scrapes web pages and extracts clean text content.
    Uses thread-parallel fetching with HTTP connection pooling.
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
        adapter = HTTPAdapter(
            pool_connections=settings.SCRAPER_MAX_WORKERS * 2,
            pool_maxsize=settings.SCRAPER_MAX_WORKERS * 2,
            max_retries=1,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        })

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch raw HTML from a URL. Returns None on error."""
        if not url or not url.startswith(("http://", "https://")):
            return None
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
            content = resp.text
            if len(content) > self.max_content_length:
                content = content[: self.max_content_length]
            return content
        except requests.exceptions.SSLError:
            # Fallback for government sites with certificate chain issues
            try:
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True, verify=False)
                if resp.status_code < 400:
                    return resp.text[: self.max_content_length]
            except Exception:
                pass
            return None
        except requests.RequestException as e:
            logger.debug("Failed to fetch %s: %s", url[:60], e)
            return None

    def extract_text(self, html: str) -> str:
        """Extract clean readable text from HTML using lxml or html.parser."""
        if not html or not html.strip():
            return ""

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def scrape_page(self, url: str) -> Optional[Dict[str, str]]:
        """Fetch a URL and return {html, text} dict, or None on failure."""
        html = self.fetch_url(url)
        if html is None:
            return None
        return {"html": html, "text": self.extract_text(html)}

    def _scrape_one(self, url: str) -> Optional[Dict[str, str]]:
        """Worker used by the thread pool."""
        result = self.scrape_page(url)
        if result and result.get("text"):
            logger.debug("Scraped %s (%d chars)", url[:60], len(result["text"]))
            return {"url": url, "text": result["text"], "html": result["html"]}
        return None

    def scrape_urls(self, urls: List[str], max_pages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Scrape multiple URLs IN PARALLEL using thread pool.
        Returns list of {url, text, html} dicts for successful fetches in original order.
        """
        limit = max_pages or settings.MAX_SCRAPE_PAGES
        target = [u for u in urls if u and u.startswith(("http://", "https://"))][:limit]

        if not target:
            return []

        results = []
        max_workers = min(len(target), settings.SCRAPER_MAX_WORKERS)
        if max_workers < 1:
            return []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._scrape_one, url): url for url in target}
            for future in as_completed(futures, timeout=self.timeout * 3):
                try:
                    data = future.result(timeout=self.timeout + 2)
                    if data:
                        results.append(data)
                except Exception as e:
                    logger.debug("Scrape worker failed for %s: %s", futures.get(future, "url")[:60], e)

        url_order = {url: i for i, url in enumerate(target)}
        results.sort(key=lambda x: url_order.get(x["url"], 999))
        return results
