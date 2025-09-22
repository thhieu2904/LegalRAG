# Identifill Service Dockerfile - Fixed OpenCV conflict
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and QR code processing
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libzbar0 \
    libzbar-dev \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages directly
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p models

# Expose port
EXPOSE 8002

# Set environment variables
ENV PYTHONPATH=/app

# Command to run the service
CMD ["python", "main.py"]