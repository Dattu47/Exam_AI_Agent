"""
Response Agent: Formats the final results and coordinates the vector store persistence.
"""

import os
import json
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from exam_ai_agent.database.vector_store import VectorStore
from exam_ai_agent.services.syllabus_service import SyllabusService
from exam_ai_agent.services.papers_service import PapersService
from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

def _get_groq_api_key() -> str:
    """Retrieve Groq API key from Streamlit secrets or environment."""
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


class ResponseAgent:
    def __init__(self, vector_store: VectorStore = None, syllabus_service: SyllabusService = None, papers_service: PapersService = None):
        self.vector_store = vector_store or VectorStore()
        self.syllabus_service = syllabus_service or SyllabusService()
        self.pdf_tool = PDFDownloaderTool(WebScraperTool())
        self.papers_service = papers_service or PapersService(self.pdf_tool)
        
        api_key = _get_groq_api_key()
        if api_key:
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.2,
                max_tokens=8192
            )
        else:
            logger.warning("[ResponseAgent] Missing GROQ_API_KEY.")
            self.llm = None

    def format_final_response(
            self,
            exam_name: str,
            info_results: List[Any],
            syllabus_results: List[Any],
            papers_results: List[Any],
            study_results: List[Any],
            youtube_results: List[Any],
            scraped_syllabus_items: List[Dict[str, str]],
            important_topics: List[str],
            study_plan: List[Dict[str, Any]],
            hidden_pdfs: List[Dict[str, str]],
            raw_text_chunks: List[str]
        ) -> Dict[str, Any]:
        """
        Builds the final structured dictionary to send back to the UI.
        """
        logger.info("[ResponseAgent] Formatting final response for %s", exam_name)
        
        result = {
            "about_exam": {"description": "", "deadline": "TBA"},
            "syllabus": [],
            "previous_papers": [],
            "important_topics": important_topics,
            "study_plan": study_plan,
            "resources": [],
            "youtube_lectures": []
        }
        
        # Step 1: Info extraction
        info_snippets = [getattr(r, "snippet", "") or r.get("snippet", "") for r in info_results]
        result["about_exam"]["description"] = " ".join(info_snippets[:3])
        
        # Step 2: Syllabus
        syllabus_items = self.syllabus_service.extract_from_search_results(syllabus_results)
        result["syllabus"] = self.syllabus_service.merge_syllabus(syllabus_items, scraped_syllabus_items, exam_name)
        
        # Step 3: Papers & Resources
        result["previous_papers"] = self.papers_service.from_search_results(papers_results)
        
        for r in study_results:
            url = getattr(r, "url", None) or (r.get("url") if isinstance(r, dict) else "")
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            if url and title:
                result["resources"].append({"title": title, "url": url, "type": "link"})

        for r in youtube_results:
            url = getattr(r, "url", None) or (r.get("url") if isinstance(r, dict) else "")
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            if url and title:
                result["youtube_lectures"].append({"title": title, "url": url, "type": "video"})
        
        # Step 4: Vector Storage (Optional background processing)
        if raw_text_chunks and self.vector_store:
            try:
                self.vector_store.add_texts(raw_text_chunks[:50], exam_name=exam_name)
            except: pass

        # Step 5: LLM Polish
        if self.llm:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", 
                     "You are an elite academic strict JSON formatter. \n"
                     "Review the provided JSON data. Apply these ABSOLUTE RULES:\n"
                     "1. Remove ANY duplicate URLs globally across all sections.\n"
                     "2. Match exactly these keys: 'about_exam', 'syllabus', 'previous_papers', 'important_topics', 'study_plan', 'resources', 'youtube_lectures'.\n"
                     "3. 'about_exam' MUST contain 'description' (concise summary) and 'deadline' (application date if found, else 'Check Official Notification').\n"
                     "4. 'syllabus' MUST be an array of objects: {'topic': string, 'subtopics': [strings]}. NO DESCRIPTIONS.\n"
                     "5. CATEGORY ISOLATION: YouTube strictly in 'youtube_lectures'.\n"
                     "6. Output ONLY valid JSON, absolutely NO markdown decorators.\n"
                    ),
                    ("human", "{data}")
                ])
                chain = prompt | self.llm
                res = chain.invoke({"data": json.dumps(result)})
                
                text = res.content.strip()
                if text.startswith("```json"): text = text[7:]
                if text.startswith("```"): text = text[3:]
                if text.endswith("```"): text = text[:-3]
                return json.loads(text)
            except Exception as e:
                logger.error(f"[ResponseAgent] Final LLM filter failed: {e}")
                return result
        
        return result
