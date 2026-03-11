# 🤖 AI Exam Research Assistant

An intelligent, multi-agent orchestration system designed to automate competitive exam preparation. Upon receiving an exam name (e.g., "GATE CSE" or "UPSC Prelims"), the system leverages specialized AI sub-agents to scour the web, extract official syllabus hierarchies, compile deduplicated previous year question papers, locate high-yield YouTube video lectures, and ultimately generate a structured, customized 4-week day-by-day study plan using local LLMs.

---

## 🌟 Key Features

*   **Multi-Agent Architecture:** A modular system orchestrated by a central `ResearchAgent`, delegating tasks to distinct experts:
    *   🔍 **Search Agent:** Autonomously formulates precise search queries for syllabi, past papers, YouTube playlists, and recommended books using DuckDuckGo.
    *   🕷️ **Scraping Agent:** Interrogates target URLs (processing PDFs and HTML) to uncover deep links and scrape raw content.
    *   🧠 **Processing Agent:** Cleans, extracts, shapes, and deduplicates the raw scraped content into structured outputs utilizing specialized Regex and HTML parsing strategies.
    *   📅 **Study Plan Agent:** Uses local LLMs (Ollama/Llama2) to generate a rigorous, syllabus-tailored 4-week study plan with daily breakdowns and actionable tips.
    *   🏗️ **Response Agent:** Combines all processed data into a strict, unified JSON contract for the frontend, incorporating a final absolute base-URL deduplication safety net.
*   **Supabase Database Caching & Analytics:** Implements edge-caching using Supabase. The orchestrator checks Supabase first; if an exam has been queried previously, it returns the cached strategy in milliseconds.
*   **Vector Database Fallback (FAISS):** Periodically chunks scraped raw text to populate a FAISS Vector database for future RAG (Retrieval-Augmented Generation) enhancements.
*   **Strict Deduplication:** Ensures 100% unique resources by stripping tracking queries, fragment hashes, and aggressive domain matching across PDFs, YouTube URLs, and reference links.
*   **Hierarchical Syllabus Extraction:** Transforms flat scraped topics into nested `Topic -> Subtopics` dictionary structures for interactive consumption.
*   **Streamlit Interactive UI:** A clean, modern tabbed interface displaying task-oriented study plans, dynamic syllabus progress trackers, and embedded YouTube videos natively.

---

## 🏗️ Architecture Flow

1.  **User Input:** The user types an exam name (e.g., "UPPSC RO ARO") into the Streamlit Web Application (`app.py`).
2.  **Orchestrator Interception:** `ResearchAgent` queries `SupabaseService`. If a cached version exists, it bypasses computation entirely.
3.  **Search & Strategy:** `SearchAgent` dispatches ~10 concurrent queries to isolate official sites, PDF repos, and YouTube channels. 
4.  **Deep Scraping:** URLs are passed to `ScrapingAgent` to extract text footprints. Hidden PDFs discovered within HTML pages are recursively added to the stack.
5.  **Data Processing:** `ProcessingAgent` utilizes `SyllabusService` and `PapersService` to cleanse the data. Duplicate links are stripped at the base-domain level. Text is forced into hierarchical dictionaries.
6.  **LLM Generation:** The 4-week study plan is constructed via `StudyPlanAgent`, piping the filtered Syllabus and Important Topics into a strict JSON-formatted prompt via Langchain to a local Ollama instance.
7.  **Final Formatting & Persistence:** `ResponseAgent` combines all segments into a monolithic dictionary. The orchestrator pushes this final output to Supabase (`exam_resources` and `study_plans` tables) for subsequent caches and sends it back to the Streamlit UI. 

---

## 💻 Tech Stack

*   **Language:** Python 3.10+
*   **Frontend:** Streamlit (`streamlit`)
*   **Database / Backend:** Supabase (PostgreSQL via `supabase-py`)
*   **AI Orchestration:** LangChain (`langchain-core`, `langchain-ollama`)
*   **Local LLM Server:** Ollama (Llama2/Llama3 for local inference)
*   **Web Scrapers/Parsers:** `beautifulsoup4`, `requests`, `duckduckgo-search` (ddgs), `PyPDF2`
*   **Memory / VDB:** FAISS (`faiss-cpu`) 

---

## 🚀 Setup & Installation

### 1. Pre-requisites
*   **Python:** Install [Python 3.10+](https://www.python.org/downloads/)
*   **Ollama:** Install [Ollama](https://ollama.com/) and pull a model (e.g., `ollama run llama2`)
*   **Supabase:** Create a free project at [Supabase](https://supabase.com/) and run the provided SQL migration.

### 2. Database Migration
Run the included `supabase_setup.sql` script in your Supabase SQL Editor. This initializes the `user_queries`, `exam_resources`, and `study_plans` tables with their respective JSONB constraints to hold the output structures (including the specifically added `youtube_lectures` column).

### 3. Environment Variables
Create a `.env` file in the root project directory containing your Supabase credentials:
```env
SUPABASE_URL="your-supabase-project-url"
SUPABASE_KEY="your-supabase-service-role-or-anon-key"
LLM_BASE_URL="http://localhost:11434"
LLM_MODEL="llama2"
LLM_TIMEOUT=60
```

### 4. Install Dependencies
Initialize a virtual environment and install the required packages:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 5. Running the Application
Spin up the Streamlit interface:
```bash
streamlit run app.py
```
*Navigate to `http://localhost:8501`, enter your exam name, and generate your customized study strategy!*

---

## 🛠️ Modifying the Agent
The codebase relies on a **Services and Agents pattern**:
*   **To modify the LLM Prompt:** Edit `exam_ai_agent/services/study_plan_service.py` under the *generate_plan* method.
*   **To alter the search strategy:** Edit `exam_ai_agent/tools/web_search.py` methods to append localized/specific queries.
*   **To adjust the final UI JSON payload structure:** Edit `exam_ai_agent/agents/response_agent.py`.
