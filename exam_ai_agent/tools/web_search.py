"""
Web search tool using DuckDuckGo.
Uses parallel threads to run all search buckets concurrently for fast results.
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
    No API key required — uses ddgs library.
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

            # Retry once with a simpler query if empty
            if not results and ("official" in query.lower() or "pdf" in query.lower()):
                retry_query = query.replace("official", "").replace("PDF", "").strip()
                raw2 = ddgs.text(retry_query, max_results=limit, region="in-en", safesearch="moderate")
                for r in raw2 or []:
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
        for q in query_list:
            try:
                merged.extend(self.search(q, max_results=limit))
                time.sleep(0.3)   # small polite delay between queries in same bucket
            except Exception as e:
                logger.warning("Bucket '%s' query failed: %s", key, e)

        seen = set()
        deduped = []
        for r in merged:
            if not r.url:
                continue
            base_url = r.url.split("&")[0] if "youtube" in r.url else r.url
            if base_url in seen:
                continue
            seen.add(base_url)
            seen.add(r.url)
            deduped.append(r)

        return key, deduped[:20]

    def search_exam_resources(self, exam_name: str) -> dict:
        """
        Run all search buckets IN PARALLEL (via threads) for maximum speed.
        Returns grouped dict: syllabus, previous_papers, exam_pattern, study_resources, youtube_lectures.
        """
        # Trimmed to the most effective queries only — quality over quantity
        queries = {
            "exam_info": [
                f"{exam_name} exam 2025 details eligibility application deadline ",
                f"{exam_name} notification official website details",
            ],
            "syllabus": [
                f"{exam_name} official syllabus geeksforgeeks",
                f"{exam_name} full syllabus portal subject notes",
            ],
            "previous_papers": [
                f"{exam_name} previous year question papers pdf",
                f"{exam_name} past papers download",
            ],
            "exam_pattern": [
                f"{exam_name} exam pattern marking scheme",
            ],
            "study_resources": [
                f"{exam_name} best books preparation guide",
                f"{exam_name} free study material NPTEL Coursera",
            ],
            "youtube_lectures": [
                f"{exam_name} full course playlist youtube",
                f"{exam_name} preparation video lectures youtube",
            ],
        }

        limits = {
            "exam_info": 5,
            "syllabus": 8,
            "previous_papers": 8,
            "exam_pattern": 6,
            "study_resources": 7,
            "youtube_lectures": 5,
        }

        output = {}

        # Run all 6 buckets concurrently
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._search_bucket, key, qlist, limits.get(key, 7)): key
                for key, qlist in queries.items()
            }
            for future in as_completed(futures):
                try:
                    key, results = future.result(timeout=60)
                    output[key] = results
                    logger.info("Bucket '%s' completed with %d results", key, len(results))
                except Exception as e:
                    key = futures[future]
                    logger.warning("Bucket '%s' future failed: %s", key, e)
                    output[key] = []

        return output
