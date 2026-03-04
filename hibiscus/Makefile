# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
# Developer Makefile — dev, test, seed, eval, monitoring
# Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.

.PHONY: dev dev-hibiscus down test test-unit test-integration eval \
        seed-kg seed-rag seed-all health-check logs costs metrics \
        refresh-kg refresh-rag eval-report

COMPOSE = docker compose -f ../docker-compose.yml

# ── Development ──────────────────────────────────────────────────
dev:
	@echo "Starting Hibiscus stack..."
	$(COMPOSE) up -d
	@echo ""
	@echo "Services:"
	@echo "  Hibiscus API:  http://localhost:8001/hibiscus/docs"
	@echo "  Neo4j Browser: http://localhost:7474"
	@echo "  Qdrant UI:     http://localhost:6333/dashboard"

dev-hibiscus:
	@echo "Starting Hibiscus API locally (fast reload)..."
	uvicorn hibiscus.main:app --host 0.0.0.0 --port 8001 --reload

down:
	$(COMPOSE) down

# ── Database Seeding ────────────────────────────────────────────
seed-kg:
	@echo "Seeding Neo4j Knowledge Graph..."
	docker exec hibiscus-api python -m hibiscus.knowledge.graph.seed

seed-rag:
	@echo "Ingesting RAG corpus into Qdrant..."
	docker exec hibiscus-api python -m hibiscus.knowledge.rag.ingestion

seed-all: seed-kg seed-rag
	@echo "All knowledge infrastructure seeded."

# ── Testing ──────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

# ── Evaluation ───────────────────────────────────────────────────
eval:
	@echo "Running HibiscusBench evaluation suite..."
	python -m hibiscus.evaluation.bench

eval-health:
	python -m hibiscus.evaluation.bench --category health

eval-adversarial:
	python -m hibiscus.evaluation.bench --category adversarial

eval-report:
	python -m hibiscus.evaluation.bench --report

# ── Monitoring ───────────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f hibiscus-api

costs:
	@echo "LLM cost summary (last 24h)..."
	docker exec hibiscus-api python -c "from hibiscus.observability.cost_tracker import print_summary; import asyncio; asyncio.run(print_summary())"

metrics:
	@echo "Key metrics..."
	curl -s http://localhost:8001/hibiscus/metrics | python -m json.tool

health-check:
	@echo "Checking all Hibiscus dependencies..."
	curl -s http://localhost:8001/hibiscus/health | python -m json.tool

# ── Maintenance ──────────────────────────────────────────────────
refresh-kg: seed-kg
refresh-rag: seed-rag
