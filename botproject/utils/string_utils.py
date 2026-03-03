"""
String Utilities
Common functions for string manipulation and formatting
"""

import re
import secrets
import string
import logging

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug

    Args:
        text: Text to convert to slug

    Returns:
        str: URL-friendly slug
    """
    if not text:
        return ""

    try:
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        slug = text.strip('-')

        logger.debug(f"Slugified text to: {slug}")
        return slug
    except Exception as e:
        logger.error(f"Error slugifying text: {e}")
        return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to max length

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 100)
        suffix: Suffix to add when truncated (default: "...")

    Returns:
        str: Truncated text
    """
    if not text:
        return ""

    try:
        if len(text) <= max_length:
            return text

        truncated = text[:max_length - len(suffix)] + suffix
        logger.debug(f"Truncated text from {len(text)} to {len(truncated)} characters")
        return truncated
    except Exception as e:
        logger.error(f"Error truncating text: {e}")
        return text


def mask_sensitive_data(text: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask sensitive data showing only last N characters

    Args:
        text: Text to mask
        visible_chars: Number of characters to keep visible at end (default: 4)
        mask_char: Character to use for masking (default: "*")

    Returns:
        str: Masked text
    """
    if not text:
        return ""

    try:
        if len(text) <= visible_chars:
            return text

        masked = mask_char * (len(text) - visible_chars) + text[-visible_chars:]
        logger.debug(f"Masked sensitive data, showing last {visible_chars} chars")
        return masked
    except Exception as e:
        logger.error(f"Error masking sensitive data: {e}")
        return text


def generate_random_string(length: int = 8, include_digits: bool = True) -> str:
    """
    Generate random alphanumeric string

    Args:
        length: Length of string to generate (default: 8)
        include_digits: Include digits in string (default: True)

    Returns:
        str: Random string
    """
    try:
        chars = string.ascii_letters
        if include_digits:
            chars += string.digits

        random_str = ''.join(secrets.choice(chars) for _ in range(length))
        logger.debug(f"Generated random string of length {length}")
        return random_str
    except Exception as e:
        logger.error(f"Error generating random string: {e}")
        return secrets.token_hex(length // 2)


def capitalize_words(text: str) -> str:
    """
    Capitalize each word in text

    Args:
        text: Text to capitalize

    Returns:
        str: Text with each word capitalized
    """
    if not text:
        return ""

    try:
        capitalized = ' '.join(word.capitalize() for word in text.split())
        logger.debug(f"Capitalized words in text")
        return capitalized
    except Exception as e:
        logger.error(f"Error capitalizing words: {e}")
        return text


def remove_extra_spaces(text: str) -> str:
    """
    Remove extra spaces from text

    Args:
        text: Text to clean

    Returns:
        str: Text with extra spaces removed
    """
    if not text:
        return ""

    try:
        cleaned = re.sub(r'\s+', ' ', text).strip()
        logger.debug(f"Removed extra spaces from text")
        return cleaned
    except Exception as e:
        logger.error(f"Error removing extra spaces: {e}")
        return text
