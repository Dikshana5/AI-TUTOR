from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

# --- 1. User Request Model ---
class DetectRequest(BaseModel):
    """
    Request payload sent from the frontend to the /analyze endpoint.
    """
    user_id: str
    session_id: str
    content: str = Field(..., min_length=1, description="The code or text to analyze")
    content_type: str = "code"  # e.g., "code" or "text"
    language: str = "python"    # Defaults to Python, but supports java/cpp


# --- 2. Diagnostic Components ---
class SemanticMatch(BaseModel):
    """
    Top semantic match from the FAISS index (problem or misconception).
    """
    id: str
    title: str
    score: float


# --- 3. Master Server Response Model ---
class DetectResponse(BaseModel):
    """
    Unified response model used by:
      - FastAPI /analyze endpoint
      - Adaptive engine.get_next_step
      - Streamlit/React frontends
    """
    status: str = "success"
    # NOTE: plural form to match detector.run_detection and engine.get_next_step
    error_types: List[str] = []
    primary_concept: Optional[str] = None
    # Free-form list of diagnosis entries (static + LLM), each a small dict.
    diagnosis: List[Dict[str, Any]] = []
    # Single best semantic match (problem or misconception), if any.
    semantic_top_match: Optional[SemanticMatch] = None
    confidence: float = 0.0
    # Future-proofing: metadata for timing, token usage, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        # Allows Pydantic to read data from database ORM objects later
        from_attributes = True

# --- 4. Database Models ---
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

# --- 5. Auth Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None