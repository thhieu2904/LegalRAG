# Storage Service

MinIO-based file storage service for LegalRAG.

## Features

- 📁 Upload/download files to MinIO (S3-compatible)
- 📄 Extract text from PDF files
- 🔍 List and delete files
- 🏥 Health checks
- 🐳 Docker-ready

## API Endpoints

- `POST /upload` - Upload file
- `GET /download` - Download file
- `GET /list` - List files
- `DELETE /delete` - Delete file
- `POST /extract-text` - Extract text from PDF
- `GET /health` - Health check
- `GET /docs` - FastAPI documentation

## Configuration

Create `.env` file with:

```env
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=legal-documents
```

## Running

```bash
# With Docker Compose
docker compose up storage-service

# Locally
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001
```

## Testing

```bash
# Health check
curl http://localhost:8001/health

# Upload file
curl -X POST http://localhost:8001/upload \
  -F "file=@document.pdf" \
  -F "document_id=uuid"

# Download file
curl http://localhost:8001/download?file_path=documents/uuid/document.pdf > output.pdf

# Extract text
curl -X POST http://localhost:8001/extract-text \
  -F "file=@document.pdf"
```
