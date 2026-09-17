"""
ExamGenie AI — Academic Exam Research & Resource Hub
Professional, modern educational website UI inspired by formal Wix academic templates.
Tabs: 🏛️ Official Authority | 📄 Question Papers (Archive) | 🎥 Video Lectures | 📚 Study Resources & Books
"""

import html
import datetime
import streamlit as st
from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)
CURRENT_YEAR = datetime.datetime.now().year

st.set_page_config(
    page_title="ExamGenie AI — Academic Exam Preparation & Resource Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── ACADEMIC / EDUCATIONAL DESIGN SYSTEM (Wix-Inspired) ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@600;700;800;900&display=swap');

:root {
  --canvas-bg: #F8FAFC;
  --surface: #FFFFFF;
  --surface-alt: #F1F5F9;
  --surface-hover: #F8FAFC;
  --primary-navy: #0F1E36;
  --primary-blue: #1E3A8A;
  --accent-blue: #2563EB;
  --accent-blue-hover: #1D4ED8;
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-muted: #64748B;
  --border-light: #E2E8F0;
  --border-strong: #CBD5E1;
  --verified-bg: #DCFCE7;
  --verified-text: #15803D;
  --verified-border: #86EFAC;
  --pdf-bg: #EFF6FF;
  --pdf-text: #1D4ED8;
  --pdf-border: #BFDBFE;
  --alert-bg: #FEF2F2;
  --alert-text: #B91C1C;
  --alert-border: #FECACA;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
}

/* Base resets & typography */
html, body, .stApp {
  background-color: var(--canvas-bg) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
}

/* Header & Navigation Bar */
.academic-navbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  padding: 16px 32px;
  margin: -6rem -4rem 2rem -4rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow-sm);
}
.brand-container {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-icon {
  font-size: 1.8rem;
  background: var(--surface-alt);
  padding: 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}
.brand-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--primary-navy);
  letter-spacing: -0.5px;
  line-height: 1.2;
}
.brand-tagline {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}
.system-status-badge {
  background: #F0FDF4;
  color: #166534;
  border: 1px solid #BBF7D0;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.status-dot {
  width: 8px;
  height: 8px;
  background: #22C55E;
  border-radius: 50%;
  display: inline-block;
}

/* Hero Section */
.hero-wrapper {
  text-align: center;
  max-width: 860px;
  margin: 1.5rem auto 2.5rem auto;
  padding: 0 16px;
}
.hero-eyebrow {
  display: inline-block;
  background: var(--surface-alt);
  color: var(--accent-blue);
  border: 1px solid var(--border-light);
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 6px 16px;
  border-radius: 30px;
  margin-bottom: 16px;
}
.hero-headline {
  font-family: 'Outfit', sans-serif;
  font-size: 3rem;
  font-weight: 800;
  color: var(--primary-navy);
  letter-spacing: -1px;
  line-height: 1.15;
  margin-bottom: 16px;
}
.hero-subtitle {
  font-size: 1.15rem;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 720px;
  margin: 0 auto 2rem auto;
}

/* Value Props Grid */
.trust-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  max-width: 1080px;
  margin: 0 auto 2.5rem auto;
  padding: 0 12px;
}
.trust-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 20px;
  text-align: left;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.trust-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--accent-blue);
}
.trust-card-icon {
  font-size: 1.5rem;
  margin-bottom: 10px;
  display: inline-block;
}
.trust-card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: var(--primary-navy);
  margin-bottom: 6px;
}
.trust-card-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* Academic Card Design */
.edu-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.edu-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
}
.edu-card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary-navy);
  margin: 10px 0 8px 0;
  letter-spacing: -0.3px;
  line-height: 1.3;
}
.edu-card-desc {
  font-size: 0.92rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}

/* Badges */
.badge-official {
  background: var(--verified-bg);
  color: var(--verified-text);
  border: 1px solid var(--verified-border);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.badge-pdf {
  background: var(--pdf-bg);
  color: var(--pdf-text);
  border: 1px solid var(--pdf-border);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.badge-tag {
  background: var(--surface-alt);
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}
.badge-alert {
  background: var(--alert-bg);
  color: var(--alert-text);
  border: 1px solid var(--alert-border);
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* Academic Info Table */
.edu-info-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}
.edu-info-row {
  border-bottom: 1px solid var(--border-light);
  padding: 12px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.edu-info-row:last-child {
  border-bottom: none;
}
.edu-info-label {
  font-size: 0.88rem;
  color: var(--text-muted);
  font-weight: 500;
}
.edu-info-value {
  font-size: 0.92rem;
  color: var(--primary-navy);
  font-weight: 700;
  text-align: right;
}

/* Streamlit Widget Overrides */
div.stButton > button {
  background: var(--accent-blue) !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  border-radius: var(--radius-sm) !important;
  height: 48px !important;
  border: none !important;
  font-size: 1rem !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
div.stButton > button:hover {
  background: var(--accent-blue-hover) !important;
  box-shadow: var(--shadow-md) !important;
  transform: translateY(-1px) !important;
}

.stTextInput > div > div > input {
  background: #FFFFFF !important;
  border: 1.5px solid var(--border-strong) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  padding: 12px 18px !important;
  font-size: 1.05rem !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--accent-blue) !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

.stLinkButton a {
  background: #FFFFFF !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--primary-blue) !important;
  font-size: 0.88rem !important;
  font-weight: 700 !important;
  padding: 8px 16px !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all 0.2s ease !important;
  text-align: center !important;
  display: block !important;
}
.stLinkButton a:hover {
  background: var(--surface-alt) !important;
  border-color: var(--accent-blue) !important;
  color: var(--accent-blue) !important;
  transform: translateY(-1px) !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background-color: transparent;
  border-bottom: 2px solid var(--border-light);
  padding-bottom: 4px;
}
.stTabs [data-baseweb="tab"] {
  height: 48px;
  background-color: transparent;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.95rem;
  padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
  background-color: var(--surface) !important;
  color: var(--accent-blue) !important;
  border-bottom: 3px solid var(--accent-blue) !important;
  font-weight: 700 !important;
}

/* Dashboard Banner */
.dash-banner {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 20px 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}
.dash-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--primary-navy);
  margin-bottom: 4px;
}
.dash-meta {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.meta-pills {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* Footer */
.academic-footer {
  border-top: 1px solid var(--border-light);
  margin-top: 4rem;
  padding: 28px 0 20px 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
}
.footer-brand {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  color: var(--primary-navy);
  font-size: 1rem;
  margin-bottom: 6px;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .hero-headline { font-size: 2.1rem; }
  .academic-navbar { margin: -5rem -1rem 1.5rem -1rem; padding: 12px 16px; }
  .trust-grid { grid-template-columns: 1fr; }
  .dash-banner { flex-direction: column; align-items: flex-start; }
}
</style>
""", unsafe_allow_html=True)

# ── TOP NAVIGATION BAR ────────────────────────────────────────────────────────
st.markdown("""
<div class="academic-navbar">
  <div class="brand-container">
    <div class="brand-icon">🎓</div>
    <div>
      <div class="brand-title">EXAMGENIE AI</div>
      <div class="brand-tagline">Academic Examination Research & Authority Hub</div>
    </div>
  </div>
  <div class="system-status-badge">
    <span class="status-dot"></span> Multi-Agent Research Engine Active
  </div>
</div>
""", unsafe_allow_html=True)

# ── SESSION STATE INITIALIZATION ──────────────────────────────────────────────
for k, v in [("agent", None), ("results", None), ("last_exam", ""), ("updated_at", ""), ("force_refresh", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.agent is None:
    st.session_state.agent = ResearchAgent()


def run_pipeline(exam_name: str, force_refresh: bool = False):
    """Executes the research aggregation pipeline with dynamic academic progress timeline."""
    with st.status(f"Conducting academic research for {exam_name}...", expanded=True) as status:
        try:
            status.update(label="1/6 🌐 Scanning Tier-1 authority portals (.gov.in / .nic.in / .ac.in)...")
            status.update(label="2/6 ⚖️ Verifying examination body facts & syllabus documents...")
            status.update(label="3/6 📑 Discovering authentic previous year question papers...")
            status.update(label="4/6 🎬 Curating verified educational video playlists (excluding Shorts)...")
            status.update(label="5/6 📖 Evaluating recognized textbooks & educational platforms...")
            
            final_res = st.session_state.agent.research_exam(exam_name, force_refresh=force_refresh)
            
            status.update(label="6/6 ✅ Finalizing verified examination dashboard...", state="complete", expanded=False)
            st.session_state.updated_at = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            return final_res
        except Exception as e:
            logger.error("Pipeline failure for '%s': %s", exam_name, e)
            status.update(label="Research aggregation encountered an issue.", state="error", expanded=True)
            st.error("Something went wrong while researching this examination. Please check your network connection or try live refresh.")
            return None


# ── HERO & SEARCH SECTION ─────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
  <div class="hero-eyebrow">Academic Research Platform</div>
  <h1 class="hero-headline">Research Less. Prepare Smarter.</h1>
  <p class="hero-subtitle">
    Autonomous discovery of verified official authority portals, authenticated syllabi, 
    genuine previous year question papers, and curated lecture series for competitive exams.
  </p>
</div>
""", unsafe_allow_html=True)

# Search input row
search_col, btn_col = st.columns([4, 1.2])
with search_col:
    exam_query = st.text_input(
        "search_input",
        value=st.session_state.last_exam,
        placeholder="Enter target exam (e.g. GATE CSE, UPSC Prelims, JEE Advanced, SSC CGL)...",
        label_visibility="collapsed",
    )
with btn_col:
    search_clicked = st.button("Search Examination 🔍", use_container_width=True)

# Options bar below search
opt_col1, opt_col2 = st.columns([1, 1])
with opt_col1:
    force_refresh_toggle = st.checkbox(
        "⚡ Bypass Cache / Force Live Refresh",
        value=False,
        help="Re-runs full web search and verification, bypassing saved database snapshots.",
    )
with opt_col2:
    if st.session_state.results:
        if st.button("🔄 Clear Search Results", use_container_width=False):
            st.session_state.results = None
            st.session_state.last_exam = ""
            st.session_state.updated_at = ""
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── TRUST & VALUE SECTION (Displayed when no active results) ───────────────────
if not st.session_state.results and not (search_clicked and exam_query.strip()):
    st.markdown("""
<div class="trust-grid">
  <div class="trust-card">
    <div class="trust-card-icon">🏛️</div>
    <div class="trust-card-title">Verified Official Portals</div>
    <div class="trust-card-desc">Direct links to conducting bodies (.gov.in, .nic.in) bypassing blog spam.</div>
  </div>
  <div class="trust-card">
    <div class="trust-card-icon">📄</div>
    <div class="trust-card-title">Authentic Past Papers</div>
    <div class="trust-card-desc">Downloadable PYQ PDFs and verified answer keys with year metadata.</div>
  </div>
  <div class="trust-card">
    <div class="trust-card-icon">🎥</div>
    <div class="trust-card-title">Curated Video Courses</div>
    <div class="trust-card-desc">Structured lecture series categorized by Foundation, Full Course, and PYQs.</div>
  </div>
  <div class="trust-card">
    <div class="trust-card-icon">📚</div>
    <div class="trust-card-title">Standard Reference Books</div>
    <div class="trust-card-desc">Recommended textbooks from recognized institutions and toppers' references.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SEARCH EXECUTION ──────────────────────────────────────────────────────────
if search_clicked and exam_query.strip():
    with st.spinner("Initializing multi-agent research..."):
        res = run_pipeline(exam_query.strip(), force_refresh=force_refresh_toggle)
        if res:
            st.session_state.results = res
            st.session_state.last_exam = exam_query.strip()
            st.rerun()

# Halt execution if no results present
if not st.session_state.results:
    st.stop()

# ── DASHBOARD RESULTS PRESENTATION ─────────────────────────────────────────────
data = st.session_state.results or {}
authority = data.get("authority", {})
archive = data.get("archive", [])
videos = data.get("videos", [])
library = data.get("library", {})
meta = data.get("_metadata", {})

active_exam = st.session_state.last_exam or "Target Examination"
is_cache_hit = meta.get("cache_hit", False)
source_status = "Cached Snapshot (Instant)" if is_cache_hit else "Live Verified Scan"
updated_display = st.session_state.updated_at or "Recently Verified"

# Results Overview Banner
st.markdown(f"""
<div class="dash-banner">
  <div>
    <div class="dash-title">🎓 {html.escape(active_exam.upper())}</div>
    <div class="dash-meta">Verified Research Dashboard • Last Checked: {updated_display}</div>
  </div>
  <div class="meta-pills">
    <span class="badge-tag">📊 Status: {source_status}</span>
    <span class="badge-tag">📑 {len(archive)} Past Papers</span>
    <span class="badge-tag">🎬 {len(videos)} Video Courses</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 4 ACADEMIC TABS ───────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏛️ Official Exam Information",
    "📄 Previous Year Question Papers",
    "🎥 Curated Video Lectures",
    "📚 Study Resources & Recommended Books",
])

# ── TAB 1: OFFICIAL EXAM INFORMATION (AUTHORITY) ──────────────────────────────
with tab1:
    details = authority.get("details", {})
    off_site = authority.get("official_site")
    syl_pdf = authority.get("syllabus_pdf")
    has_update = details.get("has_new_update", False)

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        # Official Website Card
        if off_site and off_site.get("url"):
            site_title = html.escape(off_site.get("title", f"{active_exam} Official Portal"))
            site_url = off_site.get("url", "#")
            is_gov = off_site.get("is_gov_domain", False)
            gov_badge = '<span class="badge-official">✓ Verified Official Source</span>' if is_gov else '<span class="badge-tag">Primary Portal</span>'

            st.markdown(f"""
<div class="edu-card">
  {gov_badge}
  <div class="edu-card-title">{site_title}</div>
  <div class="edu-card-desc">
    This is the primary authority portal for application procedures, notifications, and examination rules. 
    Always rely on this domain over third-party commercial portals.
  </div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Launch Official Website ↗", site_url, use_container_width=True)
        else:
            st.markdown(f"""
<div class="edu-card">
  <span class="badge-tag">Web Search</span>
  <div class="edu-card-title">Conducting Body Portal</div>
  <div class="edu-card-desc">Direct government authority domain requires manual verification.</div>
</div>
""", unsafe_allow_html=True)
            fallback_search = f"https://www.google.com/search?q={active_exam.replace(' ', '+')}+official+website"
            st.link_button("Search Official Portal on Google 🔍", fallback_search, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Official Syllabus Document Card
        if syl_pdf and syl_pdf.get("url"):
            syl_title = html.escape(syl_pdf.get("title", f"{active_exam} Information Bulletin / Syllabus PDF"))
            syl_url = syl_pdf.get("url", "#")

            st.markdown(f"""
<div class="edu-card">
  <span class="badge-pdf">📄 Deep Link Document</span>
  <div class="edu-card-title">{syl_title}</div>
  <div class="edu-card-desc">
    Official syllabus and curriculum bulletin hosted on institutional servers. 
    Bypasses third-party advertising and clickbait summaries.
  </div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Download Official Syllabus PDF 📥", syl_url, use_container_width=True)
        else:
            st.info("ℹ️ Direct syllabus PDF deep link not indexed. Refer to the official website portal above.")

    with col_right:
        # Status Ticker Card
        if has_update:
            st.markdown('<div class="badge-alert">🚨 Recent Notification / Update Live</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge-tag" style="width:100%;text-align:center;box-sizing:border-box;">ℹ️ Regular Examination Schedule</div>', unsafe_allow_html=True)

        conducting_body = html.escape(str(details.get("conducting_body", "Official Examination Authority")))
        frequency = html.escape(str(details.get("frequency", "Annual")))
        reg_dates = html.escape(str(details.get("registration_dates", "Refer to official bulletin")))
        about_exam = html.escape(str(details.get("about_exam", "")))

        st.markdown(f"""
<div class="edu-card">
  <div style="font-family:'Outfit',sans-serif;font-weight:700;color:var(--primary-navy);font-size:1.1rem;margin-bottom:12px;border-bottom:1px solid var(--border-light);padding-bottom:8px;">
    Official Key Facts
  </div>
  <div class="edu-info-table">
    <div class="edu-info-row">
      <span class="edu-info-label">Conducting Authority</span>
      <span class="edu-info-value">{conducting_body}</span>
    </div>
    <div class="edu-info-row">
      <span class="edu-info-label">Exam Frequency</span>
      <span class="edu-info-value">{frequency}</span>
    </div>
    <div class="edu-info-row">
      <span class="edu-info-label">Application Window</span>
      <span class="edu-info-value" style="color:var(--accent-blue);">{reg_dates}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        if about_exam and about_exam != "Not Available":
            st.markdown(f"""
<div class="edu-card">
  <div style="font-family:'Outfit',sans-serif;font-weight:700;color:var(--primary-navy);font-size:1.05rem;margin-bottom:8px;">
    Overview & Objective
  </div>
  <div class="edu-card-desc" style="margin-bottom:0;">{about_exam}</div>
</div>
""", unsafe_allow_html=True)


# ── TAB 2: PREVIOUS YEAR QUESTION PAPERS (ARCHIVE) ────────────────────────────
with tab2:
    st.markdown("### 📄 Previous Year Question Papers & Official Solutions")
    st.caption("Authenticated question papers, solved mock tests, and answer keys prioritized by source reliability.")

    if archive:
        for p in archive:
            title = html.escape(str(p.get("title", "Previous Year Question Paper")))
            url = p.get("url", "#")
            is_pdf = (p.get("type") == "pdf") or url.lower().endswith(".pdf") or "pdf" in url.lower()
            year = html.escape(str(p.get("year", "Recent")))
            is_off = p.get("is_official", False)
            source_lbl = html.escape(str(p.get("source", "Verified Source")))
            
            badge_html = '<span class="badge-official">✓ Official Domain</span> ' if is_off else ''
            badge_html += '<span class="badge-pdf">📄 PDF Document</span>' if is_pdf else '<span class="badge-tag">🔗 Web Portal</span>'

            st.markdown(f"""
<div class="edu-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
    <div>{badge_html}</div>
    <span class="badge-tag">Year: {year} • {source_lbl}</span>
  </div>
  <div class="edu-card-title" style="font-size:1.1rem;margin-top:4px;">{title}</div>
</div>
""", unsafe_allow_html=True)
            st.link_button(f"Access Paper ({'PDF' if is_pdf else 'Link'}) ↗", url, key=f"pyq_{url}")
    else:
        st.info("ℹ️ No previous papers were identified for this exam. You can check the official portal in Tab 1 for published question banks.")


# ── TAB 3: CURATED VIDEO LECTURES ─────────────────────────────────────────────
with tab3:
    st.markdown("### 🎥 Curated Video Courses & Topic Playlists")
    st.caption("Structured video playlists from recognized educators categorized by difficulty level.")

    if videos:
        v_cols = st.columns(2)
        for idx, v in enumerate(videos):
            title = html.escape(str(v.get("title", "Exam Lecture Series")))
            cat = html.escape(str(v.get("category", "Full Course")))
            channel = html.escape(str(v.get("channel", "Verified Educator")))
            desc = html.escape(str(v.get("description", "Comprehensive syllabus preparation course.")))
            url = v.get("url", "#")

            with v_cols[idx % 2]:
                st.markdown(f"""
<div class="edu-card" style="height:calc(100% - 20px);">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span class="badge-tag">▶️ {cat.upper()}</span>
    <span style="font-size:0.8rem;color:var(--text-muted);font-weight:600;">{channel}</span>
  </div>
  <div class="edu-card-title" style="font-size:1.15rem;">{title}</div>
  <div class="edu-card-desc">{desc}</div>
</div>
""", unsafe_allow_html=True)
                st.link_button("Watch Course Playlist ▶️", url, key=f"yt_{url}_{idx}")
    else:
        st.info("ℹ️ No verified video courses found for this query.")


# ── TAB 4: STUDY RESOURCES & RECOMMENDED BOOKS ────────────────────────────────
with tab4:
    st.markdown("### 📚 Study Resources & Recommended Reference Books")
    st.caption("Curated preparatory material from recognized educational institutions and topper recommendations.")

    edtech_links = library.get("edtech_links", [])
    books = library.get("books", [])

    st.markdown("#### 🏛️ Recognized Academic & Learning Platforms")
    if edtech_links:
        for d in edtech_links:
            title = html.escape(str(d.get("title", "Educational Resource")))
            platform = html.escape(str(d.get("platform", "Educational Platform")))
            desc = html.escape(str(d.get("description", "Exam preparation modules and practice material.")))
            url = d.get("url", "#")

            st.markdown(f"""
<div class="edu-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span class="badge-official">✓ {platform}</span>
  </div>
  <div class="edu-card-title" style="font-size:1.1rem;">{title}</div>
  <div class="edu-card-desc" style="margin-bottom:12px;">{desc}</div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Open Resource Portal ↗", url, key=f"edtech_{url}")
    else:
        st.info("ℹ️ No additional platform resources identified.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📖 Standard Reference Books & Texts")
    if books:
        for b in books:
            b_title = html.escape(str(b.get("title", "Standard Reference Textbook")))
            author = html.escape(str(b.get("author", "Standard Academic Author")))
            purpose = html.escape(str(b.get("purpose", "Core Theory & Practice")))
            url = b.get("url", "#")

            st.markdown(f"""
<div class="edu-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span class="badge-tag">📖 Textbook</span>
    <span style="font-size:0.8rem;color:var(--accent-blue);font-weight:700;">{purpose}</span>
  </div>
  <div class="edu-card-title" style="font-size:1.1rem;">{b_title}</div>
  <div class="edu-card-desc" style="margin-bottom:12px;">Author / Recommended by: <strong>{author}</strong></div>
</div>
""", unsafe_allow_html=True)
            if url and url != "#":
                st.link_button("View Book Reference ↗", url, key=f"book_{url}")
    else:
        st.info("ℹ️ No specific textbook recommendations found for this exam query.")


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="academic-footer">
  <div class="footer-brand">EXAMGENIE AI</div>
  <div>Academic Examination Research & Resource Aggregation Platform</div>
  <div style="margin-top:8px;font-size:0.78rem;color:#94A3B8;">
    Built with Python & Streamlit • Multi-Agent Verification Architecture
  </div>
</div>
""", unsafe_allow_html=True)
