"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Unit tests: guardrails — compliance, hallucination, PII, emotional, financial checks.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.guardrails.hallucination import check_hallucination
from hibiscus.guardrails.compliance import check_compliance
from hibiscus.guardrails.financial import check_financial
from hibiscus.guardrails.emotional import check_emotional
from hibiscus.guardrails.pii import check_pii, mask_pii_for_logging


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
            "Your annual premium is ₹15,000 which is reasonable for your age group."
        )
        assert result.passed is True

    def test_suspicious_amounts_detected(self):
        result = check_financial(
            "Your premium is ₹5 for a sum insured of ₹50 lakh."
        )
        # Very low premium (₹5) for high coverage (₹50L) — should flag as suspicious
        assert result.passed is False
        assert len(result.suspicious_numbers) > 0
        assert any("sum insured" in s.lower() or "low" in s.lower() for s in result.suspicious_numbers)

    def test_response_without_numbers_passes(self):
        result = check_financial(
            "Please upload your policy document so I can analyze it for you."
        )
        assert result.passed is True

    def test_modified_response_present(self):
        result = check_financial(
            "Your policy has a sum insured of ₹10 lakh and annual premium of ₹15,000."
        )
        assert result.modified_response is not None

    def test_irr_out_of_range_flagged(self):
        result = check_financial(
            "This ULIP has an IRR of 45% which is exceptional."
        )
        assert result.passed is False
        assert any("IRR" in s for s in result.suspicious_numbers)


class TestEmotionalGuard:
    def test_neutral_passes_through(self):
        result = check_emotional(
            response="Your policy covers hospitalization up to ₹10 lakh.",
            emotional_state="neutral",
        )
        assert result.passed is True
        assert result.empathy_prefix == ""
        assert result.escalate_to_claude is False

    def test_distressed_gets_empathy_prefix(self):
        result = check_emotional(
            response="Here are the steps to file your claim.",
            emotional_state="distressed",
        )
        assert result.empathy_prefix != ""
        assert result.escalate_to_claude is True
        assert result.modified_response is not None
        assert result.modified_response.startswith(result.empathy_prefix)

    def test_urgent_gets_empathy_and_escalation(self):
        result = check_emotional(
            response="You need to submit documents within 24 hours.",
            emotional_state="urgent",
        )
        assert result.empathy_prefix != ""
        assert result.escalate_to_claude is True

    def test_frustrated_gets_empathy_prefix(self):
        result = check_emotional(
            response="We cannot process your request at this time.",
            emotional_state="frustrated",
        )
        assert result.modified_response is not None
        assert result.empathy_prefix != ""
        # Frustrated responses get an empathy prefix
        assert result.modified_response.startswith(result.empathy_prefix)

    def test_curious_passes_unchanged(self):
        result = check_emotional(
            response="A deductible is the initial amount you pay before insurance coverage begins.",
            emotional_state="curious",
        )
        assert result.passed is True
        assert result.empathy_prefix == ""

    def test_already_empathetic_no_double_prefix(self):
        result = check_emotional(
            response="I understand this is a difficult time. Here are the steps.",
            emotional_state="distressed",
        )
        # Should not double the empathy prefix since response already has empathy
        count = result.modified_response.lower().count("understand")
        assert count <= 2  # Original + at most one prefix


class TestPIIGuard:
    def test_aadhaar_masked(self):
        result = check_pii("My Aadhaar number is 1234 5678 9012.")
        assert result.passed is False
        assert "aadhaar" in [t.lower() for t in result.pii_types_found]
        assert "1234 5678 9012" not in result.modified_response

    def test_pan_masked(self):
        result = check_pii("My PAN is ABCDE1234F and I need tax benefits.")
        assert result.passed is False
        assert "pan" in [t.lower() for t in result.pii_types_found]
        assert "ABCDE1234F" not in result.modified_response

    def test_phone_masked(self):
        result = check_pii("Call me at +91 9876543210 for details.")
        assert result.passed is False
        assert any("mobile" in t.lower() or "phone" in t.lower() for t in result.pii_types_found)
        assert "9876543210" not in result.modified_response

    def test_email_masked(self):
        result = check_pii("Send documents to user@example.com please.")
        assert result.passed is False
        assert "email" in [t.lower() for t in result.pii_types_found]
        assert "user@example.com" not in result.modified_response

    def test_no_pii_passes(self):
        result = check_pii("What is the waiting period for pre-existing diseases?")
        assert result.passed is True
        assert len(result.pii_types_found) == 0

    def test_multiple_pii_all_masked(self):
        text = "My Aadhaar is 1234 5678 9012 and PAN is ABCDE1234F. Call 9876543210."
        result = check_pii(text)
        assert result.passed is False
        assert len(result.pii_types_found) >= 2
        assert "1234 5678 9012" not in result.modified_response
        assert "ABCDE1234F" not in result.modified_response

    def test_mask_pii_for_logging(self):
        text = "User 9876543210 requested analysis for PAN ABCDE1234F"
        masked = mask_pii_for_logging(text)
        assert "9876543210" not in masked
        assert "ABCDE1234F" not in masked
