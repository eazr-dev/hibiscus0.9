"""
Enhanced authentication verification utilities for API endpoints
Validates access tokens, user IDs, and phone numbers for security
"""
import logging
from typing import Optional, Tuple, Dict
from session_security.token_genrations import verify_jwt_token

logger = logging.getLogger(__name__)


def verify_user_authentication(
    access_token: Optional[str],
    user_id: Optional[int],
    user_phone: Optional[str] = None,
    email: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Comprehensive verification of user authentication credentials

    This function validates:
    1. Access token is present and valid (JWT verification)
    2. User ID matches the token payload
    3. Phone number OR email matches the token payload (supports both OTP and OAuth users)

    Args:
        access_token: JWT access token from the user
        user_id: User ID claimed by the request
        user_phone: Phone number claimed by the request (for OTP users)
        email: Email claimed by the request (for OAuth users)

    Returns:
        Tuple of (is_valid, error_message, token_payload)
        - is_valid: True if authentication is valid, False otherwise
        - error_message: Description of the error if validation failed
        - token_payload: Decoded JWT payload if valid, None otherwise

    Example:
        >>> is_valid, error, payload = verify_user_authentication(token, user_id, phone=phone)
        >>> is_valid, error, payload = verify_user_authentication(token, user_id, email=email)
        >>> if not is_valid:
        >>>     return {"error": error}
    """

    # Step 1: Check if access token is provided
    if not access_token:
        logger.warning("Authentication failed: No access token provided")
        return False, "Access token is required for authenticated requests", None

    # Step 2: Verify JWT token validity
    verification_result = verify_jwt_token(access_token)

    if not verification_result.get("valid"):
        error_msg = verification_result.get("error", "Invalid token")
        logger.warning(f"JWT verification failed: {error_msg}")

        # Provide user-friendly error messages
        if "expired" in error_msg.lower():
            return False, "Your session has expired. Please login again.", None
        elif "invalid" in error_msg.lower():
            return False, "Invalid authentication token. Please login again.", None
        else:
            return False, f"Authentication failed: {error_msg}", None

    # Step 3: Extract payload from verified token
    token_payload = verification_result.get("payload", {})

    if not token_payload:
        logger.error("JWT payload is empty after successful verification")
        return False, "Invalid token payload", None

    # Step 4: Verify user_id matches token
    token_user_id = token_payload.get("id")

    if user_id and token_user_id:
        if int(user_id) != int(token_user_id):
            logger.warning(
                f"User ID mismatch: Request user_id={user_id}, "
                f"Token user_id={token_user_id}"
            )
            return False, "User ID does not match authentication token", None
    elif user_id and not token_user_id:
        logger.warning("Token does not contain user ID")
        return False, "Invalid token: missing user ID", None

    # Step 5: Verify phone number matches token (if provided)
    token_phone = token_payload.get("contactNumber")
    token_email = token_payload.get("email")

    # For OTP users: verify phone number
    if user_phone and token_phone:
        # Normalize phone numbers (remove spaces, dashes, etc.)
        normalized_request_phone = ''.join(filter(str.isdigit, user_phone))
        normalized_token_phone = ''.join(filter(str.isdigit, token_phone))

        if normalized_request_phone != normalized_token_phone:
            logger.warning(
                f"Phone number mismatch: Request phone={user_phone}, "
                f"Token phone={token_phone}"
            )
            return False, "Phone number does not match authentication token", None

    # For OAuth users: verify email (optional check)
    if email and token_email:
        if email.lower() != token_email.lower():
            logger.warning(
                f"Email mismatch: Request email={email}, "
                f"Token email={token_email}"
            )
            return False, "Email does not match authentication token", None

    # All validations passed
    logger.info(
        f"Authentication verified successfully for user_id={token_user_id}, "
        f"phone={token_phone}, email={token_email}"
    )

    return True, None, token_payload


def create_auth_error_response(error_message: str, session_id: str = None) -> Dict:
    """
    Create a standardized error response for authentication failures

    Args:
        error_message: The error message to return
        session_id: Optional session ID to include in response

    Returns:
        Standardized error response dictionary
    """
    from datetime import datetime

    response = {
        "status": "error",
        "timestamp": datetime.now().isoformat(),
        "response_type": "authentication_error",
        "data": {
            "type": "authentication_error",
            "error": error_message,
            "message": error_message,
            "action": "auth_required",
            "show_service_options": False,
            "quick_actions": [
                {"title": "Login", "action": "login"},
                {"title": "Sign Up", "action": "signup"}
            ]
        },
        "metadata": {
            "intent": "authentication_failed",
            "requires_login": True
        }
    }

    if session_id:
        response["session_id"] = session_id
        response["chat_session_id"] = session_id

    return response


def should_verify_token(
    user_session_id: Optional[str],
    access_token: Optional[str],
    user_id: Optional[int]
) -> bool:
    """
    Determine if token verification should be performed

    Token verification is required when:
    - User session ID is provided (indicates authenticated request)
    - Access token is provided
    - User ID is provided and > 0

    Args:
        user_session_id: User session identifier
        access_token: JWT access token
        user_id: User ID

    Returns:
        True if token should be verified, False otherwise (guest user)
    """
    # If any authentication credential is provided, verify it
    has_auth_credentials = (
        (user_session_id is not None) or
        (access_token is not None) or
        (user_id is not None and user_id > 0)
    )

    return has_auth_credentials
