# ============================================
# Dockerfile for LLM Service - PhoGPT Edition
# ============================================
# Multi-stage build with llama-cpp-python
# Supports both CPU and GPU (CUDA) inference

FROM python:3.11-slim as base

# Metadata
LABEL maintainer="LegalRAG Team"
LABEL description="Vietnamese Legal LLM using PhoGPT-4B"
LABEL version="1.0.0"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ============================================
# Dependencies Stage - CPU Version
# ============================================

FROM base as dependencies-cpu

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages with CPU-only llama-cpp-python
RUN pip install --upgrade pip && \
    CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
    pip install --retries 10 --timeout 300 llama-cpp-python==0.2.90 && \
    pip install --retries 10 --timeout 300 -r requirements.txt

# ============================================
# Dependencies Stage - GPU Version (CUDA)
# ============================================

FROM nvidia/cuda:12.1.1-devel-ubuntu22.04 as dependencies-gpu

# Install Python and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    cmake \
    curl \
    git \
    cuda-libraries-dev-12-1 \
    && rm -rf /var/lib/apt/lists/*

# Make python3.11 the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages with CUDA-enabled llama-cpp-python (prebuilt wheel)
RUN pip install --upgrade pip && \
    pip install --retries 10 --timeout 300 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
        llama-cpp-python==0.2.90 && \
    pip install --retries 10 --timeout 300 -r requirements.txt

# ============================================
# Runtime Stage - CPU
# ============================================

FROM base as runtime

# Copy installed packages from CPU dependencies stage
COPY --from=dependencies-cpu /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies-cpu /usr/local/bin /usr/local/bin

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/models && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser download_model.py /app/

# Switch to non-root user
USER appuser

# Expose service port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8006"]

# ============================================
# Runtime Stage - GPU (CUDA)
# ============================================

FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 as runtime-gpu

# Install Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    curl \
    libgomp1 \
    cuda-libraries-12-1 \
    && rm -rf /var/lib/apt/lists/*

# Make python3.11 the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

WORKDIR /app

# Copy installed packages from GPU dependencies stage
COPY --from=dependencies-gpu /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages

# Create non-root user and directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/models && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser download_model.py /app/

USER appuser

EXPOSE 8006

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8006"]

# ============================================
# Build Instructions
# ============================================
# CPU version (default):
#   docker build --target runtime -t llm-service:cpu .
#
# GPU version (requires NVIDIA Docker):
#   docker build --target runtime-gpu -t llm-service:gpu .
#
# Run CPU:
#   docker run -p 8006:8006 -v $(pwd)/models:/app/models llm-service:cpu
#
# Run GPU:
#   docker run --gpus all -p 8006:8006 -v $(pwd)/models:/app/models llm-service:gpu
# ============================================
