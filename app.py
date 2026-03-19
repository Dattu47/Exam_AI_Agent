"""
ExamGenie AI — Official Examination Preparation Platform
4-section design: Syllabus | Strategy | Material | Videos
"""

import streamlit as st
import datetime
from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

CURRENT_YEAR = datetime.datetime.now().year

# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI — Exam Preparation",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Design System
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800&display=swap');

:root {
    --bg:      #08090E;
    --surface: #10131C;
    --card:    #14192A;
    --border:  rgba(255,255,255,0.07);
    --accent:  #C8FF00;
    --accent2: #5B96F7;
    --text:    #E8ECF3;
    --muted:   #64718A;
    --radius:  13px;
}

html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text);
    font-family: 'Inter', sans-serif;
}

footer, #MainMenu { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem !important; }

.brand { font-family:'Outfit',sans-serif; font-size:1.55rem; font-weight:800;
         color:var(--accent); letter-spacing:-0.5px; margin-bottom:2px; }
.brand-sub { font-size:0.72rem; color:var(--muted); margin-bottom:1.8rem; }
.current-board { font-size:0.9rem; font-weight:600; color:var(--text); }
.board-meta    { font-size:0.7rem; color:var(--muted); margin-bottom:1.8rem; }

/* ── Page title ── */
.app-title {
    font-family:'Outfit',sans-serif;
    font-size:2rem; font-weight:800;
    text-align:center; margin-bottom:2px;
}
.app-title span { color:var(--accent); }
.app-sub { text-align:center; color:var(--muted); font-size:0.88rem; margin-bottom:2rem; }

/* ── Search ── */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-size: 1rem !important;
    padding: 14px 20px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(200,255,0,0.07) !important;
}

/* ── Buttons ── */
div.stButton > button {
    background: var(--accent) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    height: 52px !important;
    font-size: 0.95rem !important;
    transition: opacity .2s !important;
}
div.stButton > button:hover { opacity:.85 !important; }
.stLinkButton a {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--accent) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* ── Sidebar nav re-style ── */
div[data-testid="stSidebar"] div.stRadio > label { display:none; }
div[data-testid="stSidebar"] div[role="radiogroup"] {
    display:flex; flex-direction:column; gap:3px;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    display:flex; align-items:center;
    padding:11px 14px !important; border-radius:11px !important;
    color:var(--muted) !important; font-size:0.92rem !important;
    font-weight:500 !important; cursor:pointer; transition:all .15s;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.04) !important; color:var(--text) !important;
}

/* ── Containers / cards ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.25rem 1.5rem !important;
}

/* ── Section headings ── */
.sec-title {
    font-family:'Outfit',sans-serif;
    font-size:1.35rem; font-weight:700;
    color:var(--text); margin-bottom:3px;
}
.sec-note { font-size:0.8rem; color:var(--muted); margin-bottom:1.5rem; }

/* ── About exam box ── */
.about-box {
    background:var(--card); border:1px solid var(--border);
    border-left:3px solid var(--accent2);
    border-radius:var(--radius); padding:18px 22px; margin-bottom:1rem;
}
.about-label { font-size:0.68rem; color:var(--muted); font-weight:700;
               text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }
.about-val   { font-size:0.97rem; color:var(--text); line-height:1.7; }

/* ── Deadline box ── */
.deadline-box {
    background:var(--card); border:1px solid var(--border);
    border-left:3px solid var(--accent);
    border-radius:var(--radius); padding:16px 22px; margin-bottom:1.5rem;
    display:flex; align-items:center; justify-content:space-between;
}
.dl-label { font-size:0.7rem; color:var(--muted); font-weight:700; text-transform:uppercase; }
.dl-val   { font-size:1.1rem; font-weight:700; color:var(--accent); margin-top:3px; }

/* ── Year badge ── */
.year-badge {
    background:rgba(200,255,0,0.1); border:1px solid rgba(200,255,0,0.25);
    color:var(--accent); border-radius:20px; padding:3px 12px;
    font-size:0.75rem; font-weight:700; display:inline-block; margin-bottom:1.5rem;
}

/* ── Topic chips ── */
.chip-grid { display:flex; flex-wrap:wrap; gap:7px; margin-top:.75rem; }
.chip {
    background:rgba(255,255,255,0.05); border:1px solid var(--border);
    color:var(--text); border-radius:20px; padding:4px 13px;
    font-size:0.78rem; font-weight:500;
}

/* ── Progress bar ── */
.prog-row { display:flex; justify-content:space-between;
            font-size:0.78rem; color:var(--muted); margin-bottom:5px; }
.prog-row span:last-child { color:var(--accent); font-weight:700; }
.prog-bg { background:rgba(255,255,255,0.05); border-radius:6px; height:7px; }
.prog-fg { border-radius:6px; height:7px; background:var(--accent); transition:width 1s; }

/* ── Syllabus topic row ── */
.syl-row { border-bottom:1px solid var(--border); padding:12px 0 10px; }
.syl-topic { font-size:0.95rem; font-weight:600; color:var(--text); margin-bottom:4px; }
.syl-subs  { font-size:0.8rem; color:var(--muted); line-height:1.7; }

/* ── Week expander ── */
.stExpander {
    border:1px solid var(--border) !important;
    border-radius:var(--radius) !important;
    background:var(--card) !important;
    margin-bottom:8px !important;
}

/* ── Day tasks ── */
.day-task {
    display:flex; align-items:flex-start; gap:10px;
    padding:7px 0; border-bottom:1px solid rgba(255,255,255,0.04);
    font-size:0.88rem; color:var(--text);
}
.task-dot { color:var(--accent); font-size:0.7rem; padding-top:3px; flex-shrink:0; }

/* ── Tip callout ── */
.tip-box {
    margin-top:10px; padding:10px 14px;
    background:rgba(200,255,0,0.05); border-left:3px solid var(--accent);
    border-radius:8px; font-size:0.83rem; color:var(--text);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [("agent", None), ("results", None), ("last_exam", ""), ("updated_at", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.agent is None:
    st.session_state.agent = ResearchAgent()


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline(exam_name: str) -> dict | None:
    with st.status(f"Researching **{exam_name}** ({CURRENT_YEAR})…", expanded=True) as status:
        try:
            agent = st.session_state.agent

            status.update(label="Searching official portals and study sites…")
            raw = agent.search_agent.find_resources(exam_name)

            status.update(label="Reading and extracting syllabus content…")
            s_urls = [(r.url if hasattr(r, "url") else r.get("url", ""))
                      for r in raw.get("syllabus", [])[:12]]
            pages, pdfs = agent.scraping_agent.scrape_sources(s_urls, max_pages=10)

            status.update(label="Building structured syllabus…")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(
                exam_name, pages, s_urls, raw.get("exam_pattern", [])
            )

            status.update(label="Creating your personalised study plan…")
            plan = agent.study_agent.build_plan(exam_name, syllabus, topics, weeks=4)

            status.update(label="Compiling resources, papers, and videos…")
            final = agent.response_agent.format_final_response(
                exam_name,
                raw.get("exam_info", []),
                raw.get("syllabus", []),
                raw.get("previous_papers", []),
                raw.get("study_resources", []),
                raw.get("youtube_lectures", []),
                syllabus, topics, plan, pdfs, chunks,
            )

            st.session_state.updated_at = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            status.update(label="Done! Your preparation plan is ready.", state="complete", expanded=False)
            return final

        except Exception as e:
            status.update(label="Something went wrong.", state="error", expanded=True)
            st.error(str(e))
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Top: Brand + Persistent Search
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="app-title">🎯 <span>ExamGenie</span> AI</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="app-sub">Your complete exam preparation companion for {CURRENT_YEAR} — '
    'syllabus, strategy, papers &amp; videos in one place.</div>',
    unsafe_allow_html=True,
)

sc1, sc2 = st.columns([5, 1])
with sc1:
    exam_q = st.text_input(
        "exam_search",
        value=st.session_state.last_exam,
        placeholder=f"Search any exam for {CURRENT_YEAR}: JEE, UPSC, GATE, TCS NQT, CAT…",
        label_visibility="collapsed",
    )
with sc2:
    go = st.button("Search 🔍", use_container_width=True)

if go and exam_q.strip():
    result = run_pipeline(exam_q.strip())
    if result:
        st.session_state.results = result
        st.session_state.last_exam = exam_q.strip()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand">🎯 ExamGenie AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Exam Preparation Platform</div>', unsafe_allow_html=True)

    curr = st.session_state.last_exam or "—"
    st.markdown(f'<div class="current-board">📌 {curr}</div>', unsafe_allow_html=True)
    if st.session_state.updated_at:
        st.markdown(f'<div class="board-meta">Updated: {st.session_state.updated_at}</div>', unsafe_allow_html=True)

    st.markdown("---")
    nav = st.radio(
        "Navigate",
        options=[
            "📚 Syllabus",
            "🗓️ Preparation Strategy",
            "📖 Preparation Material",
            "▶️ YouTube Videos",
        ],
        index=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Empty State
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.results:
    st.markdown("""
    <div style="text-align:center; padding:5rem 2rem; opacity:0.45;">
        <div style="font-size:4rem; margin-bottom:1rem;">🎯</div>
        <h3 style="font-family:'Outfit',sans-serif; font-weight:700; margin-bottom:.5rem;">Ready when you are.</h3>
        <p style="font-size:0.88rem;">Type the name of any competitive exam above and press Search.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────
data      = st.session_state.results
exam_name = st.session_state.last_exam
info      = data.get("about_exam") or {}
syl       = data.get("syllabus") or []
topics    = data.get("important_topics") or []
plan      = data.get("study_plan") or []
papers    = data.get("previous_papers") or []
resources = data.get("resources") or []
videos    = data.get("youtube_lectures") or []

year_label = f"Academic Year {CURRENT_YEAR}"


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — SYLLABUS
# (includes exam overview + full syllabus hierarchy + important topics)
# ─────────────────────────────────────────────────────────────────────────────
if nav == "📚 Syllabus":
    st.markdown(f'<div class="sec-title">{exam_name} — Syllabus & Exam Details</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    # About exam
    desc = (info.get("description") or "").strip()
    if desc:
        st.markdown(f"""
        <div class="about-box">
            <div class="about-label">About the Exam</div>
            <div class="about-val">{desc}</div>
        </div>""", unsafe_allow_html=True)

    # Deadline
    dl = info.get("deadline", "Check Official Site")
    st.markdown(f"""
    <div class="deadline-box">
        <div>
            <div class="dl-label">📅 Application / Registration Deadline</div>
            <div class="dl-val">{dl}</div>
        </div>
        <span style="font-size:2rem;">📋</span>
    </div>""", unsafe_allow_html=True)

    # Progress tracker
    done_cnt = sum(1 for k in st.session_state if k.startswith(f"syl_{exam_name}_") and st.session_state[k])
    total    = max(len(syl), 1)
    pct      = int(done_cnt / total * 100)
    st.markdown(f"""
    <div class="prog-row"><span>Syllabus Progress</span><span>{pct}%</span></div>
    <div class="prog-bg"><div class="prog-fg" style="width:{pct}%;"></div></div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Syllabus topics with checkboxes
    if syl:
        for item in syl:
            topic = item.get("topic") if isinstance(item, dict) else str(item)
            subs  = item.get("subtopics", []) if isinstance(item, dict) else []
            key   = f"syl_{exam_name}_{topic}"

            col_chk, col_txt = st.columns([1, 18])
            with col_chk:
                st.checkbox(" ", value=st.session_state.get(key, False), key=key, label_visibility="hidden")
            with col_txt:
                st.markdown(f'<div class="syl-topic">{"✅ " if st.session_state.get(key) else ""}{topic}</div>', unsafe_allow_html=True)
                if subs:
                    st.markdown(
                        f'<div class="syl-subs">' + " &nbsp;·&nbsp; ".join(subs[:14]) + '</div>',
                        unsafe_allow_html=True
                    )
            st.markdown('<div style="border-bottom:1px solid rgba(255,255,255,0.05); margin:2px 0;"></div>', unsafe_allow_html=True)
    else:
        st.warning("Syllabus not available. Please try searching again or visit the official site.")

    # High-weightage topics chips
    if topics:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title" style="font-size:1.1rem;">🔥 High-Weightage Topics</div>', unsafe_allow_html=True)
        chips_html = "".join([f'<span class="chip">{t}</span>' for t in topics[:18]])
        st.markdown(f'<div class="chip-grid">{chips_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — PREPARATION STRATEGY
# (4-week plan whose topics are drawn directly from the syllabus above)
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "🗓️ Preparation Strategy":
    st.markdown(f'<div class="sec-title">4-Week Preparation Strategy — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-note">Day-by-day timetable built around your {exam_name} syllabus topics. '
        f'Topics are sourced directly from the Syllabus section.</div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    # Show which syllabus topics are covered
    if syl:
        covered = [item.get("topic") if isinstance(item, dict) else str(item) for item in syl[:6]]
        chips_html = "".join([f'<span class="chip">📌 {t}</span>' for t in covered])
        st.markdown(f'<div style="margin-bottom:1.5rem;" class="chip-grid">{chips_html}</div>', unsafe_allow_html=True)

    if plan:
        for wk in plan:
            label = f"Week {wk.get('week')}  —  {wk.get('focus', '')}"
            with st.expander(label, expanded=(wk.get("week") == 1)):
                tasks = wk.get("tasks") or []
                for t in tasks:
                    st.markdown(
                        f'<div class="day-task"><span class="task-dot">◈</span><span>{t}</span></div>',
                        unsafe_allow_html=True
                    )
                if wk.get("tip"):
                    st.markdown(
                        f'<div class="tip-box">💡 <b>Strategy Tip:</b> {wk["tip"]}</div>',
                        unsafe_allow_html=True
                    )
    else:
        st.info("Study plan not generated. Please regenerate by searching again.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PREPARATION MATERIAL
# (PYQs + books + notes + free courses)
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "📖 Preparation Material":
    st.markdown(f'<div class="sec-title">Preparation Material — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-note">Previous year papers, recommended books, notes, and free online courses.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    # PYQ Section
    st.markdown("#### 📄 Previous Year Question Papers")
    if papers:
        for p in papers:
            url   = p.get("url", "#")
            title = p.get("title", "Question Paper")
            ptype = p.get("type", "link")
            badge = "📄 PDF" if ptype == "pdf" else "🔗 Web"
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{title}**")
                    st.caption(badge)
                with c2:
                    st.link_button("Open →", url, use_container_width=True)
    else:
        st.info("No question papers found. Search on the official website.")

    st.markdown("---")

    # Study Resources Section
    st.markdown("#### 📚 Study Resources & Books")
    if resources:
        for r in resources:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{r.get('title', 'Resource')}**")
                with c2:
                    st.link_button("Open →", r.get("url", "#"), use_container_width=True)
    else:
        st.info("No study material found. Try a more specific exam name.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — YOUTUBE VIDEOS
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "▶️ YouTube Videos":
    st.markdown(f'<div class="sec-title">Video Lectures — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-note">Curated {CURRENT_YEAR} playlists and video lectures for {exam_name} preparation.</div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    if videos:
        vcols = st.columns(2)
        for i, v in enumerate(videos[:10]):
            url   = v.get("url", "")
            title = v.get("title", "Lecture")
            with vcols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    if "youtube.com" in url or "youtu.be" in url:
                        try:
                            st.video(url)
                        except Exception:
                            pass
                    st.link_button("▶️ Watch on YouTube", url, use_container_width=True)
    else:
        st.info("No video lectures found. Try searching with the exact exam name.")


st.markdown("<br><br><br>", unsafe_allow_html=True)
