"""
Admin Models - Pydantic models for admin endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= AUTHENTICATION MODELS =============

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    message: str


class QRLoginGenerateResponse(BaseModel):
    success: bool
    session_id: str
    qr_code: str
    expires_in: int


class QRLoginScanRequest(BaseModel):
    session_id: str
    phone: str


class QRLoginStatusResponse(BaseModel):
    success: bool
    status: str
    phone: Optional[str] = None
    approved: bool = False
    token: Optional[str] = None


class AuthorizedPhoneRequest(BaseModel):
    phone: str
    admin_name: Optional[str] = None


class PhoneStatusUpdateRequest(BaseModel):
    phone: str
    status: str  # "active" or "inactive"


# ============= USER MANAGEMENT MODELS =============

class UserListFilter(BaseModel):
    limit: int = 50
    skip: int = 0
    status: Optional[str] = None  # "active" or "inactive"


class UserUpdateRequest(BaseModel):
    user_name: Optional[str] = None
    phone: Optional[str] = None
    language_preference: Optional[str] = None


# ============= MODEL CONFIG MODELS =============

class ModelConfigResponse(BaseModel):
    success: bool
    config: Dict[str, Any]


class ModelSwitchRequest(BaseModel):
    force_model: str  # "primary" or "fallback"


# ============= PROMPT MANAGEMENT MODELS =============

class PromptTemplate(BaseModel):
    template_name: str
    prompt_text: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class PromptSaveRequest(BaseModel):
    template: str
    prompt: str


class PromptTestRequest(BaseModel):
    system_prompt: str
    user_message: str
    model: str = "primary"


class PromptTestResponse(BaseModel):
    success: bool
    response: str
    model: str
    time: int  # milliseconds
    tokens: int


# ============= CONVERSATION MODELS =============

class SendMessageRequest(BaseModel):
    user_id: int
    message: str
    session_id: Optional[str] = None


# ============= POLICY APPLICATION MODELS =============

class PolicyApplicationFilter(BaseModel):
    limit: int = 50
    skip: int = 0
    status: Optional[str] = None


# ============= ACTIVITY MODELS =============

class ActivityFilter(BaseModel):
    limit: int = 100
    skip: int = 0
    activity_type: Optional[str] = None
    user_id: Optional[int] = None


# ============= ANALYTICS MODELS =============

class DailyMetric(BaseModel):
    date: str
    users: int = 0
    messages: int = 0


class AdminStatsResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    timestamp: str


class AnalyticsResponse(BaseModel):
    success: bool
    analytics: Dict[str, Any]
    timestamp: str
