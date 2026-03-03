"""
Authentication Router - HTTP Endpoints
Uses AuthService for business logic

Phase 3 Refactored: Thin router with service layer separation

Advanced Rate Limiting Applied (Redis-backed):
- /send-otp: 3 requests per minute per IP + 3 per hour per phone number
- /verify-otp: 5 requests per minute per IP + 10 per hour (strict)
- /oauth-login: 10 requests per minute per IP
- /check-session: 60 requests per minute per IP

Features:
- Sliding window algorithm for accurate limiting
- Per-phone rate limiting prevents flooding specific numbers
- Adaptive blocking for repeat offenders
- Distributed limiting across multiple server instances
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from models.auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    CheckSessionRequest,
    OAuthLoginRequest,
    OAuthLoginResponse
)
from services.auth_service import AuthService
from core.rate_limiter import (
    limiter,
    RATE_LIMITS,
    check_phone_rate_limit,
    redis_rate_limiter,
    get_client_identifier
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Authentication"])

# Initialize service
auth_service = AuthService()


@router.post("/send-otp", response_model=SendOTPResponse)
@limiter.limit(RATE_LIMITS["send_otp"])
async def send_otp(request: Request, otp_request: SendOTPRequest):
    """
    Send OTP using eazr.in API

    Rate Limited:
    - 3 requests per minute per IP (SlowAPI)
    - 3 requests per hour per phone number (Redis)

    This prevents SMS flooding attacks on phone numbers.
    """
    try:
        # Additional per-phone rate limiting
        phone_allowed, phone_rate_info = check_phone_rate_limit(otp_request.phone, request)
        if not phone_allowed:
            logger.warning(f"Phone rate limit exceeded for {otp_request.phone[:6]}***")
            raise HTTPException(
                status_code=429,
                detail={
                    "success": False,
                    "error_code": "RATE_4001",
                    "message": "Too many OTP requests for this phone number. Please try again later."
                }
            )

        result = await auth_service.send_otp_to_phone(otp_request.phone)
        return SendOTPResponse(**result)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="SMS service timeout")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="SMS service unavailable")
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="SMS service error")


@router.post("/verify-otp", response_model=VerifyOTPResponse)
@limiter.limit(RATE_LIMITS["verify_otp"])
async def verify_otp(request: Request, otp_request: VerifyOTPRequest):
    """
    Verify OTP and create sessions

    Rate Limited:
    - 5 requests per minute per IP (SlowAPI)
    - 10 requests per hour per IP (Redis strict limit)

    This prevents brute force attacks on OTP verification.
    """
    try:
        # Additional strict hourly rate limiting for OTP verification
        client_id = get_client_identifier(request)
        is_allowed, rate_info = redis_rate_limiter.check_rate_limit(
            client_id,
            "verify_otp_strict",
            RATE_LIMITS["verify_otp_strict"]
        )

        if not is_allowed:
            logger.warning(f"Strict OTP verification rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=429,
                detail={
                    "success": False,
                    "error_code": "RATE_4001",
                    "message": "Too many verification attempts. Please try again later."
                }
            )

        # Convert app_version model to dict if present
        app_version_dict = None
        if otp_request.app_version:
            app_version_dict = {
                "platform": otp_request.app_version.platform,
                "android_version": otp_request.app_version.android_version,
                "ios_version": otp_request.app_version.ios_version
            }

        result = await auth_service.verify_otp_and_create_sessions(
            phone=otp_request.phone,
            otp=otp_request.otp,
            ip_address=otp_request.ip_address,
            user_agent=otp_request.user_agent,
            app_version=app_version_dict
        )
        return VerifyOTPResponse(**result)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="SMS service timeout")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="SMS service unavailable")
    except Exception as e:
        logger.error(f"Verify OTP error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/oauth-login", response_model=OAuthLoginResponse)
@limiter.limit(RATE_LIMITS["oauth_login"])
async def oauth_login(request: Request, oauth_request: OAuthLoginRequest):
    """
    OAuth login with Google or Apple

    Rate Limited: 10 requests per minute per IP
    This prevents OAuth abuse and token stuffing attacks.

    Accepts provider ('google' or 'apple') and idToken,
    calls https://api.prod.eazr.in/users/verify-idtoken for verification,
    and creates user sessions
    """
    try:
        # Convert app_version model to dict if present
        app_version_dict = None
        if oauth_request.app_version:
            app_version_dict = oauth_request.app_version.model_dump()
        result = await auth_service.verify_oauth_and_create_sessions(
            provider=oauth_request.provider,
            id_token=oauth_request.idToken,
            ip_address=oauth_request.ip_address,
            user_agent=oauth_request.user_agent,
            app_version=app_version_dict
        )
        return OAuthLoginResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="OAuth service timeout")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="OAuth service unavailable")
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="OAuth authentication failed")


@router.post("/check-session")
@limiter.limit(RATE_LIMITS["check_session"])
async def check_session(request: Request, session_request: CheckSessionRequest):
    """
    Check if session is valid with auto-regeneration

    Rate Limited: 60 requests per minute per IP
    Allows frequent session checks while preventing abuse.
    """
    session_id, session_data, was_regenerated = auth_service.validate_and_regenerate_session(
        session_request.session_id
    )

    response = {
        "valid": True,
        "message": "Session is valid" if not was_regenerated else "Session regenerated",
        "session_id": session_id,
        "user_phone": session_data.get('phone')
    }

    if was_regenerated:
        response["session_regenerated"] = True
        response["new_session_id"] = session_id
        response["original_session_id"] = session_request.session_id

    return response
