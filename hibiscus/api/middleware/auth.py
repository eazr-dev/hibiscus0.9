"""
Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
JWT auth middleware — token validation, user context injection.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# Paths that never require authentication
_EXEMPT_PATHS = {
    "/hibiscus/health",
    "/hibiscus/metrics",
    "/hibiscus/docs",
    "/hibiscus/redoc",
    "/hibiscus/openapi.json",
}

# Prefixes that are exempt (OpenAPI sub-paths)
_EXEMPT_PREFIXES = (
    "/hibiscus/docs",
    "/hibiscus/redoc",
)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Bearer token validation middleware.

    Every non-exempt request MUST carry a valid Bearer token.
    The JWT_SECRET is always set (config generates a random one if missing),
    so auth is never silently disabled.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exempt paths (health, metrics, docs)
        path = request.url.path
        if path in _EXEMPT_PATHS or path.startswith(_EXEMPT_PREFIXES):
            return await call_next(request)

        # OPTIONS requests are handled by CORS middleware
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        else:
            token = ""

        # No token provided — reject
        if not token:
            return JSONResponse(
                {"error": "Authentication required. Provide a Bearer token."},
                status_code=401,
            )

        # Validate token
        try:
            import jwt as _jwt
            payload = _jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            user_id = payload.get("user_id") or payload.get("sub") or "anonymous"
            request.state.user_id = user_id
        except Exception as e:
            logger.warning("jwt_auth_failed", path=path, error=str(e))
            return JSONResponse(
                {"error": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)
