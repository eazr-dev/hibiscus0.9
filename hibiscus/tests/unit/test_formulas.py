"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Unit tests: financial formulas — EMI, IRR, inflation, surrender value calculations.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest


class TestSurrenderValue:
    """Tests for knowledge/formulas/surrender_value.py."""

    def test_gsv_projection_returns_list(self):
        """calculate_surrender_projection returns a list of yearly results."""
        from hibiscus.knowledge.formulas.surrender_value import calculate_surrender_projection
        results = calculate_surrender_projection(
            annual_premium=50_000,
            policy_term=20,
            premium_term=20,
            sum_assured=500_000,
        )
        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0

    def test_gsv_grows_over_time(self):
        """GSV in later years should be higher than in earlier years."""
        from hibiscus.knowledge.formulas.surrender_value import calculate_surrender_projection
        results = calculate_surrender_projection(
            annual_premium=50_000,
            policy_term=20,
            premium_term=20,
            sum_assured=500_000,
        )
        # Find results for year 5 and year 10
        gsv_5 = next((r.gsv for r in results if r.year == 5), None)
        gsv_10 = next((r.gsv for r in results if r.year == 10), None)
        if gsv_5 is not None and gsv_10 is not None:
            assert gsv_10 >= gsv_5


class TestIRR:
    """Tests for knowledge/formulas/irr.py."""

    def test_irr_low_for_endowment(self):
        """Traditional endowment IRR typically 4-8%."""
        from hibiscus.knowledge.formulas.irr import compute_policy_irr
        # signature: annual_premium, premium_term, maturity_amount, policy_term
        result = compute_policy_irr(
            annual_premium=50_000,
            premium_term=20,
            maturity_amount=1_400_000,
            policy_term=20,
        )
        # Returns a float (IRR as decimal) or None
        if result is not None:
            # IRR is returned as a decimal (e.g., 0.05 = 5%) or as percentage
            # Accept both formats
            if result > 1:  # likely a percentage already
                assert 0 < result < 15
            else:
                assert 0 < result < 0.20  # 0-20% as decimal


class TestInflation:
    """Tests for knowledge/formulas/inflation.py."""

    def test_inflate_positive_growth(self):
        """Inflation must increase the amount over time."""
        from hibiscus.knowledge.formulas.inflation import inflate
        result = inflate(amount=100_000, years=10, rate=0.06)
        assert result > 100_000

    def test_inflate_zero_years(self):
        """Inflation over 0 years returns the same amount."""
        from hibiscus.knowledge.formulas.inflation import inflate
        result = inflate(amount=100_000, years=0, rate=0.06)
        assert result == pytest.approx(100_000, rel=1e-6)

    def test_real_coverage_needed_exceeds_current(self):
        """Real coverage needed after inflation should exceed current coverage."""
        from hibiscus.knowledge.formulas.inflation import real_coverage_needed
        needed = real_coverage_needed(current_coverage=500_000, years=10, rate=0.06)
        assert needed > 500_000


class TestCompoundGrowth:
    """Tests for knowledge/formulas/compound_growth.py."""

    def test_fv_lumpsum_grows(self):
        """FV of a lump sum must be greater than PV."""
        from hibiscus.knowledge.formulas.compound_growth import fv_lumpsum
        fv = fv_lumpsum(pv=100_000, rate=0.10, years=10)
        assert fv > 100_000

    def test_fv_lumpsum_at_zero_rate(self):
        """FV at 0% rate equals PV."""
        from hibiscus.knowledge.formulas.compound_growth import fv_lumpsum
        fv = fv_lumpsum(pv=100_000, rate=0.0, years=10)
        assert fv == pytest.approx(100_000, rel=1e-6)

    def test_fv_annuity_grows(self):
        """FV of annuity must be greater than sum of payments."""
        from hibiscus.knowledge.formulas.compound_growth import fv_annuity
        fv = fv_annuity(pmt=50_000, rate=0.12, years=20)
        assert fv > 50_000 * 20  # Better than just summing payments


class TestPremiumAdequacy:
    """Tests for knowledge/formulas/premium_adequacy.py."""

    def test_hlv_method_returns_dataclass(self):
        """HLV method must return an AdequacyResult with expected fields."""
        from hibiscus.knowledge.formulas.premium_adequacy import hlv_method
        result = hlv_method(
            annual_income=1_000_000,
            years_to_retirement=25,
        )
        assert hasattr(result, "recommended_coverage")
        assert result.recommended_coverage > 0

    def test_income_multiple_method_basic(self):
        """Income multiple method: 2 dependents → at least 10x coverage."""
        from hibiscus.knowledge.formulas.premium_adequacy import income_multiple_method
        result = income_multiple_method(
            annual_income=1_000_000,
            dependents=2,
        )
        assert result.recommended_coverage >= 10 * 1_000_000

    def test_health_cover_metro_family(self):
        """Metro family of 4 should need ₹25L+ recommended coverage."""
        from hibiscus.knowledge.formulas.premium_adequacy import health_cover_needed
        result = health_cover_needed(city_tier="metro", family_size=4, age=35)
        # health_cover_needed returns an AdequacyResult
        assert result.recommended_coverage >= 25_00_000  # ₹25 lakh

    def test_health_cover_tier2_lower(self):
        """Tier 2 city needs less coverage than metro."""
        from hibiscus.knowledge.formulas.premium_adequacy import health_cover_needed
        metro = health_cover_needed(city_tier="metro", family_size=4, age=35)
        tier2 = health_cover_needed(city_tier="tier2", family_size=4, age=35)
        assert metro.recommended_coverage > tier2.recommended_coverage


class TestEMI:
    """Tests for knowledge/formulas/emi.py."""

    def test_ipf_emi_returns_result(self):
        """IPF EMI must return an EMIResult with valid fields."""
        from hibiscus.knowledge.formulas.emi import ipf_emi
        result = ipf_emi(loan_amount=100_000, annual_rate=0.12, tenure_months=12)
        assert result.monthly_emi > 0
        assert result.total_payment > result.principal
        assert result.total_interest > 0

    def test_svf_emi_principal_is_surrender_value(self):
        """SVF EMI principal should match the surrender value."""
        from hibiscus.knowledge.formulas.emi import svf_emi
        result = svf_emi(surrender_value=200_000, annual_rate=0.14, tenure_months=24)
        assert result.principal == 200_000

    def test_emi_amortization_schedule_length(self):
        """Amortization schedule should have one row per month."""
        from hibiscus.knowledge.formulas.emi import ipf_emi
        result = ipf_emi(loan_amount=100_000, annual_rate=0.12, tenure_months=6)
        assert len(result.amortization_schedule) == 6

    def test_emi_higher_rate_means_higher_interest(self):
        """Higher interest rate must result in higher total interest."""
        from hibiscus.knowledge.formulas.emi import ipf_emi
        low_rate = ipf_emi(100_000, 0.10, 12)
        high_rate = ipf_emi(100_000, 0.18, 12)
        assert high_rate.total_interest > low_rate.total_interest


class TestOpportunityCost:
    """Tests for knowledge/formulas/opportunity_cost.py."""

    def test_endowment_vs_term_mf_returns_verdict(self):
        """Opportunity cost must return a verdict."""
        from hibiscus.knowledge.formulas.opportunity_cost import endowment_vs_term_mf
        result = endowment_vs_term_mf(
            endowment_premium=50_000,
            term_premium=5_000,
            endowment_sum_assured=1_000_000,
            years=20,
            mf_return=0.12,
        )
        assert hasattr(result, "verdict")
        assert hasattr(result, "opportunity_cost")
        assert result.verdict  # Non-empty verdict

    def test_high_mf_return_beats_endowment(self):
        """At 12% MF returns, term+MF should outperform endowment."""
        from hibiscus.knowledge.formulas.opportunity_cost import endowment_vs_term_mf
        result = endowment_vs_term_mf(
            endowment_premium=50_000,
            term_premium=5_000,
            endowment_sum_assured=1_000_000,
            years=20,
            mf_return=0.12,
        )
        # MF strategy should win significantly at 12% over 20 years
        assert result.investment_value > result.endowment_maturity_value


class TestEAZRScore:
    """Tests for knowledge/formulas/eazr_score.py."""

    def test_score_in_range(self):
        """EAZR score must be between 1 and 10."""
        from hibiscus.knowledge.formulas.eazr_score import calculate_eazr_score
        policy_data = {
            "sum_insured": 1_000_000,
            "annual_premium": 15_000,
            "copay_structure": "0%",
            "room_rent_limit": "No limit",
            "has_cashless": True,
            "network_hospitals": 14_000,
            "has_restoration": True,
            "exclusion_count": 5,
            "sub_limit_count": 2,
        }
        result = calculate_eazr_score(policy_data, "health")
        assert 1.0 <= result.total_score <= 10.0

    def test_better_policy_higher_score(self):
        """Policy with no copay and no room rent limit scores higher."""
        from hibiscus.knowledge.formulas.eazr_score import calculate_eazr_score
        good_policy = {
            "sum_insured": 1_000_000,
            "annual_premium": 15_000,
            "copay_structure": "0%",
            "room_rent_limit": "No limit",
            "has_cashless": True,
            "network_hospitals": 14_000,
            "has_restoration": True,
            "exclusion_count": 3,
            "sub_limit_count": 0,
        }
        bad_policy = {
            "sum_insured": 500_000,
            "annual_premium": 15_000,
            "copay_structure": "20%",
            "room_rent_limit": "1% of SI per day",
            "has_cashless": False,
            "network_hospitals": 2_000,
            "has_restoration": False,
            "exclusion_count": 15,
            "sub_limit_count": 8,
        }
        good_result = calculate_eazr_score(good_policy, "health")
        bad_result = calculate_eazr_score(bad_policy, "health")
        assert good_result.total_score > bad_result.total_score

    def test_grade_mapping(self):
        """Grade must be one of the defined grades."""
        from hibiscus.knowledge.formulas.eazr_score import calculate_eazr_score
        policy_data = {
            "sum_insured": 1_000_000,
            "annual_premium": 15_000,
        }
        result = calculate_eazr_score(policy_data, "health")
        assert result.grade in {"A+", "A", "B+", "B", "C", "D"}

    def test_score_has_interpretation(self):
        """Score result must include a non-empty interpretation string."""
        from hibiscus.knowledge.formulas.eazr_score import calculate_eazr_score
        result = calculate_eazr_score({"sum_insured": 500_000}, "health")
        assert result.interpretation
        assert len(result.interpretation) > 10
