# LegalRAG Schema v2.0 - Chi Tiết Giải Thích

## Overview: 3 Bảng Core

### 1. **Collections** - Bộ Thủ Tục

Ví dụ:

- "quy_trinh_cap_ho_tich" → Quy trình cấp hộ tịch
- "quy_trinh_boi_thuong_nn" → Quy trình bồi thường nhà nước

Mỗi collection chứa nhiều documents (văn bản).

### 2. **Documents** - Văn Bản Pháp Luật

Ví dụ:

- "Nghị định 68/2018/NĐ-CP.pdf" → 1 document
- "Thông tư 08/2025/TT-BTP.pdf" → 1 document

**Mỗi document:**

- Thuộc đúng 1 collection
- Được split thành nhiều chunks
- Có metadata auto-extracted (không manual input!)

### 3. **Chunks** - Đoạn Text với Vector

Ví dụ:

- Chunk 0: "Điều 1. Mục đích..." → vector_embedding → similarity search
- Chunk 1: "Điều 1 (tiếp)..." → vector_embedding → similarity search

**Mỗi chunk:**

- Thuộc đúng 1 document
- Có vector embedding (384-dim)
- Có section reference (Điều, Mục, Khoản)

---

## Documents Table - Detailed

### FIELDS REQUIRED (Không Nullable)

```sql
id UUID PRIMARY KEY                    -- Unique identifier
collection_id UUID NOT NULL            -- Which collection?
title VARCHAR(1000) NOT NULL           -- Document name
filename VARCHAR(500) NOT NULL         -- Original filename
file_path VARCHAR(1000)                -- MinIO storage path
mime_type VARCHAR(100)                 -- Always "application/pdf"
status VARCHAR(50)                     -- pending / processing / completed / failed
created_at TIMESTAMP                   -- When uploaded
```

### FIELD: `metadata JSONB DEFAULT '{}'`

**Key Point: NULLABLE by design (optional, supplementary, auto-extracted)**

**What it is:**

```json
{
  "document_code": "68/2018/NĐ-CP", // ← regex extract from PDF text
  "dates": ["15/5/2018", "12/6/2025"], // ← all dates found
  "organizations": ["Bộ Tư pháp"], // ← pattern matching
  "sections": ["MỤC ĐÍCH", "PHẠM VI"], // ← document structure
  "pages": 7, // ← PDF metadata
  "language": "vi", // ← language detection
  "extraction_confidence": 0.85, // ← QUALITY SCORE (important!)
  "extraction_notes": "Missing expiry date" // ← what tools couldn't extract
}
```

**Why JSONB (not separate table)?**

- Flexible structure (not all documents have same fields)
- No schema migration when adding new extraction logic
- Can be empty {} if extraction fails
- Tools populate IF they can extract, leave empty IF they can't

**Why nullable (optional)?**

- Not every document will have all metadata
- Tool might extract `document_code` but not `organizations`
- Degradation is OK (search still works without metadata)
- Extraction quality is transparent via `extraction_confidence` score

**Example scenarios:**

```
Document 1 (good extraction):
{
  "document_code": "68/2018/NĐ-CP",
  "dates": ["15/5/2018"],
  "organizations": ["Bộ Tư pháp"],
  "extraction_confidence": 0.95
}

Document 2 (partial extraction):
{
  "document_code": "01/2015/NĐ-CP",
  "extraction_confidence": 0.70,
  "extraction_notes": "Missing organization names"
}

Document 3 (extraction failed):
{
  "extraction_confidence": 0.0,
  "extraction_notes": "Poor PDF quality, OCR failed"
}
```

### Why NO These Fields?

**Removed (Why?):**

- ❌ `issuing_authority` - needs NER model or manual input
- ❌ `executing_agency` - context-dependent, hard to extract
- ❌ `document_type` - too much variation in Vietnamese docs
- ❌ `issue_date`, `effective_date` - buried in text, unreliable
- ❌ Manual date fields - instead, extract ALL dates to `metadata.dates`

**Instead:** Everything auto-extracted goes into `metadata JSONB`

---

## Chunks Table - Detailed

### FIELDS REQUIRED (Không Nullable)

```sql
id UUID PRIMARY KEY                    -- Unique chunk ID
document_id UUID NOT NULL              -- Which document?
chunk_index INTEGER NOT NULL           -- Order (0, 1, 2, ...)
content TEXT NOT NULL                  -- Actual text to search
embedding vector(384)                  -- 384-dim vector for similarity
```

### FIELDS EXTRACTABLE (Optional but Important)

```sql
section_title VARCHAR(500)             -- "Điều 1", "Mục 2.3", "Chương III"
                                       -- ✅ Auto-extracted via regex
                                       -- ✓ Helps users understand context
                                       -- ? Can be NULL if no clear sections

source_reference VARCHAR(200)          -- "Điều 5, khoản 2, điểm a"
                                       -- ✅ Auto-extracted via regex
                                       -- ✓ For legal citation
                                       -- ? Can be NULL if ambiguous
```

**Why these are extractable:**

```
Regex pattern: \b(Điều|Mục|Chương)\s+(\d+|[IVX]+)
Example text: "Điều 5, khoản 2, điểm a quy định..."
Extract: section_title = "Điều 5"
         source_reference = "Điều 5, khoản 2, điểm a"
```

### FIELD: `metadata JSONB DEFAULT '{}'`

Chunk-level metadata (different from document metadata):

```json
{
  "page_number": 5, // Which page in PDF?
  "paragraph_index": 3, // Which paragraph?
  "confidence": 0.95, // Extraction quality
  "language": "vi", // Detected language
  "is_list_item": false // Structural info
}
```

---

## Data Flow: Upload → Extract → Chunk → Search

```
1. UPLOAD
   User uploads: "Quy_trinh_xac_dinh.pdf"
   ↓
2. CREATE DOCUMENT (required fields only)
   documents {
     id: uuid_123,
     collection_id: uuid_col,
     title: "Quy trình xác định cơ quan",
     filename: "Quy_trinh_xac_dinh.pdf",
     file_path: "s3://bucket/collections/quy-trinh/uuid_123_Quy_trinh.pdf",
     file_size: 524288,
     file_hash: "abc123...",
     mime_type: "application/pdf",
     status: "processing",  ← START HERE
     chunk_count: 0,
     metadata: {},          ← EMPTY, will be filled later
     created_at: now
   }
   ↓
3. EXTRACT METADATA (async tool runs)
   Tool reads PDF text:
     "SỞ TƯ PHÁP
      Thủ tục xác định cơ quan giải quyết bồi thường
      Mã hiệu: QT 01/BTNN
      Lần ban hành: 01
      Ngày ban hành: 01/7/2025
      ..."

   Extract:
     - document_code: "QT 01/BTNN" (via regex)
     - dates: ["01/7/2025"] (via regex)
     - organizations: ["Sở Tư pháp"] (via pattern)
     - sections: ["MỤC ĐÍCH", "PHẠM VI"] (via regex)
     - pages: 7 (PDF metadata)
     - language: "vi" (langdetect)
     - extraction_confidence: 0.82
   ↓
4. UPDATE DOCUMENT METADATA
   UPDATE documents SET
     metadata = {
       "document_code": "QT 01/BTNN",
       "dates": ["01/7/2025"],
       "organizations": ["Sở Tư pháp"],
       "sections": ["MỤC ĐÍCH", "PHẠM VI"],
       "pages": 7,
       "language": "vi",
       "extraction_confidence": 0.82
     }
   ↓
5. CREATE CHUNKS (split by sections)
   Chunk 0:
     {
       id: uuid_chunk_0,
       document_id: uuid_123,
       chunk_index: 0,
       content: "MỤC ĐÍCH. Quy định thành phần hồ sơ...",
       section_title: "MỤC ĐÍCH",
       source_reference: "MỤC ĐÍCH",
       embedding: [0.1, 0.2, 0.3, ...],  ← 384 numbers
       metadata: {"page_number": 1},
       created_at: now
     }

   Chunk 1:
     {
       chunk_index: 1,
       content: "PHẠM VI. Áp dụng đối với...",
       section_title: "PHẠM VI",
       source_reference: "PHẠM VI",
       embedding: [0.4, 0.5, 0.6, ...],
       metadata: {"page_number": 2}
     }

   (repeat for all sections)
   ↓
6. UPDATE DOCUMENT STATUS
   UPDATE documents SET
     status = "completed",  ← NOW READY FOR SEARCH
     chunk_count = 7,       ← Updated by trigger
     processed_at = now
   ↓
7. USER SEARCH
   Query: "Thủ tục nào để bồi thường?"

   A. Convert to vector (384-dim)
   B. Search similar chunks using HNSW index:
      SELECT chunk_id, content, section_title, source_reference
      FROM chunks
      WHERE document_id IN (...)
      ORDER BY embedding <=> query_vector  ← vector similarity
      LIMIT 10

   C. Show results:
      - Chunk content
      - Section title: "MỤC ĐÍCH"
      - Source reference: "MỤC ĐÍCH"
      - Confidence score (from extraction metadata)
```

---

## Summary: Why This Design Works

### ✅ Scalability (10,000+ documents)

- No manual metadata input (bottleneck eliminated)
- Auto-extraction via regex/patterns
- Metadata in JSONB (no schema migrations)

### ✅ Flexibility (handle incomplete data)

- `metadata` JSONB nullable (OK if extraction fails)
- `extraction_confidence` score (transparency)
- `extraction_notes` (explain what's missing)
- Graceful degradation (search works even without perfect extraction)

### ✅ Simplicity (fewer fields, clearer intent)

- 9 required fields (no bloat)
- 1 JSONB field (flexible)
- Clear separation: required vs optional

### ✅ Searchability (semantic + structured)

- Vector embedding for semantic search
- Section title + source_reference for structured search
- Extracted metadata for filtering/sorting

### ✅ Auditability (track everything)

- `extraction_confidence` score (show data quality)
- `extraction_notes` (show what tools missed)
- Timestamps (audit trail)
- Soft delete (preserve history)

---

## Next Steps

1. **Create PostgreSQL database** with this schema
2. **Build DocumentProcessor** class (extract metadata)
3. **Build Chunker** service (split by sections)
4. **Build Embedding service** (generate vectors)
5. **Build Query service** (search + return results)

Ready to implement? 🚀
