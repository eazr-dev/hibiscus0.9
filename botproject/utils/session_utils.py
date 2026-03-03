"""
Session Utilities
Common functions for session management
"""

import time
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_session_id(prefix: str = "session", user_id: Optional[int] = None) -> str:
    """
    Generate unique session ID

    Args:
        prefix: Session ID prefix (default: "session")
        user_id: Optional user ID to include in session ID

    Returns:
        str: Unique session ID
    """
    try:
        timestamp = int(time.time())
        random_suffix = secrets.token_hex(4)

        if user_id:
            session_id = f"{prefix}_{user_id}_{timestamp}_{random_suffix}"
        else:
            session_id = f"{prefix}_{timestamp}_{random_suffix}"

        logger.debug(f"Generated session ID: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Error generating session ID: {e}")
        # Fallback to simple random ID
        return f"{prefix}_{secrets.token_hex(8)}"


def extract_user_from_session(session_data: Dict) -> Dict:
    """
    Extract user info from session data

    Args:
        session_data: Session data dictionary

    Returns:
        Dict: User information extracted from session
    """
    if not session_data:
        logger.warning("Empty session data provided")
        return {}

    try:
        user_info = {
            "user_id": session_data.get("user_id"),
            "phone": session_data.get("phone"),
            "access_token": session_data.get("access_token"),
            "user_name": session_data.get("user_name")
        }

        logger.debug(f"Extracted user info for user_id: {user_info.get('user_id')}")
        return user_info
    except Exception as e:
        logger.error(f"Error extracting user from session: {e}")
        return {}


def is_session_expired(session_data: Dict, max_age_seconds: int = 86400) -> bool:
    """
    Check if session is expired

    Args:
        session_data: Session data dictionary
        max_age_seconds: Maximum session age in seconds (default: 86400 = 24 hours)

    Returns:
        bool: True if session is expired, False otherwise
    """
    if not session_data:
        logger.debug("Empty session data - considering expired")
        return True

    if not session_data.get("created_at"):
        logger.warning("Session missing created_at timestamp - considering expired")
        return True

    try:
        created_at = datetime.fromisoformat(session_data["created_at"])
        age = (datetime.now() - created_at).total_seconds()

        is_expired = age > max_age_seconds

        if is_expired:
            logger.info(f"Session expired: age {age}s > max {max_age_seconds}s")

        return is_expired
    except Exception as e:
        logger.error(f"Error checking session expiry: {e}")
        return True


def calculate_session_expiry(hours: int = 24) -> str:
    """
    Calculate session expiry timestamp

    Args:
        hours: Hours until expiry (default: 24)

    Returns:
        str: ISO format timestamp for expiry
    """
    try:
        expiry = datetime.now() + timedelta(hours=hours)
        expiry_str = expiry.isoformat()

        logger.debug(f"Session expiry calculated: {expiry_str}")
        return expiry_str
    except Exception as e:
        logger.error(f"Error calculating session expiry: {e}")
        return datetime.now().isoformat()


def create_session_data(
    user_id: int,
    phone: str,
    access_token: str,
    **kwargs
) -> Dict:
    """
    Create session data dictionary

    Args:
        user_id: User ID
        phone: User phone number
        access_token: Access token
        **kwargs: Additional session data fields

    Returns:
        Dict: Session data dictionary
    """
    try:
        session_data = {
            "user_id": user_id,
            "phone": phone,
            "access_token": access_token,
            "created_at": datetime.now().isoformat(),
            "active": True,
            **kwargs
        }

        logger.info(f"Session data created for user_id: {user_id}")
        return session_data
    except Exception as e:
        logger.error(f"Error creating session data: {e}")
        return {}
