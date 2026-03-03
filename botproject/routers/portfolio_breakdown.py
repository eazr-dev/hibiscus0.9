"""
Portfolio Breakdown Router
API endpoint for getting portfolio breakdown by category

Rate Limiting: 20/minute per IP for dashboard data operations
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query, Request
from datetime import datetime

from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Portfolio Breakdown"])


@router.get("/portfolio/breakdown")
@limiter.limit(RATE_LIMITS["dashboard_data"])
async def get_portfolio_breakdown(
    request: Request,
    userId: str = Query(..., description="User ID"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get Portfolio Breakdown by Category

    Returns category-wise breakdown with coverage amounts, policy counts, and percentages.

    **Headers (Optional):**
    - access-token: {token}
    - Authorization: Bearer {token}

    **Query Parameters:**
    - userId: User ID (required)

    **Returns:**
    - Portfolio overview (total coverage, premium, protection score)
    - Category breakdown (life, health, motor, general, business, specialty, agricultural)
    - Active policy count
    """
    try:
        # Authentication check
        has_access_token = bool(access_token)
        has_auth = bool(authorization and authorization.startswith("Bearer "))

        if has_access_token:
            logger.info(f"Request authenticated with access-token header")
        elif has_auth:
            logger.info(f"Request authenticated with Authorization Bearer token")
        else:
            logger.info(f"Request without authentication (testing mode)")

        # Convert userId to int
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "userId must be a valid number"
                }
            )

        # Import MongoDB
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error_code": "SRV_5002",
                    "message": "Database not available"
                }
            )

        # Get all policies for user
        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Fetch only self policies (exclude family policies)
        # Exclude soft-deleted policies
        policies_cursor = policy_analysis_collection.find({
            "user_id": user_id_int,
            "policyFor": "self",
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        })
        policies = list(policies_cursor)

        logger.info(f"Found {len(policies)} self policies for user {user_id_int}")

        # Initialize counters
        total_policies = 0
        active_policies = 0
        total_coverage = 0
        total_premium = 0

        # Category breakdown
        category_breakdown = {
            "life": {"count": 0, "coverage": 0, "premium": 0, "icon": "shield", "color": "blue"},
            "health": {"count": 0, "coverage": 0, "premium": 0, "icon": "heart", "color": "green"},
            "motor": {"count": 0, "coverage": 0, "premium": 0, "icon": "car", "color": "orange"},
            "general": {"count": 0, "coverage": 0, "premium": 0, "icon": "home", "color": "purple"},
            "business": {"count": 0, "coverage": 0, "premium": 0, "icon": "briefcase", "color": "indigo"},
            "specialty": {"count": 0, "coverage": 0, "premium": 0, "icon": "plus", "color": "pink"},
            "agricultural": {"count": 0, "coverage": 0, "premium": 0, "icon": "tree", "color": "brown"},
            "other": {"count": 0, "coverage": 0, "premium": 0, "icon": "document", "color": "gray"}
        }

        # Process each policy
        for policy in policies:
            extracted_data = policy.get("extractedData", {})
            policy_type = extracted_data.get("policyType", "unknown").lower()

            # Determine category
            if policy_type in ["health", "medical", "mediclaim"]:
                policy_category = "health"
            elif policy_type in ["life", "term", "endowment", "ulip", "whole life"]:
                policy_category = "life"
            elif policy_type in ["motor", "car", "vehicle", "bike", "two-wheeler", "four-wheeler", "auto"]:
                policy_category = "motor"
            elif policy_type in ["general", "home", "property", "fire", "burglary", "travel", "personal accident"]:
                policy_category = "general"
            elif policy_type in ["agricultural", "crop", "livestock", "farm"]:
                policy_category = "agricultural"
            elif policy_type in ["business", "commercial", "liability", "professional indemnity", "cyber"]:
                policy_category = "business"
            elif policy_type in ["specialty", "marine", "aviation", "engineering"]:
                policy_category = "specialty"
            else:
                policy_category = "other"

            # Get coverage and premium
            coverage = extracted_data.get("coverageAmount", 0)
            premium = extracted_data.get("premium", 0)

            logger.info(f"Policy {policy.get('analysisId', 'unknown')}: type={policy_type}, category={policy_category}, coverage={coverage}, premium={premium}")

            # Check if active (for counting active policies)
            end_date_str = extracted_data.get("endDate", "")
            is_active = True
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                    if end_date < datetime.now():
                        is_active = False
                except:
                    is_active = True

            # Update counters (include ALL policies in breakdown)
            total_policies += 1
            total_coverage += coverage
            total_premium += premium

            if is_active:
                active_policies += 1

            # Update category breakdown (include ALL policies, not just active)
            if policy_category in category_breakdown:
                category_breakdown[policy_category]["count"] += 1
                category_breakdown[policy_category]["coverage"] += coverage
                category_breakdown[policy_category]["premium"] += premium

        # Format categories for response (include ALL categories, even with zero)
        categories = []
        for category_name, data in category_breakdown.items():
            # Calculate percentage
            percentage = round((data["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)

            # Format coverage
            coverage_value = data["coverage"]
            if coverage_value >= 10000000:  # >= 1 Cr
                coverage_formatted = f"₹{coverage_value/10000000:.1f}Cr"
            elif coverage_value >= 100000:  # >= 1 L
                coverage_formatted = f"₹{coverage_value/100000:.1f}L"
            elif coverage_value > 0:
                coverage_formatted = f"₹{coverage_value:,.0f}"
            else:
                coverage_formatted = "₹0"

            categories.append({
                "category": category_name,
                "categoryName": category_name.title(),
                "icon": data["icon"],
                "color": data["color"],
                "policyCount": data["count"],
                "coverage": data["coverage"],
                "coverageFormatted": coverage_formatted,
                "premium": data["premium"],
                "percentage": percentage
            })

        # Sort categories: non-zero first (by coverage), then zero categories
        categories.sort(key=lambda x: (x["coverage"] == 0, -x["coverage"]))

        # Calculate overall protection score (average of all policies)
        protection_scores = []
        for policy in policies:
            score = policy.get("protectionScore")
            if score is not None:
                protection_scores.append(score)

        avg_protection_score = round(sum(protection_scores) / len(protection_scores)) if protection_scores else 95

        # Format total coverage
        if total_coverage >= 10000000:
            total_coverage_formatted = f"₹{total_coverage/10000000:.1f}Cr"
        elif total_coverage >= 100000:
            total_coverage_formatted = f"₹{total_coverage/100000:.1f}L"
        else:
            total_coverage_formatted = f"₹{total_coverage:,.0f}"

        # Build response
        response = {
            "success": True,
            "userId": userId,
            "portfolioOverview": {
                "totalCoverage": total_coverage,
                "totalCoverageFormatted": total_coverage_formatted,
                "totalPremium": total_premium,
                "totalPremiumFormatted": f"₹{total_premium:,.0f}",
                "protectionScore": avg_protection_score,
                "activePolicies": active_policies,
                "totalPolicies": total_policies
            },
            "categoryBreakdown": categories
        }

        return response

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error fetching portfolio breakdown: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to fetch portfolio breakdown"
            }
        )
