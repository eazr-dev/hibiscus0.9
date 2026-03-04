"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Memory database — PostgreSQL async session factory for profile and outcome persistence.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Optional

import asyncpg

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

_pool: Optional[asyncpg.Pool] = None


def _pg_url() -> str:
    """Convert SQLAlchemy-style URL to raw asyncpg URL."""
    url = settings.postgresql_url
    # Strip SQLAlchemy dialect prefix if present
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if url.startswith(prefix):
            url = "postgresql://" + url[len(prefix):]
            break
    return url


async def get_pool() -> Optional[asyncpg.Pool]:
    """Return (or lazily create) the shared connection pool.

    Returns None when PostgreSQL is unavailable, allowing callers to degrade
    gracefully to their in-memory fallback.
    """
    global _pool
    if _pool is not None:
        return _pool

    try:
        _pool = await asyncpg.create_pool(
            _pg_url(),
            min_size=2,
            max_size=10,
            command_timeout=30,
            statement_cache_size=0,   # Safe for pgBouncer environments
        )
        # Smoke-test the pool
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.info("postgres_pool_created", min=2, max=10)
    except Exception as exc:
        logger.warning(
            "postgres_pool_failed",
            error=str(exc),
            fallback="in_memory",
        )
        _pool = None

    return _pool


async def close_pool() -> None:
    """Close the shared pool.  Call during app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("postgres_pool_closed")
