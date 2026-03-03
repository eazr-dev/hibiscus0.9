"""
Custom middleware for the application
"""
import json
import logging
from fastapi import Request
from session_security.session_manager import session_manager

logger = logging.getLogger(__name__)


async def session_regeneration_middleware(request: Request, call_next):
    """
    Middleware to handle session regeneration transparently
    Automatically regenerates expired sessions and updates request data
    """
    # Import here to avoid circular imports
    from core.dependencies import get_session, store_session

    # Only process for API endpoints that use sessions
    if request.url.path.startswith("/api/") or request.url.path in ["/ask", "/enhanced-chatbot", "/quick-action"]:
        try:
            # Try to get session_id from request
            # ONLY read body for JSON requests — reading the body stream
            # breaks FastAPI's multipart parser (used for file uploads)
            content_type = (request.headers.get("content-type") or "").lower()
            is_json = "application/json" in content_type
            if request.method == "POST" and is_json:
                body = await request.body()
                request._body = body  # Store for later use

                try:
                    data = json.loads(body)
                    session_id = data.get("session_id")

                    if session_id:
                        # Check and potentially regenerate session
                        new_session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
                            session_id,
                            get_session,
                            store_session
                        )

                        if was_regenerated:
                            # Update the request data with new session_id
                            data["session_id"] = new_session_id
                            data["_original_session_id"] = session_id

                            # Create new request with updated data
                            request._body = json.dumps(data).encode()

                except Exception as e:
                    logger.debug(f"Session middleware parsing error: {e}")
                    pass
        except Exception as e:
            logger.error(f"Session middleware error: {e}")

    response = await call_next(request)
    return response


def setup_middleware(app):
    """
    Setup all middleware for the application
    """
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.middleware.cors import CORSMiddleware
    from session_security.security_middleware import add_security_headers
    from core.config import settings

    # Response compression for faster data transfer
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

    # Security headers middleware
    app.middleware("http")(add_security_headers)

    # Session regeneration middleware
    app.middleware("http")(session_regeneration_middleware)

    # CORS configuration - Whitelist specific origins for security
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,  # Exact domain matches
        allow_origin_regex=settings.VERCEL_PATTERN,  # Pattern for Vercel preview deployments
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],  # All common methods
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-User-Token",
            "Cache-Control",
            "Pragma",
            "Expires"
        ],  # Common headers including custom ones
        expose_headers=["Content-Length", "X-Session-Id"],  # Headers accessible to browser
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    logger.info("✓ All middleware configured successfully")
