# 🤖 Exam Research AI Agent - End-to-End Documentation

## 1. Project Overview
The **Exam Research AI Agent** is an intelligent, multi-agent orchestration system designed to automate the grueling process of competitive exam preparation. Whether a student is preparing for "GATE CSE", "JEE Main", or "UPSC Prelims", the system takes the exam name as input and autonomously generates a comprehensive, personalized study strategy. 

It accomplishes this by scouring the internet for official syllabus documents, previous year question papers, recommended books, and high-yield YouTube video lectures. Finally, it uses an advanced Large Language Model (Groq's LLaMA 3.3) to synthesize this raw data into a strictly structured, day-by-day 4-week study plan.

---

## 2. Core Features
- **Automated Web Research:** Dynamically generates targeted search queries to find official, high-quality resources without manual intervention.
- **Deep Web Scraping & PDF Parsing:** Navigates HTML pages and extracts text seamlessly from nested URLs and hidden PDF documents.
- **Intelligent Syllabus Extraction:** Parses unstructured scraped text into a hierarchical, topic-and-subtopic JSON format.
- **Custom AI Study Plan Generation:** Uses the Groq Cloud LLM to build an attractive, rigorous, and syllabus-tailored 4-week timetable with daily breakdowns and strategic tips.
- **Strict Deduplication:** Ensures the user never sees duplicate URLs across resources, papers, or YouTube lectures by aggressively normalizing base URLs and domains.
- **Caching & Analytics (Supabase):** Stores user queries and full exam strategy payloads in a PostgreSQL database via Supabase. If an exam was searched previously, the system fetches it from the cache instantly, saving API costs and wait times.
- **Vector Database Integration (FAISS):** Chunks and stores all scraped raw text in a local FAISS index, laying the groundwork for future Retrieval-Augmented Generation (RAG) chatbot features.
- **Modern Interactive UI:** Built on Streamlit, the frontend features progress-tracking checkboxes, downloadable PDF links, embedded YouTube video players, and expandable resource cards.

---

## 3. Technology Stack
- **Frontend & App Framework:** [Streamlit](https://streamlit.io/) (Python)
- **AI Orchestration Framework:** [LangChain](https://www.langchain.com/) (`langchain-core`, `langchain-groq`)
- **Cloud LLM Provider:** [Groq API](https://groq.com/) (Model: `llama-3.3-70b-versatile`) for ultra-fast reasoning and synthesis.
- **Database & Caching:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Web Search/Scraping:** `duckduckgo-search` (ddgs), `requests`, `beautifulsoup4`, `PyPDF2`
- **Vector Store Local Memory:** [FAISS](https://faiss.ai/) (`faiss-cpu`)

---

## 4. Multi-Agent Architecture
The system employs a "Services and Agents" pattern to separate concerns and ensure scalable AI behavior. 

### Orchestrator: `ResearchAgent` (`agents/research_agent.py`)
Acts as the central coordinator. It first checks the Supabase cache. If no cache exists, it fires up the sub-agents in a chronological pipeline and manages state between them.

### Sub-Agents:
1. **🔍 Search Agent (`agents/search_agent.py`)** 
   - Uses `WebSearchTool` (DuckDuckGo wrapper) to execute 15-20 highly targeted search queries concurrently (e.g., "GATE CSE syllabus filetype:pdf", "GATE CSE preparation strategy site:youtube.com").
2. **🕷️ Scraping Agent (`agents/scraping_agent.py`)**
   - Receives the URLs found by the Search Agent. It navigates to these links, parsing HTML to extract raw textual footprints. It also detects deep-linked PDFs inside webpages, downloading and parsing them dynamically.
3. **🧠 Processing Agent (`agents/processing_agent.py`)**
   - Takes the mountain of raw text and uses Regex/Heuristics combined with a Groq LLM refinement prompt to carefully prune out noise. It outputs exactly 50 core `syllabus_items` and `important_topics`.
4. **📅 Study Plan Agent (`agents/study_plan_agent.py`)**
   - Pulls the cleaned syllabus topics and generates an exhaustive system prompt. It sends this to Groq to generate a 4-week, day-by-day JSON schedule.
5. **🏗️ Response Agent (`agents/response_agent.py`)**
   - Acts as the final tollgate. It aggregates all data streams (papers, study plan, syllabus, resources, videos) and passes the massive payload to Groq one last time to enforce strict deduplication and exact JSON formatting keys. It also chunks raw text into the FAISS Vector Store.

---

## 5. End-to-End User Flow (Pipeline)

1. **User Input:** User enters an exam name (e.g., "UPSC CSE") into the Streamlit Web Application and clicks "Generate Strategy". `app.py` triggers `run_research_natively`.
2. **Cache Interception:** `SupabaseService` queries the `exam_resources` and `study_plans` tables. If the exam exists, it bypasses computation entirely and returns the UI in milliseconds.
3. **Search Phase:** If no cache exists, `SearchAgent` dispatches its DuckDuckGo queries to isolate official sites, PDF repos, and YouTube channels.
4. **Scraping Phase:** URLs are concurrently fetched. `BeautifulSoup4` strips HTML while `PyPDF2` reads binary PDF data.
5. **Data Processing Phase:** The `ProcessingAgent` extracts hierarchical dictionaries (Topic -> Subtopics). It utilizes Groq to synthesize the 50 most critical topics.
6. **Study Plan Generation:** `StudyPlanAgent` feeds the synthesized syllabus into Groq LLaMA-3.3-70B, which returns a highly-granular sequence of study tasks with tips.
7. **Final Assembly & Formatting:** `ResponseAgent` combines all segments into a monolithic dictionary. It runs a final deduplication pass.
8. **Persistence:** The final output is pushed to Supabase by the Orchestrator for subsequent caches.
9. **UI Rendering:** The Streamlit app dynamically unpacks the JSON into 5 aesthetic Tabs (Syllabus, Previous Papers, Study Plan, Resources, Video Lectures) for the user to interact with.

---

## 6. Environment & Streamlit Secrets Setup
To deploy or run securely without `.env` leaks, the project leverages `.streamlit/secrets.toml`:
```toml
SUPABASE_URL="https://your-supabase-project.supabase.co"
SUPABASE_KEY="your-anon-or-service-key"
GROQ_API_KEY="gsk_your_groq_api_key_here"
```
The codebase safely accesses these in production using `st.secrets.get()`.

---

## 7. Database Entity Relationship (Supabase)
- **`user_queries` (Tracking):** Logs what exams users look for (`exam_name`, `created_at`).
- **`exam_resources` (Cache):** Stores the JSONB payload (`syllabus`, `previous_papers`, `important_topics`, `resources`, `youtube_lectures`) uniquely mapped to `exam_name` via UPSERT.
- **`study_plans` (Cache):** Stores the 4-week JSON schedule payload uniquely mapped to `exam_name`.
