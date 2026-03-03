"""
Report Generation Tool
======================
Wraps the EAZR report generators (type-specific PDF reports).

Usage:
    report = await generate_report(policy_id, user_id)
"""
from typing import Any, Dict, Optional

from hibiscus.tools.existing_api.client import EAZRClient, HibiscusToolError
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def generate_report(
    policy_id: str,
    user_id: str,
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the full policy analysis report for a previously analyzed policy.

    Returns the complete analysis including extraction data, scores,
    gaps, recommendations, and PDF report URL.
    """
    client = EAZRClient(access_token=access_token, user_id=user_id)
    try:
        result = await client.get_policy_detail(policy_id, user_id)
        logger.info("report_generated", policy_id=policy_id, user_id=user_id)
        return result
    except HibiscusToolError:
        raise
    except Exception as e:
        logger.error("report_generation_failed", error=str(e), policy_id=policy_id)
        raise HibiscusToolError(f"/api/user/policies/{policy_id}", 500, str(e))


async def get_dashboard_insights(
    user_id: str,
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Get dashboard insights and recommendations for a user."""
    client = EAZRClient(access_token=access_token, user_id=user_id)
    return await client.get_dashboard_insights(user_id)
