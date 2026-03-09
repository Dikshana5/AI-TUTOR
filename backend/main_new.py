from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# 1. Blueprint Imports
from models import (
    DetectRequest, 
    DetectResponse, 
    UserCreate, 
    UserLogin, 
    User, 
    Token, 
    UserDB
)

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


# Create database tables
Base.metadata.create_all(bind=engine)

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


@app.post("/signup", response_model=User)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == user_credentials.username).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/analyze", response_model=DetectResponse)
async def analyze(req: DetectRequest):
    """
    Takes student code and returns the AI diagnosis.
    """
    try:
        result = run_detection(req.model_dump())

        return {
            "semantic_top_match": result.get("semantic_top_match"),
            "language": result.get("language", "python")
        }

    except Exception as e:
        print(f"Detailed Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/problems")
def list_problems():
    """
    Exposes the problem bank so the frontend can list projects/challenges.
    """
    return PROBLEMS_DB


@app.post("/next-step")
def next_step(payload: dict):
    """Returns the next learning step based on analysis payload.

    The frontend sends an analysis object to this endpoint using
    `fetchNextStep`. This delegates to `get_next_step` in the
    adaptive feedback engine.
    """
    try:
        result = get_next_step(payload)
        return result
    except Exception as e:
        print(f"Next-step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/chat")
def chat_endpoint(payload: dict):
    """Simple chat endpoint that forwards messages to the Groq chat model and returns the assistant reply.

    If the Groq client is not configured or a remote error occurs, return a safe fallback reply so the frontend can still function.
    """

    messages = payload.get("messages")
    if not messages:
        msg = payload.get("message") or ""
        messages = [{"role": "user", "content": msg}]

    # If chat client not configured, return a friendly fallback reply
    if chat_client is None or MODEL_ID is None:
        return {"reply": "(local) The chat model is not configured on this server. Try setting GROQ_API_KEY or OPENAI_API_KEY. Meanwhile, here's a hint: focus on breaking the problem into smaller steps."}

    try:
        resp = chat_client.chat.completions.create(messages=messages, model=MODEL_ID)
        text = resp.choices[0].message.content
        return {"reply": text}
    except Exception as e:
        print(f"Chat error: {e}")
        # Return fallback reply instead of raising so frontend still receives a response
        return {"reply": "(local) Could not reach LLM service. Please check server configuration."}
