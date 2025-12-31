# ============================================
# Dockerfile for Form Service
# ============================================
# Handles form rendering, filling, and CCCD scanning

FROM python:3.11-slim

# Metadata
LABEL maintainer="LegalRAG Team"
LABEL description="Form processing service"
LABEL version="1.0.0"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for pyzbar and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    libzbar-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --retries 10 --timeout 300 -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . /app/

# Switch to non-root user
USER appuser

# Expose service port
EXPOSE 8015

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8015/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]
