# Identifill Service Dockerfile
FROM python:3.11-slim

# Install system dependencies for OpenCV and QR scanning
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libgthread-2.0-0 \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libice6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory for volume mounting
RUN mkdir -p /app/models

# Expose default port (can be overridden with PORT env var)
EXPOSE 8005

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=docker
ENV SERVICE_PORT=8005

# Health check (uses env variable)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import httpx; import os; httpx.get(f'http://localhost:{os.getenv(\"SERVICE_PORT\", 8005)}/health')" || exit 1

# Start the application
CMD ["python", "main.py"]