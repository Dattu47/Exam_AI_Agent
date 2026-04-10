"""
Study plan service: generates a structured, phase-wise preparation strategy
using LLM (Groq) with a template-based fallback.
"""

import json
import re
import datetime
from typing import List, Optional

from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

CURRENT_YEAR = datetime.datetime.now().year


class StudyPlanService:
    """
    Generates a phase-wise, sequenced study strategy from exam name and syllabus.
    Phases: Foundations → Core → Advanced → Revision & Mocks.
    Uses LLM via ChatGroq; falls back to a topic-based template on failure.
    """

    def __init__(self, llm=None):
        self._llm = llm

    # ──────────────────────────────────────────────────────────────────────────
    # Template fallback
    # ──────────────────────────────────────────────────────────────────────────
    def _template_plan(
        self,
        exam_name: str,
        important_topics: Optional[List[str]] = None,
    ) -> List[dict]:
        """Return a phase-split sequential plan using available topic names."""
        topics = list(important_topics or [])
        plan: List[dict] = []

        # Split topics across 3 content phases
        n = len(topics)
        splits = [0, max(1, n // 3), max(2, 2 * n // 3), n]
        phase_names = ["Phase 1 — Foundations", "Phase 2 — Core Concepts", "Phase 3 — Advanced Topics"]

        for p_idx, phase in enumerate(phase_names):
            chunk = topics[splits[p_idx]:splits[p_idx + 1]]
            for t in chunk:
                plan.append({
                    "order":    len(plan) + 1,
                    "phase":    phase,
                    "topic":    t,
                    "subtopics": "",
                    "duration": "2 Hours",
                    "tip":      f"Focus on understanding the fundamentals of {t} before solving problems.",
                })

        # Phase 4: Revision
        plan.append({
            "order":    len(plan) + 1,
            "phase":    "Phase 4 — Revision & Mocks",
            "topic":    "Full-Length Mock Tests",
            "subtopics": "Time management, accuracy, speed, error analysis",
            "duration": "3 Hours",
            "tip":      "Simulate real exam conditions. Analyse every wrong answer thoroughly.",
        })
        plan.append({
            "order":    len(plan) + 1,
            "phase":    "Phase 4 — Revision & Mocks",
            "topic":    "Final Revision",
            "subtopics": "Quick notes, formulae, key theorems, important definitions",
            "duration": "2 Hours",
            "tip":      "Only revise — do not start any new topic in the final phase.",
        })

        return plan

    # ──────────────────────────────────────────────────────────────────────────
    # Main generator
    # ──────────────────────────────────────────────────────────────────────────
    def generate_plan(
        self,
        exam_name: str,
        syllabus_summary: Optional[str] = None,
        important_topics: Optional[List[str]] = None,
        weeks: int = 8,
    ) -> List[dict]:
        """
        Generate a phase-wise preparation strategy as a JSON list.

        Returns:
            List of {"order": int, "phase": str, "topic": str,
                     "subtopics": str, "duration": str, "tip": str}
        """
        llm = self._llm
        if llm is None:
            return self._template_plan(exam_name, important_topics)

        try:
            from langchain_core.messages import SystemMessage, HumanMessage

            system_msg = (
                f"You are a top-tier exam preparation strategist and coach specialising in {exam_name} ({CURRENT_YEAR}).\n\n"
                "YOUR MISSION: Build a PRACTICAL, REALISTIC, and EXAM-SPECIFIC preparation strategy.\n\n"
                "EXAM CONTEXT YOU MUST APPLY:\n"
                "- Consider whether this exam has Prelims, Mains, Interview stages.\n"
                "- Weigh subjects by their actual marks distribution and difficulty.\n"
                "- Assume the student is a BEGINNER unless the exam is highly specialised.\n"
                "- Base your strategy on what ACTUALLY works for this specific exam (not generic advice).\n\n"
                "DIVIDE ALL TOPICS INTO EXACTLY FOUR PHASES:\n"
                "  Phase 1 - Foundations: Prerequisites, basics, easier subjects. Build speed and accuracy here.\n"
                "  Phase 2 - Core Concepts: Main high-weightage subjects and topics. Deepest study phase.\n"
                "  Phase 3 - Advanced Topics: High-difficulty, tricky, less-attempted topics. Competitive edge.\n"
                "  Phase 4 - Revision & Mocks: Full-length mocks, PYQ analysis, rapid revision, weak area targeting.\n\n"
                "FOR EACH TOPIC IN THE PLAN, PROVIDE:\n"
                "1. order (int) — global sequential number across all phases\n"
                "2. phase (str) — exactly one of the four phase names above\n"
                "3. topic (str) — the subject/topic name\n"
                "4. subtopics (str) — comma-separated key concepts to cover within this topic\n"
                "5. duration (str) — realistic time estimate: '45 Minutes', '1.5 Hours', '2 Hours', '3 Hours', etc.\n"
                "   Base duration on actual difficulty: simple topics = 45 min, complex = 3+ hours.\n"
                "6. tip (str) — ONE specific, actionable, exam-relevant tip. Examples:\n"
                "   - 'Solve last 5 years GATE questions on this topic before moving on.'\n"
                "   - 'Focus on RC passages from Hindu/Indian Express for this section.'\n"
                "   - 'Use shortcut methods for DI — do not solve full calculations in exam.'\n"
                "   NEVER write generic tips like 'study hard' or 'practice regularly'.\n\n"
                "STRATEGY DESIGN RULES:\n"
                "- Phase 4 MUST include at least 3 entries: Full Mock Test, PYQ Analysis, Final Revision.\n"
                "- Phase 4 Mock Test tip must mention: exam-like conditions, time management, error analysis.\n"
                "- Topic order within each phase must be logical: foundational → intermediate → advanced.\n"
                "- Cover EVERY topic from the given syllabus. Do not skip or merge unrelated topics.\n"
                "- PYQ (Previous Year Question) mentions: add to tips where relevant (Phase 2, 3, 4).\n\n"
                "OUTPUT: Raw JSON array ONLY. No markdown fences, no HTML, no asterisks, no commentary.\n"
                "Schema: [{\"order\": 1, \"phase\": \"Phase 1 - Foundations\", \"topic\": \"...\", "
                "\"subtopics\": \"...\", \"duration\": \"...\", \"tip\": \"...\"}]\n"
                "Start with [ and end with ]."
            )

            topics_str = "\n".join([f"- {t}" for t in (important_topics or [])[:40]])
            human_msg = (
                f"EXAM: {exam_name} ({CURRENT_YEAR})\n\n"
                f"OFFICIAL SYLLABUS:\n{(syllabus_summary or topics_str)[:5000]}\n\n"
                f"HIGH-WEIGHTAGE / IMPORTANT TOPICS:\n{topics_str[:2000]}\n\n"
                "Now generate the complete, phase-wise, exam-specific preparation strategy JSON array."
            )

            response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=human_msg)])
            text = response.content if hasattr(response, "content") else str(response)
            return self._parse_llm_plan(text, exam_name, important_topics)

        except Exception as e:
            logger.warning("LLM study plan failed: %s. Using template.", e)
            return self._template_plan(exam_name, important_topics)

    # ──────────────────────────────────────────────────────────────────────────
    # Parser
    # ──────────────────────────────────────────────────────────────────────────
    def _parse_llm_plan(
        self,
        text: str,
        exam_name: str,
        important_topics: Optional[List[str]],
    ) -> List[dict]:
        """Parse LLM JSON output into list of phase-wise plan items."""

        clean = text.strip()
        clean = re.sub(r"^```json\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"^```\s*",     "", clean)
        clean = re.sub(r"\s*```$",     "", clean)

        try:
            start = clean.find("[")
            end   = clean.rfind("]")
            if start != -1 and end != -1 and end > start:
                clean = clean[start: end + 1]
            elif start != -1:
                clean = clean[start:] + "]"
        except Exception:
            pass

        # Validate known phase names
        valid_phases = {
            "Phase 1 — Foundations",
            "Phase 2 — Core Concepts",
            "Phase 3 — Advanced Topics",
            "Phase 4 — Revision & Mocks",
        }

        try:
            data = json.loads(clean)
            if not isinstance(data, list) or len(data) == 0:
                raise ValueError("Not a non-empty list")

            plan: List[dict] = []
            for idx, item in enumerate(data, start=1):
                if not isinstance(item, dict):
                    continue

                order     = int(item.get("order", idx))
                phase     = str(item.get("phase", "Phase 1 — Foundations")).strip()
                topic     = re.sub(r'<[^>]*>', '', str(item.get("topic", ""))).replace('*', '').strip()[:200]
                subtopics = re.sub(r'<[^>]*>', '', str(item.get("subtopics", "") or "")).replace('*', '').strip()[:400]
                duration  = re.sub(r'<[^>]*>', '', str(item.get("duration", "2 Hours"))).strip()[:60]
                tip       = re.sub(r'<[^>]*>', '', str(item.get("tip", "") or "")).replace('*', '').strip()[:500]

                # Normalise phase name to what the UI expects (em-dash variant)
                pl = phase.lower()
                if "foundation" in pl:
                    phase = "Phase 1 — Foundations"
                elif "core" in pl:
                    phase = "Phase 2 — Core Concepts"
                elif "advanced" in pl:
                    phase = "Phase 3 — Advanced Topics"
                elif "revision" in pl or "mock" in pl:
                    phase = "Phase 4 — Revision & Mocks"
                else:
                    phase = "Phase 1 — Foundations"

                if not topic:
                    continue

                plan.append({
                    "order":     order,
                    "phase":     phase,
                    "topic":     topic,
                    "subtopics": subtopics,
                    "duration":  duration,
                    "tip":       tip,
                })

            if plan:
                plan.sort(key=lambda x: x["order"])
                for i, p in enumerate(plan, start=1):
                    p["order"] = i
                logger.info("[StudyPlanService] Parsed %d plan items across phases.", len(plan))
                return plan

            return self._template_plan(exam_name, important_topics)

        except Exception as e:
            logger.warning(
                "Failed to parse LLM study plan JSON: %s. Preview: %s",
                e, clean[:200]
            )
            return self._template_plan(exam_name, important_topics)
