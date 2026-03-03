"""
Hibiscus Health Endpoint
========================
GET /hibiscus/health — Comprehensive dependency health check

Checks all dependencies:
- LLM providers (DeepSeek, Claude)
- Redis (session memory)
- MongoDB (document memory)
- EAZR existing API (botproject)
- Neo4j (KG — Phase 2)
- Qdrant (RAG — Phase 2)
"""
import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


async def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    start = time.time()
    try:
        from hibiscus.memory.layers.session import _redis_client
        if _redis_client:
            await _redis_client.ping()
            return {"status": "ok", "latency_ms": int((time.time() - start) * 1000)}
        return {"status": "degraded", "reason": "in_memory_fallback"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _check_mongodb() -> Dict[str, Any]:
    """Check MongoDB connectivity."""
    start = time.time()
    try:
        from hibiscus.memory.layers.document import _db
        if _db:
            await _db.command("ping")
            return {"status": "ok", "latency_ms": int((time.time() - start) * 1000)}
        return {"status": "degraded", "reason": "in_memory_fallback"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _check_eazr_api() -> Dict[str, Any]:
    """Check EAZR botproject API connectivity."""
    start = time.time()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.eazr_api_base}/health")
            if resp.status_code == 200:
                return {
                    "status": "ok",
                    "latency_ms": int((time.time() - start) * 1000),
                    "eazr_api_base": settings.eazr_api_base,
                }
            return {
                "status": "degraded",
                "http_status": resp.status_code,
            }
    except Exception as e:
        return {"status": "error", "error": str(e), "eazr_api_base": settings.eazr_api_base}


async def _check_deepseek() -> Dict[str, Any]:
    """Check DeepSeek API key configuration."""
    if not settings.deepseek_api_key:
        return {"status": "not_configured", "note": "DeepSeek is primary LLM — set DEEPSEEK_API_KEY"}
    return {"status": "configured", "model": settings.deepseek_v3_model}


async def _check_anthropic() -> Dict[str, Any]:
    """Check Anthropic API key configuration."""
    if not settings.anthropic_api_key:
        return {"status": "not_configured", "note": "Claude is safety net (Tier 3) — optional"}
    return {"status": "configured", "model": settings.claude_sonnet_model}


@router.get(
    "/health",
    summary="Hibiscus health check — all dependencies",
)
async def health() -> JSONResponse:
    """
    Comprehensive health check of all Hibiscus dependencies.
    Returns 200 if all critical services are healthy, 503 if any critical service is down.
    """
    start = time.time()

    # Run all checks in parallel
    redis_result, mongo_result, eazr_result, ds_result, claude_result = await asyncio.gather(
        _check_redis(),
        _check_mongodb(),
        _check_eazr_api(),
        _check_deepseek(),
        _check_anthropic(),
        return_exceptions=True,
    )

    # Handle exceptions from gather
    def safe_result(r, name):
        if isinstance(r, Exception):
            return {"status": "error", "error": str(r)}
        return r

    dependencies = {
        "redis": safe_result(redis_result, "redis"),
        "mongodb": safe_result(mongo_result, "mongodb"),
        "eazr_api": safe_result(eazr_result, "eazr_api"),
        "deepseek": safe_result(ds_result, "deepseek"),
        "anthropic": safe_result(claude_result, "anthropic"),
        # Phase 2 dependencies
        "neo4j": {"status": "not_started", "phase": "Phase 2"},
        "qdrant": {"status": "not_started", "phase": "Phase 2"},
    }

    # Critical services: Redis and EAZR API are critical for Phase 1
    critical = ["redis", "eazr_api"]
    critical_healthy = all(
        dependencies[k].get("status") in ("ok", "degraded")
        for k in critical
    )

    # LLM: at least one must be configured
    llm_ready = (
        dependencies["deepseek"].get("status") == "configured" or
        dependencies["anthropic"].get("status") == "configured"
    )

    overall_status = "healthy" if critical_healthy and llm_ready else "degraded"
    http_status = 200 if overall_status == "healthy" else 503

    total_latency_ms = int((time.time() - start) * 1000)

    response = {
        "status": overall_status,
        "version": settings.app_version,
        "environment": settings.hibiscus_env,
        "latency_ms": total_latency_ms,
        "dependencies": dependencies,
        "capabilities": {
            "phase_1_ready": critical_healthy and llm_ready,
            "phase_2_ready": False,  # Neo4j + Qdrant not yet started
            "streaming": True,
            "multi_agent": True,
        },
    }

    logger.info("health_check", status=overall_status, latency_ms=total_latency_ms)

    return JSONResponse(content=response, status_code=http_status)
