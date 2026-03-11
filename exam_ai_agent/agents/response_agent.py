"""
Response Agent: Formats the final results and coordinates the vector store persistence.
"""

from typing import List, Dict, Any
from exam_ai_agent.database.vector_store import VectorStore
from exam_ai_agent.services.syllabus_service import SyllabusService
from exam_ai_agent.services.papers_service import PapersService
from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

class ResponseAgent:
    def __init__(self, vector_store: VectorStore = None, syllabus_service: SyllabusService = None, papers_service: PapersService = None):
        self.vector_store = vector_store or VectorStore()
        self.syllabus_service = syllabus_service or SyllabusService()
        self.pdf_tool = PDFDownloaderTool(WebScraperTool())
        self.papers_service = papers_service or PapersService(self.pdf_tool)

    def format_final_response(
            self,
            exam_name: str,
            syllabus_results: List[Any],
            papers_results: List[Any],
            study_results: List[Any],
            youtube_results: List[Any],
            scraped_syllabus_items: List[Dict[str, str]],
            important_topics: List[str],
            study_plan: List[Dict[str, Any]],
            hidden_pdfs: List[Dict[str, str]],
            raw_text_chunks: List[str]
        ) -> Dict[str, Any]:
        """
        Builds the final structured dictionary to send back to the UI.
        Also persists raw text chunks to FAISS vector DB asynchronously.
        """
        logger.info("[ResponseAgent] Formatting final response for %s", exam_name)
        
        result = {
            "syllabus": [],
            "previous_papers": [],
            "study_plan": study_plan,
            "resources": [],
            "youtube_lectures": []
        }

        # Step 1: Store in vector database
        if raw_text_chunks:
            # Chunk roughly by paragraphs
            chunks = []
            for t in raw_text_chunks:
                for block in t.split("\n\n"):
                    if len(block.strip()) > 100:
                        chunks.append(block.strip())
            if chunks:
                self.vector_store.add_texts(chunks, exam_name=exam_name)

        # Step 2: Build syllabus section by merging search snippets with scraped items
        syllabus_items = self.syllabus_service.extract_from_search_results(syllabus_results)
        merged_syllabus = self.syllabus_service.merge_syllabus(
            syllabus_items, scraped_syllabus_items, exam_name
        )
        
        def _base(u):
            return u.split('?')[0].split('#')[0].rstrip('/')
            
        existing_syllabus_bases = set()
        for s in merged_syllabus:
            url = s.get("source_url")
            base = _base(url) if url else None
            
            if base:
                if base not in existing_syllabus_bases:
                    result["syllabus"].append(s)
                    existing_syllabus_bases.add(base)
            else:
                result["syllabus"].append(s)

        # Step 3: Previous papers (search results + hidden PDFs found during scrape)
        result["previous_papers"] = self.papers_service.from_search_results(papers_results)
        
        def _base(u):
            return u.split('?')[0].split('#')[0].rstrip('/')
            
        existing_paper_bases = {_base(p["url"]) for p in result["previous_papers"] if p.get("url")}
        
        for pdf in hidden_pdfs:
            url = pdf.get("url")
            if url:
                base = _base(url)
                if base not in existing_paper_bases:
                    result["previous_papers"].append(pdf)
                    existing_paper_bases.add(base)
                    
        result["previous_papers"] = result["previous_papers"][:25]

        # Step 4: Study resources (free courses, books, NPTEL)
        for r in study_results:
            url = getattr(r, "url", None) or (r.get("url") or r.get("href") if isinstance(r, dict) else "")
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            if url and title:
                res_type = "pdf" if self.pdf_tool.is_pdf_url(url) else "link"
                result["resources"].append({"title": title[:300], "url": url, "type": res_type})
        result["resources"] = result["resources"][:15]

        # Step 5: YouTube Lectures
        for r in youtube_results:
            url = getattr(r, "url", None) or (r.get("url") or r.get("href") if isinstance(r, dict) else "")
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            if url and title:
                result["youtube_lectures"].append({"title": title[:300], "url": url, "type": "video"})
        result["youtube_lectures"] = result["youtube_lectures"][:10]

        logger.info("[ResponseAgent] Final payload generated successfully.")
        return result
