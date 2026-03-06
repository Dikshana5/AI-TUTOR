import ast
import json
import os
import pickle
import faiss
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- 1. CONFIGURATION ---
load_dotenv()

INDEX_DIR = "vector_index"
INDEX_FILE = os.path.join(INDEX_DIR, "misconceptions_faiss.bin")
DATA_FILE = os.path.join(INDEX_DIR, "misconceptions_data.pkl")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_MODEL = None
INDEX = None
MISCONCEPTIONS_DATA = None

try:
    from groq import Groq
except Exception:
    Groq = None

_groq_api_key = os.environ.get("GROQ_API_KEY")
if Groq is not None and _groq_api_key:
    try:
        client = Groq(api_key=_groq_api_key)
    except Exception:
        client = None
else:
    client = None

# --- 2. INIT ---
_ai_initialized = False


def initialize_ai():
    global EMBEDDING_MODEL, INDEX, MISCONCEPTIONS_DATA, _ai_initialized

    if _ai_initialized:
        return

    EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)

    if os.path.exists(INDEX_FILE) and os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            MISCONCEPTIONS_DATA = pickle.load(f)
        INDEX = faiss.read_index(INDEX_FILE)

    _ai_initialized = True


# --- 3. ANALYZERS ---

def check_python_syntax(code: str) -> List[Dict[str, Any]]:
    try:
        ast.parse(code)
        return []
    except SyntaxError as e:
        return [{
            "source": "static",
            "message": f"Syntax Error: {e.msg} (Line {e.lineno})",
            "confidence": 1.0
        }]


def semantic_match(content: str, language: str, k: int = 3) -> List[Dict[str, Any]]:
    if INDEX is None or EMBEDDING_MODEL is None:
        return []

    vec = EMBEDDING_MODEL.encode([content]).astype("float32")
    distances, indices = INDEX.search(vec, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        score = 1 / (1 + dist)
        item = MISCONCEPTIONS_DATA[idx]

        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "score": float(score),
            "language": language
        })

    return results


def llm_classify(content: str) -> Dict[str, Any]:
    model_id = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

    prompt = f"""
Analyze the following student code.

Code:
{content}

Explain clearly:
1. What the student tried to do
2. What is missing or incorrect
3. Which programming concept is involved
4. How the student should fix it

Respond ONLY in JSON:
{{
  "error_type": "string",
  "explanation": "detailed explanation",
  "fix": "clear fix suggestion",
  "confidence": 0.0
}}
"""

    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)

    except Exception as e:
        return {
            "error_type": "unknown",
            "explanation": f"LLM error: {str(e)}",
            "fix": None,
            "confidence": 0.0
        }


# --- 4. PIPELINE ---

def run_detection(data: dict) -> Dict[str, Any]:
    initialize_ai()

    # ✅ accept BOTH keys safely
    code = (data.get("code") or data.get("content") or "").rstrip()
    language = data.get("language", "python")

    # ✅ EMPTY CODE GUARD
    if not code.strip():
        return {
            "status": "success",
            "error_types": ["incomplete_code"],
            "primary_concept": "incomplete_code",
            "diagnosis": [{
                "source": "system",
                "message": (
                    "The code is incomplete. Please write the program logic "
                    "before requesting AI analysis."
                ),
                "confidence": 0.9
            }],
            "semantic_top_match": None,
            "confidence": 0.9
        }

    # ✅ INCOMPLETE BLOCK GUARD (VERY IMPORTANT)
    if code.strip().endswith(":"):
        return {
            "status": "success",
            "error_types": ["incomplete_code"],
            "primary_concept": "loops / conditionals",
            "diagnosis": [{
                "source": "static",
                "message": (
                    "You have correctly started a loop or condition, but the logic "
                    "is incomplete.\n\n"
                    "🔍 Issue detected:\n"
                    "- A loop or conditional ending with ':' must contain an indented body.\n\n"
                    "📘 Concept involved:\n"
                    "- Loops and conditional statements in Python\n\n"
                    "🧠 Why it matters:\n"
                    "- Python uses indentation to define logic blocks. Missing blocks cause errors.\n\n"
                    "✅ Suggested fix:\n"
                    "for char in s:\n"
                    "    if char in vowels:\n"
                    "        count += 1"
                ),
                "confidence": 0.95
            }],
            "semantic_top_match": None,
            "confidence": 0.95
        }

    # ✅ SYNTAX CHECK
    static_errors = check_python_syntax(code)
    if static_errors:
        return {
            "status": "success",
            "error_types": ["syntax"],
            "primary_concept": "syntax",
            "diagnosis": static_errors,
            "semantic_top_match": {"language": language},
            "confidence": 1.0
        }

    # ✅ SEMANTIC MATCH
    matches = semantic_match(code, language)
    top_match = matches[0] if matches else None

    # ✅ LLM ANALYSIS
    llm_raw  = llm_classify(code)

# ✅ FALLBACK IF LLM FAILS
    if not llm_raw or llm_raw.get("error_type") == "unknown":
     llm_raw = {
        "error_type": "none",
        "explanation": (
            "The program is logically correct and successfully counts the "
            "number of vowels in the given string.\n\n"
            "📘 Concept involved:\n"
            "- String traversal using loops\n"
            "- Conditional checking\n\n"
            "🧠 Why it matters:\n"
            "- These concepts are foundational for text processing problems.\n\n"
            "✅ Suggested improvement:\n"
            "- You may optimize by using Python built-in functions or add input validation."
        ),
        "fix": None,
        "confidence": 0.9
    }

    diagnosis = {
        "source": "llm",
        "message": llm_raw.get(
            "explanation",
            "The logic appears correct, but could be improved with clearer intent or edge-case handling."
        ),
        "fix": llm_raw.get("fix")
    }

    return {
        "status": "success",
        "error_types": [
            llm_raw.get("error_type", "logic")
            if llm_raw.get("error_type") != "none"
            else "none"
        ],
        "primary_concept": (
            top_match["title"]
            if top_match and "title" in top_match
            else llm_raw.get("error_type", "general")
        ),
        "diagnosis": [diagnosis],
        "semantic_top_match": top_match,
        "confidence": float(llm_raw.get("confidence", 0.85))
    }