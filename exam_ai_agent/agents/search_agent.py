"""
Search Agent: Responsible for generating robust search queries and finding initial relevant links.
"""

from typing import List, Dict, Any
from exam_ai_agent.tools.web_search import WebSearchTool, SearchResult
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

class SearchAgent:
    def __init__(self, web_search: WebSearchTool = None):
        self.web_search = web_search or WebSearchTool()

    def find_resources(self, exam_name: str) -> Dict[str, List[SearchResult]]:
        """
        Executes parallel searches for syllabus, previous papers, exam pattern, and general study resources.
        Returns a dictionary grouped by these categories.
        """
        logger.info("[SearchAgent] Generating search queries and looking up resources for: %s", exam_name)
        try:
            results = self.web_search.search_exam_resources(exam_name)
            
            # Log summary
            logger.info("[SearchAgent] Found %d syllabus links, %d paper links, %d pattern links, %d study links, %d youtube links",
                        len(results.get("syllabus", [])), len(results.get("previous_papers", [])),
                        len(results.get("exam_pattern", [])), len(results.get("study_resources", [])),
                        len(results.get("youtube_lectures", [])))
            return results
        except Exception as e:
            logger.error("[SearchAgent] Web search failed: %s", str(e))
            return {}
