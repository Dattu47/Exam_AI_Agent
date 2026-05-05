"""
Research Agent: The Orchestrator for Resource Aggregation.
Coordinates AuthorityService, MaterialAggregator, YoutubeAgent, and PYQ searches.
"""

from typing import Dict, Any

from exam_ai_agent.services.authority_service import AuthorityService
from exam_ai_agent.agents.material_aggregator import MaterialAggregator
from exam_ai_agent.agents.youtube_agent import YoutubeAgent
from exam_ai_agent.agents.search_agent import SearchAgent
from exam_ai_agent.services.supabase_service import SupabaseService
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

class ResearchAgent:
    def __init__(self):
        # Initialize Sub-Agents/Services
        self.authority_service = AuthorityService()
        self.material_aggregator = MaterialAggregator()
        self.youtube_agent = YoutubeAgent()
        self.search_agent = SearchAgent()
        
        # Initialize Supabase
        self.db = SupabaseService()

    def research_exam(self, exam_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Full orchestration pipeline for Resource Aggregation.
        """
        logger.info("========================================")
        logger.info("[Orchestrator] Beginning Resource Aggregation for: %s", exam_name)
        
        self.db.save_user_query(exam_name)
        
        if not force_refresh:
            cached_data = self.db.get_exam_resources(exam_name)
            if cached_data:
                logger.info("[Orchestrator] Cache hit! Returning saved data for %s", exam_name)
                return cached_data

        # 1. Authority Info
        authority_data = self.authority_service.get_authority_info(exam_name)
        
        # 2. PYQ Archive (Using search agent for PYQs)
        search_grouped = self.search_agent.find_resources(exam_name)
        pyqs = search_grouped.get("previous_papers", [])
        archive = []
        for p in pyqs[:15]:
            title = p.title if hasattr(p, "title") else p.get("title", "")
            url = p.url if hasattr(p, "url") else p.get("url", "")
            snippet = p.snippet if hasattr(p, "snippet") else p.get("snippet", "")
            archive.append({"title": title, "url": url, "snippet": snippet})
        
        # Deduplicate PYQs by url and filter relevance using Gemini
        seen = set()
        dedup_archive = []
        for p in archive:
            if p["url"] and p["url"] not in seen:
                if self.material_aggregator._is_url_alive(p["url"]):
                    dedup_archive.append(p)
                    seen.add(p["url"])
                    
        # Apply LLM filtering to PYQs if we have Gemini available
        llm = self.material_aggregator.llm
        if llm and dedup_archive:
            import json
            prompt = f"""
            You are an expert educational content curator.
            Exam: {exam_name}
            
            Previous Year Question (PYQ) Candidates:
            {json.dumps(dedup_archive[:10], indent=2)}
            
            Task:
            Filter the list to ONLY include authentic and highly relevant PYQ paper links.
            
            CRITICAL ACCURACY RULE:
            - If a link is NOT specifically a PYQ/Mock paper for the exam "{exam_name}", strictly REMOVE it.
            - If there are no highly relevant links, return an empty array `[]`.
            
            Return ONLY valid JSON in this format:
            [
                {{"title": "...", "url": "...", "snippet": "..."}},
                ...
            ]
            """
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = llm.invoke([
                    SystemMessage(content="Output ONLY raw JSON."),
                    HumanMessage(content=prompt)
                ])
                text = res.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                start = text.find("[")
                end = text.rfind("]") + 1
                if start != -1 and end > start:
                    text = text[start:end]
                dedup_archive = json.loads(text)
            except Exception as e:
                logger.error(f"[Orchestrator] PYQ LLM filter failed: {e}")
        
        
        # 3. Video Library
        videos = self.youtube_agent.get_top_playlists(exam_name)
        
        # 4. Study Materials (Drive + Books)
        materials = self.material_aggregator.aggregate_materials(exam_name)

        final_response = {
            "authority": authority_data,
            "archive": dedup_archive[:10],
            "videos": videos,
            "library": materials
        }

        # CACHING
        has_content = (
            bool(final_response.get("authority", {}).get("official_site")) or
            bool(final_response.get("archive")) or
            bool(final_response.get("library", {}).get("drive_links"))
        )
        if has_content:
            self.db.save_exam_resources(exam_name, final_response)
        else:
            logger.warning("[Orchestrator] Skipping Supabase save — result has no content.")

        logger.info("[Orchestrator] Finished research pipeline for %s", exam_name)
        return final_response
