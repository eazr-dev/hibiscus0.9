"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Session memory (L1) — Redis-backed ephemeral state for active conversation context.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Redis connection singleton ────────────────────────────────────────────
_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection. Called at app startup."""
    global _redis_client
    try:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            max_connections=20,
        )
        await _redis_client.ping()
        logger.info("redis_connected", url=settings.redis_url.split("@")[-1])
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e), fallback="in_memory")
        _redis_client = None  # Will use in-memory fallback


async def close_redis() -> None:
    """Close Redis connection. Called at app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


def _session_key(session_id: str) -> str:
    return f"hibiscus:session:{session_id}"


# ── In-memory fallback (when Redis is unavailable) ────────────────────────
_memory_store: Dict[str, Dict] = {}


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full session data."""
    key = _session_key(session_id)
    try:
        if _redis_client:
            raw = await _redis_client.get(key)
            if raw:
                return json.loads(raw)
        else:
            return _memory_store.get(key)
    except Exception as e:
        logger.warning("session_get_failed", session_id=session_id, error=str(e))
        return _memory_store.get(key)
    return None


async def save_session(session_id: str, data: Dict[str, Any]) -> None:
    """Save full session data with TTL."""
    key = _session_key(session_id)
    serialized = json.dumps(data, ensure_ascii=False, default=str)
    try:
        if _redis_client:
            await _redis_client.setex(key, settings.redis_session_ttl, serialized)
        else:
            _memory_store[key] = data
    except Exception as e:
        logger.warning("session_save_failed", session_id=session_id, error=str(e))
        _memory_store[key] = data


async def append_message(
    session_id: str,
    role: str,  # "user" | "assistant"
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a message to the session conversation history."""
    session = await get_session(session_id) or {"messages": [], "created_at": time.time()}

    message = {
        "role": role,
        "content": content,
        "timestamp": time.time(),
    }
    if metadata:
        message["metadata"] = metadata

    session.setdefault("messages", []).append(message)
    session["updated_at"] = time.time()

    await save_session(session_id, session)


async def get_session_messages(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get the last N messages from session."""
    session = await get_session(session_id)
    if not session:
        return []
    messages = session.get("messages", [])
    return messages[-limit:] if len(messages) > limit else messages


async def store_uploaded_file(session_id: str, file_info: Dict[str, Any]) -> None:
    """Store uploaded file reference in session."""
    session = await get_session(session_id) or {"messages": [], "created_at": time.time()}
    session.setdefault("uploaded_files", []).append(file_info)
    session["updated_at"] = time.time()
    await save_session(session_id, session)


async def delete_session(session_id: str) -> None:
    """Delete a session (user logout or expiry)."""
    key = _session_key(session_id)
    try:
        if _redis_client:
            await _redis_client.delete(key)
        _memory_store.pop(key, None)
    except Exception as e:
        logger.warning("session_delete_failed", session_id=session_id, error=str(e))
