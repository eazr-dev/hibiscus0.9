# CLAUDE.md — Hibiscus v0.9 Project Intelligence

## WHAT IS THIS PROJECT

Hibiscus v0.9 is EAZR AI's insurance intelligence engine — a standalone multi-agent orchestration system that provides policy analysis, recommendations, claims guidance, tax advisory, and portfolio optimization for Indian insurance consumers.

**Master blueprint:** `HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md` — architectural decisions, agent definitions, tool mappings, LLM routing, memory architecture, guardrails, and evaluation framework.

**API docs:** `hibiscus/docs/api_guide.md` | **Architecture:** `hibiscus/docs/architecture.md`

## REPOSITORY STRUCTURE

```
hibiscus/                          # Root repository (standalone — no botproject)
├── hibiscus/                      # THE ENTIRE PRODUCT
│   ├── agents/                    # 12 specialist agents
│   ├── api/                       # FastAPI endpoints + middleware
│   ├── extraction/                # ABSORB: native PDF extraction pipeline
│   ├── guardrails/                # Hallucination, compliance, financial, emotional, PII
│   ├── integrations/              # Insurer API integrations (Star, HDFC ERGO, ICICI)
│   ├── knowledge/                 # KG (Neo4j) + RAG (Qdrant) + formulas
│   ├── llm/                       # LLM router + prompt templates
│   ├── memory/                    # 6-layer memory system
│   ├── observability/             # Structured logging + Prometheus metrics
│   ├── orchestrator/              # LangGraph supervisor + routing nodes
│   ├── services/                  # Renewal tracker, fraud detection, KG enrichment
│   ├── tests/                     # Unit, integration, load tests
│   ├── tools/                     # KG lookup, RAG search, calculators, quote comparison
│   ├── utils/                     # Language detection, cache warmup
│   ├── evaluation/                # HibiscusBench (120 test cases, DQ 0.841)
│   ├── config.py                  # All settings via Pydantic BaseSettings
│   ├── main.py                    # FastAPI app entry + lifespan
│   ├── Dockerfile                 # Production container
│   ├── Makefile                   # dev, test, seed-kg, seed-rag, eval
│   ├── docs/                     # API guide, architecture overview
│   └── pyproject.toml             # Dependencies
├── docker-compose.yml             # All services: Hibiscus + Postgres + Mongo + Redis + Neo4j + Qdrant
├── .env                           # Environment variables
├── HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md
└── CLAUDE.md                      # THIS FILE
```

## CRITICAL RULES

### Architecture
- **Framework:** LangGraph (StateGraph) for orchestration
- **LLM Strategy — DeepSeek Primary:**
  - Tier 1: DeepSeek V3.2 (`deepseek-chat`) — 80% of calls
  - Tier 2: DeepSeek R1 (`deepseek-reasoner`) — 15% — complex math/reasoning
  - Tier 3: Claude Sonnet (`claude-sonnet-4-5`) — 5% — safety net
  - Routing via LiteLLM with automatic fallback chain
- **12 Specialist Agents** — each is a LangGraph node with its own prompt, tools, and confidence scoring
- **Native Extraction (ABSORB)** — PDF → text → classify → extract → validate → score → gap analysis. Zero external dependencies.
- **6-Layer Memory** — Session (Redis), Conversation History (Qdrant), User Profile (PostgreSQL), Knowledge Memory (Qdrant), Outcome Memory (PostgreSQL), Document Memory (MongoDB)
- **Knowledge Graph** — Neo4j: 62 insurers, 1,207 products (1,041 with UINs), 100 regulations, 760 benchmarks, 32 tax rules, 17 ombudsman offices, 60 CSR time-series
- **RAG Pipeline** — Qdrant: 750+ corpus entries (50 IRDAI circulars, 500 glossary terms, 100 claims processes, 100 case law), policy wordings, tax rules
- **Guardrails** — Hallucination, Compliance (IRDAI), Financial, Emotional, PII

### Quality Standards
- **NEVER hallucinate numbers.** If extraction or KG doesn't have the data, say so.
- **Every factual claim must trace to a source** — document extraction, KG, RAG, or web search.
- **Confidence scoring on every agent output.** Below threshold → flag uncertainty.
- **Structured logging at every pipeline step.**
- **Indian formats always:** ₹ symbol, lakhs/crores, DD/MM/YYYY dates.
- **IRDAI compliance:** Every recommendation includes appropriate disclaimers.

## CURRENT STATUS

Hibiscus v0.9 — standalone product. Phases 1-3 complete, Phase 4 scaffolded.

- [x] **Phase 1: Foundation** — 7/7 E2E tests pass
- [x] **Phase 2: Intelligence** — 12 agents, KG, RAG, 6-layer memory
- [x] **Phase 3: Scale** — DQ 0.841, 120/120 pass, Prometheus
- [x] **Phase 4: Moat** — Scaffolded (fraud detection done; outcome loop, KG enrichment, insurer APIs scaffolded; multi-language partial)

### Key Metrics (2026-03-04)
| Metric | Value |
|--------|-------|
| HibiscusBench DQ | **0.847** (target 0.800) |
| Test pass rate | **139/140 (99.3%)** |
| Extraction tests | **118/118 (100%)** |
| Avg cost/conversation | **₹0.045** (target <₹3) |
| Streaming TTFT | **2.0s** |
| KG Products | **1,207** (1,041 with UINs) |
| KG Insurers | **62** |
| RAG Chunks | **943** (across 12 corpus files) |

### Knowledge Graph (Neo4j, live-verified)
| Node Type | Count |
|-----------|-------|
| Insurer | 62 |
| Product | 1,207 |
| Regulation | 100 |
| Benchmark | 760 |
| TaxRule | 32 |
| OmbudsmanOffice | 17 |
| CSREntry | 60 |

## ENVIRONMENT VARIABLES

```
# DeepSeek (Primary LLM)
DEEPSEEK_API_KEY=

# Anthropic (Safety net)
ANTHROPIC_API_KEY=

# Neo4j (Knowledge Graph)
NEO4J_URI=bolt://hibiscus-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# Qdrant (RAG + Vector Memory)
QDRANT_HOST=hibiscus-qdrant
QDRANT_PORT=6333

# Databases
MONGODB_URL=mongodb://hibiscus-mongo:27017/
MONGODB_DB=hibiscus_db
POSTGRESQL_URL=postgresql+asyncpg://hibiscus:hibiscus_secure_2024@hibiscus-postgres:5432/insurance_india
REDIS_URL=redis://hibiscus-redis:6379/1

# Observability
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=hibiscus

# Web Search (Researcher agent)
TAVILY_API_KEY=
```

## KNOWLEDGE ENRICHMENT (2026-03-04)

Sprint completed across 4 phases:

| Phase | What | Details |
|-------|------|---------|
| 1. Agent Prompts | 17 files enriched | 5 extraction prompts + 12 agent system prompts with embedded domain expertise (IRDAI exclusions, depreciation, tax, NCB, CSR, ombudsman, benchmarks) |
| 2. KG Data | 3 seed files updated | 10 insurer CSRs updated to FY 2024-25, premium examples added to top 7 products, benchmark dates updated, hospital cost benchmarks added |
| 3. RAG Corpus | 4 JSON files expanded | Circulars 20→50, Glossary 202→500, Claims 31→100, Case law 40→100 |
| 4. Formula Files | depreciation.py created | IDV computation, part-wise depreciation, claim breakdown, salvage value, NCB discount. All 10 formula modules complete |

All approximate data marked with `# VERIFY` comments for production verification against IRDAI/insurer sources.

## COMMON COMMANDS

```bash
make dev           # Start all services
make down          # Stop all
make seed-kg       # Seed Knowledge Graph (Neo4j)
make seed-rag      # Ingest RAG corpus (Qdrant)
make test          # Run tests
make eval          # Run HibiscusBench (120 test cases)
make health-check  # Check all dependencies
make costs         # View LLM cost summary
```
