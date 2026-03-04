"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
EAZR protection score — proprietary 0-100 composite score across 6 dimensions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EAZRScoreResult:
    total_score: float               # 1.0 - 10.0
    grade: str                       # A+, A, B+, B, C, D
    component_scores: Dict[str, float]  # {factor_name: 0-10}
    interpretation: str
    top_strengths: List[str]
    top_gaps: List[str]
    category: str


# ── Category-specific dimension weights ──────────────────────────────────────

_WEIGHTS: Dict[str, Dict[str, float]] = {
    "health": {
        "coverage_comprehensiveness": 0.30,
        "sublimit_freedom": 0.20,
        "exclusion_fairness": 0.15,
        "insurer_quality": 0.15,
        "premium_value": 0.10,
        "claim_process_quality": 0.10,
    },
    "life_term": {
        "coverage_comprehensiveness": 0.35,
        "exclusion_fairness": 0.20,
        "insurer_quality": 0.20,
        "premium_value": 0.15,
        "claim_process_quality": 0.10,
        "sublimit_freedom": 0.00,
    },
    "life_endowment": {
        "coverage_comprehensiveness": 0.25,
        "premium_value": 0.25,
        "insurer_quality": 0.20,
        "exclusion_fairness": 0.15,
        "claim_process_quality": 0.10,
        "sublimit_freedom": 0.05,
    },
    "motor": {
        "coverage_comprehensiveness": 0.30,
        "sublimit_freedom": 0.15,
        "exclusion_fairness": 0.15,
        "insurer_quality": 0.20,
        "premium_value": 0.10,
        "claim_process_quality": 0.10,
    },
    "travel": {
        "coverage_comprehensiveness": 0.35,
        "sublimit_freedom": 0.10,
        "exclusion_fairness": 0.15,
        "insurer_quality": 0.15,
        "premium_value": 0.15,
        "claim_process_quality": 0.10,
    },
    "pa": {  # Personal Accident
        "coverage_comprehensiveness": 0.30,
        "sublimit_freedom": 0.15,
        "exclusion_fairness": 0.20,
        "insurer_quality": 0.15,
        "premium_value": 0.10,
        "claim_process_quality": 0.10,
    },
}

_DEFAULT_WEIGHTS = _WEIGHTS["health"]


def _grade(score: float) -> str:
    if score >= 9.0:
        return "A+"
    elif score >= 8.0:
        return "A"
    elif score >= 7.0:
        return "B+"
    elif score >= 6.0:
        return "B"
    elif score >= 5.0:
        return "C"
    else:
        return "D"


def _score_health(policy_data: dict, benchmarks: Optional[dict]) -> Dict[str, float]:
    """Score health policy dimensions."""
    scores = {}
    ex = policy_data

    # 1. Coverage comprehensiveness (0-10)
    comp = 5.0
    if ex.get("sum_insured", 0) >= 10_00_000:
        comp += 1.0
    if ex.get("sum_insured", 0) >= 25_00_000:
        comp += 1.0
    if ex.get("has_opd") or ex.get("opd_limit", 0) > 0:
        comp += 1.0
    if ex.get("has_restoration") or ex.get("restoration_benefit"):
        comp += 1.0
    if ex.get("has_no_claim_bonus") or ex.get("ncb"):
        comp += 0.5
    if ex.get("has_maternity"):
        comp += 0.5
    scores["coverage_comprehensiveness"] = min(10.0, comp)

    # 2. Sublimit freedom (10 = no sub-limits, 0 = many restrictive sub-limits)
    sub = 8.0
    room_rent = str(ex.get("room_rent_limit", "no limit")).lower()
    if "no limit" in room_rent or room_rent in ("", "0", "none"):
        sub += 1.0
    elif any(pct in room_rent for pct in ["1%", "0.5%"]):
        sub -= 3.0
    elif "%" in room_rent:
        sub -= 1.5
    if ex.get("has_sublimits") or ex.get("sub_limits"):
        sub -= 2.0
    scores["sublimit_freedom"] = max(1.0, min(10.0, sub))

    # 3. Exclusion fairness (fewer exclusions = higher score)
    excl_list = ex.get("exclusions", [])
    excl_count = len(excl_list) if isinstance(excl_list, list) else 0
    excl_score = max(1.0, 10.0 - excl_count * 0.5)
    # PED waiting period
    ped_wait = ex.get("ped_waiting_period_years", 4)
    if isinstance(ped_wait, (int, float)):
        if ped_wait <= 1:
            excl_score = min(10.0, excl_score + 1.0)
        elif ped_wait >= 4:
            excl_score -= 1.0
    scores["exclusion_fairness"] = max(1.0, min(10.0, excl_score))

    # 4. Insurer quality — from benchmarks or defaults
    insurer_score = 7.0
    if benchmarks:
        csr = benchmarks.get("claim_settlement_ratio", 0)
        if isinstance(csr, (int, float)):
            insurer_score = min(10.0, 5.0 + csr * 5.0)  # 100% CSR → 10, 80% → 9
    scores["insurer_quality"] = insurer_score

    # 5. Premium value — SI / annual premium ratio
    si = ex.get("sum_insured", 0)
    premium = ex.get("annual_premium", 0) or ex.get("premium", 0)
    if si > 0 and premium > 0:
        ratio = si / premium
        # Benchmark: ₹10L SI / ₹15K premium ≈ 66.7 → score 7
        if ratio >= 100:
            pv_score = 10.0
        elif ratio >= 70:
            pv_score = 8.0
        elif ratio >= 50:
            pv_score = 6.5
        elif ratio >= 30:
            pv_score = 5.0
        else:
            pv_score = 3.0
    else:
        pv_score = 5.0  # Unknown
    scores["premium_value"] = pv_score

    # 6. Claim process quality
    cp = 6.0
    if ex.get("has_cashless") or ex.get("cashless_hospitals", 0) > 0:
        cp += 1.5
    network = ex.get("network_hospitals", 0) or ex.get("cashless_hospitals", 0)
    if isinstance(network, (int, float)):
        if network >= 10000:
            cp += 1.5
        elif network >= 5000:
            cp += 0.5
    if ex.get("has_tpa") is False:
        cp += 0.5  # Direct claim settlement without TPA = slightly better
    scores["claim_process_quality"] = min(10.0, cp)

    return scores


def _score_life_term(policy_data: dict, benchmarks: Optional[dict]) -> Dict[str, float]:
    """Score term life policy dimensions."""
    scores = {}
    ex = policy_data

    # Coverage
    comp = 5.0
    sa = ex.get("sum_assured", 0)
    if sa >= 1_00_00_000:  # 1 crore
        comp += 2.0
    elif sa >= 50_00_000:
        comp += 1.0
    if ex.get("has_critical_illness_rider"):
        comp += 1.0
    if ex.get("has_waiver_of_premium"):
        comp += 1.0
    if ex.get("has_accidental_death_benefit"):
        comp += 1.0
    scores["coverage_comprehensiveness"] = min(10.0, comp)

    # Exclusions
    excl_list = ex.get("exclusions", [])
    excl_count = len(excl_list) if isinstance(excl_list, list) else 0
    scores["exclusion_fairness"] = max(1.0, 9.0 - excl_count * 0.8)

    # Insurer
    insurer_score = 7.0
    if benchmarks:
        csr = benchmarks.get("claim_settlement_ratio", 0)
        if isinstance(csr, (int, float)):
            insurer_score = min(10.0, 5.0 + csr * 5.0)
    scores["insurer_quality"] = insurer_score

    # Premium value — SA/annual premium
    sa = ex.get("sum_assured", 0)
    premium = ex.get("annual_premium", 0) or ex.get("premium", 0)
    if sa > 0 and premium > 0:
        ratio = sa / premium
        if ratio >= 1000:
            pv_score = 10.0
        elif ratio >= 500:
            pv_score = 8.0
        elif ratio >= 200:
            pv_score = 6.0
        else:
            pv_score = 4.0
    else:
        pv_score = 5.0
    scores["premium_value"] = pv_score

    # Claim process
    cp = 7.0
    if ex.get("has_online_claim"):
        cp += 1.0
    scores["claim_process_quality"] = min(10.0, cp)
    scores["sublimit_freedom"] = 0.0  # Not applicable for term

    return scores


def _score_generic(policy_data: dict, benchmarks: Optional[dict]) -> Dict[str, float]:
    """Generic scoring for motor, travel, PA."""
    scores = {
        "coverage_comprehensiveness": 6.0,
        "sublimit_freedom": 6.0,
        "exclusion_fairness": 6.0,
        "insurer_quality": 7.0,
        "premium_value": 6.0,
        "claim_process_quality": 6.0,
    }
    # Improve based on available data
    if benchmarks and benchmarks.get("claim_settlement_ratio"):
        csr = benchmarks["claim_settlement_ratio"]
        if isinstance(csr, (int, float)):
            scores["insurer_quality"] = min(10.0, 5.0 + csr * 5.0)
    return scores


def calculate_eazr_score(
    policy_data: dict,
    category: str,
    benchmarks: Optional[dict] = None,
) -> EAZRScoreResult:
    """
    Calculate the EAZR Protection Score for a policy.

    Args:
        policy_data: Extraction data from botproject (fields from policy PDF)
        category: Policy category — "health" | "life_term" | "life_endowment" | "motor" | "travel" | "pa"
        benchmarks: Optional KG benchmarks for insurer quality comparison

    Returns:
        EAZRScoreResult with score, grade, components, strengths, gaps
    """
    cat = category.lower().replace(" ", "_")
    weights = _WEIGHTS.get(cat, _DEFAULT_WEIGHTS)

    # Get component scores
    if cat == "health":
        component_scores = _score_health(policy_data, benchmarks)
    elif cat == "life_term":
        component_scores = _score_life_term(policy_data, benchmarks)
    else:
        component_scores = _score_generic(policy_data, benchmarks)

    # Weighted total
    total = sum(
        component_scores.get(dim, 0) * weight
        for dim, weight in weights.items()
    )
    total = round(min(10.0, max(1.0, total)), 1)
    grade = _grade(total)

    # Identify strengths (top 2 scoring dims) and gaps (bottom 2)
    sorted_dims = sorted(
        [(dim, component_scores.get(dim, 0)) for dim in weights if weights[dim] > 0],
        key=lambda x: x[1],
        reverse=True,
    )
    top_strengths = [
        f"{dim.replace('_', ' ').title()} ({score:.1f}/10)"
        for dim, score in sorted_dims[:2]
        if score >= 7.0
    ]
    top_gaps = [
        f"{dim.replace('_', ' ').title()} ({score:.1f}/10)"
        for dim, score in sorted_dims[-2:]
        if score < 7.0
    ]

    # Interpretation
    if grade == "A+":
        interpretation = "Excellent policy — comprehensive coverage with minimal restrictions."
    elif grade == "A":
        interpretation = "Very good policy — strong coverage with minor gaps."
    elif grade == "B+":
        interpretation = "Good policy — above average but some important gaps to address."
    elif grade == "B":
        interpretation = "Average policy — adequate basic coverage, notable gaps present."
    elif grade == "C":
        interpretation = "Below average — significant gaps that could affect claim settlement."
    else:
        interpretation = "Poor policy — major structural deficiencies. Review urgently."

    return EAZRScoreResult(
        total_score=total,
        grade=grade,
        component_scores={k: round(v, 1) for k, v in component_scores.items()},
        interpretation=interpretation,
        top_strengths=top_strengths,
        top_gaps=top_gaps,
        category=cat,
    )
