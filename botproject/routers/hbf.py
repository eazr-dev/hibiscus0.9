"""
HBF Router
API endpoints for Hospital Bill Financing: eligibility, offers, application.

Rate Limiting Applied:
- Eligibility check: 10/minute
- Loan application: 5/minute
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from core.dependencies import get_session, store_session
from core.rate_limiter import limiter, RATE_LIMITS
from session_security.session_manager import session_manager
from core.errors import ERROR_MESSAGES, ERROR_HTTP_STATUS
from models.hbf import (
    EligibilityCheckRequest,
    GetOffersRequest,
    ApplyLoanRequest,
    CompleteLoanRequest,
    BaseHBFRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hbf", tags=["HBF Financing"])

# Lazy-load service
_hbf_service = None


def _get_service():
    global _hbf_service
    if _hbf_service is None:
        from services.hbf_service import hbf_service
        _hbf_service = hbf_service
    return _hbf_service


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


class GetLoanStatusRequest(BaseHBFRequest):
    loan_id: str


# ==================== ENDPOINTS ====================

@router.get("/test")
@limiter.limit(RATE_LIMITS.get("relaxed", "30/minute"))
async def test_hbf(request: Request):
    return {"success": True, "message": "HBF Financing router is working!"}


@router.post("/eligibility")
@limiter.limit(RATE_LIMITS.get("hbf_check", "10/minute"))
async def check_eligibility(request: Request, body: EligibilityCheckRequest):
    """
    Check eligibility for HBF financing.

    Returns EAZR score breakdown, eligibility status, and max eligible amount.
    """
    validate_session(body.session_id, body.user_id)

    service = _get_service()
    result = await service.check_eligibility(
        user_id=body.user_id,
        loan_type=body.loan_type.value,
        amount=body.amount,
        audit_id=body.audit_id,
    )

    return {
        "success": True,
        "data": result,
        "session_id": body.session_id,
    }


@router.post("/offers")
@limiter.limit(RATE_LIMITS.get("hbf_check", "10/minute"))
async def generate_offers(request: Request, body: GetOffersRequest):
    """
    Generate loan offers with EMI options for a pre-qualified loan.

    Returns multiple tenure options with interest rates and EMI amounts.
    """
    validate_session(body.session_id, body.user_id)

    service = _get_service()
    result = await service.generate_offers(body.user_id, body.loan_id)

    if not result:
        _error_response("HBF_10003")

    return {
        "success": True,
        "data": result,
        "session_id": body.session_id,
    }


@router.post("/apply")
@limiter.limit(RATE_LIMITS.get("hbf_apply", "5/minute"))
async def apply_loan(request: Request, body: ApplyLoanRequest):
    """
    Apply for a loan by selecting an offer.

    Returns application status and next steps (e-KYC, e-NACH, e-Sign).
    """
    validate_session(body.session_id, body.user_id)

    service = _get_service()
    result = await service.apply_loan(body.user_id, body.loan_id, body.selected_offer_id)

    if not result:
        _error_response("HBF_10003")

    if result.get("error"):
        raise HTTPException(status_code=400, detail={
            "error_code": "HBF_10005",
            "message": result["error"],
        })

    return {
        "success": True,
        "data": result,
        "session_id": body.session_id,
    }


@router.post("/complete")
@limiter.limit(RATE_LIMITS.get("hbf_apply", "5/minute"))
async def complete_loan(request: Request, body: CompleteLoanRequest):
    """
    Complete loan process (placeholder for e-NACH/e-Sign integration).

    Marks loan as approved for disbursement.
    """
    validate_session(body.session_id, body.user_id)

    service = _get_service()
    result = await service.complete_loan(body.user_id, body.loan_id)

    if not result:
        _error_response("HBF_10003")

    if result.get("error"):
        raise HTTPException(status_code=400, detail={
            "error_code": "HBF_10005",
            "message": result["error"],
        })

    return {
        "success": True,
        "data": result,
        "session_id": body.session_id,
    }


@router.post("/status")
@limiter.limit(RATE_LIMITS.get("hbf_check", "10/minute"))
async def get_loan_status(request: Request, body: GetLoanStatusRequest):
    """Get loan status and details."""
    validate_session(body.session_id, body.user_id)

    service = _get_service()
    result = await service.get_loan_status(body.user_id, body.loan_id)

    if not result:
        _error_response("HBF_10003")

    return {
        "success": True,
        "data": result,
        "session_id": body.session_id,
    }
