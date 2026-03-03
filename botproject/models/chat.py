"""
Chat and conversation-related Pydantic models
"""
from pydantic import BaseModel
from typing import Optional


class ServiceSelectionRequest(BaseModel):
    session_id: str
    access_token: str
    user_id: int


class QueryInput(BaseModel):
    query: str
    session_id: str = "default_session"
    user_phone: Optional[str] = None
    email: Optional[str] = None  # Support OAuth users with email
    access_token: str
    user_id: int
    # Enhanced chatbot fields
    action: Optional[str] = None
    user_input: Optional[str] = None
    assistance_type: Optional[str] = None
    insurance_type: Optional[str] = None
    service_type: Optional[str] = None
    # File-related fields
    file_action: Optional[str] = None  # "analyze_insurance", "analyze_pdf", etc.
    vehicle_market_value: Optional[float] = None
    annual_income: Optional[float] = None


class QuickActionRequest(BaseModel):
    session_id: str
    action: str  # check_balance, view_transactions, etc.
    access_token: str
    user_id: int


class ChatbotContinue(BaseModel):
    session_id: str
    chatbot_type: str
    user_input: str
    access_token: Optional[str] = None
    user_id: Optional[int] = None
    sub_type: Optional[str] = None


class ChatHistoryRequest(BaseModel):
    session_id: str
    limit: Optional[int] = 10


class SearchChatRequest(BaseModel):
    session_id: str
    query: str
    limit: Optional[int] = 5


class ClearChatRequest(BaseModel):
    session_id: str
    confirm: bool = False


class UpdateChatTitleRequest(BaseModel):
    session_id: str
    new_title: str
    user_id: int


class LoadChatRequest(BaseModel):
    session_id: str
    user_id: int
    message_limit: Optional[int] = 100


class DeleteChatRequest(BaseModel):
    session_id: str
    user_id: int
    hard_delete: Optional[bool] = False


class SearchChatsRequest(BaseModel):
    user_id: int
    search_query: str
    limit: Optional[int] = 20


class ClearUserChatRequest(BaseModel):
    user_id: int
    session_id: str  # For session validation
    confirm: bool = True


class RegenerateReportRequest(BaseModel):
    report_id: str
    user_id: int
    access_token: str
    chat_session_id: Optional[str] = None


class RegenerateSectionRequest(BaseModel):
    report_id: str
    section_name: str  # e.g., "gap_analysis", "recommendations", "coverage_gaps"
    user_id: int
    access_token: str
    chat_session_id: Optional[str] = None
    additional_instructions: Optional[str] = None  # Optional custom instructions for regeneration
