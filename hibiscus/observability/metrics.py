"""
Prometheus Metrics
==================
All Hibiscus operational metrics exposed at GET /hibiscus/metrics.

Uses prometheus_client library. Metrics are process-global singletons
registered against the default REGISTRY so they accumulate across requests
within the same process lifetime.

Instrumented:
- conversations_total (Counter) — by complexity, category
- llm_calls_total (Counter) — by model, agent
- llm_cost_total_inr (Gauge) — rolling total LLM spend in INR
- guardrail_failures_total (Counter) — by guardrail_type
- errors_total (Counter) — by error_type
- response_latency_seconds (Histogram) — by complexity tier
- confidence_score (Histogram) — by agent_name
- agent_latency_seconds (Histogram) — by agent_name
- cache_hits_total (Counter) — response cache hits
- cache_misses_total (Counter) — response cache misses

All helper functions are safe to call from async context —
prometheus_client metrics are backed by thread-safe atomic operations.

If prometheus_client is not installed, all functions silently become no-ops
so the application continues to run without instrumentation.
"""

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Attempt to import prometheus_client ───────────────────────────────────────
# All metrics are set to None when the library is missing; every helper
# function checks _PROMETHEUS_AVAILABLE before touching any metric object.

_PROMETHEUS_AVAILABLE = False

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CONTENT_TYPE_LATEST,
        generate_latest,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning(
        "prometheus_client_not_installed",
        note="Install prometheus_client to enable /hibiscus/metrics. "
             "All metric helpers are no-ops until then.",
    )

# ── Latency buckets ───────────────────────────────────────────────────────────
# Designed for Hibiscus Phase 3 targets:
#   L1/L2 → <5s, L3/L4 → <15s.  Fine-grained below 5s, coarser above.
_LATENCY_BUCKETS = (
    0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 60.0
)

# Confidence score buckets: 0.0 – 1.0 in steps of 0.1
_CONFIDENCE_BUCKETS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)

# ── Metric singletons ─────────────────────────────────────────────────────────
# Declared at module level so they are created once and accumulate values for
# the lifetime of the process.  All declarations are guarded by
# _PROMETHEUS_AVAILABLE so the file can be imported safely without the library.

if _PROMETHEUS_AVAILABLE:
    # -- Conversations --
    conversations_total = Counter(
        "hibiscus_conversations_total",
        "Total conversations processed by Hibiscus",
        labelnames=["complexity", "category"],
    )

    # -- LLM --
    llm_calls_total = Counter(
        "hibiscus_llm_calls_total",
        "Total LLM API calls made by Hibiscus agents",
        labelnames=["model", "agent"],
    )

    llm_cost_total_inr = Gauge(
        "hibiscus_llm_cost_total_inr",
        "Rolling total LLM spend in Indian Rupees (INR) since process start",
    )

    # -- Guardrails --
    guardrail_failures_total = Counter(
        "hibiscus_guardrail_failures_total",
        "Total guardrail failures detected",
        labelnames=["guardrail_type"],
    )

    # -- Errors --
    errors_total = Counter(
        "hibiscus_errors_total",
        "Total pipeline errors by type",
        labelnames=["error_type"],
    )

    # -- Latency --
    response_latency_seconds = Histogram(
        "hibiscus_response_latency_seconds",
        "End-to-end response latency in seconds by complexity tier",
        labelnames=["complexity"],
        buckets=_LATENCY_BUCKETS,
    )

    agent_latency_seconds = Histogram(
        "hibiscus_agent_latency_seconds",
        "Per-agent execution latency in seconds",
        labelnames=["agent_name"],
        buckets=_LATENCY_BUCKETS,
    )

    # -- Confidence --
    confidence_score = Histogram(
        "hibiscus_confidence_score",
        "Agent output confidence score distribution (0.0–1.0)",
        labelnames=["agent_name"],
        buckets=_CONFIDENCE_BUCKETS,
    )

    # -- Cache --
    cache_hits_total = Counter(
        "hibiscus_cache_hits_total",
        "Total response cache hits (Redis response cache)",
    )

    cache_misses_total = Counter(
        "hibiscus_cache_misses_total",
        "Total response cache misses (Redis response cache)",
    )

    # -- Fraud --
    fraud_alerts_total = Counter(
        "hibiscus_fraud_alerts_total",
        "Total fraud/anomaly alerts detected",
        labelnames=["severity", "alert_type"],
    )

else:
    # Placeholder so module-level names are defined even without the library.
    conversations_total = None
    llm_calls_total = None
    llm_cost_total_inr = None
    guardrail_failures_total = None
    errors_total = None
    response_latency_seconds = None
    agent_latency_seconds = None
    confidence_score = None
    cache_hits_total = None
    cache_misses_total = None
    fraud_alerts_total = None


# ── Helper functions ──────────────────────────────────────────────────────────
# Each function is a thin wrapper that:
#   1. Returns immediately (no-op) when prometheus_client is not installed.
#   2. Catches any unexpected exception from prometheus_client itself so that
#      a metrics failure never breaks a production request path.


def record_conversation(complexity: str, category: str) -> None:
    """
    Increment conversations_total for the given complexity/category pair.

    Args:
        complexity: One of "L1", "L2", "L3", "L4".
        category:   Intent category (e.g. "health", "life", "motor", "general_chat").
    """
    if not _PROMETHEUS_AVAILABLE or conversations_total is None:
        return
    try:
        conversations_total.labels(complexity=complexity, category=category).inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_conversation_error", error=str(exc))


def record_llm_call(
    model: str,
    agent: str,
    cost_inr: float,
    latency_s: float,
) -> None:
    """
    Record a completed LLM API call.

    Increments llm_calls_total, adds cost_inr to the rolling gauge, and
    records the per-agent latency in agent_latency_seconds.

    Args:
        model:     LiteLLM model string (e.g. "deepseek/deepseek-chat").
        agent:     Agent name that initiated the call (e.g. "policy_analyzer").
        cost_inr:  Cost of this individual call in INR.
        latency_s: Wall-clock duration of the LLM call in seconds.
    """
    if not _PROMETHEUS_AVAILABLE:
        return
    try:
        if llm_calls_total is not None:
            llm_calls_total.labels(model=model, agent=agent).inc()
        if llm_cost_total_inr is not None:
            llm_cost_total_inr.inc(cost_inr)
        if agent_latency_seconds is not None:
            agent_latency_seconds.labels(agent_name=agent).observe(latency_s)
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_llm_call_error", error=str(exc))


def record_guardrail_failure(guardrail_type: str) -> None:
    """
    Increment guardrail_failures_total for the given guardrail type.

    Args:
        guardrail_type: One of "hallucination", "compliance", "financial",
                        "emotional", "pii".
    """
    if not _PROMETHEUS_AVAILABLE or guardrail_failures_total is None:
        return
    try:
        guardrail_failures_total.labels(guardrail_type=guardrail_type).inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_guardrail_failure_error", error=str(exc))


def record_error(error_type: str) -> None:
    """
    Increment errors_total for the given error type.

    Args:
        error_type: Short snake_case label (e.g. "llm_exhausted",
                    "extraction_failed", "kg_unavailable").
    """
    if not _PROMETHEUS_AVAILABLE or errors_total is None:
        return
    try:
        errors_total.labels(error_type=error_type).inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_error_error", error=str(exc))


def record_response_latency(complexity: str, latency_s: float) -> None:
    """
    Observe end-to-end response latency for a given complexity tier.

    Args:
        complexity: One of "L1", "L2", "L3", "L4".
        latency_s:  Total wall-clock response time in seconds.
    """
    if not _PROMETHEUS_AVAILABLE or response_latency_seconds is None:
        return
    try:
        response_latency_seconds.labels(complexity=complexity).observe(latency_s)
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_response_latency_error", error=str(exc))


def record_confidence(agent_name: str, score: float) -> None:
    """
    Observe a confidence score emitted by an agent.

    Args:
        agent_name: Name of the agent that produced the score.
        score:      Float in [0.0, 1.0].
    """
    if not _PROMETHEUS_AVAILABLE or confidence_score is None:
        return
    try:
        # Clamp to [0.0, 1.0] to protect histogram bucket assumptions.
        clamped = max(0.0, min(1.0, score))
        confidence_score.labels(agent_name=agent_name).observe(clamped)
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_confidence_error", error=str(exc))


def record_cache_hit() -> None:
    """Increment the response cache hit counter."""
    if not _PROMETHEUS_AVAILABLE or cache_hits_total is None:
        return
    try:
        cache_hits_total.inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_cache_hit_error", error=str(exc))


def record_cache_miss() -> None:
    """Increment the response cache miss counter."""
    if not _PROMETHEUS_AVAILABLE or cache_misses_total is None:
        return
    try:
        cache_misses_total.inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_cache_miss_error", error=str(exc))


def record_fraud_alert(severity: str, alert_type: str) -> None:
    """Increment the fraud alerts counter."""
    if not _PROMETHEUS_AVAILABLE or fraud_alerts_total is None:
        return
    try:
        fraud_alerts_total.labels(severity=severity, alert_type=alert_type).inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("metrics_record_fraud_alert_error", error=str(exc))


def get_metrics_text() -> str:
    """
    Return Prometheus text-format exposition for all registered metrics.

    Returns:
        UTF-8 decoded string in Prometheus text format 0.0.4.
        Returns a comment-only string if prometheus_client is not available.
    """
    if not _PROMETHEUS_AVAILABLE:
        return "# prometheus_client not installed — install it to enable metrics\n"
    try:
        raw: bytes = generate_latest()
        return raw.decode("utf-8")
    except Exception as exc:
        logger.warning("metrics_generate_latest_error", error=str(exc))
        return f"# metrics generation error: {exc}\n"
