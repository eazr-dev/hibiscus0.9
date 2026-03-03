"""
Family Members Router
API endpoints for managing family members and their policies

Rate Limiting: 10/minute per IP for family member operations
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query, Request
from datetime import datetime

from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Family Members"])


@router.get("/family/members")
@limiter.limit(RATE_LIMITS["family_member"])
async def get_family_members(
    request: Request,
    userId: str = Query(..., description="User ID"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get All Family Members with Their Policies

    Returns a list of family members with their policy count and total coverage.

    **Headers (Optional):**
    - access-token: {token}
    - Authorization: Bearer {token}

    **Query Parameters:**
    - userId: User ID (required)

    **Returns:**
    - List of family members
    - Each member shows: name, relationship, policy count, total coverage
    - Individual policies for each member
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

        # Get all family policies
        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Fetch all family policies (policyFor = "family")
        # Exclude soft-deleted policies
        policies_cursor = policy_analysis_collection.find({
            "user_id": user_id_int,
            "policyFor": "family",
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        }).sort("created_at", -1)

        policies = list(policies_cursor)

        logger.info(f"Found {len(policies)} family policies for user {user_id_int}")

        # Group policies by family member (using policyHolder.name)
        family_members_dict = {}

        for policy in policies:
            policy_holder = policy.get("policyHolder", {})
            extracted_data = policy.get("extractedData", {})

            # Get member details
            member_name = policy_holder.get("name", "Unknown")
            member_gender = policy_holder.get("gender", "other")
            member_dob = policy_holder.get("dateOfBirth", "")
            member_relationship = policy_holder.get("relationship", "other")

            # Create unique key for each member (name + relationship)
            member_key = f"{member_name}_{member_relationship}"

            # Initialize member if not exists
            if member_key not in family_members_dict:
                # Get emoji based on relationship and gender
                emoji = get_member_emoji(member_relationship, member_gender)

                family_members_dict[member_key] = {
                    "memberName": member_name,
                    "relationship": member_relationship.title(),
                    "gender": member_gender,
                    "dateOfBirth": member_dob,
                    "emoji": emoji,
                    "policyCount": 0,
                    "totalCoverage": 0,
                    "policies": []
                }

            # Get policy details
            policy_type = extracted_data.get("policyType", "unknown").lower()
            coverage = extracted_data.get("coverageAmount", 0)
            premium = extracted_data.get("premium", 0)

            # Determine category and icon color
            if policy_type in ["health", "medical", "mediclaim"]:
                policy_category = "health"
                icon_color = "green"
            elif policy_type in ["life", "term", "endowment", "ulip", "whole life"]:
                policy_category = "life"
                icon_color = "blue"
            elif policy_type in ["motor", "car", "vehicle", "bike", "two-wheeler", "four-wheeler", "auto"]:
                policy_category = "motor"
                icon_color = "orange"
            elif policy_type in ["general", "home", "property", "fire", "burglary", "travel", "personal accident"]:
                policy_category = "general"
                icon_color = "purple"
            else:
                policy_category = "other"
                icon_color = "gray"

            # Determine status based on start and end dates (matching /api/policy/upload logic)
            start_date_str = extracted_data.get("startDate", "")
            end_date_str = extracted_data.get("endDate", "")
            policy_status = "active"  # Default

            try:
                if start_date_str and end_date_str:
                    current_date = datetime.now().date()

                    # Parse dates (handle both YYYY-MM-DD and DD-MM-YYYY formats)
                    if "-" in start_date_str:
                        parts = start_date_str.split("-")
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                        else:  # DD-MM-YYYY
                            start_date = datetime.strptime(start_date_str, "%d-%m-%Y").date()
                    else:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

                    if "-" in end_date_str:
                        parts = end_date_str.split("-")
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                        else:  # DD-MM-YYYY
                            end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date()
                    else:
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                    # Determine status
                    if current_date < start_date:
                        policy_status = "upcoming"
                    elif current_date > end_date:
                        policy_status = "expired"
                    else:
                        policy_status = "active"
            except Exception as e:
                logger.warning(f"Could not parse policy dates: {str(e)}")
                policy_status = "active"  # Default if parsing fails

            # Add policy to member
            family_members_dict[member_key]["policies"].append({
                "policyId": policy.get("analysisId", ""),
                "policyName": extracted_data.get("insuranceProvider", "Unknown Policy"),
                "policyType": policy_type.title(),
                "category": policy_category,
                "provider": extracted_data.get("insuranceProvider", "Unknown"),
                "policyNumber": extracted_data.get("policyNumber", "N/A"),
                "coverage": coverage,
                "premium": premium,
                "status": policy_status,
                "iconColor": icon_color
            })

            # Update totals
            family_members_dict[member_key]["policyCount"] += 1
            family_members_dict[member_key]["totalCoverage"] += coverage

        # Format family members list
        family_members = []
        for member_data in family_members_dict.values():
            # Format coverage
            coverage = member_data["totalCoverage"]
            if coverage >= 10000000:
                coverage_formatted = f"₹{coverage/10000000:.1f}Cr"
            elif coverage >= 100000:
                coverage_formatted = f"₹{coverage/100000:.1f}L"
            else:
                coverage_formatted = f"₹{coverage:,.0f}"

            family_members.append({
                "memberName": member_data["memberName"],
                "relationship": member_data["relationship"],
                "emoji": member_data["emoji"],
                "policyCount": member_data["policyCount"],
                "totalCoverage": member_data["totalCoverage"],
                "totalCoverageFormatted": coverage_formatted,
                "policies": member_data["policies"]
            })

        # Sort by total coverage (highest first)
        family_members.sort(key=lambda x: x["totalCoverage"], reverse=True)

        # Calculate total overall coverage (sum of all family members)
        total_overall_coverage = sum(member["totalCoverage"] for member in family_members)

        # Calculate total policies (sum of all policyCount)
        total_policies = sum(member["policyCount"] for member in family_members)

        # Format total overall coverage
        if total_overall_coverage >= 10000000:
            total_overall_coverage_formatted = f"₹{total_overall_coverage/10000000:.1f}Cr"
        elif total_overall_coverage >= 100000:
            total_overall_coverage_formatted = f"₹{total_overall_coverage/100000:.1f}L"
        else:
            total_overall_coverage_formatted = f"₹{total_overall_coverage:,.0f}"

        # Build response
        response = {
            "success": True,
            "userId": userId,
            "totalMembers": len(family_members),
            "totalPolicies": total_policies,
            "totalOverallCoverage": total_overall_coverage,
            "totalOverallCoverageFormatted": total_overall_coverage_formatted,
            "familyMembers": family_members
        }

        return response

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error fetching family members: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to fetch family members"
            }
        )


def get_member_emoji(relationship: str, gender: str) -> str:
    """Get appropriate emoji based on relationship and gender"""
    relationship = relationship.lower()
    gender = gender.lower()

    emoji_map = {
        "spouse": "👩" if gender == "female" else "👨",
        "child": "👦" if gender == "male" else "👧",
        "son": "👦",
        "daughter": "👧",
        "parent": "👴" if gender == "male" else "👵",
        "father": "👴",
        "mother": "👵",
        "sibling": "👨" if gender == "male" else "👩",
        "brother": "👨",
        "sister": "👩",
        "other": "👤"
    }

    return emoji_map.get(relationship, "👤")
