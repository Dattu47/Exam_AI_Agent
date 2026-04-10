"""
Processing Agent: Deep extraction of syllabus from scraped pages.
Uses multi-source aggregation + LLM for structured, accurate syllabus generation.
"""

import os
import json
import datetime
import re
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

                # Build prompt as plain string to avoid LangChain brace-escaping issues
                system_msg = (
                    f"You are a Senior Academic Research Specialist with deep expertise in {exam_name} "
                    f"and Indian/global competitive examinations.\n\n"
                    "YOUR MISSION: Extract and validate the COMPLETE, OFFICIAL syllabus for this exam.\n\n"
                    "SOURCE PRIORITY (use in this order):\n"
                    "  1. Official exam website / conducting body\n"
                    "  2. Official notification PDF\n"
                    "  3. Government / conducting authority documents\n"
                    "  4. Scraped data provided below (cross-validate, do not blindly trust)\n\n"
                    "STRICT ACCURACY RULES:\n"
                    "1. NO HALLUCINATION — Every topic MUST exist in the real official syllabus. "
                    "If a topic from scraped data looks incorrect, replace it with the correct official topic. "
                    "If a subject/topic is genuinely uncertain, still include it but note it is 'Not explicitly confirmed'.\n"
                    "2. HIERARCHICAL STRUCTURE — Organise as: Subject → Topic → Subtopics. "
                    "Each 'topic' field should be the subject name (e.g., Mathematics, English Language, "
                    "Reasoning Ability, General Awareness, Computer Knowledge, etc.). "
                    "Subtopics must be the specific chapters/concepts within that subject.\n"
                    "3. GRANULAR SUBTOPICS — Each subject must have 6-15 precise, named subtopics. "
                    "BAD: 'Algebra' | GOOD: 'Quadratic Equations, Polynomials, Linear Equations, Inequalities'\n"
                    "4. COMPLETENESS — Include ALL subjects from the exam. "
                    "For Bank/SSC exams: English, Reasoning, Quant, GA, Computer. "
                    "For Engineering exams: all technical subjects. "
                    "For Civil Services: all GS papers + optional subjects structure.\n"
                    "5. ZERO ADMINISTRATIVE CLUTTER — Subtopics must be ONLY academic/conceptual content. "
                    "NEVER include: fees, eligibility, registration, dates, admit card, results, "
                    "cut-offs, login, notifications, how to apply, official website, counselling.\n"
                    "6. EXAM PATTERN AWARENESS — If you know the exam has Prelims + Mains or multiple papers, "
                    "separate them in the syllabus (e.g., 'Mathematics (Prelims)', 'Mathematics (Mains)').\n"
                    "7. HIGH-WEIGHTAGE TOPICS — Identify the 15-20 most frequently asked / highest-weightage "
                    "topics based on official pattern and previous years.\n\n"
                    "OUTPUT FORMAT — Raw JSON only, no markdown, no HTML tags, no asterisks:\n"
                    '{"syllabus": [{"topic": "Subject Name", "subtopics": ["Concept 1", "Concept 2", "Concept 3"]}], '
                    '"important_topics": ["High-weightage topic 1", "High-weightage topic 2"], '
                    '"confidence_level": "high/medium/low", '
                    '"notes": "Any discrepancies or uncertainties noted"}'
                )
                human_msg = (
                    f"EXAM: {exam_name} ({CURRENT_YEAR})\n\n"
                    f"SCRAPED SYLLABUS DATA (cross-validate this):\n{raw_json}\n\n"
                    f"ADDITIONAL SCRAPED CONTEXT:\n{text_context}\n\n"
                    "Instructions:\n"
                    "- Compare the scraped data against your authoritative knowledge of this exam.\n"
                    "- Correct any wrong topics. Fill gaps with official topics you know.\n"
                    "- If scraped data is poor/empty, generate the syllabus from your own knowledge.\n"
                    "- Return the complete, validated, structured syllabus JSON now."
                )
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=human_msg)])
                text = res.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                # Extract JSON from response robustly
                start = text.find("{")
                end   = text.rfind("}") + 1
                if start != -1 and end > start:
                    text = text[start:end]
                parsed = json.loads(text)

                for item in parsed.get("syllabus", []):
                    t = re.sub(r'<[^>]*>', '', str(item.get("topic", ""))).strip()
                    if not t:
                        continue
                    clean_subs = [re.sub(r'<[^>]*>', '', str(s)).replace('*', '').strip() for s in item.get("subtopics", []) if s]
                    final_syllabus.append({
                        "topic":     t,
                        "subtopics": [s for s in clean_subs if s],
                        "source_url": "",
                    })

                important_topics = [
                    re.sub(r'<[^>]*>', '', str(t)).strip() for t in parsed.get("important_topics", []) if t
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
