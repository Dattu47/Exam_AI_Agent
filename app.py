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
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

/* ── Design System ── */
:root {
    --bg-main: #06070B;
    --bg-card: #0F1219;
    --bg-card-hover: #141822;
    --primary: #CCFF00;             /* Electric Lime */
    --primary-glow: rgba(204, 255, 0, 0.15);
    --secondary: #7000FF;            /* Electric Violet */
    --text-main: #FFFFFF;
    --text-sub: #94A3B8;
    --border: rgba(255, 255, 255, 0.08);
    --border-bright: rgba(255, 255, 255, 0.15);
    --radius-lg: 20px;
    --radius-md: 12px;
    --transition: cubic-bezier(0.4, 0, 0.2, 1) 0.3s;
}

/* ── Global Resets ── */
.stApp, html, body {
    background-color: var(--bg-main) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Hide Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding: 4rem 2rem !important; max-width: 1200px; }

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.02em;
}

/* ── Hero ── */
.hero-centered {
    text-align: center;
    margin-bottom: 4rem;
}
.hero-title {
    font-size: 4rem;
    font-weight: 800;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #FFF 0%, #AAA 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-sub);
    max-width: 700px;
    margin: 0 auto;
    font-weight: 400;
    line-height: 1.6;
}

/* ── Search Experience ── */
.search-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 2.5rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    margin-bottom: 3rem;
}

.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: #FFF !important;
    padding: 1rem 1.5rem !important;
    font-size: 1.1rem !important;
    height: 60px !important;
    transition: var(--transition) !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 1px var(--primary) !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

/* ── Buttons ── */
div.stButton > button:first-child {
    background: var(--primary) !important;
    color: #000 !important;
    height: 60px !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    transition: var(--transition) !important;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px var(--primary-glow) !important;
}

/* ── Custom Status Card ── */
[data-testid="stStatus"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}

/* ── Results Dashboard ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 8px !important;
    margin-bottom: 2rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-sub) !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: #000 !important;
    border-color: var(--primary) !important;
}

/* Result Item Cards */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 2rem !important;
    transition: var(--transition) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    border-color: var(--border-bright) !important;
    transform: translateY(-4px);
}

/* Progress Section */
.prog-container {
    background: rgba(255,255,255,0.03);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    margin-bottom: 2rem;
}
.prog-bar-bg {
    width: 100%;
    height: 8px;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    overflow: hidden;
}
.prog-bar-fill {
    height: 100%;
    background: var(--primary);
    box-shadow: 0 0 10px var(--primary-glow);
    transition: width 1s ease-in-out;
}

/* ── Badges ── */
.badge {
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-pdf { background: rgba(255, 69, 58, 0.1); color: #FF453A; border: 1px solid rgba(255,69,58,0.2); }
.badge-video { background: rgba(0, 122, 255, 0.1); color: #0A84FF; border: 1px solid rgba(0,122,255,0.2); }
.badge-study { background: rgba(50, 215, 75, 0.1); color: #32D74B; border: 1px solid rgba(50,215,75,0.2); }

/* Custom Checkbox */
.stCheckbox div[data-testid="stMarkdownContainer"] p {
    color: var(--text-sub) !important;
    font-size: 0.9rem !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-main); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 10px; }
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


st.markdown("""
<div class="hero-centered">
    <div class="hero-title">ExamGenie AI</div>
    <p class="hero-subtitle">
        Intelligent multi-agent search for competitive examinations. 
        Curated syllabi, past archives, and personalized strategy boards in real-time.
    </p>
</div>
""", unsafe_allow_html=True)


# ── Search Panel ──────────────────────────────────────────────────────────────
st.markdown('<div class="search-container">', unsafe_allow_html=True)

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
        st.markdown('<p style="font-weight:700; color:var(--text-sub); font-size:0.85rem; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:12px;">🎯 High-Yield Focus Areas</p>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, t in enumerate(topics):
            cols[i % 3].markdown(f'<div style="background:rgba(255,255,255,0.03); border:1px solid var(--border); border-radius:10px; padding:12px; margin-bottom:10px; font-weight:600; color:var(--text-main); font-size:0.95rem;">{t}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Progress summary bar ──
    syllabus = data.get("syllabus") or []
    total_topics = len(syllabus)
    pct = _progress_pct(exam_name.strip(), total_topics)

    if total_topics:
        st.markdown(f"""
        <div class="prog-container">
            <div style="display:flex; justify-content:space-between; margin-bottom:12px; align-items:center;">
                <span style="color:var(--text-sub); font-size:0.85rem; font-weight:700; letter-spacing:0.04em; text-transform:uppercase;">Board Progress</span>
                <span style="color:var(--primary); font-size:1rem; font-weight:800;">{pct}%</span>
            </div>
            <div class="prog-bar-bg">
                <div class="prog-bar-fill" style="width: {pct}%;"></div>
            </div>
            <div style="margin-top:10px; font-size:0.75rem; color:var(--text-sub); font-weight:500;">
                {sum(1 for k,v in st.session_state.progress.items() if k.startswith(f"prog_{exam_name.strip()}_") and v)} of {total_topics} topics mastered
            </div>
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
                    badge_cls = "badge-pdf" if p.get("type") == "pdf" else "badge-video"
                    badge_lbl = "DOC" if p.get("type") == "pdf" else "WEB"
                    st.markdown(
                        f'<span class="badge {badge_cls}">{badge_lbl}</span>',
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
                        f'<span class="badge badge-study">Week {week_num}</span>'
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
                    badge_cls = "badge-pdf" if r.get("type") == "pdf" else "badge-study"
                    badge_lbl = "PDF" if r.get("type") == "pdf" else "SOURCE"
                    st.markdown(
                        f'<span class="badge {badge_cls}">{badge_lbl}</span>',
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
                        '<span class="badge badge-video">VIDEO</span>',
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



