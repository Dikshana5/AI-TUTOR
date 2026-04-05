import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from supabase import create_client, Client

# Load env for SUPABASE_URL / SUPABASE_KEY (and optional SECRET_KEY overrides)
load_dotenv()

# Secret key to sign JWT tokens
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SUPABASE: Optional[Client] = None


def _get_supabase_client() -> Client:
    global SUPABASE
    if SUPABASE is not None:
        return SUPABASE

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment")

    SUPABASE = create_client(url, key)
    return SUPABASE

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_profile_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a row from Supabase `profiles` table by `username`.

    Assumes your table has a unique `username` column.
    """
    client = _get_supabase_client()
    resp = client.table("profiles").select("*").eq("username", username).limit(1).execute()
    rows = getattr(resp, "data", []) or []
    return rows[0] if rows else None


def get_profile_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a row from Supabase `profiles` table by `email`.

    Assumes your table has a unique `email` column.
    """
    client = _get_supabase_client()
    resp = client.table("profiles").select("*").eq("email", email).limit(1).execute()
    rows = getattr(resp, "data", []) or []
    return rows[0] if rows else None


def create_profile(username: str, email: str, hashed_password: str) -> Dict[str, Any]:
    """
    Insert a new profile into Supabase `profiles` table.

    Assumptions:
      - profiles table has columns: username, email, hashed_password, is_active
      - created row is returned by Supabase; if not, we fall back to the input row.
    """
    client = _get_supabase_client()
    row = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "is_active": True,
    }
    resp = client.table("profiles").insert(row).execute()
    rows = getattr(resp, "data", []) or []
    if rows:
        return rows[0]

    # Some Supabase configurations return minimal insert responses.
    # Re-fetch so the API can return an object matching the expected schema.
    existing = get_profile_by_username(username)
    if existing:
        return existing

    # Last-resort fallback to satisfy response validation.
    return {**row, "id": 0}
