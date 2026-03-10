"""Services for syllabus, papers, and study plan generation."""
from .syllabus_service import SyllabusService
from .papers_service import PapersService
from .study_plan_service import StudyPlanService

__all__ = ["SyllabusService", "PapersService", "StudyPlanService"]
