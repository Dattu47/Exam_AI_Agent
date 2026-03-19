"""
ExamGenie AI — Official Examination Intelligence Platform
Clean, professional SaaS UI for students. No jargon. Only value.
"""

import streamlit as st
import datetime
from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI — Exam Preparation Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap');

/* ── Global ── */
:root {
    --bg:      #0A0D12;
    --surface: #111620;
    --card:    #161C28;
    --border:  rgba(255,255,255,0.07);
    --accent:  #C8FF00;
    --accent2: #4F8EF7;
    --text:    #EDF0F4;
    --muted:   #6B7280;
    --green:   #29C97A;
    --radius:  14px;
}

html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text);
    font-family: 'Inter', sans-serif;
}

/* ── Hide Streamlit chrome ── */
footer, #MainMenu { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem !important; }

.brand-logo {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--accent);
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
}
.brand-sub { font-size: 0.72rem; color: var(--muted); margin-bottom: 2rem; }
.board-title { font-size: 0.95rem; font-weight: 600; color: var(--text); }
.board-time  { font-size: 0.7rem; color: var(--muted); margin-bottom: 1.8rem; }

/* ── Page heading ── */
.page-brand {
    font-family: 'Outfit', sans-serif;
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--text);
    text-align: center;
    margin-bottom: 0.25rem;
}
.page-brand span { color: var(--accent); }
.page-tagline {
    text-align: center;
    color: var(--muted);
    font-size: 0.9rem;
    margin-bottom: 2rem;
}

/* ── Search bar ── */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-size: 1rem !important;
    padding: 14px 20px !important;
    transition: border 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(200,255,0,0.08) !important;
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
    transition: opacity 0.2s, transform 0.1s !important;
}
div.stButton > button:hover {
    opacity: 0.88 !important;
    transform: scale(1.01) !important;
}
.stLinkButton a {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--accent) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
}

/* ── Nav radio ── */
div[data-testid="stSidebar"] div.stRadio > label { display: none; }
div[data-testid="stSidebar"] div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 10px 14px !important;
    border-radius: 10px !important;
    cursor: pointer;
    color: var(--muted) !important;
    font-size: 0.9rem !important;
    transition: background 0.15s !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.05) !important;
    color: var(--text) !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] label {
    background: rgba(200,255,0,0.1) !important;
    color: var(--accent) !important;
}

/* ── Containers ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.25rem 1.5rem !important;
}

/* ── Progress bar ── */
.prog-wrap { background: rgba(255,255,255,0.05); border-radius: 6px; overflow: hidden; height: 7px; }
.prog-fill  { height: 100%; border-radius: 6px; background: var(--accent); transition: width 1s; }

/* ── Section heading ── */
.sec-head {
    font-family: 'Outfit', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.sec-sub { font-size: 0.82rem; color: var(--muted); margin-bottom: 1.5rem; }

/* ── Chip ── */
.chip {
    display: inline-block;
    background: rgba(200,255,0,0.1);
    border: 1px solid rgba(200,255,0,0.25);
    color: var(--accent);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.77rem;
    font-weight: 600;
    margin: 3px 2px;
}

/* ── Tag bar ── */
.tag-bar { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.75rem; }

/* ── Topic Card ── */
.topic-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 10px;
}
.topic-title { font-weight: 600; font-size: 1rem; margin-bottom: 6px; }
.topic-sub   { color: var(--muted); font-size: 0.82rem; line-height: 1.7; }

/* ── Info box ── */
.info-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 1rem;
}
.info-label { font-size: 0.72rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 5px; }
.info-value { font-size: 1rem; font-weight: 500; color: var(--text); }

/* ── Week expander ── */
.stExpander { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; background: var(--card) !important; margin-bottom: 8px !important; }
.stExpander > details > summary { font-size: 0.95rem !important; font-weight: 600 !important; }

/* ── Chat ── */
.stChatMessage { background: var(--card) !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [
    ("agent", None), ("results", None),
    ("last_exam", ""), ("updated_at", ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.agent is None:
    st.session_state.agent = ResearchAgent()


# ─────────────────────────────────────────────────────────────────────────────
# 4. RESEARCH PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline(exam_name: str) -> dict | None:
    with st.status(f"Researching **{exam_name}**…", expanded=True) as status:
        try:
            agent = st.session_state.agent

            status.update(label="Searching official sites and study portals…")
            raw = agent.search_agent.find_resources(exam_name)

            status.update(label="Reading and extracting syllabus documents…")
            s_urls = [
                (r.url if hasattr(r, "url") else r.get("url", ""))
                for r in raw.get("syllabus", [])[:12]
            ]
            pages, pdfs = agent.scraping_agent.scrape_sources(s_urls, max_pages=10)

            status.update(label="Building structured syllabus…")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(
                exam_name, pages, s_urls, raw.get("exam_pattern", [])
            )

            status.update(label="Creating your personalised preparation plan…")
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

            st.session_state.updated_at = datetime.datetime.now().strftime("%d %b, %I:%M %p")
            status.update(label="Done! Your strategy is ready.", state="complete", expanded=False)
            return final

        except Exception as e:
            status.update(label="Something went wrong.", state="error", expanded=True)
            st.error(f"Error: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# 5. PERSISTENT SEARCH BAR (always visible)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-brand">🎯 <span>ExamGenie</span> AI</div>', unsafe_allow_html=True)
st.markdown('<div class="page-tagline">Your complete exam preparation companion — syllabus, strategy, papers &amp; videos in one place.</div>', unsafe_allow_html=True)

s1, s2 = st.columns([5, 1])
with s1:
    exam_q = st.text_input(
        "exam_search",
        value=st.session_state.last_exam,
        placeholder="Search any exam: JEE, UPSC, GATE, TCS NQT, CAT…",
        label_visibility="collapsed",
    )
with s2:
    go = st.button("Search  🔍", use_container_width=True)

if go and exam_q.strip():
    result = run_pipeline(exam_q.strip())
    if result:
        st.session_state.results = result
        st.session_state.last_exam = exam_q.strip()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# 6. SIDEBAR NAV
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand-logo">🎯 ExamGenie AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Exam Preparation Platform</div>', unsafe_allow_html=True)

    curr = st.session_state.last_exam or "—"
    st.markdown(f'<div class="board-title">📌 {curr}</div>', unsafe_allow_html=True)
    if st.session_state.updated_at:
        st.markdown(f'<div class="board-time">Updated: {st.session_state.updated_at}</div>', unsafe_allow_html=True)

    st.markdown("---")
    nav = st.radio(
        "Navigate",
        options=[
            "📋 Exam Overview",
            "📚 Syllabus",
            "🗓️ Study Plan",
            "📄 Question Papers",
            "🔗 Study Material",
            "▶️ Video Lectures",
        ],
        index=0,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 7. EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.results:
    st.markdown("""
    <div style="text-align:center; padding:5rem 2rem; opacity:0.55;">
        <div style="font-size:3.5rem; margin-bottom:1rem;">🎯</div>
        <h3 style="font-family:'Outfit',sans-serif; font-weight:700;">Ready when you are.</h3>
        <p style="font-size:0.9rem;">Type the name of any competitive exam above and hit Search.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# 8. CONTENT PAGES
# ─────────────────────────────────────────────────────────────────────────────
data      = st.session_state.results
exam_name = st.session_state.last_exam

# ── EXAM OVERVIEW ─────────────────────────────────────────────────────────────
if nav == "📋 Exam Overview":
    st.markdown(f'<div class="sec-head">{exam_name} — Exam Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Key facts, dates, and important topics at a glance.</div>', unsafe_allow_html=True)

    info = data.get("about_exam") or {}
    desc = info.get("description", "").strip()

    if desc:
        st.markdown(f"""
        <div class="info-box">
            <div class="info-label">About the Exam</div>
            <div class="info-value">{desc}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Exam overview not found. Please visit the official website for details.")

    deadline = info.get("deadline", "Check Official Site")
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">📅 Application / Registration Deadline</div>
        <div class="info-value" style="font-size:1.15rem; font-weight:700; color:var(--accent);">{deadline}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    topics = data.get("important_topics") or []
    if topics:
        st.markdown('<div class="sec-head" style="font-size:1.1rem;">High-Weightage Topics</div>', unsafe_allow_html=True)
        chips = "".join([f'<span class="chip">🔥 {t}</span>' for t in topics[:15]])
        st.markdown(f'<div class="tag-bar">{chips}</div>', unsafe_allow_html=True)


# ── SYLLABUS ──────────────────────────────────────────────────────────────────
elif nav == "📚 Syllabus":
    syl = data.get("syllabus") or []
    done = sum(1 for k, v in st.session_state.items() if k.startswith(f"syl_{exam_name}_") and v)
    pct  = int(done / max(len(syl), 1) * 100)

    st.markdown(f'<div class="sec-head">Official Syllabus — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Sourced from official portals and leading study sites. Mark topics as you complete them.</div>', unsafe_allow_html=True)

    # Progress
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--muted); margin-bottom:5px;">
        <span>Progress</span><span style="color:var(--accent); font-weight:700;">{pct}%</span>
    </div>
    <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%;"></div></div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if syl:
        for item in syl:
            key   = f"syl_{exam_name}_{item.get('topic', item)}"
            topic = item.get("topic") if isinstance(item, dict) else str(item)
            subs  = item.get("subtopics", []) if isinstance(item, dict) else []
            done_ = st.checkbox(topic, value=st.session_state.get(key, False), key=key)
            if subs:
                sub_txt = " &nbsp;·&nbsp; ".join(subs[:12])
                st.markdown(f'<div style="margin:-8px 0 10px 28px; color:var(--muted); font-size:0.82rem;">{sub_txt}</div>', unsafe_allow_html=True)
    else:
        st.warning("Syllabus not found for this exam. Try searching again or check the official site.")


# ── STUDY PLAN ────────────────────────────────────────────────────────────────
elif nav == "🗓️ Study Plan":
    st.markdown(f'<div class="sec-head">4-Week Preparation Strategy — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Personalised day-wise plan built around your actual syllabus topics.</div>', unsafe_allow_html=True)

    plan = data.get("study_plan") or []
    if plan:
        for wk in plan:
            label = f"Week {wk.get('week')}  —  {wk.get('focus', '')}"
            with st.expander(label, expanded=True):
                tasks = wk.get("tasks") or []
                for t in tasks:
                    st.markdown(f"&nbsp;&nbsp;◈ &nbsp;{t}", unsafe_allow_html=True)
                if wk.get("tip"):
                    st.markdown(
                        f"<div style='margin-top:10px; padding:10px 14px; background:rgba(200,255,0,0.06); "
                        f"border-left:3px solid var(--accent); border-radius:8px; font-size:0.85rem;'>"
                        f"💡 <b>Tip:</b> {wk['tip']}</div>",
                        unsafe_allow_html=True
                    )
    else:
        st.info("Study plan not generated. Try regenerating the search.")


# ── QUESTION PAPERS ───────────────────────────────────────────────────────────
elif nav == "📄 Question Papers":
    st.markdown(f'<div class="sec-head">Previous Year Question Papers — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Download official question papers and practice with real exam questions.</div>', unsafe_allow_html=True)

    papers = data.get("previous_papers") or []
    if papers:
        for p in papers:
            url   = p.get("url", "#")
            title = p.get("title", "Question Paper")
            ptype = p.get("type", "link")
            badge = "📄 PDF" if ptype == "pdf" else "🔗 Link"
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{title}**")
                    st.caption(badge)
                with c2:
                    st.link_button("Open →", url, use_container_width=True)
    else:
        st.info("No question papers found. Please search on the official exam website.")


# ── STUDY MATERIAL ────────────────────────────────────────────────────────────
elif nav == "🔗 Study Material":
    st.markdown(f'<div class="sec-head">Recommended Study Material — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Books, notes, and free online courses to help you prepare.</div>', unsafe_allow_html=True)

    resources = data.get("resources") or []
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


# ── VIDEO LECTURES ────────────────────────────────────────────────────────────
elif nav == "▶️ Video Lectures":
    st.markdown(f'<div class="sec-head">Video Lectures — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Curated video playlists and lectures for visual learners.</div>', unsafe_allow_html=True)

    vids = data.get("youtube_lectures") or []
    if vids:
        cols = st.columns(2)
        for i, v in enumerate(vids[:10]):
            url   = v.get("url", "")
            title = v.get("title", "Lecture")
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    if "youtube.com" in url or "youtu.be" in url:
                        try:
                            st.video(url)
                        except Exception:
                            pass
                    st.link_button("▶️ Watch on YouTube", url, use_container_width=True)
    else:
        st.info("No video lectures found for this exam.")


st.markdown("<br><br><br>", unsafe_allow_html=True)
