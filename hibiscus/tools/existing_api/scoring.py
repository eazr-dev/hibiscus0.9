"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Scoring tool — wraps existing EAZR protection score calculator (141K lines).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.observability.logger import get_logger
from hibiscus.tools.existing_api.client import ExistingAPIError, call_existing_api

logger = get_logger("hibiscus.tools.existing_api.scoring")


async def calculate_protection_score(
    extracted_data: Dict[str, Any],
    *,
    policy_type: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate the EAZR Protection Score using the existing 141K-line scoring engine.

    Args:
        extracted_data: Structured extraction output from extract_policy().
        policy_type:    Insurance category — "health", "life", "motor", "travel", "pa".
        doc_id:         Optional document ID for tracking.

    Returns:
        Dict with protection score breakdown:
        {
            "success": True/False,
            "eazr_score": 7.8,
            "components": {
                "coverage_comprehensiveness": 8.2,
                "sublimit_freedom": 7.0,
                "exclusion_fairness": 6.5,
                "insurer_quality": 8.5,
                "premium_value": 7.2,
                "claim_process_quality": 8.0,
                "regulatory_compliance": 9.0,
            },
            "percentile": 72,
            "verdict": "Good — above average for this category",
            "doc_id": "...",
        }
    """
    logger.info(
        "calculate_score_start",
        policy_type=policy_type,
        doc_id=doc_id,
    )

    body: Dict[str, Any] = {"extracted_data": extracted_data}
    if policy_type:
        body["policy_type"] = policy_type
    if doc_id:
        body["doc_id"] = doc_id

    try:
        result = await call_existing_api(
            "POST",
            "/api/v1/score",
            operation="scoring",
            json_body=body,
        )

        logger.info(
            "calculate_score_complete",
            doc_id=doc_id,
            eazr_score=result.get("eazr_score"),
            percentile=result.get("percentile"),
        )
        return result

    except ExistingAPIError as exc:
        logger.error("calculate_score_failed", doc_id=doc_id, error=str(exc))
        return {
            "success": False,
            "error": str(exc),
            "doc_id": doc_id,
            "message": (
                "I couldn't calculate the protection score right now. "
                "The scoring service is temporarily unavailable."
            ),
        }
