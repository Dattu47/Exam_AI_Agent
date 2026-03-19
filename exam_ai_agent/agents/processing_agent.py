"""
Processing Agent: Deep extraction of syllabus from scraped pages.
Uses multi-source aggregation + LLM for structured, accurate syllabus generation.
"""

import os
import json
import datetime
from typing import List, Dict, Any, Tuple
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from exam_ai_agent.services.syllabus_service import SyllabusService
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

CURRENT_YEAR = datetime.datetime.now().year


def _get_groq_api_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


class ProcessingAgent:
    def __init__(self, syllabus_service: SyllabusService = None):
        self.syllabus_service = syllabus_service or SyllabusService()
        api_key = _get_groq_api_key()
        if api_key:
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.1,
            )
        else:
            logger.warning("[ProcessingAgent] Missing GROQ_API_KEY.")
            self.llm = None

    def extract_and_process(
        self,
        exam_name: str,
        scraped_pages: List[Dict[str, Any]],
        syllabus_urls: List[str],
        pattern_results: List[Any],
    ) -> Tuple[List[Dict], List[str], List[str]]:
        """
        Deep extraction pipeline:
          1. Extract raw topics from ALL syllabus pages (not just the best one).
          2. Aggregate multi-source topics, deduplicate by key.
          3. Use LLM to deeply structure and enrich the syllabus.
          4. Return: (syllabus_items, important_topics, text_chunks)
        """
        logger.info("[ProcessingAgent] Deep processing for %s (%s)", exam_name, CURRENT_YEAR)

        all_text_chunks: List[str] = []
        raw_items_pool: List[Dict] = []   # all topics from all pages
        seen_topic_keys: set = set()

        # ── Step 1: Multi-source extraction ───────────────────────────────────
        for page in scraped_pages:
            text = page.get("text", "")
            html = page.get("html", "")
            url  = page.get("url", "")

            if text:
                all_text_chunks.append(text[:6000])

            # Only extract syllabus from targeted pages
            if url not in syllabus_urls:
                continue

            # Try HTML first (richest structure), fall back to text
            extracted = self.syllabus_service.extract_from_html(html, url) if html else []
            if len(extracted) < 3:
                extracted = self.syllabus_service.extract_from_text(text, url)

            for item in extracted:
                key = item.get("topic", "").strip().lower()
                if not key or key in seen_topic_keys:
                    continue
                seen_topic_keys.add(key)
                raw_items_pool.append({
                    "topic":     item.get("topic", "").strip(),
                    "subtopics": item.get("subtopics", []),
                    "source_url": url,
                })

        logger.info("[ProcessingAgent] Raw pool after multi-source extraction: %d items", len(raw_items_pool))

        # ── Step 2: LLM Deep Structuring ──────────────────────────────────────
        final_syllabus: List[Dict] = []
        important_topics: List[str] = []

        if self.llm:
            try:
                raw_json = json.dumps(
                    [{"topic": x["topic"], "subtopics": x["subtopics"]} for x in raw_items_pool[:60]]
                )
                # Also include raw text snippets so LLM can fill gaps
                text_context = " | ".join([c[:500] for c in all_text_chunks[:5]])

                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     f"You are an expert academic researcher specializing in competitive exam syllabi for {CURRENT_YEAR}.\n"
                     "Your task: Generate the COMPLETE, ACCURATE, OFFICIAL syllabus for the given exam.\n"
                     "STRICT RULES:\n"
                     f"1. Use your knowledge of {exam_name} PLUS the extracted content to produce the FULL official syllabus.\n"
                     "2. Output ONLY valid JSON — no markdown, no explanation.\n"
                     "3. Format:\n"
                     '   {"syllabus": [{"topic": "Topic Name", "subtopics": ["Sub 1", "Sub 2", ...]}, ...], '
                     '"important_topics": ["Topic A", "Topic B", ...]}\n'
                     "4. Each topic must have AT LEAST 3 specific subtopics (not generic).\n"
                     "5. Do NOT include: dates, deadlines, application info, exam fees, eligibility.\n"
                     "6. Only REAL syllabus topics — subjects, chapters, concepts.\n"
                     "7. Cover ALL sections of the exam properly.\n"
                     "8. 'important_topics' = list of 10-15 highest-weightage topic names only (strings)."
                    ),
                    ("human",
                     f"Exam: {exam_name} ({CURRENT_YEAR})\n\n"
                     f"Extracted raw topics: {raw_json}\n\n"
                     f"Additional context from scraped pages: {text_context}")
                ])
                chain = prompt | self.llm
                res = chain.invoke({})
                text = res.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                parsed = json.loads(text)

                for item in parsed.get("syllabus", []):
                    t = str(item.get("topic", "")).strip()
                    if not t:
                        continue
                    final_syllabus.append({
                        "topic":     t,
                        "subtopics": [str(s) for s in item.get("subtopics", []) if s],
                        "source_url": "",
                    })

                important_topics = [
                    str(t).strip() for t in parsed.get("important_topics", []) if t
                ][:20]

                logger.info(
                    "[ProcessingAgent] LLM produced %d syllabus topics, %d important topics.",
                    len(final_syllabus), len(important_topics)
                )

            except Exception as e:
                logger.warning("[ProcessingAgent] LLM structuring failed: %s — using raw pool.", e)
                final_syllabus = raw_items_pool[:40]
                important_topics = [x["topic"] for x in raw_items_pool[:15]]

        else:
            # Fallback: use raw extracted pool directly
            final_syllabus = raw_items_pool[:40]
            important_topics = [x["topic"] for x in raw_items_pool[:15]]

        return final_syllabus, important_topics, all_text_chunks
