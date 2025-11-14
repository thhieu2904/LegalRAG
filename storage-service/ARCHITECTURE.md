# Storage Service v2.0 - Recommended Architecture

## Overview

Storage Service handles **file management + document processing** (extract metadata + chunk).

**This is the recommended design because:**

- ✅ Clear separation: File ops + extraction logic in one service
- ✅ Can be scaled independently
- ✅ Admin-Service doesn't need to know MinIO details
- ✅ Follows industry standards (AWS Lambda, Google Cloud Functions pattern)

---

## Architecture

```
┌─────────────────────────────────────┐
│ Admin-Service (Orchestrator)        │
├─────────────────────────────────────┤
│ • API endpoints                     │
│ • Document CRUD                     │
│ • Call Storage-Service              │
│ • Call Embedding-Service            │
│ • Manage database                   │
└────────────┬────────────────────────┘
             │
             ↓ (Sync: upload + process)
┌─────────────────────────────────────┐
│ Storage-Service (File + Extract)    │
├─────────────────────────────────────┤
│ • MinIO operations (file storage)   │
│ • PDF text extraction               │
│ • Metadata extraction (regex)       │
│ • Document chunking (sections)      │
│ • Return: file_id + metadata + chunks
└────────────┬────────────────────────┘
             │
             ├─→ MinIO (store file)
             │
             └─→ Return results
```

---

## API Endpoints

### Recommended: Upload + Process

**POST /upload-and-process** - Upload file to MinIO + Extract + Chunk

```bash
curl -X POST http://localhost:8000/upload-and-process \
  -F "file=@document.pdf"
```

Response:

```json
{
  "success": true,
  "file_id": "uuid-here",
  "file_path": "documents/uuid/document.pdf",
  "file_size": 102400,
  "metadata": {
    "document_code": "68/2018/NĐ-CP",
    "dates": ["15/5/2018"],
    "organizations": ["Bộ Tư pháp"],
    "sections": ["Điều 1"],
    "extraction_confidence": 0.85
  },
  "chunks": [
    {
      "chunk_index": 0,
      "content": "...",
      "section_title": "Điều 1",
      "source_reference": "Điều 1"
    }
  ],
  "total_chunks": 15,
  "processing_time_ms": 1250
}
```

### File Operations

**POST /upload** - Upload only (no processing)

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "document_id=uuid-here"
```

**GET /download** - Download file from MinIO

```bash
curl -X GET "http://localhost:8000/download?file_path=documents/uuid/file.pdf"
```

**GET /list** - List files

```bash
curl -X GET "http://localhost:8000/list?prefix=documents/"
```

**DELETE /delete** - Delete file

```bash
curl -X DELETE "http://localhost:8000/delete?file_path=documents/uuid/file.pdf"
```

---

## Using Storage Client (Admin-Service)

### Sync Version

```python
from storage_service.src.client import StorageClient

storage = StorageClient(base_url="http://storage-service:8000")

# Upload file and process
result = storage.upload_and_process(
    file_path="/path/to/document.pdf",
    file_name="document.pdf"
)

# Returns:
# {
#   'file_id': 'uuid',
#   'metadata': {...},
#   'chunks': [...],
#   'total_chunks': 15
# }

file_id = result['file_id']
metadata = result['metadata']
chunks = result['chunks']

# Save to database
db.documents.insert({
    'id': uuid.uuid4(),
    'file_id': file_id,
    'metadata': metadata,
    'chunk_count': len(chunks),
})

for chunk_data in chunks:
    db.chunks.insert({
        'document_id': ...,
        'chunk_index': chunk_data['chunk_index'],
        'content': chunk_data['content'],
        'section_title': chunk_data['section_title'],
        'source_reference': chunk_data['source_reference'],
    })
```

### Async Version (FastAPI)

```python
from storage_service.src.client import AsyncStorageClient

@router.post("/upload")
async def upload_document(file: UploadFile, collection_id: str):
    storage = AsyncStorageClient()

    # Upload and process
    result = await storage.upload_and_process(
        file_content=await file.read(),
        file_name=file.filename
    )

    # Save to database
    # ... same as above

    return result
```

---

## Processing Pipeline

### Flow Diagram

```
1. FE uploads PDF
   ↓
2. Admin-Service receives upload
   ├─ Call Storage-Service /upload-and-process
   │  (send file)
   │
3. Storage-Service processes
   ├─ Upload to MinIO
   ├─ Extract text (PyPDF2)
   ├─ Extract metadata (regex patterns)
   ├─ Chunk by sections
   └─ Return: {file_id, metadata, chunks}

4. Admin-Service receives results
   ├─ Save document + metadata to DB
   ├─ Save chunks to DB
   └─ Return file_id to FE

5. (Later) Call Embedding-Service
   ├─ Get chunks from DB
   ├─ Generate vectors
   └─ Save vectors to DB
```

### Timing

```
File upload size: 100 KB
Processing time: ~1-2 seconds

File upload size: 1 MB
Processing time: ~5-10 seconds

File upload size: 10 MB
Processing time: ~30-50 seconds
```

If files are large, consider making extraction **async**:

```python
# Async version
task = celery_app.send_task('process_document', args=[file_id])
return {'file_id': file_id, 'status': 'processing', 'task_id': task.id}
```

---

## Metadata Extraction Details

### What Gets Extracted

| Field                 | Pattern            | Example             | Success Rate |
| --------------------- | ------------------ | ------------------- | ------------ |
| document_code         | Regex              | "68/2018/NĐ-CP"     | 90%          |
| dates                 | Regex (3 patterns) | "15/5/2018"         | 85%          |
| organizations         | Regex (6 patterns) | "Bộ Tư pháp"        | 75%          |
| sections              | Regex (6 patterns) | "Điều 1", "Mục 2.3" | 80%          |
| pages                 | PDF metadata       | 7                   | 100%         |
| language              | Detection          | "vi"                | 95%          |
| word_count            | Text length        | 2500                | 100%         |
| extraction_confidence | Calculation        | 0.85                | -            |

### Confidence Score

```
4 fields found → 1.00 (perfect)
3 fields found → 0.85 (good)
2 fields found → 0.65 (okay)
1 field found  → 0.40 (poor)
0 fields found → 0.10 (minimal)
```

---

## Document Chunking

### Strategy: Section-based

Splits document by Vietnamese legal structure:

- **Chương** (Chapter) - Level 1
- **Mục** (Section) - Level 2
- **Điều** (Article) - Level 3
- **Khoản** (Paragraph) - Level 4
- **Điểm** (Point) - Level 5

### Example Output

```
Chunk 0:
├─ section_title: "Chương I"
├─ source_reference: "Chương I"
└─ content: "TÓM TẮT..."

Chunk 1:
├─ section_title: "Mục 1"
├─ source_reference: "Chương I > Mục 1"
└─ content: "Quy trình cấp hộ tích..."

Chunk 2:
├─ section_title: "Điều 1"
├─ source_reference: "Chương I > Mục 1 > Điều 1"
└─ content: "Về phạm vi áp dụng..."
```

---

## Configuration

`.env`:

```env
# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents
MINIO_SECURE=false

# Service
SERVICE_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# File handling
MAX_FILE_SIZE=50000000  # 50MB
ALLOWED_CONTENT_TYPES=application/pdf
```

---

## Docker Compose

```yaml
services:
  storage-service:
    build: ./storage-service
    ports:
      - "8000:8000"
    environment:
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
      DATABASE_URL: postgresql://...
    depends_on:
      - minio
    volumes:
      - ./storage-service:/app
```

---

## Integration with Admin-Service

### In admin-service

```python
# admin_service/config.py
STORAGE_SERVICE_URL = os.getenv('STORAGE_SERVICE_URL', 'http://storage-service:8000')

# admin_service/clients/__init__.py
from storage_service.src.client import StorageClient

def get_storage_client():
    return StorageClient(base_url=STORAGE_SERVICE_URL)

# admin_service/api/documents.py
from ..clients import get_storage_client

@router.post("/documents/upload")
async def upload_document(file: UploadFile, collection_id: str):
    storage = get_storage_client()
    result = storage.upload_and_process(...)
    # ... save to DB
```

---

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Full pipeline
curl -X POST http://localhost:8000/upload-and-process \
  -F "file=@sample.pdf"

# Interactive API
http://localhost:8000/docs
```

---

## Why This Architecture

| Aspect              | Benefit                               |
| ------------------- | ------------------------------------- |
| **Responsibility**  | Storage = file + extract (one job)    |
| **Scalability**     | Can scale Storage independently       |
| **Abstraction**     | Admin doesn't know MinIO details      |
| **Reusability**     | Other services can use Storage client |
| **Clarity**         | Clear data flow                       |
| **Testability**     | Easy to mock Storage-Service          |
| **Maintainability** | Low coupling between services         |

---

## Next Steps

1. ✅ Storage-Service: File + extraction
2. Admin-Service: API + database + orchestration
3. Embedding-Service: Vector generation
4. Query-Service: Semantic search
5. Integration testing

**Ready to build!** 🚀
