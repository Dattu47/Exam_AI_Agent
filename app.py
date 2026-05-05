"""
ExamGenie AI — Refactored for Resource Aggregation
Tabs: Authority | Archive | Video Library | Library
"""
import streamlit as st
import datetime
from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)
CURRENT_YEAR = datetime.datetime.now().year

st.set_page_config(
    page_title="ExamGenie Resource Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (Scientific, Educational, Clean) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
:root{
  --bg:#030508;--surface:#0A0F1A;--card:#101626;--card2:#151C30;
  --border:rgba(91,150,247,0.15);--accent:#00FFA3;--accent2:#5B96F7;
  --text:#F0F4F8;--muted:#8B9BB4;
  --radius:16px;
}
html,body,.stApp{background:var(--bg)!important;color:var(--text);font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid rgba(91,150,247,0.12)!important;}
.brand{font-family:'Outfit',sans-serif;font-size:2rem;font-weight:900;
  background:linear-gradient(135deg,#00FFA3 0%,#00E5FF 40%,#5B96F7 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:20px;letter-spacing:-0.5px;}
.app-title{font-family:'Outfit',sans-serif;font-size:3.5rem;font-weight:900;text-align:center;color:var(--text); letter-spacing:-2px; text-shadow:0 0 40px rgba(0,255,163,0.15);}
.g1{background:linear-gradient(135deg,#00FFA3,#00E5FF);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.app-sub{text-align:center;color:var(--muted);font-size:1.15rem;margin-bottom:2.5rem; letter-spacing:0.5px;}
div.stButton>button{
  background:linear-gradient(135deg,#00FFA3 0%,#00E5FF 100%)!important;
  color:#000!important;font-weight:800!important;
  border-radius:12px!important;height:52px!important;transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
  border:none!important; font-size:1.05rem!important; box-shadow:0 4px 15px rgba(0,255,163,0.3)!important;
}
div.stButton>button:hover{transform:translateY(-2px) scale(1.02)!important; box-shadow:0 10px 40px rgba(0,255,163,0.5)!important;}
.stTextInput>div>div>input{
  background:var(--surface)!important;border:1.5px solid rgba(0,255,163,0.15)!important;
  border-radius:12px!important;color:var(--text)!important;padding:14px 22px!important; font-size:1.1rem!important;
  transition:all 0.3s ease!important;
}
.stTextInput>div>div>input:focus{border-color:var(--accent)!important; box-shadow:0 0 20px rgba(0,255,163,0.25)!important;}
.stExpander{border:1px solid var(--border)!important;border-radius:var(--radius)!important;background:var(--card)!important;}
.stLinkButton a{
  background:var(--surface)!important;border:1px solid rgba(91,150,247,0.3)!important;
  border-radius:10px!important;color:var(--accent2)!important;
  font-size:0.9rem!important;font-weight:700!important;transition:all 0.2s!important;
}
.stLinkButton a:hover{background:rgba(91,150,247,0.1)!important; border-color:var(--accent2)!important; transform:translateY(-2px)!important;}

/* Custom Card Container */
.custom-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.custom-card::before {
    content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
    background: linear-gradient(180deg, var(--accent) 0%, var(--accent2) 100%);
    opacity: 0; transition: opacity 0.3s ease;
}
.custom-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    border-color: rgba(0,255,163,0.2);
}
.custom-card:hover::before { opacity: 1; }
.card-title {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 12px;
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.3px;
}
.card-desc {
    font-size: 0.95rem;
    color: var(--muted);
    line-height: 1.6;
    margin-bottom: 16px;
}
.badge {
    background: rgba(91,150,247,0.1);
    color: var(--accent2);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    display: inline-block;
    margin-bottom: 12px;
    border: 1px solid rgba(91,150,247,0.25);
    letter-spacing: 0.5px;
}
.badge-pdf {
    background: rgba(0,255,163,0.1);
    color: var(--accent);
    border: 1px solid rgba(0,255,163,0.2);
}
.badge-update {
    background: rgba(255,65,105,0.1);
    color: #FF4169;
    border: 1px solid rgba(255,65,105,0.3);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255,65,105, 0.4); }
    70% { box-shadow: 0 0 0 6px rgba(255,65,105, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255,65,105, 0); }
}
.info-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.info-label { color: var(--muted); font-size: 0.9rem; font-weight: 600; }
.info-val { color: var(--text); font-size: 0.95rem; font-weight: 700; text-align: right; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──
for k, v in [("agent", None), ("results", None), ("last_exam", ""), ("updated_at", "")]:
    if k not in st.session_state:
        st.session_state[k] = v
if st.session_state.agent is None:
    st.session_state.agent = ResearchAgent()

def run_pipeline(exam_name: str):
    with st.status(f"Aggregating resources for **{exam_name}**...", expanded=True) as status:
        try:
            status.update(label="🔍 Scanning for official authority URLs, PDFs, and resources...")
            final = st.session_state.agent.research_exam(exam_name)
            st.session_state.updated_at = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            status.update(label="✅ Resources compiled!", state="complete", expanded=False)
            return final
        except Exception as e:
            status.update(label="Failed to aggregate.", state="error", expanded=True)
            st.error(str(e))
            return None

st.markdown(f"""
<div style="text-align:center;padding:1rem 0;">
  <div class="app-title">🎯 <span class="g1">ExamGenie</span> Hub</div>
  <div class="app-sub">Scientific Resource Aggregation & Authority Discovery • {CURRENT_YEAR}</div>
</div>
""", unsafe_allow_html=True)

sc1, sc2 = st.columns([5, 1])
with sc1:
    exam_q = st.text_input("exam_search", value=st.session_state.last_exam, placeholder="Enter Exam Name (e.g., GATE CSE, UPSC Prelims)...", label_visibility="collapsed")
with sc2:
    go = st.button("Search 🔍", use_container_width=True)

if go and exam_q.strip():
    result = run_pipeline(exam_q.strip())
    if result:
        st.session_state.results = result
        st.session_state.last_exam = exam_q.strip()
        st.rerun()

with st.sidebar:
    st.markdown('<div class="brand">🎓 ExamGenie</div>', unsafe_allow_html=True)
    curr = st.session_state.last_exam or "No exam selected"
    st.info(f"📌 {curr}")
    if st.session_state.updated_at:
        st.caption(f"Updated: {st.session_state.updated_at}")
    if st.button("🔄 Clear Search"):
        st.session_state.results = None
        st.session_state.last_exam = ""
        st.rerun()

if not st.session_state.results:
    st.info("Enter an exam name above to aggregate official websites, PYQs, video libraries, and study materials.")
    st.stop()

data = st.session_state.results or {}
authority = data.get("authority", {})
archive = data.get("archive", [])
videos = data.get("videos", [])
library = data.get("library", {})

tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Authority", "📄 Archive (PYQs)", "🎥 Video Library", "📚 Library"])

with tab1:
    st.markdown("### 🏛️ Official Fact-Checker")
    st.caption("AI-verified authority portal and official scheduling details.")
    
    details = authority.get("details", {})
    has_update = details.get("has_new_update", False)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        off_site = authority.get("official_site")
        if off_site:
            title = off_site.get('title', 'Official Website')
            url = off_site.get('url', '#')
            is_gov = off_site.get('is_gov_domain', False)
            gov_badge = '<span style="color:#00FFA3; margin-left:8px;" title="Verified Government Domain">✅ Verified .gov / .nic</span>' if is_gov else ''
            
            st.markdown(f"""
<div class="custom-card">
    <div class="badge">🌐 OFFICIAL PORTAL</div>
    <div class="card-title">{title} {gov_badge}</div>
    <div class="card-desc">This is the verified primary source for the exam. Avoid relying on third-party blogs for application details.</div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Go to Official Website ↗", url, use_container_width=True)
        else:
            search_fallback = f"https://www.google.com/search?q={exam_q.strip().replace(' ', '+')}+official+website"
            st.warning("Could not identify the official website with high confidence.")
            st.link_button("Search Google for Official Site 🔍", search_fallback, use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        syl_pdf = authority.get("syllabus_pdf")
        if syl_pdf:
            title = syl_pdf.get('title', 'Official Syllabus PDF')
            url = syl_pdf.get('url', '#')
            st.markdown(f"""
<div class="custom-card">
    <div class="badge badge-pdf">📄 DEEP LINK</div>
    <div class="card-title">{title}</div>
    <div class="card-desc">Direct download link hosted on the official server. Bypasses ads and blog spam.</div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Download Official Syllabus 📥", url, use_container_width=True)
            
    with c2:
        # Status ticker — native Streamlit to avoid HTML rendering issues
        if has_update:
            st.markdown('<div class="badge badge-update">🚨 NEW UPDATE FOUND!</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge" style="width:100%;text-align:center;box-sizing:border-box;">ℹ️ NO NEW NOTIFICATIONS</div>', unsafe_allow_html=True)

        st.markdown("""
<div class="custom-card" style="padding:20px;">
<div class="card-title" style="font-size:1.1rem; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:10px; margin-bottom:10px;">Quick Info Card</div>
</div>
""", unsafe_allow_html=True)

        conducting = details.get('conducting_body', 'Not Available')
        frequency  = details.get('frequency', 'Not Available')
        reg_dates  = details.get('registration_dates', 'Not Available')
        about      = details.get('about_exam', '')

        st.markdown(f"""
<div class="custom-card" style="padding:18px; margin-top:-10px;">
    <div class="info-row">
        <span class="info-label">Conducting Body</span>
        <span class="info-val">{conducting}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Frequency</span>
        <span class="info-val">{frequency}</span>
    </div>
    <div class="info-row" style="border-bottom:none;">
        <span class="info-label">Reg. Dates</span>
        <span class="info-val" style="color:var(--accent);">{reg_dates}</span>
    </div>
</div>
""", unsafe_allow_html=True)

        if about and about != 'Not Available':
            st.markdown(f"""
<div class="custom-card" style="padding:18px;">
    <div class="badge" style="margin-bottom:10px;">📌 ABOUT THIS EXAM</div>
    <div class="card-desc" style="margin:0; line-height:1.7;">{about}</div>
</div>
""", unsafe_allow_html=True)

with tab2:
    st.markdown("### 📄 Archive (PYQs)")
    st.caption("Previous Year Question papers and mock tests.")
    if archive:
        for p in archive:
            title = p.get('title', 'PYQ Paper')
            snippet = p.get('snippet', '')
            url = p.get('url', '#')
            is_pdf = url.lower().endswith(".pdf")
            badge_class = "badge-pdf" if is_pdf else "badge"
            badge_text = "📄 PDF" if is_pdf else "🔗 WEB"
            
            st.markdown(f"""
<div class="custom-card">
    <div class="badge {badge_class}">{badge_text}</div>
    <div class="card-title">{title}</div>
    <div class="card-desc">{snippet}</div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Open Paper ↗", url)
    else:
        st.info("No PYQ archives found. It's possible the search didn't yield highly relevant results.")

with tab3:
    st.markdown("### 🎥 Video Library")
    st.caption("Curated top playlists grouped by topic or difficulty.")
    if videos:
        cols = st.columns(2)
        for i, v in enumerate(videos):
            title = v.get('title', 'Video Playlist')
            cat = v.get('category', 'General')
            desc = v.get('description', '')
            url = v.get('url', '#')
            with cols[i % 2]:
                st.markdown(f"""
<div class="custom-card">
    <div class="badge">▶️ {cat.upper()}</div>
    <div class="card-title">{title}</div>
    <div class="card-desc">{desc}</div>
</div>
""", unsafe_allow_html=True)
                st.link_button("Watch Playlist ▶️", url)
    else:
        st.info("No video playlists found.")

with tab4:
    st.markdown("### 📚 Library & Verified Portals")
    st.caption("Structured data from top educational platforms and government sources.")
    
    st.markdown("#### Educational Platforms & Prep Websites")
    edtech_links = library.get("edtech_links", [])
    if edtech_links:
        for d in edtech_links:
            title = d.get('title', 'Platform Link')
            url = d.get('url', '#')
            st.markdown(f"""
<div class="custom-card" style="padding:16px;">
    <div class="card-title" style="margin-bottom:0; font-size:1.1rem;">🏛️ {title}</div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Open Resource ↗", url)
    else:
        st.info("No verified educational platforms found.")
        
    st.markdown("#### Recommended Books & Official Data")
    books = library.get("books", [])
    if books:
        for b in books:
            title = b.get('title', 'Book/Data Link')
            url = b.get('url', '#')
            st.markdown(f"""
<div class="custom-card" style="padding:16px;">
    <div class="card-title" style="margin-bottom:0; font-size:1.1rem;">📖 {title}</div>
</div>
""", unsafe_allow_html=True)
            st.link_button("View Book/Resource ↗", url)
    else:
        st.info("No book recommendations found.")
