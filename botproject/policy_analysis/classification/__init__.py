"""
Policy Classification Module — Hibiscus Classifier v2.0

Provides production-grade policy type classification using a 3-tier
cascading pipeline: Rule-based → Multi-Signal Scoring → LLM (stub).
"""

from policy_analysis.classification.hibiscus_policy_classifier import (
    classify_policy,
    get_policy_type_for_analysis,
    get_classifier,
    ClassificationResult,
    PolicyType,
    PolicyCategory,
    ConfidenceLevel,
    HibiscusPolicyClassifier,
)
from policy_analysis.classification.db_service import (
    get_db_matcher,
    match_product_from_db,
    get_product_by_uin,
)

__all__ = [
    "classify_policy",
    "get_policy_type_for_analysis",
    "get_classifier",
    "ClassificationResult",
    "PolicyType",
    "PolicyCategory",
    "ConfidenceLevel",
    "HibiscusPolicyClassifier",
    "get_db_matcher",
    "match_product_from_db",
    "get_product_by_uin",
]
