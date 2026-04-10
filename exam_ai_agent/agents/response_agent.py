"""
Response Agent: Formats and polishes research results.
Enforces strict deduplication, category isolation, and clean JSON structure.
Uses LLM to enrich PYQ metadata (year/stage) and categorise model papers.
"""

import os
import json
import datetime
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from exam_ai_agent.database.vector_store import VectorStore
from exam_ai_agent.services.syllabus_service import SyllabusService
from exam_ai_agent.services.papers_service import PapersService
from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)
CURRENT_YEAR = datetime.datetime.now().year


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
        model_papers_raw: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:

        logger.info("[ResponseAgent] Building final payload for: %s", exam_name)

        # -- 1. Seed result structure
        result: Dict[str, Any] = {
            "syllabus": [],
            "previous_papers": [],
            "model_papers": [],
            "important_topics": important_topics,
            "study_plan": study_plan,
            "resources": [],
            "youtube_lectures": [],
        }

        # -- 2. Syllabus (scraped wins, search fills gaps)
        search_syllabus = self.syllabus_service.extract_from_search_results(syllabus_results)
        result["syllabus"] = self.syllabus_service.merge_syllabus(
            search_syllabus, scraped_syllabus_items, exam_name
        )

        # -- 3. Previous Papers (deduped by base URL)
        seen_paper_urls: set = set()
        all_papers = self.papers_service.from_search_results(papers_results)
        for pdf in hidden_pdfs:
            base = self._base(pdf.get("url", ""))
            if base and base not in seen_paper_urls:
                all_papers.append(pdf)
                seen_paper_urls.add(base)

        result["previous_papers"] = self._dedup_by_url(all_papers)[:20]

        # -- 4. Model Papers / Mock Tests (deduplicated)
        if model_papers_raw:
            seen_mock_urls: set = set()
            for r in model_papers_raw:
                url   = getattr(r, "url",   "") or (r.get("url",   "") if isinstance(r, dict) else "")
                title = getattr(r, "title", "") or (r.get("title", "") if isinstance(r, dict) else "")
                if not url or not title:
                    continue
                # Exclude items already in previous_papers
                base = self._base(url)
                if base in seen_mock_urls:
                    continue
                seen_mock_urls.add(base)
                # Guess type from title/URL
                rtype = "full-length"
                if any(w in title.lower() for w in ["sectional", "subject", "topic"]):
                    rtype = "sectional"
                result["model_papers"].append({
                    "title": title[:300],
                    "url": url,
                    "type": rtype,
                    "source": self._domain(url),
                })
            result["model_papers"] = result["model_papers"][:10]

        # -- 5. Study resources (no YouTube, no duplicates)
        seen_res_urls: set = set()
        for r in study_results:
            url   = getattr(r, "url",   "") or (r.get("url",   "") if isinstance(r, dict) else "")
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

        # -- 6. YouTube (deduped by video ID)
        seen_yt: set = set()
        for r in youtube_results:
            url   = getattr(r, "url",   "") or (r.get("url",   "") if isinstance(r, dict) else "")
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

        # -- 7. LLM Resource Enrichment: annotate PYQs with year/stage + enrich model papers
        if self.llm and (result["previous_papers"] or result["model_papers"]):
            result = self._enrich_resources_with_llm(exam_name, result)

        # -- 8. Vector store
        if raw_text_chunks:
            try:
                clean_chunks = [b.strip() for t in raw_text_chunks for b in t.split("\n\n") if len(b.strip()) > 120]
                if clean_chunks:
                    self.vector_store.add_texts(clean_chunks[:60], exam_name=exam_name)
            except Exception as e:
                logger.warning("Vector store save failed: %s", e)

        # -- 9. LLM QA Polish: clean syllabus + validate study plan
        if self.llm:
            result = self._qa_polish(result)

        return result

    # ── LLM Resource Enrichment ───────────────────────────────────────────────
    def _enrich_resources_with_llm(self, exam_name: str, result: Dict) -> Dict:
        """
        Uses LLM to:
        1. Annotate PYQs with year and stage (Prelims/Mains/etc.)
        2. Classify model papers by type and difficulty
        3. Remove fake/spam links
        """
        try:
            from langchain_core.messages import SystemMessage, HumanMessage as HMsg

            papers_preview = json.dumps({
                "previous_papers": result["previous_papers"][:15],
                "model_papers":    result["model_papers"][:8],
            })

            system_msg = (
                f"You are a resource curator for {exam_name} ({CURRENT_YEAR}) exam preparation.\n\n"
                "Your task is to ENRICH and VALIDATE the resource lists provided.\n\n"
                "FOR PREVIOUS YEAR PAPERS (previous_papers):\n"
                "- Inspect each paper's title and URL.\n"
                "- Add 'year' field: extract exam year (e.g. '2023', '2022') from title/URL. "
                "If year is in the title like '2023', '2022', use it. Otherwise put 'Unknown'.\n"
                "- Add 'stage' field: identify exam stage — 'Prelims', 'Mains', 'CBT', 'Phase 1', "
                "'Phase 2', 'Paper 1', 'Paper 2', or 'General' if unspecified.\n"
                "- Keep 'title', 'url', 'type' fields unchanged.\n"
                "- REMOVE entries where title/URL look like spam, clickbait, generic blogs, or "
                "are clearly unrelated to the exam.\n"
                "- Prefer entries from official bodies, govt portals, or trusted education sites.\n\n"
                "FOR MODEL PAPERS (model_papers):\n"
                "- Keep 'title', 'url', 'source', 'type' fields.\n"
                "- Add 'description': one-line description of what the mock/model paper covers.\n"
                "- Set 'difficulty': 'Easy', 'Medium', or 'Hard' based on source (official=Medium, "
                "coaching=Hard, beginner sites=Easy). Guess reasonably.\n"
                "- REMOVE clear spam or unrelated entries.\n\n"
                "QUALITY RULES:\n"
                "- Never fabricate URLs or data.\n"
                "- If a field value cannot be determined, use 'Unknown' or 'General'.\n"
                "- Return ONLY raw JSON with keys: previous_papers, model_papers\n"
                "- No markdown, no explanation."
            )

            res = self.llm.invoke([
                SystemMessage(content=system_msg),
                HMsg(content=papers_preview)
            ])
            text = res.content.strip()
            # Robust JSON extraction
            s = text.find("{")
            e = text.rfind("}") + 1
            if s != -1 and e > s:
                text = text[s:e]
            enriched = json.loads(text)
            if "previous_papers" in enriched:
                result["previous_papers"] = enriched["previous_papers"][:20]
            if "model_papers" in enriched:
                result["model_papers"] = enriched["model_papers"][:10]
            logger.info("[ResponseAgent] Resource enrichment successful.")
        except Exception as e:
            logger.warning("[ResponseAgent] Resource enrichment failed: %s. Using raw data.", e)

        return result

    # ── LLM QA Polish ─────────────────────────────────────────────────────────
    def _qa_polish(self, result: Dict) -> Dict:
        """Final LLM pass to clean syllabus and study plan."""
        try:
            from langchain_core.messages import SystemMessage, HumanMessage as HMsg

            # Only send syllabus + study_plan to save tokens (resources already enriched)
            polish_payload = {
                "syllabus":       result.get("syllabus", []),
                "important_topics": result.get("important_topics", []),
                "study_plan":     result.get("study_plan", []),
                "resources":      result.get("resources", []),
                "youtube_lectures": result.get("youtube_lectures", []),
                "previous_papers": result.get("previous_papers", []),
            }

            system_msg = (
                "You are a Quality Assurance Editor for an elite academic exam preparation platform.\n"
                "Perform a FINAL AUDIT of the exam data provided. Return ONLY cleaned, validated JSON.\n\n"
                "AUDIT RULES:\n"
                "1. SYLLABUS — Verify each entry is a genuine academic subject/topic.\n"
                "   REMOVE from subtopics ONLY: eligibility, fees, dates, registration, admit card, "
                "results, cut-offs, login, notifications, apply online, official website, counselling.\n"
                "   PRESERVE: all academic concepts, theory topics, subtopics, formulas, named theorems.\n"
                "   Every entry must have 'topic' (string) and 'subtopics' (list of strings).\n"
                "2. STUDY PLAN — Validate each item has: order (int), phase (str), topic (str), "
                "subtopics (str), duration (str), tip (str).\n"
                "   Valid phases: 'Phase 1 — Foundations', 'Phase 2 — Core Concepts', "
                "'Phase 3 — Advanced Topics', 'Phase 4 — Revision & Mocks'.\n"
                "   PRESERVE specific tips — do NOT replace actionable, exam-specific tips with generic ones.\n"
                "   REMOVE a tip only if it contains admin/spam content.\n"
                "3. DEDUPLICATION — Each URL must appear in at most ONE section. Remove broken/spam links.\n"
                "4. RESOURCES — Professional title-case titles. YouTube links ONLY in youtube_lectures.\n"
                "5. NO FABRICATION — Never invent URLs, resource titles, or topic names.\n"
                "6. FORBIDDEN TOP-LEVEL KEYS — Do NOT output: about_exam, exam_fees, registration, eligibility.\n"
                "7. PRESERVE CONTENT — Do NOT shrink the syllabus or drop study plan items. "
                "If unsure about a topic, keep it as-is rather than deleting it.\n\n"
                "Return ONLY valid raw JSON with exactly these keys:\n"
                "syllabus, previous_papers, important_topics, study_plan, resources, youtube_lectures\n"
                "No markdown fences. No commentary. Raw JSON only."
            )

            res = self.llm.invoke([
                SystemMessage(content=system_msg),
                HMsg(content=json.dumps(polish_payload))
            ])
            text = res.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            s = text.find("{")
            e = text.rfind("}") + 1
            if s != -1 and e > s:
                text = text[s:e]
            parsed = json.loads(text)
            logger.info("[ResponseAgent] QA polish successful.")
            # Merge polished fields back, keep model_papers untouched
            for key in ("syllabus", "previous_papers", "important_topics",
                        "study_plan", "resources", "youtube_lectures"):
                if key in parsed:
                    result[key] = parsed[key]
        except Exception as e:
            logger.warning("[ResponseAgent] QA polish failed: %s. Returning raw result.", e)

        return result

    # -- Helpers
    @staticmethod
    def _base(url: str) -> str:
        return url.split("?")[0].split("#")[0].rstrip("/") if url else ""

    @staticmethod
    def _domain(url: str) -> str:
        """Extract domain name from URL for source field."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return ""

    @staticmethod
    def _dedup_by_url(items: List[Dict]) -> List[Dict]:
        seen, out = set(), []
        for item in items:
            base = (item.get("url", "").split("?")[0].split("#")[0].rstrip("/"))
            if base and base not in seen:
                seen.add(base)
                out.append(item)
        return out
