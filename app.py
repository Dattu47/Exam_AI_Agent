"""
ExamGenie AI — Premium SaaS Platform
A high-performance research agent with an elite minimalist UI.
Designed to feel like Stripe / Linear / Notion.
"""

import streamlit as st
from exam_ai_agent.agents.research_agent import ResearchAgent

# ── 1. Page Config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI | Intelligent Exam Strategy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Comprehensive SaaS Design System (CSS) ──────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

/* ── Design Tokens ── */
:root {
    --bg-base: #030407;
    --bg-card: #0D1117;
    --primary: #C6FF00;            /* Electric Lime / SaaS Green */
    --primary-dim: rgba(198, 255, 0, 0.1);
    --secondary: #1E293B;
    --text-high: #F8FAFC;
    --text-low: #94A3B8;
    --border: rgba(255, 255, 255, 0.06);
    --radius-xl: 24px;
    --radius-lg: 16px;
    --shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.4);
    --transition: cubic-bezier(0.4, 0, 0.2, 1) 0.3s;
}

/* ── App Container ── */
.stApp {
    background: var(--bg-base);
    color: var(--text-high);
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Hide Native Headers */
header, footer, #MainMenu { visibility: hidden; position: absolute; }
.stDeployButton { display: none; }

/* Main Block Spacing */
.block-container {
    padding-top: 5rem !important;
    padding-bottom: 5rem !important;
    max-width: 1000px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #06080C !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarNav"] { display: none; }

.sidebar-logo {
    padding: 1rem 0 2rem;
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--primary);
    font-family: 'Outfit', sans-serif;
}

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.03em !important;
}

/* ── Hero Animation ── */
@keyframes fadeInSlideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.hero-section {
    text-align: center;
    margin-bottom: 5rem;
    animation: fadeInSlideUp 0.8s ease-out;
}

.hero-main-title {
    font-size: 4rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #FFF 50%, #777 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-low);
    max-width: 600px;
    margin: 0 auto 3rem;
    line-height: 1.6;
}

/* ── Smart Input Box (ChatGPT/Perplexity Style) ── */
.smart-search-wrapper {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 0.75rem;
    box-shadow: var(--shadow);
    transition: var(--transition);
    max-width: 800px;
    margin: 0 auto;
}
.smart-search-wrapper:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 40px rgba(198, 255, 0, 0.1);
}

.stTextInput input {
    background: transparent !important;
    border: none !important;
    color: #FFF !important;
    font-size: 1.2rem !important;
    padding: 1.5rem !important;
}
.stTextInput input:focus {
    box-shadow: none !important;
}

/* CTA Button Styles */
div.stButton > button {
    background: var(--primary) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    height: 56px !important;
    border-radius: 14px !important;
    padding: 0 2rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    transition: var(--transition) !important;
}
div.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 10px 30px var(--primary-dim) !important;
}

/* ── Tab System Overhaul ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 32px !important;
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 3rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-low) !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 12px 4px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
}
.stTabs [data-baseweb="tab-highlight-point"] {
    background-color: var(--primary) !important;
}

/* ── Cards & Containers ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.5rem !important;
}

/* ── Study Plan Calendar/Timeline Mockup ── */
.timeline-card {
    border-left: 2px solid var(--primary);
    padding-left: 1.5rem;
    margin-bottom: 2rem;
    position: relative;
}
.timeline-card::before {
    content: '';
    position: absolute;
    left: -7px;
    top: 0;
    width: 12px;
    height: 12px;
    background: var(--primary);
    border-radius: 50%;
    box-shadow: 0 0 10px var(--primary);
}

/* ── Badges ── */
.badge-pro {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--primary-dim);
    border: 1px solid rgba(198, 255, 0, 0.2);
    color: var(--primary);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Empty State ── */
.empty-state-canvas {
    text-align: center;
    padding-top: 4rem;
}
.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── 3. Sidebar Navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚡ ExamGenie</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.button("🏠 Home", use_container_width=True, key="side_home")
    st.button("📦 Saved Strategy", use_container_width=True, key="side_saved")
    st.button("🕒 History", use_container_width=True, key="side_history")
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    with st.expander("👤 My Account"):
        st.write("Dattu S")
        st.caption("Premium Member")

# ── 4. Session State & Research Logic ──────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = ResearchAgent()
if "results" not in st.session_state:
    st.session_state.results = None
if "last_exam" not in st.session_state:
    st.session_state.last_exam = ""
if "progress" not in st.session_state:
    st.session_state.progress = {}

def run_pipeline(exam_name: str, force: bool):
    """Encapsulated execution with live status pulses."""
    with st.status("🔮 Analyzing examinations...", expanded=True) as status:
        try:
            agent = st.session_state.agent
            db = agent.db
            
            # Step 1: Query Log
            db.save_user_query(exam_name)
            
            # Step 2: Intelligence Check (Cache)
            if not force:
                cached = db.get_exam_resources(exam_name)
                if cached:
                    status.update(label="🚀 Data retrieved from local intelligence.", state="complete", expanded=False)
                    return cached

            # Step 3: Deep Search
            status.update(label="📡 Scanning archives for syllabus...", state="running")
            raw_data = agent.search_agent.find_resources(exam_name)
            
            # Step 4: Page Ingestion
            status.update(label="📖 Processing authoritative sources...", state="running")
            sc_sy_urls = [(r.url if hasattr(r, "url") else r.get("url","")) for r in raw_data.get("syllabus", [])[:8]]
            sc_pa_urls = [(r.url if hasattr(r, "url") else r.get("url","")) for r in raw_data.get("previous_papers", [])[:2]]
            pages, pdfs = agent.scraping_agent.scrape_sources(sc_sy_urls + sc_pa_urls, max_pages=6)
            
            # Step 5: Linguistic Refinement
            status.update(label="🧠 Structural modeling in progress...", state="running")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(exam_name, pages, sc_sy_urls, raw_data.get("exam_pattern",[]))
            
            # Step 6: Strategy Synthesis
            status.update(label="📅 Synthesizing strategy board...", state="running")
            plan = agent.study_agent.build_plan(exam_name, syllabus, topics, weeks=4)
            
            # Step 7: Final Format
            status.update(label="📦 Finalizing your strategy dashboard...", state="running")
            final = agent.response_agent.format_final_response(
                exam_name, raw_data["syllabus"], raw_data["previous_papers"], raw_data["study_resources"],
                raw_data["youtube_lectures"], syllabus, topics, plan, pdfs, chunks
            )
            
            # Persistence
            db.save_exam_resources(exam_name, final)
            if plan: db.save_study_plan(exam_name, plan)
            
            status.update(label="✅ Strategy generated successfully.", state="complete", expanded=False)
            return final

        except Exception as e:
            status.update(label="⚠️ System reached an edge case.", state="error", expanded=True)
            st.error(f"Error trace: {e}")
            return None

# ── 5. Hero Section ───────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="badge-pro">✨ INTELLIGENT SEARCH ENGINE</div>
    <div class="hero-main-title">Your AI-Powered Exam Strategy Generator</div>
    <div class="hero-subtitle">
        Instantly get syllabus breakdowns, PYQs, high-quality video resources, and a 
        personalized study plan for any competitive examination.
    </div>
</div>
""", unsafe_allow_html=True)

# ── 6. Smart Input Area ───────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="smart-search-wrapper">', unsafe_allow_html=True)
    input_col, btn_col = st.columns([4, 1])
    
    with input_col:
        exam_query = st.text_input(
            "Search Exam",
            placeholder="Search for UPSC, GATE CSE, JEE, NEET...",
            label_visibility="collapsed",
            key="saas_search"
        )
    
    with btn_col:
        run_search = st.button("Generate 🚀", use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

# Advanced Options
c1, c2, c3 = st.columns([1.5, 3, 1.5])
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    force_refresh = st.toggle("✨ Force deep research (Bypass cache)", value=False)
    st.caption("Suggested for GATE, UPSC, JEE, NEET, SSC.")

# ── 7. Pipeline Execution ──────────────────────────────────────────────────────
if run_search and exam_query:
    result = run_pipeline(exam_query.strip(), force_refresh)
    if result:
        st.session_state.results = result
        st.session_state.last_exam = exam_query.strip()
        st.rerun()

# ── 8. Empty State Design ──────────────────────────────────────────────────────
if not st.session_state.results:
    st.markdown("""
    <div class="empty-state-canvas">
        <div class="empty-state-icon">🤖</div>
        <h3 style="color:#FFF;">Ready to start your preparation?</h3>
        <p style="color:var(--text-low);">Enter an examination name above to generate your smart study plan.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── 9. Strategy Dashboard (Results) ───────────────────────────────────────────
data = st.session_state.results
exam_name = st.session_state.last_exam

st.markdown("<br><br>", unsafe_allow_html=True)

# Dashboard HUD
st.markdown(f"### Board: {exam_name}")
st.caption(f"Strategy updated just now")

tab_plan, tab_syl, tab_pap, tab_res, tab_vid = st.tabs([
    "📂 Study Board", "📋 Syllabus", "📄 PYQ Archive", "📚 Resources", "🎬 Video Lab"
])

# ── TAB: STUDY PLAN ──
with tab_plan:
    st.markdown('<div class="prog-container" style="background:#111; border:1px solid #222;">', unsafe_allow_html=True)
    syllabus_items = data.get("syllabus") or []
    total_t = len(syllabus_items)
    done_t = sum(1 for k, v in st.session_state.progress.items() if k.startswith(f"prog_{exam_name}_") and v)
    pct = int((done_t / total_t * 100)) if total_t > 0 else 0
    
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
        <span style="color:var(--text-low); font-size:0.9rem;">Strategy Mastery</span>
        <span style="color:var(--primary); font-size:0.9rem; font-weight:800;">{pct}%</span>
    </div>
    <div class="prog-bar-bg">
        <div class="prog-bar-fill" style="width:{pct}%;"></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Timeline view
    plan_data = data.get("study_plan") or []
    if plan_data:
        for wk in plan_data:
            with st.container():
                st.markdown(f"""
                <div class="timeline-card">
                    <span style="color:var(--primary); font-weight:700; font-size:0.8rem; text-transform:uppercase;">Phase {wk.get('week')}</span>
                    <h3 style="margin:5px 0 10px;">{wk.get('focus')}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                tasks = wk.get("tasks") or []
                for t in tasks:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;○ {t}")
                
                if wk.get("tip"):
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:var(--primary); font-size:0.85rem;'>💡 {wk.get('tip')}</span>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.write("Generating your schedule...")

# ── TAB: SYLLABUS ──
with tab_syl:
    topics = data.get("important_topics") or []
    if topics:
        st.markdown("**HIGH-YIELD FOCUS AREAS**")
        st.caption("AI-identified topics with the highest exam frequency.")
        c = st.columns(3)
        for i, t in enumerate(topics):
            c[i%3].markdown(f"""
            <div style="background:#111; border:1px solid #222; padding:12px; border-radius:10px; margin-bottom:10px; font-weight:600;">
                🔥 {t}
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    if syllabus_items:
        for idx, item in enumerate(syllabus_items):
            title = item.get("topic")
            key = f"prog_{exam_name}_{title}"
            
            col_b, col_t = st.columns([1, 15])
            with col_b:
                checked = st.checkbox("Done", value=st.session_state.progress.get(key, False), key=key, label_visibility="hidden")
                st.session_state.progress[key] = checked
            with col_t:
                with st.expander(f"**{title}**"):
                    st.write(item.get("description"))
                    if item.get("subtopics"):
                        st.markdown("**Breakdown:**")
                        for sub in item.get("subtopics"):
                            st.write(f"• {sub}")

# ── TAB: PYQ ARCHIVE ──
with tab_pap:
    papers = data.get("previous_papers") or []
    if papers:
        for p in papers:
            with st.container(border=True):
                p_col, b_col = st.columns([5, 1.5])
                with p_col:
                    st.markdown(f"**{p.get('title')}**")
                    if p.get("description"): st.caption(p.get("description"))
                with b_col:
                    st.link_button("View Archive", p.get("url", "#"), use_container_width=True)
    else:
        st.write("No papers found for this query.")

# ── TAB: RESOURCES ──
with tab_res:
    res = data.get("resources") or []
    if res:
        for r in res:
            with st.container(border=True):
                st.markdown(f'<span class="badge-pro">{r.get("type", "Source").upper()}</span>', unsafe_allow_html=True)
                st.markdown(f"#### {r.get('title')}")
                st.write(r.get("description"))
                st.link_button("Access Research", r.get("url", "#"))
    else:
        st.write("Scanning digital libraries...")

# ── TAB: VIDEO LAB ──
with tab_vid:
    vids = data.get("youtube_lectures") or []
    if vids:
        grid_cols = st.columns(2)
        for i, v in enumerate(vids):
            with grid_cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{v.get('title')}**")
                    v_url = v.get('url', '')
                    if "youtube.com" in v_url or "youtu.be" in v_url:
                        st.video(v_url)
                    else:
                        st.link_button("Watch on YouTube", v_url)
    else:
        st.write("Searching for curated playlists...")

st.markdown("<br><br><br>", unsafe_allow_html=True)
