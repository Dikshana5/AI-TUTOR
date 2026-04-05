import os
import json
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer


def load_env() -> None:
    """
    Load environment variables from .env if present.
    Expects SUPABASE_URL and SUPABASE_KEY to be defined.
    """
    load_dotenv()
    missing = [name for name in ("SUPABASE_URL", "SUPABASE_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def get_supabase_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generate_embeddings(
    descriptions: List[str],
    model_name: str = "all-MiniLM-L6-v2",
) -> List[List[float]]:
    """
    Generate 384-dim embeddings for a list of descriptions.
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(descriptions, convert_to_numpy=True)
    return embeddings.tolist()


def main() -> None:
    # Resolve project root relative to this script
    backend_dir = Path(__file__).resolve().parent
    data_dir = backend_dir / "adaptive_feedback" / "feedengine"

    problems_path = data_dir / "problems.json"
    misconceptions_path = data_dir / "misconceptions.json"

    if not problems_path.exists():
        raise FileNotFoundError(f"Could not find problems.json at {problems_path}")
    if not misconceptions_path.exists():
        raise FileNotFoundError(f"Could not find misconceptions.json at {misconceptions_path}")

    print(f"Loading problems from {problems_path}")
    problems: List[Dict[str, Any]] = load_json_file(problems_path)

    print(f"Loading misconceptions from {misconceptions_path}")
    misconceptions: List[Dict[str, Any]] = load_json_file(misconceptions_path)

    # Ensure environment and Supabase client
    load_env()
    supabase = get_supabase_client()

    # Insert problems into 'problems' table
    # Assumes table columns at least: id, title, description, difficulty, topic, language
    print(f"Inserting {len(problems)} problems into 'problems' table...")
    try:
        # Use upsert so re-running the script is idempotent based on primary key
        response = supabase.table("problems").upsert(problems).execute()
        print("Problems upsert response:", getattr(response, "data", response))
    except Exception as exc:
        raise RuntimeError(f"Failed to insert problems: {exc}") from exc

    # Prepare misconceptions with embeddings (no foreign key linkage for now)
    descriptions = [m.get("description", "") for m in misconceptions]
    print(f"Generating embeddings for {len(descriptions)} misconceptions...")
    embeddings = generate_embeddings(descriptions)

    misconceptions_rows: List[Dict[str, Any]] = []
    for m, emb in zip(misconceptions, embeddings):
        language_field = str(m.get("language", "")).strip()

        row: Dict[str, Any] = {
            "title": m.get("title"),
            "description": m.get("description"),
            "language": language_field,
            "fix": m.get("fix"),
            "embedding": emb,  # 384-dim vector (for pgvector column)
        }
        misconceptions_rows.append(row)

    print(f"Inserting {len(misconceptions_rows)} misconceptions into 'misconceptions' table...")
    try:
        response = supabase.table("misconceptions").upsert(misconceptions_rows).execute()
        print("Misconceptions upsert response:", getattr(response, "data", response))
    except Exception as exc:
        raise RuntimeError(f"Failed to insert misconceptions: {exc}") from exc

    print("Migration to Supabase completed successfully.")


if __name__ == "__main__":
    main()

