# Storage Service v2.0 - Enhanced Document Processing

## Overview

Storage Service now handles **3 core functions**:

1. **MinIO File Management** - Upload, download, list, delete files
2. **PDF Text Extraction** - Extract text from PDF files
3. **Metadata Extraction** - Vietnamese legal document metadata (document_code, dates, organizations, sections)
4. **Document Chunking** - Split documents into semantic chunks by sections
5. **Full Processing** - Extract + Chunk in single call

## Architecture

```
Upload PDF
    ↓
[PDFExtractor] → Extract text (PyPDF2)
    ↓
[MetadataExtractor] → Extract structured data (regex + pattern matching)
    ├─ document_code: "68/2018/NĐ-CP"
    ├─ dates: ["15/5/2018"]
    ├─ organizations: ["Bộ Tư pháp"]
    ├─ sections: ["Điều 1", "Mục 2.3"]
    └─ extraction_confidence: 0.85 (quality score)
    ↓
[DocumentChunker] → Split into semantic chunks
    ├─ chunk_index: 0, 1, 2, ...
    ├─ content: "text chunk"
    ├─ section_title: "Điều 1"
    └─ source_reference: "Chương I > Mục 1 > Điều 1"
    ↓
Ready for Embedding Service
```

## API Endpoints

### File Management

**POST /upload** - Upload file to MinIO

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "document_id=uuid-here"
```

**GET /download** - Download file from MinIO

```bash
curl -X GET "http://localhost:8000/download?file_path=documents/uuid/file.pdf"
```

**GET /list** - List files in bucket

```bash
curl -X GET "http://localhost:8000/list?prefix=documents/"
```

**DELETE /delete** - Delete file from MinIO

```bash
curl -X DELETE "http://localhost:8000/delete?file_path=documents/uuid/file.pdf"
```

### Text Extraction

**POST /extract-text** - Extract text from PDF

```bash
curl -X POST http://localhost:8000/extract-text \
  -F "file=@document.pdf"
```

Response:

```json
{
  "success": true,
  "text": "Văn bản pháp luật...",
  "pages": 7,
  "metadata": {
    "producer": "PyPDF2",
    "creation_date": "..."
  }
}
```

### Metadata Extraction

**POST /extract-metadata** - Extract Vietnamese legal metadata

```bash
curl -X POST http://localhost:8000/extract-metadata \
  -F "file=@document.pdf" \
  -F "document_id=uuid-here"
```

Response:

```json
{
  "success": true,
  "document_id": "uuid-here",
  "metadata": {
    "document_code": "68/2018/NĐ-CP",
    "dates": ["15/5/2018", "12/6/2025"],
    "organizations": ["Bộ Tư pháp", "UBND TP HCM"],
    "sections": ["MỤC ĐÍCH", "PHẠM VI", "Điều 1", "Mục 2.3"],
    "pages": 7,
    "language": "vi",
    "word_count": 2500,
    "has_tables": true,
    "has_signatures": true,
    "extraction_confidence": 0.85,
    "extraction_notes": "Thiếu ngày hiệu lực"
  },
  "extraction_time_ms": 250
}
```

### Document Chunking

**POST /chunk-document** - Split into semantic chunks

```bash
curl -X POST http://localhost:8000/chunk-document \
  -F "file=@document.pdf" \
  -F "document_id=uuid-here" \
  -F "min_chunk_size=200" \
  -F "max_chunk_size=1000"
```

Response:

```json
{
  "success": true,
  "document_id": "uuid-here",
  "total_chunks": 15,
  "chunks": [
    {
      "chunk_index": 0,
      "content": "MỤC ĐÍCH...",
      "section_title": "MỤC ĐÍCH",
      "source_reference": "MỤC ĐÍCH",
      "metadata": {}
    },
    {
      "chunk_index": 1,
      "content": "Điều 1. Về phạm vi áp dụng...",
      "section_title": "Điều 1",
      "source_reference": "Chương I > Mục 1 > Điều 1",
      "metadata": {}
    }
  ],
  "chunking_time_ms": 120
}
```

### Full Processing

**POST /process-document** - Extract metadata + chunk in one call

```bash
curl -X POST http://localhost:8000/process-document \
  -F "file=@document.pdf" \
  -F "document_id=uuid-here"
```

Response:

```json
{
  "success": true,
  "document_id": "uuid-here",
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
  "processing_time_ms": 350
}
```

## Metadata Extraction Details

### Extraction Patterns

**Document Code** (2 patterns):

- `68/2018/NĐ-CP` → regex: `\d+/\d+/[NĐQTC]{1,3}-[\w\-]+`
- `Số: 68/2018/NĐ-CP` → regex: `(?:Số|Decision No\.?)\s*[\:\=]?\s*(\d+/\d+/[A-Za-z\-]+)`

**Dates** (3 patterns):

- `15/5/2018` → regex: `\d{1,2}/\d{1,2}/\d{4}`
- `15-05-2018` → regex: `\d{1,2}-\d{1,2}-\d{4}`
- `15 tháng 5 năm 2018` → regex: `\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}`

**Organizations** (6 patterns):

- `Bộ Tư pháp` → regex: `Bộ\s+[\w\s]+`
- `UBND TP HCM` → regex: `UBND\s+[\w\s]+`
- `Sở Nội vụ` → regex: `Sở\s+[\w\s]+`
- `Cục Đất đai` → regex: `Cục\s+[\w\s]+`
- `Vụ Pháp chế` → regex: `Vụ\s+[\w\s]+`
- `Hội Đông Quản lý` → regex: `Hội\s+[\w\s]+`

**Sections** (6 patterns):

- `Điều 1`, `Điều I` → regex: `Điều\s+[\dIVXivx\-]+`
- `Mục 2.3` → regex: `Mục\s+[\d\.]+`
- `Chương III` → regex: `Chương\s+[\dIVXivx]+`
- `Phần II` → regex: `Phần\s+[\dIVXivx]+`
- `Khoản 1` → regex: `Khoản\s+[\d]+`
- `Điểm a` → regex: `Điểm\s+[a-z]`

### Confidence Score Calculation

```
4 fields extracted → 1.00 (perfect)
3 fields extracted → 0.85 (good)
2 fields extracted → 0.65 (okay)
1 field extracted  → 0.40 (poor)
0 fields extracted → 0.10 (minimal)

Fields: document_code, dates, organizations, sections
```

## Document Chunking

### Strategy: Section-based chunking

1. **Identify section headers** (Chương, Mục, Điều, Khoản, Điểm)
2. **Group content** under each section
3. **Track section hierarchy** for source_reference
4. **Split if too large** (> max_chunk_size)
5. **Preserve order** with chunk_index

### Example

Input:

```
Chương I. TÓM TẮT VỀ QUY TRÌNH

Mục 1. Quy trình cấp hộ tích

Điều 1. Về phạm vi áp dụng
Quy trình này áp dụng cho...

Khoản 1. Các điều kiện bắt buộc
...

Mục 2. Quy trình xác nhận

Điều 2. Về phạm vi
...
```

Output:

```
Chunk 0:
- section_title: "Chương I"
- source_reference: "Chương I"
- content: "TÓM TẮT VỀ QUY TRÌNH..."

Chunk 1:
- section_title: "Mục 1"
- source_reference: "Chương I > Mục 1"
- content: "Quy trình cấp hộ tích..."

Chunk 2:
- section_title: "Điều 1"
- source_reference: "Chương I > Mục 1 > Điều 1"
- content: "Về phạm vi áp dụng...\nQuy trình này áp dụng cho..."

Chunk 3:
- section_title: "Khoản 1"
- source_reference: "Chương I > Mục 1 > Điều 1 > Khoản 1"
- content: "Các điều kiện bắt buộc..."

Chunk 4:
- section_title: "Mục 2"
- source_reference: "Chương I > Mục 2"
- content: "Quy trình xác nhận..."

Chunk 5:
- section_title: "Điều 2"
- source_reference: "Chương I > Mục 2 > Điều 2"
- content: "Về phạm vi..."
```

## Configuration

In `.env`:

```env
# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=legal-documents

# Service
SERVICE_PORT=8000
MAX_FILE_SIZE=50000000  # 50MB

# Allowed file types
ALLOWED_CONTENT_TYPES=application/pdf
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python -m src.main
# Or with Docker
docker build -t storage-service .
docker run -p 8000:8000 storage-service
```

## Dependencies

- **fastapi** - Web framework
- **minio** - S3-compatible storage client
- **PyPDF2** - PDF text extraction
- **pydantic** - Data validation
- **langdetect** - Language detection (future)

## Next Steps

1. **Embedding Service** - Generate 384-dim vectors for chunks
2. **Query Service** - Semantic search using vectors
3. **Admin Service** - Document management UI
4. **Integration** - Connect to admin-service file upload endpoint

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Full processing pipeline
curl -X POST http://localhost:8000/process-document \
  -F "file=@test_document.pdf" \
  -F "document_id=test-doc-123"

# Interactive API docs
http://localhost:8000/docs
```
