FROM python:3.11-slim

WORKDIR /app

# Create model cache directory with proper permissions
RUN mkdir -p /app/models && chmod 777 /app/models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=60s --timeout=30s --retries=3 \
    CMD python -c "import httpx; import os; httpx.get(f'http://localhost:{os.getenv(\"SERVICE_PORT\", 8011)}/health')" || exit 1

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8011}"]
