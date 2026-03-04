"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
JWT auth middleware — token validation, dev-mode bypass, user context injection.
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


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Bearer token validation middleware.

    Skipped entirely when settings.jwt_secret is empty (dev mode).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Dev mode — skip validation when no secret configured
        if not settings.jwt_secret:
            return await call_next(request)

        # Exempt paths (health, metrics, docs)
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        token = request.headers.get("Authorization", "")
        if token.startswith("Bearer "):
            token = token[7:].strip()
        else:
            token = ""

        # No token provided → treat as anonymous internal call (pass through)
        # This allows internal callers (eval runner, botproject service mesh) to proceed.
        # Only reject when a token IS provided but is invalid.
        if not token:
            return await call_next(request)

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
            logger.warning("jwt_auth_failed", path=request.url.path, error=str(e))
            return JSONResponse(
                {"error": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)
