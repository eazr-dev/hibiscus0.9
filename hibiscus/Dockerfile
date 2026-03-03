FROM python:3.12-slim

LABEL maintainer="EAZR Engineering"
LABEL description="Hibiscus v5.0 — AI Intelligence Engine"

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first (cache layer)
COPY hibiscus/pyproject.toml /app/hibiscus/pyproject.toml

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi uvicorn[standard] python-multipart \
        langgraph langchain langchain-core langchain-community langchain-text-splitters \
        litellm openai anthropic \
        httpx tenacity \
        redis hiredis motor pymongo \
        asyncpg sqlalchemy \
        qdrant-client fastembed tiktoken \
        neo4j \
        pydantic pydantic-settings \
        python-dotenv structlog orjson numpy python-dateutil \
        tavily-python langsmith \
        prometheus_client

# Pre-download fastembed model (BAAI/bge-large-en-v1.5) during build — cached in image
# This avoids a ~2s model download on first request after container start
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-large-en-v1.5')" 2>/dev/null || true

# Copy application code
COPY hibiscus/ /app/hibiscus/

# Create non-root user
RUN adduser --disabled-password --gecos "" hibiscus && \
    chown -R hibiscus:hibiscus /app

USER hibiscus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/hibiscus/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "hibiscus.main:app", "--host", "0.0.0.0", "--port", "8001", "--no-access-log"]
