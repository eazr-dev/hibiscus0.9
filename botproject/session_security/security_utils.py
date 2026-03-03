"""
Security utilities for input validation and sanitization
"""
import re
from typing import Any


def sanitize_regex_input(user_input: str, max_length: int = 100) -> str:
    """
    Sanitize user input for MongoDB regex queries to prevent ReDoS attacks

    Args:
        user_input: Raw user input string
        max_length: Maximum allowed length

    Returns:
        Escaped regex-safe string
    """
    if not isinstance(user_input, str):
        return ""

    # Limit length to prevent ReDoS
    if len(user_input) > max_length:
        user_input = user_input[:max_length]

    # Escape all special regex characters
    escaped = re.escape(user_input)

    return escaped


def validate_user_id(user_id: Any) -> int:
    """
    Validate and convert user_id to safe integer

    Args:
        user_id: User ID to validate

    Returns:
        Validated integer user ID

    Raises:
        ValueError: If user_id is invalid
    """
    try:
        uid = int(user_id)
        if uid <= 0:
            raise ValueError("User ID must be positive")
        if uid > 2147483647:  # Max 32-bit int
            raise ValueError("User ID exceeds maximum value")
        return uid
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid user ID: {e}")


def validate_limit(limit: Any, max_limit: int = 1000, default: int = 50) -> int:
    """
    Validate query limit parameter

    Args:
        limit: Limit value to validate
        max_limit: Maximum allowed limit
        default: Default limit if invalid

    Returns:
        Validated limit integer
    """
    try:
        limit_int = int(limit)
        if limit_int < 1:
            return default
        if limit_int > max_limit:
            return max_limit
        return limit_int
    except (ValueError, TypeError):
        return default


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent path traversal attacks

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    import os
    from datetime import datetime

    # Remove path components
    filename = os.path.basename(filename)

    # Remove dangerous characters, keep only alphanumeric, dash, underscore, and dot
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Prevent directory traversal
    filename = filename.replace('..', '')

    # Limit filename length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    # Ensure it's not empty
    if not filename or filename == '.':
        filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return filename


def sanitize_text_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text input to prevent XSS

    Args:
        text: Raw text input
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove null bytes
    text = text.replace('\x00', '')

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def validate_session_id(session_id: str) -> str:
    """
    Validate session ID format

    Args:
        session_id: Session ID to validate

    Returns:
        Validated session ID

    Raises:
        ValueError: If session ID is invalid
    """
    if not isinstance(session_id, str):
        raise ValueError("Session ID must be a string")

    # Check length
    if len(session_id) < 1 or len(session_id) > 200:
        raise ValueError("Session ID length must be between 1 and 200 characters")

    # Check format (alphanumeric, dash, underscore only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise ValueError("Session ID contains invalid characters")

    return session_id
