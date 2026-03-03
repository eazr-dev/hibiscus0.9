"""
Core application configuration and setup
"""
from .config import settings, get_llm_instance, get_rag_chain
from .dependencies import (
    get_session_data,
    verify_token,
    REDIS_AVAILABLE,
    MONGODB_AVAILABLE,
    LANGGRAPH_AVAILABLE,
    VOICE_AVAILABLE,
    MULTILINGUAL_AVAILABLE
)
from .errors import (
    ErrorCode,
    ErrorResponse,
    APIResponse,
    AppError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    AIServiceError,
    FileProcessingError,
    WebSocketError,
    BusinessError,
    create_error_response,
    create_success_response,
    raise_error,
    handle_exception,
    create_ws_error,
    validate_required,
    validate_file_size,
    validate_file_type
)

__all__ = [
    # Config
    "settings",
    "get_llm_instance",
    "get_rag_chain",
    "get_session_data",
    "verify_token",
    # Feature flags
    "REDIS_AVAILABLE",
    "MONGODB_AVAILABLE",
    "LANGGRAPH_AVAILABLE",
    "VOICE_AVAILABLE",
    "MULTILINGUAL_AVAILABLE",
    # Error handling
    "ErrorCode",
    "ErrorResponse",
    "APIResponse",
    "AppError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "DatabaseError",
    "ExternalServiceError",
    "AIServiceError",
    "FileProcessingError",
    "WebSocketError",
    "BusinessError",
    "create_error_response",
    "create_success_response",
    "raise_error",
    "handle_exception",
    "create_ws_error",
    "validate_required",
    "validate_file_size",
    "validate_file_type"
]
