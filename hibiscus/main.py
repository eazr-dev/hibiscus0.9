"""
Hibiscus — EAZR AI Intelligence Engine
=======================================
FastAPI application entry point.
"""
import asyncio
import os
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
    logger.info(
        "hibiscus_starting",
        version=settings.app_version,
        environment=settings.hibiscus_env,
        eazr_api_base=settings.eazr_api_base,
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
        title="Hibiscus — EAZR AI Intelligence Engine",
        description="12-agent insurance AI operating system. DeepSeek-primary.",
        version=settings.app_version,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/hibiscus/docs",
        redoc_url="/hibiscus/redoc",
        openapi_url="/hibiscus/openapi.json",
    )

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
