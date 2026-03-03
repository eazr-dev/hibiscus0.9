"""
Rate Limit Middleware
=====================
Redis sliding window rate limiter — 60 requests/minute per user/IP.

Only applied to chat and analyze endpoints.
Graceful fallback: if Redis is unavailable, requests pass through (logged).
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

_RATE_LIMITED_PATHS = {"/hibiscus/chat", "/hibiscus/analyze"}
_MAX_REQUESTS = 60
_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis INCR + EXPIRE.

    Key: rate_limit:{user_id_or_ip}
    Allows MAX_REQUESTS per WINDOW_SECONDS.
    Falls back gracefully when Redis is unavailable.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in _RATE_LIMITED_PATHS:
            return await call_next(request)

        # Identify caller: prefer JWT user_id set by auth middleware, fall back to IP
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            client = request.client
            user_id = client.host if client else "unknown"

        key = f"rate_limit:{user_id}"

        try:
            from hibiscus.memory.layers.session import get_redis
            redis = await get_redis()
            if redis is not None:
                count = await redis.incr(key)
                if count == 1:
                    # First request in window — set expiry
                    await redis.expire(key, _WINDOW_SECONDS)
                if count > _MAX_REQUESTS:
                    logger.warning(
                        "rate_limit_exceeded",
                        user_id=user_id,
                        count=count,
                        path=request.url.path,
                    )
                    return JSONResponse(
                        {
                            "error": "Rate limit exceeded",
                            "detail": f"Max {_MAX_REQUESTS} requests per {_WINDOW_SECONDS}s",
                        },
                        status_code=429,
                        headers={"Retry-After": str(_WINDOW_SECONDS)},
                    )
        except Exception as e:
            # Redis unavailable — allow through with warning
            logger.warning("rate_limit_redis_unavailable", error=str(e), user_id=user_id)

        return await call_next(request)
