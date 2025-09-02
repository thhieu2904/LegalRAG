FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Tạo thư mục data và models với quyền write
RUN mkdir -p data/models/llm_dir data/models/embeddings data/models/rerank data/models/hf_cache \
             data/documents data/vectordb data/cache && \
    chmod -R 755 data/

# Thiết lập biến môi trường
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# Override HuggingFace cache để lưu trong app
ENV HF_HOME=/app/data/models/hf_cache
ENV HUGGINGFACE_HUB_CACHE=/app/data/models/hf_cache/hub
ENV HF_HUB_CACHE=/app/data/models/hf_cache/hub

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Command to run
CMD ["python", "main.py"]
