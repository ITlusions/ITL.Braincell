# Dockerfile for BrainCell REST API Service
# This service provides programmatic access to memory functions
FROM python:3.12-alpine AS builder

WORKDIR /build

# Install build dependencies (minimal)
RUN apk add --no-cache build-base postgresql-dev

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --target ./python-packages -r requirements.txt

# ========== Runtime Stage ==========
FROM python:3.12-alpine

WORKDIR /app

# Install only essential runtime dependencies
RUN apk add --no-cache postgresql-client curl

# Copy installed packages from builder
COPY --from=builder /build/python-packages /usr/local/lib/python3.12/site-packages

# Copy application code
COPY src/api src/api
COPY src/core src/core
COPY src/services src/services
COPY src/main.py src/

# Create non-root user
RUN addgroup braincell && adduser -D -G braincell braincell && \
    chown -R braincell:braincell /app

USER braincell

EXPOSE 8000

# Health check for API
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the API service
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
