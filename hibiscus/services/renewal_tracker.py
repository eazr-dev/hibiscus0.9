"""
Renewal/Lapse Tracker
=====================
Checks user's policy portfolio for upcoming renewals and potential lapses.
Generates proactive alerts to inject into conversation context.

Alert levels:
- LAPSED: past due (red)
- URGENT: 1-7 days (orange)
- DUE_SOON: 8-30 days (yellow)

Data sources:
1. Policy portfolio (PostgreSQL via portfolio layer)
2. Document memory extractions (MongoDB via document layer)
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from hibiscus.memory.layers.document import get_latest_document
from hibiscus.memory.layers.portfolio import get_expiring_policies
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_URGENT_THRESHOLD = 7    # days — 0-7 → URGENT
_DUE_SOON_THRESHOLD = 30  # days — 8-30 → DUE_SOON

# Date formats accepted when parsing extraction fields
_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d")


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class RenewalAlert:
    """A single renewal or lapse alert for one policy."""

    policy_type: str          # e.g. "Health Insurance"
    insurer: str              # e.g. "Star Health"
    due_date: str             # DD/MM/YYYY format (Indian standard)
    days_until_due: int       # negative if already lapsed
    level: str                # "LAPSED" | "URGENT" | "DUE_SOON"
    premium_amount: Optional[float]
    message: str              # Human-readable alert in Indian English
    policy_id: Optional[str] = field(default=None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(value: Any) -> Optional[date]:
    """Try to parse *value* into a :class:`datetime.date`.

    Accepts ``date``, ``datetime``, ``str`` (multiple formats), or ``None``.
    Returns ``None`` if the value cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _format_date_indian(d: date) -> str:
    """Return a date formatted as DD/MM/YYYY (Indian convention)."""
    return d.strftime("%d/%m/%Y")


def _classify_level(days_until_due: int) -> Optional[str]:
    """Return the alert level string for the given days offset.

    Returns ``None`` if the date is more than 30 days away (no alert needed).
    """
    if days_until_due < 0:
        return "LAPSED"
    if days_until_due <= _URGENT_THRESHOLD:
        return "URGENT"
    if days_until_due <= _DUE_SOON_THRESHOLD:
        return "DUE_SOON"
    return None  # More than 30 days ahead — skip


def _build_message(level: str, policy_type: str, insurer: str, due_date: str, days_until_due: int) -> str:
    """Compose the human-readable alert message for a given level."""
    if level == "LAPSED":
        return (
            f"Your {policy_type} with {insurer} may have lapsed on {due_date}. "
            f"Please check your policy status immediately."
        )
    if level == "URGENT":
        return (
            f"Your {policy_type} with {insurer} premium is due in "
            f"{days_until_due} day(s) on {due_date}."
        )
    # DUE_SOON
    return (
        f"Reminder: Your {policy_type} with {insurer} renewal is due on "
        f"{due_date} ({days_until_due} days)."
    )


def _make_dedup_key(policy_type: str, insurer: str) -> str:
    """Normalised key used to de-duplicate alerts from different sources."""
    return f"{policy_type.strip().lower()}|{insurer.strip().lower()}"


# ── Main class ────────────────────────────────────────────────────────────────

class RenewalTracker:
    """Checks user's policy portfolio for upcoming renewals and lapses.

    Designed to be instantiated once (e.g. at module level or as a singleton)
    and called with different ``user_id`` values per request.  All I/O is
    async and non-blocking.

    Usage::

        tracker = RenewalTracker()
        context_str = await tracker.get_renewal_context(user_id)
    """

    # ── Public API ────────────────────────────────────────────────────────────

    async def check_renewals(self, user_id: str) -> List[RenewalAlert]:
        """Return all relevant renewal/lapse alerts for *user_id*.

        Pulls from two data sources:
        1. PostgreSQL portfolio layer (``get_expiring_policies``).
        2. MongoDB document memory — latest uploaded policy extraction
           (``next_premium_due_date`` / ``policy_expiry_date``).

        Results from both sources are merged, de-duplicated by
        (policy_type, insurer), and sorted: LAPSED first, then by
        ``days_until_due`` ascending.

        Args:
            user_id: EAZR user identifier.

        Returns:
            Sorted list of :class:`RenewalAlert`.  Empty list if no alerts
            are within the 30-day window.
        """
        today = date.today()
        alerts: Dict[str, RenewalAlert] = {}   # dedup_key → alert

        # ── Source 1: portfolio layer (PostgreSQL) ────────────────────────────
        try:
            portfolio_policies = await get_expiring_policies(user_id, days_ahead=_DUE_SOON_THRESHOLD)
        except Exception as exc:
            logger.warning(
                "renewal_tracker_portfolio_fetch_failed",
                user_id=user_id,
                error=str(exc),
            )
            portfolio_policies = []

        for policy in portfolio_policies:
            due_date_obj = _parse_date(policy.get("due_date"))
            if due_date_obj is None:
                continue

            days_until_due = (due_date_obj - today).days
            level = _classify_level(days_until_due)
            if level is None:
                continue

            policy_type = policy.get("policy_type") or "Insurance Policy"
            insurer = policy.get("insurer") or "Unknown Insurer"
            due_date_str = _format_date_indian(due_date_obj)
            dedup_key = _make_dedup_key(policy_type, insurer)

            alert = RenewalAlert(
                policy_type=policy_type,
                insurer=insurer,
                due_date=due_date_str,
                days_until_due=days_until_due,
                level=level,
                premium_amount=policy.get("premium_amount"),
                message=_build_message(level, policy_type, insurer, due_date_str, days_until_due),
                policy_id=policy.get("policy_id"),
            )
            # Keep the alert with the most urgent level if duplicated
            if dedup_key not in alerts or _level_priority(level) > _level_priority(alerts[dedup_key].level):
                alerts[dedup_key] = alert

        logger.info(
            "renewal_tracker_portfolio_source",
            user_id=user_id,
            policies_checked=len(portfolio_policies),
            alerts_so_far=len(alerts),
        )

        # ── Source 2: document memory (MongoDB) ───────────────────────────────
        try:
            latest_doc = await get_latest_document(user_id)
        except Exception as exc:
            logger.warning(
                "renewal_tracker_document_fetch_failed",
                user_id=user_id,
                error=str(exc),
            )
            latest_doc = None

        if latest_doc:
            extraction: Dict[str, Any] = latest_doc.get("extraction") or {}
            doc_policy_type = extraction.get("policy_type") or "Insurance Policy"
            doc_insurer = extraction.get("insurer_name") or extraction.get("insurer") or "Unknown Insurer"

            # Check both date fields from extraction
            for date_field in ("next_premium_due_date", "policy_expiry_date"):
                raw_date = extraction.get(date_field)
                if not raw_date:
                    continue

                due_date_obj = _parse_date(raw_date)
                if due_date_obj is None:
                    logger.warning(
                        "renewal_tracker_unparseable_date",
                        user_id=user_id,
                        date_field=date_field,
                        raw_value=str(raw_date)[:50],
                    )
                    continue

                days_until_due = (due_date_obj - today).days
                level = _classify_level(days_until_due)
                if level is None:
                    continue

                due_date_str = _format_date_indian(due_date_obj)
                dedup_key = _make_dedup_key(doc_policy_type, doc_insurer)

                alert = RenewalAlert(
                    policy_type=doc_policy_type,
                    insurer=doc_insurer,
                    due_date=due_date_str,
                    days_until_due=days_until_due,
                    level=level,
                    premium_amount=extraction.get("annual_premium") or extraction.get("premium_amount"),
                    message=_build_message(level, doc_policy_type, doc_insurer, due_date_str, days_until_due),
                    policy_id=latest_doc.get("doc_id"),
                )

                if dedup_key not in alerts or _level_priority(level) > _level_priority(alerts[dedup_key].level):
                    alerts[dedup_key] = alert

            logger.info(
                "renewal_tracker_document_source",
                user_id=user_id,
                doc_id=latest_doc.get("doc_id"),
                alerts_after_merge=len(alerts),
            )

        # ── Sort: LAPSED first, then by days_until_due ascending ─────────────
        sorted_alerts = sorted(
            alerts.values(),
            key=lambda a: (_level_sort_key(a.level), a.days_until_due),
        )

        logger.info(
            "renewal_tracker_check_complete",
            user_id=user_id,
            total_alerts=len(sorted_alerts),
            levels=[a.level for a in sorted_alerts],
        )
        return sorted_alerts

    async def format_alerts_for_context(self, alerts: List[RenewalAlert]) -> str:
        """Format a list of alerts as a context string for system prompt injection.

        The string is designed to be prepended to the system prompt so the LLM
        is aware of upcoming renewals and can proactively mention them to the user.

        Args:
            alerts: List produced by :meth:`check_renewals`.

        Returns:
            Formatted string, or ``""`` if *alerts* is empty.
        """
        if not alerts:
            return ""

        lines: List[str] = [
            "RENEWAL ALERTS (proactively mention these to the user where relevant):",
        ]
        for alert in alerts:
            prefix = {
                "LAPSED": "[LAPSED]",
                "URGENT": "[URGENT]",
                "DUE_SOON": "[DUE SOON]",
            }.get(alert.level, "[ALERT]")

            premium_str = ""
            if alert.premium_amount:
                try:
                    premium_str = f" | Premium: {int(float(alert.premium_amount)):,}"
                except (ValueError, TypeError):
                    premium_str = f" | Premium: {alert.premium_amount}"

            lines.append(
                f"  {prefix} {alert.policy_type} — {alert.insurer}"
                f" — Due: {alert.due_date}{premium_str}"
            )
            lines.append(f"    {alert.message}")

        return "\n".join(lines)

    async def get_renewal_context(self, user_id: str) -> str:
        """Convenience method: check renewals then format as context string.

        This is the primary entry point for injecting renewal context into
        the Hibiscus orchestration pipeline.

        Args:
            user_id: EAZR user identifier.

        Returns:
            Formatted context string, or ``""`` if no alerts are pending.
        """
        try:
            alerts = await self.check_renewals(user_id)
            return await self.format_alerts_for_context(alerts)
        except Exception as exc:
            logger.warning(
                "renewal_tracker_get_context_failed",
                user_id=user_id,
                error=str(exc),
            )
            return ""


# ── Level utilities ───────────────────────────────────────────────────────────

def _level_priority(level: str) -> int:
    """Higher number = higher urgency (used when de-duplicating)."""
    return {"LAPSED": 3, "URGENT": 2, "DUE_SOON": 1}.get(level, 0)


def _level_sort_key(level: str) -> int:
    """Lower number = appears first in sorted output (LAPSED first)."""
    return {"LAPSED": 0, "URGENT": 1, "DUE_SOON": 2}.get(level, 3)


# ── Module-level singleton ────────────────────────────────────────────────────

#: Ready-to-use singleton. Import and call directly:
#:
#:   from hibiscus.services.renewal_tracker import renewal_tracker
#:   context = await renewal_tracker.get_renewal_context(user_id)
renewal_tracker = RenewalTracker()
