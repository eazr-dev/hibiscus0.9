"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Quote comparison tool — fetches and compares real-time quotes from insurer APIs.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CATEGORY_ALIASES: Dict[str, str] = {
    # Health
    "health": "health",
    "medical": "health",
    "mediclaim": "health",
    "hospitalization": "health",
    # Life term
    "term": "life_term",
    "term life": "life_term",
    "life term": "life_term",
    # Life savings / endowment
    "life": "life_endowment",
    "endowment": "life_endowment",
    "savings plan": "life_savings",
    # ULIP
    "ulip": "ulip",
    "unit linked": "ulip",
    # Motor
    "motor": "motor",
    "car": "motor",
    "vehicle": "motor",
    "bike": "motor",
    "two wheeler": "motor",
    # Travel
    "travel": "travel",
    "international": "travel",
    # Personal Accident
    "pa": "personal_accident",
    "personal accident": "personal_accident",
    "accident": "personal_accident",
}

CITY_TIER_MAP: Dict[str, int] = {
    "mumbai": 1, "delhi": 1, "bangalore": 1, "bengaluru": 1,
    "chennai": 1, "hyderabad": 1, "pune": 1, "kolkata": 1,
    "ahmedabad": 1, "noida": 1, "gurgaon": 1, "gurugram": 1,
    "jaipur": 2, "lucknow": 2, "kanpur": 2, "nagpur": 2,
    "indore": 2, "bhopal": 2, "visakhapatnam": 2, "patna": 2,
    "vadodara": 2, "ludhiana": 2, "agra": 2, "nashik": 2,
    "coimbatore": 2, "kochi": 2, "chandigarh": 2, "surat": 2,
}

# Recommended minimum sum insured by category and city tier
MIN_SI_GUIDELINES: Dict[str, Dict[int, int]] = {
    "health": {1: 1_000_000, 2: 500_000, 3: 300_000},       # 10L / 5L / 3L
    "life_term": {1: 10_000_000, 2: 7_500_000, 3: 5_000_000},  # 1Cr / 75L / 50L
    "personal_accident": {1: 2_000_000, 2: 1_000_000, 3: 500_000},
}


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class UserRequirements:
    coverage_type: str              # Normalized category key
    age: Optional[int] = None
    sum_insured: Optional[int] = None   # INR
    premium_budget: Optional[int] = None  # Annual INR
    city: Optional[str] = None
    city_tier: int = 2
    family_size: int = 1
    existing_cover: int = 0         # Existing SI (to compute gap)
    notes: str = ""


@dataclass
class ProductMatch:
    name: str
    insurer: str
    category: str
    eazr_score: float
    sum_insured_min: int
    sum_insured_max: Optional[int]
    premium_range_min: int
    premium_range_max: int
    key_features: List[str] = field(default_factory=list)
    copay_structure: str = "0%"
    room_rent_limit: str = "N/A"
    network_hospitals: Optional[int] = None
    waiting_periods: Dict[str, int] = field(default_factory=dict)
    sub_limit_count: int = 0
    restore_benefit: bool = False
    score_breakdown: Dict[str, float] = field(default_factory=dict)


# ── Core compare function ─────────────────────────────────────────────────────

async def compare_quotes(
    requirements: UserRequirements,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Find and compare insurance products matching the user's requirements.

    Args:
        requirements: Parsed user requirements.
        top_k: Number of top products to return.

    Returns:
        Dict with:
          - products: List[ProductMatch] — ranked by composite score
          - comparison_table: str — markdown table for LLM to include
          - recommendation_note: str — 1-2 sentence guidance
          - data_source: str — "knowledge_graph" | "fallback_seed"
          - disclaimer: str — required IRDAI disclaimer
    """
    logger.info(
        "compare_quotes_start",
        coverage_type=requirements.coverage_type,
        age=requirements.age,
        sum_insured=requirements.sum_insured,
        city_tier=requirements.city_tier,
    )

    # Try KG first, fall back to seed data
    products = await _fetch_from_kg(requirements)
    data_source = "knowledge_graph"

    if not products:
        logger.info("compare_quotes_kg_empty_falling_back_to_seed")
        products = _fetch_from_seed(requirements)
        data_source = "fallback_seed"

    if not products:
        return {
            "products": [],
            "comparison_table": "",
            "recommendation_note": f"No {requirements.coverage_type} products found matching your criteria.",
            "data_source": data_source,
            "disclaimer": _IRDAI_DISCLAIMER,
        }

    # Score and rank
    scored = _score_products(products, requirements)
    top_products = scored[:top_k]

    table = _format_comparison_table(top_products, requirements)
    note = _generate_recommendation_note(top_products, requirements)

    logger.info(
        "compare_quotes_complete",
        products_found=len(products),
        top_k=len(top_products),
        data_source=data_source,
    )

    return {
        "products": top_products,
        "comparison_table": table,
        "recommendation_note": note,
        "data_source": data_source,
        "disclaimer": _IRDAI_DISCLAIMER,
    }


# ── KG query ─────────────────────────────────────────────────────────────────

async def _fetch_from_kg(req: UserRequirements) -> List[ProductMatch]:
    """Query Neo4j for matching products."""
    try:
        from hibiscus.knowledge.graph.client import get_kg_client
        kg = await get_kg_client()
        if not kg:
            return []

        # Build Cypher query
        cypher = """
        MATCH (p:Product)-[:OFFERED_BY]->(i:Insurer)
        WHERE p.category = $category
          AND ($sum_insured IS NULL OR p.sum_insured_min <= $sum_insured)
          AND ($sum_insured IS NULL OR (p.sum_insured_max IS NULL OR p.sum_insured_max >= $sum_insured))
          AND ($budget IS NULL OR p.premium_range_min <= $budget * 1.5)
        RETURN p, i.name AS insurer_name
        ORDER BY p.eazr_score DESC
        LIMIT 20
        """

        params = {
            "category": req.coverage_type,
            "sum_insured": req.sum_insured,
            "budget": req.premium_budget,
        }

        results = await kg.run_query(cypher, params)
        if not results:
            return []

        products = []
        for row in results:
            p = row.get("p", {})
            products.append(ProductMatch(
                name=p.get("name", ""),
                insurer=row.get("insurer_name", ""),
                category=p.get("category", ""),
                eazr_score=float(p.get("eazr_score", 0.0)),
                sum_insured_min=int(p.get("sum_insured_min", 0)),
                sum_insured_max=p.get("sum_insured_max"),
                premium_range_min=int(p.get("premium_range_min", 0)),
                premium_range_max=int(p.get("premium_range_max", 0)),
                key_features=p.get("key_features", []),
                copay_structure=p.get("copay_structure", "0%"),
                room_rent_limit=p.get("room_rent_limit", "N/A"),
                network_hospitals=p.get("network_hospitals"),
                waiting_periods=p.get("waiting_periods", {}),
                sub_limit_count=int(p.get("sub_limit_count", 0)),
                restore_benefit=bool(p.get("restore_benefit", False)),
            ))
        return products

    except Exception as e:
        logger.warning("compare_quotes_kg_error", error=str(e))
        return []


# ── Seed data fallback ────────────────────────────────────────────────────────

def _fetch_from_seed(req: UserRequirements) -> List[ProductMatch]:
    """Fall back to seed data if KG unavailable."""
    try:
        from hibiscus.knowledge.graph.seed.products import PRODUCTS
        results = []
        for p in PRODUCTS:
            if p.get("category") != req.coverage_type:
                continue
            # Filter by sum_insured if specified
            if req.sum_insured:
                si_min = p.get("sum_insured_min", 0)
                si_max = p.get("sum_insured_max")
                if si_max and si_max < req.sum_insured:
                    continue
                if si_min > req.sum_insured * 2:
                    continue
            # Filter by budget
            if req.premium_budget:
                if p.get("premium_range_min", 0) > req.premium_budget * 1.5:
                    continue

            results.append(ProductMatch(
                name=p.get("name", ""),
                insurer=p.get("insurer_name", ""),
                category=p.get("category", ""),
                eazr_score=float(p.get("eazr_score", 0.0)),
                sum_insured_min=int(p.get("sum_insured_min", 0)),
                sum_insured_max=p.get("sum_insured_max"),
                premium_range_min=int(p.get("premium_range_min", 0)),
                premium_range_max=int(p.get("premium_range_max", 0)),
                key_features=p.get("key_features", []),
                copay_structure=p.get("copay_structure", "0%"),
                room_rent_limit=p.get("room_rent_limit", "N/A"),
                network_hospitals=p.get("network_hospitals"),
                waiting_periods=p.get("waiting_periods", {}),
                sub_limit_count=int(p.get("sub_limit_count", 0)),
                restore_benefit=bool(p.get("restore_benefit", False)),
            ))
        return results
    except Exception as e:
        logger.warning("compare_quotes_seed_error", error=str(e))
        return []


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_products(
    products: List[ProductMatch],
    req: UserRequirements,
) -> List[ProductMatch]:
    """
    Score products by weighted composite:
    - EAZR Score: 40%
    - Budget fit: 25% (how close premium is to budget)
    - Sum insured fit: 20% (does it cover required SI)
    - Feature quality: 15% (no sub-limits, no copay, restore benefit)
    """
    for p in products:
        score = 0.0
        breakdown = {}

        # EAZR Score (0-10 → 0-4)
        eazr_contribution = (p.eazr_score / 10) * 4.0
        score += eazr_contribution
        breakdown["eazr"] = round(eazr_contribution, 2)

        # Budget fit (0-2.5)
        if req.premium_budget and p.premium_range_max > 0:
            mid_premium = (p.premium_range_min + p.premium_range_max) / 2
            ratio = req.premium_budget / mid_premium
            if ratio >= 1.0:
                budget_fit = min(2.5, 2.5 * ratio / 2)
            else:
                budget_fit = 2.5 * ratio
            score += budget_fit
            breakdown["budget_fit"] = round(budget_fit, 2)
        else:
            score += 1.25  # neutral if no budget specified
            breakdown["budget_fit"] = 1.25

        # SI fit (0-2)
        if req.sum_insured and p.sum_insured_min > 0:
            if p.sum_insured_max is None or p.sum_insured_max >= req.sum_insured:
                score += 2.0
                breakdown["si_fit"] = 2.0
            elif p.sum_insured_max >= req.sum_insured * 0.8:
                score += 1.0
                breakdown["si_fit"] = 1.0
            else:
                breakdown["si_fit"] = 0.0
        else:
            score += 1.0
            breakdown["si_fit"] = 1.0

        # Feature quality (0-1.5)
        feature_score = 0.0
        if p.copay_structure == "0%" or p.copay_structure == "None":
            feature_score += 0.5
        if p.room_rent_limit in ("No limit", "No Room Rent Limit", "Unlimited"):
            feature_score += 0.5
        if p.restore_benefit:
            feature_score += 0.3
        if p.sub_limit_count <= 3:
            feature_score += 0.2
        score += feature_score
        breakdown["features"] = round(feature_score, 2)

        p.score_breakdown = breakdown
        p.eazr_score = round(score, 2)  # overwrite with composite score

    return sorted(products, key=lambda x: x.eazr_score, reverse=True)


# ── Formatting ────────────────────────────────────────────────────────────────

def _format_inr(amount: int) -> str:
    """Format INR amount in Indian notation (lakhs/crores)."""
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.1f}Cr"
    elif amount >= 100_000:
        return f"₹{amount / 100_000:.0f}L"
    else:
        return f"₹{amount:,}"


def _format_comparison_table(
    products: List[ProductMatch],
    req: UserRequirements,
) -> str:
    """Format a markdown comparison table for the top products."""
    if not products:
        return ""

    # Determine which columns to show based on category
    is_health = req.coverage_type == "health"
    is_life = req.coverage_type in ("life_term", "life_endowment", "life_savings", "ulip")

    # Header row
    headers = ["Feature"] + [f"{p.insurer[:12]}" for p in products]
    col_width = 14
    separator = "|" + "|".join("-" * (col_width + 2) for _ in headers) + "|"
    fmt_row = lambda cells: "| " + " | ".join(str(c).ljust(col_width) for c in cells) + " |"

    rows = [fmt_row(headers), separator]

    # Sum Insured range
    si_row = ["Sum Insured"] + [
        f"{_format_inr(p.sum_insured_min)}–{_format_inr(p.sum_insured_max) if p.sum_insured_max else '∞'}"
        for p in products
    ]
    rows.append(fmt_row(si_row))

    # Est. Annual Premium
    premium_row = ["Est. Premium*"] + [
        f"{_format_inr(p.premium_range_min)}–{_format_inr(p.premium_range_max)}"
        for p in products
    ]
    rows.append(fmt_row(premium_row))

    # Health-specific rows
    if is_health:
        copay_row = ["Co-pay"] + [p.copay_structure or "0%" for p in products]
        rows.append(fmt_row(copay_row))

        room_row = ["Room Rent"] + [
            (p.room_rent_limit or "N/A")[:col_width] for p in products
        ]
        rows.append(fmt_row(room_row))

        restore_row = ["Restore Benefit"] + [
            "Yes" if p.restore_benefit else "No" for p in products
        ]
        rows.append(fmt_row(restore_row))

        ped_row = ["PED Wait (days)"] + [
            str(p.waiting_periods.get("pre_existing", "?")) for p in products
        ]
        rows.append(fmt_row(ped_row))

    # EAZR Score
    score_row = ["EAZR Score"] + [
        str(p.score_breakdown.get("eazr", 0.0) / 4.0 * 10)[:4] for p in products
    ]
    rows.append(fmt_row(score_row))

    table = "\n".join(rows)
    table += "\n\n*Premium estimates based on knowledge base data. Get exact quotes from insurer."

    return table


def _generate_recommendation_note(
    products: List[ProductMatch],
    req: UserRequirements,
) -> str:
    """Generate a 1-2 sentence recommendation note."""
    if not products:
        return ""

    top = products[0]
    note = (
        f"Based on your requirements, **{top.name}** by {top.insurer} "
        f"offers the best combination of coverage and value"
    )

    if req.sum_insured:
        si_str = _format_inr(req.sum_insured)
        note += f" for a {si_str} cover"

    if req.city_tier == 1:
        note += " in a metro city"

    note += "."

    if len(products) > 1:
        second = products[1]
        note += (
            f" **{second.name}** by {second.insurer} is also worth considering "
            f"if you prioritize lower premiums."
        )

    return note


# ── Requirements parser ───────────────────────────────────────────────────────

def parse_requirements(
    message: str,
    user_profile: Optional[Dict[str, Any]] = None,
) -> UserRequirements:
    """
    Parse user requirements from a natural language message.
    Extracts: coverage_type, age, sum_insured, premium_budget, city.
    """
    msg_lower = message.lower()
    profile = user_profile or {}

    # Coverage type
    coverage_type = "health"  # default
    for alias, cat in CATEGORY_ALIASES.items():
        if alias in msg_lower:
            coverage_type = cat
            break

    # Age
    age = profile.get("age")
    age_match = re.search(r"\b(\d{1,2})\s*(?:year|yr|age|years?\s+old)", msg_lower)
    if age_match:
        age = int(age_match.group(1))

    # Sum insured
    sum_insured = None
    si_patterns = [
        (r"(\d+)\s*(?:cr|crore)", lambda m: int(float(m.group(1)) * 10_000_000)),
        (r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l\b)", lambda m: int(float(m.group(1)) * 100_000)),
        (r"₹\s*(\d{1,2}),(\d{2}),(\d{3})", lambda m: int(m.group(1)) * 10_000_000 + int(m.group(2)) * 100_000 + int(m.group(3))),
    ]
    for pattern, converter in si_patterns:
        m = re.search(pattern, msg_lower)
        if m:
            try:
                sum_insured = converter(m)
            except Exception:
                pass
            break

    # Premium budget
    premium_budget = None
    budget_match = re.search(
        r"(?:budget|afford|pay(?:ing)?\s+(?:up\s+to)?|under)\s*[₹]?\s*(\d+)\s*(?:k|thousand|lakh|l)?",
        msg_lower,
    )
    if budget_match:
        raw = int(budget_match.group(1))
        suffix_match = re.search(r"\d+\s*(k|thousand|lakh|l)", budget_match.group(0).lower())
        if suffix_match:
            suffix = suffix_match.group(1)
            if suffix in ("k", "thousand"):
                premium_budget = raw * 1000
            elif suffix in ("lakh", "l"):
                premium_budget = raw * 100_000
        else:
            premium_budget = raw

    # City
    city = profile.get("city", "")
    city_tier = profile.get("city_tier", 2)
    for city_name, tier in CITY_TIER_MAP.items():
        if city_name in msg_lower:
            city = city_name.title()
            city_tier = tier
            break

    # Family size
    family_size = 1
    family_match = re.search(r"(?:family\s+of|for\s+(\d+))\s*(\d+)?", msg_lower)
    if family_match:
        for g in [family_match.group(1), family_match.group(2)]:
            if g and g.isdigit():
                family_size = int(g)
                break

    req = UserRequirements(
        coverage_type=coverage_type,
        age=age,
        sum_insured=sum_insured,
        premium_budget=premium_budget,
        city=city,
        city_tier=city_tier,
        family_size=family_size,
    )

    logger.info(
        "requirements_parsed",
        coverage_type=req.coverage_type,
        age=req.age,
        sum_insured=req.sum_insured,
        city_tier=req.city_tier,
    )
    return req


# ── Disclaimer ────────────────────────────────────────────────────────────────

_IRDAI_DISCLAIMER = (
    "**Disclaimer**: Premium figures shown are estimated annual ranges from our knowledge base "
    "and may vary significantly based on your age, medical history, and exact coverage chosen. "
    "This comparison is for informational purposes only and does not constitute a formal quote. "
    "Please obtain actual quotes from insurance companies or a licensed IRDAI-registered advisor "
    "before making any purchase decision. EAZR is not an insurance company or broker."
)
