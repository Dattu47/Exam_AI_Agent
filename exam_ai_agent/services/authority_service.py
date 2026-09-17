"""
Authority Service: Verifies official websites, syllabus documents, and exam authority facts.
Prioritizes Tier-1 government (.gov.in, .nic.in, .ac.in) domains, performs concurrent liveness
checks, and uses structured Gemini LLM prompts for authoritative fact extraction.
"""

import re
import json
import urllib3
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

from exam_ai_agent.config import settings
from exam_ai_agent.tools.web_search import search_bucket, get_official_site_query, get_syllabus_queries
from exam_ai_agent.utils.common import (
    get_llm,
    strip_json_fences,
    invoke_llm_with_retry,
    check_url_alive,
    filter_alive_urls_concurrent,
)
from exam_ai_agent.utils.trust_scoring import get_domain_tier, filter_and_rank_resources
from exam_ai_agent.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class AuthorityService:
    def __init__(self):
        self.llm = get_llm()

    def _scrape_text(self, url: str, max_chars: int = 3500) -> str:
        """Fetch and return plain text from a URL for LLM context."""
        if not url:
            return ""
        try:
            resp = requests.get(
                url,
                timeout=8,
                headers={"User-Agent": settings.USER_AGENT},
                verify=False,
            )
            if resp.status_code >= 400:
                return ""
            try:
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception:
                soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = re.sub(r"\s+", " ", soup.get_text(separator=" "))
            return text[:max_chars].strip()
        except Exception as e:
            logger.debug("Scrape failed for authority URL %s: %s", url[:60], e)
            return ""

    def validate_and_extract(
        self,
        exam_name: str,
        site_results: List[Dict],
        syllabus_results: List[Dict],
    ) -> Dict:
        """
        Validates official sources and extracts structured metadata via LLM.
        Prioritizes Tier-1 government (.gov.in, .nic.in, .ac.in) domains.
        """
        en = exam_name.strip()
        slug = en.lower().replace(" ", "").replace("-", "")

        # ── 1. Heuristic Official URL Probing ──────────────────────────────────
        heuristic_urls = [
            f"https://{slug}.nic.in",
            f"https://{slug}.gov.in",
            f"https://{slug}.in",
            f"https://www.{slug}.ac.in",
        ]

        candidates_to_check = []
        for h_url in heuristic_urls:
            candidates_to_check.append({
                "title": f"{en.upper()} Official Portal",
                "url": h_url,
                "snippet": "Official government examination portal.",
            })
        for s in site_results:
            if s.get("url"):
                candidates_to_check.append(s)

        # Concurrently validate site and syllabus URLs in parallel
        valid_sites_raw = filter_alive_urls_concurrent(candidates_to_check, max_workers=10, timeout=4)
        valid_syllabi_raw = filter_alive_urls_concurrent(syllabus_results, max_workers=8, timeout=4)

        # Apply deterministic trust tiering & relevance ranking
        ranked_sites = filter_and_rank_resources(
            valid_sites_raw, exam_name=en, resource_type="authority", min_score=15.0, top_k=8
        )
        ranked_syllabi = filter_and_rank_resources(
            valid_syllabi_raw, exam_name=en, resource_type="syllabus", min_score=15.0, top_k=6
        )

        # Prioritize Tier-1 (.gov/.nic/.ac) in site candidates
        tier1_sites = [s for s in ranked_sites if s.get("is_official")]
        other_sites = [s for s in ranked_sites if not s.get("is_official")]
        final_sites = (tier1_sites + other_sites)[:6]

        tier1_syl = [s for s in ranked_syllabi if s.get("is_official")]
        other_syl = [s for s in ranked_syllabi if not s.get("is_official")]
        final_syllabi = (tier1_syl + other_syl)[:6]

        # ── 2. Fallback if no LLM or no sites ──────────────────────────────────
        if not self.llm or not final_sites:
            primary_site = final_sites[0] if final_sites else None
            if primary_site and primary_site.get("url"):
                tier, _, _ = get_domain_tier(primary_site["url"])
                primary_site["is_gov_domain"] = (tier == 1)

            return {
                "official_site": primary_site,
                "syllabus_pdf": final_syllabi[0] if final_syllabi else None,
                "details": {
                    "conducting_body": f"{en} Official Authority",
                    "frequency": "Annual",
                    "registration_dates": "Check official portal",
                    "about_exam": f"National or state-level examination for {en}.",
                    "has_new_update": False,
                },
            }

        # ── 3. Rich Scraped Context for LLM ───────────────────────────────────
        best_site_url = final_sites[0]["url"]
        scraped_content = self._scrape_text(best_site_url, max_chars=3000)

        # Fallback educational portal context
        fallback_queries = [
            f"{en} exam conducting body eligibility overview site:careers360.com OR site:shiksha.com"
        ]
        fallback_results = search_bucket(fallback_queries, max_per_query=2, delay_between=0.1)
        fallback_text = ""
        for fr in fallback_results[:1]:
            ft = self._scrape_text(fr.get("url", ""), max_chars=1200)
            if ft:
                fallback_text = ft
                break

        combined_content = (scraped_content + "\n\n" + fallback_text).strip()

        # Hardened LLM prompt with strict role and schema constraints
        prompt = f"""
SYSTEM ROLE:
You are the Official Fact-Checker for competitive examinations.

TASK:
Identify the single most official portal, authenticated syllabus document, and factual metadata for: {en}.

CANDIDATE WEBSITES (Top ranked):
{json.dumps(final_sites[:5], indent=2)}

CANDIDATE SYLLABUS DOCUMENTS:
{json.dumps(final_syllabi[:5], indent=2)}

SCRAPED CONTENT FROM PRIMARY SOURCES:
{combined_content[:3500]}

CONSTRAINTS & RULES:
1. Identify the SINGLE most official website. Prioritize .gov.in, .nic.in, or .ac.in domains.
2. Identify the SINGLE most authentic syllabus PDF or document URL.
3. Extract 'conducting_body': Specific organization name (e.g. UPSC, NTA, IIT, State PSC).
4. Extract 'frequency': E.g. "Annual", "Twice a year", "As announced".
5. Extract 'registration_dates': Expected or actual application window (e.g. "Usually Aug–Oct").
6. Determine 'has_new_update': true if recent notification/admit card/results are live, else false.
7. Write a 2-3 sentence 'about_exam' explaining purpose, conducting body, and candidate eligibility.
8. Output ONLY valid JSON matching this exact schema. No markdown code blocks, no trailing comments.

OUTPUT JSON SCHEMA:
{{
    "official_site": {{"title": "...", "url": "...", "is_gov_domain": true}},
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
            content = invoke_llm_with_retry(self.llm, [
                SystemMessage(content="You are a strict JSON generator. Output raw JSON only with no formatting code fences."),
                HumanMessage(content=prompt),
            ])
            if not content:
                raise ValueError("LLM returned empty response")

            cleaned_json = strip_json_fences(content)
            data = json.loads(cleaned_json)

            # Post-verify is_gov_domain with deterministic domain tiering
            if data.get("official_site") and data["official_site"].get("url"):
                tier, _, _ = get_domain_tier(data["official_site"]["url"])
                data["official_site"]["is_gov_domain"] = (tier == 1)

            return data

        except Exception as e:
            logger.warning("[AuthorityService] LLM parsing failed: %s. Using ranked fallback.", e)
            primary_site = final_sites[0] if final_sites else None
            if primary_site and primary_site.get("url"):
                tier, _, _ = get_domain_tier(primary_site["url"])
                primary_site["is_gov_domain"] = (tier == 1)

            return {
                "official_site": primary_site,
                "syllabus_pdf": final_syllabi[0] if final_syllabi else None,
                "details": {
                    "conducting_body": f"{en} Examination Body",
                    "frequency": "Annual",
                    "registration_dates": "Refer to official portal",
                    "about_exam": f"Competitive examination for {en}.",
                    "has_new_update": False,
                },
            }

    def get_authority_info(self, exam_name: str) -> Dict:
        """Fetch and verify official information for an exam."""
        logger.info("[AuthorityService] Verifying official authority for: %s", exam_name)
        site_queries = get_official_site_query(exam_name)
        syllabus_queries = get_syllabus_queries(exam_name)

        site_results = search_bucket(site_queries, max_per_query=4, delay_between=0.2, exam_name=exam_name, resource_type="authority")
        syllabus_results = search_bucket(syllabus_queries, max_per_query=4, delay_between=0.2, exam_name=exam_name, resource_type="syllabus")

        return self.validate_and_extract(exam_name, site_results, syllabus_results)
