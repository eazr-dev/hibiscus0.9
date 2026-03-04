"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Billing tool — wraps existing bill audit module for hospital bill analysis.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.observability.logger import get_logger
from hibiscus.tools.existing_api.client import ExistingAPIError, call_existing_api

logger = get_logger("hibiscus.tools.existing_api.billing")


async def audit_bill(
    bill_data: Dict[str, Any],
    *,
    policy_data: Optional[Dict[str, Any]] = None,
    hospital_city: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Audit a hospital bill against policy terms and market benchmarks.

    Checks for:
    - Overcharging vs CGHS/Ayushman rates
    - Items not covered by policy
    - Sub-limit breaches
    - Duplicate line items
    - Inflated consumable charges

    Args:
        bill_data:     Extracted bill line items and totals.
        policy_data:   Optional policy extraction for cross-referencing coverage limits.
        hospital_city: City for regional rate comparison.

    Returns:
        Dict with audit results:
        {
            "success": True/False,
            "total_billed": 250000,
            "total_eligible": 225000,
            "overcharged_items": [...],
            "not_covered_items": [...],
            "sublimit_breaches": [...],
            "savings_identified": 25000,
            "recommendations": [...],
        }
    """
    logger.info(
        "bill_audit_start",
        total_billed=bill_data.get("total"),
        hospital_city=hospital_city,
    )

    body: Dict[str, Any] = {"bill_data": bill_data}
    if policy_data:
        body["policy_data"] = policy_data
    if hospital_city:
        body["hospital_city"] = hospital_city

    try:
        result = await call_existing_api(
            "POST",
            "/api/v1/bill/audit",
            operation="billing",
            json_body=body,
        )

        logger.info(
            "bill_audit_complete",
            total_billed=result.get("total_billed"),
            total_eligible=result.get("total_eligible"),
            savings=result.get("savings_identified"),
            overcharged=len(result.get("overcharged_items", [])),
        )
        return result

    except ExistingAPIError as exc:
        logger.error("bill_audit_failed", error=str(exc))
        return {
            "success": False,
            "error": str(exc),
            "message": (
                "I couldn't audit the bill right now. "
                "The billing analysis service is temporarily unavailable."
            ),
        }
