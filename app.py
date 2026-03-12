"""
Streamlit Cloud Entry Point for Exam Research AI Agent.
Modern UI layout leveraging the orchestrated Multi-Agent system and Supabase caching.
"""

import sys
import os
from pathlib import Path
import streamlit as st

# Streamlit naturally adds the script's directory to sys.path, so no sys.path hacks are needed.

# Import Orchestrator
from exam_ai_agent.agents.research_agent import ResearchAgent

# Initialize Orchestrator agent once and cache it in session state
if "agent" not in st.session_state:
    st.session_state.agent = ResearchAgent()

# Initialize progress tracking state
if "progress" not in st.session_state:
    st.session_state.progress = {}

def run_research_natively(exam_name: str, force: bool = False) -> dict | None:
    """Run the research agent directly in the Streamlit process."""
    try:
        return st.session_state.agent.research_exam(exam_name, force_refresh=force)
    except Exception as e:
        st.error(f"Error during research: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="AI Exam Researcher",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    
    st.title("🤖 AI Exam Research Assistant")
    st.markdown("Enter an exam name to get a structured **syllabus**, **previous papers**, **study plan**, and **curated resources**.")

    # --- Search Bar & Controls ---
    col1, col2 = st.columns([4, 1])
    with col1:
        exam_name = st.text_input(
            "Target Exam Name:",
            placeholder="e.g. GATE CSE, JEE Main, UPSC CSE",
            key="exam_name",
        )
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        force_refresh = st.checkbox("Force Fresh Search", help="Bypass database cache and scrape the web again.")
    
    if not exam_name or not exam_name.strip():
        st.info("👈 Please enter an exam name to begin your preparation journey.")
        return

    # Clear results if exam changes, or if user explicitly requested a fresh search
    if "results" not in st.session_state or st.session_state.get("last_exam") != exam_name or force_refresh:
        st.session_state.results = None

    if st.button("Generate Strategy", type="primary", use_container_width=True):
        with st.spinner("🧠 Researching and compiling data..."):
            with st.status("Initializing AI Agents...", expanded=True) as status:
                st.write("🔎 Agents are scouring the web and consulting the database cache for " + exam_name)
                res = run_research_natively(exam_name, force=force_refresh)
                
                if res:
                    st.session_state.results = res
                    st.session_state.last_exam = exam_name
                    status.update(label="✅ Strategy Generated Successfully!", state="complete", expanded=False)
                else:
                    status.update(label="❌ Failed to generate strategy.", state="error", expanded=True)

    data = st.session_state.results
    if data:
        st.divider()
        
        # --- TABS LAYOUT ---
        tab_syl, tab_pap, tab_plan, tab_res, tab_vid = st.tabs([
            "📋 Syllabus", 
            "📄 Previous Papers", 
            "📅 Study Plan", 
            "📚 Resources", 
            "📺 Video Lectures"
        ])

        # --- 1. Syllabus Tab ---
        with tab_syl:
            st.header("📋 Official Syllabus & Important Topics")
            
            # Important topics callout
            topics = data.get("important_topics") or []
            if topics:
                with st.expander("🎯 High-Yield / Important Topics identified by AI", expanded=True):
                    for t in topics:
                        st.markdown(f"- **{t}**")
                        
            st.divider()
            
            # Main syllabus items with progress tracking
            syllabus = data.get("syllabus") or []
            if syllabus:
                for idx, s in enumerate(syllabus):
                    topic_title = s.get("topic", f"Topic {idx+1}")
                    
                    # Progress tracker checkbox logic
                    cb_key = f"prog_{exam_name}_{topic_title}"
                    if cb_key not in st.session_state.progress:
                        st.session_state.progress[cb_key] = False
                        
                    colA, colB = st.columns([1, 15])
                    with colA:
                        st.session_state.progress[cb_key] = st.checkbox(
                            f"Complete {topic_title}",
                            key=cb_key, 
                            value=st.session_state.progress[cb_key],
                            label_visibility="hidden"
                        )
                        
                    with colB:
                        if st.session_state.progress[cb_key]:
                            st.markdown(f"~~**{topic_title}**~~ (Completed)")
                        else:
                            with st.expander(f"**{topic_title}**"):
                                # Check for hierarchical subtopics first
                                subtopics = s.get("subtopics", [])
                                if isinstance(subtopics, list) and subtopics:
                                    st.markdown("#### Subtopics:")
                                    for sub in subtopics:
                                        st.markdown(f"- {sub}")
                                    st.write("")
                                st.write(s.get("description", "No detailed description available."))
                                if s.get("source_url"):
                                    st.markdown(f"[🔗 View Source Material]({s.get('source_url')})")
            else:
                st.info("No structured syllabus items could be extracted.")


        # --- 2. Previous Papers Tab ---
        with tab_pap:
            st.header("📄 Previous Year Question Papers")
            papers = data.get("previous_papers") or []
            if papers:
                for p in papers:
                    with st.container(border=True):
                        col_text, col_btn = st.columns([4, 1])
                        with col_text:
                            st.subheader(p.get('title', 'Unknown Paper'))
                            st.write(p.get('description', ''))
                        with col_btn:
                            st.link_button(
                                "📥 Download PDF" if p.get('type') == 'pdf' else "🔗 Open Link", 
                                p.get('url', '#'), 
                                use_container_width=True
                            )
            else:
                st.info("No previous year papers found.")


        # --- 3. Study Plan Tab ---
        with tab_plan:
            st.header("📅 AI-Generated Study Plan")
            st.caption("A rigorous, day-by-day sequence customized to your exam's syllabus.")
            plan = data.get("study_plan") or []
            if plan:
                for w in plan:
                    with st.container(border=True):
                        st.subheader(f"Week {w.get('week', '?')}: {w.get('focus', 'General Prep')}")
                        tip = w.get("tip")
                        if tip:
                            st.info(f"💡 **Strategy Tip:** {tip}")
                        
                        # Display tasks with attractive markdown
                        for t in w.get("tasks") or []:
                            st.markdown(f"✨ {t}")
            else:
                st.info("No study plan could be generated. Try expanding your search.")


        # --- 4. Resources Tab ---
        resources = data.get("resources") or []
        with tab_res:
            st.header("📚 Recommended Books, Courses & Links")
            if resources:
                for r in resources:
                    with st.container(border=True):
                        st.markdown(f"### {r.get('title', 'Link')}")
                        desc = r.get("description")
                        if desc:
                            st.write(desc)
                        st.link_button("🌐 Open Resource", r.get('url', '#'))
            else:
                st.info("No external blogs or book resources found.")


        # --- 5. Video Lectures Tab ---
        yt_links = data.get("youtube_lectures") or []
        with tab_vid:
            st.header("📺 YouTube Playlists & Video Lectures")
            if yt_links:
                for r in yt_links:
                    with st.container(border=True):
                        st.markdown(f"### {r.get('title', 'YouTube Video')}")
                        url = r.get('url', '')
                        # Streamlit native video embed
                        try:
                            st.video(url)
                        except Exception:
                            pass
                        st.link_button("▶️ Open on YouTube", url)
            else:
                st.info("No specific YouTube playlists were found. Try searching YouTube manually.")

if __name__ == "__main__":
    main()
