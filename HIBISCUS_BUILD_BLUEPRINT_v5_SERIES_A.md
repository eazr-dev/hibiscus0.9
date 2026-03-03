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
├── docker-compose.hibiscus.yml         # Neo4j + Qdrant + Hibiscus API
├── Makefile                            # dev, test, seed-kg, seed-rag, eval, benchmark
├── .env.example                        # All required env vars
│
├── main.py                             # FastAPI app entry point
├── config.py                           # Settings via Pydantic BaseSettings
│
├── api/                                # HTTP & WebSocket endpoints
│   ├── __init__.py
│   ├── router.py                       # FastAPI APIRouter aggregation
│   ├── chat.py                         # POST /hibiscus/chat (main endpoint)
│   ├── analyze.py                      # POST /hibiscus/analyze (direct analysis)
│   ├── portfolio.py                    # GET/POST /hibiscus/portfolio
│   ├── health.py                       # GET /hibiscus/health (all deps check)
│   ├── websocket.py                    # WS /hibiscus/ws (streaming)
│   ├── middleware/
│   │   ├── auth.py                     # JWT validation (delegates to existing auth)
│   │   ├── rate_limit.py               # Per-user rate limiting
│   │   ├── request_id.py              # Inject request_id for tracing
│   │   └── cors.py                     # CORS configuration
│   └── schemas/                        # Pydantic request/response models
│       ├── chat.py                     # ChatRequest, ChatResponse
│       ├── analysis.py                 # AnalysisRequest, AnalysisResponse
│       └── common.py                   # Shared models (confidence, sources, etc.)
│
├── orchestrator/                       # THE BRAIN — LangGraph State Machine
│   ├── __init__.py
│   ├── graph.py                        # build_hibiscus_graph() — the master StateGraph
│   ├── state.py                        # HibiscusState TypedDict
│   ├── nodes/                          # Each node is a step in the graph
│   │   ├── context_assembly.py         # Pull from all 6 memory layers
│   │   ├── intent_classification.py    # Category + intent + complexity + emotion
│   │   ├── execution_planning.py       # Decompose into agent sub-tasks
│   │   ├── agent_dispatch.py           # Route to specialist agents (parallel where safe)
│   │   ├── response_aggregation.py     # Combine agent outputs into coherent response
│   │   ├── guardrail_check.py          # Hallucination, compliance, financial, PII
│   │   ├── memory_storage.py           # Extract + store new memories (async)
│   │   └── direct_llm.py              # Fast path for L1/L2 (skip agents)
│   └── routing/
│       ├── complexity_router.py        # L1/L2 → direct, L3/L4 → agents
│       ├── model_router.py             # Tier 1/2/3 model selection
│       └── emotional_router.py         # Distress detection → tone adjustment
│
├── agents/                             # 12 SPECIALIST AGENTS
│   ├── __init__.py
│   ├── base.py                         # BaseAgent ABC: logging, confidence, error handling
│   │                                   #   - Every agent outputs: {data, confidence, sources, latency}
│   │                                   #   - Every agent logs: entry, tool calls, exit
│   │                                   #   - Every agent handles: timeout, LLM failure, tool failure
│   ├── policy_analyzer.py             # Agent 1
│   │   # PURPOSE: Deep analysis of uploaded insurance policy documents
│   │   # TOOLS: extract_policy, calculate_score, check_compliance, search_knowledge, query_kg
│   │   # OUTPUTS: Structured extraction, EAZR Score, gap analysis, red flags, market comparison
│   │   # GROUNDING: All numbers from extraction tool or KG. NEVER from LLM imagination.
│   │   # CONFIDENCE: 0.9+ if from extraction, 0.7-0.9 if from KG, <0.7 → flag uncertainty
│   │   #
│   │   # THIS IS THE MOST CRITICAL AGENT.
│   │   # A user uploads a PDF. PolicyAnalyzer is the difference between
│   │   # "generic insurance explainer" and "holy shit, this AI actually read my policy."
│   │   # Every field must trace to a page number in the document.
│   │   # If extraction fails on a field, say "I couldn't find X in your document"
│   │   # NEVER invent a copay percentage, sub-limit, or exclusion.
│   │   #
│   │   # FLOW:
│   │   # 1. Call extract_policy() tool → get structured data
│   │   # 2. Call query_kg() → get insurer profile, product benchmarks
│   │   # 3. Call calculate_score() → get EAZR protection score
│   │   # 4. Call check_compliance() → get IRDAI compliance status
│   │   # 5. Call search_knowledge() → get relevant regulations/case law
│   │   # 6. Synthesize: strengths, weaknesses, gaps, red flags, recommendations
│   │   # 7. Return with confidence scores per field and page references
│   │
│   ├── surrender_calculator.py        # Agent 2
│   │   # PURPOSE: Surrender value calculations + hold vs surrender vs IPF/SVF analysis
│   │   # MODEL: DeepSeek R1 (Tier 2) — complex multi-step financial math
│   │   # TOOLS: surrender_value_formula, irr_calculator, tax_benefit_calc, query_kg
│   │   # OUTPUTS: Year-by-year SV projections, IRR comparison, tax impact,
│   │   #          opportunity cost analysis, IPF/SVF alternative modeling
│   │   # GROUNDING: All calculations show step-by-step working. User can verify.
│   │   #
│   │   # THIS AGENT DRIVES REVENUE.
│   │   # Every "should I surrender?" conversation is a potential SVF/IPF customer.
│   │   # But we MUST be honest. If surrendering is genuinely better, say so.
│   │   # Trust → long-term retention > short-term conversion.
│   │
│   ├── recommender.py                 # Agent 3
│   │   # PURPOSE: Profile-based insurance product recommendations
│   │   # TOOLS: query_kg (products, benchmarks), search_knowledge, web_search
│   │   # OUTPUTS: Ranked product recommendations with reasoning, EAZR Score per product,
│   │   #          premium estimates, coverage comparison matrix
│   │   # GROUNDING: Products from KG only. Premiums from KG or disclaimed as "approximate."
│   │   # COMPLIANCE: "This is for information only. EAZR is not an insurance distributor."
│   │   #
│   │   # RECOMMENDATION ALGORITHM:
│   │   # 1. User profile (age, family, income, health, location, existing coverage)
│   │   # 2. Coverage gap analysis (what they have vs what they need)
│   │   # 3. Query KG for products matching: category, sum insured range, premium budget
│   │   # 4. Score products on: coverage fit, insurer quality, premium value, claim experience
│   │   # 5. Rank top 3-5 with clear reasoning for each
│   │
│   ├── claims_guide.py               # Agent 4
│   │   # PURPOSE: End-to-end claims assistance
│   │   # TOOLS: search_knowledge (claims processes), query_kg (insurer contact, TPA info),
│   │   #        web_search (current claim forms, office addresses)
│   │   # OUTPUTS: Step-by-step claims process, document checklist, timeline expectations,
│   │   #          insurer/TPA contact info, escalation path, grievance option
│   │   # EMOTIONAL AWARENESS: Claims = stress. Lead with empathy, then structure.
│   │   #
│   │   # CLAIMS WORKFLOW ENGINE (built into this agent):
│   │   # Phase 1 (now): Guidance-only. Step-by-step instructions + document checklists.
│   │   # Phase 2 (later): Track claim status via user updates.
│   │   # Phase 3 (later): Direct insurer API integration for real-time status.
│   │
│   ├── calculator.py                  # Agent 5
│   │   # PURPOSE: All financial calculations
│   │   # MODEL: DeepSeek R1 for complex math, V3.2 for simple
│   │   # TOOLS: All formula tools, existing score calculator, tax tools
│   │   # OUTPUTS: Calculations with step-by-step working, assumptions stated,
│   │   #          "what-if" sensitivity analysis
│   │   # RULE: Every calculation shows its formula and inputs. Verifiable.
│   │
│   ├── researcher.py                  # Agent 6
│   │   # PURPOSE: Deep research for questions needing current/external data
│   │   # TOOLS: web_search (Tavily), search_knowledge (RAG), query_kg
│   │   # OUTPUTS: Synthesized research with cited sources
│   │   # USE CASES: "What's Star Health's latest claim settlement ratio?"
│   │   #            "Any recent IRDAI circular on health insurance?"
│   │   #            "Compare Niva Bupa vs Star Health in 2025"
│   │
│   ├── regulation_engine.py           # Agent 7
│   │   # PURPOSE: IRDAI regulation lookup and compliance checking
│   │   # TOOLS: search_knowledge (IRDAI circulars), query_kg (regulation nodes)
│   │   # OUTPUTS: Applicable regulations with circular references, consumer rights,
│   │   #          deadlines, complaint procedures
│   │   # GROUNDING: Every regulation cited with circular number and date.
│   │   #            If unsure, say "I recommend verifying at irdai.gov.in"
│   │
│   ├── risk_detector.py              # Agent 8
│   │   # PURPOSE: Identify mis-selling, coverage gaps, risk flags
│   │   # RUNS AS: Guardrail agent — invoked after PolicyAnalyzer and Recommender
│   │   # TOOLS: query_kg (benchmarks for comparison), search_knowledge (mis-selling patterns)
│   │   # OUTPUTS: Risk flags with severity (LOW/MEDIUM/HIGH/CRITICAL), evidence, action items
│   │   # PATTERNS DETECTED:
│   │   #   - ULIP sold as "guaranteed returns" → CRITICAL
│   │   #   - Endowment when term + MF is better → HIGH
│   │   #   - Premium > 10% of income → HIGH
│   │   #   - No health insurance despite family → HIGH
│   │   #   - Sum insured inadequate for metro city → MEDIUM
│   │   #   - Duplicate coverage across policies → LOW
│   │
│   ├── educator.py                    # Agent 9
│   │   # PURPOSE: Explain insurance concepts in simple language
│   │   # TOOLS: search_knowledge (glossary, educational content)
│   │   # OUTPUTS: Jargon-free explanations with Indian context, analogies, examples
│   │   # TONE: Teacher, not textbook. "Think of a sub-limit like..."
│   │   # AUDIENCE: Assume user has zero insurance knowledge unless proven otherwise.
│   │
│   ├── portfolio_optimizer.py         # Agent 10
│   │   # PURPOSE: Holistic view of all user's policies
│   │   # TOOLS: query_kg (benchmarks), calculator tools, user profile tools
│   │   # OUTPUTS: Portfolio summary, coverage gaps, overlaps, optimization recommendations,
│   │   #          family protection score, life-stage adequacy assessment
│   │
│   ├── tax_advisor.py                # Agent 11
│   │   # PURPOSE: Insurance-specific tax optimization
│   │   # TOOLS: tax_benefit_calc, search_knowledge (tax rules), calculator
│   │   # OUTPUTS: Current tax benefits, optimization opportunities, 80C/80D/10(10D) breakdown,
│   │   #          tax-optimal surrender timing, NPS vs insurance tax comparison
│   │
│   └── grievance_navigator.py        # Agent 12
│       # PURPOSE: IRDAI complaint and ombudsman guidance
│       # TOOLS: search_knowledge (grievance procedures), query_kg (ombudsman offices),
│       #        web_search (current forms, contact info)
│       # OUTPUTS: Step-by-step complaint process, applicable ombudsman office,
│       #          template complaint letter, escalation timeline, consumer court option
│
├── tools/                             # WHAT AGENTS CAN DO
│   ├── __init__.py
│   ├── registry.py                    # Central tool registry — all tools registered here
│   │
│   ├── existing_api/                  # Wrappers around existing EAZR endpoints
│   │   ├── __init__.py
│   │   ├── extraction.py              # extract_policy() → calls existing extraction pipeline
│   │   ├── scoring.py                 # calculate_protection_score() → calls existing 141K scorer
│   │   ├── reporting.py               # generate_report() → calls existing report generators
│   │   ├── compliance.py              # check_irdai_compliance() → calls existing checker
│   │   ├── billing.py                 # audit_bill() → calls existing bill audit
│   │   └── client.py                  # Resilient HTTP client: timeouts, retries, circuit breaker
│   │                                  #   - 30s timeout on extraction (large PDFs)
│   │                                  #   - 10s timeout on scoring
│   │                                  #   - 3 retries with exponential backoff
│   │                                  #   - Circuit breaker: if 5 failures in 60s, stop trying
│   │                                  #   - Graceful degradation: "I'm having trouble analyzing
│   │                                  #     your document right now" instead of crashing
│   │
│   ├── knowledge/                     # Knowledge Graph tools
│   │   ├── __init__.py
│   │   ├── insurer_lookup.py          # get_insurer_profile(name) → CSR, solvency, complaints, products
│   │   ├── product_lookup.py          # get_product_details(name) → features, premium, coverage
│   │   ├── product_compare.py         # compare_products([names]) → side-by-side matrix
│   │   ├── benchmark_lookup.py        # get_benchmarks(category, params) → market averages
│   │   └── regulation_lookup.py       # get_regulation(topic) → applicable circulars
│   │
│   ├── rag/                           # RAG semantic search tools
│   │   ├── __init__.py
│   │   └── search.py                  # search_insurance_knowledge(query, category, top_k)
│   │                                  #   - Hybrid search: dense + BM25 sparse
│   │                                  #   - Metadata filtering by corpus category
│   │                                  #   - Returns chunks with source, confidence, page ref
│   │
│   ├── calculators/                   # Financial computation tools
│   │   ├── __init__.py
│   │   ├── surrender_value.py         # Guaranteed SV, Special SV, year-by-year projection
│   │   ├── irr.py                     # Internal Rate of Return for any policy
│   │   ├── premium_adequacy.py        # Coverage gap = needed - current
│   │   ├── tax_benefit.py             # 80C, 80D, 10(10D) computation
│   │   ├── inflation_adjust.py        # Future value of coverage needs
│   │   ├── emi.py                     # IPF/SVF EMI calculator
│   │   └── opportunity_cost.py        # "What if you invested the premium in Nifty instead?"
│   │
│   ├── web/                           # External data tools
│   │   ├── __init__.py
│   │   └── search.py                  # Tavily web search for live data
│   │
│   └── user/                          # User data tools
│       ├── __init__.py
│       ├── profile.py                 # Get/update user profile
│       └── portfolio.py               # Get/update policy portfolio
│
├── memory/                            # 6-LAYER MEMORY ARCHITECTURE
│   ├── __init__.py
│   ├── assembler.py                   # THE CRITICAL FILE
│   │   #
│   │   # Context Assembler: builds the optimal context window for each query.
│   │   # Pulls from all 6 layers, prioritizes by relevance, fits within token budget.
│   │   #
│   │   # ASSEMBLY ORDER (priority):
│   │   # 1. Session memory (always — current conversation)
│   │   # 2. Document memory (always if doc uploaded — the actual extracted data)
│   │   # 3. User profile (always if exists — demographics, preferences)
│   │   # 4. Policy portfolio (always if exists — known policies)
│   │   # 5. Knowledge memories (semantic search — relevant past insights)
│   │   # 6. Conversation history (semantic search — relevant past conversations)
│   │   # 7. Outcome memories (if relevant — past advice outcomes)
│   │   #
│   │   # TOKEN BUDGET: Model context (128K) - system prompt (~4K) - tools (~2K) - response reserve (4K)
│   │   # Available for context: ~118K tokens. More than enough.
│   │   # If still over: compress older context via summarization.
│   │
│   ├── layers/
│   │   ├── __init__.py
│   │   ├── session.py                 # L1: Redis — current session state
│   │   │   # Stores: message history, active agent states, uploaded file refs
│   │   │   # Lifetime: session duration
│   │   │   # Key: session:{session_id}
│   │   │
│   │   ├── conversation.py            # L2: Qdrant — conversation history
│   │   │   # Stores: past conversation summaries, semantic-indexed
│   │   │   # Retrieval: similarity search against current query
│   │   │   # Lifetime: 90 days
│   │   │   # Enables: "As we discussed last time..."
│   │   │
│   │   ├── profile.py                 # L3: PostgreSQL — structured user profile
│   │   │   # Stores: age, gender, location, occupation, income_band,
│   │   │   #         family_structure, health_conditions (categories only),
│   │   │   #         smoker_status, risk_tolerance, communication_preference,
│   │   │   #         language_preference
│   │   │   # Updated: Auto-extracted from conversations (with user confirmation)
│   │   │   # Encrypted at rest. PII-compliant.
│   │   │
│   │   ├── portfolio.py               # L3b: PostgreSQL — insurance portfolio
│   │   │   # Stores: all known policies with:
│   │   │   #   policy_type, insurer, product_name, sum_insured, premium,
│   │   │   #   start_date, maturity_date, payment_status, riders,
│   │   │   #   surrender_value_estimate, eazr_score, analysis_date
│   │   │   # Updated: After every policy analysis
│   │   │
│   │   ├── knowledge.py               # L4: Qdrant — extracted insights
│   │   │   # Stores: key facts extracted from conversations
│   │   │   # Examples:
│   │   │   #   "User's primary concern is child's education planning"
│   │   │   #   "User was mis-sold ULIP by agent in 2019"
│   │   │   #   "User's company provides ₹5L group health cover"
│   │   │   #   "User prefers term insurance over investment-linked"
│   │   │   # Decay: recent insights weighted higher than old ones
│   │   │
│   │   ├── outcome.py                 # L5: PostgreSQL — post-advice tracking
│   │   │   # Stores: what happened after advice
│   │   │   #   advice_given, action_taken, outcome, satisfaction
│   │   │   #   policy_purchased, claim_filed, ipf_svf_used
│   │   │   # Used for: improving recommendation quality over time
│   │   │
│   │   └── document.py                # L6: MongoDB + S3 — uploaded documents
│   │       # Stores: original PDF (S3), extracted text, structured extraction,
│   │       #         analysis results, page-level references
│   │       # Lifetime: permanent (user's document vault)
│   │       # CRITICAL: This is why "what did I upload?" MUST work.
│   │
│   └── extraction/
│       ├── __init__.py
│       └── memory_extractor.py        # Post-interaction memory extraction
│           # After every conversation turn:
│           # 1. Extract profile updates (age, family, etc.)
│           # 2. Extract knowledge insights (preferences, concerns)
│           # 3. Extract portfolio updates (new policy info)
│           # 4. Store asynchronously (don't block response)
│
├── knowledge/                         # KNOWLEDGE INFRASTRUCTURE
│   ├── __init__.py
│   │
│   ├── graph/                         # NEO4J KNOWLEDGE GRAPH
│   │   ├── __init__.py
│   │   ├── client.py                  # Neo4j connection, query execution, caching
│   │   ├── schema.py                  # Cypher schema definition
│   │   │   #
│   │   │   # NODE TYPES:
│   │   │   # (:Insurer {name, type, csr, solvency_ratio, complaint_ratio, market_share,
│   │   │   #            headquarters, website, claim_settlement_time_avg, digital_score})
│   │   │   #
│   │   │   # (:Product {name, category, type, sum_insured_range, premium_range,
│   │   │   #            key_features, exclusion_count, sub_limit_count, waiting_periods,
│   │   │   #            riders_available, network_hospitals, copay_structure,
│   │   │   #            room_rent_limit, eazr_score, launch_date})
│   │   │   #
│   │   │   # (:Regulation {circular_no, date, subject, category, key_requirements,
│   │   │   #               effective_date, supersedes, compliance_deadline})
│   │   │   #
│   │   │   # (:Benchmark {category, metric, value, percentile_25, percentile_50,
│   │   │   #              percentile_75, source, date, applicable_for})
│   │   │   #
│   │   │   # (:TaxRule {section, subsection, max_deduction, applicable_to,
│   │   │   #            conditions, examples, effective_from})
│   │   │   #
│   │   │   # (:TPA {name, insurer_partnerships, network_size, digital_score,
│   │   │   #        avg_processing_time})
│   │   │   #
│   │   │   # (:OmbudsmanOffice {city, jurisdiction, address, phone, email})
│   │   │   #
│   │   │   # RELATIONSHIPS:
│   │   │   # (:Insurer)-[:OFFERS]->(:Product)
│   │   │   # (:Product)-[:GOVERNED_BY]->(:Regulation)
│   │   │   # (:Product)-[:BENCHMARKED_AGAINST]->(:Benchmark)
│   │   │   # (:Insurer)-[:USES_TPA]->(:TPA)
│   │   │   # (:Regulation)-[:SUPERSEDES]->(:Regulation)
│   │   │   # (:OmbudsmanOffice)-[:COVERS]->(:State)
│   │   │
│   │   └── seed/
│   │       ├── __init__.py
│   │       ├── insurers.py            # 50+ Indian insurers (life + general + health)
│   │       │   # Data sources: IRDAI Annual Report, public financial statements
│   │       │   # MUST INCLUDE per insurer:
│   │       │   #   - Claim Settlement Ratio (CSR) — from IRDAI data
│   │       │   #   - Solvency ratio — from IRDAI data
│   │       │   #   - Complaint ratio — from IGMS data
│   │       │   #   - Incurred Claim Ratio (ICR) — for health insurers
│   │       │   #   - Average claim settlement time — from published data
│   │       │   #   - Digital capability score — our assessment
│   │       │   #   - Network hospital count — for health insurers
│   │       │
│   │       ├── products.py            # 200+ insurance products
│   │       │   # START WITH top 10 products per category = 50 products
│   │       │   # Health: Star Comprehensive, HDFC Optima, Niva Bupa Aspire, etc.
│   │       │   # Life Term: HDFC Click2Protect, ICICI iProtect, Max Life Smart, etc.
│   │       │   # Life Endowment/ULIP: LIC Jeevan Umang, HDFC Sanchay, etc.
│   │       │   # Motor: HDFC Ergo, Bajaj Allianz, ICICI Lombard, etc.
│   │       │   # Travel: Bajaj Allianz Travel, TATA AIG, Digit, etc.
│   │       │
│   │       ├── regulations.py         # 100+ IRDAI regulations
│   │       │   # MUST INCLUDE:
│   │       │   # - Health insurance regulations 2024
│   │       │   # - IRDAI (Protection of Policyholders' Interests) Regulations
│   │       │   # - Claim settlement guidelines
│   │       │   # - Portability regulations
│   │       │   # - Free look period rules
│   │       │   # - Grievance redressal mechanism
│   │       │   # - Mis-selling guidelines
│   │       │   # - ULIP disclosure norms
│   │       │
│   │       ├── benchmarks.py          # 775+ benchmark data points
│   │       │   # By category × age_group × city_tier:
│   │       │   #   - Average premium
│   │       │   #   - Average sum insured
│   │       │   #   - Typical copay range
│   │       │   #   - Common sub-limits
│   │       │   #   - Claim frequency
│   │       │   #   - Average claim amount
│   │       │
│   │       ├── tax_rules.py           # All insurance tax provisions
│   │       │   # Section 80C: Life insurance premium (max ₹1.5L)
│   │       │   # Section 80D: Health insurance premium (₹25K/₹50K/₹1L)
│   │       │   # Section 10(10D): Maturity proceeds exemption
│   │       │   # Section 80CCC: Pension fund contribution
│   │       │   # Conditions, exceptions, edge cases — ALL documented
│   │       │
│   │       └── ombudsman.py           # 17 Insurance Ombudsman offices
│   │           # Name, jurisdiction (states), address, phone, email
│   │
│   ├── rag/                           # QDRANT RAG PIPELINE
│   │   ├── __init__.py
│   │   ├── client.py                  # Qdrant connection, hybrid search, reranking
│   │   │   #
│   │   │   # SEARCH STRATEGY:
│   │   │   # 1. Dense search (text-embedding-3-small, 1536 dims) — semantic similarity
│   │   │   # 2. Sparse search (BM25 via Qdrant native) — keyword precision
│   │   │   # 3. Hybrid fusion (RRF — Reciprocal Rank Fusion) — best of both
│   │   │   # 4. Metadata filter (category, insurer, date range)
│   │   │   # 5. Rerank top-k with cross-encoder if needed
│   │   │   #
│   │   │   # COLLECTIONS:
│   │   │   # - insurance_knowledge (main corpus — circulars, wordings, glossary, tax, claims)
│   │   │   # - user_conversations (per-user conversation history, semantic indexed)
│   │   │   # - user_knowledge (per-user extracted insights)
│   │   │
│   │   ├── embeddings.py              # Embedding model configuration
│   │   │   # PRIMARY: OpenAI text-embedding-3-small ($0.02/1M tokens, 1536 dims)
│   │   │   # Why not DeepSeek embeddings? OpenAI's embedding model is battle-tested,
│   │   │   # tiny cost, and decoupled from LLM provider choice.
│   │   │   # If cost becomes issue at scale: switch to local BGE-M3 or Jina v3
│   │   │
│   │   ├── ingestion.py               # Document ingestion pipeline
│   │   │   #
│   │   │   # PIPELINE:
│   │   │   # 1. Load document (PDF, DOCX, HTML, plain text)
│   │   │   # 2. Extract text (PyPDF for PDF, pandoc for others, OCR for scanned)
│   │   │   # 3. Clean and normalize (remove headers/footers, fix encoding)
│   │   │   # 4. Chunk (RecursiveCharacterTextSplitter, size varies by corpus type)
│   │   │   # 5. Enrich with metadata (source, category, insurer, date, section)
│   │   │   # 6. Generate embeddings (batch, async)
│   │   │   # 7. Upsert to Qdrant with payload
│   │   │   #
│   │   │   # CONTEXTUAL CHUNKING:
│   │   │   # Each chunk gets a context prefix generated by LLM:
│   │   │   # "This chunk is from IRDAI Circular 2024/Health/23, Section 4.2,
│   │   │   #  discussing network hospital empanelment requirements."
│   │   │   # This dramatically improves retrieval relevance.
│   │   │
│   │   └── corpus/                    # The actual knowledge corpus
│   │       ├── README.md              # Corpus inventory, sources, refresh schedule
│   │       ├── irdai_circulars/       # 200+ IRDAI circulars
│   │       │   # Priority circulars (must have for launch):
│   │       │   # - Master circular on health insurance
│   │       │   # - Guidelines on protection of policyholders
│   │       │   # - Claim settlement norms
│   │       │   # - Portability guidelines
│   │       │   # - Mis-selling circulars
│   │       │   # - ULIP/traditional product guidelines
│   │       │   # Source: https://irdai.gov.in/circulars
│   │       │
│   │       ├── policy_wordings/       # Standard policy wordings
│   │       │   # 10 per category = 50 sample policy wordings
│   │       │   # These ground the "what's typical" baseline
│   │       │
│   │       ├── glossary/              # 500+ insurance terms
│   │       │   # From IRDAI glossary + industry standard definitions
│   │       │   # Indian-context explanations, not US/UK definitions
│   │       │
│   │       ├── tax_rules/             # Complete tax provisions
│   │       │   # Income Tax Act sections + CBDT circulars + case law
│   │       │
│   │       ├── claims_processes/      # Insurer-wise claims procedures
│   │       │   # Top 20 insurers × claim types = 100+ documents
│   │       │
│   │       └── case_law/              # Ombudsman rulings + consumer court
│   │           # 100+ landmark rulings categorized by type
│   │
│   └── formulas/                      # Insurance calculation formulas
│       ├── __init__.py
│       ├── surrender_value.py         # GSV, SSV formulas per insurer type
│       ├── irr.py                     # Newton-Raphson IRR computation
│       ├── premium_adequacy.py        # HLV method, need-based analysis
│       ├── tax_benefit.py             # Section-wise tax computation
│       ├── inflation.py               # CPI-adjusted future value
│       ├── compound_growth.py         # FV, PV, annuity calculations
│       └── eazr_score.py             # EAZR proprietary scoring algorithm
│           # Factors: coverage_comprehensiveness, sublimit_freedom,
│           #          exclusion_fairness, insurer_quality, premium_value,
│           #          claim_process_quality, regulatory_compliance
│           # Weights: category-specific (health weights differ from life)
│           # Output: 1-10 score with component breakdown
│
├── guardrails/                        # SAFETY LAYER
│   ├── __init__.py
│   ├── hallucination.py               # PRIORITY ZERO GUARDRAIL
│   │   #
│   │   # RULE: Every factual claim must have a source.
│   │   # Sources (in order of trust):
│   │   #   1. Document extraction (confidence 0.85-0.95)
│   │   #   2. Knowledge Graph (confidence 0.90+, pre-verified)
│   │   #   3. RAG retrieval (confidence = similarity score × source trust)
│   │   #   4. Web search (confidence 0.60-0.80)
│   │   #   5. LLM reasoning only (confidence 0.30-0.50)
│   │   #   6. No source (confidence 0.00 — NEVER present as fact)
│   │   #
│   │   # BEHAVIOR:
│   │   # confidence >= 0.85 → State as fact
│   │   # 0.70 <= confidence < 0.85 → "Based on available data, X. I'd recommend verifying."
│   │   # 0.50 <= confidence < 0.70 → "I believe X, but I'm not fully certain. Please verify."
│   │   # confidence < 0.50 → "I don't have reliable information on X. Let me help you find it."
│   │   # confidence = 0.00 → NEVER STATE. Ask the user.
│   │   #
│   │   # SPECIAL RULE FOR NUMBERS:
│   │   # Copay %, sub-limits, premiums, sum insured — these MUST come from
│   │   # document extraction or KG. If from LLM reasoning only → DON'T STATE.
│   │   # "I couldn't find the copay percentage in your document. Could you check page X?"
│   │
│   ├── compliance.py                  # IRDAI compliance guardrails
│   │   # - Every recommendation includes disclaimer
│   │   # - Never say "you should buy X" → say "based on your profile, X may suit your needs"
│   │   # - Never guarantee returns
│   │   # - Never guarantee claim settlement
│   │   # - Always disclose: "EAZR provides information, not insurance advice"
│   │   # - Flag if conversation drifts into regulated territory (e.g., "I'll sell you a policy")
│   │
│   ├── financial.py                   # Financial data validation
│   │   # - Range checking: premium can't be negative, sum insured must be > 0
│   │   # - Unit checking: ₹ amounts in lakhs/crores, not raw numbers
│   │   # - Consistency: if premium is ₹50,000 and coverage is ₹50L, ratio check passes
│   │   # - If premium is ₹50 and coverage is ₹50L → flag as suspicious extraction
│   │
│   ├── emotional.py                   # Emotional state handling
│   │   # If emotional_state == "distressed":
│   │   #   - Lead with empathy: "I understand this is stressful..."
│   │   #   - Don't overwhelm with data
│   │   #   - Give one clear action step
│   │   #   - Escalate to Tier 3 (Claude) for more nuanced response
│   │   # If emotional_state == "frustrated":
│   │   #   - Acknowledge: "I see this isn't meeting your expectations..."
│   │   #   - Don't defend Hibiscus's architecture
│   │   #   - Be direct and actionable
│   │   #   - Offer to connect with human support
│   │
│   └── pii.py                         # PII protection
│       # - Mask Aadhaar, PAN, policy numbers in logs
│       # - Don't store health conditions as raw text (categories only)
│       # - Encrypt sensitive fields in PostgreSQL
│       # - Log scrubbing: no PII in LangSmith traces
│
├── llm/                               # LLM ROUTING LAYER
│   ├── __init__.py
│   ├── router.py                      # LiteLLM router with tier logic
│   │   #
│   │   # PROVIDER CONFIG:
│   │   # deepseek_v3_2:
│   │   #   model: "deepseek/deepseek-chat"  # V3.2 (latest)
│   │   #   api_key: ${DEEPSEEK_API_KEY}
│   │   #   temperature: 0.3 (factual accuracy)
│   │   #   max_tokens: 4096
│   │   #   timeout: 30s
│   │   #
│   │   # deepseek_r1:
│   │   #   model: "deepseek/deepseek-reasoner"
│   │   #   api_key: ${DEEPSEEK_API_KEY}
│   │   #   temperature: 0.5 (reasoning needs some creativity)
│   │   #   max_tokens: 8192 (R1 needs more space for chain-of-thought)
│   │   #   timeout: 60s (reasoning takes longer)
│   │   #
│   │   # claude_sonnet:
│   │   #   model: "anthropic/claude-sonnet-4-5"
│   │   #   api_key: ${ANTHROPIC_API_KEY}
│   │   #   temperature: 0.3
│   │   #   max_tokens: 4096
│   │   #   timeout: 30s
│   │   #
│   │   # FALLBACK CHAIN: DeepSeek V3.2 → DeepSeek R1 → Claude Sonnet
│   │   # COST TRACKING: Log tokens + model per call. Aggregate per conversation.
│   │
│   ├── model_selector.py              # Which model for which task
│   │   #
│   │   # SELECTION LOGIC:
│   │   # Task → Model mapping:
│   │   #   intent_classification → DeepSeek V3.2 (fast, cheap, good enough)
│   │   #   l1_l2_response → DeepSeek V3.2
│   │   #   policy_analysis → DeepSeek V3.2 (grounded by tool output)
│   │   #   surrender_calculation → DeepSeek R1 (multi-step math)
│   │   #   portfolio_optimization → DeepSeek R1 (complex reasoning)
│   │   #   tax_computation → DeepSeek R1 (precise calculation)
│   │   #   recommendation → DeepSeek V3.2 (grounded by KG)
│   │   #   education → DeepSeek V3.2 (simple, fast)
│   │   #   claims_guide → DeepSeek V3.2 (grounded by RAG)
│   │   #   regulation → DeepSeek V3.2 (grounded by RAG)
│   │   #   risk_detection → DeepSeek V3.2 (pattern matching)
│   │   #   grievance → DeepSeek V3.2 (grounded by RAG)
│   │   #   response_aggregation → DeepSeek V3.2 (synthesis)
│   │   #   low_confidence_escalation → Claude Sonnet (safety net)
│   │   #   distressed_user → Claude Sonnet (empathy + nuance)
│   │   #   memory_extraction → DeepSeek V3.2 (background, cheap)
│   │
│   └── prompts/                       # Prompt templates per agent
│       ├── system/
│       │   └── hibiscus_core.txt      # Core identity + capabilities + rules
│       ├── agents/
│       │   ├── policy_analyzer.txt
│       │   ├── surrender_calculator.txt
│       │   ├── recommender.txt
│       │   ├── claims_guide.txt
│       │   ├── calculator.txt
│       │   ├── researcher.txt
│       │   ├── regulation_engine.txt
│       │   ├── risk_detector.txt
│       │   ├── educator.txt
│       │   ├── portfolio_optimizer.txt
│       │   ├── tax_advisor.txt
│       │   └── grievance_navigator.txt
│       └── orchestrator/
│           ├── intent_classifier.txt
│           ├── task_decomposer.txt
│           └── response_aggregator.txt
│
├── evaluation/                        # HIBISCUSBENCH — QUALITY ASSURANCE
│   ├── __init__.py
│   ├── bench.py                       # Main benchmark runner
│   ├── metrics.py                     # Decision Quality (DQ) metric
│   │   # DQ = weighted(validity, specificity, correctness, safety)
│   │   # validity: Is the response actually answering the question?
│   │   # specificity: Does it reference THIS policy, not generic advice?
│   │   # correctness: Are the numbers right? Are the citations real?
│   │   # safety: No hallucination? Disclaimer present? No guaranteed returns?
│   │
│   ├── evaluator.py                   # Automated evaluation per test case
│   │   # Uses a separate LLM call (Claude) to grade Hibiscus's response
│   │   # Grades: PASS / PARTIAL / FAIL per dimension
│   │
│   ├── test_cases/                    # 100+ test cases minimum
│   │   ├── health/                    # 20+ health insurance scenarios
│   │   │   ├── analyze_star_comprehensive.json
│   │   │   ├── compare_health_plans_under_15k.json
│   │   │   ├── cashless_claim_process.json
│   │   │   ├── pre_existing_waiting_period.json
│   │   │   ├── room_rent_sublimit_explanation.json
│   │   │   └── ...
│   │   ├── life/                      # 20+ life insurance scenarios
│   │   │   ├── should_i_surrender_lic_endowment.json
│   │   │   ├── term_vs_ulip_comparison.json
│   │   │   ├── surrender_value_calculation.json
│   │   │   ├── tax_benefit_80c.json
│   │   │   └── ...
│   │   ├── motor/                     # 10+ motor scenarios
│   │   ├── travel/                    # 10+ travel scenarios
│   │   ├── pa/                        # 10+ PA scenarios
│   │   ├── cross_category/            # 10+ portfolio/multi-policy scenarios
│   │   ├── emotional/                 # 10+ distress/frustration scenarios
│   │   ├── adversarial/               # 10+ edge cases
│   │   │   ├── user_asks_for_guaranteed_returns.json
│   │   │   ├── user_uploads_non_insurance_document.json
│   │   │   ├── user_provides_contradictory_info.json
│   │   │   ├── hallucination_trap_fake_insurer.json
│   │   │   └── ...
│   │   └── ipf_svf/                   # 10+ financing scenarios
│   │
│   └── reports/                       # Benchmark results (gitignored, generated)
│       └── .gitkeep
│
├── observability/                     # PRODUCTION MONITORING
│   ├── __init__.py
│   ├── logger.py                      # Structured JSON logging
│   │   # Every log entry includes:
│   │   # {request_id, session_id, user_id, timestamp, level, component,
│   │   #  agent_name (if applicable), model_used, tokens_in, tokens_out,
│   │   #  latency_ms, confidence, message}
│   │   #
│   │   # LOG AT EVERY PIPELINE STEP:
│   │   # 1. Chat endpoint received → LOG
│   │   # 2. Context assembled → LOG (memory layers hit, token count)
│   │   # 3. Intent classified → LOG (category, intent, complexity, emotion)
│   │   # 4. Execution plan created → LOG (agents in plan)
│   │   # 5. Each agent starts → LOG (agent name, model, task)
│   │   # 6. Each tool call → LOG (tool name, args, result summary, latency)
│   │   # 7. Each agent completes → LOG (confidence, latency, tokens)
│   │   # 8. Response aggregated → LOG (agents contributed, final confidence)
│   │   # 9. Guardrails checked → LOG (pass/fail per guardrail)
│   │   # 10. Memory stored → LOG (memories extracted)
│   │   # 11. Response sent → LOG (total latency, total tokens, total cost)
│   │   #
│   │   # WHERE LOGS STOP = WHERE THE PIPELINE IS BROKEN.
│   │
│   ├── langsmith.py                   # LangSmith integration for agent debugging
│   │   # Traces every LangGraph run with full state visibility
│   │   # See which agent was called, what tools it used, what it returned
│   │   # Debug: "Why did Hibiscus hallucinate a copay?" → check PolicyAnalyzer trace
│   │
│   ├── cost_tracker.py                # Per-conversation cost tracking
│   │   # Tracks: model, tokens_in, tokens_out, cost_usd per LLM call
│   │   # Aggregates: cost_per_conversation, cost_per_user, cost_per_day
│   │   # Alerts: if avg conversation cost > threshold (₹5), alert
│   │
│   └── metrics.py                     # Prometheus-compatible metrics
│       # hibiscus_conversations_total (counter)
│       # hibiscus_response_latency_seconds (histogram, labels: complexity)
│       # hibiscus_agent_invocations_total (counter, labels: agent_name)
│       # hibiscus_llm_tokens_total (counter, labels: model, direction)
│       # hibiscus_confidence_score (histogram)
│       # hibiscus_guardrail_failures_total (counter, labels: guardrail_type)
│
└── tests/                             # TEST SUITE
    ├── __init__.py
    ├── unit/
    │   ├── test_intent_classifier.py  # Category + intent + complexity classification
    │   ├── test_model_router.py       # Correct model selected per task
    │   ├── test_confidence_scoring.py # Confidence thresholds enforced
    │   ├── test_guardrails.py         # Hallucination, compliance, financial guards
    │   ├── test_formulas.py           # SV, IRR, tax calculations verified
    │   └── test_memory_assembler.py   # Context assembly priority order
    ├── integration/
    │   ├── test_agent_pipeline.py     # Full flow: intent → agent → tools → response
    │   ├── test_rag_retrieval.py      # RAG returns relevant chunks
    │   ├── test_kg_queries.py         # KG queries return correct data
    │   └── test_existing_api_tools.py # Existing API tool wrappers work
    └── e2e/
        ├── test_policy_upload.py      # Upload → analyze → chat about results
        ├── test_surrender_inquiry.py  # "Should I surrender?" full flow
        └── test_claims_assistance.py  # Claims guidance full flow
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
