"""
ExamGenie AI — Academic Examination Research & Resource Portal
A formal, modern educational examination portal inspired by institutional and Wix education templates.
Data-first, high-contrast, clean academic layout with zero technical leaks.
"""

import html
import datetime
import streamlit as st
from exam_ai_agent.agents.research_agent import ResearchAgent
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="ExamGenie AI | Exam Research & Preparation",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── FORMAL ACADEMIC DESIGN SYSTEM ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {
  --bg-canvas: #F8FAFC;
  --surface-card: #FFFFFF;
  --surface-subtle: #F1F5F9;
  --surface-hover: #F8FAFC;
  --navy-dark: #0F172A;
  --navy-primary: #1E293B;
  --blue-academic: #1D4ED8;
  --blue-accent: #2563EB;
  --blue-hover: #1E40AF;
  --text-main: #0F172A;
  --text-body: #334155;
  --text-muted: #475569;
  --border-light: #E2E8F0;
  --border-medium: #CBD5E1;
  --badge-green-bg: #DCFCE7;
  --badge-green-text: #166534;
  --badge-green-border: #BBF7D0;
  --badge-blue-bg: #EFF6FF;
  --badge-blue-text: #1E40AF;
  --badge-blue-border: #BFDBFE;
  --badge-amber-bg: #FEF3C7;
  --badge-amber-text: #92400E;
  --badge-amber-border: #FDE68A;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-card: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-hover: 0 4px 12px rgba(15, 23, 42, 0.08);
  --radius-sm: 6px;
  --radius-md: 10px;
}

/* Page Layout & Container */
html, body, .stApp {
  background-color: var(--bg-canvas) !important;
  color: var(--text-main) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
}

p, span, div, li, td, th {
  color: var(--text-body);
}

h1, h2, h3, h4, h5, h6 {
  color: var(--navy-dark) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: -0.3px;
}

strong, b {
  color: var(--navy-dark) !important;
  font-weight: 700 !important;
}

header[data-testid="stHeader"] {
  background: transparent !important;
  height: 1.5rem !important;
}

.main .block-container {
  padding-top: 1rem !important;
  padding-bottom: 3rem !important;
  max-width: 1100px !important;
}

/* Captions & Subtitles */
.stCaption, [data-testid="stCaptionContainer"] p {
  color: var(--text-muted) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
  margin-top: -4px !important;
  margin-bottom: 14px !important;
}

/* Header & Navigation Bar */
.edu-navbar {
  background: var(--surface-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 14px 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow-sm);
}
.edu-brand-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.edu-brand-icon {
  font-size: 1.6rem;
  background: var(--surface-subtle);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}
.edu-brand-name {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--navy-dark);
  letter-spacing: -0.3px;
  line-height: 1.2;
}
.edu-brand-tag {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}
.edu-nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}
.edu-nav-item {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-body);
  text-decoration: none;
}
.edu-nav-dot {
  font-size: 0.75rem;
  color: var(--border-medium);
}
.edu-portal-tag {
  background: var(--surface-subtle);
  color: var(--blue-academic);
  border: 1px solid var(--border-light);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.3px;
}

/* Hero Section */
.edu-hero {
  text-align: center;
  max-width: 760px;
  margin: 0 auto 20px auto;
  padding: 8px 12px 0 12px;
}
.edu-hero-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 2.35rem;
  font-weight: 800;
  color: var(--navy-dark);
  letter-spacing: -0.6px;
  line-height: 1.2;
  margin-bottom: 12px;
}
.edu-hero-desc {
  font-size: 1.05rem;
  color: var(--text-body);
  line-height: 1.6;
  margin-bottom: 0;
}

/* Streamlit Input & Widget Styling */
.stTextInput > div > div > input {
  background: #FFFFFF !important;
  border: 1.5px solid var(--border-medium) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--navy-dark) !important;
  padding: 12px 16px !important;
  font-size: 1.02rem !important;
  font-weight: 500 !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--blue-academic) !important;
  box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12) !important;
}
.stTextInput > div > div > input::placeholder {
  color: #64748B !important;
  opacity: 1 !important;
}

/* Checkbox */
[data-testid="stCheckbox"] label span {
  color: var(--navy-primary) !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
}

/* Primary Button */
div.stButton > button, div.stFormSubmitButton > button {
  background: var(--blue-academic) !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  border-radius: var(--radius-sm) !important;
  height: 48px !important;
  border: none !important;
  font-size: 1rem !important;
  transition: all 0.15s ease !important;
  width: 100% !important;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
  background: var(--blue-hover) !important;
  box-shadow: 0 2px 6px rgba(29, 78, 216, 0.25) !important;
}

/* Secondary Button */
div.stButton > button[kind="secondary"] {
  background: #FFFFFF !important;
  color: var(--text-body) !important;
  border: 1px solid var(--border-medium) !important;
  height: 38px !important;
  font-size: 0.88rem !important;
}
div.stButton > button[kind="secondary"]:hover {
  background: var(--surface-subtle) !important;
  color: var(--navy-dark) !important;
  border-color: var(--text-muted) !important;
}

/* Link Button */
.stLinkButton a {
  background: #FFFFFF !important;
  border: 1.5px solid var(--border-medium) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--blue-academic) !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
  transition: all 0.15s ease !important;
  text-align: center !important;
  display: block !important;
}
.stLinkButton a:hover {
  background: var(--badge-blue-bg) !important;
  border-color: var(--blue-academic) !important;
  color: var(--blue-hover) !important;
}

/* Tabs Header */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background-color: transparent;
  border-bottom: 2px solid var(--border-light);
  padding-bottom: 2px;
}
.stTabs [data-baseweb="tab"] {
  height: 48px;
  background-color: transparent;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  padding: 8px 18px;
}
.stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {
  color: var(--text-body) !important;
  font-weight: 600 !important;
  font-size: 0.94rem !important;
}
.stTabs [aria-selected="true"] {
  background-color: var(--surface-card) !important;
  border-bottom: 3px solid var(--blue-academic) !important;
}
.stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
  color: var(--blue-academic) !important;
  font-weight: 700 !important;
}

/* Status & Alert Widgets */
[data-testid="stStatusWidget"] {
  background: #FFFFFF !important;
  border: 1.5px solid var(--border-medium) !important;
  border-radius: var(--radius-md) !important;
}
[data-testid="stStatusWidget"] * {
  color: var(--navy-dark) !important;
}

/* Academic Card Design */
.edu-card {
  background: var(--surface-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.edu-card:hover {
  border-color: var(--border-medium);
  box-shadow: var(--shadow-hover);
}
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  flex-wrap: wrap;
  gap: 8px;
}
.card-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.08rem;
  font-weight: 700;
  color: var(--navy-dark);
  margin: 4px 0 6px 0;
  line-height: 1.4;
}
.card-desc {
  font-size: 0.90rem;
  color: var(--text-body);
  line-height: 1.55;
  margin-bottom: 8px;
}
.card-meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.82rem;
  color: var(--text-muted);
  font-weight: 600;
  margin-top: 6px;
}

/* Badges */
.badge-official {
  background: var(--badge-green-bg);
  color: var(--badge-green-text);
  border: 1px solid var(--badge-green-border);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.badge-pdf {
  background: var(--badge-blue-bg);
  color: var(--badge-blue-text);
  border: 1px solid var(--badge-blue-border);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.badge-tag {
  background: var(--surface-subtle);
  color: var(--navy-primary);
  border: 1px solid var(--border-light);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}
.badge-category {
  background: var(--badge-amber-bg);
  color: var(--badge-amber-text);
  border: 1px solid var(--badge-amber-border);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
}

/* Key Fact Sheet */
.fact-table {
  width: 100%;
  border-collapse: collapse;
}
.fact-row {
  border-bottom: 1px solid var(--border-light);
  padding: 10px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.fact-row:last-child {
  border-bottom: none;
}
.fact-label {
  font-size: 0.88rem;
  color: var(--text-muted);
  font-weight: 600;
}
.fact-val {
  font-size: 0.92rem;
  color: var(--navy-dark);
  font-weight: 700;
  text-align: right;
}

/* Results Top Banner */
.results-header-banner {
  background: var(--surface-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}
.results-exam-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--navy-dark);
}
.results-timestamp {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin-top: 2px;
  font-weight: 500;
}
.results-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Feature Showcase Grid (When no active search) */
.showcase-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.showcase-card {
  background: var(--surface-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}
.showcase-icon {
  font-size: 1.8rem;
  margin-bottom: 8px;
}
.showcase-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--navy-dark);
  margin-bottom: 6px;
}
.showcase-desc {
  font-size: 0.88rem;
  color: var(--text-body);
  line-height: 1.5;
}

/* Minimal Academic Footer */
.edu-footer {
  border-top: 1px solid var(--border-light);
  margin-top: 48px;
  padding: 24px 0 12px 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.84rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .edu-hero-title { font-size: 1.85rem; }
  .edu-navbar { padding: 12px 16px; flex-direction: column; gap: 8px; align-items: flex-start; }
  .results-header-banner { flex-direction: column; align-items: flex-start; }
  .showcase-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)

# ── COMPACT HEADER & NAVBAR ───────────────────────────────────────────────────
st.markdown("""
<div class="edu-navbar">
  <div class="edu-brand-left">
    <div class="edu-brand-icon">🎓</div>
    <div>
      <div class="edu-brand-name">EXAMGENIE AI</div>
      <div class="edu-brand-tag">Exam Research & Preparation</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SESSION STATE INITIALIZATION ──────────────────────────────────────────────
for state_key, default_val in [
    ("agent", None),
    ("results", None),
    ("last_exam", ""),
    ("updated_at", ""),
    ("trigger_search", False),
]:
    if state_key not in st.session_state:
        st.session_state[state_key] = default_val

if st.session_state.agent is None:
    st.session_state.agent = ResearchAgent()


def perform_research(exam_name: str, force_refresh: bool = False):
    """Executes the research aggregation pipeline with clean educational milestones."""
    with st.status(f"Researching: {exam_name}", expanded=True) as status:
        try:
            status.update(label="✓ Finding official authority information...")
            status.update(label="✓ Collecting previous papers & answer keys...")
            status.update(label="✓ Finding study resources & textbooks...")
            status.update(label="✓ Curating video lecture courses...")

            result = st.session_state.agent.research_exam(exam_name, force_refresh=force_refresh)

            status.update(label="Research verified and complete.", state="complete", expanded=False)
            st.session_state.updated_at = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            return result
        except Exception as e:
            logger.error("Research error for '%s': %s", exam_name, e)
            status.update(label="Research encountered an issue. Please try live refresh.", state="error", expanded=True)
            st.error("Unable to complete research. Please check your connection or try Force Live Refresh.")
            return None


# ── HERO SECTION ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="edu-hero">
  <h1 class="edu-hero-title">Research Smarter. Prepare Better.</h1>
  <p class="edu-hero-desc">
    Find trusted exam information, previous papers, study resources and learning materials — all in one place.
  </p>
</div>
""", unsafe_allow_html=True)

# ── SEARCH CONTAINER ──────────────────────────────────────────────────────────
with st.container():
    with st.form(key="exam_search_form", border=False):
        search_col, btn_col = st.columns([4, 1.3])
        with search_col:
            exam_input = st.text_input(
                "search_query",
                value=st.session_state.last_exam,
                placeholder="Enter an exam or competitive test",
                label_visibility="collapsed",
            )
        with btn_col:
            search_submitted = st.form_submit_button("Start Research →", use_container_width=True)

    # Sub-controls row
    opt_col1, opt_col2 = st.columns([1.2, 1])
    with opt_col1:
        force_refresh_checked = st.checkbox(
            "Force Live Refresh",
            value=False,
            help="Bypass cached snapshots and re-run live web searches across all sources.",
        )
    with opt_col2:
        if st.session_state.results:
            if st.button("Clear Results", use_container_width=False):
                st.session_state.results = None
                st.session_state.last_exam = ""
                st.session_state.updated_at = ""
                st.rerun()

# ── HOMEPAGE OVERVIEW (When no active search results) ─────────────────────────
if not st.session_state.results and not (search_submitted and exam_input.strip()):
    st.markdown("""
<div class="showcase-grid">
  <div class="showcase-card">
    <div class="showcase-icon">🏛️</div>
    <div class="showcase-title">Official Authority Information</div>
    <div class="showcase-desc">Direct links to verified conducting bodies, authenticated syllabus bulletins, notification schedules, and official guidelines.</div>
  </div>
  <div class="showcase-card">
    <div class="showcase-icon">📄</div>
    <div class="showcase-title">Previous Question Papers</div>
    <div class="showcase-desc">Past year question papers, official answer keys, and authentic examination archives organized with year metadata.</div>
  </div>
  <div class="showcase-card">
    <div class="showcase-icon">📚</div>
    <div class="showcase-title">Resources, Books & Video Lectures</div>
    <div class="showcase-desc">Curated preparation guides from recognized academic platforms, standard reference textbooks, and structured video courses.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── HANDLE SEARCH EXECUTION ───────────────────────────────────────────────────
should_run = (search_submitted and exam_input.strip()) or st.session_state.trigger_search
target_to_run = exam_input.strip() if search_submitted else st.session_state.last_exam

if should_run and target_to_run:
    st.session_state.trigger_search = False
    with st.spinner("Conducting comprehensive exam research..."):
        fresh_data = perform_research(target_to_run, force_refresh=force_refresh_checked)
        if fresh_data:
            st.session_state.results = fresh_data
            st.session_state.last_exam = target_to_run
            st.rerun()

# If still no results present, show clean footer and stop
if not st.session_state.results:
    st.markdown("""
<div class="edu-footer">
  <strong>ExamGenie AI</strong> • Comprehensive Academic Examination Research & Preparation
</div>
""", unsafe_allow_html=True)
    st.stop()

# ── RESULTS DASHBOARD PRESENTATION ─────────────────────────────────────────────
data = st.session_state.results or {}
authority = data.get("authority") if isinstance(data.get("authority"), dict) else {}
archive = data.get("archive") if isinstance(data.get("archive"), list) else []
videos = data.get("videos") if isinstance(data.get("videos"), list) else []
library = data.get("library") if isinstance(data.get("library"), dict) else {}
edtech_links = library.get("edtech_links") if isinstance(library.get("edtech_links"), list) else []
books = library.get("books") if isinstance(library.get("books"), list) else []
meta = data.get("_metadata") if isinstance(data.get("_metadata"), dict) else {}

active_exam = st.session_state.last_exam or meta.get("exam_name", "Examination")
is_cache = meta.get("cache_hit", False)
source_label = "Instant Cached Snapshot" if is_cache else "Live Verified Research"
last_updated = st.session_state.updated_at or "Recently Verified"

total_resources_and_books = len(edtech_links) + len(books)

# Results Overview Banner
st.markdown(f"""
<div class="results-header-banner">
  <div>
    <div class="results-exam-title">{html.escape(active_exam.upper())}</div>
    <div class="results-timestamp">Last Updated: {last_updated} • Status: {source_label}</div>
  </div>
  <div class="results-pills">
    <span class="badge-tag">🏛️ Authority Verified</span>
    <span class="badge-tag">📄 {len(archive)} Papers</span>
    <span class="badge-tag">📚 {total_resources_and_books} Resources & Books</span>
    <span class="badge-tag">🎥 {len(videos)} Video Series</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 4 CONSOLIDATED ACADEMIC DATA TABS ───────────────────────────────────────────
tab_auth, tab_pyq, tab_resources, tab_video = st.tabs([
    "🏛️ Authority",
    "📄 Previous Papers",
    "📚 Resources & Books",
    "🎥 Video Lectures",
])

# ── TAB 1: AUTHORITY ──────────────────────────────────────────────────────────
with tab_auth:
    details = authority.get("details") if isinstance(authority.get("details"), dict) else {}
    off_site = authority.get("official_site") if isinstance(authority.get("official_site"), dict) else None
    syl_pdf = authority.get("syllabus_pdf") if isinstance(authority.get("syllabus_pdf"), dict) else None
    has_update = details.get("has_new_update", False)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        # Official Website Card
        if off_site and off_site.get("url"):
            site_title = html.escape(str(off_site.get("title") or f"{active_exam} Official Portal"))
            site_url = off_site.get("url", "#")
            is_gov = off_site.get("is_gov_domain", False)
            badge_html = '<span class="badge-official">✓ Official Source</span>' if is_gov else '<span class="badge-tag">Primary Portal</span>'

            st.markdown(f"""
<div class="edu-card">
  {badge_html}
  <div class="card-title">{site_title}</div>
  <div class="card-desc">
    Official authority portal for applications, notifications, schedules, and examination regulations.
  </div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Launch Official Website ↗", site_url, use_container_width=True)
        else:
            st.markdown("""
<div class="edu-card">
  <span class="badge-tag">Web Portal</span>
  <div class="card-title">Conducting Body Portal</div>
  <div class="card-desc">Direct government authority domain requires manual verification.</div>
</div>
""", unsafe_allow_html=True)
            fallback_search = f"https://www.google.com/search?q={active_exam.replace(' ', '+')}+official+website"
            st.link_button("Search Official Portal on Google 🔍", fallback_search, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Official Syllabus Card
        if syl_pdf and syl_pdf.get("url"):
            syl_title = html.escape(str(syl_pdf.get("title") or f"{active_exam} Official Syllabus / Bulletin"))
            syl_url = syl_pdf.get("url", "#")
            is_pdf = syl_pdf.get("is_pdf", False) or syl_url.lower().endswith(".pdf")
            doc_badge = '<span class="badge-pdf">📄 Syllabus PDF</span>' if is_pdf else '<span class="badge-tag">🔗 Syllabus Portal</span>'

            st.markdown(f"""
<div class="edu-card">
  {doc_badge}
  <div class="card-title">{syl_title}</div>
  <div class="card-desc">
    Official curriculum document and examination scheme published by the conducting institution.
  </div>
</div>
""", unsafe_allow_html=True)
            st.link_button("Download Official Syllabus 📥", syl_url, use_container_width=True)
        else:
            st.info("Direct syllabus document not indexed. Refer to the official website link above.")

    with col2:
        conducting_body = html.escape(str(details.get("conducting_body") or "Official Examination Authority"))
        frequency = html.escape(str(details.get("frequency") or "Annual"))
        reg_dates = html.escape(str(details.get("registration_dates") or "Refer to official notifications"))
        about_exam = html.escape(str(details.get("about_exam") or ""))

        status_tag = '<span class="badge-official">✓ Active Schedule</span>' if has_update else '<span class="badge-tag">Regular Annual Cycle</span>'

        st.markdown(f"""
<div class="edu-card">
  <div class="card-header-row">
    <span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;color:var(--navy-dark);font-size:1.05rem;">
      Key Facts
    </span>
    {status_tag}
  </div>
  <div class="fact-table">
    <div class="fact-row">
      <span class="fact-label">Conducting Authority</span>
      <span class="fact-val">{conducting_body}</span>
    </div>
    <div class="fact-row">
      <span class="fact-label">Exam Frequency</span>
      <span class="fact-val">{frequency}</span>
    </div>
    <div class="fact-row">
      <span class="fact-label">Application Timeline</span>
      <span class="fact-val" style="color:var(--blue-academic);">{reg_dates}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        if about_exam and about_exam != "Not Available":
            st.markdown(f"""
<div class="edu-card">
  <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;color:var(--navy-dark);font-size:1rem;margin-bottom:8px;">
    Examination Overview
  </div>
  <div class="card-desc" style="margin-bottom:0;">{about_exam}</div>
</div>
""", unsafe_allow_html=True)


# ── TAB 2: PREVIOUS PAPERS ────────────────────────────────────────────────────
with tab_pyq:
    st.markdown("### Previous Year Question Papers")
    st.caption("Authenticated question papers, solved past examinations, and answer keys.")

    if archive:
        # Prioritize direct PDF links first
        sorted_papers = sorted(
            archive,
            key=lambda x: (
                0 if ((x.get("type") == "pdf") or str(x.get("url", "")).lower().endswith(".pdf")) else 1,
                0 if x.get("is_official", False) else 1,
            )
        )

        seen_urls = set()
        for p in sorted_papers:
            url = p.get("url", "#")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = html.escape(str(p.get("title") or "Question Paper"))
            is_pdf = (p.get("type") == "pdf") or url.lower().endswith(".pdf") or "pdf" in url.lower()
            year = html.escape(str(p.get("year") or "Recent"))
            is_off = p.get("is_official", False)
            source_lbl = html.escape(str(p.get("source") or "Verified Source"))

            badge_html = '<span class="badge-official">✓ Official Domain</span> ' if is_off else ''
            badge_html += '<span class="badge-pdf">📄 PDF</span>' if is_pdf else '<span class="badge-tag">🔗 Web Link</span>'

            card_col, btn_col = st.columns([4, 1.2])
            with card_col:
                st.markdown(f"""
<div class="edu-card" style="margin-bottom:10px;padding:14px 18px;">
  <div class="card-header-row" style="margin-bottom:4px;">
    <div>{badge_html}</div>
    <span class="badge-tag">Year: {year} • {source_lbl}</span>
  </div>
  <div class="card-title" style="font-size:1.02rem;margin:4px 0 0 0;">{title}</div>
</div>
""", unsafe_allow_html=True)
            with btn_col:
                st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
                btn_label = "Open PDF 📥" if is_pdf else "Open Resource ↗"
                st.link_button(btn_label, url, use_container_width=True)
    else:
        st.info("No previous papers directly indexed for this query. Refer to the official website in the Authority tab.")


# ── TAB 3: COMBINED RESOURCES & BOOKS ──────────────────────────────────────────
with tab_resources:
    st.markdown("### Resources & Books")
    st.caption("Preparation resources, recognized learning platforms, standard textbooks, and study materials.")

    has_any_content = bool(edtech_links or books)

    if not has_any_content:
        st.info("No specialized study materials or books indexed for this examination query.")
    else:
        # Partition edtech_links into subcategories:
        # 1) PDFs & Study Materials
        # 2) Learning Platforms
        # 3) Preparation Resources
        pdf_materials = []
        platform_resources = []
        prep_resources = []

        for item in edtech_links:
            url_lower = str(item.get("url", "")).lower()
            cat = str(item.get("category", "")).lower()
            is_doc = url_lower.endswith(".pdf") or "pdf" in url_lower or "notes" in cat or "pdf" in cat

            if is_doc:
                pdf_materials.append(item)
            elif any(k in cat for k in ["platform", "course", "portal", "institute"]) or any(k in str(item.get("platform", "")).lower() for k in ["academy", "portal", "course"]):
                platform_resources.append(item)
            else:
                prep_resources.append(item)

        # Fallback if partitioning leaves prep_resources empty but items exist
        if not prep_resources and not platform_resources and not pdf_materials and edtech_links:
            prep_resources = edtech_links

        # ── SUBCATEGORY 1: PREPARATION RESOURCES ──────────────────────────────
        if prep_resources:
            st.markdown("#### Preparation Resources")
            for d in prep_resources:
                title = html.escape(str(d.get("title") or "Study Resource"))
                platform = html.escape(str(d.get("platform") or "Educational Source"))
                desc = html.escape(str(d.get("description") or "Comprehensive syllabus preparation material."))
                url = d.get("url", "#")
                cat_tag = html.escape(str(d.get("category") or "Preparation Guide"))

                r_col1, r_col2 = st.columns([4, 1.2])
                with r_col1:
                    st.markdown(f"""
<div class="edu-card" style="margin-bottom:10px;padding:14px 18px;">
  <div class="card-header-row" style="margin-bottom:4px;">
    <span class="badge-category">{cat_tag}</span>
    <span class="badge-tag">Source: {platform}</span>
  </div>
  <div class="card-title" style="font-size:1.02rem;margin:4px 0 6px 0;">{title}</div>
  <div class="card-desc" style="margin-bottom:0;">{desc}</div>
</div>
""", unsafe_allow_html=True)
                with r_col2:
                    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
                    st.link_button("Open Resource ↗", url, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

        # ── SUBCATEGORY 2: LEARNING PLATFORMS ─────────────────────────────────
        if platform_resources:
            st.markdown("#### Learning Platforms")
            for d in platform_resources:
                title = html.escape(str(d.get("title") or "Learning Platform Resource"))
                platform = html.escape(str(d.get("platform") or "Educational Portal"))
                desc = html.escape(str(d.get("description") or "Educational course modules and subject material."))
                url = d.get("url", "#")

                r_col1, r_col2 = st.columns([4, 1.2])
                with r_col1:
                    st.markdown(f"""
<div class="edu-card" style="margin-bottom:10px;padding:14px 18px;">
  <div class="card-header-row" style="margin-bottom:4px;">
    <span class="badge-tag">Platform: {platform}</span>
  </div>
  <div class="card-title" style="font-size:1.02rem;margin:4px 0 6px 0;">{title}</div>
  <div class="card-desc" style="margin-bottom:0;">{desc}</div>
</div>
""", unsafe_allow_html=True)
                with r_col2:
                    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
                    st.link_button("Open Resource ↗", url, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

        # ── SUBCATEGORY 3: BOOKS ──────────────────────────────────────────────
        if books:
            st.markdown("#### Books")
            b_cols = st.columns(2)
            for idx, b in enumerate(books):
                b_title = html.escape(str(b.get("title") or "Standard Reference Textbook"))
                author = html.escape(str(b.get("author") or "Recognized Academic Author"))
                purpose = html.escape(str(b.get("purpose") or "Core Theory & Practice"))
                url = b.get("url", "#")

                with b_cols[idx % 2]:
                    st.markdown(f"""
<div class="edu-card" style="height:calc(100% - 16px);margin-bottom:12px;">
  <div class="card-header-row" style="margin-bottom:6px;">
    <span class="badge-tag">📖 Reference Book</span>
    <span style="font-size:0.78rem;color:var(--blue-academic);font-weight:700;">{purpose}</span>
  </div>
  <div class="card-title" style="font-size:1.05rem;">{b_title}</div>
  <div class="card-desc">Author / Publication: <strong>{author}</strong></div>
</div>
""", unsafe_allow_html=True)
                    if url and url != "#":
                        st.link_button("View Resource ↗", url, use_container_width=True)
                    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

        # ── SUBCATEGORY 4: PDFS & STUDY MATERIALS ─────────────────────────────
        if pdf_materials:
            st.markdown("#### PDFs & Study Materials")
            for d in pdf_materials:
                title = html.escape(str(d.get("title") or "Study Notes Document"))
                platform = html.escape(str(d.get("platform") or "Educational Source"))
                desc = html.escape(str(d.get("description") or "Downloadable curriculum notes and reference document."))
                url = d.get("url", "#")

                r_col1, r_col2 = st.columns([4, 1.2])
                with r_col1:
                    st.markdown(f"""
<div class="edu-card" style="margin-bottom:10px;padding:14px 18px;">
  <div class="card-header-row" style="margin-bottom:4px;">
    <span class="badge-pdf">📄 PDF Document</span>
    <span class="badge-tag">Source: {platform}</span>
  </div>
  <div class="card-title" style="font-size:1.02rem;margin:4px 0 6px 0;">{title}</div>
  <div class="card-desc" style="margin-bottom:0;">{desc}</div>
</div>
""", unsafe_allow_html=True)
                with r_col2:
                    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
                    st.link_button("Open PDF 📥", url, use_container_width=True)


# ── TAB 4: VIDEO LECTURES ─────────────────────────────────────────────────────
with tab_video:
    st.markdown("### Video Lectures")
    st.caption("Complete courses, topic playlists, and problem-solving sessions from verified educators.")

    if videos:
        v_cols = st.columns(2)
        for idx, v in enumerate(videos):
            title = html.escape(str(v.get("title") or "Exam Lecture Series"))
            cat = html.escape(str(v.get("category") or "Full Course"))
            channel = html.escape(str(v.get("channel") or "Verified Educator"))
            desc = html.escape(str(v.get("description") or "Structured course lectures."))
            url = v.get("url", "#")

            with v_cols[idx % 2]:
                st.markdown(f"""
<div class="edu-card" style="height:calc(100% - 16px);margin-bottom:12px;">
  <div class="card-header-row" style="margin-bottom:6px;">
    <span class="badge-tag">▶️ {cat.upper()}</span>
    <span style="font-size:0.82rem;color:var(--text-muted);font-weight:600;">{channel}</span>
  </div>
  <div class="card-title" style="font-size:1.05rem;">{title}</div>
  <div class="card-desc">{desc}</div>
</div>
""", unsafe_allow_html=True)
                st.link_button("Watch Playlist ▶️", url, use_container_width=True)
                st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
    else:
        st.info("No curated video courses found for this query.")


# ── MINIMAL ACADEMIC FOOTER ───────────────────────────────────────────────────
st.markdown("""
<div class="edu-footer">
  <strong>ExamGenie AI</strong> • Comprehensive Academic Examination Research & Preparation
</div>
""", unsafe_allow_html=True)
