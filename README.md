# Exam Research AI Agent – Project Root

This repository contains the **Exam Research AI Agent** package.

## Quick start

1. **Create virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r exam_ai_agent/requirements.txt
   ```

2. **Optional: Install Ollama** for AI-generated study plans  
   [ollama.ai](https://ollama.ai) → then run `ollama run llama2`

3. **Start the API** (from this folder)
   ```bash
   python run_api.py
   ```
   Or: `uvicorn exam_ai_agent.api.main:app --reload --port 8000`

4. **Start the Streamlit UI** (in a second terminal)
   ```bash
   streamlit run exam_ai_agent/ui/streamlit_app.py
   ```

5. Open the UI in the browser, enter an exam name (e.g. **GATE CSE**), and click **Generate Preparation Plan**.

---

Full setup, configuration, and API details: **[exam_ai_agent/README.md](exam_ai_agent/README.md)**.
