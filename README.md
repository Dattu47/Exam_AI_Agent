# 🎯 ExamGenie Hub — AI-Powered Resource Aggregator

An intelligent, multi-agent system that acts as a **high-precision resource aggregator** for Indian competitive exams. Instead of generating generic study plans, ExamGenie Hub discovers and validates **official websites**, **syllabus PDFs**, **PYQ archives**, **curated YouTube playlists**, and **verified educational platform links** — all filtered by Gemini 1.5 Flash to eliminate blog spam and irrelevant content.

> **The Anti-Spam Tool for Exam Prep.** Most students waste hours on SEO-optimized blogs that copy-paste data. ExamGenie Hub goes directly to the source.

---

## ✨ Key Features

### 🏛️ Official Fact-Checker (Authority Tab)
- **Smart URL Discovery**: Automatically tries `[exam].gov.in`, `[exam].nic.in`, `[exam].in` heuristics before falling back to search results.
- **Domain Verification**: Adds a `✅ Verified .gov / .nic` badge when the domain is a confirmed government portal — builds immediate trust.
- **Deep PDF Linking**: Finds and links directly to the official syllabus PDF hosted on government servers, bypassing ads.
- **Quick Info Card**: Gemini 1.5 Flash synthesizes scraped content + its own knowledge to extract:
  - Conducting Body
  - Exam Frequency
  - Registration Dates (with intelligent fallback like "Usually August–October")
  - About Exam (2-3 sentence summary)
- **Status Ticker**: Detects recent notifications or new PDFs on the official portal and shows a pulsating `🚨 NEW UPDATE FOUND!` alert.
- **Safety Net**: If no official site is found with high confidence, provides a structured Google search fallback link instead of hallucinating a URL.

### 📄 Archive Tab (PYQ Papers)
- Searches across `testbook.com`, `examrace.com`, `careers360.com`, `mrunal.org`, and official portals.
- Validates every URL with HTTP checks before showing it.
- Gemini 1.5 Flash filters out irrelevant results — only authentic PYQ papers for the searched exam are shown.
- PDF links are detected and badged separately from web links.

### 🎥 Video Library Tab
- **Exact Phrase Search**: Wraps the exam name in quotes (`"GATE CSE"`) to force search engines to return only directly relevant results.
- **Notable Channel Targeting**: Searches across Mrunal Patel, Study IQ IAS, Neso Academy, Wifistudy, GATE Smashers, Drishti IAS, Physics Wallah, and Unacademy.
- **YouTube URL Validation**: Filters out all non-YouTube URLs before processing.
- **Strict LLM Categorization**: Gemini categorizes each playlist as Beginner/Intermediate/Advanced or by Topic (e.g., "GS Paper 1", "Quantitative Aptitude").

### 📚 Library Tab
- **Verified Educational Platforms**: Searches Shiksha, Careers360, Testbook, Adda247, Vision IAS, NPTEL, MADE EASY, GateOverflow, Oliveboard, PW, and Unacademy.
- **Government Sources**: Includes SarkariResult, FreeJobAlert, Jagran Josh, NCERT, and PIB.
- Gemini performs a final relevance filter to ensure all shown links are specific to the searched exam.

---

## 🏗️ Architecture

```
User Input (Exam Name)
        │
        ▼
  ResearchAgent (Orchestrator)
  ├── Supabase Cache Check → Return instantly if cached
  │
  ├── AuthorityService
  │   ├── Heuristic URL probing (.gov.in, .nic.in, .in)
  │   ├── WebSearchTool (DDG + Google fallback)
  │   ├── BeautifulSoup Scraper (Official site + Fallback portal)
  │   └── Gemini 1.5 Flash → Fact synthesis + Info Card
  │
  ├── SearchAgent → PYQ search across 6 targeted buckets
  │   └── Gemini 1.5 Flash → PYQ relevance filter
  │
  ├── YoutubeAgent
  │   ├── Exact phrase search + Notable channel targeting
  │   ├── YouTube URL validation filter
  │   └── Gemini 1.5 Flash → Category + strict relevance filter
  │
  └── MaterialAggregator
      ├── EdTech portal search (Shiksha, Careers360, Testbook, etc.)
      ├── Government source search (SarkariResult, NCERT, PIB)
      └── Gemini 1.5 Flash → Final relevance filter
              │
              ▼
      Supabase Cache Save + Return to UI
```

---

## 🖥️ UI Overview

The app is built with **Streamlit** and features a futuristic dark-mode design (`#0A0F1A` base, `#00FFA3` neon accent) with:
- Animated hover cards with glowing borders
- Pulsating update alert badges
- Government domain verification checkmarks
- 4 functional tabs: **Authority** | **Archive** | **Video Library** | **Library**

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Frontend** | Streamlit |
| **LLM** | Google Gemini 1.5 Flash (via `langchain-google-genai`) |
| **Database / Cache** | Supabase (PostgreSQL via `supabase-py`) |
| **Web Search** | DuckDuckGo (`ddgs`) + Google fallback |
| **Scraping** | `requests` + `BeautifulSoup4` |
| **AI Orchestration** | LangChain (`langchain-core`) |

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- **Python 3.10+**: [Download here](https://www.python.org/downloads/)
- **Supabase**: Create a free project at [supabase.com](https://supabase.com/)
- **Gemini API Key**: Get a free key from [Google AI Studio](https://aistudio.google.com/)

### 2. Database Setup
Run the included `supabase_setup.sql` in your Supabase SQL Editor to create the required tables (`user_queries`, `exam_resources`, `study_plans`).

### 3. Environment Variables
Create `.streamlit/secrets.toml` in the project root:
```toml
SUPABASE_URL = "your-supabase-project-url"
SUPABASE_KEY = "your-supabase-anon-or-service-key"
GEMINI_API_KEY = "your-gemini-api-key"
```

### 4. Install Dependencies
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Run the Application
```bash
streamlit run app.py
```
Navigate to `http://localhost:8501` and search any exam name.

---

## 📁 Project Structure

```
exam-ai-agent/
├── app.py                              # Streamlit UI (4-tab dashboard)
├── requirements.txt
├── exam_ai_agent/
│   ├── agents/
│   │   ├── research_agent.py           # Main orchestrator
│   │   ├── search_agent.py             # Web search coordination
│   │   ├── scraping_agent.py           # HTML/PDF scraping
│   │   ├── youtube_agent.py            # YouTube playlist discovery & categorization
│   │   └── material_aggregator.py      # EdTech & government source aggregation
│   ├── services/
│   │   ├── authority_service.py        # Official Fact-Checker (URL probe + Gemini synthesis)
│   │   ├── papers_service.py           # PYQ paper processing
│   │   └── supabase_service.py         # Database caching layer
│   └── tools/
│       ├── web_search.py               # DDG + Google dual-search with retry & dedup
│       └── pdf_downloader.py           # PDF link extraction
```

---

## 🔧 Customization

| Goal | File to Edit |
|---|---|
| Change which EdTech portals are searched | `exam_ai_agent/agents/material_aggregator.py` |
| Change which YouTube channels are targeted | `exam_ai_agent/agents/youtube_agent.py` |
| Modify what Gemini extracts for the Info Card | `exam_ai_agent/services/authority_service.py` |
| Add new search query buckets | `exam_ai_agent/tools/web_search.py` |
| Update UI layout or styling | `app.py` |

---

## 📝 Supported Exams (Examples)

Works with any competitive exam in India including:

`UPSC CSE` · `GATE CSE` · `GATE ECE` · `IBPS PO` · `IBPS Clerk` · `SSC CGL` · `SSC CHSL` · `RRB NTPC` · `NEET` · `JEE Main` · `CAT` · `UPPSC RO ARO` · `BPSC` · `MPPSC` · `State PSC exams`

---

## ⚠️ Disclaimer

This tool aggregates publicly available links from the web and uses AI to classify relevance. Always cross-verify critical information (dates, eligibility, fees) directly on the official exam portal before taking action.
