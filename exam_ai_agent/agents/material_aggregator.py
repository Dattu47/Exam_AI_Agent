"""
Material Aggregator: Curates verified educational platforms, reference books, and prep materials.
Concurrently checks link health and extracts high-accuracy resources with Gemini LLM.
"""

import json
from typing import List, Dict, Any

from exam_ai_agent.tools.web_search import search_bucket
from exam_ai_agent.utils.common import (
    get_llm,
    strip_json_fences,
    invoke_llm_with_retry,
    check_url_alive,
    filter_alive_urls_concurrent,
)
from exam_ai_agent.utils.trust_scoring import filter_and_rank_resources, get_domain_tier
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

# Backward-compatibility aliases
_invoke_llm_with_retry = invoke_llm_with_retry
_strip_json_fences = strip_json_fences
_is_url_alive = check_url_alive


class MaterialAggregator:
    def __init__(self):
        self.llm = get_llm()

    def aggregate_materials(self, exam_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Searches for recognized academic platforms, government sources, and standard reference books.
        Returns {'edtech_links': [...], 'books': [...]}.
        """
        en = exam_name.strip()
        logger.info("[MaterialAggregator] Searching verified materials for: %s", en)

        edtech_sites = (
            "site:nptel.ac.in OR site:shiksha.com OR site:careers360.com OR site:testbook.com "
            "OR site:pw.live OR site:unacademy.com OR site:visionias.in OR site:drishtiias.com "
            "OR site:gateoverflow.in OR site:geeksforgeeks.org"
        )
        gov_sites = (
            "site:ncert.nic.in OR site:pib.gov.in OR site:ugc.ac.in OR site:mhrd.gov.in"
        )

        edtech_queries = [
            f"{en} syllabus preparation study notes {edtech_sites}",
            f"{en} mock test series curriculum {edtech_sites}",
        ]
        books_queries = [
            f"{en} standard reference books list toppers recommendation",
            f"{en} recommended textbooks {gov_sites} OR site:nptel.ac.in",
        ]

        edtech_results = search_bucket(edtech_queries, max_per_query=6, delay_between=0.2, exam_name=en, resource_type="book")
        books_results = search_bucket(books_queries, max_per_query=6, delay_between=0.2, exam_name=en, resource_type="book")

        # Concurrently validate link health
        valid_edtech = filter_alive_urls_concurrent(edtech_results, max_workers=8, timeout=4)
        valid_books = filter_alive_urls_concurrent(books_results, max_workers=8, timeout=4)

        # Early relevance ranking
        ranked_edtech = filter_and_rank_resources(valid_edtech, exam_name=en, resource_type="book", min_score=20.0, top_k=6)
        ranked_books = filter_and_rank_resources(valid_books, exam_name=en, resource_type="book", min_score=20.0, top_k=6)

        if not self.llm:
            return {
                "edtech_links": [
                    {"title": r.get("title", "Educational Portal"), "url": r.get("url"), "platform": "Verified Platform", "description": r.get("snippet", "")}
                    for r in ranked_edtech[:5]
                ],
                "books": [
                    {"title": r.get("title", "Standard Textbook"), "url": r.get("url"), "author": "Standard Author", "purpose": "Exam Preparation"}
                    for r in ranked_books[:5]
                ],
            }

        prompt = f"""
SYSTEM ROLE:
You are an expert academic curriculum and textbook curator for competitive exams.

TASK:
Curate verified learning platforms and standard reference books specifically for: {en}.

CANDIDATE PLATFORMS:
{json.dumps(ranked_edtech[:10], indent=2)}

CANDIDATE BOOK SOURCES:
{json.dumps(ranked_books[:10], indent=2)}

INSTRUCTIONS:
1. Under "edtech_links": Extract up to 5 top recognized educational platforms (e.g. NPTEL, Shiksha, Testbook, PW, VisionIAS).
   Provide "title", "url", "platform" (name of organization), and a brief "description" of what it offers.
2. Under "books": Extract up to 5 recognized standard textbooks or recommended reference books mentioned.
   Provide "title", "author" (or "Standard Reference" if not specified), "url", and "purpose" (e.g. "Theory Foundation", "Practice Problems").
3. Only include resources genuinely relevant to "{en}". Do not fabricate links.
4. Output ONLY raw JSON matching the schema. No markdown fences.

OUTPUT JSON SCHEMA:
{{
    "edtech_links": [
        {{"title": "...", "url": "...", "platform": "...", "description": "..."}}
    ],
    "books": [
        {{"title": "...", "url": "...", "author": "...", "purpose": "..."}}
    ]
}}
"""

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            content = invoke_llm_with_retry(self.llm, [
                SystemMessage(content="You are a strict JSON generator. Output raw JSON only."),
                HumanMessage(content=prompt),
            ])
            if not content:
                raise ValueError("LLM returned empty response")

            cleaned = strip_json_fences(content)
            data = json.loads(cleaned)
            return {
                "edtech_links": data.get("edtech_links", ranked_edtech[:5]),
                "books": data.get("books", ranked_books[:5]),
            }

        except Exception as e:
            logger.warning("[MaterialAggregator] LLM processing notice: %s. Using ranked candidates.", e)
            return {
                "edtech_links": [
                    {"title": r.get("title", "Educational Resource"), "url": r.get("url"), "platform": "Academic Portal", "description": r.get("snippet", "")}
                    for r in ranked_edtech[:5]
                ],
                "books": [
                    {"title": r.get("title", "Reference Resource"), "url": r.get("url"), "author": "Standard Reference", "purpose": "Subject Preparation"}
                    for r in ranked_books[:5]
                ],
            }
