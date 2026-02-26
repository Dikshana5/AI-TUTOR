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