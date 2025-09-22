# RAG Service with GPU support
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HF_CACHE_DIR=/app/data/cache

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
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

# Install PyTorch with CUDA support (will use host GPU drivers)
RUN pip install --no-cache-dir torch==2.5.1+cu118 torchaudio==2.5.1+cu118 torchvision==0.20.1+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies (excluding llama-cpp-python)
RUN pip install --no-cache-dir -r requirements.txt

# Install LLaMA CPP with CUDA support
# Add CUDA stub libraries to the linker path and update linker cache
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1
ENV LDFLAGS="-L/usr/local/cuda/lib64/stubs"
RUN echo "/usr/local/cuda/lib64/stubs" > /etc/ld.so.conf.d/cuda-stubs.conf && \
    ldconfig
RUN pip install --no-cache-dir llama-cpp-python==0.3.15 --force-reinstall --no-cache-dir

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p data/cache data/models data/storage data/vectordb

# Expose port
EXPOSE 8000

# Command to run the service
CMD ["python", "main.py"]