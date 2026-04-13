from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends 
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict

from dotenv import load_dotenv
load_dotenv()
import os

# 1. Blueprint Imports
from models import (
    DetectRequest,
    DetectResponse,
    UserCreate,
    UserLogin,
    User,
    Token,
)

# 2. Logic Imports
from adaptive_feedback.detector import run_detection, initialize_ai

# 3. Engine Imports
from adaptive_feedback.engine import (
    _get_supabase_client,
    get_next_step,
    get_all_problems,
    get_categories,
    get_curriculum_problems,
    get_user_stats,
    save_user_activity,
)

# 4. Auth Utilities
from auth_utils import get_password_hash, verify_password, create_access_token
try:
    from groq import Groq
    _api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    chat_client = Groq(api_key=_api_key) if _api_key else None
    MODEL_ID = os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile"
except Exception:
    chat_client = None
    MODEL_ID = None


groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI(title="AI Programming Tutor - Master API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        result: Dict[str, Any] = run_detection(req.model_dump())

        # Persistence: save each submission attempt to Supabase.
        try:
            save_user_activity(
                user_id=req.user_id,
                session_id=req.session_id,
                language=req.language,
                content=req.content,
                result=result,
            )
        except Exception as persist_exc:
            # Don’t break analysis if persistence fails; it will show up in server logs.
            print(f"[user_activities] Failed to persist activity: {persist_exc}")

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
        prob_id = payload.get("problem_id") # Get the ID
    # Pass it to your new engine logic
        return get_next_step(analysis, current_lang=lang, current_problem_id=prob_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        



@app.get("/problems")
async def list_problems():
    return get_all_problems()


@app.get("/categories/{language}")
def categories(language: str):
    return get_categories(language)


@app.get("/user/stats/{user_id}")
def user_stats(user_id: str):
    print(f"Received /user/stats request for user_id: {user_id}")
    try:
        if user_id == "guest" or len(user_id) != 36:
            return {"heatmap": [], "learning_speed": [], "lessons_completed": []}

        client = _get_supabase_client()
        resp = client.table("user_activities").select("*").eq("user_id", user_id).execute()
        rows = getattr(resp, "data", []) or []

        # Calculate lessons_completed: assume all activities are successful lessons
        num_activities = len(rows)
        lessons_completed = [
            {"project": f"Lesson {i+1}", "progress": 100}
            for i in range(num_activities)
        ]

        # Group by date for learning_speed and heatmap
        date_counts = {}
        for row in rows:
            created_at = row.get("created_at")
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    if created_at.endswith("Z"):
                        created_at = created_at.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(created_at)
                except ValueError:
                    continue
            elif isinstance(created_at, datetime):
                dt = created_at
            else:
                continue

            date_key = dt.strftime("%Y-%m-%d")
            date_counts[date_key] = date_counts.get(date_key, 0) + 1

        # learning_speed: list of {"day": date, "speed": count}
        learning_speed = [
            {"day": date_key, "speed": count}
            for date_key, count in sorted(date_counts.items())
        ]

        # heatmap: list of {"month": str, "day": str, "count": int}
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        heatmap = []
        for date_key, count in date_counts.items():
            year, month, day = date_key.split("-")
            month_str = month_names[int(month) - 1]
            heatmap.append({"month": month_str, "day": day, "count": count})

        return {"heatmap": heatmap, "learning_speed": learning_speed, "lessons_completed": lessons_completed}
    except Exception as exc:
        print(f"user_stats endpoint error for {user_id}: {exc}")
        return {"heatmap": [], "learning_speed": [], "lessons_completed": []}

@app.get("/learning/categories/{language}")
def learning_categories(language: str):
    # This calls your updated engine function with source="learning"
    return get_categories(language, source="learning")

@app.get("/learning/problems")
async def learning_problems():
    # This calls your new engine function to fetch from 'learning_path'
    return get_curriculum_problems()


@app.post("/signup", response_model=User)
def signup(user: UserCreate):
    """
    Create a user profile using Supabase `profiles` table.
    """
    from auth_utils import get_profile_by_username, get_profile_by_email, create_profile

    existing_username = get_profile_by_username(user.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already registered")

    existing_email = get_profile_by_email(user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    created = create_profile(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    return created


@app.post("/login", response_model=Token)
def login(user_credentials: UserLogin):
    """
    Login using Supabase `profiles` table.
    """
    from auth_utils import get_profile_by_username

    user = get_profile_by_username(user_credentials.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    hashed_password = user.get("hashed_password")
    if not verify_password(user_credentials.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.get("username")})
    user_id = user.get("id")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user_id,
        "user": {"id": user_id, "username": user.get("username"), "email": user.get("email")}
    }


@app.post("/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    user_message = data.get("message")
    user_id = data.get("user_id")
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are COUTOR, an expert AI programming tutor."},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile", # Or your preferred Groq model
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        print(f"Chat Error: {e}")
        return {"response": "I'm having trouble connecting to my brain right now. Try again?"}
