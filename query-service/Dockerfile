FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import os,httpx; httpx.get('http://127.0.0.1:'+os.getenv('SERVICE_PORT','8002')+'/health',timeout=5).raise_for_status()" || exit 1

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8002}"]
