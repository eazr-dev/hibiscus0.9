"""
CORS Middleware Configuration
==============================
Configures Cross-Origin Resource Sharing for the Hibiscus API.

In development: allows all origins.
In production: restricts to EAZR frontend domains only.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hibiscus.config import settings


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
    "http://localhost:8000",     # Botproject
    "http://localhost:8001",     # Hibiscus dev
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]


def configure_cors(app: FastAPI) -> None:
    """
    Add CORS middleware to the FastAPI app.

    Development: allows all origins for easy testing.
    Production: restricts to known EAZR domains.
    """
    if settings.is_production:
        origins = _PRODUCTION_ORIGINS
    else:
        # Development: allow all origins
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
