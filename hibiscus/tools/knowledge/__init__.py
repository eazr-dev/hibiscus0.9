# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
from .insurer_lookup import (
    lookup_insurer,
    get_insurer_benchmarks,
    list_insurers_by_category,
    compare_insurers,
)
from .product_lookup import (
    lookup_product,
    search_products,
    compare_products,
    get_products_by_insurer,
)
from .benchmark_lookup import (
    get_benchmark,
    evaluate_against_benchmark,
    get_coverage_recommendation,
    get_premium_benchmark,
    list_benchmarks_by_category,
)
from .regulation_lookup import (
    lookup_regulation,
    get_rights_for_situation,
    lookup_ombudsman_for_state,
    get_consumer_rights_summary,
    search_regulations_by_category,
)

__all__ = [
    # Insurer
    "lookup_insurer",
    "get_insurer_benchmarks",
    "list_insurers_by_category",
    "compare_insurers",
    # Product
    "lookup_product",
    "search_products",
    "compare_products",
    "get_products_by_insurer",
    # Benchmark
    "get_benchmark",
    "evaluate_against_benchmark",
    "get_coverage_recommendation",
    "get_premium_benchmark",
    "list_benchmarks_by_category",
    # Regulation
    "lookup_regulation",
    "get_rights_for_situation",
    "lookup_ombudsman_for_state",
    "get_consumer_rights_summary",
    "search_regulations_by_category",
]
