"""
Bill Audit Router
API endpoints for Bill Audit Intelligence: upload, analyze, report, dispute letter.

Rate Limiting Applied:
- Bill upload/analysis: 5/minute
- Bill read: 30/minute
- Report generation: 5/minute
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Request

from core.dependencies import get_session, store_session
from core.rate_limiter import limiter, RATE_LIMITS
from session_security.session_manager import session_manager
from core.errors import ErrorCode, ERROR_MESSAGES, ERROR_HTTP_STATUS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bill-audit", tags=["Bill Audit Intelligence"])

# Lazy-load service
_bill_audit_service = None


def _get_service():
    global _bill_audit_service
    if _bill_audit_service is None:
        from services.bill_audit_service import bill_audit_service
        _bill_audit_service = bill_audit_service
    return _bill_audit_service


def validate_session(session_id: str, user_id: int):
    try:
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            session_id, get_session, store_session
        )
        if not session_data or not session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        session_user_id = session_data.get('user_id')
        if session_user_id and session_user_id != user_id:
            raise HTTPException(status_code=403, detail="User ID mismatch")
        return session_id, session_data, was_regenerated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        raise HTTPException(status_code=401, detail="Session validation failed")


def _error_response(error_code: str):
    message = ERROR_MESSAGES.get(error_code, "An error occurred")
    status = ERROR_HTTP_STATUS.get(error_code, 500)
    raise HTTPException(status_code=status, detail={"error_code": error_code, "message": message})


# ==================== ENDPOINTS ====================

@router.get("/test")
@limiter.limit(RATE_LIMITS.get("relaxed", "30/minute"))
async def test_bill_audit(request: Request):
    return {"success": True, "message": "Bill Audit Intelligence router is working!"}


@router.post("/upload")
@limiter.limit(RATE_LIMITS.get("bill_audit_upload", "5/minute"))
async def upload_and_analyze(
    request: Request,
    session_id: str = Form(...),
    user_id: int = Form(...),
    files: List[UploadFile] = File(...),
    policy_id: Optional[str] = Form(None),
):
    """
    Upload bill files (images/PDFs) and analyze for discrepancies.

    Returns complete audit result with bill data, discrepancies, and savings.
    """
    validate_session(session_id, user_id)

    # Validate file count
    if len(files) > 10:
        _error_response("BILL_9010")

    # Validate file types
    for f in files:
        ct = f.content_type or ""
        fname = (f.filename or "").lower()
        is_image = ct.startswith("image/") or fname.endswith(('.jpg', '.jpeg', '.png', '.webp'))
        is_pdf = ct == "application/pdf" or fname.endswith('.pdf')
        if not (is_image or is_pdf):
            _error_response("BILL_9002")

    service = _get_service()
    result = await service.process_bill_upload(
        user_id=user_id,
        files=files,
        policy_id=policy_id,
    )

    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail={
            "error_code": "BILL_9004",
            "message": result.get("error", ERROR_MESSAGES.get("BILL_9004")),
        })

    return {
        "success": True,
        "data": result,
        "session_id": session_id,
    }


@router.get("/{audit_id}")
@limiter.limit(RATE_LIMITS.get("bill_audit_read", "30/minute"))
async def get_audit_result(
    request: Request,
    audit_id: str,
    session_id: str = Query(...),
    user_id: int = Query(...),
):
    """Get a specific bill audit result."""
    validate_session(session_id, user_id)

    service = _get_service()
    result = await service.get_audit_result(user_id, audit_id)

    if not result:
        _error_response("BILL_9005")

    return {
        "success": True,
        "data": result,
        "session_id": session_id,
    }


@router.get("/history/list")
@limiter.limit(RATE_LIMITS.get("bill_audit_read", "30/minute"))
async def get_audit_history(
    request: Request,
    session_id: str = Query(...),
    user_id: int = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get user's bill audit history (paginated)."""
    validate_session(session_id, user_id)

    service = _get_service()
    audits, total = await service.get_audit_history(user_id, limit, offset)

    return {
        "success": True,
        "data": {
            "audits": audits,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(audits) < total,
        },
        "session_id": session_id,
    }


@router.post("/{audit_id}/report")
@limiter.limit(RATE_LIMITS.get("bill_audit_report", "5/minute"))
async def generate_report(
    request: Request,
    audit_id: str,
    session_id: str = Form(...),
    user_id: int = Form(...),
):
    """Generate a PDF audit report and return the download URL."""
    validate_session(session_id, user_id)

    service = _get_service()
    report_url = await service.generate_report(user_id, audit_id)

    if not report_url:
        _error_response("BILL_9008")

    return {
        "success": True,
        "data": {"report_url": report_url},
        "session_id": session_id,
    }


@router.post("/{audit_id}/dispute-letter")
@limiter.limit(RATE_LIMITS.get("bill_audit_report", "5/minute"))
async def generate_dispute_letter(
    request: Request,
    audit_id: str,
    session_id: str = Form(...),
    user_id: int = Form(...),
    include_pdf: bool = Form(True),
):
    """Generate a dispute letter (text + optional PDF) for the audit."""
    validate_session(session_id, user_id)

    service = _get_service()
    result = await service.generate_dispute_letter(user_id, audit_id, as_pdf=include_pdf)

    if not result:
        _error_response("BILL_9009")

    return {
        "success": True,
        "data": result,
        "session_id": session_id,
    }
