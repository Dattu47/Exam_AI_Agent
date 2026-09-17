"""
Supabase database integration service.
Handles saving and retrieving exam research data for persistence and caching.
"""

import socket
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """Service to interact with the Supabase database for caching and tracking."""

    def __init__(self):
        url, key = settings.resolve_supabase_credentials()
        self.client = None

        if url and key and "your_supabase" not in url:
            try:
                # Pre-check DNS reachability with timeout to avoid hanging on slow network
                host = urlparse(url).hostname
                if host:
                    prev_timeout = socket.getdefaulttimeout()
                    try:
                        socket.setdefaulttimeout(3.0)
                        socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
                    finally:
                        socket.setdefaulttimeout(prev_timeout)

                from supabase import create_client
                self.client = create_client(url, key)
                logger.info("Supabase client initialized successfully.")
            except (socket.gaierror, socket.timeout):
                logger.warning(
                    "Supabase host unreachable (DNS/network timeout). Caching will be disabled."
                )
            except Exception as e:
                logger.warning("Failed to initialize Supabase client: %s", e)
        else:
            logger.info("Supabase credentials not set or incomplete. Offline mode active.")

    def _normalize_exam_name(self, exam_name: str) -> str:
        """Normalize exam name removing irregular whitespace and casing for uniform cache matching."""
        import re
        return re.sub(r"\s+", " ", exam_name.lower().strip())

    def is_connected(self) -> bool:
        """Return True if Supabase is properly configured and connected."""
        return self.client is not None

    def save_user_query(self, exam_name: str, user_id: str = "anonymous") -> bool:
        """Log a user's search query."""
        if not self.is_connected() or not exam_name:
            return False
        try:
            self.client.table("user_queries").insert(
                {"exam_name": self._normalize_exam_name(exam_name), "user_id": user_id}
            ).execute()
            logger.info("Saved user query for '%s'", exam_name)
            return True
        except Exception as e:
            logger.warning("Failed to save user query: %s", e)
            return False

    def save_exam_resources(self, exam_name: str, resources_data: Dict[str, Any]) -> bool:
        """
        Upsert scraped resources for an exam (keyed by normalized exam_name).
        Maps the frontend response schema to database columns.
        """
        if not self.is_connected() or not exam_name:
            return False
        try:
            clean_name = self._normalize_exam_name(exam_name)
            data = {
                "exam_name": clean_name,
                "syllabus": resources_data.get("authority", {}),
                "previous_papers": resources_data.get("archive", []),
                "important_topics": [],
                "resources": resources_data.get("library", {}),
                "youtube_lectures": resources_data.get("videos", []),
            }
            self.client.table("exam_resources").upsert(
                data, on_conflict="exam_name"
            ).execute()
            logger.info("Saved exam resources for '%s'", clean_name)
            return True
        except Exception as e:
            logger.warning("Failed to save exam resources: %s", e)
            return False

    def get_exam_resources(self, exam_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored exam resources from the database.
        Returns None if not found (forces a fresh pipeline run).
        """
        if not self.is_connected() or not exam_name:
            return None
        clean_name = self._normalize_exam_name(exam_name)
        try:
            res = (
                self.client.table("exam_resources")
                .select("*")
                .eq("exam_name", clean_name)
                .execute()
            )
            if not res.data:
                return None

            db_data = res.data[0]
            logger.info("Cache hit: retrieved data for '%s' from Supabase.", exam_name)

            return {
                "authority": db_data.get("syllabus", {}),
                "archive": db_data.get("previous_papers", []),
                "videos": db_data.get("youtube_lectures", []),
                "library": db_data.get("resources", {}),
            }
        except Exception as e:
            logger.warning("Error retrieving exam resources for '%s': %s", exam_name, e)
            return None

    def save_study_plan(self, exam_name: str, plan: List[Dict[str, Any]]) -> bool:
        """Save a generated study plan."""
        if not self.is_connected() or not exam_name:
            return False
        try:
            clean_name = self._normalize_exam_name(exam_name)
            self.client.table("study_plans").upsert(
                {"exam_name": clean_name, "plan_data": plan},
                on_conflict="exam_name",
            ).execute()
            logger.info("Saved study plan for '%s'", clean_name)
            return True
        except Exception as e:
            logger.warning("Failed to save study plan: %s", e)
            return False

    def save_task_checklist(self, exam_name: str, checklist: Dict[str, bool]) -> bool:
        """Persist the daily task checklist."""
        if not self.is_connected() or not exam_name:
            return False
        try:
            clean_name = self._normalize_exam_name(exam_name)
            res = (
                self.client.table("study_plans")
                .select("plan_data")
                .eq("exam_name", clean_name)
                .execute()
            )
            plan_data = res.data[0]["plan_data"] if res.data else {}
            self.client.table("study_plans").upsert(
                {
                    "exam_name": clean_name,
                    "plan_data": plan_data,
                    "task_checklist": checklist,
                },
                on_conflict="exam_name",
            ).execute()
            return True
        except Exception as e:
            logger.warning("Failed to save task checklist: %s", e)
            return False

    def get_task_checklist(self, exam_name: str) -> Dict[str, bool]:
        """Retrieve the saved task checklist state."""
        if not self.is_connected() or not exam_name:
            return {}
        try:
            clean_name = self._normalize_exam_name(exam_name)
            res = (
                self.client.table("study_plans")
                .select("task_checklist")
                .eq("exam_name", clean_name)
                .execute()
            )
            if res.data and "task_checklist" in res.data[0]:
                return res.data[0]["task_checklist"] or {}
            return {}
        except Exception as e:
            logger.warning("Error retrieving checklist for '%s': %s", exam_name, e)
            return {}
