"""
PRD v2 Zone-Based Recommendations.

Converts Zone 3 (amber) and Zone 4 (red) features into prioritized,
costed upgrade recommendations. Red features become "urgent",
amber features become "recommended".

No LLM calls — purely rule-based using zone classification output
and static cost estimates.

Usage:
    from policy_analysis.recommendations import generate_zone_recommendations
    result = generate_zone_recommendations(zone_classification, category)
"""
import logging
from policy_analysis.recommendations.cost_estimates import get_cost_estimate

logger = logging.getLogger(__name__)


def generate_zone_recommendations(
    zone_classification: dict,
    category: str,
) -> dict:
    """Generate prioritized recommendations from zone 3/4 features.

    Args:
        zone_classification: Output of classify_zones().
        category: Detected category (health/motor/life/pa/travel).

    Returns:
        {
            "urgent": [
                {
                    "featureId": str,
                    "featureName": str,
                    "zone": "red",
                    "title": str,
                    "description": str,
                    "currentValue": str,
                    "explanation": str,
                    "estimatedAnnualCost": {"low": int, "high": int},
                    "priority": "urgent"
                }, ...
            ],
            "recommended": [...],  # amber zone features
            "totalAnnualCost": {"low": int, "high": int},
            "totalMonthlyCost": {"low": int, "high": int},
            "urgentCount": int,
            "recommendedCount": int,
        }
    """
    if not zone_classification or not zone_classification.get("features"):
        return {
            "urgent": [],
            "recommended": [],
            "totalAnnualCost": {"low": 0, "high": 0},
            "totalMonthlyCost": {"low": 0, "high": 0},
            "urgentCount": 0,
            "recommendedCount": 0,
        }

    urgent = []
    recommended = []
    total_low = 0
    total_high = 0

    for feature in zone_classification["features"]:
        zone = feature.get("zone", "")
        if zone not in ("red", "amber"):
            continue

        feature_id = feature.get("featureId", "")
        feature_name = feature.get("featureName", "")
        current_value = feature.get("currentValue", "")
        explanation = feature.get("explanation", "")
        feature_recommendation = feature.get("recommendation", "")

        # Look up cost estimate
        cost = get_cost_estimate(category, feature_id)

        if cost:
            title = cost["title"]
            description = cost["description"]
            cost_low = cost["annualCostLow"]
            cost_high = cost["annualCostHigh"]
        else:
            # Fallback for features without cost estimates
            title = feature_recommendation or f"Improve {feature_name}"
            description = explanation
            cost_low = 0
            cost_high = 0

        rec_entry = {
            "featureId": feature_id,
            "featureName": feature_name,
            "zone": zone,
            "title": title,
            "description": description,
            "explanation": explanation,
            "estimatedAnnualCost": {"low": cost_low, "high": cost_high},
            "priority": "urgent" if zone == "red" else "recommended",
        }
        # Only include currentValue when zone feature has one
        if current_value:
            rec_entry["currentValue"] = current_value

        if zone == "red":
            urgent.append(rec_entry)
        else:
            recommended.append(rec_entry)

        total_low += cost_low
        total_high += cost_high

    # Sort: higher cost items first within each priority
    urgent.sort(key=lambda x: x["estimatedAnnualCost"]["high"], reverse=True)
    recommended.sort(key=lambda x: x["estimatedAnnualCost"]["high"], reverse=True)

    logger.info(
        f"Zone recommendations [{category}]: "
        f"{len(urgent)} urgent, {len(recommended)} recommended, "
        f"total cost ₹{total_low:,}-₹{total_high:,}/yr"
    )

    return {
        "urgent": urgent,
        "recommended": recommended,
        "totalAnnualCost": {"low": total_low, "high": total_high},
        "totalMonthlyCost": {
            "low": round(total_low / 12),
            "high": round(total_high / 12),
        },
        "urgentCount": len(urgent),
        "recommendedCount": len(recommended),
    }
