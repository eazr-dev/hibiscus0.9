<!-- Hibiscus v0.9 — EAZR AI Insurance Intelligence Engine -->
<!-- Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved. -->

# Hibiscus API — Developer Guide

## Quick Start

### 1. Environment Setup

```bash
cp hibiscus/.env.example .env
# Fill in: DEEPSEEK_API_KEY, NEO4J_PASSWORD, ANTHROPIC_API_KEY (optional)
```

### 2. Start Services

```bash
docker compose up -d --build
# Wait for all services to be healthy (~60s)
docker compose ps  # All should show "healthy"
```

### 3. Seed Knowledge Infrastructure

```bash
docker exec hibiscus-api python -m hibiscus.knowledge.graph.seed  # Neo4j KG
docker exec hibiscus-api python -m hibiscus.knowledge.rag.ingestion  # Qdrant RAG
```

### 4. First API Call

```bash
curl -X POST http://localhost:8001/hibiscus/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is health insurance?",
    "session_id": "test-session",
    "user_id": "dev-user"
  }'
```

---

## Authentication

Hibiscus uses JWT Bearer tokens. In **dev mode** (empty `JWT_SECRET`), auth is bypassed — all requests are allowed.

**Production:**
```bash
curl -X POST http://localhost:8001/hibiscus/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{"message": "...", "session_id": "...", "user_id": "..."}'
```

JWT tokens should contain `user_id` and `session_id` claims. Invalid tokens are rejected; missing tokens are allowed (anonymous mode).

---

## Endpoints

### POST /hibiscus/chat

Main conversation endpoint. Supports both standard JSON and streaming SSE responses.

**Non-streaming:**
```bash
curl -X POST http://localhost:8001/hibiscus/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare term life insurance for a 30 year old earning 15 lakh",
    "session_id": "sess_001",
    "user_id": "user_123",
    "stream": false
  }'
```

**Response:**
```json
{
  "response": "Here is a comparison of term life insurance...",
  "session_id": "sess_001",
  "request_id": "req_abc123",
  "confidence": 0.85,
  "sources": [
    {"type": "knowledge_graph", "reference": "IRDAI CSR Data 2023-24", "confidence": 0.9}
  ],
  "follow_up_suggestions": ["Want me to calculate the premium?"],
  "products_relevant": ["IPF"],
  "agents_invoked": ["recommender"],
  "guardrail_results": {"hallucination": true, "compliance": true},
  "latency_ms": 3200,
  "cost_inr": 0.045,
  "response_type": "text"
}
```

**Streaming (SSE):**
```bash
curl -N -X POST http://localhost:8001/hibiscus/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is health insurance?",
    "session_id": "sess_001",
    "user_id": "user_123",
    "stream": true
  }'
```

**SSE chunk types:**

| Type | Description | Payload |
|------|-------------|---------|
| `metadata` | Processing started | `metadata.request_id`, `metadata.status` |
| `token` | Response text chunk | `content` (string) |
| `done` | Processing complete | `metadata.confidence`, `metadata.agents_invoked`, `metadata.latency_ms` |
| `error` | Error occurred | `content` (error message) |

Each chunk is JSON-encoded in `data:` lines:
```
data: {"type": "metadata", "metadata": {"request_id": "req_abc", "status": "processing"}}

data: {"type": "token", "content": "Health insurance is"}

data: {"type": "token", "content": " a contract between"}

data: {"type": "done", "metadata": {"confidence": 0.75, "latency_ms": 2100}}
```

### POST /hibiscus/analyze

Upload and analyze a policy document.

```bash
curl -X POST http://localhost:8001/hibiscus/analyze \
  -F "file=@policy.pdf" \
  -F "user_id=user_123" \
  -F "session_id=sess_001"
```

### GET /hibiscus/health

Health check for all dependencies.

```bash
curl -s http://localhost:8001/hibiscus/health | python -m json.tool
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.9.0",
  "dependencies": {
    "redis": "connected",
    "mongodb": "connected",
    "neo4j": "connected",
    "qdrant": "connected"
  }
}
```

### GET /hibiscus/metrics

Prometheus-format metrics.

```bash
curl -s http://localhost:8001/hibiscus/metrics
```

### GET /hibiscus/chat/history/{session_id}

Retrieve conversation history for a session.

```bash
curl -s http://localhost:8001/hibiscus/chat/history/sess_001
```

### WS /hibiscus/ws

WebSocket endpoint for real-time bidirectional chat.

```javascript
const ws = new WebSocket("ws://localhost:8001/hibiscus/ws?session_id=sess_001&user_id=user_123");
ws.send(JSON.stringify({ type: "message", content: "Hello" }));
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 401 | Unauthorized (invalid JWT in production) |
| 429 | Rate limited (retry after 60s) |
| 500 | Internal error (check `request_id` in logs) |

**Error response format:**
```json
{
  "error": "Rate limit exceeded",
  "detail": "60 requests per minute limit reached",
  "request_id": "req_abc123"
}
```

---

## Rate Limiting

- **Limit:** 60 requests/minute per IP
- **Header:** `X-RateLimit-Remaining` in response
- **Strategy:** Wait and retry after 60 seconds, or implement exponential backoff

---

## Interactive Docs

- **Swagger UI:** http://localhost:8001/hibiscus/docs
- **ReDoc:** http://localhost:8001/hibiscus/redoc
- **OpenAPI JSON:** http://localhost:8001/hibiscus/openapi.json
