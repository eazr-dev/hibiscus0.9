"""
Unit Tests — Model Router
==========================
Tests that correct LLM tier is selected for each task type.
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
