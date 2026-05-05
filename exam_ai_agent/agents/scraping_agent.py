"""
Scraping Agent — upgraded to use:
  - Crawl4AI (primary, handles JavaScript-rendered pages)
  - BeautifulSoup4 (fallback for simple HTML)
  - pdfplumber (replaces PyPDF2 — preserves tables and formatted text)
  - yt-dlp (YouTube metadata — title, channel, duration)
2-second delay between requests to avoid rate limiting.
"""

import os
import re
import time
import tempfile
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}
_DELAY = 2.0  # seconds between requests


# ─────────────────────────────────────────────────────────────────────────────
# 1. scrape_url — Crawl4AI primary → BeautifulSoup fallback
# ─────────────────────────────────────────────────────────────────────────────

def scrape_url(url: str) -> str:
    """
    Scrape a URL and return clean text/markdown.
    Tries Crawl4AI first (handles JS-rendered pages);
    falls back to BeautifulSoup for plain HTML.
    """
    if not url or not url.startswith(("http://", "https://")):
        return ""

    # ── Attempt 1: Crawl4AI ──────────────────────────────────────────────────
    try:
        result = _crawl4ai_scrape(url)
        if result and len(result.strip()) > 200:
            logger.info("[scrape_url] Crawl4AI success: %s (%d chars)", url[:80], len(result))
            time.sleep(_DELAY)
            return result
    except Exception as e:
        logger.debug("[scrape_url] Crawl4AI failed for %s: %s", url[:80], e)

    # ── Attempt 2: BeautifulSoup fallback ────────────────────────────────────
    try:
        result = _bs4_scrape(url)
        logger.info("[scrape_url] BS4 fallback: %s (%d chars)", url[:80], len(result))
        time.sleep(_DELAY)
        return result
    except Exception as e:
        logger.warning("[scrape_url] BS4 also failed for %s: %s", url[:80], e)

    time.sleep(_DELAY)
    return ""


def _crawl4ai_scrape(url: str) -> str:
    """Use Crawl4AI AsyncWebCrawler to fetch and return Markdown content."""
    import asyncio

    async def _run():
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        config = CrawlerRunConfig(
            word_count_threshold=10,
            exclude_external_links=True,
            remove_overlay_elements=True,
        )
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            if result.success:
                return result.markdown or result.cleaned_html or ""
            return ""

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        text = loop.run_until_complete(_run())
        loop.close()
        return text or ""
    except Exception as e:
        raise RuntimeError(f"Crawl4AI error: {e}") from e


def _bs4_scrape(url: str) -> str:
    """BeautifulSoup scraper for simple HTML pages."""
    from bs4 import BeautifulSoup

    resp = requests.get(url, headers=_REQUEST_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    # Remove navigation, ads, footers
    for tag in soup.find_all(["nav", "footer", "header", "aside", "script", "style"]):
        tag.decompose()

    # Extract meaningful text
    lines = []
    for elem in soup.find_all(["h1", "h2", "h3", "h4", "li", "p", "td", "th"]):
        txt = elem.get_text(separator=" ", strip=True)
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) > 10:
            lines.append(txt)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 2. extract_pdf_text — pdfplumber with table extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_url: str) -> str:
    """
    Download a PDF to a temp file and extract all text using pdfplumber.
    Detects and extracts tables too.
    Returns clean text string.
    """
    if not pdf_url:
        return ""

    tmp_path = None
    try:
        logger.info("[extract_pdf_text] Downloading PDF: %s", pdf_url[:80])
        resp = requests.get(pdf_url, headers=_REQUEST_HEADERS, timeout=30, stream=True)
        resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            for chunk in resp.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name

        import pdfplumber

        text_parts = []
        with pdfplumber.open(tmp_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract raw text
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                if page_text.strip():
                    text_parts.append(page_text)

                # Extract tables and represent as text
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        row_text = " | ".join(
                            (cell or "").strip() for cell in row if cell
                        )
                        if row_text.strip():
                            text_parts.append(row_text)

        full_text = "\n\n".join(text_parts)
        logger.info(
            "[extract_pdf_text] Extracted %d chars from %s",
            len(full_text), pdf_url[:80],
        )
        return full_text

    except Exception as e:
        logger.warning("[extract_pdf_text] Failed for %s: %s", pdf_url[:80], e)
        return ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        time.sleep(_DELAY)


# ─────────────────────────────────────────────────────────────────────────────
# 3. find_pdf_links — find PDFs in HTML, 1-level deep
# ─────────────────────────────────────────────────────────────────────────────

_PDF_KEYWORDS = re.compile(
    r"(syllabus|paper|question|pattern|exam|previous|year|pyq|mock|model)",
    re.IGNORECASE,
)


def find_pdf_links(html_content: str, base_url: str) -> List[str]:
    """
    Find all .pdf links and keyword-matching links in HTML.
    Recurse one level deep to discover hidden PDFs.
    Returns a deduplicated list of PDF URLs.
    """
    from bs4 import BeautifulSoup

    found: List[str] = []
    seen: set = set()

    def _collect_from_html(html: str, base: str, depth: int):
        try:
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                absolute = urljoin(base, href)
                if absolute in seen:
                    continue
                is_pdf = absolute.lower().endswith(".pdf") or "filetype=pdf" in absolute.lower()
                has_keyword = _PDF_KEYWORDS.search(href) or _PDF_KEYWORDS.search(
                    a.get_text(strip=True)
                )
                if is_pdf or has_keyword:
                    seen.add(absolute)
                    found.append(absolute)
                    # Recurse one level into keyword pages (non-PDF)
                    if not is_pdf and depth < 1:
                        try:
                            resp = requests.get(
                                absolute, headers=_REQUEST_HEADERS, timeout=12
                            )
                            if resp.status_code == 200:
                                _collect_from_html(resp.text, absolute, depth + 1)
                            time.sleep(_DELAY)
                        except Exception:
                            pass
        except Exception as e:
            logger.debug("[find_pdf_links] Parse error: %s", e)

    _collect_from_html(html_content, base_url, depth=0)
    # Prioritise actual .pdf links
    pdfs_first = [u for u in found if u.lower().endswith(".pdf")]
    others = [u for u in found if not u.lower().endswith(".pdf")]
    return (pdfs_first + others)[:30]


# ─────────────────────────────────────────────────────────────────────────────
# 4. scrape_youtube_metadata — yt-dlp
# ─────────────────────────────────────────────────────────────────────────────

def scrape_youtube_metadata(youtube_url: str) -> Dict[str, str]:
    """
    Use yt-dlp to extract video title, channel name, and duration.
    Returns {"title": "", "channel": "", "url": "", "duration": ""}
    Does NOT download the video.
    """
    result = {"title": "", "channel": "", "url": youtube_url, "duration": ""}
    if not youtube_url:
        return result
    try:
        import yt_dlp  # type: ignore

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
        logger.info("[scrape_youtube_metadata] Got metadata for %s", youtube_url[:60])
    except ImportError:
        logger.debug("[scrape_youtube_metadata] yt-dlp not installed.")
    except Exception as e:
        logger.warning("[scrape_youtube_metadata] Failed for %s: %s", youtube_url[:60], e)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compatible class wrapper
# ─────────────────────────────────────────────────────────────────────────────

class ScrapingAgent:
    """
    Orchestrates multi-URL scraping.
    Wraps the module-level functions for use by the research pipeline.
    """

    def scrape_sources(
        self, target_urls: List[str], max_pages: int = 8
    ):
        """
        Scrapes a list of URLs.
        Returns (scraped_data: list[dict], hidden_pdfs: list[dict])
        """
        logger.info("[ScrapingAgent] Scraping %d URLs (max %d)", len(target_urls), max_pages)
        unique_urls = list(dict.fromkeys(
            u for u in target_urls if u and not self._is_pdf_url(u)
        ))[:max_pages]

        scraped_data: List[Dict] = []
        hidden_pdfs: List[Dict] = []

        for url in unique_urls:
            text = scrape_url(url)
            if text:
                scraped_data.append({"url": url, "text": text, "html": text})
                domain = urlparse(url).netloc.replace("www.", "")
                pdfs = find_pdf_links(text, url)
                for pdf_url in pdfs[:5]:
                    hidden_pdfs.append({
                        "title": f"Document from {domain}",
                        "url": pdf_url,
                        "type": "pdf",
                    })

        logger.info(
            "[ScrapingAgent] Scraped %d pages, found %d PDF links",
            len(scraped_data), len(hidden_pdfs),
        )
        return scraped_data, hidden_pdfs

    @staticmethod
    def _is_pdf_url(url: str) -> bool:
        return url.lower().endswith(".pdf") or "filetype=pdf" in url.lower()
