"""
Main Application File
Eazr Financial Assistant - Modular Architecture

This is the main application file using modular routers.
Old monolithic version (11,386 lines) backed up as app_OLD_BACKUP.py

To run:
    uvicorn app:app --host 0.0.0.0 --port 8000
"""
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from core.config import settings
from core.middleware import setup_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup all middleware (CORS, GZIP, Security, Session)
setup_middleware(app)

# Setup rate limiting
try:
    from core.rate_limiter import setup_rate_limiter
    setup_rate_limiter(app)
except ImportError as e:
    logger.warning(f"⚠ Rate limiter not available: {e}")

# -------------------- Custom Exception Handler --------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler to format error responses consistently.
    Uses centralized error format.

    Standard response format:
    {
        "success": false,
        "error_code": "POL_8001",
        "message": "The provided name does not match the policy holder name in the document.",
        "details": [...]  // Optional: array of field-level errors
    }
    """
    # If detail is a dictionary, transform it to centralized format
    if isinstance(exc.detail, dict):
        error_response = {
            "success": False,
            "error_code": exc.detail.get("error", exc.detail.get("error_code", "ERROR")),
            "message": exc.detail.get("message", "An error occurred")
        }

        # Convert "details" dict to "details" array format if present
        if "details" in exc.detail:
            details_data = exc.detail["details"]
            if isinstance(details_data, dict):
                # Convert dict to array of ErrorDetail format
                error_response["details"] = [
                    {"field": k, "message": str(v)} for k, v in details_data.items()
                ]
            elif isinstance(details_data, list):
                error_response["details"] = details_data

        # Pass through additional fields (isDuplicate, existingPolicy, etc.)
        for key in ["isDuplicate", "existingPolicy", "policyId", "analysisId", "userId"]:
            if key in exc.detail:
                error_response[key] = exc.detail[key]

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )

    # If detail is a string, return simple error format
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": "ERROR",
            "message": str(exc.detail)
        }
    )

# -------------------- Import and Include Routers --------------------
# Import routers as they are created

# Health check router (example - already created)
try:
    from routers.health import router as health_router
    app.include_router(health_router)
    logger.info("✓ Health router loaded")
except ImportError as e:
    logger.warning(f"⚠ Health router not available: {e}")


# Authentication router
try:
    from routers.auth import router as auth_router
    app.include_router(auth_router)
    logger.info("✓ Auth router loaded")
except ImportError as e:
    logger.warning(f"⚠ Auth router not available: {e}")

# Chat router
try:
    from routers.chat import router as chat_router
    app.include_router(chat_router)
    logger.info("✓ Chat router loaded")
except ImportError as e:
    logger.warning(f"⚠ Chat router not available: {e}")

# User profile router
try:
    from routers.user import router as user_router
    app.include_router(user_router)
    logger.info("✓ User router loaded")
except ImportError as e:
    logger.warning(f"⚠ User router not available: {e}")

# Admin router
try:
    from routers.admin import router as admin_router
    app.include_router(admin_router)
    logger.info("✓ Admin router loaded")
except ImportError as e:
    logger.warning(f"⚠ Admin router not available: {e}")

# Insurance/Policy router
try:
    from routers.policy import router as policy_router
    app.include_router(policy_router)
    logger.info("✓ Policy router loaded")
except ImportError as e:
    logger.warning(f"⚠ Policy router not available: {e}")

# Frontend router
try:
    from routers.frontend import router as frontend_router
    app.include_router(frontend_router)
    logger.info("✓ Frontend router loaded")
except ImportError as e:
    logger.warning(f"⚠ Frontend router not available: {e}")

# Policy Locker router
try:
    from routers.policy_locker import router as policy_locker_router
    app.include_router(policy_locker_router)
    logger.info("✓ Policy Locker router loaded")
except Exception as e:
    logger.error(f"⚠ Policy Locker router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Policy Upload router (Simplified API)
try:
    from routers.policy_upload import router as policy_upload_router
    app.include_router(policy_upload_router)
    logger.info("✓ Policy Upload router loaded")
except Exception as e:
    logger.error(f"⚠ Policy Upload router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# User Policies router (Get all policies)
try:
    from routers.user_policies import router as user_policies_router
    app.include_router(user_policies_router)
    logger.info("✓ User Policies router loaded")
except Exception as e:
    logger.error(f"⚠ User Policies router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Portfolio Breakdown router
try:
    from routers.portfolio_breakdown import router as portfolio_breakdown_router
    app.include_router(portfolio_breakdown_router)
    logger.info("✓ Portfolio Breakdown router loaded")
except Exception as e:
    logger.error(f"⚠ Portfolio Breakdown router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Family Members router
try:
    from routers.family_members import router as family_members_router
    app.include_router(family_members_router)
    logger.info("✓ Family Members router loaded")
except Exception as e:
    logger.error(f"⚠ Family Members router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Dashboard router (Protection Score, Dashboard Data, Renewals, Insights)
try:
    from routers.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
    logger.info("✓ Dashboard router loaded")
except Exception as e:
    logger.error(f"⚠ Dashboard router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Legal router (Privacy Policy, Terms & Conditions)
try:
    from routers.legal import router as legal_router
    app.include_router(legal_router)
    logger.info("✓ Legal router loaded")
except Exception as e:
    logger.error(f"⚠ Legal router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Contact Support router
try:
    from routers.contact_support import router as contact_support_router
    app.include_router(contact_support_router)
    logger.info("✓ Contact Support router loaded")
except Exception as e:
    logger.error(f"⚠ Contact Support router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Eazr Credit Waitlist router
try:
    from routers.eazr_credit import router as eazr_credit_router
    app.include_router(eazr_credit_router)
    logger.info("✓ Eazr Credit Waitlist router loaded")
except Exception as e:
    logger.error(f"⚠ Eazr Credit router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Rewards router (Free Personal Accidental Insurance)
try:
    from routers.rewards import router as rewards_router
    app.include_router(rewards_router)
    logger.info("✓ Rewards router loaded")
except Exception as e:
    logger.error(f"⚠ Rewards router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Rate Limit Admin router (Analytics & Management)
try:
    from routers.rate_limit_admin import router as rate_limit_admin_router
    app.include_router(rate_limit_admin_router)
    logger.info("✓ Rate Limit Admin router loaded")
except Exception as e:
    logger.error(f"⚠ Rate Limit Admin router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Cards router (Credit & Debit Cards API)
try:
    from routers.cards import router as cards_router
    app.include_router(cards_router)
    logger.info("✓ Cards router loaded")
except Exception as e:
    logger.error(f"⚠ Cards router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Notifications router (Firebase Push Notifications)
try:
    from routers.notifications import router as notifications_router
    app.include_router(notifications_router)
    logger.info("✓ Notifications router loaded")
except Exception as e:
    logger.error(f"⚠ Notifications router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# WebSocket Chat router (Real-time chat with streaming)
try:
    from routers.websocket_chat import router as websocket_router
    app.include_router(websocket_router)
    logger.info("✓ WebSocket Chat router loaded")
except Exception as e:
    logger.error(f"⚠ WebSocket Chat router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# CEO Note router (Dynamic welcome note for first-time users)
try:
    from routers.ceo_note import router as ceo_note_router
    app.include_router(ceo_note_router)
    logger.info("✓ CEO Note router loaded")
except Exception as e:
    logger.error(f"⚠ CEO Note router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Banners router (Promotional banners, ads, coming soon features)
try:
    from routers.banners import router as banners_router
    app.include_router(banners_router)
    logger.info("✓ Banners router loaded")
except Exception as e:
    logger.error(f"⚠ Banners router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())


# Bill Audit Intelligence router (Bill analysis, discrepancy detection, reports)
try:
    from routers.bill_audit import router as bill_audit_router
    app.include_router(bill_audit_router)
    logger.info("✓ Bill Audit Intelligence router loaded")
except Exception as e:
    logger.error(f"⚠ Bill Audit router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

# HBF/GBF Financing router (Hospital/Garage Bill Financing)
try:
    from routers.hbf import router as hbf_router
    app.include_router(hbf_router)
    logger.info("✓ HBF/GBF Financing router loaded")
except Exception as e:
    logger.error(f"⚠ HBF/GBF router not available: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())


# -------------------- Static Files --------------------
# Serve frontend static files
try:
    app.mount("/frontend", StaticFiles(directory=str(settings.FRONTEND_DIR)), name="frontend")
    logger.info(f"✓ Static files mounted from {settings.FRONTEND_DIR}")
except Exception as e:
    logger.warning(f"⚠ Could not mount static files: {e}")


# -------------------- Startup/Shutdown Events --------------------

@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting Eazr Financial Assistant API")
    logger.info("=" * 60)

    # Initialize core components
    from core.config import get_llm_instance, get_rag_chain
    from core.dependencies import (
        MONGODB_AVAILABLE,
        REDIS_AVAILABLE,
        LANGGRAPH_AVAILABLE,
        VOICE_AVAILABLE,
        MULTILINGUAL_AVAILABLE
    )

    # Initialize Card Service (synchronous - uses shared MongoDB connection)
    try:
        from services.card_service import card_service
        card_service.initialize()
        logger.info("✓ Card service initialized successfully")
    except Exception as e:
        logger.warning(f"⚠ Card service initialization failed (cards API will auto-init on first request): {e}")

    # Initialize LLM
    try:
        llm = get_llm_instance()
        logger.info("✓ LLM initialized successfully")
    except Exception as e:
        logger.error(f"✗ LLM initialization failed: {e}")

    # Initialize RAG chain
    try:
        rag_chain = get_rag_chain()
        logger.info("✓ RAG chain initialized successfully")
    except Exception as e:
        logger.error(f"✗ RAG chain initialization failed: {e}")

    # Initialize Contact Support Service
    if MONGODB_AVAILABLE:
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            from services.contact_support_service import initialize_contact_support_service
            initialize_contact_support_service(mongodb_chat_manager)
            logger.info("✓ Contact Support Service initialized")
        except Exception as e:
            logger.error(f"✗ Contact Support Service initialization failed: {e}")

    # Initialize Firebase for Push Notifications
    try:
        from database_storage.firebase_config import is_firebase_available
        firebase_status = is_firebase_available()
        if firebase_status:
            logger.info("✓ Firebase Admin SDK initialized")
        else:
            logger.warning("⚠ Firebase Admin SDK not available")
    except Exception as e:
        logger.warning(f"⚠ Firebase initialization skipped: {e}")
        firebase_status = False

    # Initialize WebSocket background tasks
    websocket_available = False
    try:
        from routers.websocket_chat import start_background_tasks
        await start_background_tasks()
        websocket_available = True
        logger.info("✓ WebSocket background tasks started")
    except Exception as e:
        logger.warning(f"⚠ WebSocket background tasks not started: {e}")

    # Log feature availability
    logger.info("\n📊 Feature Availability:")
    logger.info(f"   MongoDB: {'✓' if MONGODB_AVAILABLE else '✗'}")
    logger.info(f"   Redis: {'✓' if REDIS_AVAILABLE else '✗'}")
    logger.info(f"   LangGraph: {'✓' if LANGGRAPH_AVAILABLE else '✗'}")
    logger.info(f"   Voice Recognition: {'✓' if VOICE_AVAILABLE else '✗'}")
    logger.info(f"   Multilingual Support: {'✓' if MULTILINGUAL_AVAILABLE else '✗'}")
    logger.info(f"   Firebase/FCM: {'✓' if firebase_status else '✗'}")
    logger.info(f"   WebSocket Chat: {'✓' if websocket_available else '✗'}")

    logger.info("\n🌐 API Documentation:")
    logger.info(f"   Swagger UI: {settings.BASE_URL}/docs")
    logger.info(f"   ReDoc: {settings.BASE_URL}/redoc")
    logger.info(f"   WebSocket: ws://{settings.BASE_URL.replace('http://', '').replace('https://', '')}/ws/chat")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown
    """
    logger.info("🛑 Shutting down Eazr Financial Assistant API")

    # Close MongoDB connections
    try:
        from core.dependencies import MONGODB_AVAILABLE
        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            if mongodb_chat_manager and hasattr(mongodb_chat_manager, 'client'):
                mongodb_chat_manager.client.close()
                logger.info("✓ MongoDB connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing MongoDB: {e}")

    # Close Redis connections
    try:
        from core.dependencies import REDIS_AVAILABLE
        if REDIS_AVAILABLE:
            from database_storage.simple_redis_config import redis_client
            if redis_client:
                redis_client.close()
                logger.info("✓ Redis connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing Redis: {e}")

    # Close Card Service connections (synchronous - just clears references)
    try:
        from services.card_service import card_service
        card_service.close()
        logger.info("✓ Card service connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing Card service: {e}")

    # Stop WebSocket background tasks
    try:
        from routers.websocket_chat import stop_background_tasks
        await stop_background_tasks()
        logger.info("✓ WebSocket background tasks stopped")
    except Exception as e:
        logger.error(f"✗ Error stopping WebSocket tasks: {e}")

    logger.info("👋 Shutdown complete")


# -------------------- Insurance API Integration --------------------
import httpx
import os
from typing import List, Dict, Optional

# Insurance API Configuration
INSURANCE_API_BASE_URL = os.getenv("INSURANCE_API_URL", "https://api.yourinsurance.com")
INSURANCE_API_KEY = os.getenv("INSURANCE_API_KEY", "")
INSURANCE_API_VERIFY_SSL = os.getenv("INSURANCE_API_VERIFY_SSL", "true").lower() == "true"

async def fetch_insurance_policies(access_token: Optional[str] = None) -> List[Dict]:
    """
    Fetch insurance policies from external API

    Args:
        access_token: Optional user access token for personalized policies

    Returns:
        List of policy dictionaries with structure:
        {
            "id": "policy_id",
            "title": "Policy Title",
            "category": "health/life/motor",
            "productName": "Product Name",
            "premiumAmount": 5000,
            "coverageAmount": 500000,
            "description": "Policy description",
            "features": ["Feature 1", "Feature 2"]
        }
    """
    try:
        # Skip API call if no URL configured
        if not INSURANCE_API_BASE_URL or INSURANCE_API_BASE_URL == "https://api.yourinsurance.com":
            logger.warning("⚠️ Insurance API not configured, using fallback")
            return []

        headers = {
            "Content-Type": "application/json",
        }

        # Add API key if provided
        if INSURANCE_API_KEY:
            headers["Authorization"] = f"Bearer {INSURANCE_API_KEY}"

        # Add user token if provided
        if access_token:
            headers["X-User-Token"] = access_token

        # Configure SSL verification
        verify_ssl = INSURANCE_API_VERIFY_SSL

        # Call insurance API with SSL handling
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=verify_ssl,  # Control SSL verification
            follow_redirects=True
        ) as client:
            logger.info(f"📡 Fetching policies from: {INSURANCE_API_BASE_URL}/policies")

            response = await client.get(
                f"{INSURANCE_API_BASE_URL}/policies",
                headers=headers
            )

            response.raise_for_status()

            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                policies = data.get('policies', data.get('data', []))
            else:
                policies = data

            logger.info(f"✅ Fetched {len(policies)} insurance policies from API")
            return policies

    except httpx.ConnectError as e:
        logger.error(f"❌ Connection error to insurance API: {e}")
        logger.info("💡 Using fallback to static policies")
        return []
    except httpx.TimeoutException as e:
        logger.error(f"❌ Timeout connecting to insurance API: {e}")
        logger.info("💡 Using fallback to static policies")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP {e.response.status_code} error from insurance API: {e}")
        logger.info("💡 Using fallback to static policies")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching insurance policies: {e}")
        logger.info("💡 Using fallback to static policies")
        return []


# -------------------- Root Endpoint --------------------
# Note: Root endpoint (/) is handled by frontend router
# which serves login.html or API info page


# -------------------- For Local Testing --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
