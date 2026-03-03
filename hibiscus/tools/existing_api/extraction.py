"""
Policy Extraction Tool
======================
Wraps the EAZR extraction pipeline (botproject) as a callable tool.

Usage:
    result = await extract_policy(pdf_bytes, filename, user_id, session_id)
"""
from typing import Any, Dict, Optional

from hibiscus.tools.existing_api.client import EAZRClient, HibiscusToolError
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


async def extract_policy(
    pdf_bytes: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    *,
    policy_for: str = "self",
    name: str = "",
    gender: str = "male",
    relationship: str = "self",
    dob: Optional[str] = None,
    generate_pdf: bool = True,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Upload a policy PDF and get full 7-stage analysis.

    Returns the complete extraction result including:
    - policy_type, insurer, product_name
    - sum_insured, premium, policy_term
    - coverage details, exclusions, waiting periods
    - EAZR Score, gaps, red flags

    Latency: 30-90 seconds (DeepSeek extraction + scoring + report).

    Raises HibiscusToolError on failure.
    """
    client = EAZRClient(
        session_id=session_id,
        access_token=access_token,
        user_id=user_id,
    )
    try:
        result = await client.upload_and_analyze_policy(
            pdf_bytes=pdf_bytes,
            filename=filename,
            user_id=user_id,
            session_id=session_id,
            policy_for=policy_for,
            name=name,
            gender=gender,
            relationship=relationship,
            dob=dob,
            generate_pdf=generate_pdf,
        )
        logger.info("extract_policy_success", filename=filename, user_id=user_id)
        return result
    except HibiscusToolError:
        raise
    except Exception as e:
        logger.error("extract_policy_failed", error=str(e), filename=filename)
        raise HibiscusToolError("/api/policy/upload", 500, f"Extraction failed: {e}")
