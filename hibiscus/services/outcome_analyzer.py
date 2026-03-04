"""
Outcome Analyzer Service
========================
Analyzes outcome patterns to improve recommendations.
Computes: conversion rates, satisfaction by agent, recommendation accuracy.

Used by:
- Recommender agent (injects stats into synthesis prompt)
- Admin dashboard (aggregate effectiveness metrics)
- HibiscusBench evaluation (cross-reference with DQ scores)
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


class OutcomeAnalyzer:
    """
    Analyzes outcome data to extract actionable patterns.
    All methods are safe to call even when PostgreSQL is unavailable.
    """

    async def get_recommendation_stats(
        self,
        advice_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregate stats for a specific advice type or all types.

        Returns:
            {
                "total": int,
                "conversion_rate": float (0-1),
                "avg_satisfaction": float (1-5) or None,
                "by_type": {advice_type: {total, converted, rate}},
                "top_performing_agents": [str],
            }
        """
        try:
            from hibiscus.memory.layers.outcome import get_outcome_stats

            stats = await get_outcome_stats()
            total = stats.get("total_outcomes", 0)
            if total == 0:
                return self._empty_stats()

            successful = stats.get("successful_count", 0)
            by_type = stats.get("by_advice_type", {})

            # Compute conversion rates per type
            type_stats = {}
            for atype, data in by_type.items():
                t = data.get("total", 0)
                s = data.get("successful", 0)
                type_stats[atype] = {
                    "total": t,
                    "converted": s,
                    "rate": round(s / t, 3) if t > 0 else 0.0,
                    "avg_satisfaction": data.get("avg_satisfaction"),
                }

            # Find top-performing agents (by conversion rate, min 5 outcomes)
            ranked = sorted(
                [(k, v) for k, v in type_stats.items() if v["total"] >= 5],
                key=lambda x: x[1]["rate"],
                reverse=True,
            )
            top_agents = [k for k, _ in ranked[:3]]

            result = {
                "total": total,
                "conversion_rate": round(successful / total, 3) if total > 0 else 0.0,
                "avg_satisfaction": stats.get("avg_satisfaction"),
                "by_type": type_stats,
                "top_performing_agents": top_agents,
            }

            # Filter to specific type if requested
            if advice_type and advice_type in type_stats:
                result["filtered"] = type_stats[advice_type]

            return result

        except Exception as e:
            logger.warning("outcome_analysis_failed", error=str(e))
            return self._empty_stats()

    async def get_insurer_effectiveness(self) -> Dict[str, Any]:
        """
        Get outcome stats grouped by insurer.

        Returns:
            {insurer_name: {total, successful, rate}}
        """
        try:
            from hibiscus.memory.layers.outcome import get_outcome_stats

            stats = await get_outcome_stats()
            by_insurer = stats.get("by_insurer", {})

            result = {}
            for insurer, data in by_insurer.items():
                t = data.get("total", 0)
                s = data.get("successful", 0)
                result[insurer] = {
                    "total": t,
                    "successful": s,
                    "rate": round(s / t, 3) if t > 0 else 0.0,
                }

            return result

        except Exception as e:
            logger.warning("insurer_effectiveness_failed", error=str(e))
            return {}

    def format_stats_for_prompt(self, stats: Dict[str, Any]) -> str:
        """
        Format outcome stats as a concise context string for prompt injection.
        Returns empty string if no meaningful data.
        """
        total = stats.get("total", 0)
        if total < 5:
            return ""

        parts = []
        rate = stats.get("conversion_rate", 0)
        sat = stats.get("avg_satisfaction")

        parts.append(f"OUTCOME DATA ({total} past recommendations tracked):")
        parts.append(f"  Overall follow-through rate: {rate:.0%}")
        if sat:
            parts.append(f"  Average user satisfaction: {sat:.1f}/5")

        by_type = stats.get("by_type", {})
        for atype in ("recommend", "surrender", "claim"):
            if atype in by_type and by_type[atype]["total"] >= 3:
                t = by_type[atype]
                parts.append(f"  {atype}: {t['rate']:.0%} follow-through ({t['total']} tracked)")

        return "\n".join(parts)

    @staticmethod
    def _empty_stats() -> Dict[str, Any]:
        return {
            "total": 0,
            "conversion_rate": 0.0,
            "avg_satisfaction": None,
            "by_type": {},
            "top_performing_agents": [],
        }


# ── Module-level singleton ──────────────────────────────────────────────────
outcome_analyzer = OutcomeAnalyzer()
