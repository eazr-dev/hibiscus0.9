"""
Rate Limit Admin Router
Provides endpoints for monitoring and managing rate limits

Endpoints:
- GET /admin/rate-limits/analytics - Get rate limit analytics
- GET /admin/rate-limits/client/{identifier} - Get client-specific stats
- POST /admin/rate-limits/reset/{identifier} - Reset client limits
- POST /admin/rate-limits/blacklist - Add IP to blacklist
- POST /admin/rate-limits/whitelist - Add IP to whitelist
- GET /admin/rate-limits/status - Get rate limiter status
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.rate_limiter import (
    redis_rate_limiter,
    RATE_LIMITS,
    RateLimitConfig,
    get_client_identifier
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/rate-limits", tags=["Rate Limit Admin"])

# Simple admin authentication (should be replaced with proper auth in production)
ADMIN_API_KEY = os.getenv("RATE_LIMIT_ADMIN_KEY", "")


def verify_admin_key(request: Request):
    """Verify admin API key for protected endpoints"""
    if not ADMIN_API_KEY:
        # If no admin key configured, allow access (development mode)
        logger.warning("Rate limit admin endpoints accessible without authentication!")
        return True

    api_key = request.headers.get("X-Admin-API-Key")
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin API key")
    return True


# -------------------- Models --------------------

class BlacklistRequest(BaseModel):
    identifier: str
    duration_seconds: int = 3600  # Default 1 hour


class WhitelistRequest(BaseModel):
    identifier: str


# -------------------- Endpoints --------------------

@router.get("/status")
async def get_rate_limiter_status(request: Request, _: bool = Depends(verify_admin_key)):
    """
    Get current rate limiter status and configuration
    """
    return {
        "success": True,
        "status": {
            "redis_available": redis_rate_limiter.redis_available,
            "storage_type": "redis" if redis_rate_limiter.redis_available else "memory",
            "redis_host": RateLimitConfig.REDIS_HOST if redis_rate_limiter.redis_available else None,
            "redis_port": RateLimitConfig.REDIS_PORT if redis_rate_limiter.redis_available else None,
        },
        "configuration": {
            "limits": RATE_LIMITS,
            "whitelisted_ips_count": len(RateLimitConfig.WHITELIST_IPS),
            "blacklisted_ips_count": len(RateLimitConfig.BLACKLIST_IPS),
            "adaptive_threshold": RateLimitConfig.ADAPTIVE_THRESHOLD_WARNINGS,
        },
        "memory_stats": {
            "active_windows": len(redis_rate_limiter._memory_storage),
            "blocked_clients": len(redis_rate_limiter._blacklist_cache),
            "warning_counts": len(redis_rate_limiter._warning_counts),
        }
    }


@router.get("/analytics")
async def get_rate_limit_analytics(
    request: Request,
    date: Optional[str] = None,
    _: bool = Depends(verify_admin_key)
):
    """
    Get rate limit analytics for a specific date

    Query Parameters:
        date: Date in YYYY-MM-DD format (default: today)
    """
    analytics = redis_rate_limiter.get_analytics(date)

    if "error" in analytics:
        raise HTTPException(status_code=500, detail=analytics["error"])

    return {
        "success": True,
        "analytics": analytics
    }


@router.get("/client/{identifier}")
async def get_client_stats(
    request: Request,
    identifier: str,
    _: bool = Depends(verify_admin_key)
):
    """
    Get rate limit statistics for a specific client

    Path Parameters:
        identifier: Client identifier (IP address, user ID, etc.)
    """
    stats = redis_rate_limiter.get_client_stats(identifier)

    return {
        "success": True,
        "client_stats": stats
    }


@router.post("/reset/{identifier}")
async def reset_client_limits(
    request: Request,
    identifier: str,
    _: bool = Depends(verify_admin_key)
):
    """
    Reset rate limits for a specific client

    Path Parameters:
        identifier: Client identifier to reset
    """
    success = redis_rate_limiter.reset_client_limits(identifier)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset client limits")

    return {
        "success": True,
        "message": f"Rate limits reset for: {identifier}"
    }


@router.post("/blacklist")
async def add_to_blacklist(
    request: Request,
    blacklist_request: BlacklistRequest,
    _: bool = Depends(verify_admin_key)
):
    """
    Add an IP/identifier to the blacklist

    Request Body:
        identifier: IP address or client identifier
        duration_seconds: Duration of block (0 for permanent)
    """
    success = redis_rate_limiter.add_to_blacklist(
        blacklist_request.identifier,
        blacklist_request.duration_seconds
    )

    return {
        "success": success,
        "message": f"Added {blacklist_request.identifier} to blacklist for {blacklist_request.duration_seconds}s"
    }


@router.post("/whitelist")
async def add_to_whitelist(
    request: Request,
    whitelist_request: WhitelistRequest,
    _: bool = Depends(verify_admin_key)
):
    """
    Add an IP/identifier to the whitelist

    Request Body:
        identifier: IP address or client identifier
    """
    success = redis_rate_limiter.add_to_whitelist(whitelist_request.identifier)

    return {
        "success": success,
        "message": f"Added {whitelist_request.identifier} to whitelist"
    }


@router.delete("/blacklist/{identifier}")
async def remove_from_blacklist(
    request: Request,
    identifier: str,
    _: bool = Depends(verify_admin_key)
):
    """
    Remove an IP/identifier from the blacklist
    """
    # Remove from permanent blacklist
    RateLimitConfig.BLACKLIST_IPS.discard(identifier)

    # Remove from temporary blacklist
    if identifier in redis_rate_limiter._blacklist_cache:
        del redis_rate_limiter._blacklist_cache[identifier]

    # Remove from Redis
    if redis_rate_limiter.redis_available:
        try:
            redis_rate_limiter.redis_client.delete(f"ratelimit:blocked:{identifier}")
        except Exception:
            pass

    return {
        "success": True,
        "message": f"Removed {identifier} from blacklist"
    }


@router.delete("/whitelist/{identifier}")
async def remove_from_whitelist(
    request: Request,
    identifier: str,
    _: bool = Depends(verify_admin_key)
):
    """
    Remove an IP/identifier from the whitelist
    """
    RateLimitConfig.WHITELIST_IPS.discard(identifier)

    return {
        "success": True,
        "message": f"Removed {identifier} from whitelist"
    }


@router.get("/my-status")
async def get_my_rate_limit_status(request: Request):
    """
    Get rate limit status for the current request's client
    (No admin auth required - users can check their own status)
    """
    identifier = get_client_identifier(request)
    stats = redis_rate_limiter.get_client_stats(identifier)

    # Don't expose full identifier for privacy
    stats["identifier"] = identifier[:20] + "..." if len(identifier) > 20 else identifier

    return {
        "success": True,
        "your_status": stats
    }


@router.get("/limits")
async def get_configured_limits(request: Request):
    """
    Get all configured rate limits
    (No admin auth required - public information)
    """
    return {
        "success": True,
        "limits": RATE_LIMITS,
        "note": "Limits shown as 'requests/period'"
    }
