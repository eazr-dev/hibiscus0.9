# CLAUDE.md — Hibiscus Project Intelligence

## WHAT IS THIS PROJECT

EAZR is India's AI-native insurance intelligence and premium financing platform. Hibiscus is EAZR's proprietary AI engine — a multi-agent orchestration system that transforms a policy analyzer into a full insurance AI operating system.

**Master blueprint:** `HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md` — THIS IS THE SINGLE SOURCE OF TRUTH. Every architectural decision, directory structure, agent definition, tool mapping, LLM routing strategy, memory architecture, guardrail specification, and evaluation framework is defined there. Read it fully before any work. Re-read relevant sections before building each component.

## REPOSITORY STRUCTURE

```
eazr_chat/                         # Root repository
├── botproject/                    # EXISTING Python backend (FastAPI) — READ ONLY
│   ├── main.py                    # FastAPI app entry
│   ├── routers/                   # API route handlers
│   ├── services/                  # Business logic (extraction, scoring, analysis)
│   ├── models/                    # Database models
│   ├── utils/                     # Utilities
│   └── prompts/                   # Existing LLM prompts
├── frontend/                      # Flutter mobile app — DO NOT TOUCH
├── scripts/                       # Utility scripts
├── docs/                          # Documentation
├── hibiscus/                      # NEW — The AI Intelligence Engine (BUILD HERE)
│   └── (structure defined in blueprint)
├── HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md   # MASTER BLUEPRINT
├── docker-compose.yml             # Existing services + Hibiscus additions
├── .env                           # Environment variables
└── CLAUDE.md                      # THIS FILE — project memory
```

## CRITICAL RULES

### Code Boundaries
- **NEVER modify files inside `botproject/`** — it is a running production system
- **NEVER modify files inside `frontend/`** — it is a deployed mobile app
- **ALL new code goes inside `hibiscus/`** — this is your workspace
- **Existing botproject endpoints are TOOLS** — Hibiscus agents call them via HTTP using the tool wrappers in `hibiscus/tools/existing_api/`
- When you need a capability from botproject, call it as an HTTP tool. Do not import directly.

### Architecture
- **Framework:** LangGraph (StateGraph) for orchestration. Not raw LangChain, not CrewAI.
- **LLM Strategy — DeepSeek Primary:**
  - Tier 1: DeepSeek V3.2 (`deepseek-chat`) — 80% of calls — primary for everything
  - Tier 2: DeepSeek R1 (`deepseek-reasoner`) — 15% — complex math/reasoning
  - Tier 3: Claude Sonnet (`claude-sonnet-4-5`) — 5% — safety net, low-confidence escalation
  - Routing via LiteLLM with automatic fallback chain
- **12 Specialist Agents** — each is a LangGraph node with its own prompt, tools, and confidence scoring
- **6-Layer Memory** — Session (Redis), Conversation History (Qdrant), User Profile (PostgreSQL), Knowledge Memory (Qdrant), Outcome Memory (PostgreSQL), Document Memory (MongoDB + S3)
- **Knowledge Graph** — Neo4j with insurers, products, regulations, benchmarks, tax rules
- **RAG Pipeline** — Qdrant with IRDAI circulars, policy wordings, glossary, tax rules, claims processes, case law
- **Guardrails** — Hallucination guard (confidence scoring), Compliance guard (IRDAI disclaimers), Financial guard (number validation), Emotional guard (distress detection), PII guard

### Quality Standards
- **NEVER hallucinate numbers.** If extraction or KG doesn't have the data, say so. Don't invent copay percentages, sub-limits, premiums, or sum insured values.
- **Every factual claim must trace to a source** — document extraction, Knowledge Graph, RAG retrieval, or web search. LLM reasoning alone is NOT a source for factual claims.
- **Confidence scoring on every agent output.** Below threshold → flag uncertainty to user.
- **Structured logging at every pipeline step.** Where logs stop = where the pipeline is broken.
- **Indian formats always:** ₹ symbol, lakhs/crores, DD/MM/YYYY dates.
- **IRDAI compliance:** Every recommendation includes appropriate disclaimers.

### Development Approach
- Build iteratively: get each component working before moving to the next
- Test as you build: write test cases alongside implementation
- Follow the blueprint directory structure EXACTLY
- Every agent must work independently before wiring into the supervisor
- Use `make` commands defined in the blueprint for common operations

## EXECUTION PHASES

The blueprint defines 4 deliverable-gated phases. No timelines — move to next phase when exit criteria are met.

### Phase 1: Foundation — "It Works"
**Exit criteria:** User uploads health policy PDF → Hibiscus responds with REAL extracted data, EAZR Score, identified gaps, page references, confidence scores, IRDAI disclaimer. Zero hallucination. "What did I upload?" works. Streaming response.

**Build order:**
1. API Discovery — explore botproject/, create `hibiscus/tools/existing_api/discovery.py`
2. Project scaffolding — `hibiscus/` directory with all subdirectories, `pyproject.toml`, `Dockerfile`, `docker-compose.hibiscus.yml`
3. LLM Router — `hibiscus/llm/router.py` with LiteLLM, DeepSeek primary, tiered routing
4. State definition — `hibiscus/orchestrator/state.py` (HibiscusState TypedDict)
5. Supervisor graph — `hibiscus/orchestrator/graph.py` (LangGraph StateGraph with all nodes/edges)
6. Intent classifier — `hibiscus/orchestrator/nodes/intent_classification.py`
7. Existing API tools — `hibiscus/tools/existing_api/client.py` (resilient HTTP wrappers)
8. PolicyAnalyzer agent — `hibiscus/agents/policy_analyzer.py` (calls extraction + scoring tools)
9. Session memory — `hibiscus/memory/layers/session.py` (Redis)
10. Document memory — `hibiscus/memory/layers/document.py` (MongoDB)
11. Context assembler — `hibiscus/memory/assembler.py`
12. Hallucination guard — `hibiscus/guardrails/hallucination.py`
13. Compliance guard — `hibiscus/guardrails/compliance.py`
14. Chat API endpoint — `hibiscus/api/chat.py` (POST /hibiscus/chat with streaming)
15. Health endpoint — `hibiscus/api/health.py`
16. Structured logging — `hibiscus/observability/logger.py`
17. 10 test cases — health policy analysis scenarios

### Phase 2: Intelligence — "It's Smart"
**Exit criteria:** Multi-turn conversation using 3+ agents, grounded in KG and RAG, memory persists across sessions, IPF/SVF suggestions where relevant.

**Build order:**
1. All 12 agents (build each: prompt template → tool bindings → confidence scoring → test)
2. RAG pipeline — Qdrant ingestion, hybrid search, corpus loading
3. Knowledge Graph — Neo4j schema, seed data (insurers, products, regulations, benchmarks, tax rules)
4. Full 6-layer memory system
5. DeepSeek R1 routing for complex calculations
6. Claude escalation for low-confidence and distressed users
7. Direct LLM node (fast path for L1/L2 queries)
8. Response aggregation node (multi-agent output synthesis)
9. Emotional routing (distress detection → tone adjustment)
10. HibiscusBench — 50+ test cases, automated eval runner
11. Cost tracking per conversation
12. LangSmith tracing

### Phase 3: Scale — "It's World-Class"
**Exit criteria:** 1000+ conversations/day, DQ > 0.80 on HibiscusBench (100+ cases), <5s P95 for L1/L2, <15s for L3/L4, LLM cost <₹3/conversation average.

**Build order:**
1. KG expansion (50+ insurers, 200+ products, full regulation set)
2. RAG corpus expansion (200+ circulars, 50+ wordings, 500+ glossary, 100+ case law)
3. Quote comparison engine
4. Renewal/lapse prediction
5. HibiscusBench expansion (100+ cases including adversarial)
6. Production monitoring (Prometheus, alerting, dashboards)
7. Fine-tuned extraction model (Llama 3.1 8B)
8. Load testing

### Phase 4: Moat — "Nobody Can Catch Us"
**Exit criteria:** Self-improving system with outcome tracking, auto-KG enrichment, fraud detection, insurer API integrations.

## CURRENT STATUS

<!-- Update this section as you complete work -->
- [ ] Phase 1: Foundation
  - [ ] API Discovery completed
  - [ ] Project scaffolding done
  - [ ] LLM Router working
  - [ ] Supervisor graph built
  - [ ] Intent classifier working
  - [ ] Existing API tools wrapped
  - [ ] PolicyAnalyzer agent working
  - [ ] Memory (session + document) working
  - [ ] Guardrails active
  - [ ] Chat endpoint live
  - [ ] Phase 1 exit criteria met
- [ ] Phase 2: Intelligence
- [ ] Phase 3: Scale
- [ ] Phase 4: Moat

## KEY FILE REFERENCES

When building a specific component, re-read the relevant section of the blueprint:

| Building This | Read This Section in Blueprint |
|---|---|
| LLM routing | "THE LLM STRATEGY: DEEPSEEK-PRIMARY, TIERED ARCHITECTURE" |
| Supervisor graph | "THE LANGGRAPH SUPERVISOR — PRODUCTION GRADE" |
| Any agent | "agents/" section in directory structure — each has inline comments |
| Memory system | "memory/" section — 6 layers with assembler |
| RAG pipeline | "knowledge/rag/" section — corpus structure, embedding strategy |
| Knowledge Graph | "knowledge/graph/" section — Neo4j schema, seed data |
| Guardrails | "guardrails/" section — hallucination, compliance, financial, emotional, PII |
| Tools | "tools/" section — existing API wrappers, KG tools, RAG tools, calculators |
| Evaluation | "evaluation/" section — HibiscusBench, DQ metric |
| Observability | "observability/" section — logging at every pipeline step |
| Cost model | "LLM COST MODEL" section |
| Series A narrative | "SERIES A POSITIONING" section |

## ENVIRONMENT VARIABLES NEEDED

```
# DeepSeek (Primary LLM)
DEEPSEEK_API_KEY=

# Anthropic (Safety net)
ANTHROPIC_API_KEY=

# OpenAI (Embeddings only — text-embedding-3-small)
OPENAI_API_KEY=

# Neo4j (Knowledge Graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# Qdrant (RAG + Vector Memory)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Existing databases (shared with botproject)
MONGODB_URL=
POSTGRESQL_URL=
REDIS_URL=

# Existing EAZR API (botproject)
EAZR_API_BASE=http://localhost:8000

# Observability
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=hibiscus

# Tavily (Web search for Researcher agent)
TAVILY_API_KEY=
```

## COMMON COMMANDS

```bash
# Start Hibiscus + dependencies
make dev

# Run tests
make test

# Seed Knowledge Graph
make seed-kg

# Ingest RAG corpus
make seed-rag

# Run HibiscusBench evaluation
make eval

# Check all dependency health
make health-check

# View LLM cost summary
make costs
```
