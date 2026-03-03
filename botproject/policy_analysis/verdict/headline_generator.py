"""
PRD v2 Verdict Engine — Rule-based headline, grade, and action level.

Generates a policy verdict from universal scores and zone classification.
The headline and grade are purely algorithmic; the explanation comes from
the LLM insights call (injected by the orchestrator).

Usage:
    from policy_analysis.verdict import generate_verdict
    verdict = generate_verdict(universal_scores, zone_classification)
"""
import logging

logger = logging.getLogger(__name__)


def _weak_area_name(scores: dict) -> str:
    """Identify the weakest score area for the headline."""
    score_map = {
        "Value for Money": scores.get("vfm", {}).get("score", 0),
        "Coverage Strength": scores.get("coverageStrength", {}).get("score", 0),
        "Claim Readiness": scores.get("claimReadiness", {}).get("score", 0),
    }
    return min(score_map, key=score_map.get)


def _compute_grade(avg: float) -> str:
    """Convert average score to letter grade."""
    if avg >= 90:
        return "A+"
    if avg >= 85:
        return "A"
    if avg >= 80:
        return "A-"
    if avg >= 75:
        return "B+"
    if avg >= 70:
        return "B"
    if avg >= 65:
        return "B-"
    if avg >= 60:
        return "C+"
    if avg >= 55:
        return "C"
    if avg >= 50:
        return "C-"
    if avg >= 40:
        return "D"
    return "F"


def generate_verdict(
    universal_scores: dict,
    zone_classification: dict | None = None,
) -> dict:
    """Generate a policy verdict from universal scores and zone data.

    Args:
        universal_scores: Output of compute_universal_scores().
        zone_classification: Output of classify_zones() (optional, enriches verdict).

    Returns:
        {
            "headline": str,
            "overallGrade": str,       # A+ to F
            "actionRequired": str,     # "none" | "optional" | "recommended" | "urgent"
            "explanation": str,        # Placeholder — replaced by LLM explanation in orchestrator
            "scoreSummary": {
                "vfm": int, "coverage": int, "claimReadiness": int, "average": float
            },
            "zoneSummary": {"green": N, "lightGreen": N, "amber": N, "red": N} | None
        }
    """
    if not universal_scores:
        return {
            "headline": "Analysis Unavailable",
            "overallGrade": "N/A",
            "actionRequired": "recommended",
            "explanation": "",
            "scoreSummary": {"vfm": 0, "coverage": 0, "claimReadiness": 0, "average": 0},
            "zoneSummary": None,
        }

    vfm = universal_scores.get("vfm", {}).get("score", 0)
    coverage = universal_scores.get("coverageStrength", {}).get("score", 0)
    claim = universal_scores.get("claimReadiness", {}).get("score", 0)
    avg = round((vfm + coverage + claim) / 3, 1)

    # Detect TP-only motor policies (coverage breakdown has tpOnly flag)
    _is_tp_only = (
        universal_scores.get("coverageStrength", {}).get("breakdown", {}).get("tpOnly") is True
        or universal_scores.get("vfm", {}).get("breakdown", {}).get("tpOnly") is True
    )

    scores_above_80 = sum(1 for s in (vfm, coverage, claim) if s >= 80)
    scores_below_50 = sum(1 for s in (vfm, coverage, claim) if s < 50)
    scores_60_79 = sum(1 for s in (vfm, coverage, claim) if 60 <= s < 80)

    # --- Headline rules (from plan) ---
    if _is_tp_only:
        # TP-only: override headline to reflect limited nature
        headline = "Basic Legal Coverage - No Own Damage Protection"
    elif scores_above_80 == 3:
        headline = "Comprehensive Protection - Well Covered"
    elif scores_above_80 >= 2 and scores_60_79 >= 1:
        weak = _weak_area_name(universal_scores)
        headline = f"Strong Policy - {weak} Could Be Better"
    elif scores_below_50 >= 2:
        headline = "Critical Gaps - Immediate Action Recommended"
    elif scores_below_50 >= 1:
        headline = "Significant Gaps - Review Recommended"
    elif avg >= 70:
        headline = "Good Protection - Minor Improvements Possible"
    elif avg >= 55:
        headline = "Moderate Protection - Enhancements Recommended"
    else:
        headline = "Below Average - Upgrade Recommended"

    # --- Grade ---
    grade = _compute_grade(avg)
    # TP-only motor: cap grade at B- (no matter what scores say, TP-only has inherent coverage gaps)
    if _is_tp_only and avg < 80:
        _tp_grades = ["A+", "A", "A-", "B+", "B"]
        if grade in _tp_grades:
            grade = "B-"

    # --- Action level ---
    if scores_below_50 >= 2:
        action = "urgent"
    elif scores_below_50 >= 1:
        action = "recommended"
    elif avg < 65:
        action = "recommended"
    elif avg < 80:
        action = "optional"
    else:
        action = "none"

    # Zone enrichment: if many red zones, escalate action
    zone_summary = None
    if zone_classification and zone_classification.get("features"):
        zone_summary = zone_classification.get("summary", {})
        red_count = zone_summary.get("red", 0)
        if red_count >= 3:
            if action == "none":
                action = "recommended"
            elif action == "optional":
                action = "recommended"
        # Use score-based check instead of string matching for headline override
        if red_count >= 3 and scores_above_80 == 3:
            headline = "Good Protection - Some Areas Need Attention"

    logger.info(
        f"Verdict: headline='{headline}', grade={grade}, action={action}, "
        f"scores=[VFM={vfm}, Coverage={coverage}, Claim={claim}, avg={avg}]"
    )

    return {
        "headline": headline,
        "overallGrade": grade,
        "actionRequired": action,
        "explanation": "",  # Filled by LLM in orchestrator
        "scoreSummary": {
            "vfm": vfm,
            "coverage": coverage,
            "claimReadiness": claim,
            "average": avg,
        },
        "zoneSummary": zone_summary,
    }
