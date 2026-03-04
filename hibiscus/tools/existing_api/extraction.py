"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Extraction tool — wraps existing EAZR extraction pipeline for policy PDF analysis.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.observability.logger import get_logger
from hibiscus.tools.existing_api.client import ExistingAPIError, call_existing_api

logger = get_logger("hibiscus.tools.existing_api.extraction")


async def extract_policy(
    file_path: str,
    *,
    doc_id: Optional[str] = None,
    policy_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract structured data from a policy PDF using the existing EAZR extraction pipeline.

    This is the primary tool for PolicyAnalyzer. It calls the existing Node.js extraction
    endpoint which supports 5 policy types (health, life, motor, travel, PA) with
    LLM + 5-check validation.

    Args:
        file_path:   Path or S3 key to the uploaded PDF document.
        doc_id:      Optional document ID for tracking.
        policy_type: Optional hint — "health", "life", "motor", "travel", "pa".
                     If not provided, the extraction engine auto-classifies.

    Returns:
        Dict with structured extraction:
        {
            "success": True/False,
            "policy_type": "health",
            "extraction": { ... structured fields ... },
            "confidence": 0.85,
            "page_count": 12,
            "validation": { ... 5-check results ... },
            "doc_id": "...",
        }

    Raises:
        ExistingAPIError: If extraction service is unreachable after retries.
    """
    logger.info(
        "extract_policy_start",
        file_path=file_path,
        doc_id=doc_id,
        policy_type_hint=policy_type,
    )

    body: Dict[str, Any] = {"file_path": file_path}
    if doc_id:
        body["doc_id"] = doc_id
    if policy_type:
        body["policy_type"] = policy_type

    try:
        result = await call_existing_api(
            "POST",
            "/api/v1/extract",
            operation="extraction",
            json_body=body,
        )

        logger.info(
            "extract_policy_complete",
            doc_id=doc_id,
            success=result.get("success"),
            policy_type=result.get("policy_type"),
            confidence=result.get("confidence"),
        )
        return result

    except ExistingAPIError as exc:
        logger.error(
            "extract_policy_failed",
            doc_id=doc_id,
            error=str(exc),
        )
        return {
            "success": False,
            "error": str(exc),
            "doc_id": doc_id,
            "message": (
                "I couldn't extract your policy document right now. "
                "The extraction service is temporarily unavailable. "
                "Please try uploading again in a moment."
            ),
        }
