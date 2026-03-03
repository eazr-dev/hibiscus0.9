"""
Bill Audit Tool
===============
Wraps the EAZR bill audit module for hospital bill verification.

Usage:
    result = await audit_bill(files, session_id, user_id)
"""
from typing import Any, Dict, List, Optional

from hibiscus.tools.existing_api.client import EAZRClient, HibiscusToolError
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def audit_bill(
    files: List[tuple],
    session_id: str,
    user_id: str,
    *,
    policy_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Upload hospital bills for audit.

    Args:
        files: List of (filename, bytes, content_type) tuples
        session_id: Current session ID
        user_id: User ID
        policy_id: Optional linked policy ID

    Returns audit result with line-item analysis.
    """
    client = EAZRClient(
        session_id=session_id,
        access_token=access_token,
        user_id=user_id,
    )
    try:
        result = await client.upload_bill(files, session_id, user_id, policy_id)
        logger.info("bill_audit_uploaded", user_id=user_id, file_count=len(files))
        return result
    except HibiscusToolError:
        raise
    except Exception as e:
        logger.error("bill_audit_failed", error=str(e))
        raise HibiscusToolError("/api/v1/bill-audit/upload", 500, str(e))


async def get_audit_result(
    audit_id: str,
    session_id: str,
    user_id: str,
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the result of a previously submitted bill audit."""
    client = EAZRClient(
        session_id=session_id,
        access_token=access_token,
        user_id=user_id,
    )
    return await client.get_bill_audit_result(audit_id, session_id, user_id)


async def generate_dispute_letter(
    audit_id: str,
    session_id: str,
    user_id: str,
    *,
    include_pdf: bool = True,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a dispute letter based on bill audit findings."""
    client = EAZRClient(
        session_id=session_id,
        access_token=access_token,
        user_id=user_id,
    )
    return await client.generate_dispute_letter(
        audit_id, session_id, user_id, include_pdf
    )
