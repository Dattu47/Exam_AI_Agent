"""
Search Agent: Responsible for generating robust search queries and finding initial relevant links.
"""

from typing import List, Dict, Any, Optional

from exam_ai_agent.tools.web_search import WebSearchTool, SearchResult
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class SearchAgent:
    def __init__(self, web_search: Optional[WebSearchTool] = None):
        self.web_search = web_search or WebSearchTool()

    def find_resources(self, exam_name: str) -> Dict[str, List[Any]]:
        """
        Executes parallel searches for syllabus, previous papers, exam pattern,
        and general study resources.
        Returns a dictionary grouped by these categories.
        """
        en = exam_name.strip()
        logger.info("[SearchAgent] Generating and running searches for: %s", en)
        try:
            results = self.web_search.search_exam_resources(en)
            logger.info(
                "[SearchAgent] Found — syllabus:%d, papers:%d, pattern:%d, study:%d, youtube:%d",
                len(results.get("syllabus", [])),
                len(results.get("previous_papers", [])),
                len(results.get("exam_pattern", [])),
                len(results.get("study_resources", [])),
                len(results.get("youtube_lectures", [])),
            )
            return results
        except Exception as e:
            logger.error("[SearchAgent] Search execution failed for '%s': %s", en, e)
            return {
                "syllabus": [],
                "previous_papers": [],
                "exam_pattern": [],
                "study_resources": [],
                "youtube_lectures": [],
            }
