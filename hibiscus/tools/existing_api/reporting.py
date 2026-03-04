"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Reporting tool — wraps existing type-specific report generators (80-103K lines each).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.observability.logger import get_logger
from hibiscus.tools.existing_api.client import ExistingAPIError, call_existing_api

logger = get_logger("hibiscus.tools.existing_api.reporting")


async def generate_report(
    analysis_data: Dict[str, Any],
    *,
    report_type: str = "comprehensive",
    policy_type: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a structured report using the existing EAZR report generators.

    The existing system has category-specific generators (health, life, motor, etc.)
    that produce 80-103K line reports with detailed breakdowns.

    Args:
        analysis_data: Combined extraction + scoring data.
        report_type:   "comprehensive" | "summary" | "comparison" | "gap_analysis".
        policy_type:   Insurance category for routing to the correct generator.
        doc_id:        Optional document ID for tracking.

    Returns:
        Dict with generated report:
        {
            "success": True/False,
            "report_type": "comprehensive",
            "report": { ... structured report sections ... },
            "strengths": [...],
            "weaknesses": [...],
            "recommendations": [...],
            "doc_id": "...",
        }
    """
    logger.info(
        "generate_report_start",
        report_type=report_type,
        policy_type=policy_type,
        doc_id=doc_id,
    )

    body: Dict[str, Any] = {
        "analysis_data": analysis_data,
        "report_type": report_type,
    }
    if policy_type:
        body["policy_type"] = policy_type
    if doc_id:
        body["doc_id"] = doc_id

    try:
        result = await call_existing_api(
            "POST",
            "/api/v1/report",
            operation="reporting",
            json_body=body,
        )

        logger.info(
            "generate_report_complete",
            doc_id=doc_id,
            report_type=report_type,
            sections=len(result.get("report", {}).keys()) if isinstance(result.get("report"), dict) else 0,
        )
        return result

    except ExistingAPIError as exc:
        logger.error("generate_report_failed", doc_id=doc_id, error=str(exc))
        return {
            "success": False,
            "error": str(exc),
            "doc_id": doc_id,
            "message": (
                "I couldn't generate the detailed report right now. "
                "However, I can still provide my analysis based on the extracted data."
            ),
        }
