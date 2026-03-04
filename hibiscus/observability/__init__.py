# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
#
# TODO: [OTEL] Integrate OpenTelemetry for distributed tracing and metrics.
# Plan:
#   1. Add opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp
#      to pyproject.toml dependencies.
#   2. Initialize TracerProvider in main.py lifespan with OTLP exporter
#      (configure via OTEL_EXPORTER_OTLP_ENDPOINT env var).
#   3. Instrument FastAPI with opentelemetry-instrumentation-fastapi for
#      automatic HTTP span creation.
#   4. Add manual spans for: LLM calls (per-tier), KG queries, RAG searches,
#      extraction pipeline stages, and memory assembly.
#   5. Export Prometheus metrics via opentelemetry-exporter-prometheus to
#      replace the current custom metrics.py (or bridge both).
#   6. Add trace context propagation to async memory extraction tasks.
#   7. Configure sampling (100% in dev, 10% in production) via
#      OTEL_TRACES_SAMPLER env var.
