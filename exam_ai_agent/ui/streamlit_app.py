"""
Streamlit UI for the Exam Research AI Agent.
User enters exam name and gets a structured preparation plan.
"""

import os
import streamlit as st
import requests
import sys
from pathlib import Path

# Add project root to path when running from inside exam_ai_agent
_ui_dir = Path(__file__).resolve().parent
_exam_agent_root = _ui_dir.parent
if str(_exam_agent_root.parent) not in sys.path:
    sys.path.insert(0, str(_exam_agent_root.parent))

# API base URL (set EXAM_API_URL env var for production)
API_BASE = os.environ.get("EXAM_API_URL", "http://localhost:8000")


def run_research(exam_name: str) -> dict | None:
    """Call the FastAPI research endpoint."""
    try:
        r = requests.post(
            f"{API_BASE}/research_exam",
            json={"exam_name": exam_name},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Is the server running? Start it with: `uvicorn exam_ai_agent.api.main:app --reload`")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The research is taking too long.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.status_code} - {e.response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def main():
    st.set_page_config(
        page_title="Exam Research AI Agent",
        page_icon="📚",
        layout="wide",
    )
    st.title("📚 Exam Research AI Agent")
    st.markdown("Enter an exam name to get a **syllabus**, **previous papers**, **study plan**, and **resources**.")

    exam_name = st.text_input(
        "Exam name",
        placeholder="e.g. GATE CSE, JEE Main, UPSC CSE",
        key="exam_name",
    )
    if not exam_name or not exam_name.strip():
        st.info("Enter an exam name above and click **Generate Preparation Plan**.")
        return

    if st.button("Generate Preparation Plan", type="primary"):
        with st.spinner("Searching the web, scraping resources, and generating your plan…"):
            data = run_research(exam_name.strip())
        if not data:
            return

        st.success("Here is your preparation plan.")

        # Syllabus
        st.subheader("📋 Syllabus")
        syllabus = data.get("syllabus") or []
        if syllabus:
            for i, s in enumerate(syllabus, 1):
                topic = s.get("topic", "Syllabus")
                with st.expander(f"{i}. {topic}"):
                    src = s.get("source_url", "")
                    desc = (s.get("description") or "").strip()
                    if src:
                        st.caption(src)
                    # Avoid empty-looking expanders
                    if desc:
                        st.write(desc)
                    else:
                        st.write("Open the source link above for full details.")
        else:
            st.write("No syllabus items found.")

        # Previous Papers
        st.subheader("📄 Previous Papers")
        papers = data.get("previous_papers") or []
        if papers:
            for p in papers:
                st.markdown(f"- [{p.get('title', 'Link')}]({p.get('url', '#')}) ({p.get('type', 'link')})")
        else:
            st.write("No previous papers found.")

        # Important Topics
        st.subheader("🎯 Important Topics")
        topics = data.get("important_topics") or []
        if topics:
            for t in topics:
                if isinstance(t, str):
                    st.markdown(f"- {t}")
                else:
                    st.write(t)
        else:
            st.write("No topics extracted.")

        # Study Plan
        st.subheader("📅 Study Plan")
        plan = data.get("study_plan") or []
        if plan:
            for w in plan:
                st.markdown(f"**Week {w.get('week', '')}:** {w.get('focus', '')}")
                for t in w.get("tasks") or []:
                    st.markdown(f"- {t}")
        else:
            st.write("No study plan generated.")

        # Free Courses & Resources
        st.subheader("📚 Free Courses & Resources")
        resources = data.get("resources") or []
        if resources:
            yt_links = [r for r in resources if "youtube.com" in str(r.get("url", "")).lower() or "youtu.be" in str(r.get("url", "")).lower()]
            other_links = [r for r in resources if r not in yt_links]
            
            if yt_links:
                st.markdown("**📺 YouTube Playlists & Videos:**")
                for r in yt_links:
                    st.markdown(f"- [{r.get('title', 'YouTube Link')}]({r.get('url', '#')})")
            
            if other_links:
                st.markdown("**🌐 Websites & Courses:**")
                for r in other_links:
                    st.markdown(f"- [{r.get('title', 'Resource Link')}]({r.get('url', '#')})")
        else:
            st.write("No additional resources found.")


if __name__ == "__main__":
    main()
