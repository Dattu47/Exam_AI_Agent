"""
Scraping Agent — multi-strategy page scraper:
  - BeautifulSoup4 + requests (fast primary for standard HTML)
  - Crawl4AI (optional for complex JS-rendered pages)
  - pdfplumber (PDF text + table extraction with size limits)
  - yt-dlp (YouTube metadata extraction)

Parallelized URL fetching and accurate HTML-based PDF discovery.
"""

import os
import re
import time
import tempfile
import urllib3
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)

_REQUEST_HEADERS = {
    "User-Agent": settings.USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

_PDF_KEYWORDS = re.compile(
    r"\b(syllabus|paper|question|pattern|exam|previous|year|pyq|mock|model|download|solved)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Page Scraper: Fast BS4 first -> Crawl4AI JS fallback
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_html(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch raw HTML string using requests with SSL error tolerance."""
    from exam_ai_agent.utils.trust_scoring import get_domain_tier
    tier, _, _ = get_domain_tier(url)
    if tier == 4:
        logger.debug("Skipping scrape of Tier-4 spam domain: %s", url[:60])
        return None

    try:
        resp = requests.get(url, headers=_REQUEST_HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return resp.text
    except requests.exceptions.SSLError:
        try:
            resp = requests.get(url, headers=_REQUEST_HEADERS, timeout=timeout, verify=False, allow_redirects=True)
            if resp.status_code < 400:
                return resp.text
        except Exception:
            pass
    except Exception as e:
        logger.debug("Fetch failed for %s: %s", url[:60], e)
    return None


def _clean_html_to_text(html: str) -> str:
    """Extract clean readable text from HTML."""
    if not html or not html.strip():
        return ""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
        tag.decompose()

    lines = []
    for elem in soup.find_all(["h1", "h2", "h3", "h4", "li", "p", "td", "th"]):
        txt = re.sub(r"\s+", " ", elem.get_text(separator=" ", strip=True))
        if len(txt) > 12:
            lines.append(txt)

    return "\n".join(lines).strip()


def scrape_url(url: str) -> str:
    """
    Scrape a URL and return clean text.
    Uses fast requests first; falls back to Crawl4AI if JS rendering is detected.
    """
    if not url or not url.startswith(("http://", "https://")):
        return ""

    html = _fetch_html(url)
    if html:
        text = _clean_html_to_text(html)
        if len(text) > 250:
            return text

    # If text is sparse (likely JS app like React/Angular), try Crawl4AI
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        import asyncio

        async def _run_crawl():
            config = CrawlerRunConfig(
                word_count_threshold=10,
                exclude_external_links=True,
                remove_overlay_elements=True,
            )
            async with AsyncWebCrawler() as crawler:
                res = await crawler.arun(url=url, config=config)
                return res.markdown or res.cleaned_html or ""

        loop = asyncio.new_event_loop()
        text = loop.run_until_complete(_run_crawl())
        loop.close()
        if text:
            return text
    except Exception as e:
        logger.debug("Crawl4AI fallback skipped for %s: %s", url[:60], e)

    return ""


# ─────────────────────────────────────────────────────────────────────────────
# 2. PDF Link Discovery from HTML (Fixed critical bug)
# ─────────────────────────────────────────────────────────────────────────────

def find_pdf_links(html_content: str, base_url: str) -> List[str]:
    """
    Find all .pdf and keyword-matching download links directly in HTML content.
    Returns deduplicated list of PDF/document URLs.
    """
    if not html_content:
        return []

    found: List[str] = []
    seen: set = set()

    try:
        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception:
            soup = BeautifulSoup(html_content, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            absolute = urljoin(base_url, href)
            if not absolute.startswith(("http://", "https://")) or absolute in seen:
                continue

            link_text = a.get_text(strip=True)
            is_pdf = absolute.lower().endswith(".pdf") or "filetype=pdf" in absolute.lower() or "/pdf/" in absolute.lower()
            parsed_path = urlparse(absolute).path
            has_keyword = bool(_PDF_KEYWORDS.search(parsed_path) or _PDF_KEYWORDS.search(link_text))

            if is_pdf or has_keyword:
                seen.add(absolute)
                found.append(absolute)

    except Exception as e:
        logger.debug("[find_pdf_links] Parse error for %s: %s", base_url[:60], e)

    # Sort direct PDFs first
    pdfs_first = [u for u in found if u.lower().endswith(".pdf")]
    others = [u for u in found if not u.lower().endswith(".pdf")]
    return (pdfs_first + others)[:20]


# ─────────────────────────────────────────────────────────────────────────────
# 3. PDF Text Extraction (with size limit)
# ─────────────────────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_url: str, max_bytes: int = 25_000_000) -> str:
    """
    Download a PDF to a temp file and extract text using pdfplumber.
    Safely enforces max_bytes download limit to avoid freezing on massive files.
    """
    if not pdf_url:
        return ""

    tmp_path: Optional[str] = None
    try:
        logger.info("[extract_pdf_text] Downloading PDF: %s", pdf_url[:60])
        resp = requests.get(pdf_url, headers=_REQUEST_HEADERS, timeout=20, stream=True)
        resp.raise_for_status()

        total_bytes = 0
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            for chunk in resp.iter_content(chunk_size=8192):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    logger.warning("[extract_pdf_text] PDF exceeds size limit (%d bytes), truncating", max_bytes)
                    break
                tmp.write(chunk)
            tmp_path = tmp.name

        import pdfplumber

        text_parts = []
        with pdfplumber.open(tmp_path) as pdf:
            # Process up to first 25 pages to avoid memory/time bottlenecks
            for page in pdf.pages[:25]:
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                if page_text.strip():
                    text_parts.append(page_text)
                for table in page.extract_tables():
                    for row in table:
                        row_text = " | ".join((cell or "").strip() for cell in row if cell)
                        if row_text.strip():
                            text_parts.append(row_text)

        full_text = "\n\n".join(text_parts)
        logger.info("[extract_pdf_text] Extracted %d chars from %s", len(full_text), pdf_url[:60])
        return full_text

    except Exception as e:
        logger.debug("[extract_pdf_text] Failed for %s: %s", pdf_url[:60], e)
        return ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# 4. YouTube Metadata
# ─────────────────────────────────────────────────────────────────────────────

def scrape_youtube_metadata(youtube_url: str) -> Dict[str, str]:
    """Extract YouTube video title, channel name, and duration using yt-dlp."""
    result = {"title": "", "channel": "", "url": youtube_url, "duration": ""}
    if not youtube_url:
        return result
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "extract_flat": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            if info:
                result["title"] = info.get("title") or ""
                result["channel"] = info.get("uploader") or info.get("channel") or ""
                result["url"] = info.get("webpage_url") or youtube_url
                dur = info.get("duration")
                if dur:
                    mins, secs = divmod(int(dur), 60)
                    result["duration"] = f"{mins}m {secs}s"
    except Exception as e:
        logger.debug("[scrape_youtube_metadata] yt-dlp error for %s: %s", youtube_url[:60], e)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 5. ScrapingAgent Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class ScrapingAgent:
    """Orchestrates concurrent multi-URL scraping and PDF extraction."""

    @staticmethod
    def _is_pdf_url(url: str) -> bool:
        return url.lower().endswith(".pdf") or "filetype=pdf" in url.lower()

    def _scrape_and_discover_pdfs(self, url: str) -> Tuple[Optional[Dict[str, str]], List[Dict[str, str]]]:
        """Fetch page, discover hidden PDFs from raw HTML, and clean text."""
        html = _fetch_html(url)
        if not html:
            return None, []

        pdf_links = find_pdf_links(html, url)
        domain = urlparse(url).netloc.replace("www.", "")
        hidden_pdfs = [
            {
                "title": f"Document from {domain}",
                "url": pdf_url,
                "type": "pdf",
            }
            for pdf_url in pdf_links[:5]
        ]

        text = _clean_html_to_text(html)
        scraped_doc = {"url": url, "text": text, "html": html} if text else None
        return scraped_doc, hidden_pdfs

    def scrape_sources(
        self, target_urls: List[str], max_pages: int = 6
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Scrapes a list of URLs concurrently.
        Returns (scraped_data: list[dict], hidden_pdfs: list[dict]).
        """
        unique_urls = list(dict.fromkeys(
            u for u in target_urls if u and not self._is_pdf_url(u)
        ))[:max_pages]

        if not unique_urls:
            return [], []

        logger.info("[ScrapingAgent] Scraping %d URLs concurrently", len(unique_urls))
        scraped_data: List[Dict] = []
        hidden_pdfs: List[Dict] = []

        with ThreadPoolExecutor(max_workers=min(len(unique_urls), 6)) as executor:
            future_to_url = {
                executor.submit(self._scrape_and_discover_pdfs, url): url
                for url in unique_urls
            }
            for future in as_completed(future_to_url, timeout=25):
                try:
                    scraped_doc, pdfs = future.result(timeout=15)
                    if scraped_doc:
                        scraped_data.append(scraped_doc)
                    hidden_pdfs.extend(pdfs)
                except Exception as e:
                    logger.debug("Scrape failed for %s: %s", future_to_url[future][:60], e)

        # Deduplicate hidden PDFs by URL
        seen_pdf = set()
        dedup_pdfs = []
        for p in hidden_pdfs:
            u = p.get("url", "")
            if u and u not in seen_pdf:
                seen_pdf.add(u)
                dedup_pdfs.append(p)

        logger.info("[ScrapingAgent] Scraped %d pages, found %d PDF links", len(scraped_data), len(dedup_pdfs))
        return scraped_data, dedup_pdfs
