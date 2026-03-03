"""
Policy Portfolio Memory — Layer 3b (PostgreSQL)
================================================
Stores all known user policies across all product lines.
Table: hibiscus_policy_portfolio
Updated after every policy analysis so coverage picture is always current.

Why a separate table from profiles?  A user can have many policies (1:N).
The portfolio is the source of truth for:
  - Coverage gap calculations
  - Renewal reminders
  - Total premium load
  - IPF / SVF eligibility assessment
"""
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from hibiscus.config import settings
from hibiscus.memory.db import get_pool
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── In-memory fallback ────────────────────────────────────────────────────────
_portfolio_store: Dict[str, List[Dict[str, Any]]] = {}   # user_id → list of policies

# ── DDL ───────────────────────────────────────────────────────────────────────
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS hibiscus_policy_portfolio (
    id                  SERIAL PRIMARY KEY,
    user_id             VARCHAR(255) NOT NULL,
    doc_id              VARCHAR(255),
    policy_type         VARCHAR(50),
    insurer             VARCHAR(100),
    product_name        VARCHAR(200),
    sum_insured         BIGINT,
    annual_premium      INTEGER,
    policy_start_date   DATE,
    policy_end_date     DATE,
    payment_status      VARCHAR(20),
    riders              TEXT[],
    eazr_score          FLOAT,
    analysis_date       TIMESTAMP,
    is_active           BOOLEAN DEFAULT TRUE,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_user_id
    ON hibiscus_policy_portfolio (user_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_user_active
    ON hibiscus_policy_portfolio (user_id, is_active);

CREATE INDEX IF NOT EXISTS idx_portfolio_doc_id
    ON hibiscus_policy_portfolio (doc_id)
    WHERE doc_id IS NOT NULL;
"""

# ── Allowed update fields (whitelist prevents SQL injection via field names) ───
_ALLOWED_UPDATE_FIELDS = {
    "policy_type", "insurer", "product_name", "sum_insured", "annual_premium",
    "policy_start_date", "policy_end_date", "payment_status", "riders",
    "eazr_score", "analysis_date", "is_active", "notes",
}

# ── Coverage gap thresholds (Indian market benchmarks) ────────────────────────
_HEALTH_MIN_INR = 500_000       # ₹5 lakh
_LIFE_COVER_MULTIPLIER = 10     # 10× annual income is the thumb-rule


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def init_portfolio_db() -> None:
    """Create table + indexes if they do not exist. Call at app startup."""
    pool = await get_pool()
    if pool is None:
        logger.warning("portfolio_db_init_skipped", reason="postgres_unavailable")
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)
        logger.info("portfolio_table_ready")
    except Exception as exc:
        logger.warning("portfolio_table_create_failed", error=str(exc))


# ── Public API ────────────────────────────────────────────────────────────────

async def get_user_portfolio(user_id: str) -> List[Dict[str, Any]]:
    """Return all active policies for a user.

    Args:
        user_id: EAZR user identifier.

    Returns:
        List of policy dicts (may be empty).  Falls back to in-memory store.
    """
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM hibiscus_policy_portfolio
                    WHERE user_id = $1 AND is_active = TRUE
                    ORDER BY created_at DESC
                    """,
                    user_id,
                )
            policies = []
            for row in rows:
                p = dict(row)
                # Normalise date/datetime fields to strings for JSON serialisation
                for date_field in ("policy_start_date", "policy_end_date", "analysis_date", "created_at", "updated_at"):
                    if isinstance(p.get(date_field), (date, datetime)):
                        p[date_field] = p[date_field].isoformat()
                if p.get("riders") is None:
                    p["riders"] = []
                policies.append(p)
            return policies
        except Exception as exc:
            logger.warning("portfolio_get_failed", user_id=user_id, error=str(exc))

    # Fallback
    return _portfolio_store.get(user_id, [])


async def add_policy(user_id: str, policy_data: Dict[str, Any]) -> Optional[int]:
    """Insert a new policy into the portfolio.

    Args:
        user_id:     EAZR user identifier.
        policy_data: Policy fields (doc_id, policy_type, insurer, etc.).

    Returns:
        The new row ID (int), or None on failure.
    """
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row_id = await conn.fetchval(
                    """
                    INSERT INTO hibiscus_policy_portfolio
                        (user_id, doc_id, policy_type, insurer, product_name,
                         sum_insured, annual_premium, policy_start_date, policy_end_date,
                         payment_status, riders, eazr_score, analysis_date, is_active, notes)
                    VALUES
                        ($1, $2, $3, $4, $5,
                         $6, $7, $8, $9,
                         $10, $11, $12, $13, $14, $15)
                    RETURNING id
                    """,
                    user_id,
                    policy_data.get("doc_id"),
                    policy_data.get("policy_type"),
                    policy_data.get("insurer"),
                    policy_data.get("product_name"),
                    policy_data.get("sum_insured"),
                    policy_data.get("annual_premium"),
                    _to_date(policy_data.get("policy_start_date")),
                    _to_date(policy_data.get("policy_end_date")),
                    policy_data.get("payment_status", "active"),
                    policy_data.get("riders") or [],
                    policy_data.get("eazr_score"),
                    _to_datetime(policy_data.get("analysis_date")),
                    policy_data.get("is_active", True),
                    policy_data.get("notes"),
                )
            logger.info(
                "portfolio_policy_added",
                user_id=user_id,
                row_id=row_id,
                policy_type=policy_data.get("policy_type"),
                insurer=policy_data.get("insurer"),
            )
            # Keep fallback in sync
            policy_data["id"] = row_id
            policy_data["user_id"] = user_id
            _portfolio_store.setdefault(user_id, []).append(policy_data)
            return row_id
        except Exception as exc:
            logger.warning("portfolio_add_failed", user_id=user_id, error=str(exc))

    # Fallback
    policy_data["user_id"] = user_id
    policy_data["id"] = int(time.time() * 1000)   # Pseudo-ID
    _portfolio_store.setdefault(user_id, []).append(policy_data)
    logger.info("portfolio_policy_added_fallback", user_id=user_id)
    return None


async def update_policy(
    user_id: str,
    doc_id: str,
    updates: Dict[str, Any],
) -> bool:
    """Update fields on an existing policy identified by doc_id.

    Args:
        user_id:  EAZR user identifier.
        doc_id:   Document ID of the policy to update.
        updates:  Dict of {field: value} to update.

    Returns:
        True if a row was updated, False otherwise.
    """
    # Sanitise
    clean = {k: v for k, v in updates.items() if k in _ALLOWED_UPDATE_FIELDS}
    if not clean:
        return False

    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                set_clauses = ", ".join(
                    f"{field} = ${i + 3}" for i, field in enumerate(clean.keys())
                )
                sql = f"""
                    UPDATE hibiscus_policy_portfolio
                    SET {set_clauses}, updated_at = NOW()
                    WHERE user_id = $1 AND doc_id = $2
                """
                values = [user_id, doc_id] + list(clean.values())
                result = await conn.execute(sql, *values)
            updated = result != "UPDATE 0"
            logger.info(
                "portfolio_policy_updated",
                user_id=user_id,
                doc_id=doc_id,
                fields=list(clean.keys()),
                updated=updated,
            )
            # Keep fallback in sync
            for p in _portfolio_store.get(user_id, []):
                if p.get("doc_id") == doc_id:
                    p.update(clean)
            return updated
        except Exception as exc:
            logger.warning("portfolio_update_failed", user_id=user_id, doc_id=doc_id, error=str(exc))

    # Fallback
    for p in _portfolio_store.get(user_id, []):
        if p.get("doc_id") == doc_id:
            p.update(clean)
            return True
    return False


async def get_portfolio_summary(user_id: str) -> Dict[str, Any]:
    """Aggregate coverage statistics for a user.

    Returns a dict:
        {
            total_life_cover:    int   (₹)
            total_health_cover:  int   (₹)
            total_premium:       int   (₹/year)
            policy_count:        int
            active_policy_count: int
            gaps:                list[str]  — human-readable gap descriptions
        }
    """
    policies = await get_user_portfolio(user_id)

    total_life = 0
    total_health = 0
    total_premium = 0
    policy_types: set = set()

    for p in policies:
        ptype = (p.get("policy_type") or "").lower()
        si = int(p.get("sum_insured") or 0)
        premium = int(p.get("annual_premium") or 0)
        total_premium += premium
        policy_types.add(ptype)

        if ptype in ("life_term", "life_endowment", "life_ulip", "life"):
            total_life += si
        elif ptype in ("health", "mediclaim"):
            total_health += si

    gaps: List[str] = []
    if not any(t in policy_types for t in ("health", "mediclaim")):
        gaps.append("No health / mediclaim policy detected")
    elif total_health < _HEALTH_MIN_INR:
        gaps.append(
            f"Health cover ₹{total_health:,} is below recommended ₹{_HEALTH_MIN_INR:,}"
        )

    if not any(t in policy_types for t in ("life_term", "life", "life_endowment", "life_ulip")):
        gaps.append("No life insurance policy detected")

    if "pa" not in policy_types:
        gaps.append("No personal accident (PA) cover detected")

    summary = {
        "total_life_cover": total_life,
        "total_health_cover": total_health,
        "total_premium": total_premium,
        "policy_count": len(policies),
        "active_policy_count": sum(1 for p in policies if p.get("is_active", True)),
        "policy_types": list(policy_types),
        "gaps": gaps,
    }
    logger.info("portfolio_summary_built", user_id=user_id, **{k: v for k, v in summary.items() if k != "gaps"})
    return summary


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_date(value: Any) -> Optional[date]:
    """Coerce string / date / None to date."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _to_datetime(value: Any) -> Optional[datetime]:
    """Coerce string / datetime / None to datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None
