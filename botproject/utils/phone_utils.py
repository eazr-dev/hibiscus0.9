"""
Phone Utilities
Common functions for phone number handling and validation
"""

import logging

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> str:
    """
    Remove +91 country code, return just digits

    Args:
        phone: Phone number string (may include country code)

    Returns:
        str: Normalized phone number without country code
    """
    if not phone:
        return ""
    return phone[3:] if phone.startswith("+91") else phone


def add_country_code(phone: str, code: str = "+91") -> str:
    """
    Add country code if not present

    Args:
        phone: Phone number string
        code: Country code to add (default: +91)

    Returns:
        str: Phone number with country code
    """
    if not phone:
        return ""
    if not phone.startswith("+"):
        return f"{code}{phone}"
    return phone


def validate_phone_number(phone: str) -> bool:
    """
    Validate 10-digit Indian phone number

    Args:
        phone: Phone number string

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        normalized = normalize_phone_number(phone)
        is_valid = len(normalized) == 10 and normalized.isdigit()

        if not is_valid:
            logger.debug(f"Invalid phone number format: {phone}")

        return is_valid
    except Exception as e:
        logger.error(f"Error validating phone number: {e}")
        return False


def mask_phone_number(phone: str, visible: int = 4) -> str:
    """
    Mask phone number showing only last N digits

    Args:
        phone: Phone number string
        visible: Number of digits to keep visible at the end (default: 4)

    Returns:
        str: Masked phone number (e.g., "******3210")
    """
    if not phone:
        return ""

    try:
        normalized = normalize_phone_number(phone)
        if len(normalized) > visible:
            return "*" * (len(normalized) - visible) + normalized[-visible:]
        return normalized
    except Exception as e:
        logger.error(f"Error masking phone number: {e}")
        return phone
