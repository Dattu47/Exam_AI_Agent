"""
Previous year papers service: collects and structures
question paper links and metadata from search and PDF discovery.
"""

from typing import List, Any

from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class PapersService:
    """
    Aggregates previous year paper links (PDF and web) from search results
    and optional PDF link extraction from pages.
    """

    def __init__(self, pdf_tool: PDFDownloaderTool = None):
        self.pdf_tool = pdf_tool or PDFDownloaderTool()

    def from_search_results(self, search_results: List[Any]) -> List[dict]:
        """
        Build list of previous papers from search results.
        PDF links are identified; non-PDF links are still included as potential resources.

        Args:
            search_results: List of SearchResult or dict with title, url, snippet

        Returns:
            List of {"title": str, "url": str, "type": "pdf"|"link"}
        """
        papers = []
        pdfs = self.pdf_tool.get_pdf_links_from_search_results(
            [r.__dict__ if hasattr(r, "__dict__") and not isinstance(r, dict) else r for r in search_results]
        )
        for p in pdfs:
            papers.append({
                "title": p.get("title", "Previous year paper"),
                "url": p.get("url", ""),
                "type": "pdf",
            })
        # Add non-PDF results that look like papers
        for r in search_results:
            url = getattr(r, "url", None) or (r.get("url") or r.get("href") or r.get("link") if isinstance(r, dict) else "")
            if not url or self.pdf_tool.is_pdf_url(url):
                continue
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            snippet = getattr(r, "snippet", None) or (r.get("snippet") or r.get("body") if isinstance(r, dict) else "")
            if not title:
                continue
            papers.append({
                "title": title[:300],
                "url": url,
                "type": "link",
            })
        return papers[:20]
