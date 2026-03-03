"""
Insurance-related Pydantic models
"""
from pydantic import BaseModel
from typing import Optional


class ClaimGuidanceRequest(BaseModel):
    query: str
    session_id: str
    access_token: str
    user_id: int
    insurance_type: Optional[str] = None  # health, motor, life, etc.
