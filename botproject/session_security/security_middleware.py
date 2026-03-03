"""
Security middleware for FastAPI application
Implements rate limiting, authentication, and security headers
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import time
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory, use Redis in production)
rate_limit_storage = defaultdict(lambda: defaultdict(list))

security = HTTPBearer()


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, requests: int, window: int):
        """
        Args:
            requests: Maximum number of requests
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        key = f"rate_limit:{identifier}"

        # Clean old entries
        rate_limit_storage[key] = [
            timestamp for timestamp in rate_limit_storage[key]
            if now - timestamp < self.window
        ]

        # Check rate limit
        if len(rate_limit_storage[key]) >= self.requests:
            return False

        # Add current request
        rate_limit_storage[key].append(now)
        return True


def rate_limit(requests: int = 10, window: int = 60):
    """
    Rate limiting decorator

    Args:
        requests: Maximum number of requests
        window: Time window in seconds
    """
    limiter = RateLimiter(requests, window)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # Check kwargs
                request = kwargs.get('request')

            if request:
                # Use IP address as identifier
                client_ip = request.client.host if request.client else "unknown"
                identifier = f"{func.__name__}:{client_ip}"

                if not limiter.is_allowed(identifier):
                    logger.warning(f"Rate limit exceeded for {client_ip} on {func.__name__}")
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please try again later."
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify admin authentication token

    Returns:
        Token payload if valid

    Raises:
        HTTPException: If token is invalid or not admin
    """
    from session_security.token_genrations import verify_jwt_token

    token = credentials.credentials

    # Verify token
    result = verify_jwt_token(token)

    if not result.get("valid"):
        logger.warning(f"Invalid admin token attempt: {result.get('error')}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )

    payload = result.get("payload", {})

    # Check admin role
    if payload.get("role") != "admin":
        logger.warning(f"Non-admin user attempted admin access: user_id={payload.get('id')}")
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return payload


async def verify_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify user authentication token

    Returns:
        Token payload if valid

    Raises:
        HTTPException: If token is invalid
    """
    from session_security.token_genrations import verify_jwt_token

    token = credentials.credentials

    # Verify token
    result = verify_jwt_token(token)

    if not result.get("valid"):
        logger.warning(f"Invalid token: {result.get('error')}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )

    return result.get("payload", {})


async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Remove server header (use del instead of pop for MutableHeaders)
    try:
        del response.headers["Server"]
    except KeyError:
        pass

    return response


def require_auth(allow_guest: bool = False):
    """
    Authentication decorator for endpoints

    Args:
        allow_guest: Whether to allow guest users
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a placeholder - actual implementation depends on your auth flow
            # You should extract and verify the token from the request
            return await func(*args, **kwargs)
        return wrapper
    return decorator
