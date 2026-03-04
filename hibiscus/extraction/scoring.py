"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Extraction scoring — computes coverage adequacy, value-for-money, and EAZR protection scores.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from hibiscus.extraction.schemas.common import lookup_csr, lookup_network_hospitals
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScoreComponent:
    name: str
    score: int  # 0-100
    weight: float  # 0.0-1.0
    details: str = ""


@dataclass
class ScoringResult:
    eazr_score: int = 0  # 0-100 composite
    verdict: str = ""
    verdict_color: str = ""
    components: list[ScoreComponent] = field(default_factory=list)
    vfm_score: int = 0
    coverage_score: int = 0
    claim_readiness_score: int = 0
    zone_classification: dict = field(default_factory=dict)


# ── Helpers ──────────────────────────────────────────────────────────


def _val(extraction: dict, field_name: str) -> Any:
    """Get bare value from extraction dict."""
    f = extraction.get(field_name, {})
    return f.get("value") if isinstance(f, dict) else None


def _num(extraction: dict, field_name: str) -> float:
    """Get numeric value, returns 0 on failure."""
    v = _val(extraction, field_name)
    if v is None:
        return 0.0
    try:
        return float(str(v).replace(",", "").replace("₹", ""))
    except (ValueError, TypeError):
        return 0.0


def _bool(extraction: dict, field_name: str) -> Optional[bool]:
    """Get boolean value."""
    v = _val(extraction, field_name)
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).lower()
    if s in ("true", "yes", "covered", "available", "included"):
        return True
    if s in ("false", "no", "not covered", "not available", "excluded"):
        return False
    return None


def _is_room_rent_unlimited(room_str: str) -> bool:
    """Check if room rent is unlimited."""
    if not room_str:
        return False
    lower = str(room_str).lower()
    return any(kw in lower for kw in [
        "no limit", "unlimited", "no cap", "no restriction",
        "all categories", "all room categories", "single private",
    ])


def _clamp(val: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, round(val)))


def _label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Strong"
    if score >= 60:
        return "Good"
    if score >= 45:
        return "Adequate"
    if score >= 30:
        return "Moderate"
    return "Weak"


def _verdict(score: int) -> tuple[str, str]:
    """Return (verdict_text, color_hex)."""
    if score >= 90:
        return "Excellent Protection", "#22C55E"
    if score >= 75:
        return "Strong Protection", "#84CC16"
    if score >= 60:
        return "Adequate Protection", "#EAB308"
    if score >= 40:
        return "Moderate Protection", "#F97316"
    return "Needs Attention", "#6B7280"


class ScoringEngine:
    """Category-specific EAZR score calculation."""

    async def score(
        self,
        extraction: dict[str, Any],
        category: str,
        user_profile: Optional[dict] = None,
    ) -> ScoringResult:
        """Calculate EAZR Score for extracted policy data."""

        if category == "health":
            result = self._score_health(extraction, user_profile)
        elif category == "life":
            result = self._score_life(extraction, user_profile)
        elif category == "motor":
            result = self._score_motor(extraction, user_profile)
        elif category == "travel":
            result = self._score_travel(extraction, user_profile)
        elif category == "pa":
            result = self._score_pa(extraction, user_profile)
        else:
            result = ScoringResult(eazr_score=50, verdict="Unknown category")

        logger.info(
            "scoring_complete",
            category=category,
            eazr_score=result.eazr_score,
            verdict=result.verdict,
            vfm=result.vfm_score,
        )

        return result

    # ── HEALTH SCORING ──────────────────────────────────────────────

    def _score_health(self, e: dict, profile: Optional[dict]) -> ScoringResult:
        """
        Health: 4-component system (from botproject protection_score_calculator)
        S1: Emergency Readiness (30%)
        S2: Critical Illness Preparedness (25%)
        S3: Family Protection (25%) — floater only
        S4: Coverage Stability (20%)
        """
        components = []

        # S1: Emergency Hospitalization Readiness
        s1 = self._health_s1(e)
        components.append(ScoreComponent("Emergency Readiness", s1, 0.30))

        # S2: Critical Illness Preparedness
        s2 = self._health_s2(e)
        components.append(ScoreComponent("Critical Illness", s2, 0.25))

        # S3: Family Protection (floater only)
        cover_type = str(_val(e, "coverType") or "").lower()
        policy_type = str(_val(e, "policyType") or "").lower()
        is_floater = "floater" in cover_type or "floater" in policy_type
        if is_floater:
            s3 = self._health_s3(e)
            components.append(ScoreComponent("Family Protection", s3, 0.25))
        else:
            components.append(ScoreComponent("Family Protection", 70, 0.25, "N/A for individual"))

        # S4: Coverage Stability
        s4 = self._health_s4(e)
        components.append(ScoreComponent("Coverage Stability", s4, 0.20))

        # Composite
        eazr = _clamp(sum(c.score * c.weight for c in components))
        vfm = self._health_vfm(e)
        zone = self._health_zones(e)

        verdict_text, color = _verdict(eazr)
        return ScoringResult(
            eazr_score=eazr,
            verdict=verdict_text,
            verdict_color=color,
            components=components,
            vfm_score=vfm,
            coverage_score=s1,
            claim_readiness_score=s4,
            zone_classification=zone,
        )

    def _health_s1(self, e: dict) -> int:
        """Emergency Hospitalization Readiness (100 pts)."""
        score = 0

        # Sum Insured adequacy (25 pts)
        si = _num(e, "sumInsured")
        if si >= 2_50_00_000:
            score += 25
        elif si >= 1_50_00_000:
            score += 23
        elif si >= 1_00_00_000:
            score += 21
        elif si >= 50_00_000:
            score += 17
        elif si >= 25_00_000:
            score += 12
        elif si >= 10_00_000:
            score += 8
        elif si >= 5_00_000:
            score += 5
        else:
            score += 2

        # Room rent (20 pts)
        room = str(_val(e, "roomRentLimit") or "")
        if _is_room_rent_unlimited(room):
            score += 20
        elif room:
            score += 10
        else:
            score += 10  # Not specified = neutral

        # ICU (15 pts)
        icu = _val(e, "icuLimit")
        if icu and _is_room_rent_unlimited(str(icu)):
            score += 15
        elif icu:
            score += 8
        else:
            score += 10

        # Network strength (15 pts)
        hospitals = _num(e, "networkHospitalsCount")
        if hospitals == 0:
            # Fallback: lookup from insurer name
            insurer = str(_val(e, "insurerName") or "")
            fallback = lookup_network_hospitals(insurer)
            hospitals = fallback or 0

        if hospitals >= 10_000:
            score += 15
        elif hospitals >= 5_000:
            score += 13
        elif hospitals >= 2_000:
            score += 11
        elif hospitals >= 500:
            score += 8
        elif hospitals > 0:
            score += 5
        elif _bool(e, "cashlessFacility"):
            score += 5
        else:
            score += 3

        # Restoration (10 pts)
        restoration = _val(e, "restoration")
        if restoration:
            r_str = str(restoration).lower()
            if "unlimited" in r_str:
                score += 10
            elif "100%" in r_str or restoration is True:
                score += 8
            else:
                score += 7
        else:
            score += 0

        # Copay (5 pts)
        copay = _num(e, "generalCopay")
        if copay == 0:
            score += 5
        elif copay <= 10:
            score += 3
        elif copay <= 20:
            score += 1

        return _clamp(score)

    def _health_s2(self, e: dict) -> int:
        """Critical Illness Preparedness (100 pts)."""
        score = 0

        # Modern treatment (25 pts)
        modern = _val(e, "modernTreatment")
        if modern:
            m_str = str(modern).lower()
            if "covered" in m_str or modern is True:
                score += 25
            else:
                score += 15
        else:
            score += 0

        # CI coverage via SI (20 pts)
        si = _num(e, "sumInsured")
        if si >= 1_00_00_000:
            score += 20
        elif si >= 50_00_000:
            score += 15
        elif si >= 25_00_000:
            score += 10
        else:
            score += 3

        # Waiting periods (20 pts)
        ped = str(_val(e, "preExistingDiseaseWaiting") or "").lower()
        if "waived" in ped or "no waiting" in ped:
            score += 12
        elif "12" in ped or "1 year" in ped:
            score += 10
        elif "24" in ped or "2 year" in ped:
            score += 7
        elif "36" in ped or "3 year" in ped:
            score += 4
        elif "48" in ped or "4 year" in ped:
            score += 2
        else:
            score += 5

        specific = str(_val(e, "specificDiseaseWaiting") or "").lower()
        if "waived" in specific or "no waiting" in specific:
            score += 8
        elif "12" in specific or "1 year" in specific:
            score += 6
        elif "24" in specific or "2 year" in specific:
            score += 4
        else:
            score += 4

        # Sub-limits (20 pts)
        sub_limit_count = sum(
            1 for f in ["cataractLimit", "jointReplacementLimit",
                        "internalProsthesisLimit", "kidneyStoneLimit",
                        "gallStoneLimit", "modernTreatmentLimit"]
            if _val(e, f) is not None
        )
        if sub_limit_count == 0:
            score += 20
        elif sub_limit_count <= 2:
            score += 14
        elif sub_limit_count <= 4:
            score += 8
        else:
            score += 4

        # Consumables (15 pts)
        consumables = _bool(e, "consumablesCoverage")
        if consumables:
            score += 15

        return _clamp(score)

    def _health_s3(self, e: dict) -> int:
        """Family Protection (100 pts, floater only)."""
        score = 0

        # Member count vs SI ratio (25 pts)
        si = _num(e, "sumInsured")
        members = _num(e, "totalMembersCovered") or 1
        per_member = si / max(members, 1)
        if per_member >= 50_00_000:
            score += 25
        elif per_member >= 25_00_000:
            score += 20
        elif per_member >= 10_00_000:
            score += 15
        elif per_member >= 5_00_000:
            score += 10
        else:
            score += 5

        # Per-member adequacy (25 pts)
        if si >= 1_50_00_000:
            score += 25
        elif si >= 1_00_00_000:
            score += 20
        elif si >= 50_00_000:
            score += 15
        elif si >= 25_00_000:
            score += 10
        else:
            score += 5

        # Maternity (20 pts)
        maternity = _val(e, "maternityWaiting")
        if maternity:
            m_str = str(maternity).lower()
            if "no waiting" in m_str or "covered" in m_str:
                score += 20
            elif "9" in m_str or "12" in m_str:
                score += 16
            elif "24" in m_str:
                score += 12
            else:
                score += 10
        else:
            score += 15  # N/A

        # Day care + coverage features (15 pts)
        if _val(e, "dayCareProcedures"):
            score += 8
        if _val(e, "ambulanceCover"):
            score += 4
        if _val(e, "healthCheckup"):
            score += 3

        # Coverage continuity (15 pts)
        years = _num(e, "continuousCoverageYears")
        if years >= 5:
            score += 15
        elif years >= 3:
            score += 12
        elif years >= 1:
            score += 6
        elif _val(e, "insuredSinceDate"):
            score += 7
        else:
            score += 5

        return _clamp(score)

    def _health_s4(self, e: dict) -> int:
        """Coverage Stability (100 pts)."""
        score = 0

        # CSR (25 pts)
        csr = _num(e, "claimSettlementRatio")
        if csr == 0:
            insurer = str(_val(e, "insurerName") or "")
            csr = lookup_csr(insurer) or 0

        if csr >= 97:
            score += 25
        elif csr >= 95:
            score += 22
        elif csr >= 90:
            score += 18
        elif csr >= 85:
            score += 12
        elif csr > 0:
            score += 6
        else:
            score += 10  # Unknown

        # NCB/Cumulative Bonus (25 pts)
        ncb = _num(e, "ncbPercentage")
        if ncb == 0:
            # Check cumulative bonus
            cb = _num(e, "cumulativeBonusAmount")
            si = _num(e, "sumInsured")
            if cb > 0 and si > 0:
                ncb = (cb / si) * 100

        if ncb >= 50:
            score += 25
        elif ncb >= 25:
            score += 18
        elif ncb > 0:
            score += 10
        else:
            score += 3

        # Renewability (25 pts) — assume lifetime if IRDAI compliant
        score += 20

        # Premium vs coverage value (25 pts)
        si = _num(e, "sumInsured")
        premium = _num(e, "totalPremium")
        if si > 0 and premium > 0:
            ratio = premium / si
            if ratio <= 0.01:
                score += 25
            elif ratio <= 0.02:
                score += 20
            elif ratio <= 0.03:
                score += 15
            elif ratio <= 0.05:
                score += 10
            else:
                score += 5
        else:
            score += 10

        return _clamp(score)

    def _health_vfm(self, e: dict) -> int:
        """Health Value for Money score (0-100)."""
        score = 0

        # Premium-to-SI ratio (35 pts)
        si = _num(e, "sumInsured")
        premium = _num(e, "totalPremium")
        if si > 0 and premium > 0:
            ratio = premium / si
            if ratio <= 0.01:
                score += 35
            elif ratio <= 0.02:
                score += 28
            elif ratio <= 0.03:
                score += 20
            elif ratio <= 0.05:
                score += 12
            else:
                score += 5

        # Feature count (30 pts)
        features = sum(1 for f in [
            "restoration", "dayCareProcedures", "ambulanceCover",
            "ayushTreatment", "healthCheckup", "domiciliaryHospitalization",
            "preHospitalization", "postHospitalization", "modernTreatment",
        ] if _val(e, f) is not None)
        score += min(features * 3, 30)

        # Room rent (15 pts)
        room = str(_val(e, "roomRentLimit") or "")
        if _is_room_rent_unlimited(room):
            score += 15
        elif room:
            score += 8
        else:
            score += 5

        # Copay (10 pts)
        copay = _num(e, "generalCopay")
        if copay == 0:
            score += 10
        elif copay <= 10:
            score += 6
        elif copay <= 20:
            score += 3

        # NCB (10 pts)
        ncb = _num(e, "ncbPercentage")
        if ncb >= 50:
            score += 10
        elif ncb >= 25:
            score += 6
        elif ncb > 0:
            score += 3

        return _clamp(score)

    def _health_zones(self, e: dict) -> dict:
        """4-zone classification for health features."""
        zones = {}

        # Room rent
        room = str(_val(e, "roomRentLimit") or "")
        if _is_room_rent_unlimited(room):
            zones["roomRent"] = "green"
        elif room:
            zones["roomRent"] = "lightGreen"
        else:
            zones["roomRent"] = "amber"

        # Copay
        copay = _num(e, "generalCopay")
        if copay == 0:
            zones["copay"] = "green"
        elif copay <= 5:
            zones["copay"] = "lightGreen"
        elif copay <= 15:
            zones["copay"] = "amber"
        else:
            zones["copay"] = "red"

        # Sum insured
        si = _num(e, "sumInsured")
        if si >= 25_00_000:
            zones["sumInsured"] = "green"
        elif si >= 10_00_000:
            zones["sumInsured"] = "lightGreen"
        elif si >= 5_00_000:
            zones["sumInsured"] = "amber"
        else:
            zones["sumInsured"] = "red"

        # Restoration
        restoration = _val(e, "restoration")
        if restoration:
            r_str = str(restoration).lower()
            if "100%" in r_str or "full" in r_str or restoration is True:
                zones["restoration"] = "green"
            else:
                zones["restoration"] = "lightGreen"
        else:
            zones["restoration"] = "red"

        # PED Waiting
        ped = str(_val(e, "preExistingDiseaseWaiting") or "").lower()
        if "waived" in ped or _num(e, "continuousCoverageYears") >= 8:
            zones["pedWaiting"] = "green"
        elif "24" in ped or "2 year" in ped:
            zones["pedWaiting"] = "green"
        elif "36" in ped or "3 year" in ped:
            zones["pedWaiting"] = "lightGreen"
        elif "48" in ped or "4 year" in ped:
            zones["pedWaiting"] = "amber"
        else:
            zones["pedWaiting"] = "amber"

        return zones

    # ── LIFE SCORING ─────────────────────────────────────────────────

    def _score_life(self, e: dict, profile: Optional[dict]) -> ScoringResult:
        """Life: Coverage Adequacy (35%), Policy Value (25%), Insurer (20%), Riders (10%), Flexibility (10%)."""
        components = []

        # Coverage adequacy (35%)
        sa = _num(e, "sumAssured")
        if sa >= 1_00_00_000:
            s = 90
        elif sa >= 50_00_000:
            s = 75
        elif sa >= 25_00_000:
            s = 60
        elif sa >= 10_00_000:
            s = 45
        else:
            s = 30
        components.append(ScoreComponent("Coverage Adequacy", s, 0.35))

        # Policy value (25%)
        sv = _num(e, "surrenderValue")
        bonus = _num(e, "accruedBonus")
        s = 50
        if sv > 0 or bonus > 0:
            s = 70
        components.append(ScoreComponent("Policy Value", s, 0.25))

        # Insurer quality (20%)
        insurer = str(_val(e, "insurerName") or "")
        csr = lookup_csr(insurer) or 90
        if csr >= 97:
            s = 95
        elif csr >= 95:
            s = 85
        elif csr >= 90:
            s = 70
        else:
            s = 55
        components.append(ScoreComponent("Insurer Quality", s, 0.20))

        # Riders (10%)
        riders = _val(e, "riders")
        rider_count = len(riders) if isinstance(riders, list) else 0
        s = min(50 + rider_count * 15, 100)
        components.append(ScoreComponent("Rider Coverage", s, 0.10))

        # Flexibility (10%)
        has_loan = _num(e, "policyLoanInterestRate") > 0
        has_partial = _val(e, "partialWithdrawal") is not None
        s = 50 + (20 if has_loan else 0) + (20 if has_partial else 0)
        components.append(ScoreComponent("Flexibility", _clamp(s), 0.10))

        eazr = _clamp(sum(c.score * c.weight for c in components))
        verdict_text, color = _verdict(eazr)
        return ScoringResult(
            eazr_score=eazr, verdict=verdict_text, verdict_color=color,
            components=components, vfm_score=0,
        )

    # ── MOTOR SCORING ────────────────────────────────────────────────

    def _score_motor(self, e: dict, profile: Optional[dict]) -> ScoringResult:
        """Motor: IDV (30%), Coverage (25%), Insurer (20%), Premium (15%), Claims (10%)."""
        components = []

        # IDV adequacy (30%)
        idv = _num(e, "idv")
        if idv >= 10_00_000:
            s = 90
        elif idv >= 5_00_000:
            s = 75
        elif idv >= 2_00_000:
            s = 60
        else:
            s = 40
        components.append(ScoreComponent("IDV Adequacy", s, 0.30))

        # Coverage completeness (25%)
        addons = sum(1 for f in [
            "zeroDepreciation", "engineProtection", "returnToInvoice",
            "roadsideAssistance", "consumables", "tyreCover", "keyCover",
        ] if _bool(e, f))
        s = min(30 + addons * 10, 100)
        components.append(ScoreComponent("Coverage Completeness", s, 0.25))

        # Insurer quality (20%)
        insurer = str(_val(e, "insurerName") or "")
        csr = lookup_csr(insurer) or 90
        if csr >= 97:
            s = 95
        elif csr >= 95:
            s = 85
        elif csr >= 90:
            s = 70
        else:
            s = 55
        components.append(ScoreComponent("Insurer Quality", s, 0.20))

        # Premium value (15%)
        premium = _num(e, "totalPremium")
        if idv > 0 and premium > 0:
            ratio = premium / idv
            if ratio <= 0.02:
                s = 90
            elif ratio <= 0.03:
                s = 75
            elif ratio <= 0.05:
                s = 60
            elif ratio <= 0.08:
                s = 45
            else:
                s = 30
        else:
            s = 50
        components.append(ScoreComponent("Premium Value", s, 0.15))

        # NCB (10%)
        ncb = _num(e, "ncbPercentage")
        if ncb >= 50:
            s = 95
        elif ncb >= 25:
            s = 70
        elif ncb > 0:
            s = 50
        else:
            s = 30
        components.append(ScoreComponent("NCB", s, 0.10))

        eazr = _clamp(sum(c.score * c.weight for c in components))
        verdict_text, color = _verdict(eazr)
        return ScoringResult(
            eazr_score=eazr, verdict=verdict_text, verdict_color=color,
            components=components, vfm_score=0,
        )

    # ── TRAVEL SCORING ───────────────────────────────────────────────

    def _score_travel(self, e: dict, profile: Optional[dict]) -> ScoringResult:
        """Travel: Medical (35%), Trip Protection (25%), Baggage (15%), Insurer (15%), Value (10%)."""
        components = []

        # Medical coverage (35%)
        medical = _num(e, "medicalExpenses")
        if medical >= 50_00_000:
            s = 95
        elif medical >= 25_00_000:
            s = 80
        elif medical >= 10_00_000:
            s = 60
        elif medical >= 5_00_000:
            s = 40
        else:
            s = 20
        components.append(ScoreComponent("Medical Coverage", s, 0.35))

        # Trip protection (25%)
        has_cancel = _num(e, "tripCancellation") > 0
        has_interrupt = _num(e, "tripInterruption") > 0
        has_delay = _num(e, "flightDelay") > 0
        has_evac = _num(e, "emergencyMedicalEvacuation") > 0
        s = 20 + (20 if has_cancel else 0) + (20 if has_interrupt else 0) + (20 if has_delay else 0) + (20 if has_evac else 0)
        components.append(ScoreComponent("Trip Protection", _clamp(s), 0.25))

        # Baggage (15%)
        baggage = _num(e, "baggageLoss")
        s = 70 if baggage > 0 else 30
        components.append(ScoreComponent("Baggage Coverage", s, 0.15))

        # Insurer (15%)
        insurer = str(_val(e, "insurerName") or "")
        csr = lookup_csr(insurer) or 90
        s = 85 if csr >= 95 else 70 if csr >= 90 else 55
        components.append(ScoreComponent("Insurer Quality", s, 0.15))

        # Value (10%)
        components.append(ScoreComponent("Value", 60, 0.10))

        eazr = _clamp(sum(c.score * c.weight for c in components))
        verdict_text, color = _verdict(eazr)
        return ScoringResult(
            eazr_score=eazr, verdict=verdict_text, verdict_color=color,
            components=components, vfm_score=0,
        )

    # ── PA SCORING ───────────────────────────────────────────────────

    def _score_pa(self, e: dict, profile: Optional[dict]) -> ScoringResult:
        """PA: Coverage (35%), Benefits (30%), Insurer (20%), Value (15%)."""
        components = []

        # Coverage (35%)
        si = _num(e, "paSumInsured")
        if si >= 50_00_000:
            s = 90
        elif si >= 25_00_000:
            s = 75
        elif si >= 10_00_000:
            s = 60
        else:
            s = 40
        components.append(ScoreComponent("Coverage", s, 0.35))

        # Benefits (30%)
        benefits = sum(1 for f in [
            "permanentTotalDisabilityCovered", "temporaryTotalDisabilityCovered",
            "medicalExpensesCovered", "educationBenefitCovered",
            "ambulanceChargesCovered", "transportMortalRemainsCovered",
        ] if _bool(e, f))
        s = min(30 + benefits * 12, 100)
        components.append(ScoreComponent("Benefits", s, 0.30))

        # Insurer (20%)
        insurer = str(_val(e, "insurerName") or "")
        csr = lookup_csr(insurer) or 90
        s = 85 if csr >= 95 else 70 if csr >= 90 else 55
        components.append(ScoreComponent("Insurer Quality", s, 0.20))

        # Value (15%)
        components.append(ScoreComponent("Value", 60, 0.15))

        eazr = _clamp(sum(c.score * c.weight for c in components))
        verdict_text, color = _verdict(eazr)
        return ScoringResult(
            eazr_score=eazr, verdict=verdict_text, verdict_color=color,
            components=components, vfm_score=0,
        )


# Singleton
scoring_engine = ScoringEngine()
