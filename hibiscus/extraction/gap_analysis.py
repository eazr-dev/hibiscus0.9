"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Gap analysis — identifies missing coverage, exclusion risks, and improvement opportunities.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from hibiscus.extraction.scoring import ScoringResult, _val, _num, _bool, _is_room_rent_unlimited
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Gap:
    gap_type: str  # COVERAGE_GAP, SUB_LIMIT_TRAP, MISSING_COVERAGE, etc.
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    category: str  # Specific coverage area
    description: str  # Plain language explanation
    impact: str  # Quantified financial impact
    recommendation: str  # Specific action
    estimated_cost: Optional[int] = None  # ₹ cost to fix


@dataclass
class GapAnalysisResult:
    gaps: list[Gap] = field(default_factory=list)
    total_gaps: int = 0
    critical_gaps: int = 0
    high_gaps: int = 0
    overall_risk: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL


class GapAnalysisEngine:
    """Category-specific coverage gap detection."""

    async def analyze(
        self,
        extraction: dict[str, Any],
        score: ScoringResult,
        category: str,
        user_profile: Optional[dict] = None,
    ) -> GapAnalysisResult:
        """Identify coverage gaps based on extraction and scoring."""

        if category == "health":
            result = self._analyze_health(extraction, score, user_profile)
        elif category == "life":
            result = self._analyze_life(extraction, score, user_profile)
        elif category == "motor":
            result = self._analyze_motor(extraction, score, user_profile)
        elif category == "travel":
            result = self._analyze_travel(extraction, score, user_profile)
        elif category == "pa":
            result = self._analyze_pa(extraction, score, user_profile)
        else:
            result = GapAnalysisResult()

        result.total_gaps = len(result.gaps)
        result.critical_gaps = sum(1 for g in result.gaps if g.severity == "CRITICAL")
        result.high_gaps = sum(1 for g in result.gaps if g.severity == "HIGH")

        if result.critical_gaps > 0:
            result.overall_risk = "CRITICAL"
        elif result.high_gaps > 0:
            result.overall_risk = "HIGH"
        elif result.total_gaps > 3:
            result.overall_risk = "MEDIUM"

        logger.info(
            "gap_analysis_complete",
            category=category,
            total_gaps=result.total_gaps,
            critical=result.critical_gaps,
            overall_risk=result.overall_risk,
        )

        return result

    # ── HEALTH GAP ANALYSIS ──────────────────────────────────────────

    def _analyze_health(
        self, e: dict, score: ScoringResult, profile: Optional[dict]
    ) -> GapAnalysisResult:
        result = GapAnalysisResult()

        si = _num(e, "sumInsured")
        members = max(_num(e, "totalMembersCovered"), 1)

        # G001: Sum Insured Inadequacy
        per_member = si / members
        if per_member < 5_00_000:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="CRITICAL",
                category="Sum Insured",
                description=f"Sum insured of ₹{si:,.0f} for {int(members)} members = ₹{per_member:,.0f}/person. A single major surgery can cost ₹5-15 lakhs.",
                impact=f"In a ₹10L hospitalization, you'd pay ₹{max(0, 10_00_000 - per_member):,.0f} out of pocket.",
                recommendation=f"Increase to at least ₹{max(10_00_000, int(members) * 5_00_000):,.0f} or add a Super Top-up of ₹25L.",
                estimated_cost=5000,
            ))
        elif per_member < 10_00_000:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="HIGH",
                category="Sum Insured",
                description=f"₹{per_member:,.0f} per person is moderate but may fall short for major procedures in metro hospitals.",
                impact="Critical surgeries (cardiac, transplant) can cost ₹15-30L in metros.",
                recommendation=f"Consider a Super Top-up of ₹25-50L for ₹3,000-6,000/year.",
                estimated_cost=4000,
            ))

        # G002: Room Rent Restriction
        room = str(_val(e, "roomRentLimit") or "")
        if room and not _is_room_rent_unlimited(room):
            result.gaps.append(Gap(
                gap_type="SUB_LIMIT_TRAP",
                severity="HIGH",
                category="Room Rent",
                description=f"Room rent is limited to '{room}'. This triggers proportional deduction on the ENTIRE bill, not just room charges.",
                impact="A ₹5L bill in a ₹8,000/day room with ₹4,000 limit → 50% deduction → you pay ₹2.5L.",
                recommendation="Upgrade to a plan with no room rent capping, or negotiate at claim time.",
                estimated_cost=3000,
            ))

        # G003: High Copay
        copay = _num(e, "generalCopay")
        if copay > 0:
            severity = "HIGH" if copay >= 20 else "MEDIUM" if copay >= 10 else "LOW"
            result.gaps.append(Gap(
                gap_type="SUB_LIMIT_TRAP",
                severity=severity,
                category="Co-payment",
                description=f"{int(copay)}% co-payment means you pay {int(copay)}% of every claim from your pocket.",
                impact=f"On a ₹5L claim, you pay ₹{int(5_00_000 * copay / 100):,} out of pocket.",
                recommendation="Look for plans with 0% copay. Some insurers offer copay waiver add-ons.",
                estimated_cost=2000,
            ))

        # G004: No Restoration Benefit
        restoration = _val(e, "restoration")
        if not restoration:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Restoration",
                description="No restoration benefit. If SI is exhausted in one claim, no coverage for rest of the year.",
                impact=f"After using ₹{si:,.0f} SI in one hospitalization, family has zero coverage until renewal.",
                recommendation="Choose a plan with 100% restoration or add a Super Top-up.",
                estimated_cost=2000,
            ))

        # G005: Missing Critical Illness
        # Check if SI is low and no CI rider
        if si < 25_00_000 and not _val(e, "modernTreatment"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Critical Illness",
                description="No dedicated critical illness coverage. Cancer treatment can cost ₹15-30L.",
                impact="If diagnosed with cancer, treatment costs may far exceed your SI.",
                recommendation="Add a Critical Illness rider or standalone CI policy for ₹25-50L.",
                estimated_cost=8000,
            ))

        # G006: No NCB Protection
        ncb = _num(e, "ncbPercentage")
        ncb_protect = _bool(e, "ncbProtect")
        if ncb > 0 and not ncb_protect:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="LOW",
                category="NCB Protection",
                description=f"You have {int(ncb)}% NCB but no NCB protection. One claim resets your bonus to 0%.",
                impact=f"Losing {int(ncb)}% NCB = losing ₹{int(si * ncb / 100):,} of effective coverage.",
                recommendation="Add NCB protection add-on (typically ₹500-1,500/year).",
                estimated_cost=1000,
            ))

        # G007: Long PED Waiting Period
        ped = str(_val(e, "preExistingDiseaseWaiting") or "").lower()
        if "48" in ped or "4 year" in ped:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="MEDIUM",
                category="PED Waiting",
                description="48-month (4 year) PED waiting period. Pre-existing conditions won't be covered for 4 years.",
                impact="Any hospitalization for declared PED in 4 years = 100% out of pocket.",
                recommendation="Consider porting to an insurer with 24-36 month PED waiting.",
                estimated_cost=0,
            ))

        # G008: No Personal Accident Cover
        # This is a gap identified at portfolio level — skip if just analyzing one policy

        # G009: Disease-specific Sub-limits
        sub_limits = [f for f in ["cataractLimit", "jointReplacementLimit",
                                   "internalProsthesisLimit", "kidneyStoneLimit",
                                   "gallStoneLimit"] if _val(e, f)]
        if len(sub_limits) >= 3:
            result.gaps.append(Gap(
                gap_type="SUB_LIMIT_TRAP",
                severity="MEDIUM",
                category="Sub-limits",
                description=f"Policy has {len(sub_limits)} disease-specific sub-limits: {', '.join(sub_limits)}.",
                impact="Claims for these conditions will be capped regardless of actual costs.",
                recommendation="Look for plans without disease-wise sub-limits or with higher limits.",
                estimated_cost=3000,
            ))

        # G010: No Consumables Coverage
        if not _bool(e, "consumablesCoverage"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="LOW",
                category="Consumables",
                description="No consumables coverage. Gloves, syringes, PPE, medicines used during surgery are excluded.",
                impact="Consumables can be 5-15% of hospital bill = ₹25,000-75,000 on a ₹5L bill.",
                recommendation="Add consumables cover add-on (typically ₹500-2,000/year).",
                estimated_cost=1000,
            ))

        return result

    # ── LIFE GAP ANALYSIS ────────────────────────────────────────────

    def _analyze_life(
        self, e: dict, score: ScoringResult, profile: Optional[dict]
    ) -> GapAnalysisResult:
        result = GapAnalysisResult()

        sa = _num(e, "sumAssured")

        # Inadequate sum assured
        if sa < 50_00_000:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="CRITICAL",
                category="Sum Assured",
                description=f"Sum assured of ₹{sa:,.0f} may be inadequate. Rule of thumb: 10-15x annual income.",
                impact="If income is ₹5L/year, family needs ₹50-75L coverage to maintain lifestyle.",
                recommendation="Consider a pure term plan for ₹1Cr+ at affordable premiums.",
                estimated_cost=12000,
            ))

        # No critical illness rider
        riders = _val(e, "riders") or []
        has_ci = any("critical" in str(r.get("riderName", "")).lower() for r in riders if isinstance(r, dict))
        if not has_ci:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="HIGH",
                category="Critical Illness Rider",
                description="No critical illness rider. Critical illness diagnosis (cancer, heart attack) won't trigger any payout.",
                impact="35% of life insurance claims are CI-related. Without CI rider, only death triggers payout.",
                recommendation="Add CI rider for ₹25-50L (costs ₹2,000-5,000/year).",
                estimated_cost=3000,
            ))

        # No waiver of premium
        has_wop = any("waiver" in str(r.get("riderName", "")).lower() for r in riders if isinstance(r, dict))
        if not has_wop:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Waiver of Premium",
                description="No waiver of premium rider. If disabled, you must continue paying premiums.",
                impact="Disability + premium payments = double financial burden on family.",
                recommendation="Add WOP rider (typically ₹500-1,500/year).",
                estimated_cost=1000,
            ))

        # No accidental death benefit
        has_adb = any("accident" in str(r.get("riderName", "")).lower() for r in riders if isinstance(r, dict))
        if not has_adb:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Accidental Death Benefit",
                description="No accidental death benefit rider. Accidental death pays same as natural death.",
                impact="Road accidents are leading cause of death for 18-45 age group. ADB doubles payout.",
                recommendation="Add ADB rider (typically ₹500-1,000/year).",
                estimated_cost=700,
            ))

        return result

    # ── MOTOR GAP ANALYSIS ───────────────────────────────────────────

    def _analyze_motor(
        self, e: dict, score: ScoringResult, profile: Optional[dict]
    ) -> GapAnalysisResult:
        result = GapAnalysisResult()

        # No zero depreciation
        if not _bool(e, "zeroDepreciation"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="HIGH",
                category="Zero Depreciation",
                description="No zero depreciation cover. In claims, depreciation (20-50%) is deducted from parts cost.",
                impact="On a ₹1L repair, you could pay ₹20,000-50,000 for depreciation deduction.",
                recommendation="Add zero dep cover (critical for cars <5 years old).",
                estimated_cost=2000,
            ))

        # No engine protection
        if not _bool(e, "engineProtection"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Engine Protection",
                description="No engine protection. Hydrostatic lock (waterlogging) damage is excluded.",
                impact="Engine replacement costs ₹1-5L. Without this, it's 100% out of pocket.",
                recommendation="Add engine protection cover (₹500-2,000/year).",
                estimated_cost=1500,
            ))

        # No roadside assistance
        if not _bool(e, "roadsideAssistance"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="LOW",
                category="Roadside Assistance",
                description="No roadside assistance. Breakdown on highway = no help.",
                impact="Towing alone costs ₹2,000-5,000. RSA covers towing, flat tyre, fuel, battery.",
                recommendation="Add RSA cover (₹300-800/year).",
                estimated_cost=500,
            ))

        # No consumables
        if not _bool(e, "consumables"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Consumables",
                description="No consumables cover. Nuts, bolts, engine oil, grease are excluded from claims.",
                impact="Consumables = 5-10% of repair bill = ₹5,000-15,000 on a ₹1.5L repair.",
                recommendation="Add consumables cover (₹300-800/year).",
                estimated_cost=500,
            ))

        # Low PA cover
        pa = _num(e, "paOwnerCover")
        if 0 < pa <= 15_00_000:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="MEDIUM",
                category="PA Owner Cover",
                description=f"PA cover is only ₹{pa:,.0f} (minimum mandatory). This is inadequate.",
                impact="₹15L is barely enough. Road accident injuries can require years of treatment.",
                recommendation="Increase PA cover to ₹50L+ or get a standalone PA policy.",
                estimated_cost=1000,
            ))

        return result

    # ── TRAVEL GAP ANALYSIS ──────────────────────────────────────────

    def _analyze_travel(
        self, e: dict, score: ScoringResult, profile: Optional[dict]
    ) -> GapAnalysisResult:
        result = GapAnalysisResult()

        medical = _num(e, "medicalExpenses")

        # Medical inadequate for destination
        destinations = _val(e, "destinationCountries") or []
        dest_str = " ".join(str(d).lower() for d in destinations) if isinstance(destinations, list) else str(destinations).lower()

        if "usa" in dest_str or "united states" in dest_str or "canada" in dest_str:
            if medical < 50_00_000:
                result.gaps.append(Gap(
                    gap_type="COVERAGE_GAP",
                    severity="CRITICAL",
                    category="Medical Coverage",
                    description=f"Medical cover of ₹{medical:,.0f} is dangerously low for USA/Canada. ER visit alone costs $3,000-5,000.",
                    impact="A 3-day hospitalization in USA costs $30,000-100,000+ = ₹25L-85L.",
                    recommendation="Get minimum USD 100,000-250,000 medical cover for USA/Canada.",
                    estimated_cost=5000,
                ))
        elif medical < 25_00_000:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="HIGH",
                category="Medical Coverage",
                description=f"Medical cover of ₹{medical:,.0f} may be insufficient for international travel.",
                impact="Hospitalization abroad + evacuation can cost ₹10-30L.",
                recommendation="Increase medical cover to at least $50,000 (₹40L+).",
                estimated_cost=3000,
            ))

        # No evacuation
        evac = _num(e, "emergencyMedicalEvacuation")
        if evac == 0:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="HIGH",
                category="Medical Evacuation",
                description="No emergency medical evacuation cover.",
                impact="Air ambulance from abroad costs ₹15-50L. Without this, family pays full cost.",
                recommendation="Ensure evacuation cover of at least $50,000.",
                estimated_cost=2000,
            ))

        # Schengen compliance
        if "schengen" in dest_str or any(c in dest_str for c in ["france", "germany", "italy", "spain", "portugal", "netherlands", "belgium", "austria", "greece", "switzerland"]):
            schengen = _bool(e, "schengenCompliant")
            if schengen is False or medical < 30_00_000:
                result.gaps.append(Gap(
                    gap_type="COVERAGE_GAP",
                    severity="CRITICAL",
                    category="Schengen Compliance",
                    description="Policy may not meet Schengen visa requirements (minimum €30,000 medical cover).",
                    impact="Visa rejection. Schengen countries require minimum €30,000 (~₹30L) medical cover.",
                    recommendation="Upgrade to Schengen-compliant plan with €30,000+ medical cover.",
                    estimated_cost=3000,
                ))

        # Adventure sports exclusion
        if _bool(e, "adventureSportsExclusion") is True:
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Adventure Sports",
                description="Adventure sports are excluded. Skiing, scuba, trekking, bungee injuries won't be covered.",
                impact="Injury during adventure activity = 100% out of pocket for treatment abroad.",
                recommendation="Add adventure sports add-on or choose a plan that includes it.",
                estimated_cost=1500,
            ))

        return result

    # ── PA GAP ANALYSIS ──────────────────────────────────────────────

    def _analyze_pa(
        self, e: dict, score: ScoringResult, profile: Optional[dict]
    ) -> GapAnalysisResult:
        result = GapAnalysisResult()

        si = _num(e, "paSumInsured")

        # Low sum insured
        if si < 10_00_000:
            result.gaps.append(Gap(
                gap_type="COVERAGE_GAP",
                severity="HIGH",
                category="Sum Insured",
                description=f"PA cover of ₹{si:,.0f} is low. Recommendation: 5-10x monthly income.",
                impact="Permanent disability requires years of care + lost income. ₹10L+ is minimum.",
                recommendation="Increase to ₹25-50L (PA premiums are very affordable at ₹1,000-3,000/year).",
                estimated_cost=2000,
            ))

        # No TTD
        if not _bool(e, "temporaryTotalDisabilityCovered"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Temporary Disability",
                description="No temporary total disability benefit. If temporarily disabled, no income replacement.",
                impact="3-6 months of bed rest = 3-6 months of lost income with no compensation.",
                recommendation="Choose a PA plan with weekly/monthly TTD benefit.",
                estimated_cost=1000,
            ))

        # No medical expenses
        if not _bool(e, "medicalExpensesCovered"):
            result.gaps.append(Gap(
                gap_type="MISSING_COVERAGE",
                severity="MEDIUM",
                category="Medical Expenses",
                description="No medical expenses coverage post-accident.",
                impact="Accident treatment costs aren't covered — only death/disability triggers payout.",
                recommendation="Add medical expenses coverage or ensure health insurance covers accident treatment.",
                estimated_cost=500,
            ))

        return result


# Singleton
gap_analysis_engine = GapAnalysisEngine()
