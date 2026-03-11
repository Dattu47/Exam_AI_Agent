"""
Scraping Agent: Downloads web pages, parses raw text, and extracts embedded files (like PDFs).
"""

from typing import List, Dict, Any, Tuple
from exam_ai_agent.tools.web_scraper import WebScraperTool
from exam_ai_agent.tools.pdf_downloader import PDFDownloaderTool
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

class ScrapingAgent:
    def __init__(self, scraper: WebScraperTool = None, pdf_tool: PDFDownloaderTool = None):
        self.scraper = scraper or WebScraperTool()
        self.pdf_tool = pdf_tool or PDFDownloaderTool(self.scraper)

    def scrape_sources(self, target_urls: List[str], max_pages: int = 8) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Scrapes a list of URLs. Extracts both the readable text AND any embedded PDF links in the HTML.
        Returns a tuple: (Scraped text dictionaries, Extracted PDF links)
        """
        logger.info("[ScrapingAgent] Beginning scrape for %d URLs", len(target_urls))
        
        # Deduplicate and cap URL processing locally (protects against infinite runs)
        unique_urls = list(set([u for u in target_urls if u and not self.pdf_tool.is_pdf_url(u)]))[:max_pages]
        
        scraped_data = self.scraper.scrape_urls(unique_urls, max_pages=max_pages)
        
        hidden_pdfs = []
        for item in scraped_data:
            if item.get("html"):
                pdfs_found = self.pdf_tool.extract_pdf_links_from_html(item["html"], item["url"])
                # Extract domain for cleaner titling
                domain = item['url'].split('/')[2].replace('www.', '') if '//' in item['url'] else item['url']
                
                for pdf_url in pdfs_found[:5]: # Take top 5 per page max to avoid spam
                    hidden_pdfs.append({
                        "title": f"Previous Year Paper (Scraped from {domain})", 
                        "url": pdf_url, 
                        "type": "pdf"
                    })
                    
        logger.info("[ScrapingAgent] Successfully scraped %d pages and found %d hidden PDF links", len(scraped_data), len(hidden_pdfs))
        return scraped_data, hidden_pdfs
