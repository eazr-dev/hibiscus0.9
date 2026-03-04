"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Unit tests: gap analysis — coverage gap detection and recommendation generation.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest

from hibiscus.extraction.gap_analysis import GapAnalysisEngine, GapAnalysisResult
from hibiscus.extraction.scoring import ScoringEngine, ScoringResult


@pytest.fixture
def engine():
    return GapAnalysisEngine()


@pytest.fixture
def scorer():
    return ScoringEngine()


def _cf(value, source_page=1, confidence=0.95):
    return {"value": value, "source_page": source_page, "confidence": confidence}


# ── Health Gap Analysis ───────────────────────────────────────────────


class TestHealthGaps:
    @pytest.mark.asyncio
    async def test_g001_low_si_critical(self, engine, scorer):
        """₹3L for 2 members = ₹1.5L/person → CRITICAL."""
        extraction = {
            "sumInsured": _cf(300000),
            "totalMembersCovered": _cf(2),
            "totalPremium": _cf(8000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        si_gaps = [g for g in result.gaps if g.category == "Sum Insured"]
        assert len(si_gaps) == 1
        assert si_gaps[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_g001_moderate_si_high(self, engine, scorer):
        """₹7L for 1 member → HIGH (below ₹10L/person)."""
        extraction = {
            "sumInsured": _cf(700000),
            "totalMembersCovered": _cf(1),
            "totalPremium": _cf(12000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        si_gaps = [g for g in result.gaps if g.category == "Sum Insured"]
        assert len(si_gaps) == 1
        assert si_gaps[0].severity == "HIGH"

    @pytest.mark.asyncio
    async def test_g001_adequate_si_no_gap(self, engine, scorer):
        """₹25L for 1 member → no SI gap."""
        extraction = {
            "sumInsured": _cf(2500000),
            "totalMembersCovered": _cf(1),
            "totalPremium": _cf(15000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        si_gaps = [g for g in result.gaps if g.category == "Sum Insured"]
        assert len(si_gaps) == 0

    @pytest.mark.asyncio
    async def test_g002_room_rent_restriction(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(1000000),
            "roomRentLimit": _cf("₹4,000/day"),
            "totalPremium": _cf(12000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        rr_gaps = [g for g in result.gaps if g.category == "Room Rent"]
        assert len(rr_gaps) == 1
        assert rr_gaps[0].severity == "HIGH"

    @pytest.mark.asyncio
    async def test_g002_no_room_rent_gap_unlimited(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(2500000),
            "roomRentLimit": _cf("No limit"),
            "totalPremium": _cf(15000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        rr_gaps = [g for g in result.gaps if g.category == "Room Rent"]
        assert len(rr_gaps) == 0

    @pytest.mark.asyncio
    async def test_g003_high_copay(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(2500000),
            "generalCopay": _cf(20),
            "totalPremium": _cf(10000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        copay_gaps = [g for g in result.gaps if g.category == "Co-payment"]
        assert len(copay_gaps) == 1
        assert copay_gaps[0].severity == "HIGH"

    @pytest.mark.asyncio
    async def test_g003_low_copay_severity(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(2500000),
            "generalCopay": _cf(5),
            "totalPremium": _cf(10000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        copay_gaps = [g for g in result.gaps if g.category == "Co-payment"]
        assert len(copay_gaps) == 1
        assert copay_gaps[0].severity == "LOW"

    @pytest.mark.asyncio
    async def test_g004_no_restoration(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(2500000),
            "totalPremium": _cf(15000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        rest_gaps = [g for g in result.gaps if g.category == "Restoration"]
        assert len(rest_gaps) == 1

    @pytest.mark.asyncio
    async def test_g010_no_consumables(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(2500000),
            "totalPremium": _cf(15000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        cons_gaps = [g for g in result.gaps if g.category == "Consumables"]
        assert len(cons_gaps) == 1

    @pytest.mark.asyncio
    async def test_g007_long_ped_waiting(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(2500000),
            "preExistingDiseaseWaiting": _cf("48 months"),
            "totalPremium": _cf(15000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        ped_gaps = [g for g in result.gaps if g.category == "PED Waiting"]
        assert len(ped_gaps) == 1

    @pytest.mark.asyncio
    async def test_excellent_health_few_gaps(self, engine, scorer):
        """A great policy should have very few gaps."""
        extraction = {
            "sumInsured": _cf(2500000),
            "roomRentLimit": _cf("No limit"),
            "generalCopay": _cf(0),
            "restoration": _cf("100%"),
            "modernTreatment": _cf("Covered"),
            "consumablesCoverage": _cf(True),
            "ncbPercentage": _cf(50),
            "ncbProtect": _cf(True),
            "preExistingDiseaseWaiting": _cf("24 months"),
            "totalPremium": _cf(25000),
            "totalMembersCovered": _cf(1),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        assert result.total_gaps <= 2
        assert result.critical_gaps == 0


# ── Life Gap Analysis ─────────────────────────────────────────────────


class TestLifeGaps:
    @pytest.mark.asyncio
    async def test_low_sa_critical(self, engine, scorer):
        extraction = {
            "sumAssured": _cf(1000000),
            "insurerName": _cf("LIC"),
        }
        score = await scorer.score(extraction, "life")
        result = await engine.analyze(extraction, score, "life")
        sa_gaps = [g for g in result.gaps if g.category == "Sum Assured"]
        assert len(sa_gaps) == 1
        assert sa_gaps[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_no_ci_rider(self, engine, scorer):
        extraction = {
            "sumAssured": _cf(5000000),
            "riders": _cf([{"riderName": "Waiver of Premium"}]),
            "insurerName": _cf("HDFC Life"),
        }
        score = await scorer.score(extraction, "life")
        result = await engine.analyze(extraction, score, "life")
        ci_gaps = [g for g in result.gaps if g.category == "Critical Illness Rider"]
        assert len(ci_gaps) == 1

    @pytest.mark.asyncio
    async def test_no_wop_rider(self, engine, scorer):
        extraction = {
            "sumAssured": _cf(10000000),
            "riders": _cf([{"riderName": "Critical Illness"}]),
            "insurerName": _cf("HDFC Life"),
        }
        score = await scorer.score(extraction, "life")
        result = await engine.analyze(extraction, score, "life")
        wop_gaps = [g for g in result.gaps if g.category == "Waiver of Premium"]
        assert len(wop_gaps) == 1

    @pytest.mark.asyncio
    async def test_all_riders_present(self, engine, scorer):
        extraction = {
            "sumAssured": _cf(10000000),
            "riders": _cf([
                {"riderName": "Critical Illness"},
                {"riderName": "Waiver of Premium"},
                {"riderName": "Accidental Death Benefit"},
            ]),
            "insurerName": _cf("HDFC Life"),
        }
        score = await scorer.score(extraction, "life")
        result = await engine.analyze(extraction, score, "life")
        assert result.total_gaps == 0


# ── Motor Gap Analysis ────────────────────────────────────────────────


class TestMotorGaps:
    @pytest.mark.asyncio
    async def test_no_zero_dep(self, engine, scorer):
        extraction = {
            "idv": _cf(500000),
            "totalPremium": _cf(10000),
        }
        score = await scorer.score(extraction, "motor")
        result = await engine.analyze(extraction, score, "motor")
        zd_gaps = [g for g in result.gaps if g.category == "Zero Depreciation"]
        assert len(zd_gaps) == 1
        assert zd_gaps[0].severity == "HIGH"

    @pytest.mark.asyncio
    async def test_low_pa_cover(self, engine, scorer):
        extraction = {
            "idv": _cf(500000),
            "paOwnerCover": _cf(1500000),
            "totalPremium": _cf(10000),
        }
        score = await scorer.score(extraction, "motor")
        result = await engine.analyze(extraction, score, "motor")
        pa_gaps = [g for g in result.gaps if g.category == "PA Owner Cover"]
        assert len(pa_gaps) == 1

    @pytest.mark.asyncio
    async def test_fully_loaded_motor_few_gaps(self, engine, scorer):
        extraction = {
            "idv": _cf(800000),
            "zeroDepreciation": _cf(True),
            "engineProtection": _cf(True),
            "roadsideAssistance": _cf(True),
            "consumables": _cf(True),
            "paOwnerCover": _cf(5000000),
            "totalPremium": _cf(15000),
        }
        score = await scorer.score(extraction, "motor")
        result = await engine.analyze(extraction, score, "motor")
        assert result.total_gaps <= 1  # At most missing one add-on


# ── Travel Gap Analysis ───────────────────────────────────────────────


class TestTravelGaps:
    @pytest.mark.asyncio
    async def test_low_medical_for_usa(self, engine, scorer):
        extraction = {
            "medicalExpenses": _cf(2000000),
            "destinationCountries": _cf(["United States"]),
            "totalPremium": _cf(5000),
        }
        score = await scorer.score(extraction, "travel")
        result = await engine.analyze(extraction, score, "travel")
        med_gaps = [g for g in result.gaps if g.category == "Medical Coverage"]
        assert len(med_gaps) == 1
        assert med_gaps[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_schengen_non_compliance(self, engine, scorer):
        extraction = {
            "medicalExpenses": _cf(1500000),  # < ₹30L
            "destinationCountries": _cf(["France", "Germany"]),
            "schengenCompliant": _cf(False),
            "totalPremium": _cf(3000),
        }
        score = await scorer.score(extraction, "travel")
        result = await engine.analyze(extraction, score, "travel")
        schengen_gaps = [g for g in result.gaps if g.category == "Schengen Compliance"]
        assert len(schengen_gaps) == 1
        assert schengen_gaps[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_no_evacuation(self, engine, scorer):
        extraction = {
            "medicalExpenses": _cf(5000000),
            "totalPremium": _cf(5000),
        }
        score = await scorer.score(extraction, "travel")
        result = await engine.analyze(extraction, score, "travel")
        evac_gaps = [g for g in result.gaps if g.category == "Medical Evacuation"]
        assert len(evac_gaps) == 1

    @pytest.mark.asyncio
    async def test_adventure_sports_exclusion(self, engine, scorer):
        extraction = {
            "medicalExpenses": _cf(5000000),
            "adventureSportsExclusion": _cf(True),
            "emergencyMedicalEvacuation": _cf(2500000),
            "totalPremium": _cf(5000),
        }
        score = await scorer.score(extraction, "travel")
        result = await engine.analyze(extraction, score, "travel")
        adv_gaps = [g for g in result.gaps if g.category == "Adventure Sports"]
        assert len(adv_gaps) == 1


# ── PA Gap Analysis ───────────────────────────────────────────────────


class TestPAGaps:
    @pytest.mark.asyncio
    async def test_low_si(self, engine, scorer):
        extraction = {
            "paSumInsured": _cf(500000),
            "totalPremium": _cf(500),
        }
        score = await scorer.score(extraction, "pa")
        result = await engine.analyze(extraction, score, "pa")
        si_gaps = [g for g in result.gaps if g.category == "Sum Insured"]
        assert len(si_gaps) == 1
        assert si_gaps[0].severity == "HIGH"

    @pytest.mark.asyncio
    async def test_no_ttd(self, engine, scorer):
        extraction = {
            "paSumInsured": _cf(2500000),
            "totalPremium": _cf(1500),
        }
        score = await scorer.score(extraction, "pa")
        result = await engine.analyze(extraction, score, "pa")
        ttd_gaps = [g for g in result.gaps if g.category == "Temporary Disability"]
        assert len(ttd_gaps) == 1

    @pytest.mark.asyncio
    async def test_no_medical_expenses(self, engine, scorer):
        extraction = {
            "paSumInsured": _cf(2500000),
            "totalPremium": _cf(1500),
        }
        score = await scorer.score(extraction, "pa")
        result = await engine.analyze(extraction, score, "pa")
        med_gaps = [g for g in result.gaps if g.category == "Medical Expenses"]
        assert len(med_gaps) == 1


# ── Overall Risk Classification ───────────────────────────────────────


class TestOverallRisk:
    @pytest.mark.asyncio
    async def test_critical_risk(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(200000),
            "totalMembersCovered": _cf(4),
            "totalPremium": _cf(5000),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        assert result.overall_risk == "CRITICAL"

    @pytest.mark.asyncio
    async def test_low_risk(self, engine, scorer):
        extraction = {
            "sumInsured": _cf(5000000),
            "roomRentLimit": _cf("No limit"),
            "generalCopay": _cf(0),
            "restoration": _cf("100%"),
            "modernTreatment": _cf("Covered"),
            "consumablesCoverage": _cf(True),
            "ncbPercentage": _cf(50),
            "ncbProtect": _cf(True),
            "preExistingDiseaseWaiting": _cf("24 months"),
            "totalPremium": _cf(30000),
            "totalMembersCovered": _cf(1),
        }
        score = await scorer.score(extraction, "health")
        result = await engine.analyze(extraction, score, "health")
        assert result.overall_risk == "LOW"
