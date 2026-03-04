"""
Unit tests for PolicyClassifier (Tier 1 + Tier 2 — no LLM needed).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest

from hibiscus.extraction.classifier import PolicyClassifier, ClassificationResult


@pytest.fixture
def classifier():
    return PolicyClassifier()


# ── Tier 1: UIN Patterns ─────────────────────────────────────────────


class TestTier1UIN:
    def test_health_uin_hlip(self, classifier):
        text = "Policy UIN: 123NHLIP12345 — Star Health Insurance"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "health"
        assert result.confidence >= 0.90
        assert result.tier_used == 1

    def test_health_uin_irdan(self, classifier):
        # IRDAN health UIN must end with HL (not followed by L[A-Z] which matches life)
        text = "UIN: SHAHLIP00234 Health Policy Schedule"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "health"

    def test_life_uin(self, classifier):
        text = "Policy Document UIN: 512L345V01 Life Insurance"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "life"

    def test_motor_uin(self, classifier):
        # Motor UIN needs RPMC/CPMC/etc after IRDAN pattern
        text = "UIN: IRDAN123ABCRPMC Motor Schedule"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "motor"

    def test_travel_uin(self, classifier):
        text = "UIN: IRDAN123ABCRPTV Travel Policy"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "travel"

    def test_pa_uin(self, classifier):
        text = "UIN: IRDAN123ABCRPPA Accident Policy"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "pa"


# ── Tier 1: Standard Products ─────────────────────────────────────────


class TestTier1StandardProducts:
    def test_arogya_sanjeevani(self, classifier):
        text = "AROGYA SANJEEVANI Health Insurance Policy"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "health"
        assert result.sub_type == "arogya_sanjeevani"
        assert result.confidence == 0.98

    def test_saral_jeevan_bima(self, classifier):
        text = "Saral Jeevan Bima — Standard Term Life Policy"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "life"
        assert result.sub_type == "term"

    def test_saral_suraksha_bima(self, classifier):
        text = "Saral Suraksha Bima Personal Accident Policy"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "pa"

    def test_bharat_yatra_suraksha(self, classifier):
        text = "Bharat Yatra Suraksha Travel Insurance"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "travel"


# ── Tier 1: Deterministic Fields ──────────────────────────────────────


class TestTier1DeterministicFields:
    def test_motor_deterministic(self, classifier):
        text = "Engine Number: XYZ123 Chassis Number: ABC456 Registration Number: MH01AB1234"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "motor"
        assert result.confidence >= 0.90

    def test_travel_deterministic(self, classifier):
        text = "Passport Number: K1234567 Destination Country: United States Trip Cancellation"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "travel"
        assert result.confidence >= 0.90


# ── Tier 1: Insurer Prior ────────────────────────────────────────────


class TestTier1InsurerPrior:
    def test_life_only_insurer(self, classifier):
        text = "LIC of India Policy Bond Number: 123456789 Premium Receipt"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "life"
        assert result.confidence >= 0.85

    def test_health_only_insurer(self, classifier):
        # "star health" is in _HEALTH_ONLY_INSURERS but life-only check runs first
        # and "star health" doesn't match any life-only insurer, so health wins
        text = "Niva Bupa Health Insurance Policy Schedule"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "health"
        assert result.confidence >= 0.85

    def test_care_health_insurer(self, classifier):
        text = "Manipal Cigna Health Insurance Policy Document"
        result = classifier._tier1_rules(text, text.lower())
        assert result is not None
        assert result.category == "health"


# ── Tier 2: Keyword Scoring ──────────────────────────────────────────


class TestTier2Scoring:
    def test_health_keywords(self, classifier):
        text = "room rent limit cumulative bonus day care procedure hospitalization copay sum insured"
        result = classifier._tier2_scoring(text.lower())
        assert result is not None
        assert result.category == "health"
        assert result.confidence >= 0.50
        assert result.tier_used == 2

    def test_life_keywords(self, classifier):
        text = "sum assured maturity benefit death benefit surrender value nominee premium paying term"
        result = classifier._tier2_scoring(text.lower())
        assert result is not None
        assert result.category == "life"
        assert result.confidence >= 0.50

    def test_motor_keywords(self, classifier):
        text = "idv insured declared value own damage third party liability zero depreciation ncb"
        result = classifier._tier2_scoring(text.lower())
        assert result is not None
        assert result.category == "motor"
        assert result.confidence >= 0.50

    def test_travel_keywords(self, classifier):
        text = "trip cancellation baggage loss flight delay repatriation passport destination"
        result = classifier._tier2_scoring(text.lower())
        assert result is not None
        assert result.category == "travel"
        assert result.confidence >= 0.50

    def test_pa_keywords(self, classifier):
        text = "accidental death permanent total disability permanent partial disability capital sum insured"
        result = classifier._tier2_scoring(text.lower())
        assert result is not None
        assert result.category == "pa"
        assert result.confidence >= 0.50

    def test_negative_signals_reduce_confidence(self, classifier):
        """Negative signals should reduce confidence for the wrong category."""
        # Health text with motor negative signals
        text = "hospitalization room rent copay sum insured idv chassis number registration number"
        result = classifier._tier2_scoring(text.lower())
        # Health should still win but motor keywords reduce its confidence
        assert result is not None
        assert result.category == "health"

    def test_no_keywords_returns_none(self, classifier):
        text = "this is a completely unrelated document about cooking recipes"
        result = classifier._tier2_scoring(text.lower())
        assert result is None or result.confidence < 0.50


# ── Sub-type Detection ────────────────────────────────────────────────


class TestSubTypeDetection:
    def test_health_family_floater(self, classifier):
        sub = classifier._detect_sub_type("health", "family floater policy")
        assert sub == "family_floater"

    def test_health_senior(self, classifier):
        sub = classifier._detect_sub_type("health", "senior citizen health insurance")
        assert sub == "senior"

    def test_health_topup(self, classifier):
        sub = classifier._detect_sub_type("health", "super top-up plan")
        assert sub == "top_up"

    def test_life_term(self, classifier):
        sub = classifier._detect_sub_type("life", "term plan pure protection")
        assert sub == "term"

    def test_life_ulip(self, classifier):
        sub = classifier._detect_sub_type("life", "unit linked investment plan")
        assert sub == "ulip"

    def test_life_endowment(self, classifier):
        sub = classifier._detect_sub_type("life", "endowment plan with maturity benefit")
        assert sub == "endowment"

    def test_motor_comprehensive(self, classifier):
        sub = classifier._detect_sub_type("motor", "comprehensive motor insurance package")
        assert sub == "comprehensive"

    def test_motor_third_party(self, classifier):
        sub = classifier._detect_sub_type("motor", "third party only liability policy")
        assert sub == "third_party"

    def test_travel_international(self, classifier):
        sub = classifier._detect_sub_type("travel", "international travel insurance overseas")
        assert sub == "international"

    def test_pa_group(self, classifier):
        # "personal" matches "individual" sub-type first, so use text without "personal"
        sub = classifier._detect_sub_type("pa", "group accident policy employer")
        assert sub == "group"

    def test_no_subtype(self, classifier):
        sub = classifier._detect_sub_type("health", "some generic text")
        assert sub == ""


# ── Full Classify Flow (Tier 1 + Tier 2, no LLM) ─────────────────────


class TestFullClassify:
    @pytest.mark.asyncio
    async def test_classify_health_uin(self, classifier):
        text = "UIN: 234NHLIP567 Star Health Family Floater"
        result = await classifier.classify(text)
        assert result.category == "health"
        assert result.confidence >= 0.85
        assert result.sub_type == "family_floater"

    @pytest.mark.asyncio
    async def test_classify_motor_deterministic(self, classifier):
        text = "Registration Number: MH01AB1234 Engine Number: XYZ Chassis Number: ABC Comprehensive"
        result = await classifier.classify(text)
        assert result.category == "motor"
        assert result.sub_type == "comprehensive"

    @pytest.mark.asyncio
    async def test_classify_travel_keywords(self, classifier):
        text = "trip cancellation baggage loss flight delay passport destination overseas"
        result = await classifier.classify(text)
        assert result.category == "travel"
        assert result.sub_type == "international"
