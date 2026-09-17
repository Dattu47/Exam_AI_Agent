"""
YouTube Agent: Curates top lecture series and playlists for competitive exams.
Filters out Shorts and clickbait, categorizes into academic tiers, and validates relevance.
"""

import json
from typing import List, Dict
from urllib.parse import urlparse, parse_qs

from exam_ai_agent.tools.web_search import search_bucket, generate_search_queries
from exam_ai_agent.utils.common import (
    get_llm,
    strip_json_fences,
    invoke_llm_with_retry,
)
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class YoutubeAgent:
    def __init__(self):
        self.llm = get_llm()

    def _is_youtube_url(self, url: str) -> bool:
        """Return True only for valid YouTube video/playlist URLs (excludes Shorts)."""
        if not url:
            return False
        try:
            url_lower = url.lower()
            if "/shorts/" in url_lower or "shorts" in url_lower.split("?")[0]:
                return False  # Reject YouTube Shorts

            parsed = urlparse(url.strip())
            netloc = parsed.netloc.lower().replace("www.", "")
            return "youtube.com" in netloc or "youtu.be" in netloc
        except Exception:
            return False

    def _canonical_video_key(self, url: str) -> str:
        """Extract canonical ID or query for deduplication."""
        try:
            parsed = urlparse(url.strip())
            qs = parse_qs(parsed.query)
            if "list" in qs:
                return f"playlist_{qs['list'][0]}"
            if "v" in qs:
                return f"video_{qs['v'][0]}"
            if "youtu.be" in parsed.netloc:
                return f"video_{parsed.path.lstrip('/')}"
        except Exception:
            pass
        return url.split("?")[0].rstrip("/").lower()

    def _infer_category(self, title: str, snippet: str) -> str:
        """Heuristic category assignment when LLM is offline."""
        text = f"{title} {snippet}".lower()
        if any(k in text for k in ["pyq", "previous year", "solved paper", "solution", "past year"]):
            return "PYQ Solving"
        if any(k in text for k in ["marathon", "revision", "crash course", "quick review", "one shot"]):
            return "Revision"
        if any(k in text for k in ["complete", "full course", "masterclass", "entire syllabus", "full syllabus", "playlist"]):
            return "Full Course"
        return "Topic-wise"

    def get_top_playlists(self, exam_name: str) -> List[Dict[str, str]]:
        """
        Searches for YouTube lecture courses and playlists specifically for the requested exam.
        Returns curated, categorized, and validated playlist results (6 to 10 items).
        """
        en = exam_name.strip()
        logger.info("[YoutubeAgent] Curating lecture series for: %s", en)

        # Generate multi-angle search queries
        yt_queries = generate_search_queries(en, "youtube")

        yt_results = search_bucket(yt_queries, max_per_query=8, delay_between=0.15, exam_name=en, resource_type="video")

        # Filter strictly for real YouTube URLs (no shorts) and deduplicate
        seen_keys = set()
        yt_valid = []
        for r in yt_results:
            url = r.get("url", "")
            if not self._is_youtube_url(url):
                continue
            key = self._canonical_video_key(url)
            if key not in seen_keys:
                seen_keys.add(key)
                yt_valid.append(r)

        if not yt_valid:
            return []

        if not self.llm:
            return [
                {
                    "title": r.get("title", "Exam Preparation Lecture"),
                    "url": r.get("url"),
                    "category": self._infer_category(r.get("title", ""), r.get("snippet", "")),
                    "channel": "Educational Channel",
                    "description": r.get("snippet", "Comprehensive syllabus lectures."),
                }
                for r in yt_valid[:8]
            ]

        prompt = f"""
SYSTEM ROLE:
You are an expert academic curriculum curator for competitive examinations.

TASK:
Select and categorize the top 6 to 10 most authentic, high-value lecture playlists or video series for: {en}.

CANDIDATE YOUTUBE COURSES:
{json.dumps(yt_valid[:18], indent=2)}

CATEGORIES ALLOWED:
- "Full Course"
- "Topic-wise"
- "PYQ Solving"
- "Revision"

RULES:
1. ONLY include courses directly covering "{en}".
2. Reject single short clips, clickbait, and unrelated examinations.
3. Extract or infer the channel name if identifiable from title/snippet.
4. Distribute across available categories where possible (Full Course, Topic-wise, PYQ Solving, Revision).
5. Provide a concise, professional 1-sentence description of the playlist content.
6. Output ONLY raw JSON array without formatting fences.

OUTPUT JSON SCHEMA:
[
    {{
        "title": "...",
        "url": "...",
        "channel": "...",
        "category": "Full Course | Topic-wise | PYQ Solving | Revision",
        "description": "..."
    }}
]
"""

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            content = invoke_llm_with_retry(self.llm, [
                SystemMessage(content="You are a strict JSON generator. Output a raw JSON array only."),
                HumanMessage(content=prompt),
            ])
            if not content:
                raise ValueError("LLM returned no content")

            cleaned = strip_json_fences(content)
            results = json.loads(cleaned)

            curated = [r for r in results if self._is_youtube_url(r.get("url", ""))]
            if curated:
                return curated[:10]

        except Exception as e:
            logger.warning("[YoutubeAgent] LLM curation error: %s. Using candidates.", e)

        return [
            {
                "title": r.get("title", "Exam Lecture"),
                "url": r.get("url"),
                "category": self._infer_category(r.get("title", ""), r.get("snippet", "")),
                "channel": "Verified Channel",
                "description": r.get("snippet", "Structured syllabus lectures."),
            }
            for r in yt_valid[:8]
        ]
