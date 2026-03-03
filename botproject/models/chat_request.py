"""
Chat Request Models
Shared Pydantic models for chat-related requests
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AskRequest(BaseModel):
    """Unified chat request model"""
    # Authentication
    user_session_id: Optional[str] = None
    access_token: Optional[str] = None
    user_id: Optional[int] = None
    user_phone: Optional[str] = None
    session_id: Optional[str] = None  # Backward compatibility

    # Chat Context
    chat_session_id: Optional[str] = None

    # User Input
    query: Optional[str] = None
    user_input: Optional[str] = None
    action: Optional[str] = None

    # Service Context
    assistance_type: Optional[str] = None
    insurance_type: Optional[str] = None
    service_type: Optional[str] = None
    model: str = "policy_analysis"

    # File Handling
    file_action: Optional[str] = None

    # Policy/Application Context
    policy_id: Optional[str] = None
    application_id: Optional[str] = None
    edited_answers: Optional[str] = None  # JSON string

    # Financial Data
    vehicle_market_value: Optional[float] = None
    annual_income: Optional[float] = None


class ChatContext(BaseModel):
    """Chat execution context"""
    user_id: int
    user_session_id: Optional[str]
    chat_session_id: str
    is_guest: bool
    access_token: Optional[str]
    user_phone: Optional[str]
    timestamp: str
    was_regenerated: bool = False
    original_user_session_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ChatMetadata(BaseModel):
    """Metadata for chat responses"""
    message_id: Optional[str]
    original_query: Optional[str]
    processed_query: Optional[str]
    user_session_id: Optional[str]
    chat_session_id: Optional[str]
    chat_session_created: bool = False
    chat_session_regenerated: bool = False
    is_guest: bool = False
    active_sessions: int = 0
    conversation_length: int = 0
    session_continuation: bool = False
    context_used: bool = False
    topics_discussed: List[str] = []
    last_user_question: Optional[str] = None
    language_detected: str = "en"
    language_confidence: float = 1.0
    intent: Optional[str] = None
    file_processed: bool = False
    user_session_regenerated: bool = False
    original_user_session_id: Optional[str] = None
    original_chat_session_id: Optional[str] = None
    timestamp: str
