from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 1. Blueprint Imports
from models import DetectRequest, DetectResponse

# 2. Logic Imports
from adaptive_feedback.detector import run_detection, initialize_ai

# 3. Engine Imports
from adaptive_feedback.engine import get_next_step, PROBLEMS_DB


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

