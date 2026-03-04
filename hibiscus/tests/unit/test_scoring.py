"""
Unit tests for ScoringEngine — EAZR Score calculation per category.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest

from hibiscus.extraction.scoring import ScoringEngine, ScoringResult


@pytest.fixture
def engine():
    return ScoringEngine()


def _cf(value, source_page=1, confidence=0.95):
    return {"value": value, "source_page": source_page, "confidence": confidence}


# ── Health Scoring ────────────────────────────────────────────────────


class TestHealthScoring:
    @pytest.mark.asyncio
    async def test_excellent_health_policy(self, engine):
        """₹1Cr SI, no room rent cap, 0 copay, restoration, modern treatment."""
        extraction = {
            "sumInsured": _cf(1_00_00_000),
            "roomRentLimit": _cf("No limit"),
            "icuLimit": _cf("No limit"),
            "generalCopay": _cf(0),
            "restoration": _cf("100%"),
            "insurerName": _cf("Star Health"),
            "networkHospitalsCount": _cf(14000),
            "modernTreatment": _cf("Covered"),
            "consumablesCoverage": _cf(True),
            "preExistingDiseaseWaiting": _cf("24 months"),
            "specificDiseaseWaiting": _cf("12 months"),
            "coverType": _cf("Individual"),
            "totalPremium": _cf(45000),
            "ncbPercentage": _cf(50),
            "claimSettlementRatio": _cf(97),
        }
        result = await engine.score(extraction, "health")
        assert result.eazr_score >= 75
        assert "Strong" in result.verdict or "Excellent" in result.verdict
        assert len(result.components) == 4

    @pytest.mark.asyncio
    async def test_weak_health_policy(self, engine):
        """₹3L SI, room rent capped, 20% copay, no restoration."""
        extraction = {
            "sumInsured": _cf(300000),
            "roomRentLimit": _cf("₹4,000/day"),
            "generalCopay": _cf(20),
            "coverType": _cf("Individual"),
            "totalPremium": _cf(8000),
        }
        result = await engine.score(extraction, "health")
        assert result.eazr_score < 60

    @pytest.mark.asyncio
    async def test_health_family_floater_s3(self, engine):
        """Floater policy activates S3 (Family Protection)."""
        extraction = {
            "sumInsured": _cf(1000000),
            "coverType": _cf("Family Floater"),
            "totalMembersCovered": _cf(4),
            "totalPremium": _cf(20000),
            "dayCareProcedures": _cf("Covered"),
            "ambulanceCover": _cf("₹5,000"),
            "healthCheckup": _cf("Annual"),
        }
        result = await engine.score(extraction, "health")
        assert any(c.name == "Family Protection" and c.score > 0 for c in result.components)

    @pytest.mark.asyncio
    async def test_health_vfm_score(self, engine):
        extraction = {
            "sumInsured": _cf(1000000),
            "totalPremium": _cf(12000),  # ratio = 0.012 → excellent
            "roomRentLimit": _cf("No limit"),
            "generalCopay": _cf(0),
            "ncbPercentage": _cf(50),
            "restoration": _cf("100%"),
            "dayCareProcedures": _cf("Covered"),
            "ambulanceCover": _cf("Covered"),
            "ayushTreatment": _cf("Covered"),
            "healthCheckup": _cf("Covered"),
            "modernTreatment": _cf("Covered"),
        }
        result = await engine.score(extraction, "health")
        assert result.vfm_score >= 60

    @pytest.mark.asyncio
    async def test_health_zones(self, engine):
        extraction = {
            "sumInsured": _cf(2500000),
            "roomRentLimit": _cf("No limit"),
            "generalCopay": _cf(0),
            "restoration": _cf("100%"),
            "preExistingDiseaseWaiting": _cf("24 months"),
            "totalPremium": _cf(15000),
        }
        result = await engine.score(extraction, "health")
        assert result.zone_classification["roomRent"] == "green"
        assert result.zone_classification["copay"] == "green"
        assert result.zone_classification["sumInsured"] == "green"
        assert result.zone_classification["restoration"] == "green"

    @pytest.mark.asyncio
    async def test_health_red_zones(self, engine):
        extraction = {
            "sumInsured": _cf(200000),  # < ₹5L
            "generalCopay": _cf(25),  # > 15%
            "totalPremium": _cf(5000),
        }
        result = await engine.score(extraction, "health")
        assert result.zone_classification["copay"] == "red"
        assert result.zone_classification["sumInsured"] == "red"
        assert result.zone_classification["restoration"] == "red"


# ── Motor Scoring ─────────────────────────────────────────────────────


class TestMotorScoring:
    @pytest.mark.asyncio
    async def test_comprehensive_motor_good_score(self, engine):
        extraction = {
            "idv": _cf(800000),
            "zeroDepreciation": _cf(True),
            "engineProtection": _cf(True),
            "returnToInvoice": _cf(True),
            "roadsideAssistance": _cf(True),
            "consumables": _cf(True),
            "insurerName": _cf("ICICI Lombard"),
            "totalPremium": _cf(18000),
            "ncbPercentage": _cf(50),
        }
        result = await engine.score(extraction, "motor")
        assert result.eazr_score >= 70
        assert len(result.components) == 5

    @pytest.mark.asyncio
    async def test_basic_motor_low_score(self, engine):
        extraction = {
            "idv": _cf(150000),
            "totalPremium": _cf(8000),
            "ncbPercentage": _cf(0),
        }
        result = await engine.score(extraction, "motor")
        assert result.eazr_score < 60


# ── Life Scoring ──────────────────────────────────────────────────────


class TestLifeScoring:
    @pytest.mark.asyncio
    async def test_high_sa_life_policy(self, engine):
        extraction = {
            "sumAssured": _cf(1_00_00_000),
            "insurerName": _cf("HDFC Life"),
            "riders": _cf([
                {"riderName": "Critical Illness"},
                {"riderName": "Waiver of Premium"},
                {"riderName": "Accidental Death Benefit"},
            ]),
            "surrenderValue": _cf(500000),
            "accruedBonus": _cf(200000),
            "policyLoanInterestRate": _cf(9),
        }
        result = await engine.score(extraction, "life")
        assert result.eazr_score >= 70
        assert len(result.components) == 5

    @pytest.mark.asyncio
    async def test_low_sa_life_policy(self, engine):
        extraction = {
            "sumAssured": _cf(500000),
            "insurerName": _cf("Unknown Insurer"),
        }
        result = await engine.score(extraction, "life")
        assert result.eazr_score < 60


# ── Travel Scoring ────────────────────────────────────────────────────


class TestTravelScoring:
    @pytest.mark.asyncio
    async def test_good_travel_policy(self, engine):
        extraction = {
            "medicalExpenses": _cf(5000000),
            "tripCancellation": _cf(200000),
            "tripInterruption": _cf(100000),
            "flightDelay": _cf(10000),
            "emergencyMedicalEvacuation": _cf(2500000),
            "baggageLoss": _cf(50000),
            "insurerName": _cf("Bajaj Allianz"),
        }
        result = await engine.score(extraction, "travel")
        assert result.eazr_score >= 70

    @pytest.mark.asyncio
    async def test_low_medical_travel(self, engine):
        extraction = {
            "medicalExpenses": _cf(200000),
        }
        result = await engine.score(extraction, "travel")
        assert result.eazr_score < 50


# ── PA Scoring ────────────────────────────────────────────────────────


class TestPAScoring:
    @pytest.mark.asyncio
    async def test_good_pa_policy(self, engine):
        extraction = {
            "paSumInsured": _cf(5000000),
            "permanentTotalDisabilityCovered": _cf(True),
            "temporaryTotalDisabilityCovered": _cf(True),
            "medicalExpensesCovered": _cf(True),
            "educationBenefitCovered": _cf(True),
            "ambulanceChargesCovered": _cf(True),
            "insurerName": _cf("ICICI Lombard"),
        }
        result = await engine.score(extraction, "pa")
        assert result.eazr_score >= 70

    @pytest.mark.asyncio
    async def test_basic_pa_policy(self, engine):
        extraction = {
            "paSumInsured": _cf(500000),
        }
        result = await engine.score(extraction, "pa")
        assert result.eazr_score < 60


# ── Verdict and Color ─────────────────────────────────────────────────


class TestVerdict:
    @pytest.mark.asyncio
    async def test_verdict_colors(self, engine):
        # High score
        extraction = {
            "sumInsured": _cf(1_00_00_000),
            "roomRentLimit": _cf("No limit"),
            "generalCopay": _cf(0),
            "restoration": _cf("Unlimited"),
            "insurerName": _cf("Star Health"),
            "modernTreatment": _cf("Covered"),
            "consumablesCoverage": _cf(True),
            "totalPremium": _cf(40000),
            "ncbPercentage": _cf(50),
            "claimSettlementRatio": _cf(98),
            "coverType": _cf("Individual"),
            "preExistingDiseaseWaiting": _cf("Waived"),
            "specificDiseaseWaiting": _cf("Waived"),
            "networkHospitalsCount": _cf(14000),
            "icuLimit": _cf("No limit"),
        }
        result = await engine.score(extraction, "health")
        assert result.verdict_color in ("#22C55E", "#84CC16", "#EAB308", "#F97316", "#6B7280")
        assert result.verdict != ""

    @pytest.mark.asyncio
    async def test_unknown_category_defaults(self, engine):
        result = await engine.score({}, "unknown")
        assert result.eazr_score == 50
        assert result.verdict == "Unknown category"
