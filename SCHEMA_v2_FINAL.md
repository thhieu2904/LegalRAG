# LegalRAG Schema v2.0 - FINAL CLEANED

## Tóm Tắt Quyết Định

**Chỉ support PDF** (cơ quan gửi PDF, không cần .doc hay .docx)

---

## Documents Table - FINAL

```sql
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,

    -- Basic info
    title VARCHAR(1000) NOT NULL,

    -- File info (PDF only)
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),           -- MinIO path
    file_size BIGINT,
    file_hash VARCHAR(64),             -- SHA256
    mime_type VARCHAR(100),            -- application/pdf only

    -- Processing
    status VARCHAR(50) DEFAULT 'pending',        -- pending, processing, completed, failed
    chunk_count INTEGER DEFAULT 0,               -- auto-updated
    error_message TEXT,

    -- Auto-extracted metadata (JSONB)
    metadata JSONB DEFAULT '{}',
    -- {
    --   "document_code": "68/2018/NĐ-CP",
    --   "dates": ["15/5/2018"],
    --   "organizations": ["Bộ Tư pháp"],
    --   "sections": ["MỤC ĐÍCH", "PHẠM VI"],
    --   "pages": 7,
    --   "language": "vi",
    --   "extraction_confidence": 0.85
    -- }

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
```

---

## Chunks Table (Unchanged)

```sql
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- Section info (auto-extracted from PDF)
    section_title VARCHAR(500),        -- "Điều 1", "Mục 2.3"
    source_reference VARCHAR(200),     -- "Điều 5, khoản 2"

    embedding vector(384),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
```

---

## Upload Validation

**Only accept PDF:**

```python
ACCEPTED_MIME_TYPES = {"application/pdf"}

if file.content_type not in ACCEPTED_MIME_TYPES:
    raise ValueError(
        f"Only PDF files accepted. "
        f"Received: {file.content_type}. "
        f"Please convert your document to PDF before uploading."
    )
```

---

## What Was Removed

| Field                                         | Reason                              |
| --------------------------------------------- | ----------------------------------- |
| `issuing_authority`                           | Not extractable, needs manual input |
| `executing_agency`                            | Not extractable, needs manual input |
| `document_type`                               | Too context-dependent               |
| `issue_date`, `effective_date`, `expiry_date` | Buried in text, unreliable          |
| `UNIQUE(collection_id, document_code)`        | Fixed constraint bug                |

**→ Everything goes in `metadata JSONB` if auto-extracted**

---

## Why This Works

✅ **Simple** - Only essential fields  
✅ **Scalable** - No manual metadata entry  
✅ **Flexible** - JSONB for optional data  
✅ **Extractable** - PDF → regex tools work well  
✅ **Clean** - No .doc or .docx format hassle

---

## Status: READY ✅

Schema is finalized and ready to:

1. Create PostgreSQL database
2. Build extraction service (DocumentProcessor)
3. Implement chunking service
4. Deploy to production

---

**Last Updated:** 2025-11-14  
**Format:** PDF only  
**Extraction:** Regex-based (document_code, dates, organizations, sections)  
**Confidence:** HIGH ✅
