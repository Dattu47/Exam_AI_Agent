"""
Research Agent: The Orchestrator.
Coordinates the specialized agents (Search, Scraping, Processing, StudyPlan, Response)
and Supabase caching to generate the full exam preparation plan.
"""

from typing import Dict, Any

from exam_ai_agent.agents.search_agent import SearchAgent
from exam_ai_agent.agents.scraping_agent import ScrapingAgent
from exam_ai_agent.agents.processing_agent import ProcessingAgent
from exam_ai_agent.agents.study_plan_agent import StudyPlanAgent
from exam_ai_agent.agents.response_agent import ResponseAgent
from exam_ai_agent.services.supabase_service import SupabaseService
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent:
    """
    Main Orchestrator Agent. 
    Intercepts cached database results to save time, or runs the full multi-agent pipeline if missing.
    """

    def __init__(self):
        # Initialize Sub-Agents
        self.search_agent = SearchAgent()
        self.scraping_agent = ScrapingAgent()
        self.processing_agent = ProcessingAgent()
        self.study_agent = StudyPlanAgent()
        self.response_agent = ResponseAgent()
        
        # Initialize Supabase
        self.db = SupabaseService()

    def research_exam(self, exam_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Full orchestration pipeline.
        
        Args:
            exam_name: Name of the exam (e.g., "GATE CSE")
            force_refresh: Ignore cache and re-scrape
        """
        logger.info("========================================")
        logger.info("[Orchestrator] Beginning research for: %s", exam_name)
        
        # 0. Log user query logic
        self.db.save_user_query(exam_name)
        
        # 1. Check Supabase Cache
        if not force_refresh:
            cached_data = self.db.get_exam_resources(exam_name)
            if cached_data:
                logger.info("[Orchestrator] Cache hit! Returning saved data for %s", exam_name)
                return cached_data

        result = {
            "syllabus": [],
            "previous_papers": [],
            "important_topics": [],
            "study_plan": [],
            "resources": [],
        }

        # 2. SEARH AGENT
        try:
            search_grouped = self.search_agent.find_resources(exam_name)
        except Exception as e:
            logger.exception("Search Agent failed: %s", e)
            result["error"] = f"Search failed: {e}"
            return result

        syllabus_results = search_grouped.get("syllabus", [])
        papers_results = search_grouped.get("previous_papers", [])
        pattern_results = search_grouped.get("exam_pattern", [])
        study_results = search_grouped.get("study_resources", [])
        youtube_results = search_grouped.get("youtube_lectures", [])

        # Gather target URLs
        syllabus_urls = [(r.url if hasattr(r, "url") else r.get("url", "")) for r in syllabus_results[:10]]
        paper_page_urls = [(r.url if hasattr(r, "url") else r.get("url", "")) for r in papers_results[:3]]

        # 3. SCRAPING AGENT
        scraped_pages, hidden_pdfs = self.scraping_agent.scrape_sources(syllabus_urls + paper_page_urls, max_pages=8)

        # 4. PROCESSING AGENT
        scraped_syllabus_items, important_topics, raw_text_chunks = self.processing_agent.extract_and_process(
            exam_name, scraped_pages, syllabus_urls, pattern_results
        )

        # 5. STUDY PLAN AGENT
        study_plan = self.study_agent.build_plan(exam_name, scraped_syllabus_items, important_topics, weeks=4)

        # 6. RESPONSE AGENT
        final_response = self.response_agent.format_final_response(
            exam_name,
            syllabus_results,
            papers_results,
            study_results,
            youtube_results,
            scraped_syllabus_items,
            important_topics,
            study_plan,
            hidden_pdfs,
            raw_text_chunks
        )

        # 7. CACHING: Only save to Supabase if the result has meaningful content.
        # Never overwrite good cached data with empty results caused by e.g. Groq rate limits.
        has_content = (
            bool(final_response.get("syllabus")) or
            bool(final_response.get("previous_papers")) or
            bool(final_response.get("resources"))
        )
        if has_content:
            self.db.save_exam_resources(exam_name, final_response)
            if study_plan:
                self.db.save_study_plan(exam_name, study_plan)
        else:
            logger.warning("[Orchestrator] Skipping Supabase save — result has no content (likely rate-limited).")

        logger.info("[Orchestrator] Finished research pipeline for %s", exam_name)
        return final_response
