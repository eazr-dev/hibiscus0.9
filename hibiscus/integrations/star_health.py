"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Star Health integration — health quote API, network hospital lookup, claim tracking.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from typing import Optional

from hibiscus.integrations.base import (
    InsurerIntegration, QuoteResult, ClaimsStatusResult,
    PolicyDetailResult, RenewalStatusResult,
)
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Premium estimation table (age-based, per ₹1L SI) ────────────────────────
_PREMIUM_RATES = {
    # age_range: rate per ₹1L SI (annual, individual)
    (18, 25): 450,
    (26, 35): 550,
    (36, 45): 800,
    (46, 55): 1200,
    (56, 65): 1800,
    (66, 80): 2800,
    (81, 100): 4000,
}

_FAMILY_MULTIPLIER = {1: 1.0, 2: 1.7, 3: 2.1, 4: 2.5}


def _estimate_premium(age: int, sum_insured: float, family_size: int) -> float:
    """Estimate annual premium based on age, SI, and family size."""
    rate = 600  # default
    for (lo, hi), r in _PREMIUM_RATES.items():
        if lo <= age <= hi:
            rate = r
            break
    si_lakhs = sum_insured / 100000
    multiplier = _FAMILY_MULTIPLIER.get(min(family_size, 4), 2.5)
    return round(rate * si_lakhs * multiplier)


class StarHealthIntegration(InsurerIntegration):
    name = "Star Health and Allied Insurance"
    supported_features = ["quote", "claims_status", "policy_details", "renewal"]

    async def get_quote(
        self, age: int, sum_insured: float, product_type: str = "health",
        city: str = "Mumbai", family_size: int = 1,
    ) -> Optional[QuoteResult]:
        try:
            from hibiscus.knowledge.graph.client import kg_client
            results = await kg_client.query(
                """
                MATCH (i:Insurer)-[:OFFERS]->(p:Product)
                WHERE i.name = 'Star Health and Allied Insurance'
                  AND p.category = $category
                RETURN p.name AS name, p.sum_insured_min AS si_min,
                       p.sum_insured_max AS si_max, p.eazr_score AS score,
                       p.copay AS copay, p.room_rent_limit AS room_rent
                ORDER BY p.eazr_score DESC LIMIT 3
                """,
                params={"category": product_type},
                query_name="star_health_quote",
            )

            product_name = "Star Health Comprehensive"
            features = {"network_hospitals": 14000, "no_room_rent_cap": True, "restoration_benefit": True}

            if results:
                best = results[0]
                product_name = best.get("name", product_name)
                features.update({
                    "eazr_score": best.get("score"),
                    "copay": best.get("copay"),
                    "room_rent_limit": best.get("room_rent"),
                })

            premium = _estimate_premium(age, sum_insured, family_size)

            return QuoteResult(
                insurer=self.name,
                product_name=product_name,
                premium_annual=premium,
                sum_insured=sum_insured,
                features=features,
                source="mock_kg",
                timestamp=time.time(),
            )
        except Exception as e:
            logger.warning("star_health_quote_failed", error=str(e))
            return None

    async def get_claims_status(self, policy_number: str, claim_id: str = "") -> Optional[ClaimsStatusResult]:
        return ClaimsStatusResult(
            claim_id=claim_id or f"CLM-{policy_number[-6:]}",
            status="under_review",
            amount_claimed=50000,
            amount_approved=None,
            last_updated="Pending review — mock data",
            next_steps=[
                "Submit discharge summary to TPA",
                "Expect approval within 7-10 working days",
                "Contact Star Health helpline 1800-425-2255 for status",
            ],
            source="mock_kg",
        )

    async def get_policy_details(self, policy_number: str) -> Optional[PolicyDetailResult]:
        return PolicyDetailResult(
            policy_number=policy_number,
            insurer=self.name,
            product_name="Star Health Comprehensive",
            status="active",
            sum_insured=1000000,
            premium_annual=15000,
            start_date="01/04/2025",
            end_date="31/03/2026",
            features={"network_hospitals": 14000, "restoration_benefit": True},
            source="mock_kg",
        )

    async def check_renewal_status(self, policy_number: str) -> Optional[RenewalStatusResult]:
        return RenewalStatusResult(
            policy_number=policy_number,
            renewal_due_date="31/03/2026",
            premium_amount=15000,
            auto_renewal=False,
            renewal_discount=0.0,
            source="mock_kg",
        )


star_health_integration = StarHealthIntegration()
