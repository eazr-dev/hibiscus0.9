"""
Authentication-related Pydantic models
"""
from pydantic import BaseModel
from typing import Optional


class AppVersionInfo(BaseModel):
    android_version: Optional[str] = None
    ios_version: Optional[str] = None
    platform: Optional[str] = None


class SendOTPRequest(BaseModel):
    phone: str


class SendOTPResponse(BaseModel):
    success: bool
    message: str


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    app_version: Optional[AppVersionInfo] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    session_id: str  # user_session_id (authentication)
    chat_session_id: str  # NEW: for conversations
    user_phone: str
    user_name: str  # e.g., hrushikesh282
    full_name: Optional[str] = None  # e.g., Hrushikesh Tembe
    access_token: str
    user_id: int
    profile_created: bool


class CheckSessionRequest(BaseModel):
    session_id: str


class OAuthLoginRequest(BaseModel):
    """OAuth login request with provider and idToken"""
    provider: str  # 'google' or 'apple'
    idToken: str
    app_version: Optional[AppVersionInfo] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class OAuthLoginResponse(BaseModel):
    """OAuth login response"""
    success: bool
    message: str
    session_id: str  # user_session_id (authentication)
    chat_session_id: str  # for conversations
    user_phone: Optional[str] = None  # None for OAuth users
    user_name: str  # e.g., hrushikesh282
    full_name: Optional[str] = None  # e.g., Hrushikesh Tembe
    access_token: str
    user_id: int
    profile_created: bool
    email: Optional[str] = None
    provider: str
