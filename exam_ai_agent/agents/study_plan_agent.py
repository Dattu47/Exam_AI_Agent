"""
Study Plan Agent: Wraps the StudyPlanService and builds the preparation plan based on processed data.
"""

import os
from typing import List, Dict, Any
from langchain_groq import ChatGroq

from exam_ai_agent.services.study_plan_service import StudyPlanService
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

def _get_groq_api_key() -> str:
    """Retrieve Groq API key from Streamlit secrets or environment."""
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


class StudyPlanAgent:
    def __init__(self, study_plan_service: StudyPlanService = None):
        api_key = _get_groq_api_key()
        if api_key:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.2
            )
        else:
            logger.warning("[StudyPlanAgent] Missing GROQ_API_KEY.")
            llm = None
            
        self.study_service = study_plan_service or StudyPlanService(llm=llm)

    def build_plan(self, exam_name: str, syllabus_items: List[Dict[str, Any]], important_topics: List[str], weeks: int = 4) -> List[Dict[str, Any]]:
        """
        Takes the finalized syllabus lists and generates a realistic study schedule.
        """
        logger.info("[StudyPlanAgent] Generating %d-week study plan for %s", weeks, exam_name)
        
        syllabus_summary = " ".join([s.get("topic", "") for s in syllabus_items[:50]])[:5000]
        
        if not syllabus_summary and not important_topics:
            logger.warning("[StudyPlanAgent] No syllabus or topics found. Skipping study plan generation.")
            return []
            
        plan = self.study_service.generate_plan(
            exam_name,
            syllabus_summary=syllabus_summary,
            important_topics=important_topics[:50],
            weeks=weeks,
        )
        
        if not plan:
            logger.warning("[StudyPlanAgent] Study plan generation failed or returned empty.")
        else:
            logger.info("[StudyPlanAgent] Successfully generated plan with %d weeks.", len(plan))
            
        return plan
