"""
Hibiscus v0.9 — EAZR AI Insurance Intelligence Engine
Module: main
Purpose: FastAPI application entry point and lifespan management
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger, configure_logging
from hibiscus.api.router import router as api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    configure_logging(settings.hibiscus_log_level)

    # ── Startup banner ────────────────────────────────────────────
    print(
        "\n"
        "╔══════════════════════════════════════════════════╗\n"
        "║  Hibiscus v0.9 — EAZR AI Intelligence Engine    ║\n"
        "║  12 Agents | 1,207 Products | 100 Regulations   ║\n"
        "║  Copyright (c) 2026 EAZR Digipayments Pvt Ltd   ║\n"
        "╚══════════════════════════════════════════════════╝\n",
        file=sys.stderr,
        flush=True,
    )

    logger.info(
        "hibiscus_starting",
        version=settings.app_version,
        environment=settings.hibiscus_env,
    )

    # ── Initialize connections ──────────────────────────────────
    from hibiscus.memory.layers.session import init_redis
    from hibiscus.memory.layers.document import init_mongo

    await init_redis()
    await init_mongo()

    logger.info("hibiscus_ready", message="All connections established. Hibiscus is live.")

    # ── Pre-warm response cache (non-blocking background task) ───────
    try:
        from hibiscus.utils.cache_warmup import warmup_response_cache
        asyncio.create_task(warmup_response_cache())
        logger.info("cache_warmup_task_scheduled")
    except Exception as e:
        logger.warning("cache_warmup_schedule_failed", error=str(e))

    # ── Start KG enrichment flush loop (background) ────────────────
    try:
        from hibiscus.services.kg_enrichment import kg_enrichment
        asyncio.create_task(kg_enrichment.start_flush_loop())
        logger.info("kg_enrichment_loop_scheduled")
    except Exception as e:
        logger.warning("kg_enrichment_schedule_failed", error=str(e))

    yield

    # ── Shutdown ─────────────────────────────────────────────────
    logger.info("hibiscus_shutting_down")

    # Stop KG enrichment (drain queue)
    try:
        from hibiscus.services.kg_enrichment import kg_enrichment
        await kg_enrichment.stop()
    except Exception:
        pass

    from hibiscus.memory.layers.session import close_redis
    from hibiscus.memory.layers.document import close_mongo
    await close_redis()
    await close_mongo()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hibiscus v0.9 — EAZR AI Intelligence Engine",
        description=(
            "Hibiscus is EAZR's AI insurance intelligence engine — a 12-agent orchestration system "
            "that provides policy analysis, product recommendations, claims guidance, tax advisory, "
            "surrender value calculations, and portfolio optimization for Indian insurance consumers.\n\n"
            "**Key capabilities:**\n"
            "- Native PDF extraction (ABSORB pipeline) — classify, extract, validate, score, gap-analyze\n"
            "- Knowledge Graph: 62 insurers, 1,207 products, 100 IRDAI regulations, 760 CSR benchmarks\n"
            "- RAG: 847 chunks (IRDAI circulars, glossary, tax rules, claims processes)\n"
            "- 6-layer memory: session, conversation, profile, portfolio, knowledge, document\n"
            "- Streaming SSE for real-time token delivery\n\n"
            "**Authentication:** Bearer JWT token (optional in dev mode)\n\n"
            "**Rate limiting:** 60 requests/minute per IP\n\n"
            "**LLM cost:** ~₹0.045/conversation average"
        ),
        version=settings.app_version,
        terms_of_service="https://eazr.in/terms",
        contact={
            "name": "EAZR AI Engineering",
            "url": "https://eazr.in",
            "email": "engineering@eazr.in",
        },
        license_info={
            "name": "Proprietary",
            "url": "https://eazr.in/license",
        },
        openapi_tags=[
            {"name": "Chat", "description": "Conversational AI endpoint — streaming and non-streaming"},
            {"name": "Analysis", "description": "Policy document analysis and scoring"},
            {"name": "Portfolio", "description": "Portfolio breakdown and optimization"},
            {"name": "Health", "description": "Service health, metrics, and dependency status"},
            {"name": "WebSocket", "description": "Real-time bidirectional chat via WebSocket"},
        ],
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/hibiscus/docs",
        redoc_url="/hibiscus/redoc",
        openapi_url="/hibiscus/openapi.json",
    )

    # ── Custom OpenAPI schema with security ────────────────────────
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            contact=app.contact,
            license_info=app.license_info,
        )
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token. Optional in dev mode (empty JWT_SECRET = auth skipped).",
            }
        }
        schema["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi

    # ── CORS ─────────────────────────────────────────────────────
    from hibiscus.api.middleware.cors import configure_cors
    configure_cors(app)

    # ── Request ID middleware ─────────────────────────────────────
    from hibiscus.api.middleware.request_id import RequestIdMiddleware
    app.add_middleware(RequestIdMiddleware)

    # ── Rate limit middleware (applied after request_id) ──────────
    from hibiscus.api.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # ── JWT auth middleware (applied after rate_limit) ────────────
    from hibiscus.api.middleware.auth import JWTAuthMiddleware
    app.add_middleware(JWTAuthMiddleware)

    # ── Routes ───────────────────────────────────────────────────
    app.include_router(api_router, prefix="/hibiscus")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "hibiscus.main:app",
        host="0.0.0.0",
        port=settings.hibiscus_port,
        reload=settings.hibiscus_env == "development",
        log_config=None,  # Use our structured logging
    )
