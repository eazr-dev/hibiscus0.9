"""
User Profile Tool
==================
Fetch and update user profiles from PostgreSQL.
Delegates to memory/layers/profile.py — uses same graceful no-op pattern.

Returns None / False when PostgreSQL is unavailable (dev mode).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user profile from PostgreSQL.

    Returns None if PostgreSQL is not connected (graceful no-op in dev mode).
    Agents should treat None as "no profile available" and proceed without it.

    Args:
        user_id: The user's unique identifier

    Returns:
        Profile dict or None
    """
    try:
        from hibiscus.memory.layers.profile import get_profile
        profile = await get_profile(user_id)
        return profile
    except Exception as e:
        logger.debug("get_user_profile_failed", user_id=user_id, error=str(e))
        return None


async def update_user_profile(user_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update user profile fields in PostgreSQL.

    Returns False if PostgreSQL is not connected (graceful no-op).

    Args:
        user_id: The user's unique identifier
        updates: Dict of fields to update (partial update — only provided fields)

    Returns:
        True if updated, False if unavailable or error
    """
    try:
        from hibiscus.memory.layers.profile import upsert_profile
        await upsert_profile(user_id, updates)
        return True
    except Exception as e:
        logger.debug("update_user_profile_failed", user_id=user_id, error=str(e))
        return False
