"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Neo4j client — async graph queries with connection pooling and retry logic.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, exceptions as neo4j_exc

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.client")

# ── Simple in-memory LRU cache ────────────────────────────────────────────────

class _LRUCache:
    """
    Fixed-size LRU cache with per-entry TTL.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self, maxsize: int = 256, ttl_seconds: int = 300):
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._store:
                return None
            value, expiry = self._store[key]
            if time.monotonic() > expiry:
                del self._store[key]
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, time.monotonic() + self._ttl)
            # Evict oldest if over capacity
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    def _make_key(self, cypher: str, params: Dict[str, Any]) -> str:
        """Deterministic cache key from query + sorted params."""
        import hashlib, json
        raw = cypher + json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()


# ── Neo4j Async Client ────────────────────────────────────────────────────────

class Neo4jClient:
    """
    Async Neo4j client with:
    - Connection pooling via the official neo4j async driver
    - LRU cache (5-minute TTL, 256 entries) for repeated read queries
    - Graceful degradation — returns [] instead of raising on connectivity issues
    - Structured logging on every query (query_name, latency_ms, result_count)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        cache_ttl: int = 300,
        cache_maxsize: int = 256,
    ):
        self._uri = uri or settings.neo4j_uri
        self._user = user or settings.neo4j_user
        self._password = password or settings.neo4j_password
        self._driver: Optional[AsyncDriver] = None
        self._cache = _LRUCache(maxsize=cache_maxsize, ttl_seconds=cache_ttl)
        self._connected = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Open the async driver and verify connectivity.
        On failure, logs a warning and sets _connected=False so callers
        receive empty results rather than exceptions.
        """
        if self._connected and self._driver is not None:
            return

        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
                max_connection_pool_size=50,
                connection_timeout=10.0,
                max_transaction_retry_time=30.0,
            )
            # Verify the connection
            await self._driver.verify_connectivity()
            self._connected = True
            logger.info(
                "neo4j_connected",
                uri=self._uri,
                user=self._user,
            )
        except (
            neo4j_exc.ServiceUnavailable,
            neo4j_exc.AuthError,
            neo4j_exc.ConfigurationError,
            Exception,
        ) as exc:
            self._connected = False
            self._driver = None
            logger.warning(
                "neo4j_unavailable",
                uri=self._uri,
                error=str(exc),
                degraded_mode=True,
            )

    async def close(self) -> None:
        """Close the driver and release all connections."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
        self._connected = False
        await self._cache.clear()
        logger.info("neo4j_closed")

    # ── Core Query Execution ──────────────────────────────────────────────────

    async def query(
        self,
        cypher: str,
        params: Optional[Dict[str, Any]] = None,
        query_name: str = "unnamed",
        use_cache: bool = True,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as a list of dicts.

        Args:
            cypher:      Cypher query string
            params:      Query parameters
            query_name:  Human-readable name for logging (e.g. "get_insurer_by_name")
            use_cache:   Whether to use the LRU cache (disable for writes)
            database:    Neo4j database name (defaults to driver default)

        Returns:
            List of record dicts, or [] on error / unavailable.
        """
        if params is None:
            params = {}

        if not self._connected or self._driver is None:
            # Attempt reconnect once
            await self.connect()

        if not self._connected or self._driver is None:
            logger.warning(
                "neo4j_query_skipped",
                query_name=query_name,
                reason="driver_unavailable",
            )
            return []

        # Cache check (reads only)
        cache_key: Optional[str] = None
        if use_cache:
            cache_key = self._cache._make_key(cypher, params)
            cached = await self._cache.get(cache_key)
            if cached is not None:
                logger.info(
                    "neo4j_cache_hit",
                    query_name=query_name,
                    result_count=len(cached),
                )
                return cached

        t_start = time.monotonic()
        results: List[Dict[str, Any]] = []

        try:
            async with self._driver.session(database=database) as session:
                cursor = await session.run(cypher, params)
                records = await cursor.data()
                results = [dict(r) for r in records]

            latency_ms = int((time.monotonic() - t_start) * 1000)
            logger.info(
                "neo4j_query",
                query_name=query_name,
                latency_ms=latency_ms,
                result_count=len(results),
            )

            # Populate cache
            if use_cache and cache_key is not None:
                await self._cache.set(cache_key, results)

        except neo4j_exc.ServiceUnavailable as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            self._connected = False
            logger.warning(
                "neo4j_service_unavailable",
                query_name=query_name,
                latency_ms=latency_ms,
                error=str(exc),
            )
        except neo4j_exc.CypherSyntaxError as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            logger.error(
                "neo4j_cypher_syntax_error",
                query_name=query_name,
                latency_ms=latency_ms,
                error=str(exc),
                cypher_snippet=cypher[:200],
            )
        except Exception as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            logger.error(
                "neo4j_query_error",
                query_name=query_name,
                latency_ms=latency_ms,
                error=str(exc),
            )

        return results

    async def query_one(
        self,
        cypher: str,
        params: Optional[Dict[str, Any]] = None,
        query_name: str = "unnamed_one",
        use_cache: bool = True,
        database: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Convenience method — returns the first result dict or None.
        """
        results = await self.query(
            cypher,
            params=params,
            query_name=query_name,
            use_cache=use_cache,
            database=database,
        )
        return results[0] if results else None

    async def execute_write(
        self,
        cypher: str,
        params: Optional[Dict[str, Any]] = None,
        query_name: str = "write",
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a write query (MERGE, CREATE, SET, DELETE).
        Bypasses cache automatically.
        """
        return await self.query(
            cypher,
            params=params,
            query_name=query_name,
            use_cache=False,
            database=database,
        )

    async def execute_batch(
        self,
        cypher: str,
        param_list: List[Dict[str, Any]],
        query_name: str = "batch_write",
        database: Optional[str] = None,
    ) -> int:
        """
        Execute the same Cypher for each item in param_list.
        Returns the number of successful executions.

        Useful for seeding: pass a list of dicts and a parameterised MERGE query.
        """
        if not self._connected or self._driver is None:
            await self.connect()

        if not self._connected or self._driver is None:
            logger.warning(
                "neo4j_batch_skipped",
                query_name=query_name,
                reason="driver_unavailable",
                items=len(param_list),
            )
            return 0

        t_start = time.monotonic()
        success_count = 0

        try:
            async with self._driver.session(database=database) as session:
                async def _run_batch(tx: Any) -> None:
                    nonlocal success_count
                    for p in param_list:
                        await tx.run(cypher, p)
                        success_count += 1

                await session.execute_write(_run_batch)

            latency_ms = int((time.monotonic() - t_start) * 1000)
            logger.info(
                "neo4j_batch_complete",
                query_name=query_name,
                latency_ms=latency_ms,
                items_attempted=len(param_list),
                items_succeeded=success_count,
            )
        except Exception as exc:
            latency_ms = int((time.monotonic() - t_start) * 1000)
            logger.error(
                "neo4j_batch_error",
                query_name=query_name,
                latency_ms=latency_ms,
                items_attempted=len(param_list),
                items_succeeded=success_count,
                error=str(exc),
            )

        return success_count

    # ── Health Check ──────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        """
        Returns True if Neo4j is reachable, False otherwise.
        Safe to call at any time.
        """
        result = await self.query_one(
            "RETURN 1 AS alive",
            query_name="ping",
            use_cache=False,
        )
        return result is not None and result.get("alive") == 1

    @property
    def is_connected(self) -> bool:
        """Last-known connection state."""
        return self._connected


# ── Module-level singleton ─────────────────────────────────────────────────────

kg_client = Neo4jClient()


async def init_kg() -> None:
    """
    Lifecycle hook — call at application startup.
    Connects the module-level kg_client singleton.
    """
    await kg_client.connect()
    if kg_client.is_connected:
        logger.info("kg_init_ok")
    else:
        logger.warning(
            "kg_init_degraded",
            message="Neo4j unavailable — Knowledge Graph queries will return empty results",
        )


async def close_kg() -> None:
    """
    Lifecycle hook — call at application shutdown.
    Cleanly closes the module-level kg_client singleton.
    """
    await kg_client.close()
    logger.info("kg_closed")
