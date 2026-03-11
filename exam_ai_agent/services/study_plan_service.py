"""
Study plan service: generates a structured study timetable and strategy
using LLM (Ollama) and/or template-based fallback.
"""

from typing import List, Optional, Any

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class StudyPlanService:
    """
    Generates study plan (timetable + strategy) from exam name and optional context.
    Uses LLM when available; otherwise returns a sensible template.
    """

    def __init__(self):
        self._llm = None

    def _is_ollama_reachable(self) -> bool:
        """Quick check: is Ollama running and responding?"""
        try:
            import requests as _req
            resp = _req.get(f"{settings.LLM_BASE_URL}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def _get_llm(self):
        """Lazy-load Ollama LLM only when Ollama is actually reachable."""
        if self._llm is not None:
            return self._llm
        if not self._is_ollama_reachable():
            logger.warning("Ollama not reachable at %s. Using template plan.", settings.LLM_BASE_URL)
            return None
        try:
            from langchain_ollama import ChatOllama
            self._llm = ChatOllama(
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL,
                timeout=settings.LLM_TIMEOUT,
            )
            logger.info("Ollama LLM loaded (%s @ %s)", settings.LLM_MODEL, settings.LLM_BASE_URL)
            return self._llm
        except Exception as e:
            logger.warning("Ollama LLM init failed: %s. Using template plan.", e)
            return None

    def _template_plan(self, exam_name: str, important_topics: Optional[List[str]] = None) -> List[dict]:
        """Return a study plan for this exam using real topics when available."""
        topics = list(important_topics or [])
        # Build topic-focused weeks
        plan = [
            {
                "week": 1,
                "focus": f"{exam_name} — Syllabus Overview & Weak Area Identification",
                "tasks": [
                    f"Download and read the full {exam_name} syllabus",
                    "Make a topic-wise checklist",
                    "Identify your weak vs strong areas",
                ],
            },
        ]
        # Assign real topics to weeks 2-5
        topic_chunks = [topics[i:i+3] for i in range(0, min(len(topics), 12), 3)]
        for idx, chunk in enumerate(topic_chunks, start=2):
            focus = ", ".join(chunk) if chunk else f"Core subject {idx - 1}"
            tasks = [
                f"Study theory and deeply understand {chunk[0]}" if chunk else "Study core theory",
                f"Practice 30+ problems directly related to {', '.join(chunk)}" if chunk else "Solve 20 MCQs",
                f"Make short revision notes for {chunk[0]}" if chunk else "Make short revision notes",
            ]
            plan.append({
                "week": idx,
                "focus": focus,
                "tasks": tasks,
            })
            if idx >= 5:
                break
        # Fill remaining weeks generically
        existing_weeks = {w["week"] for w in plan}
        for week_num, focus, tasks in [
            (6, "Full-length Mock Tests", ["Take 2 full-length mock tests", "Analyse mistakes and time management"]),
            (7, "Revision — Weak Topics", ["Re-study weak topics from week 1 list", "Solve previous year questions"]),
            (8, f"Final Revision & {exam_name} Strategy", [
                "Revise all short notes",
                "Read exam-day instructions and strategy",
                "Stay calm and confident",
            ]),
        ]:
            if week_num not in existing_weeks:
                plan.append({"week": week_num, "focus": focus, "tasks": tasks})
        return sorted(plan, key=lambda x: x["week"])

    def generate_plan(
        self,
        exam_name: str,
        syllabus_summary: Optional[str] = None,
        important_topics: Optional[List[str]] = None,
        weeks: int = 8,
    ) -> List[dict]:
        """
        Generate a study plan (list of week-wise focus and tasks).

        Args:
            exam_name: Name of the exam
            syllabus_summary: Optional short summary of syllabus
            important_topics: Optional list of important topics
            weeks: Number of weeks for the plan

        Returns:
            List of {"week": int, "focus": str, "tasks": List[str]}
        """
        llm = self._get_llm()
        if llm is None:
            return self._template_plan(exam_name, important_topics)

        try:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", 
                 "You are an expert exam preparation coach. Generate a {weeks}-week study plan for the exam. "
                 "CRITICAL INSTRUCTIONS:\n"
                 "1. You MUST explicitly use the provided 'Important topics' and 'Syllabus summary' to schedule real subjects.\n"
                 "2. Each week MUST contain a day-wise breakdown (Day 1, Day 2, etc.) or distinct, highly granular task phases.\n"
                 "3. You MUST include a short practical 'tip' or note for each week's block to guide the student.\n"
                 "4. You MUST reply with a valid JSON array and absolutely nothing else. Do not output markdown codeblocks.\n"
                 'Format exactly like this: [{{"week": 1, "focus": "Actual Topic 1 & 2", "tip": "Focus on high-weightage formulas", "tasks": ["Day 1-2: Study theory for Topic 1", "Day 3: Solve 50 MCQs", "Day 4-7: Mock tests"]}}]'),
                ("human", "Exam: {exam_name}. Syllabus summary: {syllabus}. Important topics: {topics}."),
            ])
            chain = prompt | llm
            syllabus = syllabus_summary or "General syllabus"
            topics = ", ".join(important_topics[:15]) if important_topics else "All syllabus topics"
            response = chain.invoke({
                "exam_name": exam_name,
                "syllabus": syllabus[:500],
                "topics": topics[:500],
                "weeks": weeks,
            })
            text = response.content if hasattr(response, "content") else str(response)
            return self._parse_llm_plan(text, exam_name, important_topics, weeks)
        except Exception as e:
            logger.warning("LLM study plan failed: %s. Using template.", e)
            return self._template_plan(exam_name, important_topics)

    def _parse_llm_plan(self, text: str, exam_name: str, important_topics: Optional[List[str]], max_weeks: int) -> List[dict]:
        """Parse LLM JSON output into list of {week, focus, tasks}."""
        import json
        import re
        
        # Clean up text (strip markdown ```json if present)
        clean_text = text.strip()
        clean_text = re.sub(r"^```json\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"^```\s*", "", clean_text)
        clean_text = re.sub(r"\s*```$", "", clean_text)
        
        # Aggressive JSON cleanup for smaller local models
        try:
            # Find the first '[' and last ']'
            start = clean_text.find('[')
            end = clean_text.rfind(']')
            if start != -1 and end != -1 and end > start:
                clean_text = clean_text[start:end+1]
            elif start != -1:
                # Missing closing bracket
                clean_text = clean_text[start:] + "]"
        except Exception:
            pass
            
        try:
            data = json.loads(clean_text)
            if not isinstance(data, list) or len(data) == 0:
                raise ValueError("JSON is not a non-empty list")
            
            plan = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                week = int(item.get("week", len(plan) + 1))
                focus = str(item.get("focus", ""))[:200]
                tasks = [str(t)[:200] for t in item.get("tasks", []) if t][:5]
                if not focus and not tasks:
                    continue
                if not tasks:
                    tasks = [focus]
                plan.append({"week": week, "focus": focus, "tasks": tasks})
                if len(plan) >= max_weeks:
                    break
                    
            if plan:
                return sorted(plan, key=lambda x: x["week"])
            return self._template_plan(exam_name, important_topics)
            
        except Exception as e:
            logger.warning("Failed to parse LLM JSON output: %s. Text was: %s", e, clean_text[:100])
            return self._template_plan(exam_name, important_topics)
