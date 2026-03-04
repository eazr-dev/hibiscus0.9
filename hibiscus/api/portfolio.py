"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Portfolio endpoint — user portfolio breakdown, coverage analysis, optimization suggestions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class PolicyEntry(BaseModel):
    insurer: str
    product_name: str
    policy_type: str                  # health | life_term | life_endowment | motor | travel | pa
    policy_number: Optional[str] = None
    sum_insured: Optional[float] = None
    annual_premium: Optional[float] = None
    start_date: Optional[str] = None  # DD/MM/YYYY
    end_date: Optional[str] = None    # DD/MM/YYYY
    nominees: Optional[List[str]] = None
    notes: Optional[str] = None


class AddPolicyRequest(BaseModel):
    user_id: str
    policy: PolicyEntry


class AddPolicyResponse(BaseModel):
    success: bool
    policy_id: str
    message: str


class PortfolioResponse(BaseModel):
    user_id: str
    policies: List[Dict[str, Any]]
    count: int
    message: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/portfolio/{user_id}", response_model=PortfolioResponse)
async def get_portfolio(user_id: str, http_request: Request) -> PortfolioResponse:
    """
    Fetch all insurance policies in a user's portfolio.

    Path parameter: user_id (required)
    Returns empty list with a note if PostgreSQL is unavailable.
    """
    # Prefer user_id from JWT state if available
    jwt_user_id = getattr(http_request.state, "user_id", None)
    if jwt_user_id and jwt_user_id != "anonymous":
        user_id = jwt_user_id

    if not user_id:
        return JSONResponse(
            {"error": "user_id is required"},
            status_code=400,
        )

    logger.info("portfolio_fetch", user_id=user_id)

    policies = []
    message = None
    try:
        from hibiscus.tools.user.portfolio import get_user_portfolio
        policies = await get_user_portfolio(user_id) or []
    except Exception as e:
        logger.warning("portfolio_fetch_error", user_id=user_id, error=str(e))
        message = "Portfolio service temporarily unavailable."

    if not policies:
        # Also try document memory for uploaded policies
        try:
            from hibiscus.memory.layers.document import get_latest_document
            doc = await get_latest_document(user_id)
            if doc and doc.get("extraction"):
                ext = doc["extraction"]
                synthetic = {
                    "policy_id": doc.get("analysis_id", "doc_" + user_id[:8]),
                    "source": "document_upload",
                    "insurer": ext.get("insurer", "Unknown"),
                    "product_name": ext.get("product_name", ""),
                    "policy_type": ext.get("policy_type", ""),
                    "policy_number": ext.get("policy_number"),
                    "sum_insured": ext.get("sum_insured"),
                    "annual_premium": ext.get("annual_premium"),
                    "eazr_score": doc.get("eazr_score"),
                }
                policies = [synthetic]
        except Exception:
            pass

    return PortfolioResponse(
        user_id=user_id,
        policies=policies,
        count=len(policies),
        message=message,
    )


@router.post("/portfolio", response_model=AddPolicyResponse)
async def add_to_portfolio(request: AddPolicyRequest, http_request: Request) -> AddPolicyResponse:
    """
    Add an insurance policy to a user's portfolio.

    If PostgreSQL is unavailable, returns success=False with a graceful message.
    """
    user_id = request.user_id
    jwt_user_id = getattr(http_request.state, "user_id", None)
    if jwt_user_id and jwt_user_id != "anonymous":
        user_id = jwt_user_id

    policy_id = str(uuid.uuid4())
    policy_data = {
        "policy_id": policy_id,
        **request.policy.model_dump(exclude_none=True),
    }

    logger.info(
        "portfolio_add",
        user_id=user_id,
        insurer=request.policy.insurer,
        policy_type=request.policy.policy_type,
    )

    try:
        from hibiscus.tools.user.portfolio import add_policy_to_portfolio
        success = await add_policy_to_portfolio(user_id, policy_data)
    except Exception as e:
        logger.warning("portfolio_add_error", user_id=user_id, error=str(e))
        success = False

    if success:
        message = f"Policy added to your portfolio (ID: {policy_id[:8]}…)"
    else:
        message = (
            "Policy received but could not be saved to your portfolio permanently. "
            "PostgreSQL connection required for persistent storage."
        )

    return AddPolicyResponse(
        success=success,
        policy_id=policy_id,
        message=message,
    )


@router.delete("/portfolio/{policy_id}")
async def remove_from_portfolio(
    policy_id: str,
    user_id: str,
    http_request: Request,
) -> JSONResponse:
    """
    Remove a policy from a user's portfolio.

    Query parameter: user_id (required unless JWT provides it)
    """
    jwt_user_id = getattr(http_request.state, "user_id", None)
    if jwt_user_id and jwt_user_id != "anonymous":
        user_id = jwt_user_id

    logger.info("portfolio_remove", user_id=user_id, policy_id=policy_id)

    try:
        from hibiscus.tools.user.portfolio import remove_policy_from_portfolio
        success = await remove_policy_from_portfolio(user_id, policy_id)
    except Exception as e:
        logger.warning("portfolio_remove_error", user_id=user_id, error=str(e))
        return JSONResponse(
            {"success": False, "message": "Portfolio service unavailable."},
            status_code=503,
        )

    if success:
        return JSONResponse({"success": True, "message": "Policy removed from portfolio."})
    return JSONResponse(
        {"success": False, "message": f"Policy {policy_id} not found or could not be removed."},
        status_code=404,
    )
