# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
#
# TODO: [TST-2] Author adversarial test cases for guardrails:
#   - Edge cases for hallucination detection (near-threshold numbers)
#   - Compliance guardrail bypass attempts (rephrased guaranteed returns)
#   - PII leakage attempts via prompt injection
#   - Financial guardrail edge cases (currency format variations)
#
# TODO: [TST-3] Build integration test infrastructure:
#   - Docker-based test harness with ephemeral Redis, Mongo, Neo4j, Qdrant
#   - Full pipeline integration tests: upload PDF -> extract -> score -> respond
#   - Memory layer integration tests across all 6 layers
#   - KG + RAG integration tests with seeded test data
#
# TODO: [TST-5] Add real PDF test fixtures:
#   - Anonymized health, life, motor, travel, PA policy PDFs
#   - Edge cases: scanned PDFs (OCR path), password-protected, corrupted
#   - Multi-page policies with complex table layouts
#   - Bilingual (Hindi+English) policy documents
#
# TODO: [TST-6] Load testing infrastructure:
#   - Locust/k6 load test scripts for WebSocket and REST endpoints
#   - Concurrent extraction pipeline stress tests
#   - Memory layer performance benchmarks under load
#
# TODO: [TST-7] CI/CD test pipeline infrastructure:
#   - GitHub Actions workflow for unit, integration, and eval tests
#   - Docker Compose test environment for CI
#   - DQ score regression gate (fail if DQ drops below 0.80)
