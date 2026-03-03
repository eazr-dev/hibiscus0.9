"""
User Portfolio Tool
====================
Fetch and update user insurance portfolio from PostgreSQL.
Delegates to memory/layers/portfolio.py — uses graceful no-op pattern.

Returns [] when PostgreSQL is unavailable (dev mode).
"""
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def get_user_portfolio(user_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all insurance policies in a user's portfolio from PostgreSQL.

    Returns [] if PostgreSQL is not connected (graceful no-op in dev mode).

    Args:
        user_id: The user's unique identifier

    Returns:
        List of policy dicts, or [] if unavailable
    """
    try:
        from hibiscus.memory.layers.portfolio import get_portfolio
        portfolio = await get_portfolio(user_id)
        return portfolio or []
    except Exception as e:
        logger.debug("get_user_portfolio_failed", user_id=user_id, error=str(e))
        return []


async def add_policy_to_portfolio(user_id: str, policy_data: Dict[str, Any]) -> bool:
    """
    Add or update a policy in the user's portfolio after analysis.

    Returns False if PostgreSQL is not connected (graceful no-op).

    Args:
        user_id: The user's unique identifier
        policy_data: Policy details from extraction (insurer, policy_type, sum_assured, premium, etc.)

    Returns:
        True if stored, False if unavailable or error
    """
    try:
        from hibiscus.memory.layers.portfolio import add_policy
        await add_policy(user_id, policy_data)
        return True
    except Exception as e:
        logger.debug("add_policy_to_portfolio_failed", user_id=user_id, error=str(e))
        return False


async def remove_policy_from_portfolio(user_id: str, policy_id: str) -> bool:
    """
    Remove a policy from the user's portfolio.

    Returns False if unavailable or error.

    Args:
        user_id: The user's unique identifier
        policy_id: The policy identifier to remove

    Returns:
        True if removed, False if unavailable or error
    """
    try:
        from hibiscus.memory.layers.portfolio import remove_policy
        await remove_policy(user_id, policy_id)
        return True
    except Exception as e:
        logger.debug("remove_policy_from_portfolio_failed", user_id=user_id, error=str(e))
        return False
