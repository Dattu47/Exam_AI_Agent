import requests
import json
import logging
import os
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from exam_ai_agent.tools.web_search import search_bucket

logger = logging.getLogger(__name__)

class MaterialAggregator:
    def __init__(self):
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
        except Exception:
            api_key = os.environ.get("GEMINI_API_KEY", "")
            
        if api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.1
            )
        else:
            self.llm = None
            
    def _is_url_alive(self, url: str) -> bool:
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                return True
            resp = requests.get(url, timeout=5, stream=True)
            return resp.status_code < 400
        except Exception:
            return False

    def aggregate_materials(self, exam_name: str) -> Dict[str, List[Dict]]:
        """
        Searches for specific educational platforms, government sources, and standard books.
        """
        logger.info(f"[MaterialAggregator] Searching verified materials for {exam_name}")
        
        # Primary Education Portals & Specialized Prep
        edtech_sites = (
            "site:shiksha.com OR site:careers360.com OR site:collegedunia.com OR site:collegedekho.com "
            "OR site:notopedia.com OR site:testbook.com OR site:adda247.com OR site:byjus.com "
            "OR site:insightsonindia.com OR site:visionias.in OR site:drishtiias.com "
            "OR site:nptel.ac.in OR site:madeeasy.in OR site:gateoverflow.in OR site:oliveboard.in "
            "OR site:pw.live OR site:unacademy.com"
        )
        
        # Govt & Books
        gov_sites = "site:sarkariresult.com OR site:freejobalert.com OR site:jagranjosh.com OR site:pib.gov.in OR site:ncert.nic.in"
        
        edtech_queries = [
            f"{exam_name} detailed syllabus preparation {edtech_sites}",
            f"{exam_name} best mock test series {edtech_sites}",
        ]
        
        books_queries = [
            f"{exam_name} standard reference books list toppers",
            f"{exam_name} NCERT books recommended {gov_sites}",
            f"{exam_name} latest notifications {gov_sites}"
        ]
        
        edtech_results = search_bucket(edtech_queries, max_per_query=8)
        books_results = search_bucket(books_queries, max_per_query=8)
        
        valid_edtech = [r for r in edtech_results if self._is_url_alive(r.get("url", ""))]
        valid_books = [r for r in books_results if self._is_url_alive(r.get("url", ""))]
        
        if not self.llm:
            return {"edtech_links": valid_edtech[:5], "books": valid_books[:5]}
            
        prompt = f"""
        You are an expert at curating educational materials from verified platforms.
        Exam: {exam_name}
        
        EdTech/Portal Candidates:
        {json.dumps(valid_edtech[:15], indent=2)}
        
        Books/Gov Candidates:
        {json.dumps(valid_books[:15], indent=2)}
        
        Task:
        1. Select the top 5 most relevant links from top educational platforms (Shiksha, Testbook, Adda247, PW, Unacademy, VisionIAS, NPTEL, etc.).
        2. Select the top 5 standard reference book lists or verified government portal data (SarkariResult, NCERT, PIB).
        
        CRITICAL ACCURACY RULE:
        - If a link is NOT specifically related to the exam "{exam_name}", DO NOT INCLUDE IT.
        - Irrelevant links (e.g. Class 6th Maths, Folder Virus Recovery, irrelevant exams) MUST be strictly excluded.
        - If there are NO highly relevant links in a category, return an empty array `[]` for that category. Do not hallucinate.
        
        Return ONLY valid JSON in this format:
        {{
            "edtech_links": [{{"title": "...", "url": "..."}}],
            "books": [{{"title": "...", "url": "..."}}]
        }}
        """
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            res = self.llm.invoke([
                SystemMessage(content="Output ONLY raw JSON."),
                HumanMessage(content=prompt)
            ])
            text = res.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]
            return json.loads(text)
        except Exception as e:
            logger.error(f"[MaterialAggregator] LLM failed: {e}")
            return {"edtech_links": valid_edtech[:5], "books": valid_books[:5]}
