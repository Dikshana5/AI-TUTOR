import os
import json
import pickle
import faiss
from typing import Dict, Any
from sentence_transformers import SentenceTransformer
from groq_client import generate_problem_with_groq

# Shared models
from models import DetectResponse, SemanticMatch

# Import your AI logic
from adaptive_feedback.detector import run_detection, initialize_ai

# --- 1. CONFIGURATION & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjusted to look inside the feedengine folder correctly
PROBLEMS_PATH = os.path.join(os.path.dirname(__file__), "feedengine", "problems.json")
INDEX_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "vector_index"))

# --- 2. CORE FUNCTIONS ---
def refresh_vector_brain():
    """Updates the FAISS brain by indexing both Problems and Misconceptions."""
    
    # 1. Define Paths (Ensuring they match your generator)
    MISCONCEPTIONS_PATH = os.path.join(BASE_DIR, "feedengine", "misconceptions.json")
    # PROBLEMS_PATH is already defined in your global scope
    
    combined_data = []
    text_to_embed = []

    # 2. Load and Format Problems
    if os.path.exists(PROBLEMS_PATH):
        with open(PROBLEMS_PATH, "r") as f:
            problems = json.load(f)
            # Ensure it's a list
            prob_list = problems if isinstance(problems, list) else problems.get("problems", [])
            for p in prob_list:
                # Type flag helps the detector know what it found later
                p["data_type"] = "problem" 
                combined_data.append(p)
                text_to_embed.append(f"Problem ({p.get('language', 'Python')}): {p.get('title', '')} - {p.get('description', '')}")

    # 3. Load and Format Misconceptions
    if os.path.exists(MISCONCEPTIONS_PATH):
        with open(MISCONCEPTIONS_PATH, "r") as f:
            miscs = json.load(f)
            # Ensure it's a list
            misc_list = miscs if isinstance(miscs, list) else miscs.get("misconceptions", [])
            for m in misc_list:
                m["data_type"] = "misconception"
                combined_data.append(m)
                text_to_embed.append(f"Misconception ({m.get('language', 'Python')}): {m.get('title', '')} - {m.get('description', '')}")

    if not combined_data:
        print("❌ Error: No data found to index.")
        return

    # 4. Create Embeddings
    print(f"🧠 Encoding {len(combined_data)} items (Problems + Misconceptions)...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(text_to_embed).astype('float32')
    faiss.normalize_L2(embeddings)

    # 5. Build and Save FAISS Index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    os.makedirs(INDEX_DIR, exist_ok=True)
    faiss.write_index(index, os.path.join(INDEX_DIR, 'misconceptions_faiss.bin'))
    
    # Save the combined metadata so we can retrieve details by index ID
    with open(os.path.join(INDEX_DIR, 'misconceptions_data.pkl'), 'wb') as f:
        pickle.dump(combined_data, f)
    
    print(f"✅ FAISS Brain Rebuilt! Total items indexed: {len(combined_data)}")

def load_problems():
    try:
        with open(PROBLEMS_PATH, "r") as f:
            data = json.load(f)
            # Handle both list format and {"problems": [...]} format
            return data if isinstance(data, list) else data.get("problems", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Load problems once when engine starts
PROBLEMS_DB = load_problems()


def analyze_student_submission(content: str, language: str = "python") -> DetectResponse:
    """
    Convenience wrapper used by the Streamlit app.
    It reuses the same detection pipeline and response model as the API.
    """
    ai_result = run_detection({"content": content, "language": language})
    return DetectResponse(**ai_result)


def get_next_step(analysis: DetectResponse, current_lang: str = "python") -> Dict[str, Any]:
    """
    The Adaptive Logic: Filters by language, then adjusts difficulty.
    """

    # 1. Filter by language first
    lang_problems = [
        p for p in PROBLEMS_DB
        if current_lang.lower() in p.get("language", "").lower()
    ]

    # 2. Determine target difficulty
    if any(err in str(analysis.error_types).lower() for err in ["syntax", "indentation"]):
        target_diff = "easy"
    elif any(err in str(analysis.error_types).lower() for err in ["logic", "conceptual"]):
        target_diff = "medium"
    else:
        target_diff = "hard"

    # 3. Try to find a match in the same concept + same difficulty
    candidates = [
        p for p in lang_problems
        if p.get("difficulty", "").lower() == target_diff
    ]

    # Concept matching (fuzzy)
    concept = (analysis.primary_concept or "").lower()
    concept_matches = [
        p for p in candidates
        if concept in p.get("title", "").lower()
        or concept in p.get("topic", "").lower()
    ]

    # 4. Final selection with safe fallbacks
    if concept_matches:
        return concept_matches[0]

    if candidates:
        return candidates[0]

    if lang_problems:
        return lang_problems[0]

    # 5. LAST RESORT — JIT generation via Groq
    return generate_problem_with_groq(
        concept=analysis.primary_concept or "Programming Basics",
        difficulty=target_diff,
        language=current_lang
    )



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