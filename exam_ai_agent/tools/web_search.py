"""
Web search tool using DuckDuckGo.
Searches the internet for exam-related queries without API keys.
"""

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
    DuckDuckGo search wrapper for finding exam resources.
    No API key required - uses ddgs library.
    """

    def __init__(self, max_results: Optional[int] = None):
        self.max_results = max_results or settings.MAX_SEARCH_RESULTS

    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform a web search and return structured results.

        Args:
            query: Search query string (e.g., "GATE CSE syllabus 2024")
            max_results: Override default max results per query

        Returns:
            List of SearchResult objects (title, url, snippet)
        """
        limit = max_results or self.max_results
        results: List[SearchResult] = []

        try:
            # `duckduckgo-search` is deprecated/renamed; `ddgs` is the maintained package.
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
                results.append(
                    SearchResult(
                        title=(r.get("title") or "").strip(),
                        url=(r.get("href") or r.get("link") or r.get("url") or "").strip(),
                        snippet=(r.get("body") or r.get("snippet") or "").strip(),
                    )
                )

            # Some environments intermittently return 0 results; retry once with a simpler query.
            if not results and ("official" in query.lower() or "pdf" in query.lower()):
                retry_query = query.replace("official", "").replace("PDF", "").strip()
                raw2 = ddgs.text(retry_query, max_results=limit, region="in-en", safesearch="moderate")
                for r in raw2 or []:
                    results.append(
                        SearchResult(
                            title=(r.get("title") or "").strip(),
                            url=(r.get("href") or r.get("link") or r.get("url") or "").strip(),
                            snippet=(r.get("body") or r.get("snippet") or "").strip(),
                        )
                    )

            logger.info("Search completed: query=%s, results=%d", query, len(results))
        except Exception as e:
            logger.exception("Web search failed for query=%s: %s", query, e)
            raise

        return results

    def search_exam_resources(self, exam_name: str) -> dict:
        """
        Run multiple targeted searches for an exam and return grouped results.

        Args:
            exam_name: Name of the exam (e.g., "GATE CSE", "JEE Main")

        Returns:
            Dict with keys: syllabus, previous_papers, exam_pattern, study_resources
        """
        # Multiple query variants per bucket improves recall.
        queries = {
            "syllabus": [
                f"{exam_name} syllabus official",
                f"{exam_name} syllabus pdf",
                f"{exam_name} subject-wise syllabus",
                f"{exam_name} syllabus pdf site:.ac.in",
                f"{exam_name} syllabus pdf site:gate2025.iitr.ac.in OR site:gate2024.iisc.ac.in OR site:gate.iitk.ac.in",
            ],
            "previous_papers": [
                f"{exam_name} previous year question papers pdf",
                f"{exam_name} question paper pdf filetype:pdf",
                f"{exam_name} previous year papers site:.ac.in pdf",
            ],
            "exam_pattern": [
                f"{exam_name} exam pattern marking scheme",
                f"{exam_name} paper pattern duration marks",
            ],
            "study_resources": [
                f"{exam_name} complete course playlist site:youtube.com",
                f"{exam_name} best reference books preparation strategy",
                f"{exam_name} free mock test series online",
                f"{exam_name} NPTEL or Coursera courses",
            ],
        }
        output = {}
        for key, query_list in queries.items():
            merged: List[SearchResult] = []
            for q in query_list:
                try:
                    merged.extend(self.search(q, max_results=7))
                except Exception as e:
                    logger.warning("Search failed for %s query=%s: %s", key, q, e)
            # Deduplicate by URL
            seen = set()
            deduped = []
            for r in merged:
                if not r.url or r.url in seen:
                    continue
                seen.add(r.url)
                deduped.append(r)
            output[key] = deduped[:20]
        return output
