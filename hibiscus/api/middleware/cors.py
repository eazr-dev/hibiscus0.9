"""
Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
CORS middleware — configures allowed origins for frontend integration.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# Production origins — EAZR frontend domains
_PRODUCTION_ORIGINS = [
    "https://app.eazr.in",
    "https://www.eazr.in",
    "https://eazr.in",
    "https://admin.eazr.in",
]

# Development origins — local development servers
_DEVELOPMENT_ORIGINS = [
    "http://localhost:3000",     # Next.js dev server
    "http://localhost:8080",     # Flutter web dev
    "http://localhost:8001",     # Hibiscus dev
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]


def configure_cors(app: FastAPI) -> None:
    """
    Add CORS middleware to the FastAPI app.

    Origin resolution order:
    1. CORS_ALLOWED_ORIGINS env var (comma-separated) — highest priority
    2. Production: hardcoded EAZR production domains
    3. Development: hardcoded localhost development servers

    The wildcard "*" is NEVER used — even in development. This prevents
    credential leakage from misconfigured browser extensions or scripts.
    """
    # Check env-configured origins first
    env_origins = settings.cors_allowed_origins.strip()
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
        # Reject wildcard even if someone puts it in the env var
        origins = [o for o in origins if o != "*"]
    elif settings.is_production:
        origins = _PRODUCTION_ORIGINS
    else:
        origins = _DEVELOPMENT_ORIGINS

    # In production, merge env origins with hardcoded production origins
    if settings.is_production:
        all_origins = list(set(origins + _PRODUCTION_ORIGINS))
    else:
        all_origins = list(set(origins))

    logger.info(
        "cors_configured",
        origin_count=len(all_origins),
        is_production=settings.is_production,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
