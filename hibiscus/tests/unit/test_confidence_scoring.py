"""
Unit Tests — Confidence Scoring
================================
Tests AgentResult confidence clamping, source weighting, and
the confidence scoring behaviour across agents.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest
from hibiscus.agents.base import AgentResult


class TestAgentResultConfidenceClamping:
    """AgentResult must clamp confidence to [0.0, 1.0]."""

    def test_confidence_clamped_above_one(self):
        result = AgentResult(response="Test", confidence=1.5)
        assert result.confidence == 1.0

    def test_confidence_clamped_below_zero(self):
        result = AgentResult(response="Test", confidence=-0.3)
        assert result.confidence == 0.0

    def test_valid_confidence_preserved(self):
        result = AgentResult(response="Test", confidence=0.75)
        assert result.confidence == 0.75

    def test_zero_confidence_accepted(self):
        result = AgentResult(response="Test", confidence=0.0)
        assert result.confidence == 0.0

    def test_one_confidence_accepted(self):
        result = AgentResult(response="Test", confidence=1.0)
        assert result.confidence == 1.0


class TestAgentResultDefaults:
    """AgentResult default field values."""

    def test_sources_default_empty_list(self):
        result = AgentResult(response="Test", confidence=0.8)
        assert result.sources == []

    def test_follow_up_default_empty_list(self):
        result = AgentResult(response="Test", confidence=0.8)
        assert result.follow_up_suggestions == []

    def test_structured_data_default_empty_dict(self):
        result = AgentResult(response="Test", confidence=0.8)
        assert result.structured_data == {}

    def test_latency_ms_default_zero(self):
        result = AgentResult(response="Test", confidence=0.8)
        assert result.latency_ms == 0


class TestAgentResultToDict:
    """AgentResult.to_dict() must include all expected keys."""

    def test_to_dict_has_required_keys(self):
        result = AgentResult(
            response="Your copay is 20%.",
            confidence=0.85,
            sources=[{"type": "document_extraction", "confidence": 0.85}],
            latency_ms=1200,
            tokens_in=500,
            tokens_out=200,
        )
        d = result.to_dict()
        assert "response" in d
        assert "confidence" in d
        assert "sources" in d
        assert "latency_ms" in d
        assert "tokens_in" in d
        assert "tokens_out" in d

    def test_to_dict_values_match(self):
        result = AgentResult(
            response="Test response",
            confidence=0.90,
            latency_ms=500,
        )
        d = result.to_dict()
        assert d["response"] == "Test response"
        assert d["confidence"] == 0.90
        assert d["latency_ms"] == 500


class TestConfidenceSourceWeighting:
    """Source type should influence whether hallucination guard passes."""

    def test_document_extraction_source_is_highest_confidence(self):
        """Document extraction sources are most reliable — should not be flagged."""
        from hibiscus.guardrails.hallucination import check_hallucination
        result = check_hallucination(
            response="Your sum insured is ₹10 lakh (page 3 of your policy).",
            sources=[{"type": "document_extraction", "confidence": 0.95}],
            confidence=0.95,
        )
        assert result.passed is True

    def test_low_confidence_llm_reasoning_flagged(self):
        """Low-confidence LLM-only sources on specific numbers should be flagged."""
        from hibiscus.guardrails.hallucination import check_hallucination
        result = check_hallucination(
            response="Your copay is 20%.",
            sources=[{"type": "llm_reasoning", "confidence": 0.30}],
            confidence=0.30,
        )
        assert result.passed is False

    def test_kg_source_accepted_for_benchmarks(self):
        """Knowledge graph source is reliable for industry benchmarks."""
        from hibiscus.guardrails.hallucination import check_hallucination
        result = check_hallucination(
            response="The industry average CSR is 98.5% according to IRDAI data.",
            sources=[{"type": "knowledge_graph", "confidence": 0.90}],
            confidence=0.90,
        )
        assert result.passed is True
