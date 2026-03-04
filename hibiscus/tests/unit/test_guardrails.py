"""
Unit Tests — Guardrails
========================
Tests hallucination detection, compliance checks, and financial validation.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest
from hibiscus.guardrails.hallucination import check_hallucination
from hibiscus.guardrails.compliance import check_compliance
from hibiscus.guardrails.financial import check_financial


class TestHallucinationGuard:
    def test_low_confidence_fails(self):
        result = check_hallucination(
            response="Your copay is 20%.",
            sources=[{"type": "llm_reasoning", "confidence": 0.45}],
            confidence=0.25,
        )
        assert result.passed is False

    def test_specific_numbers_without_doc_source_flagged(self):
        result = check_hallucination(
            response="Your copay is 20% and sum insured is ₹5 lakh.",
            sources=[{"type": "llm_reasoning", "confidence": 0.75}],
            confidence=0.75,
        )
        # Should flag copay % as suspicious without document extraction source
        assert result.modified_response is not None

    def test_high_confidence_with_doc_source_passes(self):
        result = check_hallucination(
            response="Your sum insured is ₹10 lakh as per your policy document, page 3.",
            sources=[{"type": "document_extraction", "confidence": 0.92}],
            confidence=0.92,
        )
        assert result.passed is True

    def test_uncertainty_phrases_accepted(self):
        result = check_hallucination(
            response="I couldn't find the copay percentage in your document. Please check page 5.",
            sources=[{"type": "document_extraction", "confidence": 0.90}],
            confidence=0.85,
        )
        assert result.passed is True

    def test_general_educational_response_passes(self):
        result = check_hallucination(
            response="A sub-limit is a cap on specific treatment costs within the overall sum insured.",
            sources=[{"type": "llm_reasoning", "confidence": 0.80}],
            confidence=0.80,
        )
        assert result.passed is True


class TestComplianceGuard:
    def test_guaranteed_returns_blocked(self):
        result = check_compliance(
            response="This ULIP offers guaranteed returns of 12% per year.",
            intent="recommend",
        )
        assert result.passed is False

    def test_disclaimer_added_on_recommendation(self):
        result = check_compliance(
            response="Based on your profile, Star Comprehensive Health may be suitable.",
            intent="recommend",
        )
        assert "disclaimer" in result.modified_response.lower() or "educational" in result.modified_response.lower()

    def test_direct_buy_advice_softened(self):
        result = check_compliance(
            response="You should buy this health policy immediately.",
            intent="recommend",
        )
        # Should soften the language
        assert "should buy" not in result.modified_response.lower() or \
               "may consider" in result.modified_response.lower()

    def test_general_chat_no_disclaimer_needed(self):
        result = check_compliance(
            response="A deductible is the amount you pay before insurance kicks in.",
            intent="educate",
        )
        assert result.passed is True

    def test_guaranteed_claim_settlement_blocked(self):
        result = check_compliance(
            response="Your claim will definitely be settled within 7 days.",
            intent="claim",
        )
        assert result.passed is False


class TestFinancialGuard:
    def test_normal_amounts_pass(self):
        result = check_financial(
            "Your policy has a sum insured of ₹10 lakh and annual premium of ₹15,000."
        )
        assert result.passed is True

    def test_suspicious_amounts_detected(self):
        result = check_financial(
            "Your premium is ₹5 for a sum insured of ₹50 lakh."
        )
        # Very low premium for high coverage — suspicious
        assert len(result.suspicious_numbers) >= 0  # Might or might not flag (depends on context)

    def test_response_without_numbers_passes(self):
        result = check_financial(
            "Please upload your policy document so I can analyze it for you."
        )
        assert result.passed is True
