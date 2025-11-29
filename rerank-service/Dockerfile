# ============================================
# Dockerfile for Rerank Service
# ============================================
# Multi-stage build for optimized image size
# Supports both CPU and GPU (CUDA) inference

FROM python:3.11-slim as base

# Metadata
LABEL maintainer="LegalRAG Team"
LABEL description="Vietnamese document reranking service"
LABEL version="1.0.0"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ============================================
# Dependencies Stage
# ============================================

FROM base as dependencies

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages with retry settings
RUN pip install --upgrade pip && \
    pip install --retries 10 --timeout 300 -r requirements.txt

# ============================================
# Runtime Stage
# ============================================

FROM base as runtime

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/models && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/

# Switch to non-root user
USER appuser

# Expose service port
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8013/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8013"]

# ============================================
# CPU Runtime (Default for laptop 6GB VRAM)
# ============================================
# Alias for runtime stage - used explicitly in docker-compose
FROM runtime as runtime-cpu

# ============================================
# GPU Support (Optional - for 12GB+ VRAM servers)
# ============================================
# To build with GPU support:
# docker build --target runtime-gpu -t rerank-service:gpu .
#
# To run with GPU:
# docker run --gpus all -p 8013:8013 rerank-service:gpu

FROM runtime as runtime-gpu

# No additional packages needed - PyTorch includes CUDA runtime
# Just use this target to indicate GPU-capable build
# NVIDIA GPU access is handled by Docker runtime with --gpus flag
