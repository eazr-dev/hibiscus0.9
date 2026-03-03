"""
Reward Feature Router
Allows users to unlock FREE ₹50,000 Personal Accidental Insurance by uploading 5 active policies

Rate Limiting Applied (Redis-backed):
- Reward progress: 30/minute per IP
- Reward claim: 5/minute per IP

Admin Configurable Settings:
- REQUIRED_POLICIES: Number of policies needed to unlock reward
- REWARD_COVERAGE: Coverage amount for the reward
- REWARD_BENEFITS: List of benefits to display
- REWARD_TERMS: Terms and conditions
- REWARD_HOW_IT_WORKS: Steps to claim reward
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Request

from core.rate_limiter import limiter, RATE_LIMITS

_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in multiple formats (same logic as dashboard.py)."""
    if not date_str:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _count_active_policies(db, user_id: int) -> tuple:
    """
    Count active (non-expired, non-deleted) policies for a user.

    Policy status is date-based (extractedData.endDate), not a stored field.
    A policy is active if endDate > today OR endDate is missing/unparseable.

    Returns: (active_count, active_policies_list)
    """
    policy_collection = db['policy_analysis']

    # Fetch all non-deleted policies for the user
    cursor = policy_collection.find(
        {
            "user_id": int(user_id),
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        },
        sort=[("created_at", 1)]
    )

    today = datetime.now()
    active_policies = []

    for policy in cursor:
        extracted_data = policy.get("extractedData", {})
        end_date_str = extracted_data.get("endDate", "")
        end_date = _parse_date(end_date_str)

        # Active if: no end date, can't parse, or end date is in the future
        if not end_date or end_date >= today:
            active_policies.append(policy)

    return len(active_policies), active_policies

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/rewards", tags=["Rewards"])


# ==================== ADMIN CONFIGURABLE REWARD SETTINGS ====================
# These can be moved to database/admin panel for dynamic management

REWARD_CONFIG = {
    "id": "reward_pa_50k",
    "name": "Free Personal Accidental Insurance",
    "description": "Get FREE ₹50,000 Personal Accidental Insurance coverage for 1 year",
    "requiredPolicies": 5,  # 5 policies to unlock reward
    "coverageAmount": 50000,
    "coverageFormatted": "₹50,000",
    "currency": "INR",
    "validityDays": 365,
    "originalPrice": "₹199",  # For strikethrough gamification (~~₹199~~ FREE)
    "termsAndConditionsUrl": "https://eazr.in/reward-terms",

    # Benefits to display on reward card
    "benefits": [
        {
            "icon": "shield",
            "title": "Accidental Death",
            "subtitle": "Full coverage up to ₹50,000"
        },
        {
            "icon": "accessibility",
            "title": "Permanent Disability",
            "subtitle": "Complete disability protection"
        },
        {
            "icon": "calendar",
            "title": "1 Year Coverage",
            "subtitle": "Valid for 12 months"
        },
        {
            "icon": "savings",
            "title": "Zero Premium",
            "subtitle": "Absolutely FREE!",
            "isHighlighted": True
        }
    ],

    # How it works steps
    "howItWorks": [
        {
            "step": 1,
            "title": "Upload Policies",
            "description": "Add your existing insurance policies to Eazr"
        },
        {
            "step": 2,
            "title": "Reach 5 Policies",
            "description": "Self or family policies both count towards the goal"
        },
        {
            "step": 3,
            "title": "Claim Reward",
            "description": "Get your FREE policy instantly after reaching the goal"
        }
    ],

    # Terms and conditions (detailed)
    "terms": [
        "Only active, valid insurance policies count towards the goal",
        "Both self and family member policies are eligible",
        "Reward can be claimed only once per user account",
        "Policy must be uploaded through Eazr app to count",
        "Expired or cancelled policies do not count",
        "Standard policy terms and conditions apply to the reward policy",
        "Eazr reserves the right to modify or discontinue this offer",
        "Coverage is subject to policy terms from the insurance provider"
    ],

    # Compliance information (for legal display)
    "compliance": {
        "insurerName": "Partner Insurance Company",
        "irdaRegNo": "XXXXXX",
        "policyType": "Personal Accident Insurance",
        "disclaimer": "Insurance is the subject matter of solicitation. Please read the policy terms and conditions carefully before concluding the sale."
    }
}


def get_reward_config() -> Dict[str, Any]:
    """
    Get reward configuration.
    In future, this can fetch from database for admin management.
    """
    # TODO: Fetch from MongoDB rewards_config collection for admin panel management
    # Example:
    # config = db['rewards_config'].find_one({"reward_id": "reward_pa_50k"})
    # if config:
    #     return config
    return REWARD_CONFIG


@router.get("/progress")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_reward_progress(
    request: Request,
    userId: Optional[int] = None,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Get Reward Progress

    Fetches the user's current progress towards unlocking the FREE ₹50,000
    Personal Accidental Insurance reward.

    **Query Parameters:**
    - userId: User ID (integer) - Optional, if provided uses this directly

    **Headers:**
    - Authorization: Bearer {token}
    - access-token: {token} (alternative)

    **Reward Criteria:**
    - Upload 5 active insurance policies (self or family members)
    - Unlock FREE ₹50,000 Personal Accidental Insurance for 1 year

    **Returns:**
    - requiredPolicies: Number of policies needed (configurable, default 5)
    - uploadedPolicies: Number of active policies uploaded so far
    - isUnlocked: Whether reward is unlocked (uploadedPolicies >= 5)
    - isClaimed: Whether reward has been claimed
    - reward: Details about the reward policy
    """
    try:
        # Get MongoDB connection
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": {
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "Database service is unavailable"
                    }
                }
            )

        db = mongodb_chat_manager.db

        # Determine user_id: prioritize query parameter, then extract from token
        user_id = userId

        if not user_id:
            # Try to extract from token
            token = None
            if authorization and authorization.startswith("Bearer "):
                token = authorization.replace("Bearer ", "")
            elif access_token:
                token = access_token

            if not token:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Authentication required. Provide userId parameter or Authorization header."
                        }
                    }
                )

            # Extract user_id from token
            try:
                sessions_collection = db['sessions']
                session = sessions_collection.find_one({"token": token})
                if session:
                    user_id = session.get("user_id")
            except Exception as e:
                logger.warning(f"Could not extract user_id from session: {e}")

            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Invalid or expired authentication token"
                        }
                    }
                )

        logger.info(f"Fetching reward progress for user_id: {user_id}")

        # Get reward configuration (admin manageable)
        reward_config = get_reward_config()
        required_policies = reward_config["requiredPolicies"]

        # Count active policies (date-based: endDate > today, not deleted)
        active_policies_count, _ = _count_active_policies(db, user_id)

        logger.info(f"User {user_id} has {active_policies_count} active policies")

        # Check if reward is unlocked
        is_unlocked = active_policies_count >= required_policies

        # Check if reward has been claimed
        rewards_collection = db['rewards']
        reward_claim = rewards_collection.find_one({
            "user_id": int(user_id),
            "reward_id": reward_config["id"],
            "status": "claimed"
        })

        is_claimed = reward_claim is not None

        # Build response with detailed reward information
        response = {
            "success": True,
            "data": {
                "requiredPolicies": required_policies,
                "uploadedPolicies": active_policies_count,
                "isUnlocked": is_unlocked,
                "isClaimed": is_claimed,
                "rewardCoverage": reward_config["coverageFormatted"],
                "rewardType": "Personal Accidental Insurance",
                "reward": {
                    "id": reward_config["id"],
                    "name": reward_config["name"],
                    "description": reward_config["description"],
                    "coverageAmount": reward_config["coverageAmount"],
                    "currency": reward_config["currency"],
                    "validityDays": reward_config["validityDays"],
                    "termsAndConditions": reward_config["termsAndConditionsUrl"],
                    # New fields for gamification and compliance
                    "originalPrice": reward_config["originalPrice"],
                    "benefits": reward_config["benefits"],
                    "howItWorks": reward_config["howItWorks"],
                    "terms": reward_config["terms"],
                    "compliance": reward_config["compliance"]
                }
            },
            "message": "Reward progress fetched successfully"
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reward progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "REWARD_FETCH_FAILED",
                    "message": "Unable to fetch reward progress"
                }
            }
        )


@router.get("/eligibility")
@limiter.limit(RATE_LIMITS["user_read"])
async def check_reward_eligibility(
    request: Request,
    userId: Optional[int] = None,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Check Reward Eligibility

    Checks if the user is eligible to claim the FREE ₹50,000 Personal Accidental
    Insurance reward.

    **Query Parameters:**
    - userId: User ID (integer) - Optional, if provided uses this directly

    **Headers:**
    - Authorization: Bearer {token}
    - access-token: {token} (alternative)

    **Eligibility Criteria:**
    - Must have uploaded required number of active policies (default 5)
    - Reward must not have been claimed already

    **Returns:**
    - isEligible: Whether user can claim the reward
    - isClaimed: Whether reward has been claimed
    - reason: Reason for ineligibility (if not eligible)
    - eligibleSince: Date when user became eligible (if eligible)
    - claimedAt: Date when reward was claimed (if claimed)
    """
    try:
        # Get MongoDB connection
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": {
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "Database service is unavailable"
                    }
                }
            )

        db = mongodb_chat_manager.db

        # Determine user_id: prioritize query parameter, then extract from token
        user_id = userId

        if not user_id:
            # Try to extract from token
            token = None
            if authorization and authorization.startswith("Bearer "):
                token = authorization.replace("Bearer ", "")
            elif access_token:
                token = access_token

            if not token:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Authentication required. Provide userId parameter or Authorization header."
                        }
                    }
                )

            # Extract user_id from token
            try:
                sessions_collection = db['sessions']
                session = sessions_collection.find_one({"token": token})
                if session:
                    user_id = session.get("user_id")
            except Exception as e:
                logger.warning(f"Could not extract user_id from session: {e}")

            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Invalid or expired authentication token"
                        }
                    }
                )

        logger.info(f"Checking reward eligibility for user_id: {user_id}")

        # Get reward configuration
        reward_config = get_reward_config()
        required_policies = reward_config["requiredPolicies"]

        # Count active policies (date-based: endDate > today, not deleted)
        active_policies_count, active_policies_list = _count_active_policies(db, user_id)

        # Check if reward has been claimed
        rewards_collection = db['rewards']
        reward_claim = rewards_collection.find_one({
            "user_id": int(user_id),
            "reward_id": reward_config["id"]
        })

        is_claimed = reward_claim is not None and reward_claim.get("status") == "claimed"

        # Build response based on eligibility status

        # Case 1: Already claimed
        if is_claimed:
            return {
                "success": True,
                "data": {
                    "isEligible": False,
                    "isClaimed": True,
                    "reason": "ALREADY_CLAIMED",
                    "claimedAt": reward_claim.get("claimedAt", datetime.utcnow()).isoformat() + "Z" if isinstance(reward_claim.get("claimedAt"), datetime) else reward_claim.get("claimedAt"),
                    "policyId": reward_claim.get("rewardPolicyId")
                }
            }

        # Case 2: Insufficient policies
        if active_policies_count < required_policies:
            return {
                "success": True,
                "data": {
                    "isEligible": False,
                    "isClaimed": False,
                    "reason": "INSUFFICIENT_POLICIES",
                    "currentPolicies": active_policies_count,
                    "requiredPolicies": required_policies,
                    "remainingPolicies": required_policies - active_policies_count
                }
            }

        # Case 3: Eligible to claim
        # Find the date when 5th policy was uploaded (from active policies sorted by created_at)
        eligible_since = None
        if len(active_policies_list) >= required_policies:
            fifth_policy = active_policies_list[required_policies - 1]
            eligible_since = fifth_policy.get("created_at")
            if isinstance(eligible_since, datetime):
                eligible_since = eligible_since.isoformat() + "Z"

        return {
            "success": True,
            "data": {
                "isEligible": True,
                "isClaimed": False,
                "reason": None,
                "eligibleSince": eligible_since,
                "claimDeadline": None  # No deadline for now
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking reward eligibility: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "ELIGIBILITY_CHECK_FAILED",
                    "message": "Unable to check reward eligibility"
                }
            }
        )


@router.patch("/progress")
@limiter.limit(RATE_LIMITS["user_write"])
async def claim_reward(
    request: Request,
    userId: Optional[int] = None,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Claim Reward - Set isClaimed to True

    Claims the FREE ₹50,000 Personal Accidental Insurance reward for eligible users.

    **Query Parameters:**
    - userId: User ID (integer) - Optional, if provided uses this directly

    **Headers:**
    - Authorization: Bearer {token}
    - access-token: {token} (alternative)

    **Eligibility Criteria:**
    - Must have uploaded required number of active policies (default 5)
    - Reward must not have been claimed already

    **Returns:**
    - success: Whether the claim was successful
    - data: Updated reward progress with isClaimed=true
    - message: Success or error message
    """
    try:
        # Get MongoDB connection
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": {
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "Database service is unavailable"
                    }
                }
            )

        db = mongodb_chat_manager.db

        # Determine user_id: prioritize query parameter, then extract from token
        user_id = userId

        if not user_id:
            # Try to extract from token
            token = None
            if authorization and authorization.startswith("Bearer "):
                token = authorization.replace("Bearer ", "")
            elif access_token:
                token = access_token

            if not token:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Authentication required. Provide userId parameter or Authorization header."
                        }
                    }
                )

            # Extract user_id from token
            try:
                sessions_collection = db['sessions']
                session = sessions_collection.find_one({"token": token})
                if session:
                    user_id = session.get("user_id")
            except Exception as e:
                logger.warning(f"Could not extract user_id from session: {e}")

            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Invalid or expired authentication token"
                        }
                    }
                )

        logger.info(f"Claiming reward for user_id: {user_id}")

        # Get reward configuration
        reward_config = get_reward_config()
        required_policies = reward_config["requiredPolicies"]

        # Check if reward already claimed
        rewards_collection = db['rewards']
        existing_claim = rewards_collection.find_one({
            "user_id": int(user_id),
            "reward_id": reward_config["id"],
            "status": "claimed"
        })

        if existing_claim:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "ALREADY_CLAIMED",
                        "message": "Reward has already been claimed"
                    },
                    "data": {
                        "isClaimed": True,
                        "claimedAt": existing_claim.get("claimed_at").isoformat() + "Z" if isinstance(existing_claim.get("claimed_at"), datetime) else existing_claim.get("claimed_at")
                    }
                }
            )

        # Count active policies (date-based: endDate > today, not deleted)
        active_policies_count, _ = _count_active_policies(db, user_id)

        # Check eligibility
        if active_policies_count < required_policies:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "NOT_ELIGIBLE",
                        "message": f"You need at least {required_policies} active policies to claim the reward. Currently you have {active_policies_count}."
                    },
                    "data": {
                        "requiredPolicies": required_policies,
                        "uploadedPolicies": active_policies_count,
                        "remainingPolicies": required_policies - active_policies_count
                    }
                }
            )

        # Create reward claim record
        claim_timestamp = datetime.utcnow()
        reward_claim_record = {
            "user_id": int(user_id),
            "reward_id": reward_config["id"],
            "reward_name": reward_config["name"],
            "reward_type": "Personal Accidental Insurance",
            "coverage_amount": reward_config["coverageAmount"],
            "currency": reward_config["currency"],
            "validity_days": reward_config["validityDays"],
            "status": "claimed",
            "claimed_at": claim_timestamp,
            "expires_at": datetime(claim_timestamp.year + 1, claim_timestamp.month, claim_timestamp.day),
            "policies_at_claim": active_policies_count,
            "created_at": claim_timestamp,
            "updated_at": claim_timestamp
        }

        # Insert or update the reward claim
        result = rewards_collection.update_one(
            {
                "user_id": int(user_id),
                "reward_id": reward_config["id"]
            },
            {"$set": reward_claim_record},
            upsert=True
        )

        logger.info(f"Reward claimed successfully for user_id: {user_id}, modified: {result.modified_count}, upserted: {result.upserted_id}")

        # Build success response with detailed reward information
        response = {
            "success": True,
            "data": {
                "requiredPolicies": required_policies,
                "uploadedPolicies": active_policies_count,
                "isUnlocked": True,
                "isClaimed": True,
                "claimedAt": claim_timestamp.isoformat() + "Z",
                "expiresAt": reward_claim_record["expires_at"].isoformat() + "Z",
                "rewardCoverage": reward_config["coverageFormatted"],
                "rewardType": "Personal Accidental Insurance",
                "reward": {
                    "id": reward_config["id"],
                    "name": reward_config["name"],
                    "description": reward_config["description"],
                    "coverageAmount": reward_config["coverageAmount"],
                    "currency": reward_config["currency"],
                    "validityDays": reward_config["validityDays"],
                    "termsAndConditions": reward_config["termsAndConditionsUrl"],
                    "originalPrice": reward_config["originalPrice"],
                    "benefits": reward_config["benefits"],
                    "howItWorks": reward_config["howItWorks"],
                    "terms": reward_config["terms"],
                    "compliance": reward_config["compliance"]
                }
            },
            "message": f"Reward claimed successfully! Your FREE {reward_config['coverageFormatted']} Personal Accidental Insurance is now active."
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming reward: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "CLAIM_FAILED",
                    "message": "Unable to claim reward. Please try again."
                }
            }
        )