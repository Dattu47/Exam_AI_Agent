"""
YouTube Timestamps: Uses youtube-transcript-api to extract timestamps for syllabus topics.
Supports concurrent fetching, multiple Indian regional languages, and robust URL parsing.
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

from exam_ai_agent.utils.logger import get_logger

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

logger = get_logger(__name__)

SUPPORTED_LANGUAGES = ["en", "en-IN", "hi", "hi-Latn", "en-GB", "en-US"]


class YouTubeTimestampsTool:
    """Extracts timestamps for syllabus topics from YouTube transcripts concurrently."""

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract the YouTube video ID from various YouTube URL formats."""
        if not url:
            return None
        try:
            parsed = urlparse(url.strip())
            netloc = parsed.netloc.lower().replace("www.", "")

            # youtu.be/ID
            if netloc in ("youtu.be",):
                return parsed.path.lstrip("/").split("/")[0].split("?")[0] or None

            # youtube.com or m.youtube.com
            if "youtube.com" in netloc:
                if parsed.path == "/watch":
                    return parse_qs(parsed.query).get("v", [None])[0]
                if parsed.path.startswith(("/embed/", "/v/", "/shorts/")):
                    parts = parsed.path.strip("/").split("/")
                    if len(parts) >= 2:
                        return parts[1].split("?")[0]
        except Exception:
            pass

        # Regex fallback
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        return match.group(1) if match else None

    def _fetch_single_video_timestamps(
        self,
        video_dict: Dict[str, Any],
        topics_lower: List[str],
    ) -> Dict[str, Any]:
        """Worker to extract timestamps for one video."""
        enriched = dict(video_dict)
        url = enriched.get("url", "")
        video_id = self._extract_video_id(url)

        if not video_id or not YouTubeTranscriptApi:
            enriched["timestamps"] = []
            return enriched

        timestamps = []
        try:
            # First try direct language preference
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=SUPPORTED_LANGUAGES
                )
            except Exception:
                # Fallback to any transcript available (manual or auto-generated)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript_obj = transcript_list.find_transcript(SUPPORTED_LANGUAGES)
                transcript = transcript_obj.fetch()

            seen_topics: set = set()
            for entry in transcript:
                text_lower = entry.get("text", "").lower()
                for topic in topics_lower:
                    if topic not in seen_topics and topic in text_lower:
                        seen_topics.add(topic)
                        seconds = int(entry.get("start", 0))
                        sep = "&" if "?" in url else "?"
                        timestamps.append({
                            "topic": topic.title(),
                            "timestamp_sec": seconds,
                            "deep_link": f"{url}{sep}t={seconds}s",
                        })
                        if len(timestamps) >= 5:
                            break
                if len(timestamps) >= 5:
                    break

        except Exception as e:
            logger.debug("[YouTubeTimestamps] Transcript skipped for %s: %s", video_id, e)

        enriched["timestamps"] = timestamps[:5]
        return enriched

    def enrich_with_timestamps(
        self,
        videos: List[Dict[str, Any]],
        syllabus_topics: List[str],
    ) -> List[Dict[str, Any]]:
        """
        For each video, concurrently find transcript timestamps where syllabus topics are mentioned.
        Adds a 'timestamps' key (list of up to 5 matches) to each video dict.
        """
        if not YouTubeTranscriptApi:
            logger.info("[YouTubeTimestamps] youtube-transcript-api not installed.")
            return videos

        if not videos or not syllabus_topics:
            return videos

        topics_lower = [t.strip().lower() for t in syllabus_topics if len(t.strip()) > 2]
        if not topics_lower:
            return videos

        worker_count = min(len(videos), 5)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(self._fetch_single_video_timestamps, v, topics_lower)
                for v in videos
            ]
            results = []
            for f in futures:
                try:
                    results.append(f.result(timeout=10))
                except Exception:
                    pass

        return results if results else videos
