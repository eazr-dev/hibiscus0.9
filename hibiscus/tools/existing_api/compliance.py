"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Compliance tool — wraps existing IRDAI compliance checker.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import get_logger
from hibiscus.tools.existing_api.client import ExistingAPIError, call_existing_api

logger = get_logger("hibiscus.tools.existing_api.compliance")


async def check_irdai_compliance(
    policy_data: Dict[str, Any],
    *,
    policy_type: Optional[str] = None,
    checks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Check a policy against IRDAI compliance rules using the existing checker.

    Verifies:
    - Mandatory disclosures present
    - Free look period compliance
    - Claim settlement timeline adherence
    - Portability provisions
    - Waiting period limits
    - Mis-selling indicators

    Args:
        policy_data: Extracted policy data to validate.
        policy_type: Insurance category for applicable rules.
        checks:      Optional list of specific checks to run. If None, runs all.

    Returns:
        Dict with compliance results:
        {
            "success": True/False,
            "compliant": True/False,
            "checks": [
                {"check": "free_look_period", "status": "pass", "detail": "30 days stated"},
                {"check": "claim_timeline", "status": "warning", "detail": "Not explicitly mentioned"},
            ],
            "violations": [...],
            "warnings": [...],
            "score": 0.85,
        }
    """
    logger.info(
        "compliance_check_start",
        policy_type=policy_type,
        checks_requested=checks,
    )

    body: Dict[str, Any] = {"policy_data": policy_data}
    if policy_type:
        body["policy_type"] = policy_type
    if checks:
        body["checks"] = checks

    try:
        result = await call_existing_api(
            "POST",
            "/api/v1/compliance/check",
            operation="compliance",
            json_body=body,
        )

        violations = result.get("violations", [])
        warnings = result.get("warnings", [])
        logger.info(
            "compliance_check_complete",
            compliant=result.get("compliant"),
            violations=len(violations),
            warnings=len(warnings),
            score=result.get("score"),
        )
        return result

    except ExistingAPIError as exc:
        logger.error("compliance_check_failed", error=str(exc))
        return {
            "success": False,
            "error": str(exc),
            "message": (
                "I couldn't run the full IRDAI compliance check right now. "
                "I'll note this and recommend you verify compliance independently."
            ),
        }
