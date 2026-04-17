# Dockerfile for BrainCell MCP Server (Model Context Protocol)
# This service provides standardized integration interface for AI tools
FROM python:3.12-alpine AS builder

WORKDIR /build

# Install build dependencies (minimal)
RUN apk add --no-cache build-base postgresql-dev

# Copy MCP requirements and install
COPY mcp/requirements.txt .
RUN pip install --no-cache-dir --target ./python-packages -r requirements.txt

# ========== Runtime Stage ==========
FROM python:3.12-alpine

WORKDIR /app

# Install only essential runtime dependencies
RUN apk add --no-cache postgresql-client curl

# Copy installed packages from builder
COPY --from=builder /build/python-packages /usr/local/lib/python3.12/site-packages

# Copy application code - MCP specific
COPY src/mcp src/mcp
COPY src/core src/core
COPY src/__init__.py src/

# Create non-root user
RUN addgroup braincell && adduser -D -G braincell braincell && \
    chown -R braincell:braincell /app

USER braincell

EXPOSE 9506

# Health check for MCP Server
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:9506/health || exit 1

# Start the MCP server
CMD ["python", "-m", "src.mcp.server_http"]
