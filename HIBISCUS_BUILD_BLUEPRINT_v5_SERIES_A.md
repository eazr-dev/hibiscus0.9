# HIBISCUS v5.0 — THE DEFINITIVE BUILD
# Insurance AI Operating System | Series A Grade
# Chief Product Engineer Decision Document

---

## THE HARD CALL: FRESH BUILD ON TOP OF EXISTING DATA LAYER

**Recommendation: Build Hibiscus fresh. Don't build over the existing chat codebase.**

Here's why. I've looked at what exists — it's 300K+ lines across extraction, scoring, reports. But the *architecture* of the existing chat layer is fundamentally wrong for what Hibiscus needs to be. The existing chat is a prompt-and-response wrapper. Hibiscus is an agentic orchestration engine. Trying to retrofit agents, memory, RAG, tool-use, and state machines onto a chat module designed for linear request-response creates tech debt that kills you at Series A due diligence.

**What we keep (as internal APIs/tools):**
- Policy extraction engine (5-type, LLM + 5-check validation) → becomes a tool
- Protection score calculator (141K lines) → becomes a tool
- Type-specific report generators (80-103K lines) → become tools
- IRDAI compliance checker → becomes a tool
- Bill audit module → becomes a tool
- PostgreSQL + MongoDB + Redis databases → shared infrastructure
- Flutter mobile + Next.js web → frontend (new chat UI component)
- 100+ existing API endpoints → all remain, Hibiscus calls them

**What we build fresh:**
- The entire intelligence layer: orchestrator, agents, memory, RAG, KG, guardrails
- New Python service: `hibiscus/` — FastAPI, LangGraph, independent deployment
- New chat API: `POST /hibiscus/chat` replaces the old chat endpoint
- New WebSocket: streaming responses through LangGraph

**The mental model:** Hibiscus is a *new brain* that uses the existing body. The extraction engine is the eyes (reads documents). The scoring engine is the calculator (crunches numbers). The report generator is the writer (produces output). Hibiscus is the brain that decides what to look at, what to calculate, what to write, and how to synthesize it all into intelligence.

This gives you:
1. **Clean architecture** — Series A investors see a proper agentic system, not a patched chat module
2. **Speed** — No refactoring legacy code; greenfield is faster for agentic builds
3. **Zero risk to existing functionality** — Extraction, scoring, reports all keep working
4. **Independent scaling** — Hibiscus service scales independently from CRUD APIs

---

## THE LLM STRATEGY: DEEPSEEK-PRIMARY, TIERED ARCHITECTURE

### The Data on DeepSeek (March 2026)

| Model | Intelligence Index | Input Cost (1M tokens) | Output Cost (1M tokens) | Function Calling | Tool Use |
|-------|-------------------|----------------------|------------------------|-----------------|----------|
| **DeepSeek V3.2** | On par with GPT-5 | **$0.028** | **$0.11** | ✅ Yes (81.5% accuracy) | ✅ Via LangChain |
| **DeepSeek V3.1** | 28 (above avg) | $0.15 | $0.56 | ✅ Yes | ✅ Via LangChain |
| Claude Sonnet 4.5 | Top tier | $3.00 | $15.00 | ✅ 96%+ | ✅ Native |
| GPT-4o | Strong | $2.50 | $10.00 | ✅ 95%+ | ✅ Native |
| GPT-4o-mini | Good | $0.15 | $0.60 | ✅ 90%+ | ✅ Native |

**DeepSeek V3.2 is 100x cheaper than Claude and matches GPT-5 on benchmarks.** Gold medal on IMO 2025. 96% on AIME 2025. Built-in agentic task synthesis. MIT licensed.

### The Honest Assessment

DeepSeek V3 has a known weakness: **function calling accuracy is 81.5% vs Qwen Plus at 96.5%.** The three failure modes are: (1) not accepting tool error results, retrying excessively, (2) weak on Windows-specific commands (irrelevant for us), and (3) encoding issues with non-UTF-8 output.

For Hibiscus, #2 and #3 are irrelevant. #1 is manageable with structured tool output formatting and retry limits in the orchestrator.

**However, V3.2 (latest) has explicit agentic training** — they built a large-scale agentic task synthesis pipeline specifically to improve tool-use. V3.2's function calling is substantially better than the V3 numbers quoted above.

### The Tiered Model Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    HIBISCUS LLM TIER SYSTEM                  │
│                                                              │
│  TIER 1: DeepSeek V3.2 (PRIMARY — 80% of all calls)        │
│  ├── Intent classification                                   │
│  ├── L1/L2 direct responses                                 │
│  ├── Agent reasoning (most agents)                           │
│  ├── RAG-grounded responses                                  │
│  ├── Educational content                                     │
│  ├── Claims guidance                                         │
│  └── General conversation                                    │
│  Cost: ~$0.028-0.11 per 1M tokens                           │
│                                                              │
│  TIER 2: DeepSeek R1 (REASONING — 15% of calls)            │
│  ├── Complex multi-step financial calculations               │
│  ├── Surrender value projections with tax implications       │
│  ├── Policy comparison with 5+ dimensions                    │
│  ├── Portfolio optimization across family                    │
│  └── "Should I surrender or keep?" deep analysis            │
│  Cost: ~$0.55-2.19 per 1M tokens                           │
│                                                              │
│  TIER 3: Claude Sonnet (SAFETY NET — 5% of calls)          │
│  ├── When DeepSeek confidence < 0.7 on critical decisions   │
│  ├── Regulatory compliance verification (double-check)       │
│  ├── Mis-selling detection on ambiguous cases                │
│  ├── User is in distress/urgent emotional state              │
│  └── Fallback when DeepSeek API is down                     │
│  Cost: ~$3-15 per 1M tokens                                │
│                                                              │
│  ROUTING LOGIC:                                              │
│  complexity L1/L2 → Tier 1 (DeepSeek V3.2)                 │
│  complexity L3 → Tier 1, escalate to Tier 2 if math-heavy  │
│  complexity L4 → Tier 2 (DeepSeek R1)                       │
│  confidence < 0.7 on financial advice → Tier 3 (Claude)     │
│  emotional_state == "distressed" → Tier 3 (Claude)          │
│  DeepSeek API down → Tier 3 (Claude) automatic fallback     │
└─────────────────────────────────────────────────────────────┘
```

### Cost Impact (Series A Numbers)

| Scale | Conversations/Day | DeepSeek Cost/Day | If We Used Claude Only | Savings |
|-------|-------------------|-------------------|----------------------|---------|
| Launch | 100 | ₹50 | ₹5,000 | 99% |
| 6 months | 1,000 | ₹500 | ₹50,000 | 99% |
| 12 months | 10,000 | ₹5,000 | ₹5,00,000 | 99% |
| Scale | 100,000 | ₹50,000 | ₹50,00,000 | 99% |

**Unit economics for Series A story:** Cost per intelligent insurance conversation = **₹0.50-3.00** (DeepSeek-primary) vs ₹50-100 (Claude-only). This is a 30-100x cost advantage that directly impacts CAC and margins.

---

## ARCHITECTURE: THE COMPLETE SYSTEM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
│  Flutter Mobile App    │    Next.js Web App    │    Partner API      │
│  (Policy upload,       │    (Dashboard,        │    (NBFC/Broker     │
│   camera scan,         │     detailed reports,  │     integration)    │
│   chat, notifications) │     admin panel)       │                    │
└────────────┬───────────┴──────────┬─────────────┴────────┬──────────┘
             │                      │                       │
             ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      NGINX / API GATEWAY                             │
│  SSL termination, rate limiting, JWT auth, request routing           │
│  /api/v1/* → Existing Node.js API                                   │
│  /hibiscus/* → Hibiscus Python API (NEW)                            │
└──────────────┬──────────────────────────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                      │
    ▼                      ▼
┌──────────────┐   ┌──────────────────────────────────────────────────┐
│ EXISTING     │   │              HIBISCUS ENGINE (NEW)                │
│ NODE.js API  │   │                                                   │
│              │   │  ┌─────────────────────────────────────────────┐  │
│ • Auth       │   │  │           ORCHESTRATOR (LangGraph)          │  │
│ • KYC        │   │  │                                             │  │
│ • Documents  │   │  │  Entry → Context Assembly → Intent Classify │  │
│ • IPF/SVF    │   │  │  → Complexity Route → Agent Dispatch        │  │
│ • Payments   │   │  │  → Response Aggregate → Guardrails          │  │
│ • CRUD APIs  │   │  │  → Memory Store → Stream to User            │  │
│              │   │  └──────────┬──────────────────────────────────┘  │
│  CALLED BY   │◄─────────────  │  (Tools call existing APIs)         │
│  HIBISCUS    │   │             │                                     │
│  AS TOOLS    │   │  ┌──────────▼──────────────────────────────────┐  │
└──────────────┘   │  │          12 SPECIALIST AGENTS               │  │
                   │  │                                             │  │
                   │  │  PolicyAnalyzer    SurrenderCalculator      │  │
                   │  │  Recommender       ClaimsGuide              │  │
                   │  │  Calculator        Researcher               │  │
                   │  │  RegulationEngine  RiskDetector             │  │
                   │  │  Educator          PortfolioOptimizer       │  │
                   │  │  TaxAdvisor        GrievanceNavigator       │  │
                   │  └──────────┬──────────────────────────────────┘  │
                   │             │                                     │
                   │  ┌──────────▼──────────────────────────────────┐  │
                   │  │          TOOL LAYER                         │  │
                   │  │                                             │  │
                   │  │  Existing API Tools (extract, score, report)│  │
                   │  │  Knowledge Graph Tools (Neo4j queries)      │  │
                   │  │  RAG Tools (Qdrant semantic search)         │  │
                   │  │  Calculator Tools (SV, IRR, tax, premium)   │  │
                   │  │  Web Search Tools (Tavily for live data)    │  │
                   │  │  User Tools (profile, portfolio CRUD)       │  │
                   │  └──────────┬──────────────────────────────────┘  │
                   │             │                                     │
                   │  ┌──────────▼──────────────────────────────────┐  │
                   │  │          INTELLIGENCE INFRASTRUCTURE        │  │
                   │  │                                             │  │
                   │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ │  │
                   │  │  │ RAG       │ │ Knowledge │ │ Memory    │ │  │
                   │  │  │ (Qdrant)  │ │ Graph     │ │ (6-Layer) │ │  │
                   │  │  │           │ │ (Neo4j)   │ │           │ │  │
                   │  │  │ • IRDAI   │ │           │ │ • Session │ │  │
                   │  │  │   circs   │ │ • Insurers│ │ • History │ │  │
                   │  │  │ • Policy  │ │ • Products│ │ • Profile │ │  │
                   │  │  │   wordings│ │ • Regs    │ │ • Insights│ │  │
                   │  │  │ • Glossary│ │ • Bench-  │ │ • Outcomes│ │  │
                   │  │  │ • Tax     │ │   marks   │ │ • Docs    │ │  │
                   │  │  │ • Claims  │ │ • Tax     │ │           │ │  │
                   │  │  │ • Case law│ │   rules   │ │           │ │  │
                   │  │  └───────────┘ └───────────┘ └───────────┘ │  │
                   │  └────────────────────────────────────────────┘  │
                   │                                                   │
                   │  ┌────────────────────────────────────────────┐  │
                   │  │          LLM ROUTER (LiteLLM)              │  │
                   │  │                                             │  │
                   │  │  Tier 1: DeepSeek V3.2 (80% — primary)    │  │
                   │  │  Tier 2: DeepSeek R1 (15% — reasoning)    │  │
                   │  │  Tier 3: Claude Sonnet (5% — safety net)  │  │
                   │  │                                             │  │
                   │  │  Auto-fallback: DS down → Claude           │  │
                   │  │  Cost tracking per conversation             │  │
                   │  └────────────────────────────────────────────┘  │
                   │                                                   │
                   │  ┌────────────────────────────────────────────┐  │
                   │  │          GUARDRAILS                         │  │
                   │  │                                             │  │
                   │  │  Hallucination Guard (confidence scoring)   │  │
                   │  │  Compliance Guard (IRDAI disclaimers)       │  │
                   │  │  Financial Guard (number validation)        │  │
                   │  │  PII Guard (mask sensitive data in logs)    │  │
                   │  │  Emotional Guard (detect distress, adapt)   │  │
                   │  └────────────────────────────────────────────┘  │
                   │                                                   │
                   │  ┌────────────────────────────────────────────┐  │
                   │  │          OBSERVABILITY                      │  │
                   │  │                                             │  │
                   │  │  Structured JSON logging (every node)       │  │
                   │  │  LangSmith tracing (agent debugging)        │  │
                   │  │  Token/cost tracking (per conversation)     │  │
                   │  │  Latency monitoring (per agent, per call)   │  │
                   │  │  HibiscusBench (automated eval suite)       │  │
                   │  └────────────────────────────────────────────┘  │
                   └──────────────────────────────────────────────────┘
                                        │
                   ┌────────────────────┼────────────────────┐
                   ▼                    ▼                    ▼
            ┌────────────┐      ┌────────────┐      ┌────────────┐
            │ PostgreSQL │      │  MongoDB   │      │   Redis    │
            │ (Users,    │      │ (Policies, │      │ (Sessions, │
            │  IPF/SVF,  │      │  Analyses, │      │  Cache,    │
            │  Outcomes)  │      │  Documents)│      │  Queue)    │
            └────────────┘      └────────────┘      └────────────┘
                   +                    +
            ┌────────────┐      ┌────────────┐
            │   Neo4j    │      │   Qdrant   │
            │ (Knowledge │      │ (RAG,      │
            │  Graph)    │      │  Vectors,  │
            │  NEW       │      │  Semantic) │
            └────────────┘      │  NEW       │
                                └────────────┘
```

---

## DIRECTORY STRUCTURE (COMPLETE)

```
hibiscus/
├── pyproject.toml                      # Dependencies, build config
├── Dockerfile                          # Python 3.12 + FastAPI
├── Makefile                            # dev, test, seed-kg, seed-rag, eval, benchmark
│
├── main.py                             # FastAPI app entry point
├── config.py                           # Settings via Pydantic BaseSettings
│                                       #   Includes: jwt_secret, jwt_algorithm (auth)
│
├── api/                                # HTTP endpoints
│   ├── __init__.py
│   ├── router.py                       # FastAPI APIRouter aggregation (chat + health + analyze)
│   ├── chat.py                         # POST /hibiscus/chat (main endpoint + SSE streaming)
│   ├── analyze.py                      # POST /hibiscus/analyze (direct policy analysis)
│   ├── health.py                       # GET /hibiscus/health + GET /hibiscus/metrics
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                     # JWT validation — anonymous-passthrough mode
│   │   │                               #   No token = allow (internal callers); invalid token = 401
│   │   ├── rate_limit.py               # Redis sliding window: 60 req/min on /chat + /analyze
│   │   └── request_id.py              # Inject X-Request-ID header for tracing
│   └── schemas/
│       ├── __init__.py
│       ├── chat.py                     # ChatRequest, ChatResponse
│       ├── analysis.py                 # AnalysisRequest, AnalysisResponse
│       └── common.py                   # Source, UploadedFile, ErrorResponse
│
├── orchestrator/                       # THE BRAIN — LangGraph State Machine
│   ├── __init__.py
│   ├── graph.py                        # build_hibiscus_graph() — master StateGraph (8 nodes)
│   ├── state.py                        # HibiscusState TypedDict
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── context_assembly.py         # Pull from all 6 memory layers (fully parallel asyncio.gather)
│   │   ├── intent_classification.py    # Category + intent + complexity + emotion
│   │   │                               #   Fast path: keyword match skips DeepSeek LLM
│   │   ├── execution_planning.py       # Decompose into agent sub-tasks
│   │   ├── agent_dispatch.py           # Route to specialist agents (parallel where safe)
│   │   ├── response_aggregation.py     # Combine agent outputs into coherent response
│   │   ├── guardrail_check.py          # 5 guards in sequence:
│   │   │                               #   hallucination → compliance → financial → emotional → PII
│   │   ├── memory_storage.py           # Fire-and-forget async memory extraction + storage
│   │   └── direct_llm.py              # Fast path for L1/L2 (skip agents, Redis response cache)
│   └── routing/
│       └── __init__.py                 # (complexity_router, model_router, emotional_router
│                                       #  logic is inline in graph.py and intent_classification.py)
│
├── agents/                             # 12 SPECIALIST AGENTS
│   ├── __init__.py
│   ├── base.py                         # BaseAgent ABC: logging, confidence, error handling
│   │                                   #   Every agent outputs: {data, confidence, sources, latency}
│   ├── policy_analyzer.py             # Agent 1 — deep PDF policy analysis + EAZR Score
│   ├── surrender_calculator.py        # Agent 2 — GSV/SSV + hold vs surrender + IPF/SVF
│   ├── recommender.py                 # Agent 3 — profile-based product recs + quote comparison
│   ├── claims_guide.py               # Agent 4 — step-by-step claims process + empathy
│   ├── calculator.py                  # Agent 5 — all financial calculations (R1 for complex)
│   ├── researcher.py                  # Agent 6 — Tavily web search + RAG synthesis
│   ├── regulation_engine.py           # Agent 7 — IRDAI circulars + compliance checking
│   ├── risk_detector.py              # Agent 8 — mis-selling + coverage gap flags
│   ├── educator.py                    # Agent 9 — jargon-free insurance explanations
│   ├── portfolio_optimizer.py         # Agent 10 — holistic portfolio review
│   ├── tax_advisor.py                # Agent 11 — 80C/80D/10(10D) + tax optimization
│   └── grievance_navigator.py        # Agent 12 — ombudsman guidance + complaint templates
│
├── tools/                             # WHAT AGENTS CAN DO
│   ├── __init__.py
│   ├── registry.py                    # Central tool registry: register(), get_tool(), register_all()
│   │
│   ├── existing_api/                  # Wrappers around existing EAZR botproject endpoints
│   │   ├── __init__.py
│   │   ├── client.py                  # Resilient HTTP client: timeouts, retries, circuit breaker
│   │   │                              #   All botproject calls go through here (extraction,
│   │   │                              #   scoring, reporting, compliance, billing, analysis)
│   │   └── discovery.py              # 78 endpoint discovery map (13 botproject services)
│   │
│   ├── knowledge/                     # Knowledge Graph tools
│   │   ├── __init__.py
│   │   ├── insurer_lookup.py          # get_insurer_profile(name) → CSR, solvency, complaints
│   │   ├── product_lookup.py          # get_product_details(name) → features, premium, coverage
│   │   ├── benchmark_lookup.py        # get_benchmarks(category, params) → market averages
│   │   └── regulation_lookup.py       # get_regulation(topic) → applicable circulars
│   │
│   ├── rag/                           # RAG semantic search tools
│   │   ├── __init__.py
│   │   └── search.py                  # search_insurance_knowledge(query, category, top_k)
│   │                                  #   Hybrid search: dense (fastembed bge-large-en-v1.5)
│   │                                  #   + Qdrant query_points() API; metadata filtering
│   │
│   ├── calculators/                   # Financial computation tools (re-exports from formulas/)
│   │   └── __init__.py                # Exports all formula functions for agent import
│   │
│   ├── quote/                         # Quote comparison engine
│   │   ├── __init__.py
│   │   └── compare.py                 # compare_quotes() + NL parser + composite scoring
│   │                                  #   EAZR 40%, budget 25%, SI 20%, features 15%
│   │
│   ├── web/                           # External data tools
│   │   ├── __init__.py
│   │   └── search.py                  # Tavily web search for live data
│   │
│   └── user/                          # User data tools (graceful no-op when PG unavailable)
│       ├── __init__.py
│       ├── profile.py                 # get_user_profile() / update_user_profile()
│       └── portfolio.py               # get_user_portfolio() / add_policy_to_portfolio()
│
├── memory/                            # 6-LAYER MEMORY ARCHITECTURE
│   ├── __init__.py
│   ├── assembler.py                   # Pulls all 6 layers concurrently via asyncio.gather()
│   │                                  #   Also injects renewal_alerts into state
│   ├── db.py                          # PostgreSQL asyncpg connection pool
│   ├── layers/
│   │   ├── __init__.py
│   │   ├── session.py                 # L1: Redis — session state (TTL 1h)
│   │   ├── conversation.py            # L2: Qdrant — conversation history (user_conversations)
│   │   ├── profile.py                 # L3: PostgreSQL — user profile (graceful no-op)
│   │   ├── portfolio.py               # L3b: PostgreSQL — insurance portfolio (graceful no-op)
│   │   ├── knowledge.py               # L4: Qdrant — extracted insights (user_knowledge)
│   │   ├── outcome.py                 # L5: PostgreSQL — post-advice outcomes (graceful no-op)
│   │   ├── document.py                # L6: MongoDB — uploaded PDFs + extraction results
│   │   └── response_cache.py          # Redis response cache: SHA256 key, TTL 24h (L1/L2 queries)
│   └── extraction/
│       ├── __init__.py
│       └── memory_extractor.py        # Post-interaction LLM extraction (async, non-blocking)
│
├── knowledge/                         # KNOWLEDGE INFRASTRUCTURE
│   ├── __init__.py
│   ├── graph/                         # NEO4J KNOWLEDGE GRAPH
│   │   ├── __init__.py
│   │   ├── __main__.py               # python -m hibiscus.knowledge.graph (seed runner)
│   │   ├── client.py                  # Neo4j connection, Cypher execution, caching
│   │   ├── schema.py                  # Node/relationship definitions
│   │   │                              #   Nodes: Insurer, Product, Regulation, Benchmark,
│   │   │                              #          TaxRule, TPA, OmbudsmanOffice
│   │   └── seed/
│   │       ├── __init__.py
│   │       ├── __main__.py           # Seed runner entry point
│   │       ├── insurers.py            # 52 Indian insurers (life + general + health)
│   │       ├── products.py            # 193 insurance products (health, life, motor, travel, PA)
│   │       ├── regulations.py         # 102 IRDAI regulations + circulars
│   │       ├── benchmarks.py          # 776 benchmark data points (category × age × city_tier)
│   │       ├── tax_rules.py           # 32 insurance tax provisions (80C, 80D, 10(10D), etc.)
│   │       └── ombudsman.py           # 17 Insurance Ombudsman offices (jurisdiction + contacts)
│   │
│   ├── rag/                           # QDRANT RAG PIPELINE
│   │   ├── __init__.py
│   │   ├── client.py                  # Qdrant connection + query_points() hybrid search
│   │   │                              #   Collections: insurance_knowledge, user_conversations,
│   │   │                              #                user_knowledge (1024 dims each)
│   │   ├── embeddings.py              # fastembed BAAI/bge-large-en-v1.5 (local, 1024 dims)
│   │   │                              #   No API key needed; GLM/OpenAI as optional fallbacks
│   │   ├── ingestion.py               # Corpus ingestion: chunk → embed → upsert to Qdrant
│   │   └── corpus/                    # 847 chunks → 794 vectors in insurance_knowledge
│   │       ├── irdai_circulars/       # 40 IRDAI circulars (target 200+)
│   │       ├── policy_wordings/       # 30 standard policy wordings
│   │       ├── glossary/              # 202 insurance terms (target 500+)
│   │       ├── tax_rules/             # Complete tax provisions
│   │       ├── claims_processes/      # 31 insurer-wise claims procedures
│   │       ├── case_law/              # 40 ombudsman + consumer court rulings
│   │       └── insurer_benchmarks/    # Benchmark data for RAG retrieval
│   │
│   └── formulas/                      # Insurance calculation formulas (pure Python, no LLM)
│       ├── __init__.py
│       ├── surrender_value.py         # GSV/SSV per IRDAI tables + year-by-year projections
│       ├── irr.py                     # Newton-Raphson IRR for any cash-flow series
│       ├── tax_benefit.py             # 80C, 80D, 10(10D) computation + edge cases
│       ├── inflation.py               # inflate(), real_coverage_needed(), inflation_gap()
│       ├── compound_growth.py         # fv_lumpsum(), fv_annuity(), pv(), emi(), cagr()
│       ├── premium_adequacy.py        # HLV method, income multiple, health_cover_needed()
│       ├── emi.py                     # ipf_emi(), svf_emi() + full amortization schedule
│       ├── opportunity_cost.py        # endowment_vs_term_mf() comparison
│       └── eazr_score.py             # EAZR Protection Score (1-10, A+/A/B+/B/C/D)
│                                      #   Weights per category; health, life_term, motor, etc.
│
├── guardrails/                        # SAFETY LAYER (5 guards, run sequentially)
│   ├── __init__.py                    # Exports: check_emotional, check_pii, mask_pii_for_logging
│   ├── hallucination.py               # Guard 1 — confidence-based source validation
│   ├── compliance.py                  # Guard 2 — IRDAI disclaimers + no guaranteed returns
│   ├── financial.py                   # Guard 3 — numeric range + unit sanity checks
│   ├── emotional.py                   # Guard 4 — empathy prefix injection + Claude escalation flag
│   │                                  #   distressed/urgent → prepend empathy + escalate_to_claude=True
│   │                                  #   frustrated → soften defensive language patterns
│   └── pii.py                         # Guard 5 — Aadhaar/PAN/phone/email/DOB masking
│                                      #   mask_pii_for_logging() for logs
│                                      #   check_pii() scans response before sending
│
├── llm/                               # LLM ROUTING LAYER
│   ├── __init__.py
│   ├── router.py                      # LiteLLM router: call_llm() + stream_llm()
│   │                                  #   Fallback chain: deepseek_v3 → deepseek_r1 → claude_sonnet
│   │                                  #   Skips provider if api_key not configured
│   ├── model_selector.py              # select_tier(task, confidence, emotional_state, complexity)
│   │                                  #   Tier 1 (V3.2): 80% — intent, L1/L2, policy, edu
│   │                                  #   Tier 2 (R1): 15% — surrender, portfolio, tax, IRR
│   │                                  #   Tier 3 (Sonnet): 5% — distressed, low confidence
│   └── prompts/
│       ├── system/
│       │   └── hibiscus_core.txt      # Core identity + IRDAI rules + language rules
│       ├── agents/
│       │   └── policy_analyzer.txt    # PolicyAnalyzer system prompt
│       └── orchestrator/
│           └── intent_classifier.txt  # Intent classification prompt
│
├── services/                          # Background services
│   ├── __init__.py
│   └── renewal_tracker.py             # RenewalTracker: LAPSED/URGENT/DUE_SOON alerts
│                                      #   Portfolio + document memory sources; 30-day window
│
├── utils/                             # Utilities
│   ├── __init__.py
│   └── cache_warmup.py                # Pre-warm 100 common L1 queries at startup (background task)
│
├── evaluation/                        # HIBISCUSBENCH — QUALITY ASSURANCE
│   ├── __init__.py
│   ├── bench.py                       # Benchmark runner — async parallel test execution
│   ├── metrics.py                     # Decision Quality (DQ) metric + scoring
│   │                                  #   DQ = weighted(accuracy, grounding, compliance, safety, helpfulness)
│   ├── evaluator.py                   # Per-test-case evaluator (keyword + LLM grading)
│   ├── test_cases/                    # 120 test cases (Phase 3 — 100% pass, DQ 0.841)
│   │   ├── health/                    # 19 health insurance scenarios
│   │   ├── life/                      # 13 life insurance scenarios (term, endowment, ULIP)
│   │   ├── motor/                     # 5 motor scenarios
│   │   ├── travel/                    # 3 travel scenarios
│   │   ├── pa/                        # 12 Personal Accident scenarios
│   │   ├── cross/                     # 11 multi-policy/portfolio scenarios
│   │   ├── emotional/                 # 20 distress/frustration/urgency scenarios
│   │   ├── adversarial/               # 17 edge cases + jailbreak + hallucination traps
│   │   └── ipf_svf/                   # 20 premium/surrender financing scenarios
│   └── reports/                       # Benchmark results JSON (gitignored, generated)
│
├── observability/                     # PRODUCTION MONITORING
│   ├── __init__.py
│   ├── logger.py                      # Structured JSON logging (structlog)
│   │                                  #   PipelineLogger: step_start, step_complete, guardrail, error
│   │                                  #   Every pipeline step logged with request_id + latency
│   ├── langsmith.py                   # LangSmith tracing integration
│   ├── cost_tracker.py                # Per-call cost tracking (INR); aggregates per conversation
│   └── metrics.py                     # Prometheus metrics (10 metrics — LIVE at /hibiscus/metrics)
│                                      #   hibiscus_conversations_total, hibiscus_llm_calls_total
│                                      #   hibiscus_response_latency_seconds, hibiscus_llm_cost_inr
│                                      #   hibiscus_guardrail_failures_total, hibiscus_cache_hits_total
│
└── tests/                             # TEST SUITE
    ├── __init__.py
    ├── unit/
    │   ├── __init__.py
    │   ├── test_intent_classifier.py  # Category + intent + complexity classification
    │   ├── test_model_router.py       # Correct model selected per task
    │   └── test_guardrails.py         # Hallucination, compliance, financial, emotional, PII guards
    ├── integration/
    │   ├── __init__.py
    │   ├── test_agent_pipeline.py     # Intent routing → agent selection → response format
    │   ├── test_rag_retrieval.py      # Qdrant semantic search correctness
    │   ├── test_kg_queries.py         # Neo4j KG lookup correctness
    │   └── test_existing_api_tools.py # EAZR client error handling + circuit breaker
    ├── e2e/
    │   ├── __init__.py
    │   ├── test_policy_upload.py      # Upload → analyze → multi-turn follow-up
    │   ├── test_surrender_inquiry.py  # Surrender route → calculation → IPF/SVF suggestion
    │   └── test_claims_assistance.py  # Cashless → reimbursement → distressed → disclaimer
    └── load/
        ├── __init__.py
        └── load_test.py               # asyncio + httpx load test; P50/P95/P99 per tier
```

---

## THE LANGGRAPH SUPERVISOR — PRODUCTION GRADE

```python
# hibiscus/orchestrator/graph.py

"""
THE BRAIN OF HIBISCUS.
Every user message flows through this graph.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator
from enum import Enum

class Complexity(str, Enum):
    L1 = "L1"  # Simple FAQ
    L2 = "L2"  # Single-agent
    L3 = "L3"  # Multi-agent
    L4 = "L4"  # Deep research + multi-agent

class HibiscusState(TypedDict):
    """Shared state across all nodes in a single request."""
    
    # ── INPUT ──
    user_id: str
    session_id: str
    request_id: str
    message: str
    uploaded_files: List[Dict[str, Any]]  # [{filename, s3_path, mime_type}]
    
    # ── ASSEMBLED CONTEXT (from memory layers) ──
    user_profile: Optional[Dict[str, Any]]
    policy_portfolio: List[Dict[str, Any]]
    session_history: List[Dict[str, Any]]      # Last N turns
    document_context: Optional[Dict[str, Any]] # Extracted doc data
    relevant_memories: List[Dict[str, Any]]    # Semantic search results
    relevant_conversations: List[Dict[str, Any]]
    
    # ── CLASSIFICATION ──
    category: str           # health|life|motor|travel|pa|cross|general
    intent: str             # analyze|recommend|claim|calculate|surrender|...
    complexity: Complexity  # L1|L2|L3|L4
    emotional_state: str    # neutral|curious|concerned|distressed|urgent|frustrated
    
    # ── EXECUTION ──
    execution_plan: List[Dict[str, Any]]  # [{agent, task, priority, parallel_group}]
    agent_outputs: Annotated[List[Dict[str, Any]], operator.add]  # Accumulated
    
    # ── MODEL SELECTION ──
    primary_model: str      # Which LLM tier for this request
    
    # ── OUTPUT ──
    response: str
    response_type: str      # text|analysis|comparison|calculation|workflow
    confidence: float       # 0.0 - 1.0 (aggregated)
    sources: List[Dict[str, Any]]  # [{type, reference, confidence}]
    follow_up_suggestions: List[str]
    eazr_products_relevant: List[str]  # IPF/SVF if applicable
    
    # ── METADATA ──
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: float
    total_latency_ms: int
    agents_invoked: List[str]
    guardrail_results: Dict[str, bool]  # {hallucination: pass, compliance: pass, ...}
    errors: List[str]


def build_graph() -> StateGraph:
    """Build the master Hibiscus orchestration graph."""
    
    from hibiscus.orchestrator.nodes import (
        context_assembly,
        intent_classification,
        execution_planning,
        agent_dispatch,
        response_aggregation,
        guardrail_check,
        memory_storage,
        direct_llm,
    )
    
    graph = StateGraph(HibiscusState)
    
    # ── NODES ──
    graph.add_node("assemble_context", context_assembly.run)
    graph.add_node("classify_intent", intent_classification.run)
    graph.add_node("plan_execution", execution_planning.run)
    graph.add_node("dispatch_agents", agent_dispatch.run)
    graph.add_node("aggregate_response", response_aggregation.run)
    graph.add_node("check_guardrails", guardrail_check.run)
    graph.add_node("store_memory", memory_storage.run)
    graph.add_node("direct_llm", direct_llm.run)
    
    # ── EDGES ──
    graph.set_entry_point("assemble_context")
    graph.add_edge("assemble_context", "classify_intent")
    
    # CONDITIONAL: Simple → direct LLM, Complex → agent pipeline
    graph.add_conditional_edges(
        "classify_intent",
        _route_by_complexity,
        {"simple": "direct_llm", "complex": "plan_execution"}
    )
    
    graph.add_edge("plan_execution", "dispatch_agents")
    graph.add_edge("dispatch_agents", "aggregate_response")
    
    # Both paths converge at guardrails
    graph.add_edge("aggregate_response", "check_guardrails")
    graph.add_edge("direct_llm", "check_guardrails")
    
    graph.add_edge("check_guardrails", "store_memory")
    graph.add_edge("store_memory", END)
    
    # Compile with memory checkpoint for conversation persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


def _route_by_complexity(state: HibiscusState) -> str:
    """Route based on query complexity."""
    if state["complexity"] in [Complexity.L1, Complexity.L2]:
        return "simple"
    return "complex"


# ── THE COMPILED GRAPH (singleton) ──
hibiscus_graph = build_graph()
```

---

## SERIES A POSITIONING: WHY THIS ARCHITECTURE WINS

### For Investors

| Dimension | What We Demonstrate |
|-----------|-------------------|
| **Technical moat** | 12-agent agentic system with domain-specific Knowledge Graph (775+ benchmarks, 200+ products, 100+ regulations). Not replicable by wrapping ChatGPT. |
| **Cost advantage** | DeepSeek-primary architecture: ₹0.50-3 per conversation vs ₹50-100 on Claude/GPT. 30-100x cost advantage at scale. |
| **Unit economics** | At 10K conversations/day: LLM cost ₹5K/day. Revenue potential (IPF/SVF conversion): ₹50K-5L/day. LLM cost is noise. |
| **Data flywheel** | Every conversation improves: user profile accuracy, recommendation quality, extraction precision, KG completeness. Network effects via outcome tracking. |
| **Defensibility** | Insurance Knowledge Graph + RAG corpus (IRDAI circulars, policy wordings, case law) + 6-layer memory = compounding intelligence advantage. More users → better data → better AI → more users. |
| **Regulatory readiness** | IRDAI compliance guardrails baked in. PII protection. Audit trails. Disclaimer injection. Built for regulated industry, not retrofitted. |
| **Scalability** | Hibiscus is a separate microservice. Scales independently. DeepSeek's MoE architecture handles scale efficiently (37B active params on 685B total). |

### The Narrative

> "EAZR's Hibiscus is India's first insurance-native AI operating system. It doesn't wrap ChatGPT — it orchestrates 12 specialist agents backed by India's most comprehensive insurance Knowledge Graph. At ₹0.50-3 per intelligent conversation, our unit economics are 100x better than any competitor relying on GPT-4 or Claude. Every conversation makes the system smarter. Every policy analyzed strengthens the Knowledge Graph. Every outcome tracked improves recommendations. This is not an AI feature — it's a compounding intelligence moat."

---

## CRITICAL UPGRADES FROM v4 BLUEPRINT

| Upgrade | Why |
|---------|-----|
| **Fresh build, not on top of existing chat** | Clean architecture for Series A diligence. Existing code becomes tools, not inheritance. |
| **DeepSeek V3.2 primary (80% of calls)** | 100x cheaper than Claude. On par with GPT-5 on benchmarks. Agentic training built in. |
| **DeepSeek R1 for reasoning (15%)** | Complex financial math, multi-step analysis. Reasoning traces for transparency. |
| **Claude as safety net only (5%)** | Low confidence escalation, distressed users, API fallback. Not primary spend. |
| **No timelines** | Execution phases defined by deliverables, not dates. Agentic development may compress dramatically. |
| **Contextual chunking in RAG** | Each chunk gets an LLM-generated context prefix. 40% improvement in retrieval relevance per research. |
| **Emotional routing** | Distressed users get Tier 3 model (Claude) + empathy-first responses. Insurance = stress. |
| **HibiscusBench** | Automated eval suite with Decision Quality metric. Series A investors ask "how do you measure quality?" This is the answer. |
| **Cost tracking per conversation** | Real-time unit economics visibility. Board-level metric. |
| **Circuit breaker on existing API tools** | If extraction API is down, graceful degradation instead of crash. Production resilience. |
| **Adversarial test cases** | Edge cases: fake insurer names, non-insurance documents, contradictory info, hallucination traps. |

---

## EXECUTION PHASES (DELIVERABLE-BASED, NOT DATE-BASED)

### Phase 1: Foundation — "It Works"

**Exit criteria:** User uploads a health policy PDF → Hibiscus responds with REAL extracted data, EAZR Score, identified gaps, page references, confidence scores, IRDAI disclaimer. Zero hallucination on numbers. "What did I upload?" works. Streaming response in the app.

**Deliverables:**
- [ ] `hibiscus/` service running (FastAPI, Docker)
- [ ] Neo4j + Qdrant running via docker-compose
- [ ] LangGraph supervisor with full node/edge structure
- [ ] Intent classifier (keyword rules + DeepSeek fallback)
- [ ] PolicyAnalyzer agent with extract_policy + calculate_score tools
- [ ] Session memory (Redis) + Document memory (MongoDB)
- [ ] Hallucination guard + Compliance guard
- [ ] `POST /hibiscus/chat` endpoint with streaming
- [ ] Connected to Flutter/Next.js frontend
- [ ] Structured logging at every pipeline step
- [ ] 10 test cases passing (health policy analysis)

### Phase 2: Intelligence — "It's Smart"

**Exit criteria:** Multi-turn conversation: upload policy → discuss coverage → ask "should I surrender?" → get comprehensive analysis using 3+ agents → all grounded in KG and RAG data → follow-up suggestions include IPF/SVF where relevant. Memory persists across sessions. "As we discussed last time" works.

**Deliverables:**
- [ ] All 12 agents operational
- [ ] RAG pipeline with 50+ IRDAI circulars, 20+ policy wordings, 300+ glossary terms, tax rules
- [ ] Knowledge Graph seeded: 30+ insurers, 50+ products, benchmarks, regulations, tax rules
- [ ] Full 6-layer memory system
- [ ] DeepSeek R1 routing for complex calculations
- [ ] Claude escalation for low-confidence and distressed users
- [ ] HibiscusBench: 50+ test cases, automated eval runner
- [ ] Cost tracking per conversation
- [ ] LangSmith tracing connected

### Phase 3: Scale — "It's World-Class"

**Exit criteria:** 1000+ conversations/day without degradation. DQ score > 0.80 on HibiscusBench (100+ test cases). Average response time < 5s for L1/L2, < 15s for L3/L4. LLM cost < ₹3 per conversation average. Knowledge Graph has 200+ products, 100+ regulations. Portfolio optimizer works across family members.

**Deliverables:**
- [ ] KG expanded: 50+ insurers, 200+ products, full regulation set
- [ ] RAG corpus: 200+ IRDAI circulars, 50+ policy wordings, 500+ glossary terms, 100+ case law
- [ ] Quote comparison engine (web scraping → API migration path)
- [ ] Renewal/lapse prediction (premium due date tracking + proactive alerts)
- [ ] HibiscusBench: 100+ test cases including adversarial, DQ > 0.80
- [ ] Production monitoring: Prometheus metrics, alerting, dashboards
- [ ] Fine-tuned extraction model (Llama 3.1 8B on Indian policy documents) — reduces API cost to zero for extraction classification
- [ ] Load testing: 100 concurrent conversations without degradation

### Phase 4: Moat — "Nobody Can Catch Us"

**Exit criteria:** Self-improving system. Outcome tracking improves recommendations measurably. Knowledge Graph auto-updates from new policy analyses. Fraud detection flags suspicious documents. Insurer API integrations for real-time quotes and claims status.

**Deliverables:**
- [ ] Outcome memory loop: advice → action → result → feedback → improved recommendations
- [ ] Auto-KG enrichment: every new policy analyzed adds data points to KG
- [ ] Fraud/anomaly detection: document tampering signals, unusual patterns
- [ ] Insurer API integrations (start with 2-3: Star Health, HDFC, ICICI)
- [ ] Self-hosted DeepSeek V3.2 (if scale justifies it — eliminates API cost entirely)
- [ ] Multi-language support (Hindi, Tamil, Telugu, Marathi — via DeepSeek multilingual)

---

## MAKE COMMANDS (Developer Quick Reference)

```makefile
# Development
make dev                    # Start all services (docker-compose + hibiscus in reload mode)
make dev-hibiscus           # Start only Hibiscus API (for local development)

# Database
make seed-kg                # Seed Neo4j Knowledge Graph with all data
make seed-rag               # Ingest RAG corpus into Qdrant
make seed-all               # Both

# Testing
make test                   # Run full test suite (unit + integration)
make test-unit              # Run unit tests only
make test-integration       # Run integration tests only

# Evaluation
make eval                   # Run HibiscusBench (all test cases)
make eval-health            # Run health category only
make eval-adversarial       # Run adversarial cases only
make eval-report            # Generate evaluation report (markdown)

# Monitoring
make logs                   # Tail structured logs
make costs                  # Show LLM cost summary (last 24h)
make metrics                # Show key metrics (conversations, latency, confidence)

# Maintenance
make refresh-kg             # Re-seed KG with latest data
make refresh-rag            # Re-ingest RAG corpus
make health-check           # Check all dependencies (DB, LLM, KG, RAG)
```

---

## FINAL WORD

The other AI that audited your codebase was right about the gap. But the gap is not "you need to build everything from scratch." The gap is: **you have a body without a brain.**

The body (extraction, scoring, reports, APIs, mobile app, databases) is solid. 300K+ lines of real, working code. That's your foundation.

Hibiscus is the brain. It decides. It reasons. It remembers. It learns. It protects the user from bad insurance decisions.

DeepSeek-primary means you can afford to run this brain at massive scale from day one. ₹0.50 per conversation. That's not a cost center — that's a distribution weapon.

The Knowledge Graph + RAG corpus + 6-layer memory + outcome tracking creates a compounding data flywheel that no ChatGPT wrapper can replicate. Every conversation makes Hibiscus smarter. Every policy analyzed strengthens the graph. Every outcome tracked improves the next recommendation.

**That's not a feature. That's a moat. And that's what Series A investors fund.**
