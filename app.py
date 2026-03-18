"""
ExamGenie AI — Premium SaaS Platform (Revised v3)
Refined for tcs nqt style deep research and sidebar dashboard.
"""

import streamlit as st
import datetime
from exam_ai_agent.agents.research_agent import ResearchAgent

# ── 1. Page Config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI | Professional Strategy Display",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Comprehensive SaaS Style System ────────────────────────────────────────
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
header, footer, #MainMenu { visibility: hidden; position: absolute; }
.stDeployButton { display: none; }

[data-testid="stSidebar"] {
    background-color: #06080C !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 1rem !important;
}

/* Sidebar Headings */
.sidebar-board-head {
    font-size: 1.1rem;
    font-weight: 700;
    color: #FFF;
    margin-bottom: 2px;
}
.sidebar-board-sub {
    font-size: 0.75rem;
    color: var(--text-low);
    margin-bottom: 2rem;
}

/* Typography */
h1, h2, h3 { font-family: 'Outfit', sans-serif !important; letter-spacing: -0.02em; }

/* Dashboard Cards */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
}

/* Custom Progress Bar */
.prog-bar-bg { width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; margin: 10px 0; }
.prog-bar-fill { height: 100%; background: var(--primary); transition: width 1s ease; }

/* Timeline UI */
.timeline-card { border-left: 2px solid var(--primary); padding-left: 1.25rem; margin-bottom: 1.5rem; position: relative; }
.timeline-card::before { content: ''; position: absolute; left: -7px; top: 0; width: 12px; height: 12px; background: var(--primary); border-radius: 50%; }

/* Navigation Radio Styling hack */
div[data-testid="stSidebar"] div.stRadio > label { display: none; }
div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)

# ── 3. Session State ──────────────────────────────────────────────────────────
if "agent" not in st.session_state: st.session_state.agent = ResearchAgent()
if "results" not in st.session_state: st.session_state.results = None
if "last_exam" not in st.session_state: st.session_state.last_exam = ""
if "progress" not in st.session_state: st.session_state.progress = {}
if "updated_at" not in st.session_state: st.session_state.updated_at = "Long ago"

# ── 4. Research Logic ─────────────────────────────────────────────────────────
def run_deep_research(exam_name: str, force: bool):
    with st.status("🔮 Orchestrating deep intelligence search...", expanded=True) as status:
        try:
            agent = st.session_state.agent
            
            # Step 1: Deep Search for Syllabus
            status.update(label=f"📡 Deep scanning for {exam_name} syllabus hierarchy...", state="running")
            raw = agent.search_agent.find_resources(exam_name)
            
            # Step 2: Extraction
            status.update(label="📖 Scrutinizing authoritative exam modules...", state="running")
            sy_urls = [(r.url if hasattr(r, "url") else r.get("url","")) for r in raw.get("syllabus", [])[:10]]
            pages, pdfs = agent.scraping_agent.scrape_sources(sy_urls, max_pages=8)
            
            # Step 3: Formal Syllabus Development
            status.update(label="🧠 Building official syllabus structure...", state="running")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(exam_name, pages, sy_urls, raw.get("exam_pattern",[]))
            
            # Step 4: Recursive Study Plan (Week & Day granularity)
            status.update(label="📅 Synthesizing day-wise 4-week timetable...", state="running")
            # We explicitly task the study plan agent with day-wise granularity now
            plan = agent.study_agent.build_plan(exam_name, syllabus, topics, weeks=4)
            
            # Step 5: Final Response assembly
            status.update(label="📦 Packaging intelligence dashboard...", state="running")
            final = agent.response_agent.format_final_response(
                exam_name, raw["syllabus"], raw["previous_papers"], raw["study_resources"],
                raw["youtube_lectures"], syllabus, topics, plan, pdfs, chunks
            )
            
            st.session_state.updated_at = datetime.datetime.now().strftime("%I:%M %p")
            return final
        except Exception as e:
            st.error(f"Intelligence failure: {e}")
            return None

# ── 5. Sidebar Dashboard Components ────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:1.5rem; font-weight:800; color:var(--primary); margin-bottom:1rem;">⚡ ExamGenie</div>', unsafe_allow_html=True)
    
    current_board = st.session_state.last_exam or "tcs nqt"
    st.markdown(f'<div class="sidebar-board-head">Board: {current_board}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-board-sub">Strategy updated {st.session_state.updated_at}</div>', unsafe_allow_html=True)
    
    nav = st.radio(
        "Navigation",
        ["📂 Study Board", "📋 Syllabus", "📄 PYQ Archive", "📚 Resources", "🎬 Video Lab"],
        index=1 if st.session_state.results else 0
    )

# ── 6. Main Interaction UI ────────────────────────────────────────────────────
if not st.session_state.results:
    st.markdown(f'<h1 style="font-size:3.5rem; padding-top:2rem;">Intelligence for {current_board}</h1>', unsafe_allow_html=True)
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        exam_query = st.text_input("Examination Query", value=current_board, placeholder="Enter exam name...", label_visibility="collapsed")
    with col_btn:
        generate = st.button("Generate Strategy 🚀", use_container_width=True)
    
    if generate and exam_query:
        res = run_deep_research(exam_query.strip(), True)
        if res:
            st.session_state.results = res
            st.session_state.last_exam = exam_query.strip()
            st.rerun()
    st.stop()

# ── 7. Display Result Dashboard Based on Nav ───────────────────────────────────
data = st.session_state.results
exam_name = st.session_state.last_exam

if nav == "📂 Study Board":
    st.markdown("### 📅 Personalized Study Plan (4-Week Tree View)")
    st.caption("A day-by-day rigorous strategy derived from your syllabus.")
    
    plan_data = data.get("study_plan") or []
    if plan_data:
        for wk in plan_data:
            with st.expander(f"WEEK {wk.get('week')} — {wk.get('focus')}", expanded=True):
                tasks = wk.get("tasks") or []
                for t in tasks:
                    st.markdown(f"**{t}**")
                if wk.get("tip"):
                    st.info(f"💡 Strategy: {wk.get('tip')}")
    else: st.write("Building schedule...")

elif nav == "📋 Syllabus":
    st.markdown("### 📋 Formatted Syllabus & Focus Areas")
    
    # Progress HUD
    syllabus_items = data.get("syllabus") or []
    total_t = len(syllabus_items)
    done_t = sum(1 for k, v in st.session_state.progress.items() if k.startswith(f"prog_{exam_name}_") and v)
    pct = int((done_t / total_t * 100)) if total_t > 0 else 0
    
    st.markdown(f"""
    <div style="background:#111; padding:15px; border-radius:12px; margin-bottom:2rem;">
        <span style="color:var(--text-low); font-size:0.8rem;">SYLLABUS MASTERY: {pct}%</span>
        <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Topics
    topics = data.get("important_topics") or []
    if topics:
        st.markdown("**HIGH-YIELD CORE CONTENT**")
        c = st.columns(3)
        for i, t in enumerate(topics[:12]):
            c[i%3].markdown(f"🔥 **{t}**")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if syllabus_items:
        for idx, item in enumerate(syllabus_items):
            title = item.get("topic")
            key = f"prog_{exam_name}_{title}"
            col_b, col_t = st.columns([1, 15])
            with col_b: st.checkbox("✔", value=st.session_state.progress.get(key, False), key=key, label_visibility="hidden")
            with col_t:
                with st.expander(f"**{title}**"):
                    st.write(item.get("description"))
                    if item.get("subtopics"):
                        for s in item["subtopics"]: st.markdown(f"• {s}")

elif nav == "📄 PYQ Archive":
    st.markdown("### 📄 Previous Question Papers")
    papers = data.get("previous_papers") or []
    for p in papers[:10]:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1: st.markdown(f"**{p.get('title')}**")
            with c2: st.link_button("Open", p.get("url", "#"), use_container_width=True)

elif nav == "📚 Resources":
    st.markdown("### 📚 Curated Deep Study Material")
    res = data.get("resources") or []
    for r in res[:12]:
        with st.container(border=True):
            st.markdown(f"#### {r.get('title')}")
            st.write(r.get("description"))
            st.link_button("Access Material", r.get("url", "#"))

elif nav == "🎬 Video Lab":
    st.markdown("### 🎬 Visual Learning Labs")
    vids = data.get("youtube_lectures") or []
    v_cols = st.columns(2)
    for i, v in enumerate(vids[:10]):
        with v_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{v.get('title')}**")
                v_url = v.get('url', '')
                if "youtube.com" in v_url or "youtu.be" in v_url: st.video(v_url)
                st.link_button("▶️ Watch on YouTube", v_url, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
