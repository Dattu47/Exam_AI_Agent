import os
from unittest.mock import patch

def mock_get_secrets(*args, **kwargs):
    import toml
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            data = toml.load(f)
            return data
    except Exception:
        return {}

# Patch st.secrets before importing the rest of the application
# Streamlit secrets behaves like a dictionary.
# A simple patch to test without the full `streamlit run` context.
import streamlit as st

class MockSecrets(dict):
    pass

st.secrets = MockSecrets(mock_get_secrets())

# Now import the Research Agent
from exam_ai_agent.agents.research_agent import ResearchAgent

print("Starting research test for 'GATE CSE'...")

agent = ResearchAgent()
# Use force_refresh=True to mandate the whole pipeline firing, bypassing DB cache
results = agent.research_exam("GATE CSE", force_refresh=True)

import json
print("\n--- RESULTS JSON KEY DUMP ---")
print(json.dumps({k: bool(v) for k, v in results.items()}, indent=2))
print("--- TEST COMPLETED ---")
