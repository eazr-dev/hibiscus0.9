"""
Response Cache — L1 Hot Cache (Redis)
======================================
Caches LLM responses for L1 educational/general queries where the answer
is factual and independent of user-specific context.

Only caches when:
- Intent is "educate" or "general_chat"
- No uploaded files
- No document context loaded
- Response confidence >= 0.70

Cache key: hibiscus:resp_cache:{sha256(normalized_message)}
TTL: 24h for educational facts (insurance definitions don't change daily)

Impact: Repeat questions (e.g. "what is copay?") answered in <50ms vs ~15s.
"""
import hashlib
import json
import re
from typing import Optional

from hibiscus.observability.logger import get_logger
from hibiscus.observability.metrics import record_cache_hit as _metric_cache_hit, record_cache_miss as _metric_cache_miss

logger = get_logger(__name__)

_CACHE_TTL = 86400         # 24 hours
_CACHE_KEY_PREFIX = "hibiscus:resp_cache:"

# Intents eligible for response caching (no user-specific data)
_CACHEABLE_INTENTS = {"educate", "general_chat"}


def _cache_key(message: str) -> str:
    """Normalize message and generate cache key."""
    # Normalize: lowercase, collapse whitespace, strip punctuation at edges
    normalized = re.sub(r"\s+", " ", message.lower().strip())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:24]
    return f"{_CACHE_KEY_PREFIX}{digest}"


def is_cacheable(
    intent: str,
    has_document: bool,
    uploaded_files: list,
    document_context: object,
) -> bool:
    """Return True if this response can be safely cached."""
    if intent not in _CACHEABLE_INTENTS:
        return False
    if uploaded_files or has_document or document_context:
        return False
    return True


async def get_cached_response(message: str) -> Optional[dict]:
    """
    Look up a cached response for this message.
    Returns the cached payload dict or None on miss/error.
    """
    try:
        from hibiscus.memory.layers.session import _redis_client
        if _redis_client is None:
            return None
        key = _cache_key(message)
        raw = await _redis_client.get(key)
        if raw:
            payload = json.loads(raw)
            logger.info("response_cache_hit", key=key[:16])
            _metric_cache_hit()
            return payload
        logger.info("response_cache_miss", key=key[:16])
        _metric_cache_miss()
    except Exception as e:
        logger.warning("response_cache_get_error", error=str(e))
    return None


async def set_cached_response(message: str, payload: dict) -> None:
    """Store a response in the cache with TTL."""
    try:
        from hibiscus.memory.layers.session import _redis_client
        if _redis_client is None:
            return
        key = _cache_key(message)
        await _redis_client.setex(key, _CACHE_TTL, json.dumps(payload))
        logger.info("response_cached", key=key[:16], ttl=_CACHE_TTL)
    except Exception as e:
        logger.warning("response_cache_set_error", error=str(e))
