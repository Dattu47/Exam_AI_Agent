"""
ExamGenie AI — Official Examination Preparation Platform
Ultra-animated premium UI: Syllabus | Strategy | Material | Videos
"""

import streamlit as st
import datetime
import textwrap
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
# Design System + Animations
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --bg:       #05060C;
    --surface:  #0A0D16;
    --card:     #0F1420;
    --card2:    #141A2E;
    --border:   rgba(255,255,255,0.07);
    --accent:   #C8FF00;
    --accent2:  #5B96F7;
    --accent3:  #FF6B35;
    --accent4:  #B47FFF;
    --text:     #E8ECF4;
    --muted:    #56637A;
    --radius:   14px;
}

html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text);
    font-family: 'Inter', sans-serif;
}
footer, #MainMenu { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Animated mesh background ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 90% 50% at 15% 5%,  rgba(91,150,247,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 70% 60% at 85% 90%, rgba(200,255,0,0.05)  0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50% 50%, rgba(180,127,255,0.03) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
    animation: meshShift 12s ease-in-out infinite alternate;
}
@keyframes meshShift {
    from { opacity: 0.7; }
    to   { opacity: 1.0; }
}

/* ── Scanning line overlay ── */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        rgba(255,255,255,0.012) 0px,
        rgba(255,255,255,0.012) 1px,
        transparent 1px,
        transparent 3px
    );
    pointer-events: none;
    z-index: 0;
    animation: scanPulse 8s linear infinite;
}
@keyframes scanPulse {
    0% { background-position: 0 0; }
    100% { background-position: 0 100vh; }
}

/* ═══════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid rgba(91,150,247,0.12) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem !important; }

.brand {
    font-family: 'Outfit', sans-serif;
    font-size: 1.65rem;
    font-weight: 900;
    background: linear-gradient(135deg, #C8FF00 0%, #7DD800 40%, #5B96F7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.6px;
    margin-bottom: 2px;
}
.brand-sub {
    font-size: 0.65rem;
    color: var(--muted);
    margin-bottom: 1.6rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}
.current-board {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
    background: rgba(200,255,0,0.05);
    border: 1px solid rgba(200,255,0,0.12);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 4px;
}
.board-meta { font-size: 0.66rem; color: var(--muted); margin-bottom: 1.6rem; padding-left: 2px; }

/* Sidebar nav */
div[data-testid="stSidebar"] div.stRadio > label { display: none; }
div[data-testid="stSidebar"] div[role="radiogroup"] {
    display: flex; flex-direction: column; gap: 3px;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex; align-items: center;
    padding: 11px 14px !important;
    border-radius: 11px !important;
    color: var(--muted) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent !important;
    position: relative;
    overflow: hidden;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 0;
    background: linear-gradient(90deg, rgba(200,255,0,0.15), transparent);
    transition: width 0.25s ease;
    border-radius: 11px 0 0 11px;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover::before { width: 100%; }
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    border-color: rgba(200,255,0,0.18) !important;
    color: var(--text) !important;
}

/* ═══════════════════════════════════════════════
   HERO
   ═══════════════════════════════════════════════ */
.hero-wrap {
    text-align: center;
    padding: 1.2rem 0 0.2rem;
    position: relative;
}
.hero-orb {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 700px; height: 220px;
    background: radial-gradient(ellipse, rgba(200,255,0,0.12) 0%, rgba(91,150,247,0.08) 40%, transparent 70%);
    pointer-events: none;
    animation: orbPulse 4s ease-in-out infinite;
    filter: blur(20px);
}
@keyframes orbPulse {
    0%, 100% { transform: translate(-50%,-50%) scale(1);    opacity: 0.8; filter: blur(20px); }
    50%       { transform: translate(-50%,-50%) scale(1.25); opacity: 1.0; filter: blur(25px); }
}
.app-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.8rem;
    font-weight: 900;
    letter-spacing: -1.5px;
    position: relative;
    z-index: 1;
    animation: slideDown 0.65s cubic-bezier(0.22,1,0.36,1) both;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-28px); }
    to   { opacity: 1; transform: translateY(0); }
}
.app-title .g1 {
    background: linear-gradient(135deg, #C8FF00 0%, #8BEB00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.app-sub {
    text-align: center;
    color: var(--muted);
    font-size: 0.9rem;
    margin-bottom: 1.6rem;
    animation: slideDown 0.85s cubic-bezier(0.22,1,0.36,1) both;
    position: relative; z-index: 1;
}
.tagline-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(91,150,247,0.08);
    border: 1px solid rgba(91,150,247,0.2);
    border-radius: 24px;
    padding: 3px 14px;
    font-size: 0.7rem;
    color: var(--accent2);
    font-weight: 600;
    margin-bottom: 12px;
    animation: fadeUp 0.5s ease both;
    letter-spacing: 0.05em;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ═══════════════════════════════════════════════
   SEARCH
   ═══════════════════════════════════════════════ */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1.5px solid rgba(255,255,255,0.09) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-size: 1rem !important;
    padding: 14px 22px !important;
    transition: all 0.28s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 15px rgba(200,255,0,0.25), inset 0 0 10px rgba(200,255,0,0.1) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--muted) !important; }

div.stButton > button {
    background: linear-gradient(135deg, #C8FF00 0%, #A2E000 100%) !important;
    color: #000 !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 14px !important;
    height: 54px !important;
    font-size: 0.95rem !important;
    transition: all 0.22s ease !important;
    box-shadow: 0 4px 20px rgba(200,255,0,0.25), 0 1px 0 rgba(255,255,255,0.2) inset !important;
    letter-spacing: 0.01em !important;
    animation: btnBreath 3s infinite alternate;
}
@keyframes btnBreath {
    from { box-shadow: 0 4px 20px rgba(200,255,0,0.25), 0 1px 0 rgba(255,255,255,0.2) inset !important; }
    to { box-shadow: 0 4px 35px rgba(200,255,0,0.45), 0 1px 0 rgba(255,255,255,0.4) inset !important; }
}
div.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 10px 40px rgba(200,255,0,0.5) !important;
}
div.stButton > button:active { transform: translateY(0) scale(0.99) !important; }

.stLinkButton a {
    background: var(--card2) !important;
    border: 1px solid rgba(91,150,247,0.25) !important;
    border-radius: 10px !important;
    color: var(--accent2) !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}
.stLinkButton a:hover {
    background: rgba(91,150,247,0.08) !important;
    border-color: rgba(91,150,247,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ═══════════════════════════════════════════════
   CONTAINERS
   ═══════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.1rem 1.4rem !important;
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    border-color: rgba(255,255,255,0.11) !important;
    box-shadow: 0 6px 28px rgba(0,0,0,0.45) !important;
}

/* ═══════════════════════════════════════════════
   SECTION TITLES
   ═══════════════════════════════════════════════ */
.sec-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 4px;
    letter-spacing: -0.4px;
}
.sec-note {
    font-size: 0.81rem;
    color: var(--muted);
    margin-bottom: 1.4rem;
    line-height: 1.55;
}
.year-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(200,255,0,0.07);
    border: 1px solid rgba(200,255,0,0.2);
    color: var(--accent);
    border-radius: 24px;
    padding: 4px 14px;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
    animation: popIn 0.5s cubic-bezier(0.34,1.56,0.64,1) both 0.1s;
}
@keyframes popIn {
    from { opacity: 0; transform: scale(0.75); }
    to   { opacity: 1; transform: scale(1); }
}

/* ═══════════════════════════════════════════════
   SYLLABUS CARDS — topic-only, accordion style
   ═══════════════════════════════════════════════ */
.syl-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-bottom: 8px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    transition: all 0.22s ease;
    animation: rowIn 0.35s cubic-bezier(0.22,1,0.36,1) both;
    cursor: default;
    position: relative;
    overflow: hidden;
}
.syl-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, rgba(200,255,0,0.0) 0%, rgba(200,255,0,0.025) 100%);
    opacity: 0;
    transition: opacity 0.25s;
    pointer-events: none;
}
.syl-card:hover { 
    border-color: rgba(200,255,0,0.5); 
    transform: translateX(6px) scale(1.01); 
    box-shadow: -4px 0 15px rgba(200,255,0,0.2), inset 0 0 10px rgba(200,255,0,0.08); 
}
.syl-card:hover::after { opacity: 1; }
@keyframes rowIn {
    from { opacity: 0; transform: translateX(-14px); }
    to   { opacity: 1; transform: translateX(0); }
}
.syl-num {
    min-width: 28px;
    height: 28px;
    background: linear-gradient(135deg, rgba(200,255,0,0.18), rgba(91,150,247,0.12));
    border: 1px solid rgba(200,255,0,0.25);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--accent);
    flex-shrink: 0;
    margin-top: 1px;
}
.syl-body { flex: 1; }
.syl-topic-name {
    font-size: 0.97rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.4;
}
.syl-subs-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.syl-chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: var(--muted);
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 0.74rem;
    font-weight: 500;
    transition: all 0.18s;
}
.syl-chip:hover {
    background: rgba(200,255,0,0.07);
    border-color: rgba(200,255,0,0.28);
    color: var(--accent);
}
.chip-hot {
    background: rgba(255,107,53,0.1);
    border: 1px solid rgba(255,107,53,0.28);
    color: #FF8C5A;
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 0.74rem;
    font-weight: 600;
    display: inline-block;
    margin: 3px;
    transition: all 0.18s;
}
.chip-hot:hover {
    background: rgba(255,107,53,0.18);
    transform: translateY(-1px);
}

/* ═══════════════════════════════════════════════
   PREPARATION STRATEGY — Phase timeline
   ═══════════════════════════════════════════════ */
.phase-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    background: var(--card2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 2px;
    position: relative;
    overflow: hidden;
    animation: slideRight 0.45s cubic-bezier(0.22,1,0.36,1) both;
}
@keyframes slideRight {
    from { opacity: 0; transform: translateX(-20px); }
    to   { opacity: 1; transform: translateX(0); }
}
.phase-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
}
.phase-1 { background: rgba(200,255,0,0.12);  border: 1px solid rgba(200,255,0,0.3);  color: #C8FF00; }
.phase-2 { background: rgba(91,150,247,0.12); border: 1px solid rgba(91,150,247,0.3); color: #7AAEFF; }
.phase-3 { background: rgba(180,127,255,0.12);border: 1px solid rgba(180,127,255,0.3);color: #C49FFF; }
.phase-4 { background: rgba(255,107,53,0.12); border: 1px solid rgba(255,107,53,0.3); color: #FF8C5A; }

.phase-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--text);
}
.phase-meta {
    font-size: 0.75rem;
    color: var(--muted);
    margin-left: auto;
    white-space: nowrap;
}

.topic-row {
    display: flex;
    align-items: flex-start;
    gap: 0;
    margin-bottom: 2px;
}
.topic-connector {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 42px;
    flex-shrink: 0;
    padding-top: 18px;
}
.tc-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--accent);
    border: 2px solid rgba(200,255,0,0.4);
    box-shadow: 0 0 10px rgba(200,255,0,0.35);
    flex-shrink: 0;
    animation: dotPulse 2.5s ease-in-out infinite;
}
@keyframes dotPulse {
    0%, 100% { box-shadow: 0 0 6px rgba(200,255,0,0.3); }
    50%       { box-shadow: 0 0 16px rgba(200,255,0,0.6); }
}
.tc-line {
    width: 2px;
    min-height: 36px;
    flex: 1;
    background: linear-gradient(180deg, rgba(200,255,0,0.2) 0%, rgba(200,255,0,0.03) 100%);
    margin-top: 4px;
}
.topic-card {
    flex: 1;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 2px;
    transition: all 0.22s ease;
    animation: cardFade 0.4s ease both;
}
.topic-card:hover {
    border-color: rgba(200,255,0,0.4);
    box-shadow: -3px 0 20px rgba(200,255,0,0.15), 0 4px 24px rgba(200,255,0,0.05);
    transform: translateX(4px) scale(1.01);
}
@keyframes cardFade {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.topic-row-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 5px;
}
.topic-name-str {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text);
    flex: 1;
}
.dur-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(91,150,247,0.08);
    border: 1px solid rgba(91,150,247,0.22);
    color: #7AAEFF;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 700;
    white-space: nowrap;
    font-family: 'JetBrains Mono', monospace;
}
.topic-subs-str {
    font-size: 0.77rem;
    color: var(--muted);
    line-height: 1.6;
    margin-bottom: 6px;
}
.tip-row {
    display: flex;
    align-items: flex-start;
    gap: 7px;
    background: rgba(200,255,0,0.03);
    border-left: 2px solid rgba(200,255,0,0.3);
    border-radius: 0 7px 7px 0;
    padding: 7px 12px;
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.55;
}
.tip-row span.tip-icon { color: var(--accent); font-size: 0.82rem; flex-shrink: 0; }

/* ═══════════════════════════════════════════════
   MATERIAL + VIDEO CARDS
   ═══════════════════════════════════════════════ */
.mat-title { font-size: 0.92rem; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.mat-badge {
    font-size: 0.67rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    font-family: 'JetBrains Mono', monospace;
}
.badge-pdf {
    background: rgba(255,107,53,0.1);
    border: 1px solid rgba(255,107,53,0.28);
    color: #FF8C5A;
}
.badge-web {
    background: rgba(91,150,247,0.08);
    border: 1px solid rgba(91,150,247,0.22);
    color: var(--accent2);
}

/* ═══════════════════════════════════════════════
   STATS ROW
   ═══════════════════════════════════════════════ */
.stats-row {
    display: flex;
    gap: 10px;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    animation: fadeUp 0.55s ease both;
}
.stat-box {
    flex: 1;
    min-width: 110px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 14px 16px;
    text-align: center;
    transition: all 0.22s ease;
    position: relative;
    overflow: hidden;
}
.stat-box::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transform: scaleX(0);
    transition: transform 0.3s ease;
    transform-origin: left;
}
.stat-box:hover::before { transform: scaleX(1); }
.stat-box:hover { border-color: rgba(200,255,0,0.2); transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.4); }
.stat-val {
    font-family: 'Outfit', sans-serif;
    font-size: 1.7rem;
    font-weight: 900;
    color: var(--accent);
    line-height: 1;
    animation: countUp 0.8s ease both;
    text-shadow: 0 0 10px rgba(200,255,0,0.4);
}
@keyframes countUp {
    from { opacity: 0; transform: translateY(12px) scale(0.8); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.stat-label {
    font-size: 0.68rem;
    color: var(--muted);
    margin-top: 5px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}

/* ═══════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════ */
.empty-hero {
    text-align: center;
    padding: 4.5rem 2rem;
    animation: fadeUp 0.7s ease;
    position: relative;
}
.empty-ring {
    position: relative;
    display: inline-block;
    margin-bottom: 1.5rem;
}
.empty-icon {
    font-size: 4.5rem;
    animation: floatIcon 3.5s ease-in-out infinite;
    display: block;
    position: relative;
    z-index: 1;
}
@keyframes floatIcon {
    0%, 100% { transform: translateY(0) rotate(-3deg); }
    50%       { transform: translateY(-14px) rotate(3deg); }
}
.ring-glow {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%,-50%);
    width: 120px; height: 120px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(200,255,0,0.12) 0%, transparent 70%);
    animation: ringPulse 3.5s ease-in-out infinite;
}
@keyframes ringPulse {
    0%, 100% { transform: translate(-50%,-50%) scale(1);   opacity: 0.6; }
    50%       { transform: translate(-50%,-50%) scale(1.4); opacity: 1; }
}
.empty-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.9rem;
    font-weight: 900;
    color: var(--text);
    margin-bottom: 0.55rem;
    letter-spacing: -0.5px;
}
.empty-sub {
    font-size: 0.88rem;
    color: var(--muted);
    max-width: 460px;
    margin: 0 auto 2.2rem;
    line-height: 1.65;
}
.feature-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-top: 1.2rem;
}
.feature-pill {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 7px 16px;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--muted);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.22s;
    animation: pillIn 0.5s ease both;
}
@keyframes pillIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.feature-pill:hover {
    border-color: rgba(200,255,0,0.3);
    color: var(--accent);
    background: rgba(200,255,0,0.04);
    transform: translateY(-2px);
}

/* ── Separator ── */
.sep { border: none; border-top: 1px solid var(--border); margin: 1.8rem 0; }

/* ── Expander ── */
.stExpander {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--card) !important;
    margin-bottom: 8px !important;
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

            status.update(label="🔍 Scanning official exam portals and databases…")
            raw = agent.search_agent.find_resources(exam_name)

            status.update(label="📄 Extracting syllabus from authoritative sources…")
            s_urls = [(r.url if hasattr(r, "url") else r.get("url", ""))
                      for r in raw.get("syllabus", [])[:12]]
            pages, pdfs = agent.scraping_agent.scrape_sources(s_urls, max_pages=10)

            status.update(label="🧠 Building accurate, structured syllabus…")
            syllabus, topics, chunks = agent.processing_agent.extract_and_process(
                exam_name, pages, s_urls, raw.get("exam_pattern", [])
            )

            status.update(label="📋 Generating personalised preparation strategy…")
            plan = agent.study_agent.build_plan(exam_name, syllabus, topics, weeks=4)

            status.update(label="🎯 Compiling resources, papers, and videos…")
            final = agent.response_agent.format_final_response(
                exam_name,
                raw.get("exam_info", []),
                raw.get("syllabus", []),
                raw.get("previous_papers", []),
                raw.get("study_resources", []),
                raw.get("youtube_lectures", []),
                syllabus, topics, plan, pdfs, chunks,
                model_papers_raw=raw.get("model_papers", []),
            )

            st.session_state.updated_at = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            status.update(label="✅ Your preparation guide is ready!", state="complete", expanded=False)
            return final

        except Exception as e:
            status.update(label="Something went wrong.", state="error", expanded=True)
            st.error(str(e))
            logger.exception("[app] Pipeline failed: %s", e)
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Hero
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-orb"></div>
    <div style="margin-bottom:8px;">
        <span class="tagline-pill">✦ AI-Powered Exam Preparation · {CURRENT_YEAR}</span>
    </div>
    <div class="app-title">🎯 <span class="g1">ExamGenie</span> AI</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    f'<div class="app-sub">Complete preparation guide — official syllabus, phase-wise strategy, PYQ papers &amp; curated video lectures.</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────────────────────
sc1, sc2 = st.columns([5, 1])
with sc1:
    exam_q = st.text_input(
        "exam_search",
        value=st.session_state.last_exam,
        placeholder="Type any exam: JEE Main, UPSC CSE, GATE CSE, TCS NQT, IBPS PO, CAT, NEET…",
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
    st.markdown('<div class="brand-sub">AI Exam Preparation</div>', unsafe_allow_html=True)

    curr = st.session_state.last_exam or "No exam selected"
    st.markdown(f'<div class="current-board">📌 {curr}</div>', unsafe_allow_html=True)
    if st.session_state.updated_at:
        st.markdown(f'<div class="board-meta">Last updated: {st.session_state.updated_at}</div>', unsafe_allow_html=True)

    st.markdown("---")
    nav = st.radio(
        "Navigate",
        options=[
            "📚 Syllabus",
            "🗓️ Preparation Strategy",
            "📖 Study Material",
            "▶️ Video Lectures",
        ],
        index=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Empty State
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.results:
    st.markdown("""
    <div class="empty-hero">
        <div class="empty-ring">
            <div class="ring-glow"></div>
            <span class="empty-icon">🎯</span>
        </div>
        <div class="empty-title">Ready when you are.</div>
        <div class="empty-sub">Search any competitive, government, or placement exam above. Get a complete, AI-curated preparation plan in under 60 seconds.</div>
        <div class="feature-row">
            <span class="feature-pill">📋 Official Syllabus</span>
            <span class="feature-pill">🗓️ Phase-wise Strategy</span>
            <span class="feature-pill">📄 Previous Year Papers</span>
            <span class="feature-pill">📚 Books &amp; Resources</span>
            <span class="feature-pill">▶️ Video Lectures</span>
            <span class="feature-pill">🔥 High-Weightage Topics</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────
data      = st.session_state.results
exam_name = st.session_state.last_exam
syl           = data.get("syllabus") or []
topics        = data.get("important_topics") or []
plan          = data.get("study_plan") or []
papers        = data.get("previous_papers") or []
model_papers  = data.get("model_papers") or []
resources     = data.get("resources") or []
videos        = data.get("youtube_lectures") or []

year_label = f"Academic Year {CURRENT_YEAR}"

# Stats bar
n_topics = len(syl)
n_steps  = len(plan)
n_papers = len(papers)
n_videos = len(videos)

st.markdown(f"""
<div class="stats-row">
    <div class="stat-box">
        <div class="stat-val">{n_topics}</div>
        <div class="stat-label">Topics</div>
    </div>
    <div class="stat-box">
        <div class="stat-val">{n_steps}</div>
        <div class="stat-label">Plan Steps</div>
    </div>
    <div class="stat-box">
        <div class="stat-val">{n_papers}</div>
        <div class="stat-label">PYQ Papers</div>
    </div>
    <div class="stat-box">
        <div class="stat-val">{n_videos}</div>
        <div class="stat-label">Videos</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — SYLLABUS
# Topic-only clean accordion with subtopic chips
# ─────────────────────────────────────────────────────────────────────────────
if nav == "📚 Syllabus":
    st.markdown(f'<div class="sec-title">{exam_name} — Official Syllabus</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-note">Subject-wise topic breakdown for {CURRENT_YEAR}. Click any topic to expand subtopics.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    if syl:
        for i, item in enumerate(syl, start=1):
            topic = (item.get("topic") if isinstance(item, dict) else str(item)) or ""
            subs  = (item.get("subtopics", []) if isinstance(item, dict) else []) or []
            # Filter out garbage subtopics (too long, URLs, or numbers-only)
            clean_subs = [
                s for s in subs
                if isinstance(s, str) and 2 < len(s.strip()) < 120
                and not s.strip().startswith("http")
            ][:18]

            with st.expander(f"**{topic}**", expanded=False):
                if clean_subs:
                    chips = "".join([f'<span class="syl-chip">{s}</span>' for s in clean_subs])
                    st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:6px;padding:4px 0;">{chips}</div>', unsafe_allow_html=True)
                else:
                    st.caption("Core topic — refer to the official syllabus document for details.")
    else:
        st.warning("Syllabus data not found. Try a more specific exam name or re-search.")

    # High-weightage chips
    if topics:
        st.markdown("<hr class='sep'>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title" style="font-size:1.1rem;">🔥 High-Weightage Topics</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-note">These topics consistently carry the most marks in this exam.</div>', unsafe_allow_html=True)
        chips_html = "".join([f'<span class="chip-hot">{t}</span>' for t in topics[:20]])
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{chips_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — PREPARATION STRATEGY
# Phase-wise timeline timetable
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "🗓️ Preparation Strategy":
    st.markdown(f'<div class="sec-title">Ultimate Preparation Strategy — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-note">A phase-wise, sequenced study roadmap built from your syllabus. '
        'Each topic is ordered from foundational to advanced with time estimates and expert tips.</div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    if plan:
        # Group plan items by phase
        phase_map: dict = {}
        for item in plan:
            phase = str(item.get("phase", "Phase 1"))
            phase_map.setdefault(phase, []).append(item)

        # Phase color classes
        phase_styles = {
            0: ("phase-1", "Phase 1 — Foundations"),
            1: ("phase-2", "Phase 2 — Core Concepts"),
            2: ("phase-3", "Phase 3 — Advanced Topics"),
            3: ("phase-4", "Phase 4 — Revision & Mocks"),
        }

        phases = list(phase_map.keys())
        for pidx, phase_key in enumerate(phases):
            style_cls, default_label = phase_styles.get(pidx % 4, ("phase-1", f"Phase {pidx+1}"))
            items = phase_map[phase_key]
            total_dur = len(items)

            # Phase header
            phase_display = phase_key if phase_key.strip().lower().startswith("phase") else default_label
            phase_html = textwrap.dedent(f"""
            <div class="phase-header">
                <span class="phase-badge {style_cls}">{phase_display}</span>
                <span class="phase-name">{phase_display.split('—')[-1].strip() if '—' in phase_display else phase_display}</span>
                <span class="phase-meta">{total_dur} topic{"s" if total_dur != 1 else ""}</span>
            </div>
            """)
            st.markdown(phase_html, unsafe_allow_html=True)

            # Timeline rows
            for j, item in enumerate(items):
                order = item.get("order", j + 1)
                topic = item.get("topic", "")
                dur   = item.get("duration", "2 Hours")
                subs  = item.get("subtopics", "") or ""
                tip   = item.get("tip", "") or ""
                is_last = (j == len(items) - 1)

                subs_html = f'<div class="topic-subs-str">{subs}</div>' if subs else ""
                tip_html  = (f'<div class="tip-row"><span class="tip-icon">💡</span>{tip}</div>'
                             if tip else "")

                html_block = (
                    '<div class="topic-row">'
                    '<div class="topic-connector">'
                    '<div class="tc-dot"></div>'
                    + ("" if is_last else '<div class="tc-line"></div>') +
                    '</div>'
                    '<div class="topic-card">'
                    '<div class="topic-row-header">'
                    f'<span class="topic-name-str">{order}. {topic}</span>'
                    f'<span class="dur-pill">⏱ {dur}</span>'
                    '</div>'
                    f'{subs_html}'
                    f'{tip_html}'
                    '</div></div>'
                )
                st.markdown(html_block, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

    else:
        # Fallback: if no phase data, render flat list
        if plan:
            for item in plan:
                order = item.get("order", "?")
                topic = item.get("topic", "Topic")
                dur   = item.get("duration", "N/A")
                subs  = item.get("subtopics", "") or ""
                tip   = item.get("tip", "") or ""
                subs_html = "<div class='topic-subs-str'>" + subs + "</div>" if subs else ""
                tip_html  = "<div class='tip-row'><span class='tip-icon'>💡</span>" + tip + "</div>" if tip else ""
                
                html_block = (
                    '<div class="topic-row">'
                    '<div class="topic-connector">'
                    '<div class="tc-dot"></div>'
                    '<div class="tc-line"></div>'
                    '</div>'
                    '<div class="topic-card">'
                    '<div class="topic-row-header">'
                    f'<span class="topic-name-str">{order}. {topic}</span>'
                    f'<span class="dur-pill">⏱ {dur}</span>'
                    '</div>'
                    f'{subs_html}'
                    f'{tip_html}'
                    '</div></div>'
                )
                st.markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("Strategy not generated. Please search again.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — STUDY MATERIAL
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "📖 Study Material":
    st.markdown(f'<div class="sec-title">Study Material — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-note">Previous year papers (with year &amp; stage), mock tests, recommended books, and free resources.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="year-badge">📅 {year_label}</div>', unsafe_allow_html=True)

    # ── PYQs with year + stage badges ────────────────────────────────────────
    st.markdown("#### 📄 Previous Year Question Papers (PYQs)")
    if papers:
        for p in papers:
            url        = p.get("url", "#")
            title      = p.get("title", "Question Paper")
            ptype      = p.get("type", "link")
            pyear      = p.get("year", "")
            stage      = p.get("stage", "")
            badge_class = "badge-pdf" if ptype == "pdf" else "badge-web"
            badge_label = "📄 PDF" if ptype == "pdf" else "🔗 Web"
            # Year badge HTML
            year_tag  = f'<span class="mat-badge" style="background:rgba(200,255,0,0.08);border:1px solid rgba(200,255,0,0.25);color:#C8FF00;margin-left:6px;">📅 {pyear}</span>' if pyear and pyear != "Unknown" else ""
            stage_tag = f'<span class="mat-badge" style="background:rgba(91,150,247,0.08);border:1px solid rgba(91,150,247,0.25);color:#7AAEFF;margin-left:6px;">{stage}</span>' if stage and stage != "General" else ""
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(
                        f'<div class="mat-title">{title}</div>'
                        f'<span class="mat-badge {badge_class}">{badge_label}</span>'
                        f'{year_tag}{stage_tag}',
                        unsafe_allow_html=True
                    )
                with c2:
                    st.link_button("Open →", url, use_container_width=True)
    else:
        st.info("No question papers found. Try searching with the official exam name.")

    st.markdown("<hr class='sep'>", unsafe_allow_html=True)

    # ── Model Papers / Mock Tests ─────────────────────────────────────────────
    st.markdown("#### 🧪 Model Papers & Mock Tests")
    if model_papers:
        for m in model_papers:
            url   = m.get("url", "#")
            title = m.get("title", "Mock Test")
            mtype = m.get("type", "full-length").title()
            src   = m.get("source", "")
            desc  = m.get("description", "")
            diff  = m.get("difficulty", "")
            type_tag = f'<span class="mat-badge badge-web">🧪 {mtype}</span>'
            diff_tag = ""
            if diff:
                diff_color = {"Easy": "rgba(200,255,0,0.08)", "Medium": "rgba(91,150,247,0.08)", "Hard": "rgba(255,107,53,0.08)"}.get(diff, "rgba(255,255,255,0.05)")
                diff_border = {"Easy": "rgba(200,255,0,0.25)", "Medium": "rgba(91,150,247,0.25)", "Hard": "rgba(255,107,53,0.25)"}.get(diff, "rgba(255,255,255,0.1)")
                diff_text   = {"Easy": "#C8FF00", "Medium": "#7AAEFF", "Hard": "#FF8C5A"}.get(diff, "#888")
                diff_tag = f'<span class="mat-badge" style="background:{diff_color};border:1px solid {diff_border};color:{diff_text};margin-left:6px;">{diff}</span>'
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    src_text = f" · {src}" if src else ""
                    st.markdown(
                        f'<div class="mat-title">{title}{src_text}</div>'
                        f'{type_tag}{diff_tag}'
                        + (f'<div style="font-size:0.78rem;color:var(--muted);margin-top:5px;">{desc}</div>' if desc else ""),
                        unsafe_allow_html=True
                    )
                with c2:
                    st.link_button("Open →", url, use_container_width=True)
    else:
        st.info("No mock tests found. Try re-searching with the full exam name.")

    st.markdown("<hr class='sep'>", unsafe_allow_html=True)

    # ── Books & Online Resources ──────────────────────────────────────────────
    st.markdown("#### 📚 Books & Online Resources")
    if resources:
        for r in resources:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f'<div class="mat-title">{r.get("title", "Resource")}</div>', unsafe_allow_html=True)
                with c2:
                    st.link_button("Open →", r.get("url", "#"), use_container_width=True)
    else:
        st.info("No study resources found. Try a more specific exam name.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — VIDEO LECTURES
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "▶️ Video Lectures":
    st.markdown(f'<div class="sec-title">Video Lectures — {exam_name}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-note">Curated {CURRENT_YEAR} playlists and full-course video lectures.</div>',
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
                    st.markdown(f'<div style="font-size:0.88rem;font-weight:600;color:var(--text);margin-bottom:10px;">{title}</div>',
                                unsafe_allow_html=True)
                    if "youtube.com" in url or "youtu.be" in url:
                        try:
                            st.video(url)
                        except Exception:
                            pass
                    st.link_button("▶️ Watch on YouTube", url, use_container_width=True)
    else:
        st.info("No video lectures found. Try searching with the exact exam name.")


st.markdown("<br><br><br>", unsafe_allow_html=True)
