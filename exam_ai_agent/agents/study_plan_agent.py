"""
Study Plan Agent: Wraps the StudyPlanService and builds the preparation plan based on processed data.
"""

from typing import List, Dict, Any
import streamlit as st
from langchain_groq import ChatGroq

from exam_ai_agent.services.study_plan_service import StudyPlanService
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

class StudyPlanAgent:
    def __init__(self, study_plan_service: StudyPlanService = None):
        api_key = st.secrets.get("GROQ_API_KEY", "")
        if api_key:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.2
            )
        else:
            logger.warning("[StudyPlanAgent] Missing GROQ_API_KEY in st.secrets.")
            llm = None
            
        self.study_service = study_plan_service or StudyPlanService(llm=llm)

    def build_plan(self, exam_name: str, syllabus_items: List[Dict[str, Any]], important_topics: List[str], weeks: int = 4) -> List[Dict[str, Any]]:
        """
        Takes the finalized syllabus lists and generates a realistic study schedule through the LLM.
        """
        logger.info("[StudyPlanAgent] Generating %d-week study plan for %s", weeks, exam_name)
        
        # We cap summary to avoid blowing out context windows on fallback LLMs
        syllabus_summary = " ".join([s.get("topic", "") for s in syllabus_items[:50]])[:5000]
        
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
