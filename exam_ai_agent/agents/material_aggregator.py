"""
Material Aggregator: Curates verified educational platforms, subject tutorials, and reference books.
Embraces established competitive examination learning platforms with high recall and structured output.
"""

import json
from typing import List, Dict, Any

from exam_ai_agent.tools.web_search import search_bucket, get_preparation_queries, get_books_queries
from exam_ai_agent.utils.common import (
    get_llm,
    strip_json_fences,
    invoke_llm_with_retry,
    check_url_alive,
    filter_alive_urls_concurrent,
)
from exam_ai_agent.utils.trust_scoring import filter_and_rank_resources
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

# Backward-compatibility aliases
_invoke_llm_with_retry = invoke_llm_with_retry
_strip_json_fences = strip_json_fences
_is_url_alive = check_url_alive


def _infer_study_category(title: str, snippet: str) -> str:
    """Classify study resources into meaningful preparation categories."""
    text = f"{title} {snippet}".lower()
    if any(k in text for k in ["mock", "test series", "quiz", "practice set", "question bank", "sample paper"]):
        return "Practice & Mock Tests"
    if any(k in text for k in ["topic", "subject", "algorithm", "formula", "notes", "tutorial", "chapter", "concept"]):
        return "Subject-wise Notes"
    return "Preparation Guides"


class MaterialAggregator:
    def __init__(self):
        self.llm = get_llm()

    def aggregate_materials(self, exam_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Searches for recognized academic platforms, subject tutorials, mock tests, and standard reference books.
        Returns {'edtech_links': [...], 'books': [...]}.
        """
        en = exam_name.strip()
        logger.info("[MaterialAggregator] Aggregating high-recall study materials for: %s", en)

        edtech_queries = get_preparation_queries(en)
        books_queries = get_books_queries(en)

        # Broad search queries
        edtech_results = search_bucket(edtech_queries, max_per_query=8, delay_between=0.15, exam_name=en, resource_type="resource")
        books_results = search_bucket(books_queries, max_per_query=8, delay_between=0.15, exam_name=en, resource_type="book")

        # Concurrently validate link health
        valid_edtech = filter_alive_urls_concurrent(edtech_results, max_workers=10, timeout=4)
        valid_books = filter_alive_urls_concurrent(books_results, max_workers=10, timeout=4)

        # High-recall ranking with relaxed threshold (10.0)
        ranked_edtech = filter_and_rank_resources(valid_edtech, exam_name=en, resource_type="resource", min_score=10.0, top_k=15)
        ranked_books = filter_and_rank_resources(valid_books, exam_name=en, resource_type="book", min_score=10.0, top_k=10)

        # Fallback if LLM is not configured
        if not self.llm:
            return {
                "edtech_links": [
                    {
                        "title": r.get("title", "Study Resource"),
                        "url": r.get("url"),
                        "platform": r.get("trust_label", "Educational Platform"),
                        "category": _infer_study_category(r.get("title", ""), r.get("snippet", "")),
                        "description": r.get("snippet", "Preparation guide and study material."),
                    }
                    for r in ranked_edtech[:12]
                ],
                "books": [
                    {
                        "title": r.get("title", "Recommended Reference Book"),
                        "url": r.get("url"),
                        "author": "Standard Academic Author",
                        "purpose": "Core Concept Theory & Practice",
                    }
                    for r in ranked_books[:8]
                ],
            }

        prompt = f"""
SYSTEM ROLE:
You are an expert academic curriculum and textbook curator for competitive examinations.

TASK:
Curate authentic learning platforms, subject-wise notes, and standard reference books specifically for: {en}.

CANDIDATE STUDY PLATFORMS:
{json.dumps(ranked_edtech[:14], indent=2)}

CANDIDATE BOOK SOURCES:
{json.dumps(ranked_books[:12], indent=2)}

INSTRUCTIONS:
1. Under "edtech_links": Curate 8-12 top recognized educational platforms and preparation resources 
   (e.g., GeeksforGeeks, PrepInsta, Testbook, NPTEL, Shiksha, Unacademy, Adda247, VisionIAS, etc.).
   Provide "title", "url", "platform" (name of organization/platform), and a concise "description" of what it offers.
2. Under "books": Curate 5-8 standard textbooks or recommended reference books mentioned.
   Provide "title", "author" (or "Standard Reference" if not specified), "url", and "purpose" (e.g. "Core Theory", "Practice Problems", "Revision").
3. DO NOT reject legitimate educational platforms simply because they are not .gov.in or .nic.in.
4. Output ONLY raw JSON matching the schema. No markdown code fences.

OUTPUT JSON SCHEMA:
{{
    "edtech_links": [
        {{"title": "...", "url": "...", "platform": "...", "category": "Preparation Guides | Subject-wise Notes | Practice & Mock Tests", "description": "..."}}
    ],
    "books": [
        {{"title": "...", "url": "...", "author": "...", "purpose": "..."}}
    ]
}}
"""

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            content = invoke_llm_with_retry(self.llm, [
                SystemMessage(content="You are a strict JSON generator. Output raw JSON only with no markdown code fences."),
                HumanMessage(content=prompt),
            ])
            if not content:
                raise ValueError("LLM returned empty response")

            cleaned = strip_json_fences(content)
            data = json.loads(cleaned)
            edtech = data.get("edtech_links", [])
            books = data.get("books", [])

            # Ensure category field exists on all items
            for e in edtech:
                if not e.get("category"):
                    e["category"] = _infer_study_category(e.get("title", ""), e.get("description", ""))

            return {
                "edtech_links": edtech if edtech else [
                    {
                        "title": r.get("title", "Study Material"),
                        "url": r.get("url"),
                        "platform": r.get("trust_label", "Educational Platform"),
                        "category": _infer_study_category(r.get("title", ""), r.get("snippet", "")),
                        "description": r.get("snippet", ""),
                    }
                    for r in ranked_edtech[:12]
                ],
                "books": books if books else [
                    {"title": r.get("title", "Reference Book"), "url": r.get("url"), "author": "Standard Author", "purpose": "Preparation"}
                    for r in ranked_books[:8]
                ],
            }

        except Exception as e:
            logger.warning("[MaterialAggregator] LLM processing note: %s. Using high-recall candidates.", e)
            return {
                "edtech_links": [
                    {
                        "title": r.get("title", "Study Resource"),
                        "url": r.get("url"),
                        "platform": r.get("trust_label", "Educational Platform"),
                        "category": _infer_study_category(r.get("title", ""), r.get("snippet", "")),
                        "description": r.get("snippet", "Preparation guide and study material."),
                    }
                    for r in ranked_edtech[:12]
                ],
                "books": [
                    {
                        "title": r.get("title", "Recommended Reference Book"),
                        "url": r.get("url"),
                        "author": "Standard Academic Author",
                        "purpose": "Subject Preparation",
                    }
                    for r in ranked_books[:8]
                ],
            }
