"""
ExamGenie AI — Elite SaaS intelligence Platform
Features: Persistent Search, Exam Details, Deep Syllabus, Integrated Chatbot.
"""

import streamlit as st
import datetime
import json
from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger
logger = get_logger(__name__)

# ── 1. Page Config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExamGenie AI | Intelligent Strategies",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Professional SaaS Design System ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

:root {
    --bg-base: #030407;
    --bg-card: #0D1117;
    --primary: #C6FF00;
    --primary-dim: rgba(198, 255, 0, 0.1);
    --border: rgba(255, 255, 255, 0.06);
    --text-high: #F8FAFC;
    --text-low: #94A3B8;
}

.stApp { background: var(--bg-base); color: var(--text-high); font-family: 'Plus Jakarta Sans', sans-serif; }
footer, #MainMenu { visibility: hidden; }
header { background: transparent !important; }

/* Header Branding */
.app-brand {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--primary);
    font-family: 'Outfit', sans-serif;
    text-align: center;
    margin-bottom: 1.5rem;
}

/* Persistent Search Bar Style */
.stTextInput > div > div > input {
    background-color: #0D1117 !important;
    border: 1px solid var(--border) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 12px 20px !important;
}

[data-testid="stSidebar"] {
    background-color: #06080C !important;
    border-right: 1px solid var(--border) !important;
}

.sidebar-hud-head { font-size: 1rem; font-weight: 700; color: #FFF; margin-bottom: 2px; }
.sidebar-hud-sub { font-size: 0.7rem; color: var(--text-low); margin-bottom: 2rem; }

/* Timeline UI */
.timeline-card { border-left: 2px solid var(--primary); padding-left: 1.25rem; margin-bottom: 1.5rem; position: relative; }
.timeline-card::before { content: ''; position: absolute; left: -7px; top: 0; width: 12px; height: 12px; background: var(--primary); border-radius: 50%; }

/* Navigation Radio Styling */
div[data-testid="stSidebar"] div.stRadio > label { display: none; }
</style>
""", unsafe_allow_html=True)

# ── 3. Session State ──────────────────────────────────────────────────────────
if "agent" not in st.session_state: st.session_state.agent = ResearchAgent()
if "results" not in st.session_state: st.session_state.results = None
if "last_exam" not in st.session_state: st.session_state.last_exam = ""
if "updated_at" not in st.session_state: st.session_state.updated_at = "Ready"
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# ── 4. Research Intelligence Pipeline ──────────────────────────────────────────
def run_intelligence_pipeline(exam_name: str):
    with st.status(f"🔮 Excavating {exam_name} Intelligence...", expanded=True) as status:
        try:
            agent = st.session_state.agent
            status.update(label="📡 Scanning official sites & GFG archives...", state="running")
            raw = agent.search_agent.find_resources(exam_name)
            
            status.update(label="📖 Scraping authoritative syllabus documents...", state="running")
            s_urls = [(r.url if hasattr(r, "url") else r.get("url","")) for r in raw.get("syllabus", [])[:12]]
            pages, pdfs = agent.scraping_agent.scrape_sources(s_urls, max_pages=10)
            
            status.update(label="🧠 Structuring deep syllabus hierarchy...", state="running")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(exam_name, pages, s_urls, raw.get("exam_pattern",[]))
            
            status.update(label="📅 Synthesizing strategy based on exact syllabus...", state="running")
            plan = agent.study_agent.build_plan(exam_name, syllabus, topics, weeks=4)
            
            status.update(label="📦 Packaging Intelligence Dashboard...", state="running")
            final = agent.response_agent.format_final_response(
                exam_name, raw.get("exam_info", []), raw["syllabus"], raw["previous_papers"],
                raw["study_resources"], raw["youtube_lectures"], syllabus, topics, plan, pdfs, chunks
            )
            
            st.session_state.updated_at = datetime.datetime.now().strftime("%I:%M %p")
            return final
        except Exception as e:
            st.error(f"Intelligence failure: {e}")
            return None

# ── 5. PERSISTENT TOP SEARCH BAR ──────────────────────────────────────────────
st.markdown('<div class="app-brand">⚡ ExamGenie AI</div>', unsafe_allow_html=True)

search_col_1, search_col_2 = st.columns([5, 1])
with search_col_1:
    exam_q = st.text_input(
        "Exam Search", 
        value=st.session_state.last_exam, 
        placeholder="Enter search: UPSC, GATE, CAT, TCS NQT...", 
        label_visibility="collapsed"
    )
with search_col_2:
    trigger = st.button("Generate ✨", use_container_width=True)

if trigger and exam_q:
    new_res = run_intelligence_pipeline(exam_q.strip())
    if new_res:
        st.session_state.results = new_res
        st.session_state.last_exam = exam_q.strip()
        st.rerun()

# ── 6. Sidebar HUD ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:1.4rem; font-weight:800; color:var(--primary); margin-bottom:1rem;">⚡ Workspace</div>', unsafe_allow_html=True)
    curr_exam = st.session_state.last_exam or "Empty Board"
    st.markdown(f'<div class="sidebar-hud-head">Board: {curr_exam}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-hud-sub">Refined {st.session_state.updated_at}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    nav = st.radio(
        "Nav",
        ["📖 Exam Details", "📂 Study Board", "📋 Syllabus", "📖 Study Vault", "🎬 Video Lab", "🤖 Exam Chat"],
        index=0 if st.session_state.results else 0
    )

# ── 7. Main Dashboard Content ─────────────────────────────────────────────────
if not st.session_state.results:
    st.markdown("""
    <div style="text-align:center; padding-top:4rem;">
        <h3 style="color:var(--text-low);">Enter your examination above to start the deep research.</h3>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Data shortcuts
data = st.session_state.results
exam_name = st.session_state.last_exam

if nav == "📖 Exam Details":
    st.markdown(f"### 📋 {exam_name} Detail Brief")
    info = data.get("about_exam") or {}
    st.info(info.get("description", "No detailed overview found. Please check official site for English notification."))
    
    st.markdown(f"""
    <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #222; margin-top:2rem;">
        <h4 style="color:var(--primary); margin-bottom:5px;">📅 Key Deadlines & Notifications</h4>
        <p style="font-size:1.1rem; font-weight:700;">{info.get('deadline', 'Check Official Site')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Important Focus Topics")
    topics = data.get("important_topics") or []
    if topics:
        cols = st.columns(3)
        for i, t in enumerate(topics[:12]):
            cols[i%3].markdown(f"🔥 **{t}**")

elif nav == "📂 Study Board":
    st.markdown(f"### 🎯 Tailored 4-Week Strategy — {exam_name}")
    st.caption("Content strictly aligned with the extracted syllabus topics.")
    plan = data.get("study_plan") or []
    for wk in plan:
        with st.expander(f"PHASE {wk.get('week')} — {wk.get('focus')}", expanded=True):
            tasks = wk.get("tasks") or []
            for t in tasks: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;◈ {t}", unsafe_allow_html=True)
            if wk.get("tip"): st.markdown(f"<br>&nbsp;&nbsp;&nbsp;&nbsp;💡 *Tactical Tip: {wk.get('tip')}*", unsafe_allow_html=True)

elif nav == "📋 Syllabus":
    st.markdown(f"### 📋 Academic Syllabus Hierarchy")
    st.caption("Extracted from GFG and Official Documentation.")
    syllabus = data.get("syllabus") or []
    if syllabus:
        for item in syllabus:
            with st.container(border=True):
                st.markdown(f"#### {item.get('topic')}")
                subs = item.get("subtopics") or []
                for s in subs: st.markdown(f"• {s}")
    else: st.warning("No syllabus data found. Attempting recursive search...")

elif nav == "📖 Study Vault":
    st.markdown(f"### 📖 Integrated Preparation Materials")
    papers = data.get("previous_papers") or []
    res = data.get("resources") or []
    
    with st.container(border=True):
        st.markdown("**Previous Year Question (PYQ) Archives**")
        for p in papers[:10]:
            c1, c2 = st.columns([4, 1])
            with c1: st.write(p.get("title"))
            with c2: st.link_button("View", p.get("url", "#"), use_container_width=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**Additional Learning Resources**")
        for r in res[:10]:
            c1, c2 = st.columns([4, 1])
            with c1: st.write(r.get("title"))
            with c2: st.link_button("Access", r.get("url", "#"), use_container_width=True)

elif nav == "🎬 Video Lab":
    st.markdown("### 🎬 Curated Video Lectures")
    vids = data.get("youtube_lectures") or []
    vcols = st.columns(2)
    for i, v in enumerate(vids[:8]):
        with vcols[i%2]:
            with st.container(border=True):
                st.write(f"**{v.get('title')}**")
                url = v.get('url', '')
                if "youtube" in url: st.video(url)
                st.link_button("▶️ Watch", url, use_container_width=True)

elif nav == "🤖 Exam Chat":
    st.markdown(f"### 🤖 {exam_name} AI Expert Bot")
    st.caption("Powered by AI — Ask about syllabus, dates, strategy, or anything about this exam.")
    
    # Initialize per-exam chat history
    chat_key = f"chat_{exam_name}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": f"👋 Hi! I'm your **{exam_name}** expert. Ask me anything — syllabus topics, important dates, preparation strategy, or exam pattern."}
        ]
    
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]): st.write(msg["content"])
        
    chat_input = st.chat_input(f"Ask about {exam_name}...")
    if chat_input:
        st.session_state[chat_key].append({"role": "user", "content": chat_input})
        with st.chat_message("user"): st.write(chat_input)
        
        agent = st.session_state.agent
        
        # Build rich context from already-fetched exam data (RAG from session)
        syllabus_str = "\n".join([f"- {s.get('topic')}: {', '.join(s.get('subtopics', []))}" for s in (data.get('syllabus') or [])])
        topics_str = ", ".join(data.get('important_topics') or [])
        about_str = (data.get('about_exam') or {}).get('description', '')
        deadline_str = (data.get('about_exam') or {}).get('deadline', '')
        plan_str = ""
        for w in (data.get('study_plan') or []):
            plan_str += f"Week {w.get('week')}: {w.get('focus')}\n"
            for t in (w.get('tasks') or []): plan_str += f"  - {t}\n"
        
        # Also try FAISS vector search for extra context
        vs_context = ""
        try:
            vs_results = agent.response_agent.vector_store.similarity_search(
                chat_input, k=3, filter_dict={"exam_name": exam_name}
            )
            vs_context = "\n".join([r.get("content", "") for r in vs_results])
        except Exception as e:
            logger.warning(f"Vector search: {e}")
        
        full_context = f"""
Exam: {exam_name}
About: {about_str}
Deadline: {deadline_str}
Key Topics: {topics_str}
Syllabus:\n{syllabus_str}
Study Plan:\n{plan_str}
Additional Research:\n{vs_context}
"""
        prompt = f"""You are an expert on {exam_name}. Use ONLY the information below to answer the user question accurately. Be concise, professional, and specific.

EXAM DATA:
{full_context}

USER QUESTION: {chat_input}

ANSWER:"""
        
        try:
            llm = agent.response_agent.llm
            if llm is None:
                raise ValueError("LLM not initialized")
            ans = llm.invoke(prompt).content
        except Exception as e:
            ans = f"⚠️ Chatbot unavailable: {e}. Please verify GROQ_API_KEY in secrets."
        
        st.session_state[chat_key].append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.write(ans)

st.markdown("<br><br><br>", unsafe_allow_html=True)
