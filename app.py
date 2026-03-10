"""
Streamlit Cloud Entry Point for Exam Research AI Agent.
This version bypasses the FastAPI backend and runs the agent natively for easy hosting.
"""

import sys
import os
from pathlib import Path
import streamlit as st

# Add the local directory to the Python path so local modules resolve
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import the main research agent
from exam_ai_agent.agents.research_agent import ResearchAgent

# Initialize agent once and cache it in session state
if "agent" not in st.session_state:
    st.session_state.agent = ResearchAgent()

def run_research_natively(exam_name: str) -> dict | None:
    """Run the research agent directly in the Streamlit process."""
    try:
        return st.session_state.agent.research_exam(exam_name)
    except Exception as e:
        st.error(f"Error during research: {str(e)}")
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
        st.info("Please enter an exam name to begin.")
        return

    # Check if we already have results for this exam
    if "results" not in st.session_state or st.session_state.get("last_exam") != exam_name:
        st.session_state.results = None

    if st.button("Generate Strategy", type="primary"):
        with st.spinner(f"Agent is researching {exam_name}... This may take 30-60 seconds..."):
            res = run_research_natively(exam_name)
            if res:
                st.session_state.results = res
                st.session_state.last_exam = exam_name

    data = st.session_state.results
    if data:
        st.success("Research complete!")
        
        # Syllabus
        st.subheader("📋 Syllabus Topics")
        syllabus = data.get("syllabus") or []
        if syllabus:
            for s in syllabus:
                with st.expander(s.get("topic", "Topic")):
                    st.write(s.get("description", "No details"))
                    if s.get("source_url"):
                        st.markdown(f"[Source link]({s.get('source_url')})")
        else:
            st.write("No syllabus topics found.")

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
