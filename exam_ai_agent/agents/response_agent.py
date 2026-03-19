"""
Response Agent: Formats and polishes research results.
Enforces strict deduplication, category isolation, and clean JSON structure.
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
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


class ResponseAgent:
    def __init__(self, vector_store=None, syllabus_service=None, papers_service=None):
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
        scraped_syllabus_items: List[Dict],
        important_topics: List[str],
        study_plan: List[Dict],
        hidden_pdfs: List[Dict],
        raw_text_chunks: List[str],
    ) -> Dict[str, Any]:

        logger.info("[ResponseAgent] Building final payload for: %s", exam_name)

        # ── 1. Seed result structure ──────────────────────────────────────────
        result: Dict[str, Any] = {
            "about_exam": {"description": "", "deadline": "Check Official Site"},
            "syllabus": [],
            "previous_papers": [],
            "important_topics": important_topics,
            "study_plan": study_plan,
            "resources": [],
            "youtube_lectures": [],
        }

        # ── 2. Exam overview from info bucket ────────────────────────────────
        snippets = []
        for r in info_results:
            s = getattr(r, "snippet", "") or (r.get("snippet", "") if isinstance(r, dict) else "")
            if s:
                snippets.append(s)
        result["about_exam"]["description"] = " ".join(snippets[:4]).strip()

        # ── 3. Syllabus (scraped wins, search fills gaps) ────────────────────
        search_syllabus = self.syllabus_service.extract_from_search_results(syllabus_results)
        result["syllabus"] = self.syllabus_service.merge_syllabus(
            search_syllabus, scraped_syllabus_items, exam_name
        )

        # ── 4. Previous Papers (deduped by base URL) ─────────────────────────
        seen_paper_urls: set = set()
        all_papers = self.papers_service.from_search_results(papers_results)
        for pdf in hidden_pdfs:
            base = self._base(pdf.get("url", ""))
            if base and base not in seen_paper_urls:
                all_papers.append(pdf)
                seen_paper_urls.add(base)

        result["previous_papers"] = self._dedup_by_url(all_papers)[:20]

        # ── 5. Study resources (no YouTube, no duplicates) ───────────────────
        seen_res_urls: set = set()
        for r in study_results:
            url = getattr(r, "url", "") or (r.get("url", "") if isinstance(r, dict) else "")
            title = getattr(r, "title", "") or (r.get("title", "") if isinstance(r, dict) else "")
            if not url or not title:
                continue
            if "youtube.com" in url or "youtu.be" in url:
                continue
            base = self._base(url)
            if base in seen_res_urls:
                continue
            seen_res_urls.add(base)
            result["resources"].append({"title": title[:300], "url": url, "type": "link"})

        result["resources"] = result["resources"][:12]

        # ── 6. YouTube (deduped by video ID) ─────────────────────────────────
        seen_yt: set = set()
        for r in youtube_results:
            url = getattr(r, "url", "") or (r.get("url", "") if isinstance(r, dict) else "")
            title = getattr(r, "title", "") or (r.get("title", "") if isinstance(r, dict) else "")
            if not url or not title:
                continue
            if "youtube.com" not in url and "youtu.be" not in url:
                continue
            vid_key = url.split("&")[0].strip("/")
            if vid_key in seen_yt:
                continue
            seen_yt.add(vid_key)
            result["youtube_lectures"].append({"title": title[:300], "url": url})

        result["youtube_lectures"] = result["youtube_lectures"][:10]

        # ── 7. Vector store ───────────────────────────────────────────────────
        if raw_text_chunks:
            try:
                clean_chunks = [b.strip() for t in raw_text_chunks for b in t.split("\n\n") if len(b.strip()) > 120]
                if clean_chunks:
                    self.vector_store.add_texts(clean_chunks[:60], exam_name=exam_name)
            except Exception as e:
                logger.warning("Vector store save failed: %s", e)

        # ── 8. LLM polish: clean syllabus, extract deadline, dedup ───────────
        if self.llm:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "You are a precise academic JSON formatter for an exam preparation platform.\n"
                     "RULES (STRICT):\n"
                     "1. Output ONLY valid JSON, no markdown fences.\n"
                     "2. Keep exactly these keys: about_exam, syllabus, previous_papers, important_topics, study_plan, resources, youtube_lectures.\n"
                     "3. 'about_exam': {'description': <2-3 sentence exam overview in English>, 'deadline': <application/registration deadline or 'Check Official Site'>}.\n"
                     "4. 'syllabus': list of {topic: string, subtopics: [string]}. ONLY real syllabus topics. No generic words.\n"
                     "5. Global dedup: remove any URL appearing in more than one section — keep it only in the MOST relevant section.\n"
                     "6. YouTube links ONLY in 'youtube_lectures'. Remove from resources/papers if present.\n"
                     "7. Do NOT invent content. Only clean and restructure what is given."),
                    ("human", "{data}")
                ])
                chain = prompt | self.llm
                res = chain.invoke({"data": json.dumps(result)})
                text = res.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                parsed = json.loads(text)
                logger.info("[ResponseAgent] LLM polish successful.")
                return parsed
            except Exception as e:
                logger.warning("[ResponseAgent] LLM polish failed: %s. Returning raw result.", e)

        return result

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _base(url: str) -> str:
        return url.split("?")[0].split("#")[0].rstrip("/") if url else ""

    @staticmethod
    def _dedup_by_url(items: List[Dict]) -> List[Dict]:
        seen, out = set(), []
        for item in items:
            base = (item.get("url", "").split("?")[0].split("#")[0].rstrip("/"))
            if base and base not in seen:
                seen.add(base)
                out.append(item)
        return out
