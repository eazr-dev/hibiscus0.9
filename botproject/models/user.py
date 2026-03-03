"""
User profile-related Pydantic models
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class UpdateUserProfileRequest(BaseModel):
    session_id: str
    profile_data: Dict[str, Any]


class UserProfileUpdateRequest(BaseModel):
    user_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    app_platform: Optional[str] = None
    android_version: Optional[str] = None
    ios_version: Optional[str] = None
    language_preference: Optional[str] = None
    interests: Optional[List[str]] = None
    gender: Optional[str] = None
    dob: Optional[str] = None  # Date of birth in YYYY-MM-DD format
    age: Optional[int] = None
    profile_pic: Optional[str] = None  # URL or base64 encoded image


class UserProfileUpdateResponse(BaseModel):
    success: bool
    message: str
    updated_fields: List[str]
    profile: dict
    timestamp: Optional[str] = None
    session_id: Optional[str] = None
    session_regenerated: Optional[bool] = None
    original_session_id: Optional[str] = None


class DeleteAccountRequest(BaseModel):
    session_id: str
    user_id: int
    confirm: bool = True
    reason: Optional[str] = None
