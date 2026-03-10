"""
Convenience script to run the FastAPI server from the project root.
Usage: python run_api.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "exam_ai_agent.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
