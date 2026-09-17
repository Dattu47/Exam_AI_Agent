"""
YouTube Agent: Curates top lecture series and playlists for competitive exams.
Filters out Shorts and clickbait, categorizes into academic tiers, and validates relevance.
"""

import json
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs

from exam_ai_agent.tools.web_search import search_bucket
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
            if "/shorts/" in url.lower():
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

    def get_top_playlists(self, exam_name: str) -> List[Dict[str, str]]:
        """
        Searches for YouTube lecture courses and playlists specifically for the requested exam.
        Returns curated, categorized, and validated playlist results.
        """
        en = exam_name.strip()
        logger.info("[YoutubeAgent] Curating lecture series for: %s", en)

        exam_q = f'"{en}"'

        upsc_channels = "Mrunal Patel OR Study IQ IAS OR Khan GS Research Centre OR Drishti IAS"
        gate_channels = "Neso Academy OR GATE Smashers OR Ravindrababu Ravula OR Unacademy GATE"
        bank_channels = "Wifistudy OR Adda247 OR Oliveboard OR Unacademy Banking"
        general_channels = "Physics Wallah OR Unacademy OR BYJU'S Exam Prep"
        all_channels = f"{upsc_channels} OR {gate_channels} OR {bank_channels} OR {general_channels}"

        yt_queries = [
            f"{exam_q} complete preparation playlist site:youtube.com ({all_channels}) -shorts",
            f"{exam_q} full course lectures playlist site:youtube.com -shorts",
            f"{exam_q} previous year questions solved playlist site:youtube.com -shorts",
        ]

        yt_results = search_bucket(yt_queries, max_per_query=6, delay_between=0.2, exam_name=en, resource_type="video")

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
                    "category": "Full Course",
                    "channel": "Educational Channel",
                    "description": r.get("snippet", "Comprehensive exam preparation course."),
                }
                for r in yt_valid[:4]
            ]

        prompt = f"""
SYSTEM ROLE:
You are an expert academic curriculum curator for competitive examinations.

TASK:
Select and categorize the top 4 most authentic lecture playlists or video series for: {en}.

CANDIDATE YOUTUBE COURSES:
{json.dumps(yt_valid[:12], indent=2)}

CATEGORIES ALLOWED:
- "Foundation / Beginner"
- "Full Course"
- "PYQ Solving"
- "Topic-wise"

RULES:
1. ONLY include courses directly covering "{en}".
2. Reject single short clips, clickbait, and unrelated examinations.
3. Extract or infer the channel name if identifiable from title/snippet.
4. Provide a concise, professional 1-sentence description of the playlist content.
5. Output ONLY raw JSON array without formatting fences.

OUTPUT JSON SCHEMA:
[
    {{
        "title": "...",
        "url": "...",
        "channel": "...",
        "category": "Foundation / Beginner | Full Course | PYQ Solving | Topic-wise",
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
            return curated[:4] if curated else [
                {
                    "title": r.get("title", "Exam Lecture"),
                    "url": r.get("url"),
                    "category": "Full Course",
                    "channel": "Verified Channel",
                    "description": r.get("snippet", "Structured syllabus lectures."),
                }
                for r in yt_valid[:4]
            ]

        except Exception as e:
            logger.warning("[YoutubeAgent] LLM curation error: %s. Using candidates.", e)
            return [
                {
                    "title": r.get("title", "Exam Lecture"),
                    "url": r.get("url"),
                    "category": "Full Course",
                    "channel": "Verified Channel",
                    "description": r.get("snippet", "Structured syllabus lectures."),
                }
                for r in yt_valid[:4]
            ]
