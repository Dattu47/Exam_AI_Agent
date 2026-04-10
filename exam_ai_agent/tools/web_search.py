"""
Web Search Tool — DuckDuckGo powered, multi-bucket parallel search.
Targets authoritative Indian exam portals and official bodies for
accurate, deduplicated, end-to-end exam data.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from dataclasses import dataclass

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

# ── Authoritative source domains (used inside queries, never shown to users) ──
_OFFICIAL_PORTALS = (
    "site:nta.ac.in OR site:ssc.nic.in OR site:upsc.gov.in OR site:gate.iitkgp.ac.in"
)
_EXAM_INFO_SITES = (
    "site:careers360.com OR site:shiksha.com OR site:geeksforgeeks.org OR site:testbook.com"
)
_GOVT_EXAM_SITES = (
    "site:careers360.com OR site:testbook.com OR site:adda247.com OR site:shiksha.com"
)
_PLACEMENT_SITES = (
    "site:geeksforgeeks.org OR site:indiabix.com OR site:interviewbit.com OR site:testbook.com"
)
_PYQ_SITES = (
    "site:pyqpaper.com OR site:examrace.com OR site:mrunal.org OR site:testbook.com "
    "OR site:careers360.com OR site:geeksforgeeks.org"
)
_OFFICIAL_PYQ_SITES = (
    "site:upsc.gov.in OR site:ssc.nic.in OR site:nta.ac.in OR site:ibps.in OR site:rbi.org.in"
)
_RESOURCE_SITES = (
    "site:geeksforgeeks.org OR site:testbook.com OR site:careers360.com OR site:indiabix.com"
)
_STUDY_MATERIAL_SITES = (
    "site:geeksforgeeks.org OR site:tutorialspoint.com OR site:nptel.ac.in "
    "OR site:testbook.com OR site:adda247.com"
)
_YOUTUBE_CHANNELS = (
    "site:youtube.com"
)


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
        Queries target authoritative Indian exam portals and official bodies.
        Returns grouped dict of results per category.
        """
        import datetime as _dt
        year = _dt.datetime.now().year
        en   = exam_name

        queries = {
            # ── Exam overview / eligibility / pattern ──────────────────────────
            "exam_info": [
                f"{en} exam eligibility syllabus exam pattern complete details {year}",
                f"{en} official notification eligibility criteria {year} {_OFFICIAL_PORTALS}",
                f"{en} exam overview conducting authority {year} {_EXAM_INFO_SITES}",
                f"{en} exam {year} full details marks scheme sections {_GOVT_EXAM_SITES}",
            ],

            # ── Syllabus — highest priority; pull from trusted portals ─────────
            "syllabus": [
                f"{en} complete syllabus {year} subject-wise topics chapters {_EXAM_INFO_SITES}",
                f"{en} syllabus PDF official {year} {_OFFICIAL_PORTALS}",
                f"{en} detailed syllabus {year} all subjects units {_GOVT_EXAM_SITES}",
                f"{en} syllabus {year} topic list preparation {_PLACEMENT_SITES}",
                f"{en} updated syllabus {year} topics subtopics official",
            ],

            # ── Previous Year Papers (PYQs) — year-wise + stage-wise ──────────
            "previous_papers": [
                f"{en} previous year question papers PDF free download {year} {_PYQ_SITES}",
                f"{en} PYQ solved papers last 5 years free PDF official {_PYQ_SITES}",
                f"{en} question papers {year} {year-1} {year-2} download official {_OFFICIAL_PYQ_SITES}",
                f"{en} prelims previous year papers PDF download official",
                f"{en} mains previous year papers PDF download free",
                f"{en} previous papers with solutions PDF {_PYQ_SITES}",
            ],

            # ── Model Papers / Mock Tests ──────────────────────────────────────
            "model_papers": [
                f"{en} model papers mock tests free PDF official sample papers {year}",
                f"{en} full length mock test practice papers {year} {_RESOURCE_SITES}",
                f"{en} sample question paper official {year} {_OFFICIAL_PORTALS}",
                f"{en} online mock test free {year} {_GOVT_EXAM_SITES}",
                f"{en} sectional mock test subject-wise practice {_RESOURCE_SITES}",
            ],

            # ── Exam pattern / marking scheme ──────────────────────────────────
            "exam_pattern": [
                f"{en} exam pattern marks scheme sections {year} {_EXAM_INFO_SITES}",
                f"{en} marking scheme negative marking total marks {year}",
                f"{en} exam structure sections time duration {year} official",
            ],

            # ── Subject-wise Study Material / Notes / PDFs ────────────────────
            "study_resources": [
                f"{en} subject-wise study material notes PDF free {year} {_STUDY_MATERIAL_SITES}",
                f"{en} best books preparation guide recommended {year} {_RESOURCE_SITES}",
                f"{en} free study notes PDF topic-wise {year} {_STUDY_MATERIAL_SITES}",
                f"{en} NPTEL free course study material {year}",
                f"{en} preparation tips important books subject notes {year}",
            ],

            # ── YouTube — complete playlists / structured courses only ─────────
            "youtube_lectures": [
                f"{en} complete preparation full course playlist {_YOUTUBE_CHANNELS} {year}",
                f"{en} full syllabus video lectures playlist {_YOUTUBE_CHANNELS}",
                f"{en} subject-wise video lectures playlist {_YOUTUBE_CHANNELS} {year}",
                f"{en} best youtube channel complete course {year}",
                f"{en} free video course lectures {_YOUTUBE_CHANNELS}",
            ],
        }

        limits = {
            "exam_info":        6,
            "syllabus":        10,
            "previous_papers": 12,
            "model_papers":     8,
            "exam_pattern":     6,
            "study_resources":  8,
            "youtube_lectures": 8,
        }

        output = {}

        num_workers = max(1, len(queries))
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
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
