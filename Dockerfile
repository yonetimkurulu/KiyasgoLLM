# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install only production dependencies (exclude torch/transformers for smaller image)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install \
    fastapi==0.109.0 \
    "uvicorn[standard]==0.27.0" \
    groq==0.4.2 \
    openai==1.12.0 \
    httpx==0.26.0 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0 \
    redis==5.0.1 \
    cachetools==5.3.2 \
    asyncpg==0.29.0 \
    sqlalchemy==2.0.25 \
    python-dotenv==1.0.1 \
    tenacity==8.2.3 \
    structlog==24.1.0 \
    slowapi==0.1.9

# ---- Runtime Stage ----
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY .env.example ./.env.example

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
