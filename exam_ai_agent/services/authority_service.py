import requests
from bs4 import BeautifulSoup
import json
import logging
import os
import re
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from exam_ai_agent.tools.web_search import search_bucket, get_official_site_query, get_syllabus_queries

logger = logging.getLogger(__name__)

class AuthorityService:
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
        if not url: return False
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                return True
            resp = requests.get(url, timeout=5, stream=True)
            return resp.status_code < 400
        except Exception:
            return False

    def _scrape_text(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code < 400:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=' ')
                # Collapse whitespace
                text = re.sub(r'\s+', ' ', text)
                return text[:8000] # Return first 8k chars for LLM
        except Exception as e:
            logger.warning(f"Scrape failed for {url}: {e}")
        return ""

    def validate_and_extract(self, exam_name: str, site_results: List[Dict], syllabus_results: List[Dict]) -> Dict:
        """
        Validates official sources and acts as an Official Fact-Checker to extract deeper metadata.
        """
        valid_sites = []
        # URL Discovery heuristics
        heuristic_urls = [
            f"https://{exam_name.lower().replace(' ', '')}.nic.in",
            f"https://{exam_name.lower().replace(' ', '')}.gov.in",
            f"https://{exam_name.lower().replace(' ', '')}.in"
        ]
        
        for h_url in heuristic_urls:
            if self._is_url_alive(h_url):
                valid_sites.append({"title": f"{exam_name.upper()} Official Portal", "url": h_url, "snippet": ""})
                
        # Add search results
        seen = set([s["url"] for s in valid_sites])
        for s in site_results:
            u = s.get("url", "")
            if u not in seen and self._is_url_alive(u):
                valid_sites.append(s)
                seen.add(u)
                
        valid_syllabi = [r for r in syllabus_results if self._is_url_alive(r.get("url", ""))]
        
        if not self.llm or not valid_sites:
            return {
                "official_site": valid_sites[0] if valid_sites else None,
                "syllabus_pdf": valid_syllabi[0] if valid_syllabi else None,
                "details": {}
            }
            
        # Fact Checking & Synthesis
        best_site_url = valid_sites[0]["url"]
        scraped_content = self._scrape_text(best_site_url)
        
        # Fallback: also scrape from an educational portal for richer detail
        fallback_queries = [
            f"{exam_name} exam overview conducting body eligibility notification shiksha.com OR careers360.com OR jagranjosh.com"
        ]
        fallback_results = search_bucket(fallback_queries, max_per_query=3)
        fallback_text = ""
        for fr in fallback_results[:2]:
            ft = self._scrape_text(fr.get("url", ""))
            if ft:
                fallback_text += ft[:2000]
                break
        
        combined_content = scraped_content[:3000] + "\n\n" + fallback_text[:2000]
        
        prompt = f"""
        You are the 'Official Fact-Checker' for Indian competitive exams.
        Exam: {exam_name}
        
        Website Candidates (Top matches):
        {json.dumps(valid_sites[:5], indent=2)}
        
        Syllabus PDF Candidates:
        {json.dumps(valid_syllabi[:5], indent=2)}
        
        Scraped Content from Official + Educational Portal:
        {combined_content[:5000]}
        
        Task:
        1. Identify the SINGLE most official website. Prioritize .gov.in or .nic.in domains.
        2. Identify the SINGLE most official syllabus PDF.
        3. Extract 'Official Conducting Body Name'. If not in scraped content, use your knowledge.
        4. Extract 'Frequency' (e.g. Annual, Twice a year). If not in scraped content, use your knowledge.
        5. Extract 'Registration Dates' or 'Latest Notification Date'. If unavailable, state the typical registration window from your knowledge (e.g. "Usually August–October").
        6. Determine 'Has_New_Update' (Boolean). Set to true if a notification or PDF was uploaded recently.
        7. Write a 2-3 sentence 'About Exam' summary covering: what the exam is for, who conducts it, and why students take it. Use your knowledge if the scraped content is insufficient.
        
        CRITICAL RULES:
        - Use your internal knowledge to fill gaps — do NOT output "Not Available" unless you truly have no information at all.
        - For fields like conducting_body and frequency, you almost always know these for major Indian exams.
        - If the websites are irrelevant to the exam, strictly return null for 'official_site' and 'syllabus_pdf'.
        
        Return ONLY valid JSON in this format:
        {{
            "official_site": {{"title": "...", "url": "...", "is_gov_domain": true/false}},
            "syllabus_pdf": {{"title": "...", "url": "..."}},
            "details": {{
                "conducting_body": "...",
                "frequency": "...",
                "registration_dates": "...",
                "about_exam": "...",
                "has_new_update": false
            }}
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
                
            data = json.loads(text)
            
            # Post-verification for is_gov_domain
            if data.get("official_site") and data["official_site"].get("url"):
                url = data["official_site"]["url"].lower()
                data["official_site"]["is_gov_domain"] = ".gov.in" in url or ".nic.in" in url
                
            return data
        except Exception as e:
            logger.error(f"[AuthorityService] Validation failed: {e}")
            return {
                "official_site": valid_sites[0] if valid_sites else None,
                "syllabus_pdf": valid_syllabi[0] if valid_syllabi else None,
                "details": {}
            }

    def get_authority_info(self, exam_name: str) -> Dict:
        logger.info(f"[AuthorityService] Fact-Checking official sources for {exam_name}")
        site_queries = get_official_site_query(exam_name)
        syllabus_queries = get_syllabus_queries(exam_name)
        
        site_results = search_bucket(site_queries, max_per_query=5)
        syllabus_results = search_bucket(syllabus_queries, max_per_query=5)
        
        return self.validate_and_extract(exam_name, site_results, syllabus_results)
