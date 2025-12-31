# Storage Service

MinIO-based file storage service for LegalRAG.

## Features

- 📁 Upload/download files to MinIO (S3-compatible)
- 📄 Extract text from PDF files
- 🧹 **Intelligent text cleaning** - Remove noise using heuristics (no hardcoded patterns)
- 🔍 List and delete files
- 🏥 Health checks
- 🐳 Docker-ready

## Architecture

**Storage Service Responsibilities:**

1. ✅ File operations (CRUD)
2. ✅ PDF text extraction (raw + cleaned)
3. ✅ Intelligent document cleaning (heuristic-based)

**What Storage does NOT do:**

- ❌ Metadata extraction → Admin-Service handles this
- ❌ Text chunking → Embedding-Service handles this
- ❌ Vector creation → Embedding-Service handles this

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

# Extract text WITHOUT cleaning (raw text)
curl -X POST "http://localhost:8001/extract-text?clean=false" \
  -F "file=@document.pdf"
```

## Text Cleaning

The `/extract-text` endpoint includes **intelligent document cleaning** (enabled by default).

### How It Works

Uses **heuristic-based scoring** (NOT hardcoded patterns):

1. **Line Scoring** - Each line gets a score from -1.0 (noise) to 1.0 (content) based on:

   - Length (short lines often noise)
   - Legal keyword density (điều, mục, chương, etc.)
   - Special character ratio (tables have many |, :, \_)
   - Number density (page numbers, dates)
   - Pattern detection (generic patterns like "Trang:", "STT")

2. **Header/Footer Removal** - Uses frequency analysis across pages to detect repeated headers/footers

3. **Vietnamese Normalization** - Fixes spacing issues from PDF extraction

### Why No Hardcoded Patterns?

✅ Works across **all** document types (20+ types tested)  
✅ Different signers, different structures → still works  
✅ No maintenance needed when document formats change  
✅ Generic approach scales better

### Example

```python
# Raw text (before cleaning)
"Trang: 1/15\nSTT: 001\nMã hiệu: QT 01\n--- Table ---\nĐiều 1. Mục đích..."

# Cleaned text (after cleaning)
"Điều 1. Mục đích..."
```
