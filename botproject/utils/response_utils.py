"""
Response Utilities
Common functions for API response formatting
"""

from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_success_response(
    data: Any,
    message: str = "Success",
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Create standardized success response

    Args:
        data: Response data
        message: Success message (default: "Success")
        metadata: Optional metadata dictionary

    Returns:
        Dict: Standardized success response
    """
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    if metadata:
        response["metadata"] = metadata

    logger.debug(f"Success response created: {message}")
    return response


def create_error_response(
    error: str,
    details: Optional[Dict] = None,
    error_code: Optional[str] = None
) -> Dict:
    """
    Create standardized error response

    Args:
        error: Error message
        details: Optional error details dictionary
        error_code: Optional error code

    Returns:
        Dict: Standardized error response
    """
    response = {
        "success": False,
        "error": error
    }
    if details:
        response["details"] = details
    if error_code:
        response["error_code"] = error_code

    logger.warning(f"Error response created: {error}")
    return response


def paginate_response(
    data: list,
    page: int,
    limit: int,
    total: int
) -> Dict:
    """
    Create paginated response

    Args:
        data: List of data items for current page
        page: Current page number
        limit: Items per page
        total: Total number of items

    Returns:
        Dict: Paginated response with metadata
    """
    try:
        total_pages = (total + limit - 1) // limit  # Ceiling division

        response = {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

        logger.debug(f"Paginated response: page {page}/{total_pages}, {len(data)} items")
        return response
    except Exception as e:
        logger.error(f"Error creating paginated response: {e}")
        return create_error_response("Pagination error", {"error": str(e)})


def format_api_response(
    data: Any,
    status: str = "success",
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Format data with metadata

    Args:
        data: Response data
        status: Response status (default: "success")
        metadata: Optional metadata dictionary

    Returns:
        Dict: Formatted response with timestamp
    """
    response = {
        "status": status,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    if metadata:
        response.update(metadata)

    logger.debug(f"API response formatted with status: {status}")
    return response
