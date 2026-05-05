"""
Web Search Tool — DuckDuckGo primary + Google fallback.
6 specialised query generators targeting authoritative Indian exam sources.
Retry logic with exponential backoff, domain-level deduplication.
"""

import time
import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional


# ── Backward-compat dataclass (imported by search_agent.py) ──────────────────
@dataclass
class SearchResult:
    """Search result — attribute access shim over plain dict."""
    title: str
    url: str
    snippet: str
from urllib.parse import urlparse, urlencode, quote_plus

logger = logging.getLogger(__name__)

# ── Authoritative source domains ─────────────────────────────────────────────
_OFFICIAL_GOV = (
    "site:nic.in OR site:gov.in OR site:nta.ac.in OR site:ssc.nic.in "
    "OR site:upsc.gov.in OR site:bpsc.bih.nic.in OR site:mppsc.nic.in "
    "OR site:ukpsc.gov.in OR site:uppsc.up.nic.in"
)
_EXAM_INFO = (
    "site:careers360.com OR site:shiksha.com OR site:testbook.com "
    "OR site:adda247.com OR site:byjus.com OR site:gradeup.co"
)
_PYQ_SITES = (
    "site:testbook.com OR site:examrace.com OR site:careers360.com "
    "OR site:mrunal.org OR site:studyiq.com OR site:adda247.com"
)
_BOOK_SITES = (
    "site:amazon.in OR site:flipkart.com OR site:goodreads.com "
    "OR site:testbook.com OR site:careers360.com"
)
_STUDY_SITES = (
    "site:nptel.ac.in OR site:geeksforgeeks.org OR site:testbook.com "
    "OR site:adda247.com OR site:byjus.com OR site:unacademy.com"
)
_YT_CHANNELS = (
    "Unacademy OR \"Physics Wallah\" OR BYJU'S OR \"Let's Crack\" "
    "OR StudyIQ OR WiFiStudy OR \"Gate Smashers\" OR \"Khan Academy\""
)


# ── Result type ──────────────────────────────────────────────────────────────

def _make_result(title: str, url: str, snippet: str) -> Dict[str, str]:
    return {
        "title": (title or "").strip()[:300],
        "url": (url or "").strip(),
        "snippet": (snippet or "").strip()[:500],
    }


# ── 6 Specialised Query Generators ──────────────────────────────────────────

def get_syllabus_queries(exam_name: str) -> List[str]:
    """Target official .gov.in / exam-body sites for authoritative syllabus."""
    en = exam_name
    return [
        f"{en} official syllabus PDF {_OFFICIAL_GOV}",
        f"{en} complete syllabus subject-wise topics {_EXAM_INFO}",
        f"{en} detailed syllabus {_STUDY_SITES}",
        f"{en} syllabus PDF download filetype:pdf",
        f"{en} exam syllabus unit-wise chapter list",
    ]


def get_pyq_queries(exam_name: str) -> List[str]:
    """Find previous year question paper PDFs."""
    en = exam_name
    return [
        f"{en} previous year question papers PDF free download {_PYQ_SITES}",
        f"{en} PYQ solved papers last 5 years filetype:pdf",
        f"{en} question paper 2023 2022 2021 PDF official",
        f"{en} prelims mains previous year papers PDF {_OFFICIAL_GOV}",
        f"{en} solved question paper download free PDF",
    ]


def get_youtube_queries(exam_name: str) -> List[str]:
    """Find edu-channel playlists: Unacademy, Physics Wallah, BYJU's, Khan Academy."""
    en = exam_name
    return [
        f"{en} complete course playlist site:youtube.com {_YT_CHANNELS}",
        f"{en} preparation video lectures site:youtube.com",
        f"{en} subject-wise lectures playlist site:youtube.com",
        f"{en} free full course site:youtube.com",
    ]


def get_books_queries(exam_name: str) -> List[str]:
    """Find recommended books lists."""
    en = exam_name
    return [
        f"{en} best books for preparation recommended list {_BOOK_SITES}",
        f"{en} standard reference books toppers recommendation",
        f"{en} important books subject-wise {_EXAM_INFO}",
        f"{en} must-read books study material list",
    ]


def get_official_site_query(exam_name: str) -> List[str]:
    """Find official exam conducting body URL."""
    en = exam_name
    return [
        f"{en} official website exam conducting body",
        f"{en} official portal notification {_OFFICIAL_GOV}",
    ]


def get_topic_deep_dive_query(exam_name: str, topic: str) -> List[str]:
    """Deep-dive queries for a specific syllabus topic."""
    en = exam_name
    return [
        f"{en} {topic} detailed notes PDF {_STUDY_SITES}",
        f"{en} {topic} important questions previous year",
        f"{en} {topic} concept explained site:youtube.com",
    ]


# ── Core Search Functions ─────────────────────────────────────────────────────

def _ddg_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """DuckDuckGo search via ddgs library."""
    results = []
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        raw = ddgs.text(
            query,
            max_results=max_results,
            region="in-en",
            safesearch="moderate",
        )
        for r in raw or []:
            url = r.get("href") or r.get("link") or r.get("url") or ""
            results.append(_make_result(
                r.get("title", ""),
                url,
                r.get("body") or r.get("snippet") or "",
            ))
    except Exception as e:
        logger.debug("DDG search failed for '%s': %s", query[:60], e)
    return results


def _google_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Google search via googlesearch-python (free, no API key)."""
    results = []
    try:
        from googlesearch import search as gsearch
        urls = list(gsearch(query, num_results=max_results, lang="en", region="in"))
        for url in urls:
            results.append(_make_result(query[:80], url, ""))
    except ImportError:
        logger.debug("googlesearch-python not installed; skipping Google fallback.")
    except Exception as e:
        logger.debug("Google search failed for '%s': %s", query[:60], e)
    return results


def _search_with_retry(
    query: str,
    max_results: int = 10,
    retries: int = 3,
) -> List[Dict[str, str]]:
    """
    Try DDG first; fallback to Google if DDG returns nothing.
    Exponential backoff on failure.
    """
    delay = 1.0
    for attempt in range(retries):
        try:
            results = _ddg_search(query, max_results)
            if results:
                return results
            # DDG returned nothing — try Google
            logger.debug("DDG empty, trying Google for '%s'", query[:60])
            results = _google_search(query, max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(
                "Search attempt %d/%d failed for '%s': %s",
                attempt + 1, retries, query[:60], e,
            )
        if attempt < retries - 1:
            time.sleep(delay)
            delay *= 2  # exponential backoff

    return []


# ── Domain deduplication ──────────────────────────────────────────────────────

def _domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return url


def _deduplicate_by_domain(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep the first (best) result per base-domain+path combination."""
    seen_bases: set = set()
    deduped = []
    for r in results:
        url = r.get("url", "")
        if not url:
            continue
        # For YouTube, use video ID as the key
        if "youtube.com/watch" in url or "youtu.be/" in url:
            key = url.split("&")[0].rstrip("/")
        else:
            base = url.split("?")[0].split("#")[0].rstrip("/")
            key = base.lower()
        if key not in seen_bases:
            seen_bases.add(key)
            deduped.append(r)
    return deduped


# ── High-level bucket search ─────────────────────────────────────────────────

def search_bucket(
    queries: List[str],
    max_per_query: int = 8,
    delay_between: float = 2.0,
) -> List[Dict[str, str]]:
    """
    Run a list of queries sequentially, deduplicate by domain, and return results.
    Adds a configurable delay between queries to avoid rate limiting.
    """
    all_results: List[Dict[str, str]] = []
    for q in queries:
        hits = _search_with_retry(q, max_results=max_per_query)
        all_results.extend(hits)
        time.sleep(delay_between)

    return _deduplicate_by_domain(all_results)


def search_exam_resources(exam_name: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Run all resource-category searches for the given exam.
    Returns a dict keyed by category.
    """
    import datetime as _dt
    from concurrent.futures import ThreadPoolExecutor, as_completed

    year = _dt.datetime.now().year
    en = exam_name

    bucket_queries = {
        "syllabus": get_syllabus_queries(en),
        "previous_papers": get_pyq_queries(en),
        "youtube_lectures": get_youtube_queries(en),
        "study_resources": get_books_queries(en),
        "official_site": get_official_site_query(en),
        "exam_info": [
            f"{en} exam pattern marking scheme sections {year}",
            f"{en} eligibility exam overview {_EXAM_INFO}",
            f"{en} exam {year} full details {_OFFICIAL_GOV}",
        ],
    }

    output: Dict[str, List[Dict[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=len(bucket_queries)) as executor:
        futures = {
            executor.submit(search_bucket, queries): key
            for key, queries in bucket_queries.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                output[key] = future.result(timeout=90)
                logger.info("Bucket '%s' → %d results", key, len(output[key]))
            except Exception as e:
                logger.warning("Bucket '%s' failed: %s", key, e)
                output[key] = []

    return output


# ── Backward-compat shim (for existing code that imports WebSearchTool) ───────

class WebSearchTool:
    """Thin wrapper kept for backward compatibility with existing agents."""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        return _search_with_retry(query, max_results=max_results or self.max_results)

    def search_exam_resources(self, exam_name: str) -> Dict[str, List]:
        return search_exam_resources(exam_name)
