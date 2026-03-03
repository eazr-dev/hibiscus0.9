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
        langgraph langchain langchain-core langchain-community \
        litellm openai anthropic \
        httpx tenacity \
        redis hiredis motor pymongo \
        asyncpg sqlalchemy \
        qdrant-client tiktoken \
        pydantic pydantic-settings \
        python-dotenv structlog orjson numpy python-dateutil

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

CMD ["uvicorn", "hibiscus.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-config", "/dev/null"]
