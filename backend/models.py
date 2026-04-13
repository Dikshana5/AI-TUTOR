from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

# --- 1. User Request Model ---
class DetectRequest(BaseModel):
    """
    Request payload sent from the frontend to the /analyze endpoint.
    """
    user_id: str
    session_id: str
    content: str = Field(..., min_length=1, description="The code or text to analyze")
    content_type: str = "code"  # e.g., "code" or "text"
    language: str = "python"    # Supports python/java/cpp

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
    Unified response model used by FastAPI, Adaptive Engine, and React Frontend.
    """
    status: str = "success"
    error_types: List[str] = []
    primary_concept: Optional[str] = None
    diagnosis: List[Dict[str, Any]] = []
    semantic_top_match: Optional[SemanticMatch] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

# --- 4. Auth Schemas (Pydantic only) ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(UserBase):
    id: str
    is_active: bool = True

    class Config:
        from_attributes = True

class User(UserBase):
    id: str
    is_active: bool = True

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class TokenData(BaseModel):
    email: Optional[str] = None
