"""
Previous Year Papers Service: Collects, scores, and structures authentic question paper links.
Prioritizes direct PDF downloads, extracts exam years, and retains rich candidate collections.
"""

import re
from typing import List, Any, Dict, Optional

from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.utils.trust_scoring import get_domain_tier, calculate_relevance_score
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

_PAPER_KEYWORDS = re.compile(
    r"\b(paper|pyq|question|previous|year|solved|shift|answer\s*key|sample|mock|test\s*paper|exam\s*paper)\b",
    re.IGNORECASE,
)

_YEAR_REGEX = re.compile(r"\b(20[12][0-9])\b")


class PapersService:
    """
    Aggregates previous year paper links (PDF and web) from search results
    and optional PDF link extraction from pages.
    """

    def __init__(self, pdf_tool: Optional[PDFDownloaderTool] = None):
        self.pdf_tool = pdf_tool or PDFDownloaderTool()

    def _base_url(self, u: str) -> str:
        """Strip query parameters and trailing fragments for deduplication."""
        if not u:
            return ""
        return u.split("?")[0].split("#")[0].rstrip("/").lower()

    def _extract_year(self, text: str) -> str:
        """Extract primary 4-digit examination year from title or URL."""
        matches = _YEAR_REGEX.findall(text)
        if matches:
            return sorted(matches, reverse=True)[0]
        return "Recent"

    def from_search_results(
        self,
        search_results: List[Any],
        exam_name: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Build list of previous papers from search results with high recall.
        PDF links are prioritized; non-PDF links from educational portals are retained.
        """
        papers: List[Dict[str, Any]] = []
        seen_urls = set()

        clean_items = [
            r.__dict__ if hasattr(r, "__dict__") and not isinstance(r, dict) else r
            for r in search_results
        ]

        # 1. Extract and rank direct PDF links
        pdfs = self.pdf_tool.get_pdf_links_from_search_results(clean_items)

        for p in pdfs:
            url = p.get("url", "")
            base = self._base_url(url)
            if not base or base in seen_urls:
                continue

            tier, tier_label, _ = get_domain_tier(url)
            if tier == 4:
                continue  # Skip spam domains

            title = p.get("title", "Previous Year Question Paper (PDF)")
            year = self._extract_year(f"{title} {url}")

            seen_urls.add(base)
            papers.append({
                "title": title,
                "url": url,
                "type": "pdf",
                "year": year,
                "is_official": (tier == 1),
                "source": tier_label,
            })

        # 2. Add authenticated non-PDF links matching question papers
        for r in clean_items:
            url = r.get("url") or r.get("href") or r.get("link") or ""
            if not url or self.pdf_tool.is_pdf_url(url):
                continue

            base = self._base_url(url)
            if not base or base in seen_urls:
                continue

            tier, tier_label, _ = get_domain_tier(url)
            if tier == 4:
                continue

            title = r.get("title") or ""
            snippet = r.get("snippet") or ""
            combined_text = f"{title} {snippet} {url}"

            # Validate that the link is actually about question papers / PYQs
            if not _PAPER_KEYWORDS.search(combined_text):
                continue

            # Generous relevance check
            if exam_name:
                score = calculate_relevance_score(
                    title=title, url=url, snippet=snippet, exam_name=exam_name, resource_type="pyq"
                )
                if score < 10.0:  # Relaxed to ensure educational websites are preserved
                    continue

            year = self._extract_year(combined_text)
            seen_urls.add(base)

            clean_title = title.strip() or "Previous Year Paper & Solutions"
            if len(clean_title) > 180:
                clean_title = clean_title[:180] + "..."

            papers.append({
                "title": clean_title,
                "url": url,
                "type": "link",
                "year": year,
                "is_official": (tier == 1),
                "source": tier_label,
            })

        # Sort: Official Tier-1 direct PDFs first, then PDFs, then authenticated web links
        papers.sort(key=lambda x: (x.get("is_official", False), x.get("type") == "pdf"), reverse=True)
        return papers[:20]
