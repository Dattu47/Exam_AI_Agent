import json
import logging
import os
import requests
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from exam_ai_agent.tools.web_search import search_bucket

logger = logging.getLogger(__name__)

class YoutubeAgent:
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

    def _is_youtube_url(self, url: str) -> bool:
        """Confirm the URL is a real YouTube link."""
        return bool(url) and ("youtube.com" in url or "youtu.be" in url)

    def _is_url_alive(self, url: str) -> bool:
        try:
            r = requests.head(url, timeout=5, allow_redirects=True)
            return r.status_code < 400
        except Exception:
            return False

    def get_top_playlists(self, exam_name: str) -> List[Dict]:
        """
        Searches for YouTube playlists strictly related to the given exam.
        Uses exact phrase + notable channels. Returns top 3 validated results.
        """
        logger.info(f"[YoutubeAgent] Finding playlists for {exam_name}")
        
        # Use exact exam name in quotes so results are STRICTLY for this exam
        exam_q = f'"{exam_name}"'
        
        # Target notable channels for different exam categories
        upsc_channels = "Mrunal Patel OR Study IQ IAS OR Khan GS Research Centre OR Drishti IAS OR Insights IAS"
        gate_channels = "Neso Academy OR GATE Smashers OR Ravindrababu Ravula OR Unacademy GATE"
        bank_channels = "Wifistudy OR Adda247 OR Oliveboard OR Unacademy Banking"
        general_channels = "Physics Wallah OR Unacademy OR BYJU'S Exam Prep"
        all_channels = f"{upsc_channels} OR {gate_channels} OR {bank_channels} OR {general_channels}"

        yt_queries = [
            f"{exam_q} complete preparation playlist site:youtube.com ({all_channels})",
            f"{exam_q} full course lectures site:youtube.com",
            f"{exam_q} 2024 preparation tips video site:youtube.com",
        ]
        
        yt_results = search_bucket(yt_queries, max_per_query=8)
        
        # Filter: only keep valid YouTube URLs
        yt_valid = [r for r in yt_results if self._is_youtube_url(r.get("url", ""))]
        
        if not yt_valid:
            return []
            
        if not self.llm:
            return [{"title": r.get("title"), "url": r.get("url"), "category": "General", "description": r.get("snippet", "")} for r in yt_valid[:3]]
            
        prompt = f"""
        You are an expert at curating educational YouTube content for Indian competitive exams.
        Exam: {exam_name}
        
        YouTube Search Results (all are YouTube links):
        {json.dumps(yt_valid[:15], indent=2)}
        
        Task:
        1. Select the top 3 most relevant playlists or video series for the exam "{exam_name}".
        2. Categorize each as: "Beginner", "Intermediate", "Advanced", or the specific Topic (e.g. "Quantitative Aptitude", "GS Paper 1").
        3. Write a 1-line description of what each playlist covers.
        
        STRICT RULES:
        - ONLY include videos/playlists that are DIRECTLY about "{exam_name}". 
        - A general "Banking" video must NOT be included for "IBPS PO" unless it specifically mentions IBPS PO.
        - A general "UPSC" channel must NOT be included for "GATE CSE" — they are completely different exams.
        - Reject any video that is not relevant. Return [] if nothing is genuinely relevant.
        
        Return ONLY valid JSON:
        [
            {{"title": "...", "url": "...", "category": "...", "description": "..."}},
            ...
        ]
        """
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            res = self.llm.invoke([
                SystemMessage(content="Output ONLY raw JSON array. No markdown fences."),
                HumanMessage(content=prompt)
            ])
            text = res.content.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                text = text[start:end]
            results = json.loads(text)
            # Final safety filter: only YouTube URLs
            return [r for r in results if self._is_youtube_url(r.get("url", ""))][:3]
        except Exception as e:
            logger.error(f"[YoutubeAgent] LLM failed: {e}")
            return [{"title": r.get("title"), "url": r.get("url"), "category": "General", "description": r.get("snippet", "")} for r in yt_valid[:3]]
