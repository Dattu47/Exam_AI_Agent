"""
YouTube Timestamps: Uses youtube-transcript-api to extract specific timestamps for syllabus topics.
"""

from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
from exam_ai_agent.utils.logger import get_logger

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

logger = get_logger(__name__)


class YouTubeTimestampsTool:
    """Extracts timestamps for syllabus topics from YouTube transcripts."""
    
    def enrich_with_timestamps(self, videos: List[Dict[str, Any]], syllabus_topics: List[str]) -> List[Dict[str, Any]]:
        """
        Takes a list of video dicts and a list of syllabus topics.
        Adds a 'timestamps' list to each video dict.
        """
        if not YouTubeTranscriptApi:
            logger.warning("[YouTubeTimestamps] youtube-transcript-api not installed.")
            return videos
            
        if not videos or not syllabus_topics:
            return videos
            
        topics_lower = [t.lower() for t in syllabus_topics if len(t) > 3]
        
        enriched_videos = []
        for v in videos:
            enriched = dict(v)
            url = enriched.get("url", "")
            if not url:
                enriched_videos.append(enriched)
                continue
                
            video_id = self._extract_video_id(url)
            if not video_id:
                enriched_videos.append(enriched)
                continue
                
            timestamps = []
            try:
                # Fetch transcript
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-IN'])
                
                # Simple fuzzy matching across transcript
                seen_topics = set()
                
                for entry in transcript:
                    text = entry['text'].lower()
                    for topic in topics_lower:
                        if topic not in seen_topics and topic in text:
                            seen_topics.add(topic)
                            seconds = int(entry['start'])
                            
                            # Build deep link
                            if '?' in url:
                                deep_link = f"{url}&t={seconds}s"
                            else:
                                deep_link = f"{url}?t={seconds}s"
                                
                            timestamps.append({
                                "topic": topic.title(),
                                "timestamp_sec": seconds,
                                "deep_link": deep_link
                            })
                            
            except Exception as e:
                logger.debug("[YouTubeTimestamps] Transcript fetch failed for %s: %s", video_id, e)
                
            enriched["timestamps"] = timestamps[:5] # Limit to 5 per video
            enriched_videos.append(enriched)
            
        return enriched_videos
        
    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        parsed = urlparse(url)
        if parsed.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed.path[1:]
        if parsed.hostname in ('youtube.com', 'www.youtube.com'):
            if parsed.path == '/watch':
                return parse_qs(parsed.query).get('v', [None])[0]
        return None
