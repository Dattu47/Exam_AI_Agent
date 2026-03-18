"""
Exam Research AI Agent — Streamlit App
A premium multi-agent exam preparation assistant with a stunning UI.
"""

import streamlit as st
from exam_ai_agent.agents.research_agent import ResearchAgent

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI · Your Smart Study Companion",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── Root tokens ── */
:root {
    --primary: #6C63FF;
    --primary-dark: #4B44CC;
    --secondary: #FF6584;
    --accent: #43D9AD;
    --bg-dark: #0F1117;
    --bg-card: #1A1D2E;
    --bg-card2: #21253A;
    --text-primary: #F0F2FF;
    --text-muted: #8B92B8;
    --border: rgba(108,99,255,0.25);
    --glow: 0 0 30px rgba(108,99,255,0.3);
    --radius: 16px;
    --transition: 0.25s ease;
}

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding: 2rem 3rem !important; max-width: 1400px; }

/* ── Hero Section ── */
.hero-wrapper {
    background: linear-gradient(135deg, #1A1D2E 0%, #12152B 50%, #1A1D2E 100%);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 1.75rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--glow);
}
.hero-wrapper::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(108,99,255,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero-wrapper::after {
    content: '';
    position: absolute;
    bottom: -40px; left: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(67,217,173,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1.15;
    margin: 0 0 0.6rem;
    background: linear-gradient(135deg, #F0F2FF 0%, #A89FFF 55%, #43D9AD 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-subtitle {
    font-size: 1rem;
    color: var(--text-muted);
    line-height: 1.6;
    margin: 0;
}

/* ── Search bar card ── */
.search-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

/* ── Streamlit input overrides ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(108,99,255,0.35) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-size: 1rem !important;
    padding: 0.8rem 1.2rem !important;
    transition: border-color var(--transition), box-shadow var(--transition) !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.2) !important;
    outline: none !important;
}
.stTextInput > label {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 20px rgba(108,99,255,0.4) !important;
    transition: all var(--transition) !important;
    width: 100% !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(108,99,255,0.55) !important;
}
.stButton > button[kind="primary"]:active {
    transform: translateY(0) !important;
}

/* ── Secondary / regular button ── */
.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: rgba(108,99,255,0.08) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 14px !important;
    padding: 6px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.1rem !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all var(--transition) !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
    color: #fff !important;
    box-shadow: 0 2px 12px rgba(108,99,255,0.35) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

/* ── Cards (containers with border) ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.25rem !important;
    transition: border-color var(--transition), box-shadow var(--transition) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    border-color: rgba(108,99,255,0.5) !important;
    box-shadow: 0 4px 20px rgba(108,99,255,0.12) !important;
}

/* ── Expander ── */
details {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.25rem 0.5rem !important;
}
summary {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    cursor: pointer !important;
}

/* ── Status widget ── */
[data-testid="stStatus"] {
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

/* ── Info / warning / error boxes ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}
[data-baseweb="notification"] {
    border-radius: 12px !important;
}

/* ── Progress ── */
.topic-done { opacity: 0.5; }
.topic-done strong { text-decoration: line-through; }

/* ── Checkbox ── */
.stCheckbox label {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Link buttons ── */
.stLinkButton a {
    background: rgba(108,99,255,0.12) !important;
    color: var(--primary) !important;
    border: 1.5px solid rgba(108,99,255,0.35) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
    text-decoration: none !important;
}
.stLinkButton a:hover {
    background: var(--primary) !important;
    color: #fff !important;
    border-color: var(--primary) !important;
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
}
.section-header h2 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
}

/* ── Result cards ── */
.result-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.badge-pdf { background: rgba(255,101,132,0.15); color: #FF6584; border: 1px solid rgba(255,101,132,0.3); }
.badge-link { background: rgba(67,217,173,0.15); color: #43D9AD; border: 1px solid rgba(67,217,173,0.3); }
.badge-video { background: rgba(255,0,0,0.12); color: #ff6b6b; border: 1px solid rgba(255,0,0,0.25); }
.badge-week { background: rgba(108,99,255,0.15); color: var(--primary); border: 1px solid rgba(108,99,255,0.3); }

/* ── Spinner / Loading overrides ── */
.stSpinner > div {
    border-top-color: var(--primary) !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-muted);
}
.empty-state .icon { font-size: 3rem; margin-bottom: 0.75rem; }
.empty-state p { font-size: 1rem; }

/* ── Progress ring ── */
.progress-summary {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(108,99,255,0.08);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 12px;
    padding: 0.9rem 1.25rem;
    margin-bottom: 1.25rem;
}
.progress-summary .bar-wrap {
    flex: 1;
    height: 6px;
    background: rgba(255,255,255,0.08);
    border-radius: 10px;
    overflow: hidden;
}
.progress-summary .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    border-radius: 10px;
    transition: width 0.5s ease;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(108,99,255,0.4); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Session state initialization ──────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = ResearchAgent()
if "progress" not in st.session_state:
    st.session_state.progress = {}
if "results" not in st.session_state:
    st.session_state.results = None
if "last_exam" not in st.session_state:
    st.session_state.last_exam = ""


# ── Step-by-step research runner (gives real live progress) ───────────────────
def run_research_with_progress(exam_name: str, force: bool, status_widget) -> dict | None:
    """
    Runs the full research pipeline step by step, updating `status_widget`
    after each agent so the user sees real-time progress instead of a spinner.
    Returns the final result dict or None on hard failure.
    """
    agent = st.session_state.agent
    db = agent.db

    # ── 0. Log query ──
    db.save_user_query(exam_name)

    # ── 1. Cache check ──
    if not force:
        cached = db.get_exam_resources(exam_name)
        if cached:
            status_widget.update(label="⚡  Loaded from cache instantly!", state="complete", expanded=False)
            return cached

    result = {"syllabus": [], "previous_papers": [], "important_topics": [],
               "study_plan": [], "resources": [], "youtube_lectures": []}

    # ── 2. Search Agent ──
    status_widget.update(label="🔍  Search Agent — querying the web…", state="running", expanded=True)
    try:
        search_grouped = agent.search_agent.find_resources(exam_name)
    except Exception as e:
        status_widget.update(label="❌  Search failed.", state="error", expanded=True)
        st.error(f"Web search failed: {e}")
        return None

    syllabus_results  = search_grouped.get("syllabus", [])
    papers_results    = search_grouped.get("previous_papers", [])
    pattern_results   = search_grouped.get("exam_pattern", [])
    study_results     = search_grouped.get("study_resources", [])
    youtube_results   = search_grouped.get("youtube_lectures", [])

    syllabus_urls    = [(r.url if hasattr(r, "url") else r.get("url", "")) for r in syllabus_results[:8]]
    paper_page_urls  = [(r.url if hasattr(r, "url") else r.get("url", "")) for r in papers_results[:2]]

    # ── 3. Scraping Agent ──
    status_widget.update(label="🕸️  Scraping Agent — reading top pages…", state="running", expanded=True)
    scraped_pages, hidden_pdfs = agent.scraping_agent.scrape_sources(
        syllabus_urls + paper_page_urls, max_pages=6
    )

    # ── 4. Processing Agent ──
    status_widget.update(label="⚙️  Processing Agent — extracting & refining topics…", state="running", expanded=True)
    scraped_syllabus_items, important_topics, raw_text_chunks = agent.processing_agent.extract_and_process(
        exam_name, scraped_pages, syllabus_urls, pattern_results
    )

    # ── 5. Study Plan Agent ──
    status_widget.update(label="📅  Study Plan Agent — building your schedule…", state="running", expanded=True)
    study_plan = agent.study_agent.build_plan(exam_name, scraped_syllabus_items, important_topics, weeks=4)

    # ── 6. Response Agent ──
    status_widget.update(label="📦  Compiling final results…", state="running", expanded=True)
    final_response = agent.response_agent.format_final_response(
        exam_name, syllabus_results, papers_results, study_results,
        youtube_results, scraped_syllabus_items, important_topics,
        study_plan, hidden_pdfs, raw_text_chunks
    )

    # ── 7. Cache save ──
    has_content = (bool(final_response.get("syllabus")) or
                   bool(final_response.get("previous_papers")) or
                   bool(final_response.get("resources")))
    if has_content:
        db.save_exam_resources(exam_name, final_response)
        if study_plan:
            db.save_study_plan(exam_name, study_plan)

    return final_response


def _progress_pct(exam_name: str, total: int) -> int:
    if total == 0:
        return 0
    done = sum(
        1 for k, v in st.session_state.progress.items()
        if k.startswith(f"prog_{exam_name}_") and v
    )
    return int((done / total) * 100)


# ── Hero Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-title">🎓 ExamGenie AI</div>
    <p class="hero-subtitle">
        Your AI-powered exam preparation assistant — get a curated syllabus, previous papers,
        a personalised study plan, and top resources for any competitive exam.
    </p>
</div>
""", unsafe_allow_html=True)


# ── Search Panel ──────────────────────────────────────────────────────────────
st.markdown('<div class="search-card">', unsafe_allow_html=True)

col_input, col_opts = st.columns([5, 2])
with col_input:
    exam_name = st.text_input(
        "🎯  Target Exam",
        placeholder="e.g.  GATE CSE,  JEE Main,  UPSC CSE,  CAT,  NEET ...",
        key="exam_input",
        label_visibility="visible",
    )
with col_opts:
    st.markdown("<br>", unsafe_allow_html=True)
    force_refresh = st.checkbox(
        "🔄  Force Fresh Search",
        help="Bypass cached results and re-scrape the web. Use when data seems outdated.",
        key="force_refresh_cb"
    )

search_clicked = st.button("🚀  Generate Study Strategy", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ── Guard: no exam entered ─────────────────────────────────────────────────────
if not exam_name or not exam_name.strip():
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🎓</div>
        <p>Type the name of any exam above and hit <strong>Generate Study Strategy</strong>.<br>
        Our AI agents will research and build your complete preparation plan.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Clear results on new exam ──────────────────────────────────────────────────
if st.session_state.last_exam != exam_name.strip():
    st.session_state.results = None



# ── Run research on button click ───────────────────────────────────────────────
if search_clicked:
    with st.status("🔍  Starting research pipeline…", expanded=True) as status:
        try:
            res = run_research_with_progress(exam_name.strip(), force=force_refresh, status_widget=status)
        except Exception as e:
            res = None
            status.update(label="❌  An unexpected error occurred.", state="error", expanded=True)
            st.error(f"Pipeline error: {e}")

        if res:
            has_content = any([
                res.get("syllabus"), res.get("previous_papers"),
                res.get("resources"), res.get("study_plan"),
            ])
            if has_content:
                st.session_state.results = res
                st.session_state.last_exam = exam_name.strip()
                status.update(label="✅  Strategy ready!", state="complete", expanded=False)
            else:
                # Pipeline ran but Groq returned nothing (rate limited)
                status.update(label="⚠️  AI processing returned empty — rate limit likely.", state="error", expanded=False)
                if st.session_state.results:
                    st.warning("⚠️ Fresh search returned no AI content. Showing your previously cached results below.")
                else:
                    st.warning(
                        "⚠️ **Server Busy.** We couldn't generate results right now due to high demand.\n\n"
                        "Please try again in a minute, or load your previous results by **searching without Force Fresh Search**."
                    )
        elif res is None and st.session_state.results:
            # Soft failure — keep showing old results
            pass


# ── Results display ────────────────────────────────────────────────────────────
data = st.session_state.results
if not data:
    st.stop()

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_syl, tab_pap, tab_plan, tab_res, tab_vid = st.tabs([
    "📋  Syllabus",
    "📄  Previous Papers",
    "📅  Study Plan",
    "📚  Resources",
    "▶️  Video Lectures",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 · SYLLABUS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_syl:
    st.markdown("""
    <div class="section-header">
        <h2>📋 Official Syllabus &amp; Important Topics</h2>
    </div>
    """, unsafe_allow_html=True)

    # ── Important topics callout ──
    topics = data.get("important_topics") or []
    if topics:
        with st.expander("🎯  High-Yield Topics identified by AI", expanded=True):
            cols = st.columns(3)
            for i, t in enumerate(topics):
                cols[i % 3].markdown(f"● **{t}**")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Progress summary bar ──
    syllabus = data.get("syllabus") or []
    total_topics = len(syllabus)
    pct = _progress_pct(exam_name.strip(), total_topics)

    if total_topics:
        st.markdown(f"""
        <div class="progress-summary">
            <span style="color:var(--text-muted);font-size:0.85rem;white-space:nowrap;">
                📈 Progress &nbsp; <strong style="color:var(--text-primary)">{pct}%</strong>
            </span>
            <div class="bar-wrap">
                <div class="bar-fill" style="width:{pct}%"></div>
            </div>
            <span style="color:var(--text-muted);font-size:0.82rem;white-space:nowrap;">
                {sum(1 for k,v in st.session_state.progress.items() if k.startswith(f"prog_{exam_name.strip()}_") and v)} / {total_topics} done
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ── Topic list ──
    if syllabus:
        for idx, s in enumerate(syllabus):
            topic_title = s.get("topic", f"Topic {idx + 1}")
            cb_key = f"prog_{exam_name.strip()}_{topic_title}"
            if cb_key not in st.session_state.progress:
                st.session_state.progress[cb_key] = False

            col_cb, col_body = st.columns([1, 18])
            with col_cb:
                st.session_state.progress[cb_key] = st.checkbox(
                    "Mark complete",
                    key=cb_key,
                    value=st.session_state.progress[cb_key],
                    label_visibility="hidden",
                )
            with col_body:
                if st.session_state.progress[cb_key]:
                    st.markdown(
                        f'<p class="topic-done">✅ <strong>{topic_title}</strong> &nbsp;'
                        f'<span style="font-size:0.78rem;color:var(--accent)">Completed</span></p>',
                        unsafe_allow_html=True,
                    )
                else:
                    with st.expander(f"**{topic_title}**"):
                        subtopics = s.get("subtopics", [])
                        if isinstance(subtopics, list) and subtopics:
                            st.markdown("**Subtopics:**")
                            for sub in subtopics:
                                st.markdown(f"&nbsp;&nbsp;▸ {sub}")
                            st.write("")
                        desc = s.get("description", "No detailed description available.")
                        st.write(desc)
                        if s.get("source_url"):
                            st.markdown(f"[🔗 View Source]({s['source_url']})")
    else:
        st.markdown('<div class="empty-state"><div class="icon">📋</div><p>No structured syllabus could be extracted. Try a more specific exam name.</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 · PREVIOUS PAPERS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_pap:
    st.markdown("""
    <div class="section-header">
        <h2>📄 Previous Year Question Papers</h2>
    </div>
    """, unsafe_allow_html=True)

    papers = data.get("previous_papers") or []
    if papers:
        for p in papers:
            with st.container(border=True):
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    badge_cls = "badge-pdf" if p.get("type") == "pdf" else "badge-link"
                    badge_lbl = "📄 PDF" if p.get("type") == "pdf" else "🌐 Link"
                    st.markdown(
                        f'<span class="result-badge {badge_cls}">{badge_lbl}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{p.get('title', 'Untitled Paper')}**")
                    desc = p.get("description", "")
                    if desc:
                        st.caption(desc)
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_label = "📥 Download" if p.get("type") == "pdf" else "🔗 Open"
                    st.link_button(btn_label, p.get("url", "#"), use_container_width=True)
    else:
        st.markdown('<div class="empty-state"><div class="icon">📄</div><p>No previous year papers found for this exam.</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 · STUDY PLAN
# ═══════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.markdown("""
    <div class="section-header">
        <h2>📅 AI-Generated Study Plan</h2>
    </div>
    """, unsafe_allow_html=True)
    st.caption("A rigorous, week-by-week schedule tailored to your exam syllabus and important topics.")

    plan = data.get("study_plan") or []
    if plan:
        for w in plan:
            week_num = w.get("week", "?")
            focus = w.get("focus", "General Preparation")
            tip = w.get("tip", "")
            tasks = w.get("tasks") or []

            with st.container(border=True):
                col_badge, col_head = st.columns([1, 8])
                with col_badge:
                    st.markdown(
                        f'<div style="text-align:center;padding-top:4px">'
                        f'<span class="result-badge badge-week">Wk {week_num}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_head:
                    st.markdown(f"### {focus}")

                if tip:
                    st.info(f"💡 **Strategy Tip:** {tip}")

                for t in tasks:
                    st.markdown(f"&nbsp;&nbsp;✦ {t}")
    else:
        st.markdown('<div class="empty-state"><div class="icon">📅</div><p>No study plan was generated. Try expanding your search or running a fresh search.</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 · RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_res:
    st.markdown("""
    <div class="section-header">
        <h2>📚 Books, Courses &amp; Online Resources</h2>
    </div>
    """, unsafe_allow_html=True)

    resources = data.get("resources") or []
    if resources:
        for r in resources:
            with st.container(border=True):
                col_text, col_btn = st.columns([5, 1])
                with col_text:
                    badge_cls = "badge-pdf" if r.get("type") == "pdf" else "badge-link"
                    badge_lbl = "📄 PDF" if r.get("type") == "pdf" else "🌐 Web"
                    st.markdown(
                        f'<span class="result-badge {badge_cls}">{badge_lbl}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{r.get('title', 'Resource')}**")
                    desc = r.get("description", "")
                    if desc:
                        st.caption(desc)
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.link_button("🌐 Open", r.get("url", "#"), use_container_width=True)
    else:
        st.markdown('<div class="empty-state"><div class="icon">📚</div><p>No external resources were found. Try a fresh search.</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 · VIDEO LECTURES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_vid:
    st.markdown("""
    <div class="section-header">
        <h2>▶️ YouTube Playlists &amp; Video Lectures</h2>
    </div>
    """, unsafe_allow_html=True)

    yt_links = data.get("youtube_lectures") or []
    if yt_links:
        vid_cols = st.columns(2)
        for i, r in enumerate(yt_links):
            with vid_cols[i % 2]:
                with st.container(border=True):
                    st.markdown(
                        '<span class="result-badge badge-video">▶ YouTube</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{r.get('title', 'YouTube Video')}**")
                    url = r.get("url", "")
                    if url:
                        try:
                            st.video(url)
                        except Exception:
                            pass
                        st.link_button("▶️ Open on YouTube", url, use_container_width=True)
    else:
        st.markdown('<div class="empty-state"><div class="icon">▶️</div><p>No YouTube playlists found. Try searching manually on YouTube.</p></div>', unsafe_allow_html=True)



