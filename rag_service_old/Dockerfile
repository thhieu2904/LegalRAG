# RAG Service with GPU support
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HF_CACHE_DIR=/app/data/models/hf_cache
ENV ENVIRONMENT=docker
ENV LEGALRAG_BASE_PATH=/app
ENV LEGALRAG_DATA_PATH=/app/data

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    python3.11-venv \
    gcc \
    g++ \
    cmake \
    make \
    ninja-build \
    git \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-clean.txt ./requirements.txt

# Install PyTorch with CUDA 12.1 support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install llama-cpp-python with CUDA support
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1
ENV LDFLAGS="-L/usr/local/cuda/lib64/stubs"
RUN echo "/usr/local/cuda/lib64/stubs" > /etc/ld.so.conf.d/cuda-stubs.conf && \
    ldconfig
RUN pip install --no-cache-dir llama-cpp-python --force-reinstall --no-cache-dir

# Install other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure directories exist (but don't overwrite existing files)
RUN mkdir -p data/models data/vectordb

# Note: data/cache and data/storage already copied by 'COPY . .' above

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the service
CMD ["python", "main.py"]