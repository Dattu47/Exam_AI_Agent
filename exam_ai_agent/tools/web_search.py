"""
Web Search Tool — DuckDuckGo (ddgs) primary + Google fallback.
Targeted query generators focused on Tier-1 (.gov/.nic/.ac) and Tier-2 educational platforms.
Integrated relevance scoring, canonical deduplication, and early spam filtering.
"""

import time
import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger
from exam_ai_agent.utils.trust_scoring import filter_and_rank_resources

logger = get_logger(__name__)

CURRENT_YEAR = datetime.datetime.now().year


# ── Backward-compat dataclass ────────────────────────────────────────────────
@dataclass
class SearchResult:
    """Search result — attribute access shim over plain dict."""
    title: str
    url: str
    snippet: str

    def get(self, key: str, default=None):
        return getattr(self, key, default)


# ── Authoritative source domain filters ────────────────────────────────────────
_OFFICIAL_GOV = (
    "site:gov.in OR site:nic.in OR site:ac.in OR site:edu.in OR site:nta.ac.in OR site:upsc.gov.in"
)
_EXAM_INFO = (
    "site:careers360.com OR site:shiksha.com OR site:testbook.com OR site:nptel.ac.in"
)
_PYQ_SITES = (
    "site:testbook.com OR site:careers360.com OR site:gateoverflow.in OR site:adda247.com"
)
_YT_CHANNELS = (
    "Unacademy OR \"Physics Wallah\" OR BYJU'S OR \"Gate Smashers\" OR \"Neso Academy\" "
    "OR StudyIQ OR \"Khan Academy\""
)


# ── Result factory ─────────────────────────────────────────────────────────────
def _make_result(title: str, url: str, snippet: str) -> Dict[str, str]:
    return {
        "title": (title or "").strip()[:300],
        "url": (url or "").strip(),
        "snippet": (snippet or "").strip()[:500],
    }


# ── Hyper-Targeted Query Generators ───────────────────────────────────────────

def get_official_site_query(exam_name: str) -> List[str]:
    """Find official exam conducting body portal and notifications."""
    en = exam_name.strip()
    return [
        f"{en} official website portal {_OFFICIAL_GOV}",
        f"{en} official portal notification {CURRENT_YEAR}",
        f"{en} information bulletin bulletin {_OFFICIAL_GOV}",
    ]


def get_syllabus_queries(exam_name: str) -> List[str]:
    """Target official .gov.in / .nic.in / .ac.in sites for authentic syllabus."""
    en = exam_name.strip()
    return [
        f"{en} official syllabus PDF download {_OFFICIAL_GOV}",
        f"{en} information bulletin detailed syllabus PDF",
        f"{en} complete subject wise syllabus topics {_EXAM_INFO}",
    ]


def get_pyq_queries(exam_name: str) -> List[str]:
    """Find authentic previous year question paper PDFs."""
    en = exam_name.strip()
    return [
        f"{en} official previous year question paper PDF {_OFFICIAL_GOV}",
        f"{en} PYQ solved question papers PDF {CURRENT_YEAR-1} {CURRENT_YEAR-2}",
        f"{en} previous year question papers solved {_PYQ_SITES}",
    ]


def get_youtube_queries(exam_name: str) -> List[str]:
    """Find structured lecture playlists from top creators (exclude Shorts)."""
    en = exam_name.strip()
    return [
        f"{en} complete course playlist site:youtube.com ({_YT_CHANNELS}) -shorts",
        f"{en} full preparation lectures playlist site:youtube.com -shorts",
        f"{en} topic wise lectures complete course site:youtube.com",
    ]


def get_books_queries(exam_name: str) -> List[str]:
    """Find recognized reference books and topper lists."""
    en = exam_name.strip()
    return [
        f"{en} standard reference books list toppers recommendation",
        f"{en} best books for preparation {_EXAM_INFO}",
        f"{en} NCERT reference study material list",
    ]


def get_topic_deep_dive_query(exam_name: str, topic: str) -> List[str]:
    """Deep-dive queries for a specific syllabus topic."""
    en = exam_name.strip()
    return [
        f"{en} {topic} detailed notes PDF site:nptel.ac.in OR site:geeksforgeeks.org",
        f"{en} {topic} previous year questions solved",
    ]


# ── Core Search Functions ──────────────────────────────────────────────────────

def _ddg_search(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    """DuckDuckGo search via ddgs or duckduckgo_search library."""
    results = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        ddgs = DDGS()
        raw = ddgs.text(
            query,
            max_results=max_results,
            region="in-en",
            safesearch="moderate",
        )
        for r in raw or []:
            url = r.get("href") or r.get("link") or r.get("url") or ""
            if url:
                results.append(_make_result(
                    r.get("title", ""),
                    url,
                    r.get("body") or r.get("snippet") or "",
                ))
    except Exception as e:
        logger.debug("DDG search notice for '%s': %s", query[:50], e)
    return results


def _google_search(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    """Google search fallback via googlesearch-python."""
    results = []
    try:
        from googlesearch import search as gsearch
        urls = list(gsearch(query, num_results=max_results, lang="en", region="in"))
        for url in urls:
            if url:
                results.append(_make_result(query[:80], url, ""))
    except Exception as e:
        logger.debug("Google search fallback notice for '%s': %s", query[:50], e)
    return results


def _search_with_retry(
    query: str,
    max_results: int = 8,
    retries: int = 2,
) -> List[Dict[str, str]]:
    """Search with DuckDuckGo first; fallback to Google. Retries only on exceptions."""
    for attempt in range(retries):
        try:
            results = _ddg_search(query, max_results=max_results)
            if results:
                return results

            google_results = _google_search(query, max_results=max_results)
            if google_results:
                return google_results

            return []
        except Exception as e:
            logger.debug("Search attempt %d failed for '%s': %s", attempt + 1, query[:50], e)
            if attempt < retries - 1:
                time.sleep(0.8 * (attempt + 1))

    return []


# ── URL-level deduplication & canonical normalization ─────────────────────────

def _normalize_url(url: str) -> str:
    """Normalize URL, removing tracking params and canonicalizing YouTube links."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower().replace("www.", "")

        # Canonicalize YouTube links to standard watch URL
        if netloc in ("youtu.be", "m.youtube.com", "youtube.com"):
            if netloc == "youtu.be":
                video_id = parsed.path.lstrip("/").split("/")[0].split("?")[0]
                if video_id:
                    return f"https://youtube.com/watch?v={video_id}"
            elif parsed.path == "/watch":
                qs = parse_qs(parsed.query)
                vid = qs.get("v", [None])[0]
                if vid:
                    return f"https://youtube.com/watch?v={vid}"

        # Strip standard marketing tracking parameters
        clean_query = []
        if parsed.query:
            qs = parse_qs(parsed.query, keep_blank_values=False)
            filtered = {
                k: v for k, v in qs.items()
                if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref", "source"))
            }
            clean_query = urlencode(filtered, doseq=True)

        return urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            parsed.path.rstrip("/"),
            "",
            clean_query,
            "",
        ))
    except Exception:
        return url.split("?")[0].split("#")[0].rstrip("/").lower()


def _deduplicate(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep the highest ranked result per canonical normalized URL."""
    seen: set = set()
    deduped = []
    for r in results:
        url = r.get("url", "")
        if not url:
            continue
        canon = _normalize_url(url)
        if canon not in seen:
            seen.add(canon)
            deduped.append(r)
    return deduped


# ── High-level bucket search with early relevance ranking ─────────────────────

def search_bucket(
    queries: List[str],
    max_per_query: int = 6,
    delay_between: float = 0.3,
    exam_name: Optional[str] = None,
    resource_type: str = "general",
) -> List[Dict[str, str]]:
    """
    Run targeted queries, deduplicate by canonical URL, and apply early trust filtering.
    """
    all_results: List[Dict[str, str]] = []
    for q in queries:
        hits = _search_with_retry(q, max_results=max_per_query)
        all_results.extend(hits)
        if delay_between > 0:
            time.sleep(delay_between)

    deduped = _deduplicate(all_results)

    # Early relevance ranking if exam_name is provided
    if exam_name:
        return filter_and_rank_resources(
            deduped,
            exam_name=exam_name,
            resource_type=resource_type,
            min_score=20.0,
            top_k=max_per_query * 2,
        )
    return deduped


def search_exam_resources(exam_name: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Run all resource-category searches for the given exam in parallel threads.
    Applies early trust tiering and deterministic relevance ranking.
    """
    en = exam_name.strip()

    bucket_queries = {
        "syllabus": (get_syllabus_queries(en), "syllabus"),
        "previous_papers": (get_pyq_queries(en), "pyq"),
        "youtube_lectures": (get_youtube_queries(en), "video"),
        "study_resources": (get_books_queries(en), "book"),
        "official_site": (get_official_site_query(en), "authority"),
        "exam_info": (
            [
                f"{en} official exam pattern marking scheme {_OFFICIAL_GOV}",
                f"{en} eligibility overview {CURRENT_YEAR} {_EXAM_INFO}",
            ],
            "authority",
        ),
    }

    output: Dict[str, List[Dict[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=len(bucket_queries)) as executor:
        futures = {
            executor.submit(search_bucket, queries, 6, 0.2, en, res_type): key
            for key, (queries, res_type) in bucket_queries.items()
        }
        for future in as_completed(futures, timeout=50):
            key = futures[future]
            try:
                output[key] = future.result(timeout=40)
                logger.info("Search bucket '%s' -> %d quality results", key, len(output[key]))
            except Exception as e:
                logger.warning("Search bucket '%s' completed with fallback: %s", key, e)
                output[key] = []

    # Map aliases for caller compatibility
    output["exam_pattern"] = output.get("exam_info", [])
    return output


# ── Backward-compat class wrapper ──────────────────────────────────────────────

class WebSearchTool:
    """Wrapper kept for backward compatibility with existing agent code."""

    def __init__(self, max_results: int = 8):
        self.max_results = max_results

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        return _search_with_retry(query, max_results=max_results or self.max_results)

    def search_exam_resources(self, exam_name: str) -> Dict[str, List[Dict[str, str]]]:
        return search_exam_resources(exam_name)
