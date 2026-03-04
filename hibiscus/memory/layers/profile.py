"""
User Profile Memory — Layer 3 (PostgreSQL)
==========================================
Structured user demographics and preferences.
Table: hibiscus_user_profiles
Encrypted at rest for PII fields (handled by the DB-level encryption and TLS
in transit; the application layer does not store raw PII beyond what is shown
in the schema below).

Why PostgreSQL?  Profile data is structured, relational, and mutated
incrementally (one field at a time).  It also needs to join with the portfolio
table in Phase 2 analytics queries.

Health conditions are stored as **categories** only ("diabetes", "hypertension")
— never as free-text verbatim data from the user.  This limits PII exposure.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from typing import Any, Dict, List, Optional

from hibiscus.config import settings
from hibiscus.memory.db import get_pool
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── In-memory fallback (when PostgreSQL is unavailable) ───────────────────────
_profile_store: Dict[str, Dict[str, Any]] = {}

# ── DDL ───────────────────────────────────────────────────────────────────────
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS hibiscus_user_profiles (
    user_id                     VARCHAR(255) PRIMARY KEY,
    age                         INTEGER,
    gender                      VARCHAR(10),
    city                        VARCHAR(100),
    city_tier                   INTEGER,
    state                       VARCHAR(100),
    occupation                  VARCHAR(100),
    income_band                 VARCHAR(50),
    family_structure            VARCHAR(100),
    num_dependents              INTEGER,
    smoker_status               BOOLEAN,
    risk_tolerance              VARCHAR(20),
    communication_preference    VARCHAR(20),
    language_preference         VARCHAR(20),
    health_conditions_categories TEXT[],
    created_at                  TIMESTAMP DEFAULT NOW(),
    updated_at                  TIMESTAMP DEFAULT NOW()
);
"""

# ── Allowed profile fields (whitelist to prevent SQL-injection via field names) ─
_ALLOWED_FIELDS = {
    "age",
    "gender",
    "city",
    "city_tier",
    "state",
    "occupation",
    "income_band",
    "family_structure",
    "num_dependents",
    "smoker_status",
    "risk_tolerance",
    "communication_preference",
    "language_preference",
    "health_conditions_categories",
}


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def init_profile_db() -> None:
    """Create table if it does not exist. Call at app startup."""
    pool = await get_pool()
    if pool is None:
        logger.warning("profile_db_init_skipped", reason="postgres_unavailable")
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)
        logger.info("profile_table_ready")
    except Exception as exc:
        logger.warning("profile_table_create_failed", error=str(exc))


async def close_profile_db() -> None:
    """No-op — pool lifecycle is managed by hibiscus.memory.db."""
    pass


# ── Public API ────────────────────────────────────────────────────────────────

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile from PostgreSQL.

    Returns:
        Profile dict if the user exists, None otherwise.
        Falls back to in-memory store when PostgreSQL is unavailable.
    """
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM hibiscus_user_profiles WHERE user_id = $1",
                    user_id,
                )
            if row is None:
                return None
            profile = dict(row)
            # asyncpg returns lists for TEXT[] — ensure it's always a list
            if profile.get("health_conditions_categories") is None:
                profile["health_conditions_categories"] = []
            return profile
        except Exception as exc:
            logger.warning("profile_get_failed", user_id=user_id, error=str(exc))

    # Fallback
    return _profile_store.get(user_id)


async def upsert_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
    """Create or fully replace a user profile.

    Args:
        user_id:      EAZR user identifier.
        profile_data: Dict with any subset of profile fields.

    Returns:
        True on success, False on failure.
    """
    # Sanitise: only keep known fields
    clean = {k: v for k, v in profile_data.items() if k in _ALLOWED_FIELDS}

    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                # Build dynamic upsert
                fields = list(clean.keys())
                if not fields:
                    return False

                col_list = ", ".join(fields)
                placeholder_list = ", ".join(f"${i+2}" for i in range(len(fields)))
                update_list = ", ".join(
                    f"{f} = EXCLUDED.{f}" for f in fields
                )
                sql = f"""
                    INSERT INTO hibiscus_user_profiles (user_id, {col_list}, updated_at)
                    VALUES ($1, {placeholder_list}, NOW())
                    ON CONFLICT (user_id) DO UPDATE
                    SET {update_list}, updated_at = NOW()
                """
                values = [user_id] + [clean[f] for f in fields]
                await conn.execute(sql, *values)

            logger.info(
                "profile_upserted",
                user_id=user_id,
                fields_updated=list(clean.keys()),
            )
            # Keep fallback in sync
            existing = _profile_store.get(user_id, {})
            existing.update(clean)
            existing["user_id"] = user_id
            _profile_store[user_id] = existing
            return True
        except Exception as exc:
            logger.warning("profile_upsert_failed", user_id=user_id, error=str(exc))

    # Fallback: in-memory only
    existing = _profile_store.get(user_id, {})
    existing.update(clean)
    existing["user_id"] = user_id
    existing["updated_at"] = time.time()
    _profile_store[user_id] = existing
    logger.info("profile_upserted_fallback", user_id=user_id, fields=list(clean.keys()))
    return False


async def update_profile_field(user_id: str, field: str, value: Any) -> bool:
    """Update a single profile field.

    Args:
        user_id: EAZR user identifier.
        field:   Column name (must be in _ALLOWED_FIELDS).
        value:   New value.

    Returns:
        True on success, False on failure or unknown field.
    """
    if field not in _ALLOWED_FIELDS:
        logger.warning("profile_field_rejected", field=field, reason="not_in_whitelist")
        return False

    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO hibiscus_user_profiles (user_id, {field}, updated_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (user_id) DO UPDATE
                    SET {field} = EXCLUDED.{field}, updated_at = NOW()
                    """,
                    user_id,
                    value,
                )
            logger.info(
                "profile_field_updated",
                user_id=user_id,
                field=field,
                # Audit log: log the field name but not the value (PII guard)
                value_type=type(value).__name__,
            )
            # Keep fallback in sync
            _profile_store.setdefault(user_id, {})
            _profile_store[user_id][field] = value
            _profile_store[user_id]["updated_at"] = time.time()
            return True
        except Exception as exc:
            logger.warning(
                "profile_field_update_failed",
                user_id=user_id,
                field=field,
                error=str(exc),
            )

    # Fallback
    _profile_store.setdefault(user_id, {})
    _profile_store[user_id][field] = value
    _profile_store[user_id]["updated_at"] = time.time()
    logger.info("profile_field_updated_fallback", user_id=user_id, field=field)
    return False


async def get_all_profiles(limit: int = 100) -> List[Dict[str, Any]]:
    """Return all profiles (admin / analytics use only).

    Args:
        limit: Maximum rows to return.
    """
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM hibiscus_user_profiles ORDER BY updated_at DESC LIMIT $1",
                    limit,
                )
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("profile_list_failed", error=str(exc))

    return list(_profile_store.values())[:limit]
