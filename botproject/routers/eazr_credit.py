"""
Eazr Credit Waitlist Router - HTTP Endpoints
API endpoints for managing Eazr Credit waitlist

Endpoints:
    POST /api/eazr-credit/waitlist/join     - Join the waitlist
    GET  /api/eazr-credit/waitlist/status/{user_id} - Check waitlist status

Rate Limiting: 5/minute for write operations, 30/minute for read
"""
import logging
from fastapi import APIRouter, HTTPException, Header, Path, Request
from typing import Optional

from models.eazr_credit import (
    JoinWaitlistRequest,
    WaitlistResponse,
    WaitlistStatusResponse,
    WaitlistData
)
from services.eazr_credit_service import eazr_credit_waitlist_service
from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/eazr-credit",
    tags=["Eazr Credit Waitlist"]
)


@router.post(
    "/waitlist/join",
    response_model=WaitlistResponse,
    responses={
        200: {
            "description": "Successfully joined the waitlist",
            "model": WaitlistResponse
        },
        409: {
            "description": "User is already on the waitlist",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "You are already on the waitlist",
                        "data": {
                            "user_id": 12345,
                            "is_waitlisted": True,
                            "waitlist_id": "WL-2024-001234",
                            "position": 10542,
                            "joined_at": "2024-12-15T08:20:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or expired token"
        },
        500: {
            "description": "Internal server error"
        }
    },
    summary="Join Eazr Credit Waitlist",
    description="""
    Add the logged-in user to the Eazr Credit waitlist.

    Since the user is already authenticated, only user_id is required.
    The API will:
    - Check if user is already on waitlist
    - If not, add them with auto-generated position
    - Return waitlist ID and position

    **Note:** Returns 409 Conflict if user is already on waitlist.
    """
)
@limiter.limit(RATE_LIMITS["user_write"])
async def join_waitlist(
    request: Request,
    waitlist_request: JoinWaitlistRequest,
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token")
):
    """
    Join the Eazr Credit waitlist

    - **user_id**: User's unique ID from session

    Returns success with waitlist ID and position, or 409 if already joined.
    """
    try:
        logger.info(f"Join waitlist request for user_id: {waitlist_request.user_id}")

        # Validate user_id
        if not waitlist_request.user_id or waitlist_request.user_id <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "Invalid user_id provided"
                }
            )

        # Call service to join waitlist
        success, data, status_code = eazr_credit_waitlist_service.join_waitlist(waitlist_request.user_id)

        if status_code == 409:
            # Already on waitlist - return 409 with existing data
            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "error_code": "RES_3003",
                    "message": "You are already on the waitlist"
                }
            )

        if not success:
            # Server error
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "SRV_5001",
                    "message": "Something went wrong. Please try again."
                }
            )

        # Success response
        logger.info(f"User {waitlist_request.user_id} successfully joined waitlist at position {data.get('position')}")

        return WaitlistResponse(
            success=True,
            message="Successfully joined the waitlist",
            data=WaitlistData(**data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in join_waitlist endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Something went wrong. Please try again."
            }
        )


@router.get(
    "/waitlist/status/{user_id}",
    response_model=WaitlistStatusResponse,
    responses={
        200: {
            "description": "User waitlist status retrieved",
            "model": WaitlistStatusResponse
        },
        400: {
            "description": "Invalid user_id"
        },
        401: {
            "description": "Unauthorized - Invalid or expired token"
        },
        500: {
            "description": "Internal server error"
        }
    },
    summary="Check Waitlist Status",
    description="""
    Check if a user is on the Eazr Credit waitlist.

    Returns:
    - **is_waitlisted: true** - User is on waitlist with position details
    - **is_waitlisted: false** - User is not on waitlist

    Use this on app launch to determine which UI to show:
    - If is_waitlisted=true: Show "You're on the waitlist!" with position
    - If is_waitlisted=false: Show "Join the Waitlist" button
    """
)
@limiter.limit(RATE_LIMITS["user_read"])
async def get_waitlist_status(
    request: Request,
    user_id: int = Path(..., description="User's unique ID", gt=0),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token")
):
    """
    Check if user is on the Eazr Credit waitlist

    - **user_id**: User's unique ID (path parameter)

    Returns waitlist status with position if user is on waitlist.
    """
    try:
        logger.info(f"Checking waitlist status for user_id: {user_id}")

        # Validate user_id
        if not user_id or user_id <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "Invalid user_id provided"
                }
            )

        # Call service to get status
        data = eazr_credit_waitlist_service.get_waitlist_status(user_id)

        logger.info(f"Waitlist status for user {user_id}: is_waitlisted={data.get('is_waitlisted')}")

        return WaitlistStatusResponse(
            success=True,
            message="User waitlist status retrieved",
            data=WaitlistData(**data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_waitlist_status endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Something went wrong. Please try again."
            }
        )


# ==================== ADMIN ENDPOINT (Optional) ====================

@router.get(
    "/waitlist/stats",
    tags=["Eazr Credit Admin"],
    summary="Get Waitlist Statistics (Admin)",
    description="Get overall waitlist statistics. For admin use only."
)
@limiter.limit(RATE_LIMITS["admin_read"])
async def get_waitlist_stats(
    request: Request,
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Get waitlist statistics (admin endpoint)

    Returns total signups, active, notified, and converted counts.
    """
    try:
        stats = eazr_credit_waitlist_service.get_waitlist_stats()

        return {
            "success": True,
            "message": "Waitlist statistics retrieved",
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting waitlist stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to retrieve statistics"
            }
        )
