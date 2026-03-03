"""
Date Utilities
Common functions for date and time handling
"""

from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def calculate_age(dob_str: str) -> Optional[int]:
    """
    Calculate age from DOB string (YYYY-MM-DD or DD-MM-YYYY)

    Args:
        dob_str: Date of birth as string in various formats

    Returns:
        Optional[int]: Age in years, or None if invalid format
    """
    try:
        # Try YYYY-MM-DD format
        if "-" in dob_str and len(dob_str.split("-")[0]) == 4:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        # Try DD-MM-YYYY format
        elif "-" in dob_str:
            dob = datetime.strptime(dob_str, "%d-%m-%Y").date()
        # Try DD/MM/YYYY format
        elif "/" in dob_str:
            dob = datetime.strptime(dob_str, "%d/%m/%Y").date()
        else:
            logger.warning(f"Unknown date format: {dob_str}")
            return None

        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < 0:
            logger.warning(f"Calculated negative age for DOB: {dob_str}")
            return None

        return age
    except Exception as e:
        logger.error(f"Error calculating age from {dob_str}: {e}")
        return None


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format

    Returns:
        str: Current timestamp in ISO 8601 format
    """
    return datetime.now().isoformat()


def format_datetime(dt: datetime, format_type: str = "iso") -> str:
    """
    Format datetime to string

    Args:
        dt: Datetime object to format
        format_type: Type of format (iso, date, datetime, display)

    Returns:
        str: Formatted datetime string
    """
    try:
        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "datetime":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "display":
            return dt.strftime("%B %d, %Y at %I:%M %p")
        else:
            logger.warning(f"Unknown format_type: {format_type}, using ISO")
            return dt.isoformat()
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return dt.isoformat()


def days_between(date1: datetime, date2: datetime) -> int:
    """
    Calculate days between two dates

    Args:
        date1: First datetime
        date2: Second datetime

    Returns:
        int: Absolute number of days between the two dates
    """
    try:
        return abs((date2 - date1).days)
    except Exception as e:
        logger.error(f"Error calculating days between dates: {e}")
        return 0
