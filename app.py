"""
ExamGenie AI — Premium SaaS (Final Revision v4)
Includes Application Name Header, Merged Materials, Clean Syllabus, and Exam Intel Overview.
"""

import streamlit as st
import datetime
from exam_ai_agent.agents.research_agent import ResearchAgent

# ── 1. Page Config (Dynamic Sidebar) ──────────────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI | Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Comprehensive SaaS Styling ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

:root {
    --bg-base: #030407;
    --bg-card: #0D1117;
    --primary: #C6FF00;
    --primary-dim: rgba(198, 255, 0, 0.1);
    --secondary: #1E293B;
    --text-high: #F8FAFC;
    --text-low: #94A3B8;
    --border: rgba(255, 255, 255, 0.06);
    --radius-xl: 18px;
    --radius-lg: 12px;
}

.stApp { background: var(--bg-base); color: var(--text-high); font-family: 'Plus Jakarta Sans', sans-serif; }
footer, #MainMenu { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none; }

/* Custom App Header */
.app-header-main {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--primary);
    font-family: 'Outfit', sans-serif;
    margin-bottom: 2rem;
    text-align: center;
}

[data-testid="stSidebar"] {
    background-color: #06080C !important;
    border-right: 1px solid var(--border) !important;
}

.sidebar-board-head { font-size: 1.1rem; font-weight: 700; color: #FFF; margin-bottom: 2px; }
.sidebar-board-sub { font-size: 0.75rem; color: var(--text-low); margin-bottom: 2.5rem; }

/* Timeline UI */
.timeline-card { border-left: 2px solid var(--primary); padding-left: 1.25rem; margin-bottom: 1.5rem; position: relative; }
.timeline-card::before { content: ''; position: absolute; left: -7px; top: 0; width: 12px; height: 12px; background: var(--primary); border-radius: 50%; }

/* Vault Card */
.vault-card { background: #111; border: 1px solid #222; padding: 16px; border-radius: 12px; margin-bottom: 12px; }

/* Dashboard Cards */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
}
</style>
""", unsafe_allow_html=True)

# ── 3. Application Branding ───────────────────────────────────────────────────
st.markdown('<div class="app-header-main">⚡ ExamGenie AI</div>', unsafe_allow_html=True)

# ── 4. Session State ──────────────────────────────────────────────────────────
if "agent" not in st.session_state: st.session_state.agent = ResearchAgent()
if "results" not in st.session_state: st.session_state.results = None
if "last_exam" not in st.session_state: st.session_state.last_exam = ""
if "progress" not in st.session_state: st.session_state.progress = {}
if "updated_at" not in st.session_state: st.session_state.updated_at = "Long ago"

# ── 5. Integrated Pipeline ────────────────────────────────────────────────────
def run_unified_pipeline(exam_name: str):
    with st.status(f"🔮 Analyzing {exam_name} Intelligence Archive...", expanded=True) as status:
        try:
            agent = st.session_state.agent
            status.update(label="📡 Parallelizing deep search buckets...", state="running")
            raw = agent.search_agent.find_resources(exam_name)
            
            status.update(label="📖 Scraping authoritative syllabi and documents...", state="running")
            s_urls = [(r.url if hasattr(r, "url") else r.get("url","")) for r in raw.get("syllabus", [])[:10]]
            pages, pdfs = agent.scraping_agent.scrape_sources(s_urls, max_pages=6)
            
            status.update(label="🧠 Building hierarchical syllabus map...", state="running")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(exam_name, pages, s_urls, raw.get("exam_pattern",[]))
            
            status.update(label="📅 Synthesizing day-wise recursive timetable...", state="running")
            plan = agent.study_agent.build_plan(exam_name, syllabus, topics, weeks=4)
            
            status.update(label="📦 Finalizing SaaS Intelligence Dashboard...", state="running")
            final = agent.response_agent.format_final_response(
                exam_name, raw.get("exam_info", []), raw["syllabus"], raw["previous_papers"],
                raw["study_resources"], raw["youtube_lectures"], syllabus, topics, plan, pdfs, chunks
            )
            
            st.session_state.updated_at = datetime.datetime.now().strftime("%I:%M %p")
            return final
        except Exception as e:
            st.error(f"Intelligence failure: {e}")
            return None

# ── 6. Sidebar Navigation HUD ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:1.5rem; font-weight:800; color:var(--primary); margin-bottom:1rem;">⚡ ExamGenie</div>', unsafe_allow_html=True)
    
    current_board = st.session_state.last_exam or "tcs nqt"
    st.markdown(f'<div class="sidebar-board-head">Board: {current_board}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-board-sub">Strategy updated {st.session_state.updated_at}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    nav = st.radio(
        "Navigation",
        ["📖 Exam Overview", "📂 Study Board", "📋 Syllabus", "📖 Study Vault", "🎬 Video Lab"],
        index=0 if st.session_state.results else 0
    )

# ── 7. Search Interaction ─────────────────────────────────────────────────────
if not st.session_state.results:
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        exam_query = st.text_input("Examination Query", value=current_board, placeholder="Enter exam name (e.g. UPSC, JEE)...", label_visibility="collapsed")
    with col_btn:
        generate = st.button("Generate Strategy 🚀", use_container_width=True)
    
    if generate and exam_query:
        res = run_unified_pipeline(exam_query.strip())
        if res:
            st.session_state.results = res
            st.session_state.last_exam = exam_query.strip()
            st.rerun()
    st.stop()

# ── 8. Intelligence Display Tabs ──────────────────────────────────────────────
data = st.session_state.results
exam_name = st.session_state.last_exam

if nav == "📖 Exam Overview":
    st.markdown(f"### 📋 About {exam_name}")
    info = data.get("about_exam") or {}
    st.info(info.get("description", "Gathering details..."))
    st.markdown(f"""
    <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #222;">
        <h4 style="color:var(--primary); margin-bottom:5px;">Application Deadline</h4>
        <p style="font-size:1.2rem; font-weight:700;">{info.get('deadline', 'Check Official Site')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### High-Weightage Core Topics")
    topics = data.get("important_topics") or []
    c = st.columns(3)
    for i, t in enumerate(topics[:12]):
        c[i%3].markdown(f"🔥 **{t}**")

elif nav == "📂 Study Board":
    st.markdown(f"### 📅 4-Week Deep Strategy for {exam_name}")
    plan_data = data.get("study_plan") or []
    for wk in plan_data:
        with st.expander(f"WEEK {wk.get('week')} — {wk.get('focus')}", expanded=True):
            tasks = wk.get("tasks") or []
            for t in tasks:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;◈ {t}", unsafe_allow_html=True)
            if wk.get("tip"):
                st.markdown(f"<br>&nbsp;&nbsp;&nbsp;&nbsp;💡 *Strategy: {wk.get('tip')}*", unsafe_allow_html=True)

elif nav == "📋 Syllabus":
    st.markdown(f"### 📋 Neat Syllabus Hierarchy")
    syllabus = data.get("syllabus") or []
    if syllabus:
        for idx, item in enumerate(syllabus):
            title = item.get("topic")
            with st.container(border=True):
                st.markdown(f"#### {title}")
                subs = item.get("subtopics") or []
                if subs:
                    for s in subs: st.markdown(f"• {s}")
                else: st.caption("No subtopics listed")
    else: st.warning("Syllabus details unavailable.")

elif nav == "📖 Study Vault":
    st.markdown(f"### 📖 Combined Materials & PYQ Archives")
    papers = data.get("previous_papers") or []
    resources = data.get("resources") or []
    
    # Grid for papers
    if papers:
        st.markdown("**Previous Year Question Papers**")
        for p in papers[:10]:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1: st.write(p.get("title"))
                with c2: st.link_button("View", p.get("url", "#"), use_container_width=True)
    
    st.markdown("---")
    # Grid for resources
    if resources:
        st.markdown("**Additional Study Materials**")
        for r in resources[:10]:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1: st.write(r.get("title"))
                with c2: st.link_button("Link", r.get("url", "#"), use_container_width=True)

elif nav == "🎬 Video Lab":
    st.markdown("### 🎬 Visual Intelligence Labs")
    vids = data.get("youtube_lectures") or []
    v_cols = st.columns(2)
    for i, v in enumerate(vids[:10]):
        with v_cols[i % 2]:
            with st.container(border=True):
                st.write(f"**{v.get('title')}**")
                v_url = v.get('url', '')
                if "youtube" in v_url: st.video(v_url)
                st.link_button("▶️ Watch Link", v_url, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
