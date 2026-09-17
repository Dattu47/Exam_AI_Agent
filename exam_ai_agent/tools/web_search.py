"""
Web Search Tool — DuckDuckGo (ddgs) primary + Google fallback.
Multi-faceted, high-recall search query generation covering:
  - Official Information & Authority
  - Previous Year Question Papers (PYQs)
  - Preparation Guides & Subject-Specific Study Materials
  - Standard Recommended Reference Books
  - YouTube Video Courses & Playlists
Features automatic fallback query expansion to ensure high recall across all exams.
"""

import time
import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# ── Result factory ─────────────────────────────────────────────────────────────
def _make_result(title: str, url: str, snippet: str) -> Dict[str, str]:
    return {
        "title": (title or "").strip()[:300],
        "url": (url or "").strip(),
        "snippet": (snippet or "").strip()[:500],
    }


# ── High-Recall Query Generators ──────────────────────────────────────────────

def get_official_site_query(exam_name: str) -> List[str]:
    """Broad official authority discovery queries."""
    en = exam_name.strip()
    return [
        f"{en} official website portal",
        f"{en} official portal notification {CURRENT_YEAR}",
        f"{en} information bulletin {CURRENT_YEAR} PDF",
        f"{en} conducting authority site:gov.in OR site:nic.in OR site:ac.in",
    ]


def get_syllabus_queries(exam_name: str) -> List[str]:
    """Authoritative syllabus and exam scheme discovery queries."""
    en = exam_name.strip()
    return [
        f"{en} official syllabus PDF download",
        f"{en} information bulletin detailed syllabus PDF",
        f"{en} complete subject wise syllabus topics",
        f"{en} exam pattern marking scheme syllabus",
    ]


def get_pyq_queries(exam_name: str) -> List[str]:
    """Comprehensive previous year question papers queries."""
    en = exam_name.strip()
    return [
        f"{en} previous year question papers PDF download",
        f"{en} PYQ question papers solved with answer key",
        f"{en} solved question papers year wise PDF",
        f"{en} previous year question paper official",
        f"{en} question papers shift wise solved",
    ]


def get_preparation_queries(exam_name: str) -> List[str]:
    """Preparation guides, tutorials, notes, and subject-specific topics."""
    en = exam_name.strip()
    queries = [
        f"{en} complete preparation guide study material",
        f"{en} important topics subject wise notes",
        f"{en} practice questions question bank mock test",
        f"{en} topic wise tutorials notes",
    ]

    en_lower = en.lower()
    # Dynamic sub-topic expansion based on exam domain
    if any(k in en_lower for k in ("cse", "computer", "cs", "software")):
        queries.extend([
            f"{en} data structures algorithms notes",
            f"{en} operating systems dbms preparation",
            f"{en} computer networks theory of computation notes",
        ])
    elif any(k in en_lower for k in ("upsc", "ias", "civil services")):
        queries.extend([
            f"{en} polity governance modern history notes",
            f"{en} economy geography environment preparation",
            f"{en} csat analytical reasoning study material",
        ])
    elif any(k in en_lower for k in ("jee", "iit")):
        queries.extend([
            f"{en} physics chemistry mathematics formula sheets notes",
            f"{en} problem solving practice question bank",
        ])
    elif any(k in en_lower for k in ("ssc", "cgl", "chsl")):
        queries.extend([
            f"{en} quantitative aptitude reasoning notes",
            f"{en} general awareness english practice questions",
        ])

    return queries


def get_books_queries(exam_name: str) -> List[str]:
    """Recognized reference books and topper reading lists."""
    en = exam_name.strip()
    return [
        f"{en} best books for preparation toppers recommended list",
        f"{en} standard reference textbooks subject wise",
        f"{en} recommended books list study material",
        f"{en} topper booklist reference texts",
    ]


def get_youtube_queries(exam_name: str) -> List[str]:
    """Full lecture playlists and courses (excluding Shorts)."""
    en = exam_name.strip()
    return [
        f"{en} complete course playlist lectures -shorts",
        f"{en} subject wise playlist free course -shorts",
        f"{en} previous year questions solved revision -shorts",
        f"{en} full course marathon preparation lectures -shorts",
    ]


def get_topic_deep_dive_query(exam_name: str, topic: str) -> List[str]:
    """Deep-dive queries for a specific syllabus topic."""
    en = exam_name.strip()
    return [
        f"{en} {topic} detailed notes PDF",
        f"{en} {topic} previous year questions solved",
    ]


def generate_search_queries(exam_name: str, category: str = "official") -> List[str]:
    """Unified helper to generate queries across categories."""
    cat = (category or "").lower().strip()
    if cat in ("official", "authority"):
        return get_official_site_query(exam_name)
    elif cat in ("syllabus", "curriculum"):
        return get_syllabus_queries(exam_name)
    elif cat in ("pyq", "paper", "papers", "previous_papers"):
        return get_pyq_queries(exam_name)
    elif cat in ("study", "preparation", "materials", "edtech"):
        return get_preparation_queries(exam_name)
    elif cat in ("books", "textbooks"):
        return get_books_queries(exam_name)
    elif cat in ("youtube", "video", "videos"):
        return get_youtube_queries(exam_name)
    return get_official_site_query(exam_name)


# ── Core Search Engine Invocations ─────────────────────────────────────────────

def _ddg_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
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
        logger.debug("DDG search note for '%s': %s", query[:50], e)
    return results


def _google_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Google search fallback via googlesearch-python."""
    results = []
    try:
        from googlesearch import search as gsearch
        urls = list(gsearch(query, num_results=max_results, lang="en", region="in"))
        for url in urls:
            if url:
                results.append(_make_result(query[:80], url, ""))
    except Exception as e:
        logger.debug("Google search fallback note for '%s': %s", query[:50], e)
    return results


def _search_with_retry(
    query: str,
    max_results: int = 10,
    retries: int = 2,
) -> List[Dict[str, str]]:
    """Search with DDG first; fallback to Google. Retries on transient exceptions."""
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
                time.sleep(0.5 * (attempt + 1))

    return []


# ── Canonical Deduplication (By Path, NOT by Domain) ──────────────────────────

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
    """Deduplicate by canonical URL path, preserving distinct resource pages on the same domain."""
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


# ── High-Recall Bucket Search with Fallback Expansion ──────────────────────────

def search_bucket(
    queries: List[str],
    max_per_query: int = 8,
    delay_between: float = 0.2,
    exam_name: Optional[str] = None,
    resource_type: str = "general",
) -> List[Dict[str, str]]:
    """
    Executes multiple targeted queries, deduplicates by canonical URL,
    and applies fallback query expansion if candidate counts are low.
    """
    all_results: List[Dict[str, str]] = []
    for q in queries:
        hits = _search_with_retry(q, max_results=max_per_query)
        all_results.extend(hits)
        if delay_between > 0:
            time.sleep(delay_between)

    deduped = _deduplicate(all_results)

    # Fallback expansion: if results are very sparse, try broad fallback query
    if len(deduped) < 4 and exam_name:
        fallback_q = f"{exam_name} {resource_type} preparation study material"
        fallback_hits = _search_with_retry(fallback_q, max_results=8)
        all_results.extend(fallback_hits)
        deduped = _deduplicate(all_results)

    # Return full candidate list so agents have high recall to work with
    if exam_name:
        return filter_and_rank_resources(
            deduped,
            exam_name=exam_name,
            resource_type=resource_type,
            min_score=10.0,  # Generous threshold to avoid dropping valid educational content
            top_k=max(len(deduped), 20),
        )
    return deduped


def search_exam_resources(exam_name: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Run all resource-category searches for the given exam in parallel threads.
    Generates rich, multifaceted candidate pools ensuring high recall.
    """
    en = exam_name.strip()

    bucket_queries = {
        "syllabus": (get_syllabus_queries(en), "syllabus"),
        "previous_papers": (get_pyq_queries(en), "pyq"),
        "youtube_lectures": (get_youtube_queries(en), "video"),
        "study_resources": (get_preparation_queries(en), "resource"),
        "books": (get_books_queries(en), "book"),
        "official_site": (get_official_site_query(en), "authority"),
        "exam_info": (
            [
                f"{en} official exam pattern marking scheme",
                f"{en} eligibility overview {CURRENT_YEAR}",
            ],
            "authority",
        ),
    }

    output: Dict[str, List[Dict[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=len(bucket_queries)) as executor:
        futures = {
            executor.submit(search_bucket, queries, 8, 0.15, en, res_type): key
            for key, (queries, res_type) in bucket_queries.items()
        }
        for future in as_completed(futures, timeout=60):
            key = futures[future]
            try:
                output[key] = future.result(timeout=45)
                logger.info("Search bucket '%s' -> %d high-recall candidates", key, len(output[key]))
            except Exception as e:
                logger.warning("Search bucket '%s' notice: %s", key, e)
                output[key] = []

    # Map aliases for caller compatibility
    output["exam_pattern"] = output.get("exam_info", [])
    return output


# ── Backward-compat class wrapper ──────────────────────────────────────────────

class WebSearchTool:
    """Wrapper kept for backward compatibility with existing agent code."""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        return _search_with_retry(query, max_results=max_results or self.max_results)

    def search_exam_resources(self, exam_name: str) -> Dict[str, List[Dict[str, str]]]:
        return search_exam_resources(exam_name)
