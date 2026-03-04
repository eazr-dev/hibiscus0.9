"""
HDFC ERGO Mock Integration
============================
Returns realistic data from KG seed data.
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

_PREMIUM_RATES = {
    (18, 25): 500, (26, 35): 600, (36, 45): 850,
    (46, 55): 1300, (56, 65): 2000, (66, 80): 3200, (81, 100): 4500,
}

_FAMILY_MULTIPLIER = {1: 1.0, 2: 1.7, 3: 2.1, 4: 2.5}


def _estimate_premium(age: int, sum_insured: float, family_size: int) -> float:
    rate = 650
    for (lo, hi), r in _PREMIUM_RATES.items():
        if lo <= age <= hi:
            rate = r
            break
    si_lakhs = sum_insured / 100000
    multiplier = _FAMILY_MULTIPLIER.get(min(family_size, 4), 2.5)
    return round(rate * si_lakhs * multiplier)


class HDFCErgoIntegration(InsurerIntegration):
    name = "HDFC ERGO General Insurance"
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
                WHERE i.name = 'HDFC ERGO General Insurance'
                  AND p.category = $category
                RETURN p.name AS name, p.eazr_score AS score,
                       p.copay AS copay, p.room_rent_limit AS room_rent
                ORDER BY p.eazr_score DESC LIMIT 3
                """,
                params={"category": product_type},
                query_name="hdfc_ergo_quote",
            )

            product_name = "HDFC ERGO Optima Secure"
            features = {"network_hospitals": 13000, "global_coverage": True, "no_claim_bonus": "50%"}

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
            logger.warning("hdfc_ergo_quote_failed", error=str(e))
            return None

    async def get_claims_status(self, policy_number: str, claim_id: str = "") -> Optional[ClaimsStatusResult]:
        return ClaimsStatusResult(
            claim_id=claim_id or f"HDT-{policy_number[-6:]}",
            status="under_review",
            amount_claimed=75000,
            amount_approved=None,
            last_updated="Pending review — mock data",
            next_steps=[
                "Upload original bills via HDFC ERGO app",
                "Expect processing within 14 working days",
                "Call 1800-266-0700 for status",
            ],
            source="mock_kg",
        )

    async def get_policy_details(self, policy_number: str) -> Optional[PolicyDetailResult]:
        return PolicyDetailResult(
            policy_number=policy_number,
            insurer=self.name,
            product_name="HDFC ERGO Optima Secure",
            status="active",
            sum_insured=1500000,
            premium_annual=18000,
            start_date="15/06/2025",
            end_date="14/06/2026",
            features={"network_hospitals": 13000, "global_coverage": True},
            source="mock_kg",
        )

    async def check_renewal_status(self, policy_number: str) -> Optional[RenewalStatusResult]:
        return RenewalStatusResult(
            policy_number=policy_number,
            renewal_due_date="14/06/2026",
            premium_amount=18000,
            auto_renewal=True,
            renewal_discount=5.0,
            source="mock_kg",
        )


hdfc_ergo_integration = HDFCErgoIntegration()
