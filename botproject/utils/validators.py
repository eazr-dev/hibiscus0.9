"""
Validators
Common validation functions for user input and data
"""

import re
from typing import Any
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address string

    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email:
        return False

    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))

        if not is_valid:
            logger.debug(f"Invalid email format: {email}")

        return is_valid
    except Exception as e:
        logger.error(f"Error validating email: {e}")
        return False


def validate_otp(otp: str) -> bool:
    """
    Validate OTP is 4-6 digits

    Args:
        otp: OTP string

    Returns:
        bool: True if valid OTP format, False otherwise
    """
    if not otp:
        return False

    try:
        is_valid = otp.isdigit() and 4 <= len(otp) <= 6

        if not is_valid:
            logger.debug(f"Invalid OTP format: {otp}")

        return is_valid
    except Exception as e:
        logger.error(f"Error validating OTP: {e}")
        return False


def validate_user_id(user_id: Any) -> bool:
    """
    Validate user ID is positive integer

    Args:
        user_id: User ID (can be string or int)

    Returns:
        bool: True if valid positive integer, False otherwise
    """
    try:
        uid = int(user_id)
        is_valid = uid > 0

        if not is_valid:
            logger.debug(f"Invalid user ID: {user_id}")

        return is_valid
    except Exception as e:
        logger.debug(f"Error validating user ID {user_id}: {e}")
        return False


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format

    Args:
        session_id: Session ID string

    Returns:
        bool: True if valid session ID format, False otherwise
    """
    if not session_id or len(session_id) < 10:
        return False

    try:
        # Session IDs usually start with a prefix
        valid_prefixes = ["user_", "chat_", "session_", "guest_"]
        is_valid = any(session_id.startswith(prefix) for prefix in valid_prefixes)

        if not is_valid:
            logger.debug(f"Invalid session ID format: {session_id}")

        return is_valid
    except Exception as e:
        logger.error(f"Error validating session ID: {e}")
        return False


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input

    Args:
        text: Input text to sanitize
        max_length: Maximum length of output (default: 1000)

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    try:
        # Remove potentially dangerous characters
        text = text.strip()
        text = re.sub(r'[<>]', '', text)  # Remove HTML brackets
        sanitized = text[:max_length]

        if len(text) > max_length:
            logger.debug(f"Text truncated from {len(text)} to {max_length} characters")

        return sanitized
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        return ""
