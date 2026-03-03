"""HibiscusBench — Evaluation suite for Hibiscus AI engine."""
from .evaluator import HibiscusEvaluator
from .metrics import evaluate_response, aggregate_results, EvalResult

__all__ = ["HibiscusEvaluator", "evaluate_response", "aggregate_results", "EvalResult"]
