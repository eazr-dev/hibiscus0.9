# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
# Production container image
# Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.

FROM python:3.12-slim

LABEL maintainer="EAZR AI Engineering"
LABEL com.hibiscus.engine="hibiscus"
LABEL com.hibiscus.version="0.9.0"
LABEL com.hibiscus.vendor="EAZR Digipayments Pvt Ltd"
LABEL com.hibiscus.url="https://eazr.in"
LABEL org.opencontainers.image.title="Hibiscus"
LABEL org.opencontainers.image.description="EAZR AI Insurance Intelligence Engine"
LABEL org.opencontainers.image.version="0.9.0"
LABEL org.opencontainers.image.vendor="EAZR Digipayments Pvt Ltd"
LABEL org.opencontainers.image.url="https://eazr.in"

# System dependencies (including Tesseract for OCR fallback and poppler for pdf2image)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy full package (pyproject.toml + source) — hatchling needs source to resolve packages
COPY hibiscus/ /app/hibiscus/

# Install package with dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    cd /app/hibiscus && pip install --no-cache-dir .

# Create non-root user
RUN adduser --disabled-password --gecos "" hibiscus && \
    chown -R hibiscus:hibiscus /app

USER hibiscus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/hibiscus/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "hibiscus.main:app", "--host", "0.0.0.0", "--port", "8001", "--no-access-log"]
