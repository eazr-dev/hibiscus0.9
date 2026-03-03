"""
Centralized Error Handling Module for EAZR Chat API

This module provides:
1. Standardized error codes and messages
2. Custom exception classes
3. Error response models
4. Helper functions for consistent error handling

Usage:
    from core.errors import (
        AppError, ErrorCode, ErrorResponse,
        AuthenticationError, ValidationError, NotFoundError,
        raise_error, create_error_response
    )

    # Raise a custom error
    raise AuthenticationError("Invalid token")

    # Create error response dict
    return create_error_response(ErrorCode.VALIDATION_ERROR, "Invalid input")
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


# ============= Error Codes =============

class ErrorCode(str, Enum):
    """Standardized error codes for the entire application"""

    # Authentication & Authorization (1xxx)
    AUTH_REQUIRED = "AUTH_1001"
    AUTH_INVALID_TOKEN = "AUTH_1002"
    AUTH_TOKEN_EXPIRED = "AUTH_1003"
    AUTH_INVALID_CREDENTIALS = "AUTH_1004"
    AUTH_PERMISSION_DENIED = "AUTH_1005"
    AUTH_SESSION_EXPIRED = "AUTH_1006"
    AUTH_SESSION_INVALID = "AUTH_1007"
    AUTH_USER_NOT_FOUND = "AUTH_1008"
    AUTH_ACCOUNT_LOCKED = "AUTH_1009"
    AUTH_OTP_INVALID = "AUTH_1010"
    AUTH_OTP_EXPIRED = "AUTH_1011"

    # Validation Errors (2xxx)
    VALIDATION_ERROR = "VAL_2001"
    VALIDATION_REQUIRED_FIELD = "VAL_2002"
    VALIDATION_INVALID_FORMAT = "VAL_2003"
    VALIDATION_OUT_OF_RANGE = "VAL_2004"
    VALIDATION_INVALID_TYPE = "VAL_2005"
    VALIDATION_FILE_TOO_LARGE = "VAL_2006"
    VALIDATION_UNSUPPORTED_FILE = "VAL_2007"
    VALIDATION_INVALID_JSON = "VAL_2008"

    # Resource Errors (3xxx)
    NOT_FOUND = "RES_3001"
    NOT_FOUND_USER = "RES_3002"
    NOT_FOUND_CHAT = "RES_3003"
    NOT_FOUND_POLICY = "RES_3004"
    NOT_FOUND_SESSION = "RES_3005"
    NOT_FOUND_MESSAGE = "RES_3006"
    NOT_FOUND_FILE = "RES_3007"
    ALREADY_EXISTS = "RES_3008"
    CONFLICT = "RES_3009"

    # Rate Limiting (4xxx)
    RATE_LIMIT_EXCEEDED = "RATE_4001"
    RATE_LIMIT_OTP = "RATE_4002"
    RATE_LIMIT_API = "RATE_4003"
    RATE_LIMIT_UPLOAD = "RATE_4004"

    # Server Errors (5xxx)
    INTERNAL_ERROR = "SRV_5001"
    DATABASE_ERROR = "SRV_5002"
    EXTERNAL_SERVICE_ERROR = "SRV_5003"
    AI_SERVICE_ERROR = "SRV_5004"
    FILE_PROCESSING_ERROR = "SRV_5005"
    CONFIGURATION_ERROR = "SRV_5006"
    SERVICE_UNAVAILABLE = "SRV_5007"
    TIMEOUT_ERROR = "SRV_5008"

    # WebSocket Errors (6xxx)
    WS_CONNECTION_ERROR = "WS_6001"
    WS_AUTH_REQUIRED = "WS_6002"
    WS_AUTH_FAILED = "WS_6003"
    WS_INVALID_MESSAGE = "WS_6004"
    WS_RATE_LIMITED = "WS_6005"
    WS_SESSION_ERROR = "WS_6006"

    # Business Logic Errors (7xxx)
    BUSINESS_RULE_VIOLATION = "BIZ_7001"
    POLICY_ANALYSIS_FAILED = "BIZ_7002"
    DOCUMENT_PROCESSING_FAILED = "BIZ_7003"
    PAYMENT_FAILED = "BIZ_7004"
    SUBSCRIPTION_REQUIRED = "BIZ_7005"

    # Policy Upload Errors (8xxx)
    POLICY_NAME_MISMATCH = "POL_8001"
    POLICY_HOLDER_NOT_FOUND = "POL_8002"
    POLICY_INVALID_DOCUMENT = "POL_8003"
    POLICY_UPLOAD_FAILED = "POL_8004"
    POLICY_ALREADY_EXISTS = "POL_8005"
    POLICY_EXPIRED = "POL_8006"

    # Bill Audit Errors (9xxx)
    BILL_UPLOAD_FAILED = "BILL_9001"
    BILL_INVALID_FILE_TYPE = "BILL_9002"
    BILL_EXTRACTION_FAILED = "BILL_9003"
    BILL_ANALYSIS_FAILED = "BILL_9004"
    BILL_NOT_FOUND = "BILL_9005"
    BILL_POLICY_NOT_FOUND = "BILL_9006"
    BILL_POLICY_MISMATCH = "BILL_9007"
    BILL_REPORT_GENERATION_FAILED = "BILL_9008"
    BILL_DISPUTE_GENERATION_FAILED = "BILL_9009"
    BILL_TOO_MANY_FILES = "BILL_9010"

    # HBF Financing Errors (10xxx)
    HBF_NOT_ELIGIBLE = "HBF_10001"
    HBF_AMOUNT_OUT_OF_RANGE = "HBF_10002"
    HBF_LOAN_NOT_FOUND = "HBF_10003"
    HBF_OFFER_NOT_FOUND = "HBF_10004"
    HBF_INVALID_STATUS = "HBF_10005"
    HBF_SCORE_CALCULATION_FAILED = "HBF_10007"


# ============= Error Messages =============

ERROR_MESSAGES: Dict[ErrorCode, str] = {
    # Authentication
    ErrorCode.AUTH_REQUIRED: "Authentication required. Please login to continue.",
    ErrorCode.AUTH_INVALID_TOKEN: "Invalid authentication token.",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Your session has expired. Please login again.",
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid username or password.",
    ErrorCode.AUTH_PERMISSION_DENIED: "You don't have permission to perform this action.",
    ErrorCode.AUTH_SESSION_EXPIRED: "Your session has expired. Please login again.",
    ErrorCode.AUTH_SESSION_INVALID: "Invalid session. Please login again.",
    ErrorCode.AUTH_USER_NOT_FOUND: "User not found.",
    ErrorCode.AUTH_ACCOUNT_LOCKED: "Your account has been locked. Please contact support.",
    ErrorCode.AUTH_OTP_INVALID: "Invalid OTP. Please try again.",
    ErrorCode.AUTH_OTP_EXPIRED: "OTP has expired. Please request a new one.",

    # Validation
    ErrorCode.VALIDATION_ERROR: "Invalid input data.",
    ErrorCode.VALIDATION_REQUIRED_FIELD: "Required field is missing.",
    ErrorCode.VALIDATION_INVALID_FORMAT: "Invalid data format.",
    ErrorCode.VALIDATION_OUT_OF_RANGE: "Value is out of allowed range.",
    ErrorCode.VALIDATION_INVALID_TYPE: "Invalid data type.",
    ErrorCode.VALIDATION_FILE_TOO_LARGE: "File size exceeds the maximum allowed limit.",
    ErrorCode.VALIDATION_UNSUPPORTED_FILE: "File type is not supported.",
    ErrorCode.VALIDATION_INVALID_JSON: "Invalid JSON format.",

    # Resource
    ErrorCode.NOT_FOUND: "The requested resource was not found.",
    ErrorCode.NOT_FOUND_USER: "User not found.",
    ErrorCode.NOT_FOUND_CHAT: "Chat session not found.",
    ErrorCode.NOT_FOUND_POLICY: "Policy not found.",
    ErrorCode.NOT_FOUND_SESSION: "Session not found.",
    ErrorCode.NOT_FOUND_MESSAGE: "Message not found.",
    ErrorCode.NOT_FOUND_FILE: "File not found.",
    ErrorCode.ALREADY_EXISTS: "Resource already exists.",
    ErrorCode.CONFLICT: "Resource conflict detected.",

    # Rate Limiting
    ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please try again later.",
    ErrorCode.RATE_LIMIT_OTP: "Too many OTP requests. Please wait before trying again.",
    ErrorCode.RATE_LIMIT_API: "API rate limit exceeded. Please slow down.",
    ErrorCode.RATE_LIMIT_UPLOAD: "Upload rate limit exceeded. Please wait.",

    # Server
    ErrorCode.INTERNAL_ERROR: "An internal error occurred. Please try again later.",
    ErrorCode.DATABASE_ERROR: "Database error. Please try again later.",
    ErrorCode.EXTERNAL_SERVICE_ERROR: "External service error. Please try again later.",
    ErrorCode.AI_SERVICE_ERROR: "AI service temporarily unavailable. Please try again.",
    ErrorCode.FILE_PROCESSING_ERROR: "Error processing file. Please try again.",
    ErrorCode.CONFIGURATION_ERROR: "Server configuration error.",
    ErrorCode.SERVICE_UNAVAILABLE: "Service temporarily unavailable.",
    ErrorCode.TIMEOUT_ERROR: "Request timed out. Please try again.",

    # WebSocket
    ErrorCode.WS_CONNECTION_ERROR: "WebSocket connection error.",
    ErrorCode.WS_AUTH_REQUIRED: "WebSocket authentication required.",
    ErrorCode.WS_AUTH_FAILED: "WebSocket authentication failed.",
    ErrorCode.WS_INVALID_MESSAGE: "Invalid WebSocket message format.",
    ErrorCode.WS_RATE_LIMITED: "WebSocket rate limit exceeded.",
    ErrorCode.WS_SESSION_ERROR: "WebSocket session error.",

    # Business
    ErrorCode.BUSINESS_RULE_VIOLATION: "Business rule violation.",
    ErrorCode.POLICY_ANALYSIS_FAILED: "Failed to analyze policy. Please try again.",
    ErrorCode.DOCUMENT_PROCESSING_FAILED: "Document processing failed.",
    ErrorCode.PAYMENT_FAILED: "Payment processing failed.",
    ErrorCode.SUBSCRIPTION_REQUIRED: "Subscription required for this feature.",

    # Policy Upload
    ErrorCode.POLICY_NAME_MISMATCH: "The provided name does not match the policy holder name in the document.",
    ErrorCode.POLICY_HOLDER_NOT_FOUND: "Unable to verify policy. Policy holder name could not be extracted from the document.",
    ErrorCode.POLICY_INVALID_DOCUMENT: "Invalid policy document. Please upload a valid insurance policy.",
    ErrorCode.POLICY_UPLOAD_FAILED: "Failed to upload policy. Please try again.",
    ErrorCode.POLICY_ALREADY_EXISTS: "This policy has already been uploaded.",
    ErrorCode.POLICY_EXPIRED: "This policy has expired.",

    # Bill Audit
    ErrorCode.BILL_UPLOAD_FAILED: "Failed to upload bill. Please try again.",
    ErrorCode.BILL_INVALID_FILE_TYPE: "Unsupported file type. Please upload images (JPG, PNG, WEBP) or PDF files.",
    ErrorCode.BILL_EXTRACTION_FAILED: "Failed to extract text from bill. Please ensure the image/PDF is clear and readable.",
    ErrorCode.BILL_ANALYSIS_FAILED: "Bill analysis failed. Please try again later.",
    ErrorCode.BILL_NOT_FOUND: "Bill audit not found.",
    ErrorCode.BILL_POLICY_NOT_FOUND: "The specified policy was not found in your policy locker.",
    ErrorCode.BILL_POLICY_MISMATCH: "The bill type does not match the policy type.",
    ErrorCode.BILL_REPORT_GENERATION_FAILED: "Failed to generate audit report.",
    ErrorCode.BILL_DISPUTE_GENERATION_FAILED: "Failed to generate dispute letter.",
    ErrorCode.BILL_TOO_MANY_FILES: "Too many files uploaded. Maximum 10 files per audit.",

    # HBF Financing
    ErrorCode.HBF_NOT_ELIGIBLE: "You are not eligible for hospital bill financing at this time.",
    ErrorCode.HBF_AMOUNT_OUT_OF_RANGE: "Requested amount is outside the allowed range.",
    ErrorCode.HBF_LOAN_NOT_FOUND: "Loan application not found.",
    ErrorCode.HBF_OFFER_NOT_FOUND: "Selected offer not found or has expired.",
    ErrorCode.HBF_INVALID_STATUS: "Invalid loan status for this operation.",
    ErrorCode.HBF_SCORE_CALCULATION_FAILED: "Failed to calculate eligibility score. Please try again.",
}


# ============= HTTP Status Mapping =============

ERROR_HTTP_STATUS: Dict[ErrorCode, int] = {
    # Authentication - 401/403
    ErrorCode.AUTH_REQUIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTH_SESSION_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_SESSION_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.AUTH_ACCOUNT_LOCKED: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTH_OTP_INVALID: status.HTTP_400_BAD_REQUEST,
    ErrorCode.AUTH_OTP_EXPIRED: status.HTTP_400_BAD_REQUEST,

    # Validation - 400/413/415
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VALIDATION_REQUIRED_FIELD: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VALIDATION_INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VALIDATION_OUT_OF_RANGE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VALIDATION_INVALID_TYPE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VALIDATION_FILE_TOO_LARGE: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    ErrorCode.VALIDATION_UNSUPPORTED_FILE: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ErrorCode.VALIDATION_INVALID_JSON: status.HTTP_400_BAD_REQUEST,

    # Resource - 404/409
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_USER: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_CHAT: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_POLICY: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_SESSION: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_MESSAGE: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_FILE: status.HTTP_404_NOT_FOUND,
    ErrorCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,

    # Rate Limiting - 429
    ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.RATE_LIMIT_OTP: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.RATE_LIMIT_API: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.RATE_LIMIT_UPLOAD: status.HTTP_429_TOO_MANY_REQUESTS,

    # Server - 500/502/503/504
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.EXTERNAL_SERVICE_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.AI_SERVICE_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.FILE_PROCESSING_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,

    # WebSocket - 400
    ErrorCode.WS_CONNECTION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.WS_AUTH_REQUIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.WS_AUTH_FAILED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.WS_INVALID_MESSAGE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.WS_RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.WS_SESSION_ERROR: status.HTTP_400_BAD_REQUEST,

    # Business - 400/402/422
    ErrorCode.BUSINESS_RULE_VIOLATION: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.POLICY_ANALYSIS_FAILED: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.DOCUMENT_PROCESSING_FAILED: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.PAYMENT_FAILED: status.HTTP_402_PAYMENT_REQUIRED,
    ErrorCode.SUBSCRIPTION_REQUIRED: status.HTTP_402_PAYMENT_REQUIRED,

    # Policy Upload - 400
    ErrorCode.POLICY_NAME_MISMATCH: status.HTTP_400_BAD_REQUEST,
    ErrorCode.POLICY_HOLDER_NOT_FOUND: status.HTTP_400_BAD_REQUEST,
    ErrorCode.POLICY_INVALID_DOCUMENT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.POLICY_UPLOAD_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.POLICY_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.POLICY_EXPIRED: status.HTTP_400_BAD_REQUEST,

    # Bill Audit - 400/404/500
    ErrorCode.BILL_UPLOAD_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.BILL_INVALID_FILE_TYPE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BILL_EXTRACTION_FAILED: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.BILL_ANALYSIS_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.BILL_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.BILL_POLICY_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.BILL_POLICY_MISMATCH: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BILL_REPORT_GENERATION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.BILL_DISPUTE_GENERATION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.BILL_TOO_MANY_FILES: status.HTTP_400_BAD_REQUEST,

    # HBF - 400/404/422
    ErrorCode.HBF_NOT_ELIGIBLE: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.HBF_AMOUNT_OUT_OF_RANGE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.HBF_LOAN_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.HBF_OFFER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.HBF_INVALID_STATUS: status.HTTP_400_BAD_REQUEST,
    ErrorCode.HBF_SCORE_CALCULATION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


# ============= Response Models =============

class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    value: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response model for all API endpoints"""
    success: bool = False
    error_code: str = Field(..., description="Unique error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    path: Optional[str] = Field(None, description="API endpoint path")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "VAL_2001",
                "message": "Invalid input data.",
                "details": [
                    {"field": "email", "message": "Invalid email format", "value": "invalid-email"}
                ],
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_abc123",
                "path": "/api/v1/users"
            }
        }


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"user_id": 123, "name": "John"},
                "message": "User created successfully",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


# ============= Custom Exception Classes =============

class AppError(Exception):
    """Base exception class for all application errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
        original_error: Optional[Exception] = None
    ):
        self.error_code = error_code
        self.message = message or ERROR_MESSAGES.get(error_code, "An error occurred")
        self.details = details
        self.original_error = original_error
        self.http_status = ERROR_HTTP_STATUS.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "success": False,
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.utcnow().isoformat()
        }

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.http_status,
            detail=self.to_dict()
        )


class AuthenticationError(AppError):
    """Authentication-related errors"""
    def __init__(self, message: Optional[str] = None, error_code: ErrorCode = ErrorCode.AUTH_REQUIRED):
        super().__init__(error_code=error_code, message=message)


class ValidationError(AppError):
    """Validation errors"""
    def __init__(
        self,
        message: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR
    ):
        details = None
        if field:
            details = [{"field": field, "message": message or "Invalid value", "value": value}]
        super().__init__(error_code=error_code, message=message, details=details)


class NotFoundError(AppError):
    """Resource not found errors"""
    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"
        super().__init__(error_code=ErrorCode.NOT_FOUND, message=message)


class RateLimitError(AppError):
    """Rate limiting errors"""
    def __init__(self, message: Optional[str] = None, retry_after: Optional[int] = None):
        details = None
        if retry_after:
            details = [{"field": "retry_after", "message": f"Retry after {retry_after} seconds", "value": retry_after}]
        super().__init__(error_code=ErrorCode.RATE_LIMIT_EXCEEDED, message=message, details=details)


class DatabaseError(AppError):
    """Database errors"""
    def __init__(self, message: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message or "Database operation failed",
            original_error=original_error
        )


class ExternalServiceError(AppError):
    """External service errors (AI, payment, etc.)"""
    def __init__(self, service: str = "External service", message: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=message or f"{service} is temporarily unavailable"
        )


class AIServiceError(AppError):
    """AI service specific errors"""
    def __init__(self, message: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.AI_SERVICE_ERROR,
            message=message or "AI service temporarily unavailable. Please try again."
        )


class FileProcessingError(AppError):
    """File processing errors"""
    def __init__(self, filename: Optional[str] = None, message: Optional[str] = None):
        msg = message or "Error processing file"
        if filename:
            msg = f"Error processing file '{filename}'"
        super().__init__(error_code=ErrorCode.FILE_PROCESSING_ERROR, message=msg)


class WebSocketError(AppError):
    """WebSocket specific errors"""
    def __init__(self, error_code: ErrorCode = ErrorCode.WS_CONNECTION_ERROR, message: Optional[str] = None):
        super().__init__(error_code=error_code, message=message)


class BusinessError(AppError):
    """Business logic errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION):
        super().__init__(error_code=error_code, message=message)


# ============= Helper Functions =============

def create_error_response(
    error_code: Union[ErrorCode, str],
    message: Optional[str] = None,
    details: Optional[List[Dict[str, Any]]] = None,
    path: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.

    Args:
        error_code: Error code (ErrorCode enum or string)
        message: Custom error message (optional)
        details: Additional error details
        path: API endpoint path
        request_id: Request tracking ID

    Returns:
        Dictionary with standardized error response
    """
    if isinstance(error_code, str):
        code_str = error_code
        default_message = "An error occurred"
    else:
        code_str = error_code.value
        default_message = ERROR_MESSAGES.get(error_code, "An error occurred")

    return {
        "success": False,
        "error_code": code_str,
        "message": message or default_message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
        "path": path,
        "request_id": request_id
    }


def create_success_response(
    data: Any = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response dictionary.

    Args:
        data: Response data
        message: Success message

    Returns:
        Dictionary with standardized success response
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }


def raise_error(
    error_code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Raise an HTTPException with standardized error format.

    Args:
        error_code: Error code from ErrorCode enum
        message: Custom error message
        details: Additional error details

    Raises:
        HTTPException with proper status code and error details
    """
    http_status = ERROR_HTTP_STATUS.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    error_response = create_error_response(error_code, message, details)
    raise HTTPException(status_code=http_status, detail=error_response)


def handle_exception(
    error: Exception,
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    log_error: bool = True
) -> Dict[str, Any]:
    """
    Handle an exception and return a standardized error response.

    Args:
        error: The exception to handle
        default_code: Default error code if not an AppError
        log_error: Whether to log the error

    Returns:
        Standardized error response dictionary
    """
    if log_error:
        logger.error(f"Exception: {type(error).__name__}: {str(error)}", exc_info=True)

    if isinstance(error, AppError):
        return error.to_dict()
    elif isinstance(error, HTTPException):
        return create_error_response(
            default_code,
            message=str(error.detail) if error.detail else None
        )
    else:
        return create_error_response(
            default_code,
            message="An unexpected error occurred. Please try again later."
        )


# ============= WebSocket Error Helpers =============

def create_ws_error(
    error_code: Union[ErrorCode, str],
    message: Optional[str] = None,
    recoverable: bool = True
) -> Dict[str, Any]:
    """
    Create a WebSocket error message.

    Args:
        error_code: Error code
        message: Error message
        recoverable: Whether the client can recover from this error

    Returns:
        WebSocket error message dictionary
    """
    if isinstance(error_code, ErrorCode):
        code_str = error_code.value
        default_message = ERROR_MESSAGES.get(error_code, "WebSocket error")
    else:
        code_str = error_code
        default_message = "WebSocket error"

    return {
        "type": "error",
        "error_code": code_str,
        "error": message or default_message,
        "recoverable": recoverable,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============= Validation Helpers =============

def validate_required(value: Any, field_name: str) -> None:
    """Validate that a required field is present"""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            error_code=ErrorCode.VALIDATION_REQUIRED_FIELD
        )


def validate_file_size(file_size: int, max_size_mb: int = 10, field_name: str = "file") -> None:
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise ValidationError(
            message=f"File size exceeds maximum allowed size of {max_size_mb}MB",
            field=field_name,
            value=f"{file_size / (1024*1024):.2f}MB",
            error_code=ErrorCode.VALIDATION_FILE_TOO_LARGE
        )


def validate_file_type(
    filename: str,
    allowed_types: List[str],
    field_name: str = "file"
) -> None:
    """Validate file type by extension"""
    if not filename:
        return

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in [t.lower().lstrip('.') for t in allowed_types]:
        raise ValidationError(
            message=f"File type '.{ext}' is not supported. Allowed: {', '.join(allowed_types)}",
            field=field_name,
            value=ext,
            error_code=ErrorCode.VALIDATION_UNSUPPORTED_FILE
        )
