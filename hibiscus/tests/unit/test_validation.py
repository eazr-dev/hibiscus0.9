"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Unit tests: extraction validation — cross-referencing extracted data with source text.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest

from hibiscus.extraction.validation import ValidationEngine, ValidationResult


@pytest.fixture
def engine():
    return ValidationEngine()


def _cf(value, source_page=1, confidence=0.95):
    """Shortcut for building ConfidenceField dicts."""
    return {"value": value, "source_page": source_page, "confidence": confidence}


# ── Check 1: Evidence Grounding ───────────────────────────────────────


class TestEvidenceGrounding:
    @pytest.mark.asyncio
    async def test_critical_field_missing_page_is_error(self, engine):
        extraction = {
            "sumInsured": {"value": 500000, "source_page": None, "confidence": 0.9},
        }
        result = await engine.validate(extraction, "health")
        errors = [e for e in result.errors if e.check == "evidence"]
        assert len(errors) == 1
        assert errors[0].field == "sumInsured"

    @pytest.mark.asyncio
    async def test_important_field_missing_page_is_warning(self, engine):
        # Use a field with IMPORTANT criticality (weight=2) — generates warning, not error
        extraction = {
            "restoration": {"value": "100%", "source_page": None, "confidence": 0.8},
        }
        result = await engine.validate(extraction, "health")
        warnings = [w for w in result.warnings if w.check == "evidence"]
        assert len(warnings) >= 1

    @pytest.mark.asyncio
    async def test_field_with_page_no_issues(self, engine):
        extraction = {
            "sumInsured": _cf(1000000),
            "totalPremium": _cf(25000),
        }
        result = await engine.validate(extraction, "health")
        evidence_errors = [e for e in result.errors if e.check == "evidence"]
        assert len(evidence_errors) == 0


# ── Check 2: Cross-Field Logic ────────────────────────────────────────


class TestCrossFieldLogic:
    @pytest.mark.asyncio
    async def test_zero_coverage_is_error(self, engine):
        extraction = {"sumInsured": _cf(0)}
        result = await engine.validate(extraction, "health")
        logic_errors = [e for e in result.errors if e.check == "logic"]
        assert any("must be > 0" in e.message for e in logic_errors)

    @pytest.mark.asyncio
    async def test_premium_gt_coverage_warning(self, engine):
        extraction = {
            "sumInsured": _cf(500000),
            "totalPremium": _cf(600000),
        }
        result = await engine.validate(extraction, "health")
        logic_warnings = [w for w in result.warnings if w.check == "logic"]
        assert any("Premium" in w.message and ">= coverage" in w.message for w in logic_warnings)

    @pytest.mark.asyncio
    async def test_end_before_start_is_error(self, engine):
        extraction = {
            "policyPeriodStart": _cf("2025-06-01"),
            "policyPeriodEnd": _cf("2024-05-31"),
        }
        result = await engine.validate(extraction, "health")
        logic_errors = [e for e in result.errors if e.check == "logic"]
        assert any("End date" in e.message for e in logic_errors)

    @pytest.mark.asyncio
    async def test_motor_standalone_od_tp_warning(self, engine):
        extraction = {
            "productType": _cf("Standalone OD"),
            "tpPremium": _cf(5000),
            "idv": _cf(500000),
        }
        result = await engine.validate(extraction, "motor")
        logic_warnings = [w for w in result.warnings if w.check == "logic"]
        assert any("Standalone OD" in w.message for w in logic_warnings)

    @pytest.mark.asyncio
    async def test_motor_pan_4th_char_error(self, engine):
        extraction = {
            "ownerPan": _cf("ABCDE1234F"),  # 4th char is 'D', not 'P'
            "idv": _cf(500000),
        }
        result = await engine.validate(extraction, "motor")
        logic_errors = [e for e in result.errors if e.check == "logic"]
        assert any("PAN 4th char" in e.message for e in logic_errors)

    @pytest.mark.asyncio
    async def test_motor_valid_pan(self, engine):
        extraction = {
            "ownerPan": _cf("ABCPD1234F"),  # 4th char is 'P' = correct
            "idv": _cf(500000),
        }
        result = await engine.validate(extraction, "motor")
        pan_errors = [e for e in result.errors if "PAN" in e.message]
        assert len(pan_errors) == 0

    @pytest.mark.asyncio
    async def test_motor_gross_gst_total_mismatch(self, engine):
        extraction = {
            "grossPremium": _cf(10000),
            "gst": _cf(1800),
            "totalPremium": _cf(15000),  # Should be 11800
            "idv": _cf(500000),
        }
        result = await engine.validate(extraction, "motor")
        logic_warnings = [w for w in result.warnings if "grossPremium" in w.message]
        assert len(logic_warnings) == 1

    @pytest.mark.asyncio
    async def test_motor_insurer_email_domain(self, engine):
        extraction = {
            "ownerEmail": _cf("claims@hdfcergo.com"),
            "idv": _cf(500000),
        }
        result = await engine.validate(extraction, "motor")
        email_warnings = [w for w in result.warnings if "ownerEmail" in w.field]
        assert len(email_warnings) == 1

    @pytest.mark.asyncio
    async def test_life_maturity_mismatch(self, engine):
        extraction = {
            "maturityDate": _cf("2040-01-01"),
            "policyPeriodEnd": _cf("2045-01-01"),
            "sumAssured": _cf(5000000),
        }
        result = await engine.validate(extraction, "life")
        mat_warnings = [w for w in result.warnings if "maturityDate" in w.field]
        assert len(mat_warnings) == 1


# ── Check 3: Format Validation ────────────────────────────────────────


class TestFormatValidation:
    @pytest.mark.asyncio
    async def test_bad_date_format_warning(self, engine):
        extraction = {
            "policyPeriodStart": _cf("01/06/2025"),  # DD/MM/YYYY instead of YYYY-MM-DD
        }
        result = await engine.validate(extraction, "health")
        format_warnings = [w for w in result.warnings if w.check == "format"]
        assert any("YYYY-MM-DD" in w.message for w in format_warnings)

    @pytest.mark.asyncio
    async def test_good_date_format_no_warning(self, engine):
        extraction = {
            "policyPeriodStart": _cf("2025-06-01"),
        }
        result = await engine.validate(extraction, "health")
        date_warnings = [w for w in result.warnings if w.check == "format" and "policyPeriodStart" in w.field]
        assert len(date_warnings) == 0

    @pytest.mark.asyncio
    async def test_percentage_out_of_range(self, engine):
        extraction = {
            "generalCopay": _cf(150),  # > 100%
        }
        result = await engine.validate(extraction, "health")
        pct_warnings = [w for w in result.warnings if w.check == "format"]
        assert any("Percentage" in w.message for w in pct_warnings)

    @pytest.mark.asyncio
    async def test_short_uin_warning(self, engine):
        extraction = {
            "uin": _cf("AB"),  # Too short
        }
        result = await engine.validate(extraction, "health")
        uin_warnings = [w for w in result.warnings if "uin" in w.field.lower()]
        assert len(uin_warnings) >= 1


# ── Check 4: Range Validation ─────────────────────────────────────────


class TestRangeValidation:
    @pytest.mark.asyncio
    async def test_health_si_below_range(self, engine):
        extraction = {"sumInsured": _cf(50000)}  # Below ₹1L min
        result = await engine.validate(extraction, "health")
        range_warnings = [w for w in result.warnings if w.check == "range"]
        assert any("sumInsured" in w.field for w in range_warnings)

    @pytest.mark.asyncio
    async def test_health_si_above_range(self, engine):
        extraction = {"sumInsured": _cf(600000000)}  # Above ₹5Cr max
        result = await engine.validate(extraction, "health")
        range_warnings = [w for w in result.warnings if w.check == "range"]
        assert any("sumInsured" in w.field for w in range_warnings)

    @pytest.mark.asyncio
    async def test_motor_idv_in_range(self, engine):
        extraction = {"idv": _cf(500000)}  # ₹5L — fine
        result = await engine.validate(extraction, "motor")
        range_warnings = [w for w in result.warnings if w.check == "range" and w.field == "idv"]
        assert len(range_warnings) == 0

    @pytest.mark.asyncio
    async def test_motor_ncb_over_65(self, engine):
        extraction = {"ncbPercentage": _cf(70)}  # Motor max 65%
        result = await engine.validate(extraction, "motor")
        range_warnings = [w for w in result.warnings if w.check == "range" and w.field == "ncbPercentage"]
        assert len(range_warnings) == 1


# ── Check 5: Confidence Scoring ───────────────────────────────────────


class TestConfidenceScoring:
    @pytest.mark.asyncio
    async def test_high_confidence_all_fields(self, engine):
        extraction = {
            "sumInsured": _cf(1000000, confidence=0.95),
            "totalPremium": _cf(25000, confidence=0.95),
            "insurerName": _cf("Star Health", confidence=0.98),
            "policyPeriodStart": _cf("2025-01-01", confidence=0.95),
            "policyPeriodEnd": _cf("2026-01-01", confidence=0.95),
        }
        result = await engine.validate(extraction, "health")
        assert result.weighted_confidence >= 0.8
        assert result.confidence == "HIGH"

    @pytest.mark.asyncio
    async def test_low_confidence_critical_field_warning(self, engine):
        extraction = {
            "sumInsured": _cf(1000000, confidence=0.3),  # Critical field, low confidence
        }
        result = await engine.validate(extraction, "health")
        conf_warnings = [w for w in result.warnings if w.check == "confidence"]
        assert len(conf_warnings) >= 1


# ── Overall Score ─────────────────────────────────────────────────────


class TestOverallScore:
    @pytest.mark.asyncio
    async def test_perfect_extraction_high_score(self, engine):
        extraction = {
            "sumInsured": _cf(1000000, confidence=0.98),
            "totalPremium": _cf(25000, confidence=0.95),
            "insurerName": _cf("Star Health", confidence=0.99),
            "policyPeriodStart": _cf("2025-01-01", confidence=0.95),
            "policyPeriodEnd": _cf("2026-01-01", confidence=0.95),
            "roomRentLimit": _cf("No limit", confidence=0.9),
            "generalCopay": _cf(0, confidence=0.95),
        }
        result = await engine.validate(extraction, "health")
        assert result.score >= 80
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_many_errors_low_score(self, engine):
        extraction = {
            "sumInsured": {"value": 0, "source_page": None, "confidence": 0.2},
            "totalPremium": {"value": -100, "source_page": None, "confidence": 0.1},
            "policyPeriodStart": _cf("2026-01-01"),
            "policyPeriodEnd": _cf("2025-01-01"),
        }
        result = await engine.validate(extraction, "health")
        assert result.score < 80
        assert len(result.errors) > 0
