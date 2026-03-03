# =============================================================
# EAZR Chat — FastAPI Application
# =============================================================
FROM python:3.12-slim

# Minimal system deps (no build-essential — use binary wheels only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    pip install --no-cache-dir psycopg2-binary boto3 matplotlib pandas PyPDF2 \
        pdfplumber PyMuPDF qrcode websockets

# Copy application source
COPY . .

# Create directories the app expects
RUN mkdir -p /app/frontend /app/faiss_index /app/uploads /app/generated_pdfs /app/reports

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "65", "--log-level", "info"]
