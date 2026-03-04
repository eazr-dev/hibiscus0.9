"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Unit tests: model router — LLM tier selection based on complexity signals.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest
from hibiscus.llm.model_selector import select_tier, Tier


class TestModelSelector:
    def test_intent_classification_uses_tier1(self):
        tier = select_tier("intent_classification")
        assert tier == Tier.T1

    def test_surrender_uses_tier2(self):
        tier = select_tier("surrender_calculation")
        assert tier == Tier.T2

    def test_distressed_user_uses_tier3(self):
        tier = select_tier("policy_analysis", emotional_state="distressed")
        assert tier == Tier.T3

    def test_urgent_uses_tier3(self):
        tier = select_tier("claims_guide", emotional_state="urgent")
        assert tier == Tier.T3

    def test_low_confidence_financial_escalates(self):
        tier = select_tier("surrender_calculation", confidence=0.50)
        assert tier == Tier.T3

    def test_l4_complexity_uses_tier2(self):
        tier = select_tier("policy_analysis", complexity="L4")
        assert tier == Tier.T2

    def test_high_complexity_overrides_default_tier1(self):
        """Tasks normally routed to Tier 1 should escalate to Tier 2+ with high complexity."""
        # education normally routes to Tier 1, but L4 complexity should override
        tier = select_tier("education", complexity="L4")
        assert tier in (Tier.T2, Tier.T3), f"High complexity should route to Tier 2 or 3, got {tier}"

    def test_high_complexity_with_low_confidence_escalates_to_tier3(self):
        """High complexity + low confidence on critical task should escalate to Tier 3."""
        tier = select_tier("surrender_calculation", complexity="L4", confidence=0.50)
        assert tier == Tier.T3

    def test_l1_uses_tier1(self):
        tier = select_tier("l1_response", complexity="L1")
        assert tier == Tier.T1

    def test_education_uses_tier1(self):
        tier = select_tier("education")
        assert tier == Tier.T1

    def test_portfolio_optimization_uses_tier2(self):
        tier = select_tier("portfolio_optimization")
        assert tier == Tier.T2

    def test_tax_computation_uses_tier2(self):
        tier = select_tier("tax_computation")
        assert tier == Tier.T2
