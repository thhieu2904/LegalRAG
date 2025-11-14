# LegalRAG Schema Verification & Document Processing Strategy

## 1. Schema Field Verification

### Documents Table - Fields Analysis

| Field                      | Current          | Status | Necessity | Reason                                             |
| -------------------------- | ---------------- | ------ | --------- | -------------------------------------------------- |
| `id`                       | ✅ UUID          | KEEP   | ⭐⭐⭐    | Primary key                                        |
| `collection_id`            | ✅ UUID FK       | KEEP   | ⭐⭐⭐    | Essential for grouping                             |
| `document_code`            | ❌ REMOVED       | ?      | ⭐⭐⭐    | e.g., "01/2015/NĐ-CP" - identify document uniquely |
| `title`                    | ✅ VARCHAR(1000) | KEEP   | ⭐⭐⭐    | Document name                                      |
| `issuing_authority`        | ❌ REMOVED       | ?      | ⭐⭐      | "Chính phủ", "Bộ Tư Pháp" - important metadata     |
| `executing_agency`         | ❌ REMOVED       | ?      | ⭐        | "Sở Tư pháp" - administrative info                 |
| `document_type`            | ❌ REMOVED       | ?      | ⭐⭐      | "Nghị định", "Thông tư" - classification           |
| `issue_date`               | ❌ REMOVED       | ?      | ⭐⭐      | Ngày ban hành - temporal validity                  |
| `effective_date`           | ❌ REMOVED       | ?      | ⭐⭐⭐    | Ngày hiệu lực - when document applies              |
| `expiry_date`              | ❌ REMOVED       | ?      | ⭐        | Ngày hết hiệu lực - relevance filter               |
| `filename`                 | ✅ VARCHAR(500)  | KEEP   | ⭐⭐⭐    | File name                                          |
| `file_path`                | ✅ VARCHAR(1000) | KEEP   | ⭐⭐⭐    | Storage path in MinIO                              |
| `file_size`                | ✅ BIGINT        | KEEP   | ⭐        | For monitoring                                     |
| `file_hash`                | ✅ VARCHAR(64)   | KEEP   | ⭐⭐      | SHA256 for deduplication                           |
| `mime_type`                | ✅ VARCHAR(100)  | KEEP   | ⭐⭐      | File type indicator                                |
| `status`                   | ✅ VARCHAR(50)   | KEEP   | ⭐⭐⭐    | pending, processing, completed, failed             |
| `chunk_count`              | ✅ INT           | KEEP   | ⭐⭐      | Cached for perf                                    |
| `error_message`            | ✅ TEXT          | KEEP   | ⭐⭐      | Debug info                                         |
| `metadata`                 | ✅ JSONB         | KEEP   | ⭐⭐⭐    | Flexible storage                                   |
| `created_at`, `updated_at` | ✅               | KEEP   | ⭐⭐      | Audit trail                                        |
| `processed_at`             | ✅ TIMESTAMP     | KEEP   | ⭐        | When fully processed                               |
| `is_deleted`               | ✅ BOOLEAN       | KEEP   | ⭐⭐⭐    | Soft delete                                        |

**⚠️ Recommendation**:

- **RESTORE** `document_code`, `effective_date`, `document_type` → Essential for legal docs
- **CONSIDER MOVING** to `metadata` JSONB: `issuing_authority`, `executing_agency`, `issue_date`, `expiry_date`
- This way: strict columns stay normalized, flexible data in JSONB

---

### Chunks Table - Fields Analysis

| Field              | Current         | Status | Necessity | Reason                        |
| ------------------ | --------------- | ------ | --------- | ----------------------------- |
| `id`               | ✅ UUID         | KEEP   | ⭐⭐⭐    | Primary key                   |
| `document_id`      | ✅ UUID FK      | KEEP   | ⭐⭐⭐    | Which document                |
| `chunk_index`      | ✅ INT          | KEEP   | ⭐⭐⭐    | Order preservation            |
| `content`          | ✅ TEXT         | KEEP   | ⭐⭐⭐    | Actual text                   |
| `section_title`    | ✅ VARCHAR(500) | KEEP   | ⭐⭐      | e.g., "Điều 1", "Mục 2.3"     |
| `source_reference` | ✅ VARCHAR(200) | KEEP   | ⭐⭐      | e.g., "Điều 5, khoản 2"       |
| `embedding`        | ✅ vector(384)  | KEEP   | ⭐⭐⭐    | For similarity search         |
| `metadata`         | ✅ JSONB        | KEEP   | ⭐⭐      | Page number, confidence, etc. |
| `created_at`       | ✅ TIMESTAMP    | KEEP   | ⭐        | For audit                     |

**Status**: ✅ Chunks table looks good!

---

## 2. Document File Format Analysis

Vietnamese legal documents có đặc thù:

- **PDF**: Phổ biến nhất, nhưng khó extract text (layout, signatures, tables)
- **DOCX**: Dễ extract, structure preserved, nhưng bước lưu trữ phức tạp hơn
- **TXT/RTF**: Đơn giản nhưng mất formatting

### Comparison

| Aspect                         | PDF      | DOCX       | Hybrid (PDF + DOCX) |
| ------------------------------ | -------- | ---------- | ------------------- |
| **Text Extraction**            | ⚠️ Khó   | ✅ Dễ      | ✅ Dùng cả hai      |
| **Structure Preservation**     | ⚠️ Mất   | ✅ Giữ     | ✅ Tốt nhất         |
| **Tables/Signature Detection** | ❌ Khó   | ✅ Dễ      | ✅ Tốt nhất         |
| **Section Detection**          | ⚠️ Khó   | ✅ Dễ      | ✅ Tốt nhất         |
| **Storage Size**               | ✅ Nhỏ   | ⚠️ Lớn hơn | ⚠️ Cần cả hai       |
| **Legal Standard**             | ✅ Chuẩn | ⚠️ Ít dùng | ✅ Tốt nhất         |

### 🎯 Recommendation: **Hybrid Approach**

**Accept both PDF and DOCX, process differently:**

```
PDF → pdfplumber/pypdf → tables, text, sections
DOCX → python-docx → paragraphs, styles, structure
```

**Schema Update Needed:**

```sql
-- In documents table, add:
original_format VARCHAR(20),  -- 'pdf', 'docx', 'txt'
processed_formats JSONB,       -- {"pdf_text": "...", "docx_structure": {...}}
structure_metadata JSONB,      -- sections, paragraphs, tables info
```

---

## 3. Vietnamese Legal Document Structure

### Typical Structure (Very Inconsistent!)

```
┌─────────────────────────────┐
│  HEADER (ministry, etc.)    │  ← Usually sparse/optional
├─────────────────────────────┤
│  DOCUMENT CODE              │  ← e.g., "01/2015/NĐ-CP"
│  TITLE                      │  ← e.g., "NGHỊ ĐỊNH"
├─────────────────────────────┤
│  METADATA (Issue, Effective)│  ← Sometimes present, sometimes not
│  Issuing Authority          │
│  Executing Agency           │
├─────────────────────────────┤
│  BODY TEXT                  │
│  ├─ Điều 1                  │  ← Section (sometimes)
│  ├─ Khoản 1                 │  ← Subsection (sometimes)
│  ├─ Điểm a, b, c            │  ← Points (sometimes)
│  └─ Text content            │
│                             │
│  Signature Block (✍️)        │  ← Handwritten, hard to read
│  ├─ Name                    │
│  ├─ Title                   │
│  ├─ Date                    │
│  └─ Signature               │
│                             │
│  TABLES (Law content)       │  ← Very common, complex structure
│  APPENDICES                 │  ← Sometimes attached
└─────────────────────────────┘

⚠️ PROBLEMS:
- No consistent section numbering
- Some docs have "Điều" (articles), some don't
- Tables with embedded text
- Multiple columns/complex layouts
- Handwritten signatures (unusable for text)
- Language switches (Vietnamese + English)
```

---

## 4. Processing Strategy

### Phase 1: Document Upload & Format Detection

```
Input: PDF/DOCX file
  ↓
1. Validate file size (< 50MB)
2. Detect format (PDF → pdfplumber, DOCX → python-docx)
3. Store original file in MinIO
4. Extract metadata:
   - Title, pages, encoding
   - Detected language (Vietnamese, English, mixed)
5. Store processing_stage = "metadata_extracted"
```

### Phase 2: Structure Analysis & Cleaning

```
For PDF:
  1. Extract text + layout info using pdfplumber
  2. Detect sections:
     - Look for patterns: "Điều \d+", "Mục \d+", "Chương"
     - Extract section titles
  3. Detect & separate:
     - Signature blocks (remove)
     - Tables (mark as table, extract content)
     - Lists/numbered items
  4. Output: structured_content = {sections, tables, paragraphs}

For DOCX:
  1. Iterate through paragraphs
  2. Detect style (heading, normal, table)
  3. Preserve hierarchy:
     - Level 1: Chapters
     - Level 2: Articles/Sections
     - Level 3: Subsections
  4. Output: structured_content = {hierarchy, styles, tables}
```

### Phase 3: Intelligent Chunking

```
Current: Just split by CHUNK_SIZE (800 chars)
Better:
  1. Use structure from Phase 2
  2. Chunk by sections when possible
  3. For tables: treat each row/cell as context
  4. For long sections: split but preserve section reference

Example:
  Content: "Điều 1. Phạm vi áp dụng..."
  Chunks:
    - chunk_0: "Điều 1. Phạm vi áp dụng. 1. Luật này quy định..."
    - chunk_1: "Điều 1 (continued). 2. Bao gồm..."

  Metadata:
    - section_title: "Điều 1"
    - source_reference: "Điều 1, khoản 1"
    - is_table: false
    - section_level: 1
```

### Phase 4: Storage & Indexing

```
Store in chunks:
  ✅ content (TEXT) - actual text to index
  ✅ section_title - "Điều 1"
  ✅ source_reference - "Điều 1, khoản 2, điểm a"
  ✅ embedding - vector
  ✅ metadata (JSONB):
     {
       "page_number": 5,
       "document_code": "01/2015/NĐ-CP",
       "section_level": 1,
       "section_type": "article",  // "article", "subsection", "item", "table"
       "is_table": false,
       "confidence": 0.95,
       "language": "vi"
     }
```

---

## 5. Recommended Schema Updates

### Documents Table (FINAL)

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id),

    -- ESSENTIAL FIELDS
    title VARCHAR(1000) NOT NULL,
    document_code VARCHAR(200),  -- "01/2015/NĐ-CP" (RESTORE THIS!)

    -- FILE INFO
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    mime_type VARCHAR(100),
    original_format VARCHAR(20),  -- 'pdf', 'docx'

    -- PROCESSING STATUS
    status VARCHAR(50) DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    processing_stage VARCHAR(50),  -- metadata_extracted, structure_analyzed, chunked

    -- METADATA (Flexible - can be extended)
    metadata JSONB DEFAULT '{}',  -- Contains:
    -- {
    --   "effective_date": "2015-01-01",
    --   "expiry_date": null,
    --   "document_type": "Nghị định",
    --   "issuing_authority": "Chính phủ",
    --   "executing_agency": "Sở Tư pháp",
    --   "pages": 15,
    --   "language": "vi",
    --   "has_tables": true,
    --   "has_signatures": true
    -- }

    structure_metadata JSONB DEFAULT '{}',  -- Contains:
    -- {
    --   "sections": [
    --     {"title": "Điều 1", "start_page": 1, "end_page": 2},
    --     {"title": "Điều 2", "start_page": 2, "end_page": 3}
    --   ],
    --   "tables": [{...}],
    --   "paragraphs_count": 45
    -- }

    -- TIMESTAMPS
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    -- SOFT DELETE
    is_deleted BOOLEAN DEFAULT FALSE,

    UNIQUE(collection_id, document_code)
);
```

### Chunks Table (FINAL)

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- CHUNK IDENTITY
    chunk_index INTEGER NOT NULL,

    -- CONTENT
    content TEXT NOT NULL,
    section_title VARCHAR(500),  -- "Điều 1", "Mục 2.3"
    source_reference VARCHAR(200),  -- "Điều 5, khoản 2, điểm a"

    -- VECTOR
    embedding vector(384),

    -- METADATA
    metadata JSONB DEFAULT '{}',  -- Contains:
    -- {
    --   "page_number": 5,
    --   "document_code": "01/2015/NĐ-CP",
    --   "section_level": 1,  // 1=Article, 2=Subsection, 3=Item
    --   "section_type": "article",  // article, subsection, item, table, appendix
    --   "is_table": false,
    --   "confidence": 0.95,
    --   "language": "vi",
    --   "word_count": 250
    -- }

    -- TIMESTAMPS
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(document_id, chunk_index)
);
```

---

## 6. Implementation Plan

### Step 1: Update Schema ✅

- Restore `document_code` to documents
- Move temporal fields to metadata JSONB
- Add `original_format`, `processing_stage`, `structure_metadata`

### Step 2: Create Format Detectors

```python
class DocumentProcessor:
    async def detect_format(self, file: UploadFile) -> str:
        """Detect 'pdf' or 'docx'"""

    async def extract_metadata(self, file_path: str, format: str) -> dict:
        """Extract: title, pages, language, structure indicators"""

    async def extract_structure(self, file_path: str, format: str) -> dict:
        """Extract: sections, tables, paragraphs"""
```

### Step 3: Implement Intelligent Chunking

```python
class IntelligentChunker:
    async def chunk_by_structure(self, content: dict, max_size: int) -> list:
        """Chunk respecting document structure"""
        # 1. Split by sections first
        # 2. If section > max_size, split further
        # 3. Preserve source_reference

    async def detect_sections(self, text: str) -> list:
        """Find "Điều X", "Mục X", "Chương X" patterns"""

    async def mark_special_content(self, chunk: str) -> dict:
        """Identify: signatures, tables, lists"""
```

### Step 4: Test Pipeline

```bash
1. Upload sample PDF (law document)
2. Verify metadata extraction
3. Check structure detection
4. Validate chunking
5. Verify embeddings
```

---

## 7. Critical Questions for You

1. **Document Collection** 📄

   - Bạn có sample Vietnamese legal documents để test không?
   - Mostly PDF? DOCX? Mixed?

2. **Signature Blocks** ✍️

   - Nên xóa toàn bộ signature blocks không?
   - Hay giữ metadata (người ký, chức vụ)?

3. **Tables** 📊

   - Bảng luật (e.g., fee tables) là quan trọng không?
   - Extract từng row riêng biệt hay giữ nguyên?

4. **Sections Consistency** 🔢

   - Documents của bạn có consistent section numbering không?
   - Hay rất rối (some have "Điều", some don't)?

5. **Processing Performance** ⏱️
   - Bạn accept slow processing (detailed structure analysis) không?
   - Hay prefer fast processing (simple chunking)?

---

## Summary

| What               | Current            | Recommendation           | Status                |
| ------------------ | ------------------ | ------------------------ | --------------------- |
| **Schema**         | Missing key fields | Restore + JSONB hybrid   | ⏳ Ready to implement |
| **File Formats**   | Single format?     | Support PDF + DOCX       | ⏳ Need library setup |
| **Chunking**       | Simple split       | Structure-aware          | ⏳ Need logic         |
| **Extraction**     | Unknown            | pdfplumber + python-docx | ⏳ Ready to code      |
| **Error Handling** | Unknown            | Graceful degradation     | ⏳ Need planning      |

**Next Step**: Bạn confirm những câu hỏi trên, mình sẽ implement chi tiết! 🚀
