<!-- 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine -->

# 🌺 Hibiscus v0.9

![Version](https://img.shields.io/badge/version-0.9.0-blue)
![DQ Score](https://img.shields.io/badge/DQ_Score-0.841-green)
![Agents](https://img.shields.io/badge/agents-12-orange)
![License](https://img.shields.io/badge/license-Proprietary-red)

**EAZR AI Insurance Intelligence Engine** — a 12-agent orchestration system that provides policy analysis, product recommendations, claims guidance, tax advisory, surrender value calculations, and portfolio optimization for Indian insurance consumers. Built on LangGraph with DeepSeek primary LLM routing, a Neo4j knowledge graph (62 insurers, 1,207 products, 102 regulations), Qdrant RAG (847 chunks), and a 6-layer memory system.

```
┌─────────────────────────────────────────────────────┐
│  🌺 HIBISCUS v0.9                                   │
│  EAZR AI Insurance Intelligence Engine              │
│  ─────────────────────────────────────               │
│  12 Agents · 1,207 Products · 102 Regulations       │
│  Built in India · EAZR Digipayments Pvt Ltd         │
│  https://eazr.in                                     │
└─────────────────────────────────────────────────────┘
```

## Architecture

```
                    ┌──────────────┐
                    │   FastAPI    │
                    │  /hibiscus/* │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  LangGraph   │
                    │  Supervisor  │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │   Intent    │ │   Context   │ │  Guardrail  │
    │  Classify   │ │  Assembly   │ │   Check     │
    └──────┬──────┘ └──────┬──────┘ └─────────────┘
           │               │
    ┌──────▼───────────────▼──────┐
    │      12 Specialist Agents    │
    │  ┌─────────┐ ┌────────────┐ │
    │  │Analyzer │ │Recommender │ │
    │  │Claims   │ │Calculator  │ │
    │  │Tax      │ │Surrender   │ │
    │  │Educator │ │Researcher  │ │
    │  │Risk     │ │Regulation  │ │
    │  │Portfolio│ │Grievance   │ │
    │  └─────────┘ └────────────┘ │
    └──────┬───────────────┬──────┘
           │               │
    ┌──────▼──────┐ ┌──────▼──────┐
    │  Tools      │ │  Memory     │
    │  KG·RAG·Calc│ │  6 Layers   │
    └─────────────┘ └─────────────┘
```

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env   # Add your DEEPSEEK_API_KEY

# 2. Start all services
make dev

# 3. Open Swagger UI
open http://localhost:8001/hibiscus/docs
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/hibiscus/chat` | Main conversation endpoint (JSON + SSE streaming) |
| `POST` | `/hibiscus/analyze` | Policy document analysis (PDF upload) |
| `GET`  | `/hibiscus/portfolio/{user_id}` | Portfolio breakdown and optimization |
| `GET`  | `/hibiscus/chat/history/{session_id}` | Conversation history |
| `GET`  | `/hibiscus/health` | Dependency health check |
| `GET`  | `/hibiscus/metrics` | Prometheus metrics |
| `WS`   | `/hibiscus/ws/{session_id}` | WebSocket real-time chat |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Orchestration | LangGraph (StateGraph) |
| Primary LLM | DeepSeek V3.2 (80%) + R1 (15%) + Claude Sonnet (5%) |
| Knowledge Graph | Neo4j 5 — 62 insurers, 1,207 products, 102 regulations |
| RAG | Qdrant + fastembed (BAAI/bge-large-en-v1.5) — 847 chunks |
| Memory | Redis (session) · Qdrant (conversation) · PostgreSQL (profile/outcomes) · MongoDB (documents) |
| API | FastAPI + uvicorn + ORJSON |
| Guardrails | Hallucination · IRDAI Compliance · Financial · Emotional · PII |
| Observability | structlog (JSON) · Prometheus · LangSmith |

## Metrics

| Metric | Value |
|--------|-------|
| HibiscusBench DQ | **0.841** (target 0.800) |
| Test pass rate | **120/120 (100%)** |
| Avg cost/conversation | **~₹0.045** |
| Streaming TTFT | **~2.0s** |

## License

Proprietary — Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.

https://eazr.in
