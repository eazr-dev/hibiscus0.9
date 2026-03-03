"""
File Utilities
Common functions for file handling and validation
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import secrets
import logging

logger = logging.getLogger(__name__)


def get_file_extension(filename: str) -> str:
    """
    Extract file extension (without dot)

    Args:
        filename: Name of the file

    Returns:
        str: File extension without the dot
    """
    if not filename:
        return ""
    return Path(filename).suffix.lstrip('.')


def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """
    Validate file type against allowed list

    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['jpg', 'png'])

    Returns:
        bool: True if file type is allowed, False otherwise
    """
    if not filename or not allowed_extensions:
        return False

    try:
        ext = get_file_extension(filename).lower()
        is_valid = ext in [e.lower() for e in allowed_extensions]

        if not is_valid:
            logger.debug(f"File type '{ext}' not in allowed list: {allowed_extensions}")

        return is_valid
    except Exception as e:
        logger.error(f"Error validating file type: {e}")
        return False


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate unique filename with timestamp and random string

    Args:
        original_filename: Original filename
        prefix: Optional prefix to add (default: "")

    Returns:
        str: Unique filename
    """
    if not original_filename:
        return ""

    try:
        ext = get_file_extension(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = secrets.token_hex(4)
        base = Path(original_filename).stem[:50]  # Limit length

        if prefix:
            return f"{prefix}_{base}_{timestamp}_{random_str}.{ext}"
        return f"{base}_{timestamp}_{random_str}.{ext}"
    except Exception as e:
        logger.error(f"Error generating unique filename: {e}")
        return original_filename


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in MB

    Args:
        file_path: Path to the file

    Returns:
        float: File size in megabytes
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0.0


def is_image_file(filename: str) -> bool:
    """
    Check if file is an image

    Args:
        filename: Name of the file

    Returns:
        bool: True if file is an image, False otherwise
    """
    if not filename:
        return False

    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    return get_file_extension(filename).lower() in image_extensions


def is_document_file(filename: str) -> bool:
    """
    Check if file is a document

    Args:
        filename: Name of the file

    Returns:
        bool: True if file is a document, False otherwise
    """
    if not filename:
        return False

    doc_extensions = ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx']
    return get_file_extension(filename).lower() in doc_extensions
