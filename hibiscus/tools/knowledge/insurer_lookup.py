"""
Tool: Insurer Lookup — Neo4j Knowledge Graph
=============================================
Look up insurer data from the KG.
Used by: PolicyAnalyzer, Recommender, RiskDetector agents.

Functions
---------
lookup_insurer(name)                    — fuzzy match by name/alias
get_insurer_benchmarks(insurer_id)      — CSR/ICR vs industry benchmarks
list_insurers_by_category(category)     — all insurers in a category
compare_insurers(names)                 — side-by-side comparison dict
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.graph.client import kg_client
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.tools.knowledge.insurer_lookup")

# Industry average benchmarks (from IRDAI Annual Report 2022-23)
# Used as fallback when KG benchmarks are unavailable
_INDUSTRY_DEFAULTS = {
    "life_csr_avg": 98.5,
    "health_icr_healthy_min": 55.0,
    "health_icr_healthy_max": 80.0,
    "health_csr_avg": 89.0,
    "solvency_regulatory_min": 1.50,
}


async def lookup_insurer(insurer_name: str) -> Dict[str, Any]:
    """
    Look up an insurer by name using fuzzy matching.

    Matches against:
      - i.name (full legal name)
      - i.short_name (common name, e.g. "HDFC ERGO")
      - i.aliases (list of alternative names)

    Args:
        insurer_name: Partial or full insurer name.

    Returns:
        Dict of insurer properties, or {} if not found / KG unavailable.

    Example:
        result = await lookup_insurer("HDFC Ergo")
        # Returns: {"name": "HDFC ERGO General Insurance", "csr": 92.1, ...}
    """
    if not insurer_name or not insurer_name.strip():
        return {}

    if not kg_client.is_connected:
        await kg_client.connect()

    if not kg_client.is_connected:
        logger.warning(
            "insurer_lookup_kg_unavailable",
            insurer_name=insurer_name,
        )
        return {}

    query = """
    MATCH (i:Insurer)
    WHERE toLower(i.name) CONTAINS toLower($name)
       OR toLower(i.short_name) CONTAINS toLower($name)
    RETURN i
    ORDER BY
      CASE
        WHEN toLower(i.name) = toLower($name) THEN 0
        WHEN toLower(i.short_name) = toLower($name) THEN 1
        ELSE 2
      END
    LIMIT 1
    """
    try:
        results = await kg_client.query(
            query,
            params={"name": insurer_name.strip()},
            query_name="lookup_insurer",
        )
        if results and "i" in results[0]:
            data = dict(results[0]["i"])
            logger.info(
                "insurer_lookup_hit",
                query=insurer_name,
                matched=data.get("name"),
            )
            return data
        logger.info("insurer_lookup_miss", query=insurer_name)
        return {}
    except Exception as exc:
        logger.warning("insurer_lookup_error", insurer_name=insurer_name, error=str(exc))
        return {}


async def get_insurer_benchmarks(insurer_id: str) -> Dict[str, Any]:
    """
    Get benchmark comparison data for a specific insurer.

    Compares the insurer's CSR, ICR, and solvency ratio against industry
    averages and regulatory minimums.

    Args:
        insurer_id: The insurer's name (matches Insurer.name in KG)
                    or short_name.

    Returns:
        Dict with keys:
          - insurer_name: str
          - csr: float — insurer CSR
          - csr_industry_avg: float
          - csr_status: "excellent" | "good" | "below_average" | "poor"
          - icr: float | None
          - icr_healthy_range: dict {"min": 55, "max": 80}
          - icr_status: "healthy" | "low_risk" | "high_risk" | None
          - solvency_ratio: float
          - solvency_status: "adequate" | "marginal" | "below_minimum"
          - network_hospitals: int | None
          - digital_score: int | None
          - raw: dict — full insurer node
    """
    insurer = await lookup_insurer(insurer_id)
    if not insurer:
        return {"error": f"Insurer not found: {insurer_id}"}

    insurer_type = insurer.get("type", "")
    is_life = "life" in insurer_type
    csr = insurer.get("csr")
    icr = insurer.get("icr")
    solvency = insurer.get("solvency_ratio")

    # CSR evaluation
    if csr is None:
        csr_status = "unknown"
    elif csr >= 99.0:
        csr_status = "excellent"
    elif csr >= 97.0:
        csr_status = "good"
    elif csr >= 95.0:
        csr_status = "below_average"
    else:
        csr_status = "poor"

    # ICR evaluation (health/general only)
    icr_status: Optional[str] = None
    if icr is not None and not is_life:
        if _INDUSTRY_DEFAULTS["health_icr_healthy_min"] <= icr <= _INDUSTRY_DEFAULTS["health_icr_healthy_max"]:
            icr_status = "healthy"
        elif icr < _INDUSTRY_DEFAULTS["health_icr_healthy_min"]:
            icr_status = "low_risk"  # Low ICR can mean claims being rejected
        else:
            icr_status = "high_risk"  # High ICR means insurer is financially stressed

    # Solvency evaluation
    if solvency is None:
        solvency_status = "unknown"
    elif solvency >= 1.75:
        solvency_status = "adequate"
    elif solvency >= 1.50:
        solvency_status = "marginal"
    else:
        solvency_status = "below_minimum"

    industry_csr_avg = (
        _INDUSTRY_DEFAULTS["life_csr_avg"] if is_life
        else _INDUSTRY_DEFAULTS["health_csr_avg"]
    )

    return {
        "insurer_name": insurer.get("name"),
        "short_name": insurer.get("short_name"),
        "insurer_type": insurer_type,
        "csr": csr,
        "csr_industry_avg": industry_csr_avg,
        "csr_status": csr_status,
        "icr": icr,
        "icr_healthy_range": {
            "min": _INDUSTRY_DEFAULTS["health_icr_healthy_min"],
            "max": _INDUSTRY_DEFAULTS["health_icr_healthy_max"],
        },
        "icr_status": icr_status,
        "solvency_ratio": solvency,
        "solvency_regulatory_min": _INDUSTRY_DEFAULTS["solvency_regulatory_min"],
        "solvency_status": solvency_status,
        "network_hospitals": insurer.get("network_hospitals"),
        "claim_settlement_time_avg": insurer.get("claim_settlement_time_avg"),
        "digital_score": insurer.get("digital_score"),
        "complaint_ratio": insurer.get("complaint_ratio"),
        "headquarters": insurer.get("headquarters"),
        "established_year": insurer.get("established_year"),
        "irdai_reg_no": insurer.get("irdai_reg_no"),
        "raw": insurer,
    }


async def list_insurers_by_category(category: str) -> List[Dict[str, Any]]:
    """
    List all insurers in a given category, ordered by CSR descending.

    Args:
        category: One of:
          - "life" — all life insurers (public_life, private_life)
          - "health" — standalone health insurers (standalone_health)
          - "general" — general/multi-line insurers (private_general, public_general)
          - "public" — all PSU insurers
          - "private" — all private insurers

    Returns:
        List of insurer dicts, ordered by CSR descending.
        Returns [] if KG unavailable.
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("list_insurers_kg_unavailable", category=category)
        return []

    category_lower = category.lower().strip()
    type_filters: List[str] = []

    if category_lower == "life":
        type_filters = ["public_life", "private_life"]
    elif category_lower == "health":
        type_filters = ["standalone_health"]
    elif category_lower == "general":
        type_filters = ["private_general", "public_general"]
    elif category_lower == "public":
        type_filters = ["public_life", "public_general"]
    elif category_lower == "private":
        type_filters = ["private_life", "private_general", "standalone_health"]
    else:
        # Try direct match
        type_filters = [category_lower]

    query = """
    MATCH (i:Insurer)
    WHERE i.type IN $types
    RETURN i
    ORDER BY i.csr DESC
    """
    try:
        results = await kg_client.query(
            query,
            params={"types": type_filters},
            query_name="list_insurers_by_category",
        )
        insurers = [dict(r["i"]) for r in results if "i" in r]
        logger.info(
            "list_insurers_by_category",
            category=category,
            count=len(insurers),
        )
        return insurers
    except Exception as exc:
        logger.warning(
            "list_insurers_by_category_error",
            category=category,
            error=str(exc),
        )
        return []


async def compare_insurers(insurer_names: List[str]) -> Dict[str, Any]:
    """
    Build a side-by-side comparison dict for multiple insurers.

    Args:
        insurer_names: List of insurer names or short names (2–5 recommended).

    Returns:
        Dict with:
          - "insurers": list of insurer dicts (one per found insurer)
          - "comparison_fields": list of fields included in comparison
          - "not_found": list of names that couldn't be matched
          - "summary": dict of best/worst per metric

    Example:
        result = await compare_insurers(["HDFC Life", "Max Life", "LIC"])
    """
    found: List[Dict[str, Any]] = []
    not_found: List[str] = []

    for name in insurer_names:
        insurer = await lookup_insurer(name)
        if insurer:
            found.append(insurer)
        else:
            not_found.append(name)

    if not found:
        return {"insurers": [], "not_found": insurer_names, "comparison_fields": []}

    comparison_fields = [
        "name", "short_name", "type", "csr", "icr",
        "solvency_ratio", "network_hospitals",
        "claim_settlement_time_avg", "digital_score",
        "complaint_ratio", "market_share",
    ]

    # Build summary: best/worst per numeric metric
    numeric_metrics = ["csr", "icr", "solvency_ratio", "digital_score", "claim_settlement_time_avg"]
    summary: Dict[str, Any] = {}

    for metric in numeric_metrics:
        values = [(i.get("name"), i.get(metric)) for i in found if i.get(metric) is not None]
        if not values:
            continue
        # For claim_settlement_time_avg, lower is better
        if metric == "claim_settlement_time_avg":
            best = min(values, key=lambda x: x[1])
            worst = max(values, key=lambda x: x[1])
        else:
            best = max(values, key=lambda x: x[1])
            worst = min(values, key=lambda x: x[1])
        summary[metric] = {"best": best[0], "best_value": best[1], "worst": worst[0], "worst_value": worst[1]}

    return {
        "insurers": found,
        "comparison_fields": comparison_fields,
        "not_found": not_found,
        "summary": summary,
    }
