import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv
from supabase import create_client, Client

from groq_client import generate_problem_with_groq

# Shared models
from models import DetectResponse, SemanticMatch

# Import your AI logic
from adaptive_feedback.detector import run_detection, initialize_ai


load_dotenv()

SUPABASE: Optional[Client] = None


def _normalize_language(language: str) -> str:
    l = (language or "").strip().lower()
    if l in {"cpp", "c++"}:
        return "c++"
    return l


def _get_supabase_client() -> Client:
    """
    Lazily initialize and return a Supabase client.
    """
    global SUPABASE
    if SUPABASE is not None:
        return SUPABASE

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment")

    SUPABASE = create_client(url, key)
    return SUPABASE


def get_all_problems() -> List[Dict[str, Any]]:
    """
    Fetch all problems from the Supabase 'problems' table.
    """
    client = _get_supabase_client()
    resp = client.table("problems").select("*").execute()
    return getattr(resp, "data", []) or []

def get_curriculum_problems() -> List[Dict[str, Any]]:
    """Fetch structured problems from the 'learning_path' table."""
    try:
        client = _get_supabase_client()
        resp = client.table("learning_path").select("*").execute()
        return getattr(resp, "data", []) or []
    except Exception:
        return []

def get_categories(language: str, source: str = "problems") -> List[str]:
    language_norm = _normalize_language(language)
    if not language_norm:
        return []

    # Choose table based on source
    problems_db = get_curriculum_problems() if source == "learning" else get_all_problems()
    
    topics = set()
    for p in problems_db:
        p_lang = str(p.get("language", "")).lower()
        if language_norm in p_lang:
            topic = str(p.get("topic", "")).strip()
            if topic:
                topics.add(topic)
    return sorted(topics)


def save_user_activity(
    user_id: str,
    session_id: str,
    language: str,
    content: str,
    result: Dict[str, Any],
) -> None:
    """
    Persist each analysis run into the Supabase `user_activities` table.

    Assumptions (adjust column names if your schema differs):
      - user_id (text)
      - session_id (text)
      - language (text)
      - content (text)
      - result (json/jsonb)
    """
    client = _get_supabase_client()

    row = {
        "user_id": user_id,
        "session_id": session_id,
        "language": language,
        "content": content,
        "result": result,
    }

    # Don’t hard-fail the entire request if persistence fails; the caller may decide.
    client.table("user_activities").insert(row).execute()


def get_user_stats(user_id: str) -> Dict[str, Any]:
    client = _get_supabase_client()
    try:
        # Fetch only timestamps for this specific user activity
        resp = client.table("user_activities").select("created_at").eq("user_id", user_id).execute()
        rows = getattr(resp, "data", []) or []
    except Exception as exc:
        print(f"Error fetching stats: {exc}")
        rows = []

    # Initialize grouped data
    counts: Dict[str, int] = {}
    speed_data: Dict[str, List[float]] = {}

    for row in rows:
        dt = parse_dt(row.get("created_at"))
        if not dt:
            continue

        # Group by actual calendar date
        date_key = dt.strftime("%Y-%m-%d")
        counts[date_key] = counts.get(date_key, 0) + 1

        # For Learning Speed, use a placeholder when only created_at is selected
        weekday = dt.strftime("%a")
        if weekday not in speed_data:
            speed_data[weekday] = []
        speed_data[weekday].append(0.5)

    # Convert grouped date counts to heatmap-compatible month/day buckets
    months_list = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]
    days_list = ["Mon", "Wed", "Fri"]
    heatmap_counts: Dict[Tuple[str, str], int] = {}
    for date_key, count in counts.items():
        dt = parse_dt(date_key)
        if not dt:
            continue
        month, day = dt.strftime("%b"), dt.strftime("%a")
        heatmap_counts[(month, day)] = heatmap_counts.get((month, day), 0) + count

    heatmap = [{"month": m, "day": d, "count": heatmap_counts.get((m, d), 0)} for m in months_list for d in days_list]

    learning_speed = [{"day": d, "speed": round(sum(v) / len(v), 2)} for d, v in speed_data.items()]

    return {
        "heatmap": heatmap,
        "learning_speed": learning_speed or [{"day": "Mon", "speed": 0}],
        "lessons_completed": []
    }


def analyze_student_submission(content: str, language: str = "python") -> DetectResponse:
    """
    Convenience wrapper used by the Streamlit app.
    It reuses the same detection pipeline and response model as the API.
    """
    ai_result = run_detection({"content": content, "language": language})
    return DetectResponse(**ai_result)


def get_next_step(analysis: DetectResponse, current_lang: str, current_problem_id: str) -> Dict[str, Any]:
    """
    Adaptive Logic for College Demo:
    - Score < 0.7: Give the very next problem in the SAME topic.
    - Score >= 0.7: Jump to the first problem of the NEXT topic.
    """
    mastery_score = float(analysis.confidence or 0.0)
    client = _get_supabase_client()

    # 1. Get the current problem's details (Topic and Order)
    current_res = client.table("learning_path").select("*").eq("id", current_problem_id).single().execute()
    current_prob = current_res.data
    
    if not current_prob:
        return {"error": "Current problem not found"}

    current_topic = current_prob.get("topic")
    current_order = current_prob.get("order_index")

    # 2. Decide the "Search Criteria" based on mastery
    if mastery_score < 0.7:
        # STRUGGLING: Find the next problem in the same topic
        # (e.g., if they were on prob 1, give them prob 2 of 'Basics')
        next_res = client.table("learning_path") \
            .select("*") \
            .eq("language", current_lang) \
            .eq("topic", current_topic) \
            .gt("order_index", current_order) \
            .order("order_index") \
            .limit(1) \
            .execute()
    else:
        # MASTERED: Jump to the first problem of a DIFFERENT topic
        next_res = client.table("learning_path") \
            .select("*") \
            .eq("language", current_lang) \
            .neq("topic", current_topic) \
            .order("topic") \
            .order("order_index") \
            .limit(1) \
            .execute()

    # 3. Return the new problem or a fallback if they finished everything
    if next_res.data:
        return next_res.data[0]
    else:
        # Fallback: If no "next" exists, just give them the next global problem
        fallback = client.table("learning_path") \
            .select("*") \
            .eq("language", current_lang) \
            .gt("order_index", current_order) \
            .limit(1).execute()
        return fallback.data[0] if fallback.data else current_prob



# --- TEST ---
if __name__ == "__main__":
    initialize_ai()
    # test_code = "def hello() print('hi')" # Syntax error example
    test_code = "x = 10 / 0" # Runtime/Logic example
    
    print("--- 1. AI Analysis ---")
    result = analyze_student_submission(test_code, language="python")
    # Pydantic V2 fix: model_dump_json() instead of .json()
    print(result.model_dump_json(indent=2)) 
    
    print("\n--- 2. Adaptive Recommendation ---")
    next_p = get_next_step(result, current_lang="python")
    print(f"Recommended Next Task: {next_p.get('title')} ({next_p.get('difficulty')})")