"""
Web Search Tool — DuckDuckGo powered, multi-bucket parallel search.
Targets authoritative educational sources for accurate, deduplicated results.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from dataclasses import dataclass

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Single search result with title, URL, and snippet."""
    title: str
    url: str
    snippet: str


class WebSearchTool:
    """
    DuckDuckGo search wrapper. Runs multi-bucket searches in parallel threads.
    """

    def __init__(self, max_results: Optional[int] = None):
        self.max_results = max_results or settings.MAX_SEARCH_RESULTS

    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform a single web search and return structured results."""
        limit = max_results or self.max_results
        results: List[SearchResult] = []

        try:
            from ddgs import DDGS
            ddgs = DDGS()
            raw = ddgs.text(
                query,
                max_results=limit,
                region="in-en",
                safesearch="moderate",
                timelimit=None,
            )
            for r in raw or []:
                results.append(SearchResult(
                    title=(r.get("title") or "").strip(),
                    url=(r.get("href") or r.get("link") or r.get("url") or "").strip(),
                    snippet=(r.get("body") or r.get("snippet") or "").strip(),
                ))

            logger.info("Search '%s' → %d results", query[:60], len(results))
        except Exception as e:
            logger.warning("Search failed for '%s': %s", query[:60], e)

        return results

    def _search_bucket(self, key: str, query_list: List[str], limit: int) -> tuple:
        """Run all queries for one bucket and return deduplicated results."""
        merged: List[SearchResult] = []
        seen_bases = set()

        for q in query_list:
            try:
                hits = self.search(q, max_results=limit)
                for r in hits:
                    if not r.url:
                        continue
                    base = r.url.split("?")[0].split("#")[0].rstrip("/")
                    # For YouTube, use the video ID as dedup key
                    if "youtube.com/watch" in r.url or "youtu.be" in r.url:
                        base = r.url.split("&")[0]
                    if base not in seen_bases:
                        seen_bases.add(base)
                        merged.append(r)
                time.sleep(0.4)
            except Exception as e:
                logger.warning("Bucket '%s' query '%s' failed: %s", key, q, e)

        return key, merged[:20]

    def search_exam_resources(self, exam_name: str) -> dict:
        """
        Run all search buckets IN PARALLEL for maximum speed.
        Returns grouped dict of results per category.
        """
        en = exam_name  # shorthand

        queries = {
            "exam_info": [
                f"{en} exam eligibility syllabus pattern details 2025",
                f"{en} official notification exam overview site:geeksforgeeks.org OR site:shiksha.com OR site:collegedunia.com",
            ],
            "syllabus": [
                f"{en} syllabus 2025 topics chapters site:geeksforgeeks.org",
                f"{en} complete syllabus subject-wise official",
                f"{en} syllabus PDF official website",
            ],
            "previous_papers": [
                f"{en} previous year question papers PDF download",
                f"{en} past PYQ papers free download",
                f"{en} solved papers last 5 years",
            ],
            "exam_pattern": [
                f"{en} exam pattern marks scheme sections",
            ],
            "study_resources": [
                f"{en} best books preparation guide recommended",
                f"{en} free study material notes PDF NPTEL Coursera",
            ],
            "youtube_lectures": [
                f"{en} complete preparation playlist site:youtube.com",
                f"{en} exam preparation lectures youtube 2025",
            ],
        }

        limits = {
            "exam_info": 5,
            "syllabus": 8,
            "previous_papers": 10,
            "exam_pattern": 5,
            "study_resources": 8,
            "youtube_lectures": 8,
        }

        output = {}

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._search_bucket, key, qlist, limits.get(key, 7)): key
                for key, qlist in queries.items()
            }
            for future in as_completed(futures):
                try:
                    key, results = future.result(timeout=60)
                    output[key] = results
                    logger.info("Bucket '%s' → %d results", key, len(results))
                except Exception as e:
                    key = futures[future]
                    logger.warning("Bucket '%s' future failed: %s", key, e)
                    output[key] = []

        return output
