"""
Unit Tests — Intent Classifier
================================
Tests keyword classification, complexity routing, and agent assignment.
These tests use keyword rules only (no LLM call required).
"""
import pytest
from hibiscus.orchestrator.nodes.intent_classification import (
    _fast_classify,
    _determine_complexity,
    _determine_agents,
)


class TestFastClassify:
    def test_health_policy_intent(self):
        result = _fast_classify("analyze my star health policy", [])
        assert result["category"] == "health"
        assert result["intent"] == "analyze"

    def test_surrender_intent(self):
        result = _fast_classify("should I surrender my LIC policy?", [])
        assert result["intent"] == "surrender"
        assert result["category"] == "life"

    def test_claim_intent(self):
        result = _fast_classify("help me file a claim for hospitalization", [])
        assert result["intent"] == "claim"
        assert result["emotional_state"] in ("neutral", "concerned")

    def test_education_intent(self):
        result = _fast_classify("what is a sub-limit in health insurance?", [])
        assert result["intent"] == "educate"

    def test_distressed_state(self):
        result = _fast_classify("my claim was rejected and I have an emergency", [])
        assert result["emotional_state"] == "distressed"

    def test_has_document_with_file(self):
        result = _fast_classify("analyze this", [{"filename": "policy.pdf"}])
        assert result["has_document"] is True
        assert result["intent"] == "analyze"

    def test_has_document_from_text(self):
        result = _fast_classify("what does my policy cover?", [])
        assert result["has_document"] is True

    def test_tax_intent(self):
        result = _fast_classify("how much 80D deduction can I claim?", [])
        assert result["intent"] == "tax"

    def test_general_chat(self):
        result = _fast_classify("hello", [])
        assert result["intent"] == "general_chat"
        assert result["category"] == "general"

    def test_grievance_intent(self):
        result = _fast_classify("how do I complain to IRDAI ombudsman?", [])
        assert result["intent"] == "grievance"


class TestComplexityDetermination:
    def test_l1_general_education(self):
        complexity = _determine_complexity("educate", has_document=False, agents_needed=[])
        assert complexity == "L1"

    def test_l2_policy_analysis(self):
        complexity = _determine_complexity("analyze", has_document=True, agents_needed=["policy_analyzer"])
        assert complexity == "L2"

    def test_l3_recommendation(self):
        complexity = _determine_complexity("recommend", has_document=False, agents_needed=["recommender"])
        assert complexity == "L3"

    def test_l4_surrender(self):
        complexity = _determine_complexity("surrender", has_document=True, agents_needed=["surrender_calculator"])
        assert complexity == "L4"


class TestAgentDetermination:
    def test_analyze_assigns_policy_analyzer(self):
        agents = _determine_agents("analyze", "health", has_document=True)
        assert "policy_analyzer" in agents

    def test_claim_assigns_claims_guide(self):
        agents = _determine_agents("claim", "health", has_document=False)
        assert "claims_guide" in agents

    def test_surrender_assigns_surrender_calculator(self):
        agents = _determine_agents("surrender", "life", has_document=True)
        assert "surrender_calculator" in agents

    def test_education_no_agents_needed(self):
        agents = _determine_agents("educate", "general", has_document=False)
        assert len(agents) == 0  # Direct LLM path
