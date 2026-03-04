<!-- Hibiscus v0.9 — EAZR AI Insurance Intelligence Engine -->
<!-- Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved. -->

# Hibiscus Architecture Overview

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Hibiscus v0.9 — EAZR AI                       │
│                                                                   │
│  ┌─────────┐    ┌──────────────────────────────────────────────┐ │
│  │ FastAPI  │───▶│           LangGraph Orchestrator              │ │
│  │ /chat    │    │                                               │ │
│  │ /analyze │    │  assemble_context ──▶ classify_intent          │ │
│  │ /health  │    │       │                    │                   │ │
│  └─────────┘    │       ▼                    ▼                   │ │
│                 │  [memory layers]    ┌──────────────┐           │ │
│                 │                     │ direct_llm   │ (L1/L2)   │ │
│                 │                     │ plan+dispatch │ (L3/L4)   │ │
│                 │                     └──────┬───────┘           │ │
│                 │                            ▼                   │ │
│                 │                   aggregate_response            │ │
│                 │                            │                   │ │
│                 │                            ▼                   │ │
│                 │                   check_guardrails              │ │
│                 │                            │                   │ │
│                 │                            ▼                   │ │
│                 │                    store_memory                 │ │
│                 └──────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    12 Specialist Agents                      │  │
│  │                                                              │  │
│  │  policy_analyzer    recommender     surrender_calculator     │  │
│  │  claims_guide       calculator      tax_advisor              │  │
│  │  explainer          comparator      risk_detector            │  │
│  │  portfolio_optimizer researcher     general_chat             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────────────────┐│
│  │   Neo4j KG   │ │  Qdrant RAG  │ │     LLM Router            ││
│  │ 62 insurers  │ │  847 chunks  │ │ DeepSeek V3 (80%)         ││
│  │ 1,207 prods  │ │  794 vectors │ │ DeepSeek R1 (15%)         ││
│  │ 100 regs     │ │              │ │ Claude Sonnet (5%)        ││
│  │ 760 benchmks │ │              │ │ via LiteLLM               ││
│  └──────────────┘ └──────────────┘ └───────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘

External:
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ PostgreSQL│ │ MongoDB  │ │  Redis   │ │  Qdrant  │
  │ profiles  │ │ documents│ │ sessions │ │ vectors  │
  │ outcomes  │ │ extracts │ │ cache    │ │ RAG+mem  │
  └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## LangGraph Pipeline — 8 Nodes

```
1. assemble_context    → Parallel fetch from 6 memory layers (~50ms)
2. classify_intent     → Fast keyword + LLM intent classification
3. [BRANCH]
   a. direct_llm       → L1/L2 simple queries — single LLM call
   b. plan_execution   → L3/L4 complex — build execution plan
      dispatch_agents   → Run agents (parallel within groups)
      aggregate_response→ Synthesize multi-agent outputs
4. check_guardrails    → Hallucination, compliance, financial, emotional, PII
5. store_memory        → Fire-and-forget background storage
```

## 12 Specialist Agents

| # | Agent | Role | LLM Tier |
|---|-------|------|----------|
| 1 | `policy_analyzer` | Analyze uploaded policy documents (ABSORB) | Tier 1 |
| 2 | `surrender_calculator` | Surrender value + hold-vs-exit analysis | Tier 2 |
| 3 | `recommender` | Product recommendations based on gaps | Tier 1 |
| 4 | `claims_guide` | Claims filing guidance and process | Tier 1 |
| 5 | `calculator` | Financial calculations (life need, IRR, EMI) | Tier 2 |
| 6 | `tax_advisor` | Tax benefits under 80C, 80D, 10(10D) | Tier 1 |
| 7 | `explainer` | Insurance concept explanations | Tier 1 |
| 8 | `risk_detector` | Mis-selling, coverage gaps, red flags | Tier 1 |
| 9 | `comparator` | Product comparison tables | Tier 1 |
| 10 | `portfolio_optimizer` | Portfolio review and optimization | Tier 2 |
| 11 | `researcher` | Web search for latest regulations | Tier 1 |
| 12 | `general_chat` | General conversation and greetings | Tier 1 |

## 6-Layer Memory System

| Layer | Storage | Purpose | TTL |
|-------|---------|---------|-----|
| L1 Session | Redis | Current conversation context | 1 hour |
| L2 Conversation | Qdrant | Past relevant conversations (semantic) | Permanent |
| L3 User Profile | PostgreSQL | Demographics, preferences | Permanent |
| L4 Knowledge | Qdrant | Extracted insights per user | Permanent |
| L5 Outcome | PostgreSQL | Advice outcomes, follow-ups | Permanent |
| L6 Document | MongoDB | Uploaded document extractions | Permanent |

## LLM Routing Tiers

| Tier | Model | Usage | Cost |
|------|-------|-------|------|
| Tier 1 | DeepSeek V3.2 (`deepseek-chat`) | 80% — general queries, explanations | ~₹0.02/call |
| Tier 2 | DeepSeek R1 (`deepseek-reasoner`) | 15% — complex math, multi-step reasoning | ~₹0.08/call |
| Tier 3 | Claude Sonnet (`claude-sonnet-4-5`) | 5% — safety net, fallback | ~₹0.15/call |

Routing is handled by LiteLLM with automatic fallback: Tier 1 → Tier 3 on failure.

## Guardrail Pipeline

Applied to every response before delivery:

1. **Hallucination guard** — Cross-check numbers against extraction/KG sources
2. **Compliance guard** — IRDAI disclaimer on all insurance advice
3. **Financial guard** — No specific return promises, no "guaranteed" claims
4. **Emotional guard** — Empathetic framing for distressed users
5. **PII guard** — Redact Aadhaar, PAN, phone numbers from logs

## Knowledge Infrastructure

### Neo4j Knowledge Graph
- **62 insurers** (life, health, general) with CSR, ICR, solvency data
- **1,207 products** (1,041 with IRDAI UIN numbers)
- **100 IRDAI regulations** (circulars, master guidelines)
- **760 CSR benchmarks** (time-series: 2019-2024)
- **32 tax rules** (80C, 80D, 10(10D), NPS, etc.)
- **17 ombudsman offices** (jurisdiction mapping)
- **60 CSR entries** (per-insurer claim settlement data)

### Qdrant RAG Corpus
- **847 chunks** across 6 collections
- IRDAI circulars, policy wordings, glossary, tax rules, claims processes, case law
- Embedding: `BAAI/bge-large-en-v1.5` (local inference)

## Native Extraction (ABSORB Pipeline)

```
PDF → text (pdfplumber + OCR fallback)
    → classify (3-tier: keyword → regex → LLM)
    → extract (type-specific LLM prompts)
    → validate (5-check: completeness, consistency, range, cross-field, regex)
    → score (EAZR Score 0-100, using KG benchmarks)
    → gap analysis (coverage gaps with severity + cost estimates)
```

Supports 5 policy types: health, life (term/endowment/ULIP), motor, travel, personal accident.
366 extraction fields across all types. 118/118 extraction tests passing.
