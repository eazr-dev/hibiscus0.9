"""
Protection Score Tool
=====================
Wraps the EAZR protection score calculator (141K-line scoring engine).

Usage:
    score = await calculate_protection_score(user_id)
"""
from typing import Any, Dict, Optional

from hibiscus.tools.existing_api.client import EAZRClient, HibiscusToolError
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def calculate_protection_score(
    user_id: str,
    *,
    annual_income: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate the EAZR protection score for a user.

    Returns score breakdown, component scores, and recommendations.
    """
    client = EAZRClient(access_token=access_token, user_id=user_id)
    try:
        result = await client.get_protection_score(user_id, annual_income)
        logger.info("protection_score_success", user_id=user_id)
        return result
    except HibiscusToolError:
        raise
    except Exception as e:
        logger.error("protection_score_failed", error=str(e), user_id=user_id)
        raise HibiscusToolError("/api/dashboard/protection-score", 500, str(e))


async def refresh_protection_score(
    *,
    annual_income: Optional[int] = None,
    reason: str = "",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Force-refresh the protection score (e.g., after new policy upload)."""
    client = EAZRClient(access_token=access_token)
    return await client.refresh_protection_score(annual_income, reason)
