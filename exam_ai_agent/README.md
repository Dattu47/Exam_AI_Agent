# Exam Research AI Agent

A production-ready AI agent that performs deep web research to collect and organize exam preparation resources for students. Give it an exam name (e.g. **GATE CSE**, **JEE Main**) and it will find syllabus, previous year papers, important topics, a study plan, free courses, and reference links.

## Features

- **Deep web research** via DuckDuckGo (no API key required)
- **Automatic resource collection**: syllabus, papers, exam pattern, study material
- **AI-generated study plan** (Ollama) with fallback template
- **Resource categorization** and PDF link detection
- **FAISS vector store** for storing and searching scraped knowledge
- **REST API** (FastAPI) and **Streamlit** web UI
- Modular, logged, and error-handled code

## Tech Stack

| Component        | Technology              |
|-----------------|-------------------------|
| Language        | Python 3.10+            |
| Backend         | FastAPI                 |
| Agent / LLM     | LangChain + Ollama      |
| Search          | DuckDuckGo (duckduckgo-search) |
| Scraping        | BeautifulSoup + Requests |
| Vector DB       | FAISS                   |
| Frontend        | Streamlit               |

## Project Structure

```
exam_ai_agent/
├── agents/
│   └── research_agent.py    # Main orchestration agent
├── tools/
│   ├── web_search.py        # DuckDuckGo search
│   ├── web_scraper.py       # BeautifulSoup scraper
│   └── pdf_downloader.py    # PDF link discovery
├── services/
│   ├── syllabus_service.py  # Syllabus extraction
│   ├── papers_service.py   # Previous papers aggregation
│   └── study_plan_service.py # Study plan generation (LLM/template)
├── database/
│   └── vector_store.py     # FAISS vector store
├── api/
│   └── main.py             # FastAPI app & /research_exam
├── ui/
│   └── streamlit_app.py    # Streamlit UI
├── config/
│   └── settings.py         # Configuration
├── utils/
│   └── logger.py           # Logging
├── requirements.txt
└── README.md
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

From the **project root** (the folder that contains `exam_ai_agent`):

```bash
pip install -r exam_ai_agent/requirements.txt
```

If your project root is `exam_ai_agent` itself:

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

### 4. Run the API

From the **project root** (parent of `exam_ai_agent`):

```bash
# Make sure the package is on PYTHONPATH (project root = current directory)
uvicorn exam_ai_agent.api.main:app --reload --host 0.0.0.0 --port 8000
```

If you are inside `exam_ai_agent`:

```bash
cd exam_ai_agent
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: **http://localhost:8000/docs**

### 5. Run the Streamlit UI

In a **second terminal**, from the project root:

```bash
streamlit run exam_ai_agent/ui/streamlit_app.py
```

If you are inside `exam_ai_agent`:

```bash
streamlit run ui/streamlit_app.py
```

The UI will open in the browser and call the API at `http://localhost:8000`. Keep the API running while using the UI.

**Alternative – run API with a script (from project root):**

```bash
python run_api.py
```

## Usage

### Web UI

1. Open the Streamlit app.
2. Enter an exam name (e.g. **GATE CSE**, **JEE Main**, **UPSC CSE**).
3. Click **Generate Preparation Plan**.
4. View **Syllabus**, **Previous Papers**, **Important Topics**, **Study Plan**, and **Resources**.

### API

**POST** `/research_exam`:

```json
// Request
{ "exam_name": "GATE CSE" }

// Response
{
  "syllabus": [{ "topic": "...", "source_url": "...", "description": "..." }],
  "previous_papers": [{ "title": "...", "url": "...", "type": "pdf" | "link" }],
  "important_topics": ["...", "..."],
  "study_plan": [{ "week": 1, "focus": "...", "tasks": ["..."] }],
  "resources": [{ "title": "...", "url": "...", "type": "..." }]
}
```

Example with `curl`:

```bash
curl -X POST http://localhost:8000/research_exam -H "Content-Type: application/json" -d "{\"exam_name\": \"GATE CSE\"}"
```

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

Environment variables (optional; defaults in `config/settings.py`):

| Variable            | Default                 | Description                    |
|---------------------|-------------------------|--------------------------------|
| `LLM_BASE_URL`      | `http://localhost:11434`| Ollama API URL                 |
| `LLM_MODEL`         | `llama2`                | Ollama model name              |
| `MAX_SEARCH_RESULTS`| `10`                    | Max DuckDuckGo results per query |
| `MAX_SCRAPE_PAGES`  | `5`                     | Max pages to scrape per run     |
| `VECTOR_STORE_PATH` | `exam_ai_agent/data/faiss_index` | FAISS index directory   |
| `LOG_LEVEL`         | `INFO`                  | Logging level                  |

Create a `.env` in the project root or set these in the environment.

## Error handling and logging

- All modules use a central logger (`utils/logger.py`).
- Search and scrape failures are caught and logged; the agent returns partial results when possible.
- API errors return appropriate HTTP status and messages.

## Deployment notes

- **API**: Run with a production ASGI server, e.g. `uvicorn exam_ai_agent.api.main:app --host 0.0.0.0 --port 8000` (no `--reload`).
- **Streamlit**: Point the UI to your API by setting the `API_BASE` in `ui/streamlit_app.py` or via an env-based config.
- **Ollama**: For production, run Ollama (and optional embedding model) on the same host or a dedicated service.

## License

Use and modify as needed for your project.
