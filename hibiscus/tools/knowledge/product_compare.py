"""
Tool: Product Compare — Markdown Comparison Tables
===================================================
Wraps compare_products() from product_lookup with rich markdown formatting.
Used by Recommender and Researcher agents to render comparison tables.

Functions
---------
compare_products_table(product_names)   — side-by-side markdown table
compare_products_summary(product_names) — structured comparison dict
"""
from typing import Any, Dict, List

from hibiscus.observability.logger import get_logger
from hibiscus.tools.knowledge.product_lookup import compare_products

logger = get_logger("hibiscus.tools.knowledge.product_compare")

# Fields to include in markdown comparison table
_TABLE_FIELDS = [
    ("insurer_name", "Insurer"),
    ("category", "Category"),
    ("eazr_score", "EAZR Score"),
    ("sum_insured_min", "Min Sum Insured"),
    ("sum_insured_max", "Max Sum Insured"),
    ("copay_structure", "Copay"),
    ("room_rent_limit", "Room Rent"),
    ("sub_limit_count", "Sub-limits"),
    ("exclusion_count", "Exclusions"),
    ("waiting_periods", "Waiting Periods"),
    ("key_features", "Key Features"),
]


def _fmt_inr(value: Any) -> str:
    """Format a number as Indian ₹ (lakhs/crores)."""
    if value is None:
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if n >= 1_00_00_000:
        return f"₹{n / 1_00_00_000:.1f} Cr"
    if n >= 1_00_000:
        return f"₹{n / 1_00_000:.1f}L"
    if n >= 1_000:
        return f"₹{n / 1_000:.0f}K"
    return f"₹{n:.0f}"


def _fmt_field(field: str, value: Any) -> str:
    """Format a field value for the comparison table."""
    if value is None:
        return "—"
    inr_fields = {"sum_insured_min", "sum_insured_max", "premium_range_min", "premium_range_max"}
    if field in inr_fields:
        return _fmt_inr(value)
    if isinstance(value, list):
        if not value:
            return "—"
        return "; ".join(str(v) for v in value[:3]) + (" …" if len(value) > 3 else "")
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


async def compare_products_table(product_names: List[str]) -> str:
    """
    Build a markdown comparison table for the given products.

    Args:
        product_names: List of 2–5 product names.

    Returns:
        Markdown string with:
          - Side-by-side comparison table
          - Notable gaps section
          - Summary (best/worst per key metric)

    Returns a "no data" message if none of the products are found.
    """
    if not product_names:
        return "No product names provided for comparison."

    result = await compare_products(product_names)
    products = result.get("products", [])
    not_found = result.get("not_found", [])
    gaps = result.get("gaps", [])
    summary = result.get("summary", {})

    if not products:
        msg = "Could not find comparison data for: " + ", ".join(not_found)
        msg += "\n\nTry searching by insurer name or use the full product name."
        return msg

    # ── Build comparison table ──────────────────────────────────────────
    product_names_found = [p.get("name", "Unknown") for p in products]
    header = "| Feature | " + " | ".join(product_names_found) + " |"
    separator = "|---------|" + "|---------|" * len(products)

    rows = []
    for field_key, field_label in _TABLE_FIELDS:
        cells = [_fmt_field(field_key, p.get(field_key)) for p in products]
        rows.append(f"| {field_label} | " + " | ".join(cells) + " |")

    table = "\n".join([header, separator] + rows)

    # ── Notable gaps ────────────────────────────────────────────────────
    gaps_section = ""
    if gaps:
        gaps_section = "\n\n**Notable Differences:**\n" + "\n".join(f"- {g}" for g in gaps)

    # ── Summary ─────────────────────────────────────────────────────────
    summary_lines = []
    label_map = {
        "eazr_score": "Best EAZR Score",
        "exclusion_count": "Fewest Exclusions",
        "sub_limit_count": "Fewest Sub-limits",
        "sum_insured_max": "Highest Coverage",
    }
    for metric, label in label_map.items():
        if metric in summary:
            s = summary[metric]
            summary_lines.append(f"- **{label}:** {s['best']} ({_fmt_field(metric, s['best_value'])})")

    summary_section = ""
    if summary_lines:
        summary_section = "\n\n**Summary:**\n" + "\n".join(summary_lines)

    # ── Not found notice ────────────────────────────────────────────────
    not_found_note = ""
    if not_found:
        not_found_note = f"\n\n*Products not found in database: {', '.join(not_found)}*"

    logger.info(
        "compare_products_table",
        requested=len(product_names),
        found=len(products),
        not_found=len(not_found),
    )

    return table + gaps_section + summary_section + not_found_note


async def compare_products_summary(product_names: List[str]) -> Dict[str, Any]:
    """
    Return structured comparison data (not markdown) for programmatic use.

    Args:
        product_names: List of 2–5 product names.

    Returns:
        Dict from compare_products() with added "markdown_table" key.
    """
    result = await compare_products(product_names)
    # Attach markdown table for convenience
    try:
        result["markdown_table"] = await compare_products_table(product_names)
    except Exception:
        result["markdown_table"] = ""
    return result
