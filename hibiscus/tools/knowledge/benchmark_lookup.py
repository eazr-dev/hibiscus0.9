"""
Tool: Benchmark Lookup — Neo4j Knowledge Graph
===============================================
Retrieve and evaluate insurance benchmarks from the KG.
Used by: PolicyAnalyzer, Recommender, RiskDetector, Calculator agents.

Functions
---------
get_benchmark(metric, category, age_group, year)    — fetch a specific benchmark
evaluate_against_benchmark(metric, value, category) — classify value vs benchmark
get_coverage_recommendation(category, age_group)    — recommended SI for a profile
get_premium_benchmark(category, age_group)          — typical premium for a profile
list_benchmarks_by_category(category)               — all benchmarks in a category
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.graph.client import kg_client
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.tools.knowledge.benchmark_lookup")

# Evaluation thresholds — used as fallback when KG is unavailable
_FALLBACK_BENCHMARKS: Dict[str, Any] = {
    "life_csr_excellent": 99.0,
    "life_csr_good": 97.0,
    "life_csr_poor": 95.0,
    "health_icr_healthy_min": 55.0,
    "health_icr_healthy_max": 80.0,
    "health_min_eazr_score": 7.5,
    "term_coverage_multiplier": 12,   # times annual income
    "health_metro_min_si_family": 1000000,  # ₹10L minimum for family in metro
    "health_metro_min_si_individual": 500000,  # ₹5L minimum individual
}

_EVALUATION_LABELS = {
    "excellent": "Excellent — top tier performer",
    "above_average": "Above average — better than industry",
    "average": "Average — meets industry standard",
    "below_average": "Below average — room for improvement",
    "poor": "Poor — consider alternatives",
    "healthy": "Healthy range",
    "low_risk": "Below healthy range — may indicate claim rejection issues",
    "high_risk": "Above healthy range — insurer may be financially stressed",
}


async def get_benchmark(
    metric: str,
    category: str,
    age_group: Optional[str] = None,
    year: int = 2024,
) -> Dict[str, Any]:
    """
    Retrieve a specific benchmark from the Knowledge Graph.

    Args:
        metric:    Benchmark metric key (e.g. "avg_annual_premium_5L_cover",
                   "recommended_sum_insured", "minimum_acceptable_csr",
                   "acceptable_icr_range").
        category:  Benchmark category (e.g. "health_insurance",
                   "life_term_insurance", "life_endowment", "ulip").
        age_group: Optional age group filter (e.g. "25-35", "35-45", "55+").
        year:      Data year (default 2024).

    Returns:
        Dict with benchmark data, or {} if not found.

    Example:
        bm = await get_benchmark("avg_annual_premium_5L_cover", "health_insurance", "25-35")
        # Returns: {"value": 8000, "context": "...", "recommendations": [...], ...}
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("get_benchmark_kg_unavailable", metric=metric, category=category)
        return {}

    if age_group:
        query = """
        MATCH (b:Benchmark)
        WHERE b.metric = $metric
          AND b.category = $category
          AND b.age_group = $age_group
        RETURN b
        ORDER BY b.date DESC
        LIMIT 1
        """
        params: Dict[str, Any] = {
            "metric": metric,
            "category": category,
            "age_group": age_group,
        }
    else:
        query = """
        MATCH (b:Benchmark)
        WHERE b.metric = $metric
          AND b.category = $category
        RETURN b
        ORDER BY b.date DESC
        LIMIT 1
        """
        params = {"metric": metric, "category": category}

    try:
        results = await kg_client.query(query, params=params, query_name="get_benchmark")
        if results and "b" in results[0]:
            data = dict(results[0]["b"])
            logger.info(
                "get_benchmark_hit",
                metric=metric,
                category=category,
                age_group=age_group,
                value=data.get("value"),
            )
            return data
        logger.info(
            "get_benchmark_miss",
            metric=metric,
            category=category,
            age_group=age_group,
        )
        return {}
    except Exception as exc:
        logger.warning("get_benchmark_error", metric=metric, error=str(exc))
        return {}


async def evaluate_against_benchmark(
    metric: str,
    value: float,
    category: str,
    age_group: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate a given value against the industry benchmark for that metric.

    Args:
        metric:    The metric being evaluated (e.g. "csr", "icr", "eazr_score",
                   "sum_insured", "premium").
        value:     The value to evaluate.
        category:  Benchmark category.
        age_group: Optional age group for age-dependent benchmarks.

    Returns:
        Dict with:
          - metric: str
          - value: float — the input value
          - status: str — "excellent" | "above_average" | "average" | "below_average" | "poor"
          - status_label: str — human-readable label
          - benchmark_value: float | None — the reference value
          - percentile: str | None — approximate percentile band
          - explanation: str — narrative explanation
          - recommendations: list — actionable recommendations

    Example:
        result = await evaluate_against_benchmark("icr", 58.0, "health_insurance")
        # Returns: {"status": "healthy", "explanation": "ICR 58% is in the healthy 55-80% range", ...}
    """
    bm = await get_benchmark(metric, category, age_group)
    result: Dict[str, Any] = {
        "metric": metric,
        "value": value,
        "category": category,
        "age_group": age_group,
        "benchmark_value": bm.get("value"),
        "percentile_25": bm.get("percentile_25"),
        "percentile_50": bm.get("percentile_50"),
        "percentile_75": bm.get("percentile_75"),
        "source": bm.get("source", "IRDAI Annual Report"),
        "recommendations": bm.get("recommendations", []),
    }

    # CSR evaluation
    if metric in ("csr", "claim_settlement_ratio"):
        if value >= _FALLBACK_BENCHMARKS["life_csr_excellent"]:
            status, explanation = "excellent", f"CSR {value:.1f}% is excellent (top tier ≥ {_FALLBACK_BENCHMARKS['life_csr_excellent']}%)"
        elif value >= _FALLBACK_BENCHMARKS["life_csr_good"]:
            status, explanation = "above_average", f"CSR {value:.1f}% is good (above industry avg of 98.5%)"
        elif value >= _FALLBACK_BENCHMARKS["life_csr_poor"]:
            status, explanation = "below_average", f"CSR {value:.1f}% is below average (industry avg 98.5%)"
        else:
            status, explanation = "poor", f"CSR {value:.1f}% is poor — significant claim rejection risk"

    # ICR evaluation (health)
    elif metric in ("icr", "incurred_claim_ratio"):
        icr_min = _FALLBACK_BENCHMARKS["health_icr_healthy_min"]
        icr_max = _FALLBACK_BENCHMARKS["health_icr_healthy_max"]
        if icr_min <= value <= icr_max:
            status = "healthy"
            explanation = f"ICR {value:.1f}% is in the healthy range ({icr_min:.0f}–{icr_max:.0f}%)"
        elif value < icr_min:
            status = "low_risk"
            explanation = (
                f"ICR {value:.1f}% is below the healthy range ({icr_min:.0f}%). "
                "This may indicate the insurer is rejecting more claims than average."
            )
        else:
            status = "high_risk"
            explanation = (
                f"ICR {value:.1f}% is above the healthy range ({icr_max:.0f}%). "
                "The insurer may be financially stressed — premium hikes likely."
            )

    # EAZR score evaluation
    elif metric == "eazr_score":
        threshold = _FALLBACK_BENCHMARKS["health_min_eazr_score"]
        if value >= 9.0:
            status, explanation = "excellent", f"EAZR score {value:.1f} is excellent — best-in-class plan"
        elif value >= 8.0:
            status, explanation = "above_average", f"EAZR score {value:.1f} is above average — good plan"
        elif value >= threshold:
            status, explanation = "average", f"EAZR score {value:.1f} meets minimum threshold of {threshold}"
        elif value >= 7.0:
            status, explanation = "below_average", f"EAZR score {value:.1f} is below the recommended minimum of {threshold}"
        else:
            status, explanation = "poor", f"EAZR score {value:.1f} is poor — significant policy gaps likely"

    # Generic numeric evaluation against benchmark
    elif bm.get("value") is not None:
        bm_value = bm["value"]
        p25 = bm.get("percentile_25", bm_value * 0.75)
        p75 = bm.get("percentile_75", bm_value * 1.25)

        if value >= p75:
            status, explanation = "excellent", f"{value:,.0f} is in the top quartile (benchmark: {bm_value:,.0f})"
        elif value >= bm_value:
            status, explanation = "above_average", f"{value:,.0f} is above the benchmark of {bm_value:,.0f}"
        elif value >= p25:
            status, explanation = "average", f"{value:,.0f} is near the benchmark of {bm_value:,.0f}"
        else:
            status, explanation = "below_average", f"{value:,.0f} is below the 25th percentile (benchmark: {bm_value:,.0f})"
    else:
        status, explanation = "unknown", f"No benchmark available for {metric} in {category}"

    result["status"] = status
    result["status_label"] = _EVALUATION_LABELS.get(status, status)
    result["explanation"] = explanation

    logger.info(
        "evaluate_against_benchmark",
        metric=metric,
        value=value,
        category=category,
        status=status,
    )
    return result


async def get_coverage_recommendation(
    category: str,
    age_group: str,
    annual_income: Optional[int] = None,
    city_tier: str = "metro",
) -> Dict[str, Any]:
    """
    Get recommended sum insured for a user profile.

    Args:
        category:       "health" or "life_term"
        age_group:      Age group string (e.g. "25-35", "35-45")
        annual_income:  Annual income in INR (required for life term recommendations)
        city_tier:      "metro" | "tier1" | "tier2" (affects health SI recommendation)

    Returns:
        Dict with:
          - recommended_si: int — recommended sum insured in INR
          - minimum_si: int
          - ideal_si: int
          - rationale: str
          - source: str
    """
    if category == "health":
        bm = await get_benchmark("recommended_sum_insured", "health_insurance", age_group)
        if bm.get("value"):
            base_si = bm["value"]
        else:
            # Fallback: age-based defaults
            age_defaults = {
                "25-35": 500000,
                "35-45": 1000000,
                "45-55": 1500000,
                "55+": 2000000,
            }
            base_si = age_defaults.get(age_group, 500000)

        # Adjust for city tier
        multiplier = {"metro": 1.5, "tier1": 1.2, "tier2": 1.0}.get(city_tier, 1.0)
        recommended_si = int(base_si * multiplier)
        minimum_si = base_si
        ideal_si = recommended_si * 2  # Typically 2x recommended is ideal

        return {
            "category": category,
            "age_group": age_group,
            "city_tier": city_tier,
            "recommended_si": recommended_si,
            "minimum_si": minimum_si,
            "ideal_si": ideal_si,
            "recommended_formatted": f"₹{recommended_si // 100000}L",
            "rationale": (
                f"For age {age_group} in {city_tier} city, minimum ₹{minimum_si // 100000}L "
                f"is recommended. With hospital costs in {city_tier}, "
                f"₹{recommended_si // 100000}L is the suggested coverage."
            ),
            "source": bm.get("source", "EAZR Coverage Adequacy Model v1.0"),
        }

    elif category == "life_term":
        if not annual_income:
            return {
                "error": "annual_income is required for life term coverage recommendation",
                "recommendation": "Life cover should be 10–15× annual income",
            }
        bm = await get_benchmark("recommended_si_multiplier", "life_term_insurance")
        multiplier_val = bm.get("value", _FALLBACK_BENCHMARKS["term_coverage_multiplier"])
        minimum_si = annual_income * 10
        recommended_si = int(annual_income * multiplier_val)
        ideal_si = annual_income * 15

        return {
            "category": category,
            "age_group": age_group,
            "annual_income": annual_income,
            "multiplier_used": multiplier_val,
            "recommended_si": recommended_si,
            "minimum_si": minimum_si,
            "ideal_si": ideal_si,
            "recommended_formatted": f"₹{recommended_si // 10000000}Cr" if recommended_si >= 10000000 else f"₹{recommended_si // 100000}L",
            "rationale": (
                f"With annual income ₹{annual_income // 100000}L, "
                f"recommended life cover = {multiplier_val}× income = "
                f"₹{recommended_si // 10000000}Cr. "
                f"Add outstanding liabilities (home loan, etc.) to this figure."
            ),
            "formula": bm.get("formula", "recommended_SI = 12 × annual_income"),
            "source": bm.get("source", "EAZR Coverage Adequacy Model v1.0"),
        }
    else:
        return {"error": f"No coverage recommendation model for category: {category}"}


async def get_premium_benchmark(
    category: str,
    age_group: str,
    sum_insured: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get typical premium range for a given profile.

    Args:
        category:     Insurance category.
        age_group:    Age group.
        sum_insured:  Optional — for context in the response.

    Returns:
        Dict with typical_premium, percentile_25, percentile_75, and context.
    """
    metric_map = {
        "health": "avg_annual_premium_5L_cover",
        "life_term": "avg_annual_premium_1cr_cover",
    }
    metric = metric_map.get(category, "avg_annual_premium_5L_cover")
    bm = await get_benchmark(metric, f"{category}_insurance", age_group)

    if bm:
        return {
            "category": category,
            "age_group": age_group,
            "typical_premium": bm.get("value"),
            "percentile_25": bm.get("percentile_25"),
            "percentile_75": bm.get("percentile_75"),
            "context": bm.get("context", ""),
            "source": bm.get("source"),
            "recommendations": bm.get("recommendations", []),
        }
    return {
        "category": category,
        "age_group": age_group,
        "typical_premium": None,
        "error": f"No premium benchmark found for {category} age {age_group}",
    }


async def list_benchmarks_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Retrieve all benchmarks for a given category.

    Args:
        category: Benchmark category (e.g. "health_insurance", "life_term_insurance").

    Returns:
        List of benchmark dicts ordered by date descending.
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("list_benchmarks_kg_unavailable", category=category)
        return []

    query = """
    MATCH (b:Benchmark)
    WHERE b.category = $category
    RETURN b
    ORDER BY b.date DESC
    """
    try:
        results = await kg_client.query(
            query,
            params={"category": category},
            query_name="list_benchmarks_by_category",
        )
        benchmarks = [dict(r["b"]) for r in results if "b" in r]
        logger.info(
            "list_benchmarks_by_category",
            category=category,
            count=len(benchmarks),
        )
        return benchmarks
    except Exception as exc:
        logger.warning("list_benchmarks_by_category_error", category=category, error=str(exc))
        return []
