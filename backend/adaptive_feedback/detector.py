import base64
import json
import os
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
import requests
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
load_dotenv()

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_MODEL = None
SUPABASE: Optional[Client] = None
JUDGE0_URL = os.getenv("JUDGE0_URL", "https://ce.judge0.com")
JUDGE0_TIMEOUT_S = int(os.getenv("JUDGE0_TIMEOUT_S", "20"))
JUDGE0_LANGUAGE_ID_FALLBACK = {
    # NOTE: these are best-effort defaults; if they fail, we fall back to /languages discovery.
    "python": 71,
    "java": 62,
    "cpp": 54,
    "c++": 54,
}
_judge0_language_id_cache: Dict[str, int] = {}

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
    """
    Initialize shared AI resources.

    Currently this only loads the SentenceTransformer embedding model.
    Supabase is initialized lazily when needed.
    """
    global EMBEDDING_MODEL, _ai_initialized

    if _ai_initialized:
        return

    EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
    _ai_initialized = True


# --- 3. ANALYZERS ---
def _b64_decode_maybe(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


def _normalize_language(lang: str) -> str:
    l = (lang or "").strip().lower()
    if l in {"c++", "cpp"}:
        return "cpp"
    if l in {"py", "python"}:
        return "python"
    if l in {"java"}:
        return "java"
    # default: preserve what we got; Judge0 resolver may still handle it
    return l or "python"


def _resolve_judge0_language_id(language: str) -> int:
    """
    Resolve a Judge0 `language_id` for a given language label.

    We try:
    1) Cached resolution
    2) /languages discovery
    3) Best-effort fallbacks
    """
    normalized = _normalize_language(language)
    if normalized in _judge0_language_id_cache:
        return _judge0_language_id_cache[normalized]

    # Fall back to configured defaults if we can’t reach /languages.
    fallback = JUDGE0_LANGUAGE_ID_FALLBACK.get(normalized)

    try:
        url = f"{JUDGE0_URL.rstrip('/')}/languages"
        resp = requests.get(url, timeout=JUDGE0_TIMEOUT_S)
        resp.raise_for_status()
        languages = resp.json()
        if isinstance(languages, dict):
            # Some APIs wrap the list; tolerate both.
            languages = languages.get("languages") or languages.get("data") or []

        needle = normalized
        # Heuristic needle for matching “C++” vs “cpp”.
        if needle == "cpp":
            needle = "c++"

        best: Optional[Tuple[int, Dict[str, Any]]] = None  # (score, lang_row)
        for lang_row in languages or []:
            name = str(lang_row.get("name") or "").lower()
            aliases = " ".join(lang_row.get("aliases") or []).lower()
            if needle not in name and needle not in aliases:
                continue

            # Score higher if needle appears in name.
            score = 0
            if needle in name:
                score += 2
            if "openjdk" in name and normalized == "java":
                score += 1
            if "python" in name and normalized == "python":
                score += 1
            if "c++" in name and normalized == "cpp":
                score += 1
            if "17" in name and normalized == "cpp":
                score += 1

            lang_id = lang_row.get("id")
            try:
                lang_id_int = int(lang_id)
            except Exception:
                continue

            if best is None or score > best[0]:
                best = (score, {**lang_row, "id_int": lang_id_int})

        if best is not None:
            resolved = int(best[1]["id_int"])
            _judge0_language_id_cache[normalized] = resolved
            return resolved
    except Exception:
        # We’ll use fallback below.
        pass

    if fallback is not None:
        _judge0_language_id_cache[normalized] = int(fallback)
        return int(fallback)

    raise RuntimeError(f"Unable to resolve Judge0 language_id for language={language!r}")


def _judge0_execute(source_code: str, language: str) -> Dict[str, Any]:
    """
    Execute code on Judge0 CE for Python/Java/C++.

    Returns a dict with (at minimum):
      - status_id (int | None)
      - status_description (str | None)
      - stdout (str)
      - stderr (str)
    """
    language_id = _resolve_judge0_language_id(language)
    src_b64 = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")

    # wait=true returns the final submission status synchronously.
    params = {
        "base64_encoded": "true",
        "wait": "true",
        "fields": "*",
    }
    payload = {
        "source_code": src_b64,
        "language_id": language_id,
    }

    url = f"{JUDGE0_URL.rstrip('/')}/submissions/"
    resp = requests.post(url, params=params, json=payload, timeout=JUDGE0_TIMEOUT_S)
    resp.raise_for_status()
    data = resp.json() or {}
    print(f"\n--- DEBUG RAW JUDGE0 ---\n{data}\n------------------------\n") 
    # -------------------------------

    status = data.get("status") or {}
    status_id = status.get("id")

    data = resp.json() or {}
    status = data.get("status") or {}
    status_id = status.get("id")
    try:
        status_id_int = int(status_id) if status_id is not None else None
    except Exception:
        status_id_int = None

    status_desc = status.get("description")

    stdout = _b64_decode_maybe(data.get("stdout"))
    stderr = _b64_decode_maybe(data.get("stderr"))

    is_accepted = status_id_int == 3  # Judge0: 3 => Accepted
    return {
        "status_id": status_id_int,
        "status_description": status_desc,
        "stdout": stdout,
        "stderr": stderr,
        # ADD THIS LINE: It decodes the actual Java compiler message
        "compile_output": _b64_decode_maybe(data.get("compile_output")), 
        "is_error": not is_accepted,
        "raw": data,
    }


def semantic_match(content: str, language: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Generate an embedding for the given content and use Supabase RPC
    to find the closest misconceptions.
    """
    if EMBEDDING_MODEL is None:
        return []

    # Lazy-init Supabase so we don't hard-fail if env vars are missing at import time
    global SUPABASE
    if SUPABASE is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            # If Supabase is not configured, silently skip semantic matching
            return []
        SUPABASE = create_client(supabase_url, supabase_key)

    # 384-dim embedding from SentenceTransformer
    vec = EMBEDDING_MODEL.encode([content], convert_to_numpy=True)[0].tolist()

    try:
        # Assumes you have a Postgres function `match_misconceptions`
        # that accepts at least: query_embedding (vector), match_count (int), language (text)
        rpc_payload = {
            "query_embedding": vec,
            "match_count": k,
            "language": language,
        }
        resp = SUPABASE.rpc("match_misconceptions", rpc_payload).execute()
        rows = getattr(resp, "data", []) or []
    except Exception:
        # If RPC fails for any reason, fall back to no semantic matches
        return []

    results: List[Dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "id": row.get("id"),
                "title": row.get("title"),
                # Many typical match_* RPCs return a `score` or `similarity` column
                "score": float(row.get("score", row.get("similarity", 0.0))),
                # Optional fields (RPC may return them)
                "fix": row.get("fix"),
                "description": row.get("description"),
            }
        )

    return results


def llm_classify(content: str, language: str, error_output: Optional[str] = None) -> Dict[str, Any]:
    model_id = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
    language_norm = _normalize_language(language)

    status_context = f"failed with error: {error_output}" if error_output else "passed execution"
    
    prompt = f"""
    TASK: Evaluate this student's {language_norm} code {status_context}.
    
    STUDENT CODE:
    {content}

    COMPILER/RUNTIME ERROR (IF ANY):
    {error_output}

    GRADING RUBRIC (Confidence Score 0.0 to 1.0):
    - 0.0 to 0.4: Code has major errors or missing concepts.
    - 0.5 to 0.7: Code runs but is inefficient or messy.
    - 0.8 to 1.0: Professional, clean, and correct solution.

    Respond ONLY in valid JSON format:
    {{
      "error_type": "Short Label",
      "explanation": "• 1-sentence what is wrong\\n• 1-sentence why it happens",
      "fix": "Specific 1-line code hint",
      "confidence": 0.0
    }}
 """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.1, # Change this from 0.3 to 0.1
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        return {"error_type": "Error", "explanation": "• AI failed to respond.", "fix": None, "confidence": 0.0}
        

# --- 4. PIPELINE ---
def run_detection(data: dict) -> Dict[str, Any]:
    initialize_ai()

    # ✅ accept BOTH keys safely
    code = (data.get("code") or data.get("content") or "").rstrip()
    language = data.get("language", "python")
    language_norm = _normalize_language(language)
    # For curriculum/semantic filtering we want to match the stored format like "C++"
    language_for_match = "c++" if language_norm == "cpp" else language_norm

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

    # ✅ INCOMPLETE BLOCK GUARD (Python-only heuristic)
    if language_norm == "python" and code.strip().endswith(":"):
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

    # ✅ UNIVERSAL EXECUTION VIA JUDGE0
       # ✅ 1. ATTEMPT EXECUTION
    try:
        exec_result = _judge0_execute(code, language_norm)
    except Exception as exc:
        exec_result = {
            "is_error": True,
            "stderr": f"Execution Service Error: {str(exc)}",
            "status_description": "Service Unavailable"
        }

    # ✅ 2. ERROR PATH (Compiler/Runtime Error)
    if exec_result.get("is_error") or exec_result.get("status_id") != 3:
        # Mastery logic: Fail to compile = Low Mastery (20%)
        # This triggers the 'Keep Practicing' branch in engine.py
        mastery_score = 0.2 
        
        actual_compiler_error = (
            exec_result.get("compile_output") or 
            exec_result.get("stderr") or 
            "Execution failed."
        )
        
        # Ask LLM to explain the error in student-friendly terms
        llm_raw = llm_classify(code, language_norm, error_output=actual_compiler_error)

        return {
            "status": "error",
            "primary_concept": "Syntax & Basics",
            "diagnosis": [{
                "message": llm_raw.get("explanation"),
                "fix": llm_raw.get("fix")
            }],
            "confidence": mastery_score, 
            "metadata": {"output": actual_compiler_error}
        }

    # ✅ 3. SUCCESS PATH (Code works)
    # The code ran! Now the AI evaluates if the logic is "Masterful"
    llm_raw = llm_classify(code, language_norm)
    
    # AI grades the student's work (usually returns 0.7 - 1.0)
    mastery_score = float(llm_raw.get("confidence", 0.85))

    # Identify the specific concept for the curriculum tracker
    matches = semantic_match(code, language_for_match)
    concept_title = matches[0].get("title") if matches else "Logic Implementation"

    return {
        "status": "success",
        "primary_concept": concept_title,
        "diagnosis": [{
            "message": llm_raw.get("explanation", "Excellent work! Your logic is sound."),
            "fix": llm_raw.get("fix")
        }],
        "confidence": mastery_score, 
        "metadata": {
            "output": exec_result.get("stdout") or "Program executed successfully.",
            "judge0": exec_result
        }
    }