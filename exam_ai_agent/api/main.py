"""
FastAPI application: exposes research endpoint for the Exam Research AI Agent.
"""

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


# --- Request/Response models ---

class ResearchRequest(BaseModel):
    """Request body for POST /research_exam."""
    exam_name: str = Field(..., min_length=1, max_length=200, description="Name of the exam (e.g., GATE CSE)")


class SyllabusItem(BaseModel):
    topic: str
    source_url: str = ""
    description: str = ""


class PaperItem(BaseModel):
    title: str
    url: str
    type: str  # "pdf" | "link"


class StudyPlanWeek(BaseModel):
    week: int
    focus: str
    tasks: List[str]


class ResourceItem(BaseModel):
    title: str
    url: str
    type: str


class ResearchResponse(BaseModel):
    """Structured response for exam research."""
    syllabus: List[SyllabusItem] = []
    previous_papers: List[PaperItem] = []
    important_topics: List[str] = []
    study_plan: List[StudyPlanWeek] = []
    resources: List[ResourceItem] = []


# --- App lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup; cleanup on shutdown."""
    app.state.agent = ResearchAgent()
    logger.info("Research agent initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Exam Research AI Agent",
    description="Deep web research and resource collection for exam preparation",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Endpoints ---

@app.get("/")
def root():
    """Health and info."""
    return {
        "service": "Exam Research AI Agent",
        "docs": "/docs",
        "research": "POST /research_exam",
    }


@app.get("/health")
def health():
    """Health check for deployment."""
    return {"status": "ok"}


@app.post("/research_exam", response_model=ResearchResponse)
def research_exam(req: ResearchRequest):
    """
    Run full research for the given exam name.
    Returns syllabus, previous papers, important topics, study plan, and resources.
    """
    agent: ResearchAgent = app.state.agent
    try:
        raw = agent.research_exam(req.exam_name.strip())
    except Exception as e:
        logger.exception("Research failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    if raw.get("error"):
        raise HTTPException(status_code=502, detail=raw["error"])

    # Map to response model (strip extra keys, ensure types)
    def to_syllabus(x):
        return SyllabusItem(
            topic=x.get("topic", ""),
            source_url=x.get("source_url", ""),
            description=x.get("description", ""),
        )

    def to_paper(x):
        return PaperItem(
            title=x.get("title", ""),
            url=x.get("url", ""),
            type=x.get("type", "link"),
        )

    def to_week(x):
        return StudyPlanWeek(
            week=int(x.get("week", 0)),
            focus=x.get("focus", ""),
            tasks=list(x.get("tasks") or []),
        )

    def to_resource(x):
        return ResourceItem(
            title=x.get("title", ""),
            url=x.get("url", ""),
            type=x.get("type", "link"),
        )

    return ResearchResponse(
        syllabus=[to_syllabus(s) for s in raw.get("syllabus", [])],
        previous_papers=[to_paper(p) for p in raw.get("previous_papers", [])],
        important_topics=list(raw.get("important_topics", [])),
        study_plan=[to_week(w) for w in raw.get("study_plan", [])],
        resources=[to_resource(r) for r in raw.get("resources", [])],
    )
