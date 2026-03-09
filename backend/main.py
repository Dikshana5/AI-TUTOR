from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 1. Blueprint Imports
from models import DetectRequest, DetectResponse

# 2. Logic Imports
from adaptive_feedback.detector import run_detection, initialize_ai

# 3. Engine Imports
from adaptive_feedback.engine import get_next_step, PROBLEMS_DB


# 4. Database and Auth Imports
from database import engine, Base, get_db
from auth_utils import get_password_hash, verify_password, create_access_token

from dotenv import load_dotenv
load_dotenv()
import os
try:
    from groq import Groq
    _api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    chat_client = Groq(api_key=_api_key) if _api_key else None
    MODEL_ID = os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile"
except Exception:
    chat_client = None
    MODEL_ID = None


@app.on_event("startup")
def startup_event():
    try:
        initialize_ai()
        print("AI engine initialized")
    except Exception as e:
        print("AI initialization skipped:", e)

@app.get("/")
def root():
    return {"message": "AI Programming Tutor API running"}

app = FastAPI(title="AI Programming Tutor - Master API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "online", "engine": "Adaptive Feedback Logic Ready"}


@app.post("/analyze", response_model=DetectResponse)
async def analyze(req: DetectRequest):
    """
    Takes student code and returns the AI diagnosis.
    """
    try:
        # We pass the req.dict() because our updated detector expects a dictionary
        result = run_detection(req.model_dump())
        return result
    except Exception as e:
        # This will print the error in your Uvicorn terminal so you can see it
        print(f"Detailed Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/next-step")
def next_step(payload: dict):
    try:
        analysis = DetectResponse(**payload)
        lang = payload.get("language", "python")
        return get_next_step(analysis, current_lang=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/problems")
def list_problems():
    """
    Exposes the problem bank so the frontend can list projects/challenges.
    """
    return PROBLEMS_DB

