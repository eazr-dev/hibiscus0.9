"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Health endpoint — comprehensive dependency check for Redis, MongoDB, Neo4j, Qdrant, LLM providers.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
from typing import Any, Dict

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

from hibiscus.config import settings, ENGINE_NAME, ENGINE_VERSION, ENGINE_VENDOR, ENGINE_URL
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
        if _db is not None:
            await _db.command("ping")
            return {"status": "ok", "latency_ms": int((time.time() - start) * 1000)}
        return {"status": "degraded", "reason": "in_memory_fallback"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


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


async def _check_neo4j() -> Dict[str, Any]:
    """Check Neo4j connectivity."""
    start = time.time()
    try:
        from hibiscus.knowledge.graph.client import kg_client
        if not kg_client.is_connected:
            return {"status": "not_initialized", "note": "Run seed-kg to initialize"}
        result = await kg_client.query("RETURN 1 AS n", query_name="health")
        if result:
            return {"status": "ok", "latency_ms": int((time.time() - start) * 1000)}
        return {"status": "degraded", "reason": "query returned empty"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _check_qdrant() -> Dict[str, Any]:
    """Check Qdrant connectivity."""
    start = time.time()
    try:
        from hibiscus.knowledge.rag.client import rag_client
        if not rag_client.is_available:
            # Try to initialize
            await rag_client.connect()
        if rag_client._client is not None:
            info = await rag_client._client.get_collections()
            collections = [c.name for c in info.collections]
            return {
                "status": "ok",
                "latency_ms": int((time.time() - start) * 1000),
                "collections": collections,
            }
        return {"status": "not_initialized", "note": "Qdrant client not connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _build_health_response() -> tuple:
    """Build the health check response data. Returns (response_dict, http_status)."""
    start = time.time()

    results = await asyncio.gather(
        _check_redis(),
        _check_mongodb(),
        _check_deepseek(),
        _check_anthropic(),
        _check_neo4j(),
        _check_qdrant(),
        return_exceptions=True,
    )
    redis_result, mongo_result, ds_result, claude_result, neo4j_result, qdrant_result = results

    def safe_result(r, name):
        if isinstance(r, Exception):
            return {"status": "error", "error": str(r)}
        return r

    dependencies = {
        "redis": safe_result(redis_result, "redis"),
        "mongodb": safe_result(mongo_result, "mongodb"),
        "deepseek": safe_result(ds_result, "deepseek"),
        "anthropic": safe_result(claude_result, "anthropic"),
        "neo4j": safe_result(neo4j_result, "neo4j"),
        "qdrant": safe_result(qdrant_result, "qdrant"),
    }

    critical = ["redis"]
    critical_healthy = all(
        dependencies[k].get("status") in ("ok", "degraded")
        for k in critical
    )

    llm_ready = (
        dependencies["deepseek"].get("status") == "configured" or
        dependencies["anthropic"].get("status") == "configured"
    )

    overall_status = "healthy" if critical_healthy and llm_ready else "degraded"
    http_status = 200 if overall_status == "healthy" else 503

    total_latency_ms = int((time.time() - start) * 1000)

    response = {
        "engine": ENGINE_NAME.lower(),
        "version": ENGINE_VERSION,
        "vendor": ENGINE_VENDOR,
        "url": ENGINE_URL,
        "status": overall_status,
        "environment": settings.hibiscus_env,
        "latency_ms": total_latency_ms,
        "dependencies": dependencies,
        "capabilities": {
            "phase_1_ready": critical_healthy and llm_ready,
            "phase_2_ready": (
                dependencies["neo4j"].get("status") == "ok" and
                dependencies["qdrant"].get("status") == "ok"
            ),
            "streaming": True,
            "multi_agent": True,
        },
    }

    logger.info("health_check", status=overall_status, latency_ms=total_latency_ms)
    return response, http_status


@router.get(
    "/health/json",
    summary="Health check (JSON only)",
    include_in_schema=False,
)
async def health_json() -> JSONResponse:
    """JSON-only health endpoint used by the HTML dashboard."""
    response, http_status = await _build_health_response()
    return JSONResponse(content=response, status_code=http_status)


@router.get(
    "/health",
    summary="Hibiscus health check — all dependencies",
)
async def health(request: Request) -> JSONResponse:
    """
    Comprehensive health check of all Hibiscus dependencies.
    Returns HTML dashboard for browsers, JSON for API clients.
    """
    accept = request.headers.get("accept", "")

    if "text/html" in accept:
        dashboard_path = Path(__file__).parent / "static" / "health-dashboard.html"
        return HTMLResponse(content=dashboard_path.read_text())

    response, http_status = await _build_health_response()
    return JSONResponse(content=response, status_code=http_status)


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Prometheus-format metrics for scraping by Prometheus or compatible systems.",
    response_class=PlainTextResponse,
)
async def metrics() -> PlainTextResponse:
    """Return Prometheus text-format metrics (text/plain; version=0.0.4)."""
    try:
        from hibiscus.observability.metrics import get_metrics_text
        text = get_metrics_text()
        return PlainTextResponse(content=text, media_type="text/plain; version=0.0.4")
    except ImportError:
        return PlainTextResponse(content="# prometheus_client not installed\n")
    except Exception as e:
        return PlainTextResponse(content=f"# metrics error: {e}\n")
