"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Outcome memory (L5) — PostgreSQL tracking of advice outcomes for self-improvement loop.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from hibiscus.config import settings
from hibiscus.memory.db import get_pool
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── In-memory fallback ────────────────────────────────────────────────────────
_outcome_store: Dict[int, Dict[str, Any]] = {}
_outcome_id_counter: int = 0

# ── DDL ───────────────────────────────────────────────────────────────────────
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS hibiscus_outcomes (
    id                  SERIAL PRIMARY KEY,
    user_id             VARCHAR(255) NOT NULL,
    session_id          VARCHAR(255),
    conversation_id     VARCHAR(255),
    advice_type         VARCHAR(50),
    advice_summary      TEXT,
    action_taken        VARCHAR(50),
    outcome             VARCHAR(50) DEFAULT 'pending',
    satisfaction        INTEGER,
    policy_type         VARCHAR(50),
    insurer             VARCHAR(100),
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outcomes_user_id
    ON hibiscus_outcomes (user_id);

CREATE INDEX IF NOT EXISTS idx_outcomes_advice_type
    ON hibiscus_outcomes (advice_type);

CREATE INDEX IF NOT EXISTS idx_outcomes_outcome
    ON hibiscus_outcomes (outcome);
"""

# ── Valid value sets (guard against arbitrary strings) ────────────────────────
_VALID_ADVICE_TYPES = {"recommend", "surrender", "calculate", "claim", "compare", "tax", "general"}
_VALID_ACTIONS = {"purchased", "surrendered", "filed_claim", "ignored", "pending", "converted", "researching"}
_VALID_OUTCOMES = {"successful", "failed", "pending", "unknown", "partial"}


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def init_outcome_db() -> None:
    """Create table + indexes if they do not exist. Call at app startup."""
    pool = await get_pool()
    if pool is None:
        logger.warning("outcome_db_init_skipped", reason="postgres_unavailable")
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)
        logger.info("outcome_table_ready")
    except Exception as exc:
        logger.warning("outcome_table_create_failed", error=str(exc))


# ── Public API ────────────────────────────────────────────────────────────────

async def record_outcome(
    user_id: str,
    session_id: str,
    advice_type: str,
    advice_summary: str,
    conversation_id: Optional[str] = None,
    policy_type: Optional[str] = None,
    insurer: Optional[str] = None,
) -> Optional[int]:
    """Record that advice was given.  Outcome starts as 'pending'.

    Call this immediately after the agent delivers a recommendation or
    significant guidance so we have a record regardless of follow-up.

    Args:
        user_id:         EAZR user identifier.
        session_id:      Session in which advice was given.
        advice_type:     Category: recommend / surrender / calculate / claim / compare / tax.
        advice_summary:  1–3 sentence plain-text summary of the advice.
        conversation_id: Optional conversation ID for finer tracing.
        policy_type:     Policy type the advice related to.
        insurer:         Insurer the advice related to.

    Returns:
        The new outcome row ID, or None on failure.
    """
    if advice_type not in _VALID_ADVICE_TYPES:
        advice_type = "general"

    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row_id = await conn.fetchval(
                    """
                    INSERT INTO hibiscus_outcomes
                        (user_id, session_id, conversation_id, advice_type,
                         advice_summary, outcome, policy_type, insurer)
                    VALUES ($1, $2, $3, $4, $5, 'pending', $6, $7)
                    RETURNING id
                    """,
                    user_id,
                    session_id,
                    conversation_id,
                    advice_type,
                    advice_summary[:1000],   # Guard against huge texts
                    policy_type,
                    insurer,
                )
            logger.info(
                "outcome_recorded",
                user_id=user_id,
                row_id=row_id,
                advice_type=advice_type,
            )
            # Keep fallback in sync
            _outcome_store[row_id] = {
                "id": row_id,
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "advice_type": advice_type,
                "advice_summary": advice_summary,
                "outcome": "pending",
                "action_taken": None,
                "satisfaction": None,
                "policy_type": policy_type,
                "insurer": insurer,
                "created_at": time.time(),
                "updated_at": time.time(),
            }
            return row_id
        except Exception as exc:
            logger.warning("outcome_record_failed", user_id=user_id, error=str(exc))

    # Fallback
    global _outcome_id_counter
    _outcome_id_counter += 1
    fake_id = _outcome_id_counter
    _outcome_store[fake_id] = {
        "id": fake_id,
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "advice_type": advice_type,
        "advice_summary": advice_summary,
        "outcome": "pending",
        "action_taken": None,
        "satisfaction": None,
        "policy_type": policy_type,
        "insurer": insurer,
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    logger.info("outcome_recorded_fallback", user_id=user_id, fake_id=fake_id)
    return None


async def update_outcome(
    outcome_id: int,
    action_taken: Optional[str] = None,
    outcome: Optional[str] = None,
    satisfaction: Optional[int] = None,
    notes: Optional[str] = None,
) -> bool:
    """Update an existing outcome record when user reports what happened.

    Args:
        outcome_id:   Row ID returned by record_outcome().
        action_taken: What the user actually did (purchased, ignored, etc.).
        outcome:      Result: successful / failed / partial / pending / unknown.
        satisfaction: User satisfaction 1–5 (from in-app feedback widget).
        notes:        Free-text notes (from feedback or support agent).

    Returns:
        True if the row was found and updated, False otherwise.
    """
    # Sanitise
    if action_taken and action_taken not in _VALID_ACTIONS:
        logger.warning("outcome_invalid_action", action_taken=action_taken)
        action_taken = None
    if outcome and outcome not in _VALID_OUTCOMES:
        logger.warning("outcome_invalid_outcome", outcome=outcome)
        outcome = None
    if satisfaction is not None:
        satisfaction = max(1, min(5, int(satisfaction)))   # Clamp 1–5

    # Build SET clause dynamically (only update provided fields)
    updates: Dict[str, Any] = {}
    if action_taken is not None:
        updates["action_taken"] = action_taken
    if outcome is not None:
        updates["outcome"] = outcome
    if satisfaction is not None:
        updates["satisfaction"] = satisfaction
    if notes is not None:
        updates["notes"] = notes[:500]

    if not updates:
        return False

    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                set_clauses = ", ".join(
                    f"{col} = ${i + 2}" for i, col in enumerate(updates.keys())
                )
                sql = f"""
                    UPDATE hibiscus_outcomes
                    SET {set_clauses}, updated_at = NOW()
                    WHERE id = $1
                """
                values = [outcome_id] + list(updates.values())
                result = await conn.execute(sql, *values)
            updated = result != "UPDATE 0"
            logger.info(
                "outcome_updated",
                outcome_id=outcome_id,
                fields=list(updates.keys()),
                updated=updated,
            )
            if outcome_id in _outcome_store:
                _outcome_store[outcome_id].update(updates)
            return updated
        except Exception as exc:
            logger.warning("outcome_update_failed", outcome_id=outcome_id, error=str(exc))

    # Fallback
    if outcome_id in _outcome_store:
        _outcome_store[outcome_id].update(updates)
        _outcome_store[outcome_id]["updated_at"] = time.time()
        return True
    return False


async def get_user_outcomes(
    user_id: str,
    advice_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve past outcome records for a user.

    Args:
        user_id:     EAZR user identifier.
        advice_type: Optional filter by advice category.
        limit:       Maximum rows to return.

    Returns:
        List of outcome dicts, most-recent first.
    """
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                if advice_type:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM hibiscus_outcomes
                        WHERE user_id = $1 AND advice_type = $2
                        ORDER BY created_at DESC LIMIT $3
                        """,
                        user_id, advice_type, limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM hibiscus_outcomes
                        WHERE user_id = $1
                        ORDER BY created_at DESC LIMIT $2
                        """,
                        user_id, limit,
                    )
            return [_row_to_dict(r) for r in rows]
        except Exception as exc:
            logger.warning("outcome_get_failed", user_id=user_id, error=str(exc))

    # Fallback
    records = [
        v for v in _outcome_store.values()
        if v["user_id"] == user_id
        and (advice_type is None or v["advice_type"] == advice_type)
    ]
    records.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return records[:limit]


async def get_outcome_stats() -> Dict[str, Any]:
    """Return aggregate statistics across all outcomes (for system improvement).

    Used by:
      - HibiscusBench evaluation runner
      - Phase 4 self-improvement loop
      - Admin dashboard

    Returns:
        {
            total_outcomes:          int
            pending_count:           int
            successful_count:        int
            failed_count:            int
            avg_satisfaction:        float | None
            by_advice_type:          {advice_type: {total, successful, avg_satisfaction}}
            by_insurer:              {insurer: {total, successful}}
        }
    """
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                totals = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*)                                    AS total_outcomes,
                        COUNT(*) FILTER (WHERE outcome = 'pending') AS pending_count,
                        COUNT(*) FILTER (WHERE outcome = 'successful') AS successful_count,
                        COUNT(*) FILTER (WHERE outcome = 'failed')   AS failed_count,
                        AVG(satisfaction)::FLOAT                    AS avg_satisfaction
                    FROM hibiscus_outcomes
                    """
                )
                by_type = await conn.fetch(
                    """
                    SELECT
                        advice_type,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE outcome = 'successful') AS successful,
                        AVG(satisfaction)::FLOAT AS avg_satisfaction
                    FROM hibiscus_outcomes
                    GROUP BY advice_type
                    """
                )
                by_insurer = await conn.fetch(
                    """
                    SELECT
                        insurer,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE outcome = 'successful') AS successful
                    FROM hibiscus_outcomes
                    WHERE insurer IS NOT NULL
                    GROUP BY insurer
                    ORDER BY total DESC
                    LIMIT 20
                    """
                )

            stats = dict(totals)
            stats["by_advice_type"] = {
                r["advice_type"]: {
                    "total": r["total"],
                    "successful": r["successful"],
                    "avg_satisfaction": round(r["avg_satisfaction"] or 0, 2),
                }
                for r in by_type
            }
            stats["by_insurer"] = {
                r["insurer"]: {"total": r["total"], "successful": r["successful"]}
                for r in by_insurer
                if r["insurer"]
            }
            return stats
        except Exception as exc:
            logger.warning("outcome_stats_failed", error=str(exc))

    # Fallback: compute from in-memory store
    records = list(_outcome_store.values())
    sats = [r["satisfaction"] for r in records if r.get("satisfaction")]
    return {
        "total_outcomes": len(records),
        "pending_count": sum(1 for r in records if r.get("outcome") == "pending"),
        "successful_count": sum(1 for r in records if r.get("outcome") == "successful"),
        "failed_count": sum(1 for r in records if r.get("outcome") == "failed"),
        "avg_satisfaction": round(sum(sats) / len(sats), 2) if sats else None,
        "by_advice_type": {},
        "by_insurer": {},
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_dict(row: Any) -> Dict[str, Any]:
    """Convert asyncpg Record to plain dict, normalising datetime fields."""
    d = dict(row)
    for key in ("created_at", "updated_at"):
        if isinstance(d.get(key), datetime):
            d[key] = d[key].isoformat()
    return d
