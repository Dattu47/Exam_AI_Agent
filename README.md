# Exam Research AI Agent

A production-ready AI agent that performs deep web research to collect and organize exam preparation resources for students. Give it an exam name (e.g. **GATE CSE**, **JEE Main**) and it will find syllabus, previous year papers, important topics, a study plan, free courses, and reference links.

## Features

- **Deep web research** via DuckDuckGo (no API key required)
- **Automatic resource collection**: syllabus, papers, exam pattern, study material
- **AI-generated study plan** (Ollama) with fallback template
- **Resource categorization** and PDF link detection
- **FAISS vector store** for storing and searching scraped knowledge
- **Streamlit web UI** running natively with the agent
- Modular, logged, and error-handled code

## Tech Stack

| Component        | Technology              |
|-----------------|-------------------------|
| Language        | Python 3.10+            |
| Agent / LLM     | LangChain + Ollama      |
| Search          | DuckDuckGo (duckduckgo-search) |
| Scraping        | BeautifulSoup + Requests |
| Vector DB       | FAISS                   |
| UI              | Streamlit               |

## Project Structure

```
├── app.py                  # Main Streamlit UI & entry point
├── requirements.txt        # Dependencies
├── .env.example            # Environment variables template
├── exam_ai_agent/
│   ├── agents/
│   │   └── research_agent.py    # Main orchestration agent
│   ├── tools/
│   │   ├── web_search.py        # DuckDuckGo search
│   │   ├── web_scraper.py       # BeautifulSoup scraper
│   │   └── pdf_downloader.py    # PDF link discovery
│   ├── services/
│   │   ├── syllabus_service.py  # Syllabus extraction
│   │   ├── papers_service.py   # Previous papers aggregation
│   │   └── study_plan_service.py # Study plan generation (LLM/template)
│   ├── database/
│   │   └── vector_store.py     # FAISS vector store
│   ├── config/
│   │   └── settings.py         # Configuration
│   └── utils/
│       └── logger.py           # Logging
```

## Setup (Run Locally)

### 1. Python environment

Use Python 3.10 or higher. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Optional: Ollama (for AI study plan and embeddings)

- Install [Ollama](https://ollama.ai).
- Run a chat model, e.g.:
  ```bash
  ollama run llama2
  ```
- For vector store embeddings (optional):
  ```bash
  ollama run nomic-embed-text
  ```

If Ollama is not running, the app still works: the study plan uses a **template** and the vector store uses a simple fallback.

### 4. Run the App

```bash
streamlit run app.py
```

## Usage

1. Open the Streamlit app.
2. Enter an exam name (e.g. **GATE CSE**, **JEE Main**, **UPSC CSE**).
3. Click **Generate Strategy**.
4. View **Syllabus**, **Previous Papers**, **Important Topics**, **Study Plan**, and **Resources**.

### Python (calling the agent directly)

```python
from exam_ai_agent.agents.research_agent import ResearchAgent

agent = ResearchAgent()
result = agent.research_exam("GATE CSE")

print(result["syllabus"])
print(result["previous_papers"])
print(result["study_plan"])
```

## Configuration

Environment variables (optional; defaults in `exam_ai_agent/config/settings.py`):

| Variable            | Default                 | Description                    |
|---------------------|-------------------------|--------------------------------|
| `LLM_BASE_URL`      | `http://localhost:11434`| Ollama API URL                 |
| `LLM_MODEL`         | `llama2`                | Ollama model name              |
| `MAX_SEARCH_RESULTS`| `10`                    | Max DuckDuckGo results per query |
| `MAX_SCRAPE_PAGES`  | `5`                     | Max pages to scrape per run     |
| `VECTOR_STORE_PATH` | `exam_ai_agent/data/faiss_index` | FAISS index directory   |
| `LOG_LEVEL`         | `INFO`                  | Logging level                  |

Create a `.env` in the project root or set these in the environment.

## License

Use and modify as needed for your project.
