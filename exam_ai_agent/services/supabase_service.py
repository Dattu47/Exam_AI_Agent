"""
Supabase database integration service.
Handles saving and retrieving exam research data to persist history and enable caching.
"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

# Attempt to load from .env file directly if not in env
load_dotenv()


class SupabaseService:
    """Service to interact with the Supabase database for caching and tracking."""
    
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL", "")
        self.key: str = os.environ.get("SUPABASE_KEY", "")
        self.client: Optional[Client] = None
        
        if self.url and self.key and "your_supabase" not in self.url:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error("Failed to initialize Supabase client: %s", e)
        else:
            logger.warning("Supabase credentials not found or invalid. Database features will be disabled.")

    def is_connected(self) -> bool:
        """Check if Supabase is properly configured and connected."""
        return self.client is not None

    def save_user_query(self, exam_name: str, user_id: str = "anonymous") -> bool:
        """Log a user's search query."""
        if not self.is_connected():
            return False
        try:
            data = {"exam_name": exam_name, "user_id": user_id}
            self.client.table("user_queries").insert(data).execute()
            logger.info("Saved user query for '%s'", exam_name)
            return True
        except Exception as e:
            logger.warning("Failed to save user query: %s", e)
            return False

    def save_exam_resources(self, exam_name: str, resources_data: Dict[str, Any]) -> bool:
        """
        Save the scraped resources (syllabus, papers, important topics, links).
        Upserts based on exam_name uniquely.
        """
        if not self.is_connected():
            return False
            
        try:
            # We assume exam_name is the unique key in the DB.
            data = {
                "exam_name": exam_name.lower().strip(),
                "syllabus": resources_data.get("syllabus", []),
                "previous_papers": resources_data.get("previous_papers", []),
                "important_topics": resources_data.get("important_topics", []),
                "resources": resources_data.get("resources", []),
                "youtube_lectures": resources_data.get("youtube_lectures", [])
            }
            # Upsert requires the table to have a unique constraint on exam_name
            self.client.table("exam_resources").upsert(data, on_conflict="exam_name").execute()
            logger.info("Saved exam resources to database for '%s'", exam_name)
            return True
        except Exception as e:
            logger.warning("Failed to save exam resources: %s", e)
            return False

    def save_study_plan(self, exam_name: str, plan: List[Dict[str, Any]]) -> bool:
        """Save the generated study plan."""
        if not self.is_connected():
            return False
            
        try:
            data = {
                "exam_name": exam_name.lower().strip(),
                "plan_data": plan
            }
            self.client.table("study_plans").upsert(data, on_conflict="exam_name").execute()
            logger.info("Saved study plan to database for '%s'", exam_name)
            return True
        except Exception as e:
            logger.warning("Failed to save study plan: %s", e)
            return False

    def get_exam_resources(self, exam_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored exam resources and study plan from the database.
        Returns None if not found, forcing a fresh scrape.
        """
        if not self.is_connected():
            return None
            
        clean_name = exam_name.lower().strip()
        try:
            # Fetch resources
            res = self.client.table("exam_resources").select("*").eq("exam_name", clean_name).execute()
            if not res.data:
                return None
                
            db_data = res.data[0]
            
            # Fetch study plan
            plan_res = self.client.table("study_plans").select("plan_data").eq("exam_name", clean_name).execute()
            db_plan = plan_res.data[0]["plan_data"] if plan_res.data else []
            
            logger.info("Cache hit: Retrieved exam data for '%s' from Supabase.", exam_name)
            
            return {
                "syllabus": db_data.get("syllabus", []),
                "previous_papers": db_data.get("previous_papers", []),
                "important_topics": db_data.get("important_topics", []),
                "resources": db_data.get("resources", []),
                "youtube_lectures": db_data.get("youtube_lectures", []),
                "study_plan": db_plan
            }
            
        except Exception as e:
            logger.error("Error retrieving exam resources from database: %s", e)
            return None
