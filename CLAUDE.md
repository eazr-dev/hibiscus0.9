# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hibiscus v0.9 is EAZR AI's insurance intelligence engine — a 12-agent orchestration system for Indian insurance consumers providing policy analysis, recommendations, claims guidance, tax advisory, and portfolio optimization.

**Master blueprint:** `HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md`
**API docs:** `hibiscus/docs/api_guide.md` | **Architecture:** `hibiscus/docs/architecture.md`

## Commands

All commands run from `hibiscus/` directory unless noted otherwise.

```bash
# Development
make dev                # Start full Docker stack (API + Postgres + Mongo + Redis + Neo4j + Qdrant)
make dev-hibiscus       # Local fast-reload (uvicorn --reload on :8001)
make down               # Stop all services

# Testing (pytest with pytest-asyncio, asyncio_mode="auto")
make test               # All tests: pytest tests/ -v --tb=short
make test-unit          # Unit only: pytest tests/unit/ -v --tb=short
make test-integration   # Integration only: pytest tests/integration/ -v --tb=short
pytest tests/unit/test_guardrails.py -v --tb=short          # Single file
pytest tests/unit/test_guardrails.py::test_hallucination -v # Single test

# Linting (no Makefile targets — run manually)
ruff check hibiscus/    # Lint (line-length=100, target=py312)
ruff format hibiscus/   # Format
mypy hibiscus/          # Type check

# Knowledge seeding (runs inside Docker container)
make seed-kg            # Neo4j knowledge graph
make seed-rag           # Qdrant RAG corpus
make seed-all           # Both

# Evaluation
make eval               # HibiscusBench (120 test cases)
make eval-health        # Health category only
make eval-report        # Full report

# Monitoring
make health-check       # curl /hibiscus/health
make metrics            # curl /hibiscus/metrics
make logs               # Docker logs -f
make costs              # LLM cost summary
```

## Architecture

### Orchestration Flow (LangGraph StateGraph)

```
assemble_context → classify_intent → [routing decision]
  ├─ simple (L1/L2, non-distressed) → direct_llm ─────────────┐
  └─ complex (L3/L4, agents needed, or distressed) → plan_execution → dispatch_agents → aggregate_response ─┐
                                                                                                             │
                                                          check_guardrails ← ────────────────────────────────┘
                                                               │
                                                          store_memory → END
```

- **State:** `HibiscusState` (TypedDict, ~35 fields). `agent_outputs` uses `Annotated[List, operator.add]` reducer for parallel accumulation.
- **Entry point:** `from hibiscus.orchestrator.graph import run_graph`
- **Graph nodes** are in `hibiscus/orchestrator/nodes/` — each is a separate module.

### Docker Compose

The docker compose file is `docker-compose.yml` (in the repo root).

### LLM Routing (3-tier via LiteLLM)

| Tier | Model | When |
|------|-------|------|
| T1 | `deepseek/deepseek-chat` (80%) | Default — intent classification, most agents |
| T2 | `deepseek/deepseek-reasoner` (15%) | Math-heavy: surrender calcs, IRR, portfolio optimization, L4 complexity |
| T3 | `anthropic/claude-sonnet-4-5` (5%) | Safety net: distressed users, low-confidence (<0.70) financial tasks |

Fallback chain: T1 → T2 → T3. Model selection logic in `hibiscus/llm/model_selector.py`, router in `hibiscus/llm/router.py`. Both sync (`call_llm`) and streaming (`stream_llm`) supported.

### Extraction Pipeline (ABSORB) — `hibiscus/extraction/`

PDF → `processor.py` (pdfplumber → PyPDF2 fallback → pytesseract OCR) → `classifier.py` (UIN regex → keyword scoring → LLM) → type-specific extractors (`extractors/{health,life,motor,travel,pa}.py` inheriting `base.py`) → `validation.py` → `scoring.py` → `gap_analysis.py` → structured result stored in MongoDB.

### Memory System — `hibiscus/memory/`

6 layers assembled in parallel via `assembler.py`:

| Layer | Store | Purpose |
|-------|-------|---------|
| Session | Redis (1h TTL) | Current session turns |
| Conversation | Qdrant | Past session summaries (semantic search) |
| User Profile | PostgreSQL | Demographics, income, risk tolerance |
| Policy Portfolio | PostgreSQL | Known policies |
| Knowledge | Qdrant | User-specific insights |
| Document | MongoDB | Extracted policy documents |

Context budget: 12,000 chars total, priority-allocated (document: 4K, session: 3K, portfolio: 1.5K, knowledge: 1.5K, conversation: 1.2K, profile: 800).

### Guardrails — `hibiscus/guardrails/`

Five guardrails run sequentially in `check_guardrails` node. Each can modify but never block the response:
- **Hallucination** — confidence thresholds, domain-implausible numbers (CSR outside 50-100%, NCB outside 0-65%)
- **Compliance** — IRDAI: no guaranteed returns/settlement language, appends disclaimers
- **Financial** — range validation on financial values
- **Emotional** — empathy prefix for distressed users, escalation to Claude
- **PII** — masks Aadhaar, PAN, account numbers, phone, email in outbound responses

### API — `hibiscus/api/`

FastAPI mounted at `/hibiscus`. Middleware stack: CORS → RequestId → RateLimit (60/min/IP) → JWT Auth (skipped if `JWT_SECRET` unset).

Key endpoints: `POST /chat`, `POST /analyze` (PDF upload), `GET /portfolio/{user_id}`, `WS /ws/{session_id}`, `GET /health`, `GET /metrics`.

### Config — `hibiscus/config.py`

Single `HibiscusSettings(BaseSettings)` with `.env` loading. Accessed via `settings = get_settings()` (lru_cached singleton). JWT secret auto-generates if unset. Confidence thresholds: high=0.85, medium=0.70, low=0.50.

### Knowledge Infrastructure

- **KG (Neo4j):** Seeded via `python -m hibiscus.knowledge.graph.seed`. Uses MERGE (idempotent, safe to re-run). Client in `knowledge/graph/client.py` with async driver, 50-connection pool, LRU cache (256 entries, 5-min TTL).
- **RAG (Qdrant):** Ingested via `python -m hibiscus.knowledge.rag.ingestion`. Uses `fastembed` with `BAAI/bge-large-en-v1.5` (local, no API key, 1024-dim). Stable chunk IDs (MD5-based UUID) prevent duplicates on re-run. Corpus in `knowledge/rag/corpus/`.
- **Embeddings:** All vector stores (RAG, conversation memory, knowledge memory) use `fastembed` with `BAAI/bge-large-en-v1.5` (1024-dim). No OpenAI/GLM embedding dependency.

## Critical Rules

- **Never hallucinate numbers.** If extraction or KG doesn't have the data, say so.
- **Every factual claim must trace to a source** — document extraction, KG, RAG, or web search.
- **Confidence scoring on every agent output.** Below threshold → flag uncertainty.
- **Indian formats always:** ₹ symbol, lakhs/crores, DD/MM/YYYY dates.
- **IRDAI compliance:** Every recommendation includes appropriate disclaimers.
- **All approximate data in seed files marked with `# VERIFY`** for production verification.

## Environment Variables

```
DEEPSEEK_API_KEY=           # Primary LLM
ANTHROPIC_API_KEY=          # Safety net (T3)
NEO4J_URI=bolt://hibiscus-neo4j:7687
NEO4J_PASSWORD=
QDRANT_HOST=hibiscus-qdrant
MONGODB_URL=mongodb://hibiscus-mongo:27017/
POSTGRESQL_URL=postgresql+asyncpg://hibiscus:hibiscus_secure_2024@hibiscus-postgres:5432/insurance_india
REDIS_URL=redis://hibiscus-redis:6379/1
TAVILY_API_KEY=             # Web search (Researcher agent)
LANGSMITH_API_KEY=          # Observability (optional)
```
