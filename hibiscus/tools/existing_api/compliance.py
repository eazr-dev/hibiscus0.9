"""
IRDAI Compliance Tool
=====================
Wraps compliance checks against the existing EAZR system.

For Hibiscus, most compliance checks are done by the compliance guardrail
(hibiscus/guardrails/compliance.py). This tool provides access to the
botproject's claim guidance which includes IRDAI-mandated timelines and rights.

Usage:
    guidance = await check_irdai_compliance(query, session_id, user_id)
"""
from typing import Any, Dict, Optional

from hibiscus.tools.existing_api.client import EAZRClient, HibiscusToolError
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def check_irdai_compliance(
    query: str,
    session_id: str,
    user_id: str,
    *,
    insurance_type: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get IRDAI-compliant claim guidance from the existing system.

    Returns step-by-step guidance with regulatory references,
    mandated timelines, and consumer rights.
    """
    client = EAZRClient(
        session_id=session_id,
        access_token=access_token or "",
        user_id=user_id,
    )
    try:
        result = await client.get_claim_guidance(
            query=query,
            session_id=session_id,
            access_token=access_token or "",
            user_id=user_id,
            insurance_type=insurance_type,
        )
        logger.info("compliance_check_success", user_id=user_id)
        return result
    except HibiscusToolError:
        raise
    except Exception as e:
        logger.error("compliance_check_failed", error=str(e))
        raise HibiscusToolError("/insurance-claim-guidance", 500, str(e))
