"""
Tool: Product Lookup — Neo4j Knowledge Graph
=============================================
Look up and search insurance product data from the KG.
Used by: PolicyAnalyzer, Recommender, RiskDetector, PortfolioOptimizer agents.

Functions
---------
lookup_product(name, insurer_name)        — find product by name (fuzzy)
search_products(category, filters)        — search by category with filters
compare_products(product_ids)             — side-by-side comparison
get_product_by_insurer(insurer_name, cat) — list products from one insurer
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.graph.client import kg_client
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.tools.knowledge.product_lookup")


async def lookup_product(
    product_name: str,
    insurer_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Look up a product by name using fuzzy matching.

    Args:
        product_name:  Partial or full product name.
        insurer_name:  Optional — narrows search to a specific insurer.

    Returns:
        Dict of product properties, or {} if not found / KG unavailable.

    Example:
        result = await lookup_product("Optima Secure", "HDFC ERGO")
        result = await lookup_product("iProtect Smart")
    """
    if not product_name or not product_name.strip():
        return {}

    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("product_lookup_kg_unavailable", product_name=product_name)
        return {}

    if insurer_name:
        query = """
        MATCH (p:Product)
        WHERE toLower(p.name) CONTAINS toLower($name)
          AND toLower(p.insurer_name) CONTAINS toLower($insurer)
        RETURN p
        ORDER BY
          CASE WHEN toLower(p.name) = toLower($name) THEN 0 ELSE 1 END
        LIMIT 1
        """
        params: Dict[str, Any] = {
            "name": product_name.strip(),
            "insurer": insurer_name.strip(),
        }
    else:
        query = """
        MATCH (p:Product)
        WHERE toLower(p.name) CONTAINS toLower($name)
        RETURN p
        ORDER BY
          CASE WHEN toLower(p.name) = toLower($name) THEN 0 ELSE 1 END
        LIMIT 1
        """
        params = {"name": product_name.strip()}

    try:
        results = await kg_client.query(
            query,
            params=params,
            query_name="lookup_product",
        )
        if results and "p" in results[0]:
            data = dict(results[0]["p"])
            logger.info(
                "product_lookup_hit",
                query=product_name,
                matched=data.get("name"),
            )
            return data
        logger.info("product_lookup_miss", query=product_name)
        return {}
    except Exception as exc:
        logger.warning("product_lookup_error", product_name=product_name, error=str(exc))
        return {}


async def search_products(
    category: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search products by category with optional filter criteria.

    Args:
        category: Product category — one of:
          "health", "life_term", "life_endowment", "life_savings",
          "ulip", "motor", "travel", "personal_accident",
          "critical_illness", "senior_citizen_health"
        filters: Optional dict of filter criteria. Supported keys:
          - min_sum_insured: int — minimum sum insured (INR)
          - max_premium: int — maximum annual premium (INR)
          - no_copay: bool — if True, only return products with 0% copay
          - no_room_rent_limit: bool — if True, only return "No limit" plans
          - min_eazr_score: float — minimum EAZR score threshold
          - insurer_name: str — filter by insurer
        limit: Maximum number of results to return (default 10).

    Returns:
        List of product dicts ordered by EAZR score descending.
        Returns [] if KG unavailable.

    Example:
        results = await search_products(
            "health",
            filters={"no_copay": True, "min_sum_insured": 500000, "min_eazr_score": 8.0},
        )
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("search_products_kg_unavailable", category=category)
        return []

    if filters is None:
        filters = {}

    # Build WHERE clauses
    where_clauses = ["p.category = $category"]
    params: Dict[str, Any] = {"category": category, "limit": limit}

    if filters.get("min_sum_insured"):
        where_clauses.append("p.sum_insured_min <= $min_sum_insured")
        params["min_sum_insured"] = filters["min_sum_insured"]

    if filters.get("max_premium"):
        where_clauses.append("(p.premium_range_min IS NULL OR p.premium_range_min <= $max_premium)")
        params["max_premium"] = filters["max_premium"]

    if filters.get("no_copay"):
        where_clauses.append("p.copay_structure = '0%'")

    if filters.get("no_room_rent_limit"):
        where_clauses.append("p.room_rent_limit = 'No limit'")

    if filters.get("min_eazr_score"):
        where_clauses.append("p.eazr_score >= $min_eazr_score")
        params["min_eazr_score"] = filters["min_eazr_score"]

    if filters.get("insurer_name"):
        where_clauses.append("toLower(p.insurer_name) CONTAINS toLower($insurer_name)")
        params["insurer_name"] = filters["insurer_name"]

    where_str = " AND ".join(where_clauses)

    query = f"""
    MATCH (p:Product)
    WHERE {where_str}
    RETURN p
    ORDER BY p.eazr_score DESC
    LIMIT $limit
    """

    try:
        results = await kg_client.query(
            query,
            params=params,
            query_name="search_products",
        )
        products = [dict(r["p"]) for r in results if "p" in r]
        logger.info(
            "search_products_results",
            category=category,
            filters=filters,
            count=len(products),
        )
        return products
    except Exception as exc:
        logger.warning("search_products_error", category=category, error=str(exc))
        return []


async def compare_products(product_names: List[str]) -> Dict[str, Any]:
    """
    Build a side-by-side comparison dict for multiple products.

    Args:
        product_names: List of product names (2–5 recommended).

    Returns:
        Dict with:
          - "products": list of product dicts (one per found product)
          - "comparison_fields": list of fields included
          - "not_found": list of names that couldn't be matched
          - "summary": dict of best/worst per metric
          - "gaps": list of notable differences (e.g., copay present in some but not others)

    Example:
        result = await compare_products([
            "HDFC ERGO Optima Secure",
            "Niva Bupa ReAssure 2.0",
            "Care Supreme Health Insurance",
        ])
    """
    found: List[Dict[str, Any]] = []
    not_found: List[str] = []

    for name in product_names:
        product = await lookup_product(name)
        if product:
            found.append(product)
        else:
            not_found.append(name)

    if not found:
        return {"products": [], "not_found": product_names, "comparison_fields": []}

    comparison_fields = [
        "name", "insurer_name", "category", "type",
        "sum_insured_min", "sum_insured_max",
        "premium_range_min", "premium_range_max",
        "eazr_score", "copay_structure", "room_rent_limit",
        "exclusion_count", "sub_limit_count",
        "waiting_periods", "key_features",
    ]

    # Build summary: best/worst per numeric metric
    numeric_better_higher = ["eazr_score", "sum_insured_max"]
    numeric_better_lower = ["premium_range_min", "exclusion_count", "sub_limit_count"]
    summary: Dict[str, Any] = {}

    for metric in numeric_better_higher:
        values = [(p.get("name"), p.get(metric)) for p in found if p.get(metric) is not None]
        if values:
            best = max(values, key=lambda x: x[1])
            worst = min(values, key=lambda x: x[1])
            summary[metric] = {
                "best": best[0], "best_value": best[1],
                "worst": worst[0], "worst_value": worst[1],
                "lower_is_better": False,
            }

    for metric in numeric_better_lower:
        values = [(p.get("name"), p.get(metric)) for p in found if p.get(metric) is not None]
        if values:
            best = min(values, key=lambda x: x[1])
            worst = max(values, key=lambda x: x[1])
            summary[metric] = {
                "best": best[0], "best_value": best[1],
                "worst": worst[0], "worst_value": worst[1],
                "lower_is_better": True,
            }

    # Identify notable gaps/differences
    gaps: List[str] = []
    copay_values = {p.get("name"): p.get("copay_structure", "") for p in found}
    if len(set(copay_values.values())) > 1:
        zero_copay = [n for n, v in copay_values.items() if v == "0%"]
        has_copay = [n for n, v in copay_values.items() if v != "0%" and v != "NA"]
        if zero_copay and has_copay:
            gaps.append(
                f"Copay difference: {', '.join(zero_copay)} have 0% copay; "
                f"{', '.join(has_copay)} have copay"
            )

    room_rent_values = {p.get("name"): p.get("room_rent_limit", "") for p in found}
    no_limit = [n for n, v in room_rent_values.items() if "No limit" in str(v)]
    has_limit = [n for n, v in room_rent_values.items() if "No limit" not in str(v) and v != "NA"]
    if no_limit and has_limit:
        gaps.append(
            f"Room rent: {', '.join(no_limit)} have no room rent cap; "
            f"{', '.join(has_limit)} have room rent sublimit"
        )

    eazr_scores = [(p.get("name"), p.get("eazr_score")) for p in found if p.get("eazr_score")]
    if len(eazr_scores) > 1:
        max_score = max(eazr_scores, key=lambda x: x[1])
        min_score = min(eazr_scores, key=lambda x: x[1])
        if max_score[1] - min_score[1] >= 1.0:
            gaps.append(
                f"EAZR Score range: {max_score[0]} scores {max_score[1]} vs "
                f"{min_score[0]} scores {min_score[1]} — significant quality gap"
            )

    return {
        "products": found,
        "comparison_fields": comparison_fields,
        "not_found": not_found,
        "summary": summary,
        "gaps": gaps,
    }


async def get_products_by_insurer(
    insurer_name: str,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get all products offered by a specific insurer.

    Args:
        insurer_name: Insurer name (partial match accepted).
        category:     Optional — filter by category.

    Returns:
        List of product dicts ordered by EAZR score descending.
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("get_products_by_insurer_kg_unavailable", insurer_name=insurer_name)
        return []

    if category:
        query = """
        MATCH (i:Insurer)-[:OFFERS]->(p:Product)
        WHERE toLower(i.name) CONTAINS toLower($insurer_name)
           OR toLower(i.short_name) CONTAINS toLower($insurer_name)
        AND p.category = $category
        RETURN p
        ORDER BY p.eazr_score DESC
        """
        params: Dict[str, Any] = {
            "insurer_name": insurer_name.strip(),
            "category": category,
        }
    else:
        query = """
        MATCH (i:Insurer)-[:OFFERS]->(p:Product)
        WHERE toLower(i.name) CONTAINS toLower($insurer_name)
           OR toLower(i.short_name) CONTAINS toLower($insurer_name)
        RETURN p
        ORDER BY p.category, p.eazr_score DESC
        """
        params = {"insurer_name": insurer_name.strip()}

    try:
        results = await kg_client.query(
            query,
            params=params,
            query_name="get_products_by_insurer",
        )
        products = [dict(r["p"]) for r in results if "p" in r]
        logger.info(
            "get_products_by_insurer_results",
            insurer_name=insurer_name,
            category=category,
            count=len(products),
        )
        return products
    except Exception as exc:
        logger.warning("get_products_by_insurer_error", insurer_name=insurer_name, error=str(exc))
        return []
