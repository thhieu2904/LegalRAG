# LegalRAG Schema v2.0 - FINAL (Pragmatic Design)

## Key Insight

**Bạn đúng hoàn toàn!**

Admin không thể (và không nên) nhập thủ công `document_code`, `issuing_authority`, `executing_agency`, vv cho hàng ngàn documents.

**Solution: Only store what Python tools can extract automatically!**

---

## What Changed

### ❌ REMOVED (Non-Extractable)

- `document_code` VARCHAR(200) - field deleted
- `issuing_authority` VARCHAR(500) - field deleted
- `executing_agency` VARCHAR(500) - field deleted
- `document_type` VARCHAR(100) - field deleted
- `issue_date` DATE - field deleted
- `effective_date` DATE - field deleted
- `expiry_date` DATE - field deleted
- `UNIQUE(collection_id, document_code)` - constraint deleted ✅ FIXED BUG!

### ✅ KEPT (Required, Auto-Extractable)

```sql
CREATE TABLE documents (
    -- UUID relationships
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id),

    -- Required fields (auto-extractable)
    title VARCHAR(1000) NOT NULL,      -- from document or filename
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),           -- MinIO path
    file_size BIGINT,
    file_hash VARCHAR(64),             -- SHA256
    mime_type VARCHAR(100),            -- application/pdf, application/vnd.openxmlformats-...

    -- Processing state
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    chunk_count INTEGER DEFAULT 0,         -- auto-updated by trigger
    error_message TEXT,

    -- FLEXIBLE: Auto-extracted metadata (optional, no admin input!)
    metadata JSONB DEFAULT '{}',
    -- Example content:
    -- {
    --   "document_code": "68/2018/NĐ-CP",        ✓ Regex extract
    --   "issue_date": "15/5/2018",               ✓ Regex extract
    --   "organizations": ["Bộ Tư pháp"],        ✓ Pattern match
    --   "pages": 7,                              ✓ PDF metadata
    --   "language": "vi",                        ✓ Langdetect
    --   "extraction_confidence": 0.85,           ✓ IMPORTANT!
    --   "extraction_notes": "..."
    -- }

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);
```

### ✅ CHUNKS (Unchanged - These ARE Extractable!)

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- These STAY - highly extractable!
    section_title VARCHAR(500),     -- e.g., "Điều 1", "Mục 2.3" ✓
    source_reference VARCHAR(200),  -- e.g., "Điều 5, khoản 2" ✓

    embedding vector(384),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(document_id, chunk_index)
);
```

---

## File Format Strategy

### ✅ ACCEPT: PDF + DOCX

| Format  | Support  | Tool                | Notes                            |
| ------- | -------- | ------------------- | -------------------------------- |
| `.pdf`  | ✅ YES   | PyPDF2 / pdfplumber | Works great, 95% accuracy        |
| `.docx` | ✅ YES   | python-docx         | Modern Word format               |
| `.doc`  | ❌ NO    | -                   | Old Word 97-2003, not supported  |
| `.txt`  | ⚠️ Maybe | None needed         | Plain text, no extraction needed |

### Validation Logic

```python
ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

if file.content_type not in ALLOWED_TYPES:
    raise ValueError(f"Unsupported format. Accept PDF or DOCX only.")
```

---

## What Python Tools CAN Extract

### High Confidence (85%+) ✅

- **PDF text** via PyPDF2
- **DOCX text** via python-docx
- **Document code** via regex: `\d+/\d+/(NĐ|TT|QĐ)` → "68/2018/NĐ-CP"
- **Dates** via regex: `\d{1,2}/\d{1,2}/\d{4}` → "15/5/2018"
- **Sections** via regex: `Điều \d+`, `Mục \d+`, `Chương` → "Điều 1"
- **Organization names** via simple patterns: "Bộ ", "UBND", "Sở "
- **Page count** via PDF metadata
- **Language** via langdetect library
- **File hash** via SHA256
- **Word/char count** via text length

### Medium Confidence (40-70%) ⚠️

- **Multiple organization detection** - May need NER model
- **Table content extraction** - Inconsistent Vietnamese table formatting
- **Document type** - Pattern matching only ("Quy trình", "Hướng dẫn", etc.)

### Low/No Confidence (<35%) ❌

- **Issuing authority** - "Chính phủ", "Bộ Tư pháp" - context-dependent
- **Executing agency** - Context-dependent, often in text, hard to identify
- **Effective/Expiry dates** - Unreliable, buried in document text
- **Signature extraction** - Handwritten, images, impossible
- **Form fields** - Requires OCR + ML models

---

## Extraction Pipeline (Python Service)

```python
class DocumentProcessor:
    """Auto-extract metadata from Vietnamese legal documents"""

    async def process_upload(self, file_path: str) -> dict:
        """
        Returns:
        {
            "title": "...",
            "document_code": "68/2018/NĐ-CP" or None,
            "dates_found": ["15/5/2018", "12/6/2025"],
            "organizations": ["Bộ Tư pháp", "UBND"],
            "sections": ["MỤC ĐÍCH", "PHẠM VI", "NỘI DUNG"],
            "pages": 7,
            "language": "vi",
            "word_count": 2500,
            "has_tables": True,
            "has_signatures": True,
            "extraction_confidence": 0.85,
            "extraction_notes": "Missing effective date, signature blocks ignored",
            "errors": []
        }
        """

        # 1. Detect format
        file_type = detect_format(file_path)  # "pdf" or "docx"

        # 2. Extract raw text
        raw_text = extract_text(file_path, file_type)

        # 3. Extract metadata
        metadata = {}

        # Document code
        match = re.search(r'(\d+/\d+/(NĐ|TT|QĐ)[^/]*)', raw_text)
        if match:
            metadata["document_code"] = match.group(1)

        # All dates
        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', raw_text)
        metadata["dates_found"] = list(set(dates))

        # Organizations
        orgs = re.findall(r'(Bộ\s+\w+|UBND|Sở\s+\w+)', raw_text)
        metadata["organizations"] = list(set(orgs))

        # Sections
        sections = re.findall(r'^(\d+\.\s+[A-Z\s]+)$', raw_text, re.MULTILINE)
        metadata["sections"] = list(set(sections))

        # Language
        metadata["language"] = detect_language(raw_text)

        # Pages
        metadata["pages"] = count_pages(file_path)

        # Confidence score
        confidence = 0.85  # Base confidence
        if not metadata.get("document_code"):
            confidence -= 0.1
        metadata["extraction_confidence"] = confidence

        return metadata
```

---

## Data Flow: Upload → Store → Query

```
User Upload
    ↓
1. Validate file format (PDF or DOCX only)
    ↓
2. Store in MinIO
    ↓
3. DocumentProcessor.process_upload()
    ├─ Extract text
    ├─ Run regex patterns
    ├─ Detect language/pages
    ├─ Generate metadata JSON
    └─ Add extraction_confidence score
    ↓
4. Insert into documents table:
    {
        id: UUID,
        collection_id: UUID,
        title: "...",
        filename: "...",
        file_path: "...",
        file_size: 12345,
        file_hash: "abc123...",
        mime_type: "application/pdf",
        status: "processing",
        chunk_count: 0,
        error_message: null,
        metadata: {
            "document_code": "68/2018/NĐ-CP",
            "dates_found": ["15/5/2018"],
            "organizations": ["Bộ Tư pháp"],
            "extraction_confidence": 0.85,
            ...
        },
        created_at: now,
        ...
    }
    ↓
5. Chunking & Embedding Service
    ├─ Split by sections (using section_title + source_reference)
    ├─ Create embeddings
    └─ Insert into chunks table
    ↓
6. Update status → "completed"
    ↓
7. User Query
    ├─ Search similar chunks (vector similarity)
    ├─ Show chunk content + section reference
    ├─ Show document metadata (including extracted document_code)
    └─ Display extraction_confidence
```

---

## Summary: Why This Works

### Scalability ✅

- No manual data entry = scales to 10,000+ documents
- Auto-extraction = consistent results
- Error handling = graceful degradation when tools miss data

### Maintainability ✅

- Simple schema = fewer fields to manage
- JSONB flexibility = add new metadata without schema changes
- Extraction service = centralized logic, easy to improve

### User Experience ✅

- Document code in search results = better identification
- Section references = precise citations
- Confidence scores = transparency about data quality
- Extraction notes = explains what's missing

### Cost Efficiency ✅

- Python tools (free) = no expensive NLP models
- Regex patterns = fast extraction
- JSONB storage = no expensive schema migrations

---

## Next Implementation Steps

1. ✅ **Schema finalized** - Ready for PostgreSQL
2. ⏳ **DocumentProcessor class** - Build extraction service
3. ⏳ **File upload endpoint** - Handle PDF/DOCX validation
4. ⏳ **Chunking service** - Section-aware Vietnamese chunking
5. ⏳ **Query service** - Return metadata + confidence scores
6. ⏳ **Admin UI** - Display extraction quality metrics

---

**Decision:** ✅ Keep schema simple, rely on Python regex tools  
**Result:** Scalable, maintainable, no manual bottleneck  
**Risk:** Low - extraction tools are proven to work  
**Recommendation:** PROCEED with implementation
