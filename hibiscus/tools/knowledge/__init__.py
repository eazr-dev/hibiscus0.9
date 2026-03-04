"""
Knowledge Graph Tool Package
==============================
Tools for querying the Hibiscus Neo4j Knowledge Graph.
Used by PolicyAnalyzer, Recommender, RiskDetector, RegulationEngine,
GrievanceNavigator, TaxAdvisor, and Educator agents.

All tools are async and handle KG unavailability gracefully — they return
empty results ([] or {}) rather than raising exceptions when Neo4j is down.

Exports
-------
Insurer tools:
    lookup_insurer(name)
    get_insurer_benchmarks(insurer_id)
    list_insurers_by_category(category)
    compare_insurers(names)

Product tools:
    lookup_product(name, insurer_name=None)
    search_products(category, filters=None)
    compare_products(product_ids)
    get_products_by_insurer(insurer_name, category=None)

Benchmark tools:
    get_benchmark(metric, category, age_group=None)
    evaluate_against_benchmark(metric, value, category)
    get_coverage_recommendation(category, age_group, annual_income=None)
    get_premium_benchmark(category, age_group)
    list_benchmarks_by_category(category)

Regulation tools:
    lookup_regulation(topic)
    get_rights_for_situation(situation)
    lookup_ombudsman_for_state(state)
    get_consumer_rights_summary()
    search_regulations_by_category(category)
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
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
