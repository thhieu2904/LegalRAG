# Admin Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# LibreOffice for .doc file conversion (Vietnamese legal documents are typically .doc format)
RUN apt-get update && apt-get install -y \
    gcc \
    libreoffice-writer \
    libreoffice-core \
    libreoffice-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path for imports
ENV PYTHONPATH=/app

# Set environment variable for Docker detection
ENV ENVIRONMENT=docker

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python", "main.py"]