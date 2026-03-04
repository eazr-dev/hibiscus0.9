"""
HibiscusBench — Evaluation suite for Hibiscus AI engine.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from .evaluator import HibiscusEvaluator
from .metrics import evaluate_response, aggregate_results, EvalResult

__all__ = ["HibiscusEvaluator", "evaluate_response", "aggregate_results", "EvalResult"]
