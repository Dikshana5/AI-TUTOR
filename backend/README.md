# Misconception Detector Backend (Member 1)

This service provides the core detection pipeline, including static analysis, LLM classification, and semantic retrieval, via a set of REST endpoints.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
Configure environment variables:
Copy .env.example to .env and fill in your OPENAI_API_KEY.

2. Running the Server
Start the FastAPI application with Uvicorn:

Bash
uvicorn main:app --reload

Key Endpoints
GET /health: Server status check.

POST /detect: Primary endpoint for diagnosis.

*(This is the instruction manual for the project.)*
