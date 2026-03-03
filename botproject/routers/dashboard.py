"""
Dashboard Router
API endpoints for dashboard data including Protection Score calculation

Protection Score Formula (from protection_score_api_spec.md):
Overall Score = (Coverage Adequacy × 0.40) +
                (Portfolio Diversity × 0.30) +
                (Cost Efficiency × 0.20) +
                (Policy Freshness × 0.10)

Rate Limiting Applied (Redis-backed):
- Dashboard data: 20/minute per IP
- Protection score: 10/minute per IP
- Insights/Renewals: 20/minute per IP
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query, Body, Request
from datetime import datetime, timedelta
from pydantic import BaseModel

from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Dashboard"])


# ==================== PYDANTIC MODELS ====================

class RefreshScoreRequest(BaseModel):
    annualIncome: Optional[float] = None
    reason: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

def calculate_coverage_adequacy(total_coverage: float, annual_income: float = None) -> Dict[str, Any]:
    """
    Factor 1: Coverage Adequacy (40% Weight)
    Measures if the user has enough coverage relative to their income.
    Ideal: Total coverage should be 10-15× annual income.

    When income is NOT provided, score is based on absolute coverage amount:
    - ₹1Cr+ coverage = 90-100 score
    - ₹50L-1Cr = 70-89 score
    - ₹25L-50L = 50-69 score
    - ₹10L-25L = 30-49 score
    - Below ₹10L = 10-29 score

    Returns dict with score and details
    """
    recommended_coverage = 0
    coverage_ratio = 0
    message = ""

    if annual_income and annual_income > 0:
        # WITH INCOME: Score based on coverage-to-income ratio
        recommended_coverage = annual_income * 10
        coverage_ratio = round(total_coverage / recommended_coverage, 2) if recommended_coverage > 0 else 0

        # Score mapping based on spec
        if coverage_ratio >= 1.0:
            score = 100
        elif coverage_ratio >= 0.8:
            score = int(80 + (coverage_ratio - 0.8) * 100)
        elif coverage_ratio >= 0.5:
            score = int(50 + (coverage_ratio - 0.5) * 100)
        else:
            score = int(coverage_ratio * 100)

        score = max(0, min(100, score))
        percentage = int(coverage_ratio * 100)
        message = f"Your coverage is {percentage}% of recommended 10x annual income"
    else:
        # WITHOUT INCOME: Score based on absolute coverage amount
        # This gives a fair score even when user hasn't added income
        if total_coverage >= 10000000:  # ₹1Cr+
            score = 95
            message = f"Excellent coverage of {format_currency(total_coverage)}"
        elif total_coverage >= 5000000:  # ₹50L-1Cr
            score = 80
            message = f"Good coverage of {format_currency(total_coverage)}"
        elif total_coverage >= 2500000:  # ₹25L-50L
            score = 65
            message = f"Moderate coverage of {format_currency(total_coverage)}"
        elif total_coverage >= 1000000:  # ₹10L-25L
            score = 50
            message = f"Basic coverage of {format_currency(total_coverage)}"
        elif total_coverage > 0:
            score = 35
            message = f"Limited coverage of {format_currency(total_coverage)}. Consider increasing."
        else:
            score = 0
            message = "No coverage yet. Add your first policy."

    return {
        "score": score,
        "weight": 40,
        "weightedScore": round(score * 0.40, 1),
        "details": {
            "recommendedCoverage": recommended_coverage,
            "actualCoverage": total_coverage,
            "coverageRatio": coverage_ratio,
            "message": message
        }
    }


def calculate_portfolio_diversity(categories: Dict[str, int]) -> Dict[str, Any]:
    """
    Factor 2: Portfolio Diversity (30% Weight)
    Measures if the user has coverage across different insurance categories.
    Ideal: Having both Life and Health insurance (essential) plus other categories.

    Returns dict with score and details
    """
    # Get categories with at least 1 policy
    covered_categories = [cat for cat, count in categories.items() if count > 0]

    # Essential categories
    essential_categories = ["life", "health", "motor", "general"]
    missing_categories = [cat for cat in essential_categories if categories.get(cat, 0) == 0]

    # Calculate diversity ratio
    covered_essential = len([c for c in covered_categories if c in essential_categories])
    total_essential = len(essential_categories)

    # Score calculation
    score = int((covered_essential / total_essential) * 100)
    score = max(0, min(100, score))

    message = f"Covering {covered_essential} of {total_essential} essential insurance categories"

    return {
        "score": score,
        "weight": 30,
        "weightedScore": round(score * 0.30, 1),
        "details": {
            "totalCategories": total_essential,
            "coveredCategories": covered_essential,
            "missingCategories": missing_categories,
            "message": message
        }
    }


def calculate_cost_efficiency(total_coverage: float, total_premium: float, annual_income: float = None) -> Dict[str, Any]:
    """
    Factor 3: Cost Efficiency (20% Weight)
    Measures if the user is getting good value (coverage per rupee of premium).

    WITHOUT INCOME: Score based purely on coverage-to-premium ratio
    - ₹100+ coverage per ₹1 premium = Excellent (90+)
    - ₹50-100 coverage per ₹1 premium = Good (70-89)
    - ₹20-50 coverage per ₹1 premium = Fair (50-69)
    - Below ₹20 = Needs improvement

    Returns dict with score and details
    """
    premium_to_income_ratio = 0
    coverage_per_rupee = 0
    message = ""

    # Calculate coverage-to-premium ratio (works without income)
    if total_premium > 0 and total_coverage > 0:
        coverage_per_rupee = round(total_coverage / total_premium, 1)

        # Score based on coverage per rupee of premium
        if coverage_per_rupee >= 100:
            score = 95
            message = f"Excellent value: ₹{coverage_per_rupee:.0f} coverage per ₹1 premium"
        elif coverage_per_rupee >= 50:
            score = 80
            message = f"Good value: ₹{coverage_per_rupee:.0f} coverage per ₹1 premium"
        elif coverage_per_rupee >= 20:
            score = 60
            message = f"Fair value: ₹{coverage_per_rupee:.0f} coverage per ₹1 premium"
        elif coverage_per_rupee >= 10:
            score = 45
            message = f"Below average: ₹{coverage_per_rupee:.0f} coverage per ₹1 premium"
        else:
            score = 30
            message = f"Low value: Consider reviewing your policies"

        # If income is available, adjust based on premium-to-income ratio
        if annual_income and annual_income > 0:
            premium_to_income_ratio = round(total_premium / annual_income, 3)
            percentage = round(premium_to_income_ratio * 100, 1)

            if 0.05 <= premium_to_income_ratio <= 0.10:
                # Ideal range - boost score
                score = min(100, score + 10)
                message += f" | Premium is {percentage}% of income (ideal)"
            elif premium_to_income_ratio > 0.15:
                # Too high - reduce score
                score = max(0, score - 15)
                message += f" | Premium is {percentage}% of income (high)"
    else:
        score = 70  # Default when no premium data
        message = "Add policies to calculate cost efficiency"

    score = max(0, min(100, score))

    return {
        "score": score,
        "weight": 20,
        "weightedScore": round(score * 0.20, 1),
        "details": {
            "totalPremium": total_premium,
            "totalCoverage": total_coverage,
            "coveragePerRupee": coverage_per_rupee,
            "premiumToIncomeRatio": premium_to_income_ratio,
            "message": message
        }
    }


def calculate_policy_freshness(policies: List[Dict], active_count: int, expiring_count: int, expired_count: int) -> Dict[str, Any]:
    """
    Factor 4: Policy Freshness (10% Weight)
    Measures what percentage of policies are currently active (not expired).
    Ideal: All policies should be active.

    Returns dict with score and details
    """
    total_count = len(policies)

    if total_count > 0:
        # Active policies get full credit, expiring gets partial
        effective_active = active_count + (expiring_count * 0.5)
        base_score = int((effective_active / total_count) * 100)

        # Penalty for expiring policies
        expiring_penalty = expiring_count * 5
        score = max(0, base_score - expiring_penalty)
    else:
        score = 0

    score = max(0, min(100, score))

    if expiring_count > 0:
        message = f"{expiring_count} policy expiring within 60 days"
    elif expired_count > 0:
        message = f"{expired_count} policy has expired"
    else:
        message = "All policies are active"

    return {
        "score": score,
        "weight": 10,
        "weightedScore": round(score * 0.10, 1),
        "details": {
            "totalPolicies": total_count,
            "activePolicies": active_count,
            "expiringSoon": expiring_count,
            "expired": expired_count,
            "message": message
        }
    }


def get_score_category(score: int) -> str:
    """Get score category label based on score value"""
    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    else:
        return "Needs Improvement"


def get_score_color(score: int) -> str:
    """Get score color based on value"""
    if score >= 90:
        return "#10B981"  # Green
    elif score >= 70:
        return "#8B5CF6"  # Purple
    elif score >= 50:
        return "#F59E0B"  # Orange
    else:
        return "#EF4444"  # Red


def format_currency(amount: float) -> str:
    """Format currency value to Indian format (Cr/L/K)"""
    if amount is None:
        return "₹0"
    if amount >= 10000000:  # >= 1 Cr
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # >= 1 L
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:  # >= 1 K
        return f"₹{amount/1000:.1f}K"
    elif amount > 0:
        return f"₹{amount:,.0f}"
    else:
        return "₹0"


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in multiple formats"""
    if not date_str:
        return None

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_user_annual_income(user_id: int, db) -> Optional[float]:
    """
    Fetch user's annual income from their profile in MongoDB.
    Returns None if not found.
    """
    try:
        users_collection = db['user_profiles']
        user_profile = users_collection.find_one({"user_id": user_id})

        if user_profile:
            # Check in preferences
            preferences = user_profile.get("preferences", {})

            # Try different field names that might store income
            income = preferences.get("annualIncome") or preferences.get("annual_income") or preferences.get("income")

            if income:
                # Convert to float if string
                if isinstance(income, str):
                    # Remove currency symbols and commas
                    income = income.replace("₹", "").replace(",", "").replace(" ", "").strip()
                    try:
                        return float(income)
                    except ValueError:
                        return None
                return float(income)

        return None
    except Exception as e:
        logger.warning(f"Could not fetch annual income for user {user_id}: {e}")
        return None


def calculate_policy_status(end_date_str: str) -> str:
    """Calculate policy status based on end date"""
    if not end_date_str:
        return "active"

    end_date = parse_date(end_date_str)
    if not end_date:
        return "active"

    today = datetime.now()
    days_left = (end_date - today).days

    if days_left < 0:
        return "expired"
    elif days_left <= 60:
        return "expiring_soon"
    else:
        return "active"


def get_days_left(end_date_str: str) -> int:
    """Get days left until policy expiry"""
    if not end_date_str:
        return 365  # Default to 1 year if no date

    end_date = parse_date(end_date_str)
    if not end_date:
        return 365

    return (end_date - datetime.now()).days


def get_policy_category(policy_type: str) -> str:
    """Determine policy category from policy type"""
    policy_type = policy_type.lower() if policy_type else "other"

    if policy_type in ["health", "medical", "mediclaim"]:
        return "health"
    elif policy_type in ["life", "term", "endowment", "ulip", "whole life"]:
        return "life"
    elif policy_type in ["motor", "car", "vehicle", "bike", "two-wheeler", "four-wheeler", "auto"]:
        return "motor"
    elif policy_type in ["accidental", "accident", "personal accident", "pa", "personal accidental"]:
        return "accidental"
    elif policy_type in ["travel"]:
        return "travel"
    elif policy_type in ["home", "property", "fire", "burglary"]:
        return "home"
    elif policy_type in ["general"]:
        return "general"
    elif policy_type in ["agricultural", "crop", "livestock", "farm"]:
        return "agricultural"
    elif policy_type in ["business", "commercial", "liability", "professional indemnity", "cyber"]:
        return "business"
    elif policy_type in ["specialty", "marine", "aviation", "engineering"]:
        return "specialty"
    else:
        return "other"


def generate_insights(
    policies: List[Dict],
    categories: Dict[str, int],
    annual_income: float = None,
    total_coverage: float = 0
) -> List[Dict[str, Any]]:
    """
    Generate AI-like insights based on policy data
    Returns insights in the format specified by the API spec

    Note: Returns empty list if user has no policies (first-time user)
    """
    insights = []

    # If user has no policies, return empty insights
    # First-time users should not see gap recommendations
    if len(policies) == 0:
        return insights

    # Rule 1: Missing Health Insurance (Gap)
    if categories.get("health", 0) == 0:
        insights.append({
            "id": "insight_health_gap",
            "type": "gap",
            "severity": "high",
            "title": "No Health Coverage",
            "description": "Medical emergencies can be financially devastating. Consider health insurance.",
            "actionText": "Add Health Policy",
            "actionType": "add_policy",
            "actionData": {"category": "health"}
        })

    # Rule 2: Missing Life Insurance (Gap)
    if categories.get("life", 0) == 0:
        insights.append({
            "id": "insight_life_gap",
            "type": "gap",
            "severity": "high",
            "title": "No Life Insurance",
            "description": "Protect your family's financial future with term life insurance.",
            "actionText": "Add Life Policy",
            "actionType": "add_policy",
            "actionData": {"category": "life"}
        })

    # Rule 3: Missing Motor Insurance (Gap)
    if categories.get("motor", 0) == 0:
        insights.append({
            "id": "insight_motor_gap",
            "type": "gap",
            "severity": "medium",
            "title": "No Motor Insurance",
            "description": "You don't have motor insurance coverage",
            "actionText": "Add Motor Policy",
            "actionType": "add_policy",
            "actionData": {"category": "motor"}
        })

    # Rule 4: Low Life Coverage (Recommendation)
    life_coverage = sum(
        p.get("extractedData", {}).get("coverageAmount", 0) or 0
        for p in policies
        if get_policy_category(p.get("extractedData", {}).get("policyType", "")) == "life"
    )

    # Check if life coverage is low (either against income or absolute amount)
    if life_coverage > 0:
        if annual_income and annual_income > 0 and life_coverage < annual_income * 5:
            # Has income data - compare against income
            insights.append({
                "id": "insight_low_life_cover",
                "type": "recommendation",
                "severity": "medium",
                "title": "Increase Life Coverage",
                "description": f"Consider increasing life cover to 10x annual income ({format_currency(annual_income * 10)})",
                "actionText": "Compare Plans",
                "actionType": "compare_plans",
                "actionData": {"category": "life"}
            })
        elif not annual_income and life_coverage < 2500000:  # Less than ₹25L without income data
            insights.append({
                "id": "insight_low_life_cover",
                "type": "recommendation",
                "severity": "medium",
                "title": "Consider More Life Coverage",
                "description": f"Your life coverage is {format_currency(life_coverage)}. Consider increasing for better protection.",
                "actionText": "Compare Plans",
                "actionType": "compare_plans",
                "actionData": {"category": "life"}
            })

    # Rule 5: Expiring Soon Alert
    expiring_policies = []
    for p in policies:
        extracted_data = p.get("extractedData", {})
        end_date_str = extracted_data.get("endDate", "")
        days_left = get_days_left(end_date_str)

        if 0 < days_left <= 60:
            expiring_policies.append({
                "policyId": p.get("analysisId", ""),
                "policyName": extracted_data.get("insuranceProvider", "Unknown"),
                "daysLeft": days_left
            })

    for exp_policy in expiring_policies[:3]:  # Limit to 3 expiring alerts
        severity = "high" if exp_policy["daysLeft"] <= 30 else "medium"
        insights.append({
            "id": f"insight_expiring_{exp_policy['policyId']}",
            "type": "alert",
            "severity": severity,
            "title": "Policy Expiring Soon",
            "description": f"Your {exp_policy['policyName']} policy expires in {exp_policy['daysLeft']} days",
            "actionText": "Renew Now",
            "actionType": "renew_policy",
            "actionData": {"policyId": exp_policy["policyId"]}
        })

    # Rule 6: Expired Policy Alert (NEW)
    expired_policies_list = []
    for p in policies:
        extracted_data = p.get("extractedData", {})
        end_date_str = extracted_data.get("endDate", "")
        days_left = get_days_left(end_date_str)

        if days_left < 0:  # Already expired
            expired_policies_list.append({
                "policyId": p.get("analysisId", ""),
                "policyName": extracted_data.get("insuranceProvider", "Unknown"),
                "daysExpired": abs(days_left),
                "category": get_policy_category(extracted_data.get("policyType", ""))
            })

    # Add expired policy insights (high severity)
    for exp_policy in expired_policies_list[:3]:  # Limit to 3 expired alerts
        insights.append({
            "id": f"insight_expired_{exp_policy['policyId']}",
            "type": "alert",
            "severity": "high",
            "title": "Policy Expired",
            "description": f"Your {exp_policy['policyName']} policy expired {exp_policy['daysExpired']} days ago. Renew immediately to restore coverage.",
            "actionText": "Renew Now",
            "actionType": "renew_policy",
            "actionData": {"policyId": exp_policy["policyId"], "isExpired": True}
        })

    # Rule 7: Good Portfolio Achievement
    covered_cats = [cat for cat, count in categories.items() if count > 0 and cat in ["life", "health", "motor", "general"]]
    if len(covered_cats) >= 3 and "life" in covered_cats and "health" in covered_cats:
        insights.append({
            "id": "insight_diversified",
            "type": "achievement",
            "severity": "low",
            "title": "Well-Diversified Portfolio",
            "description": "Great job! You have comprehensive coverage across categories.",
            "actionText": None,
            "actionType": None,
            "actionData": None
        })

    # Sort by severity (high first)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    insights.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return insights


def get_upcoming_renewals(policies: List[Dict], within_days: int = 90) -> List[Dict]:
    """
    Get policies expiring within the specified number of days
    Returns renewals in the format specified by the API spec
    """
    renewals = []
    today = datetime.now()

    for policy in policies:
        extracted_data = policy.get("extractedData", {})
        end_date_str = extracted_data.get("endDate", "")
        end_date = parse_date(end_date_str)

        if not end_date:
            continue

        days_left = (end_date - today).days

        # Include if: expiry is AFTER today AND BEFORE cutoff
        if 0 < days_left <= within_days:
            category = get_policy_category(extracted_data.get("policyType", ""))

            renewals.append({
                "policyId": policy.get("analysisId", ""),
                "policyName": extracted_data.get("insuranceProvider", "Unknown Policy"),
                "provider": extracted_data.get("insuranceProvider", ""),
                "category": category,
                "daysLeft": days_left,
                "premium": extracted_data.get("premium", 0) or 0,
                "expiryDate": end_date_str,
                "isUrgent": days_left <= 30
            })

    # Sort by days left (nearest first)
    renewals.sort(key=lambda x: x["daysLeft"])

    return renewals


def get_expired_policies(policies: List[Dict]) -> List[Dict]:
    """
    Get policies that have already expired.
    Returns expired policies sorted by most recently expired first.
    """
    expired = []
    today = datetime.now()

    for policy in policies:
        extracted_data = policy.get("extractedData", {})
        end_date_str = extracted_data.get("endDate", "")
        end_date = parse_date(end_date_str)

        if not end_date:
            continue

        days_expired = (today - end_date).days

        # Include if policy has expired (end_date is in the past)
        if days_expired > 0:
            category = get_policy_category(extracted_data.get("policyType", ""))

            expired.append({
                "policyId": policy.get("analysisId", ""),
                "policyName": extracted_data.get("insuranceProvider", "Unknown Policy"),
                "policyNumber": extracted_data.get("policyNumber", ""),
                "provider": extracted_data.get("insuranceProvider", ""),
                "category": category,
                "categoryName": category.title(),
                "policyType": extracted_data.get("policyType", ""),
                "daysExpired": days_expired,
                "expiredDate": end_date_str,
                "expiredDateFormatted": end_date.strftime("%d %b %Y") if end_date else "",
                "coverage": extracted_data.get("coverageAmount", 0) or 0,
                "coverageFormatted": format_currency(extracted_data.get("coverageAmount", 0) or 0),
                "premium": extracted_data.get("premium", 0) or 0,
                "premiumFormatted": format_currency(extracted_data.get("premium", 0) or 0),
                "status": "expired",
                "statusColor": "#EF4444",  # Red
                "actionRequired": "Renew this policy to restore coverage"
            })

    # Sort by most recently expired first (least days_expired first)
    expired.sort(key=lambda x: x["daysExpired"])

    return expired


def get_score_journey(user_id: int, current_score: int, db) -> Dict[str, Any]:
    """
    Calculate score journey data for Activity Summary Card

    Returns:
    - scoreStart: First score when user joined
    - scoreCurrent: Current protection score
    - scoreChange: Total improvement since start
    - trend: Change from last period (30 days)
    """
    try:
        snapshots_collection = db.get('protection_score_snapshots')

        score_start = current_score
        trend = 0

        if snapshots_collection:
            # Get first ever score
            first_snapshot = snapshots_collection.find_one(
                {"user_id": user_id},
                sort=[("snapshot_date", 1)]
            )
            if first_snapshot:
                score_start = first_snapshot.get("overall_score", current_score)

            # Get score from 30 days ago
            thirty_days_ago = datetime.now() - timedelta(days=30)
            old_snapshot = snapshots_collection.find_one(
                {"user_id": user_id, "snapshot_date": {"$lte": thirty_days_ago}},
                sort=[("snapshot_date", -1)]
            )
            if old_snapshot:
                trend = current_score - old_snapshot.get("overall_score", current_score)

        score_change = current_score - score_start

        return {
            "scoreStart": score_start,
            "scoreCurrent": current_score,
            "scoreChange": score_change,
            "trend": trend,
            "trendPeriod": "30d",
            "periodStart": (datetime.now() - timedelta(days=30)).isoformat() + "Z",
            "periodEnd": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        logger.warning(f"Could not calculate score journey: {e}")
        return {
            "scoreStart": current_score,
            "scoreCurrent": current_score,
            "scoreChange": 0,
            "trend": 0,
            "trendPeriod": "30d",
            "periodStart": (datetime.now() - timedelta(days=30)).isoformat() + "Z",
            "periodEnd": datetime.now().isoformat() + "Z"
        }


def store_score_snapshot(user_id: int, score_data: Dict, db):
    """Store a score snapshot for history tracking"""
    try:
        snapshots_collection = db.get('protection_score_snapshots')
        if snapshots_collection is None:
            # Create collection if it doesn't exist
            db.create_collection('protection_score_snapshots')
            snapshots_collection = db['protection_score_snapshots']

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Upsert today's snapshot
        snapshots_collection.update_one(
            {"user_id": user_id, "snapshot_date": today},
            {"$set": {
                "user_id": user_id,
                "snapshot_date": today,
                "overall_score": score_data.get("overallScore", 0),
                "coverage_adequacy": score_data.get("factors", {}).get("coverageAdequacy", {}).get("score", 0),
                "portfolio_diversity": score_data.get("factors", {}).get("portfolioDiversity", {}).get("score", 0),
                "cost_efficiency": score_data.get("factors", {}).get("costEfficiency", {}).get("score", 0),
                "policy_freshness": score_data.get("factors", {}).get("policyFreshness", {}).get("score", 0),
                "created_at": datetime.utcnow()
            }},
            upsert=True
        )
    except Exception as e:
        logger.warning(f"Could not store score snapshot: {e}")


# ==================== API ENDPOINTS ====================

@router.get("/v1/users/{userId}/protection-score")
@limiter.limit(RATE_LIMITS["protection_score"])
async def get_protection_score_v1(
    request: Request,
    userId: str,
    annualIncome: Optional[float] = Query(None, description="User's annual income for accurate score calculation"),
    forceRefresh: bool = Query(False, description="Skip cache, recalculate fresh"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get Protection Score with detailed breakdown (API v1)

    Matches the API specification in protection_score_api_spec.md

    **Formula:**
    ```
    Overall Score = (Coverage Adequacy × 0.40) +
                    (Portfolio Diversity × 0.30) +
                    (Cost Efficiency × 0.20) +
                    (Policy Freshness × 0.10)
    ```
    """
    try:
        # Convert userId to int
        try:
            user_id_int = int(userId)
        except ValueError:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "userId must be a valid number"
                }
            }

        # Import MongoDB
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            return {
                "success": False,
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database not available"
                }
            }

        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Get all policies for user (all types, exclude deleted)
        policies_cursor = policy_analysis_collection.find({
            "user_id": user_id_int,
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        })
        policies = list(policies_cursor)

        logger.info(f"Calculating protection score v1 for user {user_id_int} with {len(policies)} policies")

        # Auto-fetch annual income if not provided
        user_annual_income = annualIncome
        if user_annual_income is None:
            user_annual_income = get_user_annual_income(user_id_int, db)

        # Initialize counters
        total_coverage = 0
        total_premium = 0
        active_count = 0
        expiring_count = 0
        expired_count = 0

        # Category counts
        categories = {
            "life": 0, "health": 0, "motor": 0, "accidental": 0, "travel": 0, "home": 0,
            "general": 0, "agricultural": 0, "business": 0, "specialty": 0, "other": 0
        }

        # Process each policy
        for policy in policies:
            extracted_data = policy.get("extractedData", {})

            coverage = extracted_data.get("coverageAmount", 0) or 0
            premium = extracted_data.get("premium", 0) or 0

            total_coverage += coverage
            total_premium += premium

            # Determine category
            category = get_policy_category(extracted_data.get("policyType", ""))
            categories[category] += 1

            # Check status
            status = calculate_policy_status(extracted_data.get("endDate", ""))
            if status == "active":
                active_count += 1
            elif status == "expiring_soon":
                expiring_count += 1
            else:
                expired_count += 1

        # Calculate factor scores with details
        coverage_adequacy = calculate_coverage_adequacy(total_coverage, user_annual_income)
        portfolio_diversity = calculate_portfolio_diversity(categories)
        cost_efficiency = calculate_cost_efficiency(total_coverage, total_premium, user_annual_income)
        policy_freshness = calculate_policy_freshness(policies, active_count, expiring_count, expired_count)

        # Calculate overall score
        overall_score = int(
            coverage_adequacy["weightedScore"] +
            portfolio_diversity["weightedScore"] +
            cost_efficiency["weightedScore"] +
            policy_freshness["weightedScore"]
        )
        overall_score = max(0, min(100, overall_score))

        # Get score journey
        score_journey = get_score_journey(user_id_int, overall_score, db)

        # Generate insights
        insights = generate_insights(policies, categories, user_annual_income, total_coverage)

        # Get upcoming renewals
        upcoming_renewals = get_upcoming_renewals(policies, within_days=90)

        # Count family members from family policies (within already-fetched policies)
        family_policies = [p for p in policies if p.get("policyFor") == "family"]
        family_members = set()
        for fp in family_policies:
            holder = fp.get("policyHolder", {})
            if holder.get("name"):
                family_members.add(holder.get("name"))

        # Build response matching API spec
        response_data = {
            "overallScore": overall_score,
            "category": get_score_category(overall_score),
            "lastCalculatedAt": datetime.utcnow().isoformat() + "Z",

            "scoreJourney": score_journey,

            "factors": {
                "coverageAdequacy": coverage_adequacy,
                "portfolioDiversity": portfolio_diversity,
                "costEfficiency": cost_efficiency,
                "policyFreshness": policy_freshness
            },

            "insights": insights[:5],  # Limit to 5

            "upcomingRenewals": upcoming_renewals[:5],  # Limit to 5

            "summary": {
                "totalPolicies": len(policies),
                "activePolicies": active_count,
                "totalCoverage": total_coverage,
                "totalPremium": total_premium,
                "familyMembersCovered": len(family_members)
            }
        }

        # Store snapshot for history tracking
        store_score_snapshot(user_id_int, response_data, db)

        return {
            "success": True,
            "data": response_data
        }

    except Exception as e:
        logger.error(f"Error calculating protection score v1: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Failed to calculate protection score"
            }
        }


@router.get("/v1/users/{userId}/protection-score/history")
@limiter.limit(RATE_LIMITS["dashboard_data"])
async def get_protection_score_history(
    request: Request,
    userId: str,
    period: str = Query("6m", description="Time period: 1m, 3m, 6m, 1y"),
    granularity: str = Query("monthly", description="Data points: daily, weekly, monthly"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get Protection Score History

    Returns historical scores for trend chart.
    """
    try:
        user_id_int = int(userId)

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            return {
                "success": False,
                "error": {"code": "DATABASE_UNAVAILABLE", "message": "Database not available"}
            }

        db = mongodb_chat_manager.db

        # Calculate period dates
        period_days = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}
        days = period_days.get(period, 180)
        period_start = datetime.now() - timedelta(days=days)
        period_end = datetime.now()

        # Get snapshots from database
        snapshots_collection = db.get('protection_score_snapshots')
        history = []

        if snapshots_collection:
            snapshots_cursor = snapshots_collection.find({
                "user_id": user_id_int,
                "snapshot_date": {"$gte": period_start}
            }).sort("snapshot_date", 1)

            for snapshot in snapshots_cursor:
                history.append({
                    "date": snapshot.get("snapshot_date", datetime.now()).strftime("%Y-%m-%d"),
                    "score": snapshot.get("overall_score", 0),
                    "factors": {
                        "coverageAdequacy": snapshot.get("coverage_adequacy", 0),
                        "portfolioDiversity": snapshot.get("portfolio_diversity", 0),
                        "costEfficiency": snapshot.get("cost_efficiency", 0),
                        "policyFreshness": snapshot.get("policy_freshness", 0)
                    },
                    "events": []  # Events would come from a separate events collection
                })

        # Calculate statistics
        scores = [h["score"] for h in history] if history else [0]
        current_score = scores[-1] if scores else 0

        # Calculate trend
        first_score = scores[0] if scores else current_score
        trend_direction = "up" if current_score > first_score else ("down" if current_score < first_score else "stable")
        trend_change = current_score - first_score
        trend_percentage = round((trend_change / first_score * 100) if first_score > 0 else 0, 1)

        return {
            "success": True,
            "data": {
                "currentScore": current_score,
                "periodStart": period_start.strftime("%Y-%m-%d"),
                "periodEnd": period_end.strftime("%Y-%m-%d"),
                "trend": {
                    "direction": trend_direction,
                    "change": trend_change,
                    "percentageChange": trend_percentage
                },
                "history": history,
                "milestones": [],  # Would be populated from events
                "statistics": {
                    "highestScore": max(scores) if scores else 0,
                    "highestScoreDate": "",
                    "lowestScore": min(scores) if scores else 0,
                    "lowestScoreDate": "",
                    "averageScore": round(sum(scores) / len(scores)) if scores else 0,
                    "totalPoliciesAdded": 0,
                    "totalPoliciesRenewed": 0
                }
            }
        }

    except ValueError:
        return {
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid userId"}
        }
    except Exception as e:
        logger.error(f"Error fetching protection score history: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to fetch score history"}
        }


@router.post("/v1/users/{userId}/protection-score/refresh")
@limiter.limit(RATE_LIMITS["protection_score"])
async def refresh_protection_score(
    request: Request,
    userId: str,
    refresh_request: RefreshScoreRequest = Body(...),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Refresh Protection Score

    Force recalculate after policy changes.
    """
    try:
        user_id_int = int(userId)

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            return {
                "success": False,
                "error": {"code": "DATABASE_UNAVAILABLE", "message": "Database not available"}
            }

        db = mongodb_chat_manager.db

        # Get previous score
        snapshots_collection = db.get('protection_score_snapshots')
        previous_score = 0

        if snapshots_collection:
            last_snapshot = snapshots_collection.find_one(
                {"user_id": user_id_int},
                sort=[("snapshot_date", -1)]
            )
            if last_snapshot:
                previous_score = last_snapshot.get("overall_score", 0)

        # Calculate new score
        result = await get_protection_score_v1(
            request=request,
            userId=userId,
            annualIncome=refresh_request.annualIncome,
            forceRefresh=True
        )

        if result.get("success"):
            new_score = result["data"]["overallScore"]
            change = new_score - previous_score

            message = f"Score improved by {change} points" if change > 0 else \
                      f"Score decreased by {abs(change)} points" if change < 0 else \
                      "Score unchanged"

            if refresh_request.reason:
                message += f" after {refresh_request.reason.replace('_', ' ')}"

            return {
                "success": True,
                "data": {
                    "previousScore": previous_score,
                    "newScore": new_score,
                    "change": change,
                    "message": message
                }
            }
        else:
            return result

    except ValueError:
        return {
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid userId"}
        }
    except Exception as e:
        logger.error(f"Error refreshing protection score: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to refresh score"}
        }


# ==================== LEGACY ENDPOINTS (for backward compatibility) ====================

@router.get("/dashboard/protection-score")
@limiter.limit(RATE_LIMITS["protection_score"])
async def get_protection_score(
    request: Request,
    userId: str = Query(..., description="User ID"),
    annualIncome: Optional[float] = Query(None, description="User's annual income for accurate score calculation"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get Protection Score (Legacy endpoint)

    Redirects to v1 API internally but returns in old format for compatibility.
    """
    result = await get_protection_score_v1(request, userId, annualIncome, False, access_token, authorization)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", {}))

    data = result["data"]

    # Transform to legacy format
    return {
        "success": True,
        "userId": userId,
        "protectionScore": {
            "overall": data["overallScore"],
            "category": data["category"],
            "color": get_score_color(data["overallScore"]),
            "factors": {
                "coverageAdequacy": {
                    "score": data["factors"]["coverageAdequacy"]["score"],
                    "weight": 0.40,
                    "weightedScore": data["factors"]["coverageAdequacy"]["weightedScore"],
                    "description": "Measures if your total coverage is adequate relative to your income",
                    "ideal": "Coverage should be 10-15× annual income"
                },
                "portfolioDiversity": {
                    "score": data["factors"]["portfolioDiversity"]["score"],
                    "weight": 0.30,
                    "weightedScore": data["factors"]["portfolioDiversity"]["weightedScore"],
                    "description": "Measures coverage across different insurance categories",
                    "ideal": "Have both Life and Health insurance plus other categories"
                },
                "costEfficiency": {
                    "score": data["factors"]["costEfficiency"]["score"],
                    "weight": 0.20,
                    "weightedScore": data["factors"]["costEfficiency"]["weightedScore"],
                    "description": "Measures value for money (coverage per rupee of premium)",
                    "ideal": "Higher coverage for lower premium"
                },
                "policyFreshness": {
                    "score": data["factors"]["policyFreshness"]["score"],
                    "weight": 0.10,
                    "weightedScore": data["factors"]["policyFreshness"]["weightedScore"],
                    "description": "Percentage of policies that are currently active",
                    "ideal": "All policies should be active and not expired"
                }
            }
        },
        "scoreJourney": data["scoreJourney"],
        "summary": data["summary"],
        "insights": data["insights"],
        "upcomingRenewals": data["upcomingRenewals"],
        "calculatedAt": data["lastCalculatedAt"]
    }


@router.get("/dashboard/data")
@limiter.limit(RATE_LIMITS["dashboard_data"])
async def get_dashboard_data_legacy(
    request: Request,
    userId: str = Query(..., description="User ID"),
    annualIncome: Optional[float] = Query(None, description="User's annual income"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get Complete Dashboard Data

    Returns all data needed for the dashboard.
    """
    try:
        user_id_int = int(userId)

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(status_code=503, detail="Database not available")

        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Auto-fetch annual income
        user_annual_income = annualIncome
        income_source = "query_parameter" if annualIncome else None

        if user_annual_income is None:
            user_annual_income = get_user_annual_income(user_id_int, db)
            income_source = "user_profile" if user_annual_income else "not_available"

        # Get all policies for user (all types, exclude deleted)
        all_policies = list(policy_analysis_collection.find({
            "user_id": user_id_int,
            "$or": [{"isDeleted": {"$exists": False}}, {"isDeleted": False}]
        }).sort("created_at", -1))

        # Separate family policies for family data section
        family_policies = [p for p in all_policies if p.get("policyFor") == "family"]

        # Process all policies for score calculation
        total_coverage = 0
        total_premium = 0
        active_count = 0
        expiring_count = 0
        expired_count = 0

        categories = {"life": 0, "health": 0, "motor": 0, "accidental": 0, "travel": 0, "home": 0, "general": 0, "agricultural": 0, "business": 0, "specialty": 0, "other": 0}
        category_coverage = {"life": 0, "health": 0, "motor": 0, "accidental": 0, "travel": 0, "home": 0, "general": 0, "agricultural": 0, "business": 0, "specialty": 0, "other": 0}

        for policy in all_policies:
            extracted_data = policy.get("extractedData", {})
            coverage = extracted_data.get("coverageAmount", 0) or 0
            premium = extracted_data.get("premium", 0) or 0

            total_coverage += coverage
            total_premium += premium

            category = get_policy_category(extracted_data.get("policyType", ""))
            categories[category] += 1
            category_coverage[category] += coverage

            status = calculate_policy_status(extracted_data.get("endDate", ""))
            if status == "active":
                active_count += 1
            elif status == "expiring_soon":
                expiring_count += 1
            else:
                expired_count += 1

        # Calculate scores
        coverage_adequacy = calculate_coverage_adequacy(total_coverage, user_annual_income)
        portfolio_diversity = calculate_portfolio_diversity(categories)
        cost_efficiency = calculate_cost_efficiency(total_coverage, total_premium, user_annual_income)
        policy_freshness_data = calculate_policy_freshness(all_policies, active_count, expiring_count, expired_count)

        overall_score = int(
            coverage_adequacy["weightedScore"] +
            portfolio_diversity["weightedScore"] +
            cost_efficiency["weightedScore"] +
            policy_freshness_data["weightedScore"]
        )
        overall_score = max(0, min(100, overall_score))

        # Score journey
        score_journey = get_score_journey(user_id_int, overall_score, db)

        # Family data
        family_members = set()
        family_coverage = 0
        for fp in family_policies:
            holder = fp.get("policyHolder", {})
            if holder.get("name"):
                family_members.add(holder.get("name"))
            family_coverage += fp.get("extractedData", {}).get("coverageAmount", 0) or 0

        # Category breakdown
        category_colors = {
            "life": {"icon": "shield", "color": "#8B5CF6"},
            "health": {"icon": "heart", "color": "#10B981"},
            "motor": {"icon": "car", "color": "#3B82F6"},
            "accidental": {"icon": "alert-triangle", "color": "#EF4444"},
            "travel": {"icon": "plane", "color": "#06B6D4"},
            "home": {"icon": "home", "color": "#F59E0B"},
            "general": {"icon": "file-text", "color": "#78716C"},
            "agricultural": {"icon": "tree", "color": "#84CC16"},
            "business": {"icon": "briefcase", "color": "#6366F1"},
            "specialty": {"icon": "star", "color": "#EC4899"},
            "other": {"icon": "document", "color": "#6B7280"}
        }

        category_breakdown = []
        for cat, count in categories.items():
            if count > 0:
                percentage = round((category_coverage[cat] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                category_breakdown.append({
                    "category": cat,
                    "categoryName": cat.title(),
                    "count": count,
                    "coverage": category_coverage[cat],
                    "coverageFormatted": format_currency(category_coverage[cat]),
                    "percentage": percentage,
                    "icon": category_colors[cat]["icon"],
                    "color": category_colors[cat]["color"]
                })
        category_breakdown.sort(key=lambda x: -x["coverage"])

        # Insights, renewals, and expired policies
        insights = generate_insights(all_policies, categories, user_annual_income, total_coverage)
        upcoming_renewals = get_upcoming_renewals(all_policies, within_days=90)
        expired_policies = get_expired_policies(all_policies)

        return {
            "success": True,
            "userId": userId,

            "protectionScore": {
                "score": overall_score,
                "category": get_score_category(overall_score),
                "color": get_score_color(overall_score),
                "factors": {
                    "coverageAdequacy": coverage_adequacy["score"],
                    "portfolioDiversity": portfolio_diversity["score"],
                    "costEfficiency": cost_efficiency["score"],
                    "policyFreshness": policy_freshness_data["score"]
                }
            },

            "scoreJourney": score_journey,

            "portfolioOverview": {
                "totalPolicies": len(all_policies),
                "activePolicies": active_count,
                "expiringPolicies": expiring_count,
                "expiredPolicies": expired_count,
                "totalCoverage": total_coverage,
                "totalCoverageFormatted": format_currency(total_coverage),
                "totalPremium": total_premium,
                "totalPremiumFormatted": format_currency(total_premium) + "/year"
            },

            "categoryBreakdown": category_breakdown,

            "coverageByType": [
                {"type": cat["categoryName"], "count": cat["count"], "color": cat["color"]}
                for cat in category_breakdown
            ],

            "upcomingRenewals": {
                "count": len(upcoming_renewals),
                "items": upcoming_renewals[:5]
            },

            # NEW: Expired Policies Section
            "expiredPolicies": {
                "count": len(expired_policies),
                "hasExpired": len(expired_policies) > 0,
                "items": expired_policies[:5],  # Limit to 5 for dashboard
                "message": f"You have {len(expired_policies)} expired policy that needs renewal" if len(expired_policies) == 1 else f"You have {len(expired_policies)} expired policies that need renewal" if len(expired_policies) > 0 else "All your policies are active"
            },

            "insights": {
                "count": len(insights),
                "items": insights[:5]
            },

            "familyData": {
                "hasFamilyPolicies": len(family_policies) > 0,
                "membersCount": len(family_members),
                "policiesCount": len(family_policies),
                "totalCoverage": family_coverage,
                "totalCoverageFormatted": format_currency(family_coverage)
            },

            "quickStats": {
                "policies": f"{active_count + expiring_count}/{len(all_policies)}",
                "policiesLabel": "active",
                "coverage": format_currency(total_coverage),
                "coverageLabel": "total",
                "premium": format_currency(total_premium),
                "premiumLabel": "/year",
                "expired": expired_count,
                "expiredLabel": "expired"
            },

            "incomeData": {
                "annualIncome": user_annual_income,
                "annualIncomeFormatted": format_currency(user_annual_income) if user_annual_income else None,
                "source": income_source
            },

            "generatedAt": datetime.utcnow().isoformat() + "Z"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail={"success": False, "error_code": "VAL_2001", "message": "Invalid userId"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error_code": "SRV_5001", "message": "Failed to fetch dashboard data"})


@router.get("/dashboard/renewals")
@limiter.limit(RATE_LIMITS["dashboard_data"])
async def get_renewals(
    request: Request,
    userId: str = Query(..., description="User ID"),
    days: int = Query(90, description="Days to look ahead for renewals"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """Get Upcoming Policy Renewals"""
    try:
        user_id_int = int(userId)

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(status_code=503, detail="Database not available")

        db = mongodb_chat_manager.db
        policies = list(db['policy_analysis'].find({
            "user_id": user_id_int,
            "$or": [{"isDeleted": {"$exists": False}}, {"isDeleted": False}]
        }))

        renewals = get_upcoming_renewals(policies, within_days=days)

        return {
            "success": True,
            "userId": userId,
            "withinDays": days,
            "totalRenewals": len(renewals),
            "urgentCount": len([r for r in renewals if r["isUrgent"]]),
            "renewals": renewals
        }

    except ValueError:
        raise HTTPException(status_code=400, detail={"success": False, "error_code": "VAL_2001", "message": "Invalid userId"})
    except Exception as e:
        logger.error(f"Error fetching renewals: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error_code": "SRV_5001", "message": "Failed to fetch renewals"})


@router.get("/dashboard/expired")
@limiter.limit(RATE_LIMITS["dashboard_data"])
async def get_expired(
    request: Request,
    userId: str = Query(..., description="User ID"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get Expired Policies

    Returns all policies that have already expired.
    Use this to show users which policies need immediate renewal.
    """
    try:
        user_id_int = int(userId)

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(status_code=503, detail="Database not available")

        db = mongodb_chat_manager.db
        policies = list(db['policy_analysis'].find({
            "user_id": user_id_int,
            "$or": [{"isDeleted": {"$exists": False}}, {"isDeleted": False}]
        }))

        expired_policies = get_expired_policies(policies)

        # Calculate total lost coverage from expired policies
        total_expired_coverage = sum(p["coverage"] for p in expired_policies)

        return {
            "success": True,
            "userId": userId,
            "totalExpired": len(expired_policies),
            "hasExpiredPolicies": len(expired_policies) > 0,
            "totalExpiredCoverage": total_expired_coverage,
            "totalExpiredCoverageFormatted": format_currency(total_expired_coverage),
            "message": f"You have {len(expired_policies)} expired policy" if len(expired_policies) == 1 else f"You have {len(expired_policies)} expired policies" if len(expired_policies) > 0 else "No expired policies",
            "expiredPolicies": expired_policies
        }

    except ValueError:
        raise HTTPException(status_code=400, detail={"success": False, "error_code": "VAL_2001", "message": "Invalid userId"})
    except Exception as e:
        logger.error(f"Error fetching expired policies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error_code": "SRV_5001", "message": "Failed to fetch expired policies"})


@router.get("/dashboard/insights")
async def get_insights(
    userId: str = Query(..., description="User ID"),
    annualIncome: Optional[float] = Query(None, description="User's annual income"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """Get AI-Generated Insights"""
    try:
        user_id_int = int(userId)

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(status_code=503, detail="Database not available")

        db = mongodb_chat_manager.db
        policies = list(db['policy_analysis'].find({
            "user_id": user_id_int,
            "$or": [{"isDeleted": {"$exists": False}}, {"isDeleted": False}]
        }))

        user_annual_income = annualIncome or get_user_annual_income(user_id_int, db)

        categories = {"life": 0, "health": 0, "motor": 0, "accidental": 0, "travel": 0, "home": 0, "general": 0, "agricultural": 0, "business": 0, "specialty": 0, "other": 0}
        total_coverage = 0

        for policy in policies:
            extracted_data = policy.get("extractedData", {})
            total_coverage += extracted_data.get("coverageAmount", 0) or 0
            category = get_policy_category(extracted_data.get("policyType", ""))
            if category in categories:
                categories[category] += 1
            else:
                categories["other"] += 1

        insights = generate_insights(policies, categories, user_annual_income, total_coverage)

        return {
            "success": True,
            "userId": userId,
            "totalInsights": len(insights),
            "highPriority": len([i for i in insights if i["severity"] == "high"]),
            "insights": insights
        }

    except ValueError:
        raise HTTPException(status_code=400, detail={"success": False, "error_code": "VAL_2001", "message": "Invalid userId"})
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error_code": "SRV_5001", "message": "Failed to generate insights"})
