# ==============================================================================
# OpenPaperCheck Backend API Container (FastAPI + SQLite Snapshot + Ingest CLI)
# Multi-stage lightweight build on Python 3.12 Slim
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and source
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build wheel package
RUN pip install --no-cache-dir build \
    && python -m build --wheel

# ------------------------------------------------------------------------------
# Production Runtime Stage
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Create dedicated non-root user
RUN groupadd -g 1001 opc && \
    useradd -u 1001 -g opc -s /bin/bash -m opc

WORKDIR /app

# Install curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install openpapercheck with server dependencies
RUN pip install --no-cache-dir /tmp/*.whl[server] \
    && rm -rf /tmp/*.whl

# Setup data and cache directories
ENV OPC_DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/data && chown -R opc:opc /app

# Switch to non-root user
USER opc

# Pre-build bundled sample snapshot so container runs offline out-of-the-box
RUN opc snapshot build --sample

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

CMD ["uvicorn", "openpapercheck.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
