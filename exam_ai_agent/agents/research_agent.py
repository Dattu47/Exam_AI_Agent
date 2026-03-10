"""
Research agent: orchestrates web search, scraping, extraction,
vector storage, and structured output generation for exam preparation.
"""

from typing import List, Optional, Any

from exam_ai_agent.tools.web_search import WebSearchTool, SearchResult
from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.services.syllabus_service import SyllabusService
from exam_ai_agent.services.papers_service import PapersService
from exam_ai_agent.services.study_plan_service import StudyPlanService
from exam_ai_agent.database.vector_store import VectorStore
from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


def _result_to_dict(r: SearchResult) -> dict:
    return {"title": r.title, "url": r.url, "snippet": r.snippet}

def _slice_gate_cs_section(text: str) -> str:
    """
    Heuristic: for GATE CS/CSE, try to isolate the CS syllabus portion from long pages.
    Returns a smaller text window around the 'Computer Science and Information Technology' section.
    """
    if not text:
        return ""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    markers = (
        "computer science and information technology",
        "computer science & information technology",
        "computer science and information tech",
        "computer science",
        "cs and it",
    )
    idx = -1
    for i, ln in enumerate(lines):
        low = ln.lower()
        if any(m in low for m in markers):
            idx = i
            break
    if idx == -1:
        return text
    start = max(0, idx - 10)
    end = min(len(lines), idx + 260)
    return "\n".join(lines[start:end])

class ResearchAgent:
    """
    Main agent that performs deep research for an exam and returns
    syllabus, previous papers, important topics, study plan, and resources.
    """

    def __init__(
        self,
        web_search: Optional[WebSearchTool] = None,
        scraper: Optional[WebScraperTool] = None,
        pdf_tool: Optional[PDFDownloaderTool] = None,
        syllabus_service: Optional[SyllabusService] = None,
        papers_service: Optional[PapersService] = None,
        study_plan_service: Optional[StudyPlanService] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.web_search = web_search or WebSearchTool()
        self.scraper = scraper or WebScraperTool()
        self.pdf_tool = pdf_tool or PDFDownloaderTool(self.scraper)
        self.syllabus_service = syllabus_service or SyllabusService()
        self.papers_service = papers_service or PapersService(self.pdf_tool)
        self.study_plan_service = study_plan_service or StudyPlanService()
        self.vector_store = vector_store or VectorStore()

    def research_exam(self, exam_name: str) -> dict:
        """
        Full pipeline: search -> scrape -> extract -> store -> generate plan.

        Args:
            exam_name: Name of the exam (e.g., "GATE CSE", "JEE Main")

        Returns:
            Structured dict with keys:
            - syllabus: list of {topic, source_url, description}
            - previous_papers: list of {title, url, type}
            - important_topics: list of strings
            - study_plan: list of {week, focus, tasks}
            - resources: list of {title, url, type} (courses, books, etc.)
        """
        logger.info("Starting research for exam: %s", exam_name)
        result = {
            "syllabus": [],
            "previous_papers": [],
            "important_topics": [],
            "study_plan": [],
            "resources": [],
        }

        # Step 1 & 2: Web search for syllabus, papers, pattern, resources
        try:
            search_grouped = self.web_search.search_exam_resources(exam_name)
        except Exception as e:
            logger.exception("Search failed: %s", e)
            result["error"] = f"Search failed: {e}"
            return result

        syllabus_results = search_grouped.get("syllabus", [])
        papers_results = search_grouped.get("previous_papers", [])
        pattern_results = search_grouped.get("exam_pattern", [])
        study_results = search_grouped.get("study_resources", [])

        # Step 3 & 4: Scrape top pages and extract content
        syllabus_urls = [
            (r.url if hasattr(r, "url") else r.get("url", ""))
            for r in syllabus_results[:10]
        ]
        paper_page_urls = [
            (r.url if hasattr(r, "url") else r.get("url", ""))
            for r in papers_results[:3]
        ]

        # Deduplicate by domain: allow at most 2 URLs per domain so we get
        # diverse sources instead of many pages from the same site.
        from urllib.parse import urlparse as _urlparse
        def _domain(u: str) -> str:
            try:
                return _urlparse(u).netloc.lstrip("www.")
            except Exception:
                return u

        domain_count: dict = {}
        urls_to_scrape: List[str] = []
        for u in (syllabus_urls + paper_page_urls):
            if not u or self.pdf_tool.is_pdf_url(u):
                continue
            d = _domain(u)
            if domain_count.get(d, 0) >= 2:
                continue
            domain_count[d] = domain_count.get(d, 0) + 1
            urls_to_scrape.append(u)
        urls_to_scrape = urls_to_scrape[:8]  # hard cap

        scraped = self.scraper.scrape_urls(urls_to_scrape, max_pages=8)
        all_text_for_vector = []
        scraped_syllabus_topics: List[str] = []
        scraped_syllabus_items: List[dict] = []
        hidden_pdfs: List[dict] = []

        topics_per_url: dict = {}   # cap topics contributed per source URL

        for item in scraped:
            all_text_for_vector.append(item["text"])
            
            # Extract PDF links hidden in the HTML of top pages
            if item.get("html"):
                pdfs_found = self.pdf_tool.extract_pdf_links_from_html(item["html"], item["url"])
                for pdf_url in pdfs_found[:5]: # grab up to 5 per page
                    domain = item['url'].split('/')[2].replace('www.', '')
                    hidden_pdfs.append({
                        "title": f"Previous Year Paper (from {domain})", 
                        "url": pdf_url, 
                        "type": "pdf"
                    })
            # Only treat topics from pages that were selected as syllabus URLs
            if item["url"] in syllabus_urls:
                text_for_topics = item["text"]
                # GATE CSE/CS special-case: extract from CS-specific section if present.
                low_exam = exam_name.lower()
                if "gate" in low_exam and ("cse" in low_exam or "cs" in low_exam):
                    text_for_topics = _slice_gate_cs_section(text_for_topics)
                # First try extracting directly from HTML
                topics = self.syllabus_service.extract_from_html(item.get("html", ""), item["url"])
                # If HTML extraction failed to find anything useful, fall back to text approach
                if len(topics) < 3:
                    topics.extend(self.syllabus_service.extract_from_text(text_for_topics, item["url"]))
                    # Quick dedupe
                    seen_t = set()
                    topics = [x for x in topics if x.lower() not in seen_t and not seen_t.add(x.lower())]
                # Build a context snippet for each topic from the surrounding lines
                lines_for_context = text_for_topics.split("\n")
                # Get as many topics as we can from this URL
                for t in topics:
                    scraped_syllabus_topics.append(t)
                    snippet = ""
                    t_lower = t.lower()
                    for li, ln in enumerate(lines_for_context):
                        if t_lower in ln.lower():
                            ctx_start = max(0, li)
                            ctx_lines = [
                                lines_for_context[j].strip()
                                for j in range(ctx_start, min(len(lines_for_context), ctx_start + 4))
                                if lines_for_context[j].strip()
                            ]
                            snippet = " | ".join(ctx_lines)[:300]
                            break
                    scraped_syllabus_items.append(
                        {
                            "topic": t,
                            "source_url": item["url"],
                            "description": snippet if snippet else f"{t} — syllabus topic for {exam_name}.",
                        }
                    )
                    topics_per_url[item["url"]] = topics_per_url.get(item["url"], 0) + 1

        # Use only the single best syllabus source (the one that gave the most topics)
        if topics_per_url:
            best_url = max(topics_per_url, key=topics_per_url.get)
            scraped_syllabus_items = [x for x in scraped_syllabus_items if x["source_url"] == best_url][:40]
            # Since we only use one source, update the extracted topics list to match
            scraped_syllabus_topics = [x["topic"] for x in scraped_syllabus_items]

        # Step 5: Store in vector database
        if all_text_for_vector:
            # Chunk roughly by paragraphs for storage
            chunks = []
            for t in all_text_for_vector:
                for block in t.split("\n\n"):
                    if len(block.strip()) > 100:
                        chunks.append(block.strip())
            if chunks:
                self.vector_store.add_texts(chunks, exam_name=exam_name)

        # Build syllabus section
        syllabus_items = self.syllabus_service.extract_from_search_results(syllabus_results)
        result["syllabus"] = self.syllabus_service.merge_syllabus(
            syllabus_items, scraped_syllabus_items, exam_name
        )

        # Previous papers (PDF + links)
        result["previous_papers"] = self.papers_service.from_search_results(papers_results)
        
        # Merge in any hidden PDFs found during scrape
        existing_paper_urls = {p["url"] for p in result["previous_papers"]}
        for pdf in hidden_pdfs:
            if pdf["url"] not in existing_paper_urls:
                result["previous_papers"].append(pdf)
                existing_paper_urls.add(pdf["url"])
        result["previous_papers"] = result["previous_papers"][:25]

        # Important topics: prefer extracted syllabus topics above all else.
        important: List[str] = []
        for t in scraped_syllabus_topics:
            if t and t not in important:
                important.append(t)
            if len(important) >= 20:
                break
        
        # Only use exam-pattern snippets if we failed to find any structured syllabus topics
        if len(important) < 5:
            for r in pattern_results[:6]:
                sn = getattr(r, "snippet", None) or (r.get("snippet") if isinstance(r, dict) else "")
                if sn:
                    s = sn.strip()
                    if s and s not in important:
                        important.append(s[:180])
                if len(important) >= 15:
                    break
                    
        result["important_topics"] = important[:20]

        # Study plan (LLM or template)
        syllabus_summary = " ".join([s.get("topic", "") for s in result["syllabus"][:10]])
        result["study_plan"] = self.study_plan_service.generate_plan(
            exam_name,
            syllabus_summary=syllabus_summary[:500],
            important_topics=result["important_topics"][:10],
            weeks=8,
        )

        # Resources: free courses, books, practice (from study_resources search)
        for r in study_results:
            url = getattr(r, "url", None) or (r.get("url") or r.get("href") if isinstance(r, dict) else "")
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            if url and title:
                res_type = "pdf" if self.pdf_tool.is_pdf_url(url) else "link"
                result["resources"].append({"title": title[:300], "url": url, "type": res_type})
        result["resources"] = result["resources"][:15]

        logger.info("Research completed for %s", exam_name)
        return result
