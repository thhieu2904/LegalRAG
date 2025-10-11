# 🎯 Architecture Analysis: Document Management Strategy

**Date**: October 11, 2025  
**Context**: NEW Requirements - Document Replacement & JSON CRUD

---

## 📋 Clarified Requirements

### **User's Goals**:

1. **Document Replacement**:

   - Thay file `.doc` cũ → file `.doc`/`.docx` mới
   - Update văn bản luật mới
   - Bỏ hoàn toàn file cũ

2. **Processing Pipeline**:

   - Upload new document
   - Tạo JSON (OCR/processing)
   - Build lại (vectorDB, embeddings)

3. **Display**:

   - **CHỈ HIỂN THỊ** nội dung file doc
   - **KHÔNG EDIT** file doc trực tiếp
   - Read-only display

4. **JSON CRUD**:
   - **EDIT** JSON processed data
   - CRUD operations on JSON
   - Update metadata, content, etc.

---

## 🔍 Architecture Comparison

### **Approach A: Complex Rendering (Current Direction)**

```
User → Admin → RAG (raw file) → Admin (render HTML) → Display
         ↓
    Mammoth/LibreOffice rendering
```

**Components**:

- ✅ Fetch raw .doc/.docx from RAG
- ✅ Render to HTML with Mammoth/LibreOffice
- ✅ Display in browser
- ❌ Complex setup (LibreOffice in Docker)
- ❌ Performance overhead (conversion)

**When to Use**:

- Need HIGH FIDELITY display
- Need to preview complex formatting
- Source document is primary reference

---

### **Approach B: JSON-First Display (RECOMMENDED)**

```
User → Admin → Display JSON content
         ↓
    JSON file already has all content!
```

**Components**:

- ✅ Read JSON file (already processed)
- ✅ Display structured data
- ✅ NO rendering needed
- ✅ Fast, simple
- ✅ Focus on CRUD

**Workflow**:

```
1. Upload .doc/.docx → Process → JSON created
2. Display: Show JSON content (not raw doc)
3. Edit: CRUD on JSON
4. Rebuild: Trigger vectorDB update
```

**When to Use**:

- Processed data is source of truth
- JSON has all extracted content
- Display = view processed data
- Primary use case: CRUD JSON

---

## 📊 Current System Analysis

### **What You ALREADY HAVE** (Questions CRUD):

```python
# admin_service/app/api/questions.py

# CREATE
POST /api/questions/collections/{collection}/documents/{doc_id}
→ Creates questions.json

# READ
GET /api/questions/collections/{collection}/documents/{doc_id}
→ Returns questions.json content

# UPDATE
PUT /api/questions/collections/{collection}/documents/{doc_id}
→ Updates questions.json via RAG Service

# DELETE
DELETE /api/questions/collections/{collection}/documents/{doc_id}
→ Deletes questions.json
```

**Pattern**:

- ✅ Admin Service calls RAG Service
- ✅ RAG Service performs file operations
- ✅ Backup before modify
- ✅ Rebuild trigger after changes

---

### **JSON File Structure**:

```json
// {doc_id}.json - Processed document content
{
  "id": "DOC_001",
  "title": "Thủ tục xác định cơ quan...",
  "content": "Full extracted text...",
  "sections": [
    {
      "title": "1. Trình tự thực hiện",
      "content": "...",
      "subsections": [...]
    }
  ],
  "metadata": {
    "effective_date": "2024-01-01",
    "code": "TTr-001",
    "executing_agency": "Sở Tư pháp"
  },
  "requirements": [...],
  "procedures": [...]
}
```

**This JSON has EVERYTHING you need to display!**

---

## 🎯 Recommended Approach

### **Strategy: JSON-First with Optional Source Preview**

#### **Core Philosophy**:

- **JSON = Source of Truth** (for display & CRUD)
- **Source .doc/.docx = Reference** (read-only, optional preview)

#### **Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│ DOCUMENT LIFECYCLE                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. UPLOAD                                                  │
│     User uploads .doc/.docx → RAG Service                   │
│     ├─ Save to: /data/storage/collections/{col}/docs/{id}/ │
│     └─ Replace old file if exists                           │
│                                                             │
│  2. PROCESS                                                 │
│     RAG Service processes document                          │
│     ├─ OCR/Extract content                                  │
│     ├─ Parse sections, metadata                             │
│     └─ Generate {doc_id}.json                               │
│                                                             │
│  3. DISPLAY (Two Options)                                   │
│     ┌─────────────────┬──────────────────────┐             │
│     │ Primary Display │ Optional Source View │             │
│     ├─────────────────┼──────────────────────┤             │
│     │ Show JSON       │ Show .doc preview    │             │
│     │ - Sections      │ - Raw document       │             │
│     │ - Metadata      │ - Read-only          │             │
│     │ - Procedures    │ - For reference      │             │
│     └─────────────────┴──────────────────────┘             │
│                                                             │
│  4. EDIT (JSON CRUD)                                        │
│     User edits processed data via Admin UI                  │
│     ├─ Update JSON content                                  │
│     ├─ Modify metadata                                      │
│     └─ Edit sections, procedures                            │
│                                                             │
│  5. REBUILD                                                 │
│     Trigger vectorDB rebuild                                │
│     ├─ Re-embed updated JSON                                │
│     └─ Update ChromaDB                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Options

### **Option 1: MINIMAL - JSON Display Only** (RECOMMENDED START)

**What to Build**:

```python
# admin_service/app/api/documents.py

@router.get("/collections/{collection}/documents/{doc_id}/content")
async def get_document_content(collection: str, doc_id: str):
    """
    Display processed document content from JSON
    (NOT from source .doc file)
    """
    # Get JSON file via RAG Service
    json_content = await rag_client.get_document_json(collection, doc_id)

    return {
        "success": True,
        "content": json_content,
        "source": "processed_json"
    }
```

**Frontend Display**:

```typescript
// Display structured JSON content
<DocumentViewer>
  <Title>{doc.title}</Title>
  <Metadata>{doc.metadata}</Metadata>
  <Sections>
    {doc.sections.map((section) => (
      <Section>{section.content}</Section>
    ))}
  </Sections>
</DocumentViewer>
```

**Pros**:

- ✅ Zero rendering complexity
- ✅ Fast (no conversion)
- ✅ Already have JSON structure
- ✅ Focus on CRUD (main goal)
- ✅ No LibreOffice needed

**Cons**:

- ❌ Can't view original formatting
- ❌ No source document preview

**Effort**: 1-2 hours (use existing JSON API)

---

### **Option 2: JSON + Simple Source Preview**

**What to Build**:

```python
# Primary: JSON display (Option 1)
GET /api/documents/{id}/content → JSON content

# Optional: Source preview (simplified)
GET /api/documents/{id}/preview/docx → Basic HTML
```

**Source Preview Options**:

**2A: Text-Only Extraction** (Simplest)

```python
from docx import Document

def extract_text_preview(file_bytes: bytes) -> str:
    """Simple text extraction for preview"""
    doc = Document(BytesIO(file_bytes))

    text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    return f"<pre>{text}</pre>"
```

**2B: Mammoth (docx only)**

```python
async def preview_source(collection: str, doc_id: str):
    # Get file bytes
    file_bytes = await rag_client.get_document_file(...)

    # Detect format
    if file_bytes[:2] == b'PK':  # .docx
        return mammoth.convert_to_html(BytesIO(file_bytes)).value
    else:  # .doc
        return extract_text_preview(file_bytes)  # Fallback to text
```

**Pros**:

- ✅ JSON display (primary)
- ✅ Source preview (reference)
- ✅ Moderate complexity
- ✅ No LibreOffice needed

**Cons**:

- ⚠️ .doc preview is text-only
- ⚠️ Two display modes

**Effort**: 3-4 hours

---

### **Option 3: JSON + Full Rendering** (Complex)

**What to Build**:

- Primary: JSON display (Option 1)
- Optional: Full rendering with LibreOffice
- Support both .doc and .docx with formatting

**Pros**:

- ✅ Complete solution
- ✅ High fidelity .doc preview

**Cons**:

- ❌ Complex setup (LibreOffice)
- ❌ Slower performance
- ❌ Overkill for "just display"

**Effort**: 6-8 hours + Docker setup

---

## 📋 JSON CRUD Implementation

### **What You Already Have**:

```python
# Questions CRUD (as reference pattern)

# CREATE
POST /api/questions/collections/{col}/documents/{id}
Body: {"main_question": "...", "question_variants": [...]}

# READ
GET /api/questions/collections/{col}/documents/{id}
Response: {"main_question": "...", "question_variants": [...]}

# UPDATE
PUT /api/questions/collections/{col}/documents/{id}
Body: {"main_question": "...", "question_variants": [...]}

# DELETE
DELETE /api/questions/collections/{col}/documents/{id}
```

### **What to Add - Document JSON CRUD**:

```python
# admin_service/app/api/documents.py

@router.get("/collections/{col}/documents/{id}/json")
async def get_document_json(col: str, id: str):
    """Get processed document JSON"""
    return await rag_client.get_document_json(col, id)

@router.put("/collections/{col}/documents/{id}/json")
async def update_document_json(col: str, id: str, data: dict):
    """
    Update document JSON
    - Edit sections
    - Update metadata
    - Modify procedures
    """
    # Validate data structure
    validate_document_json(data)

    # Update via RAG Service
    result = await rag_client.update_document_json(col, id, data)

    # Trigger rebuild
    if result["success"]:
        await rag_client.trigger_rebuild(scope="document", doc_id=id)

    return result
```

**RAG Service**:

```python
# rag_service/app/api/internal_documents.py

@router.put("/internal/documents/collections/{col}/documents/{id}/json")
async def update_document_json(col: str, id: str, data: dict):
    """Update JSON file with backup"""

    json_path = get_document_json_path(col, id)

    # Backup existing file
    backup_path = create_backup(json_path)

    # Write new content
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "file_path": str(json_path),
        "backup_path": str(backup_path)
    }
```

**Effort**: 2-3 hours (reuse questions CRUD pattern)

---

## 🚀 FINAL RECOMMENDATION

### **Phase 1: MINIMAL (Ship Fast)** ⭐

**Build**:

1. ✅ **JSON Display** - Show processed content (NOT source doc)
2. ✅ **JSON CRUD** - Edit metadata, sections, procedures
3. ✅ **Rebuild Trigger** - Update vectorDB after changes

**Skip** (for now):

- ❌ Source document rendering
- ❌ LibreOffice setup
- ❌ Complex .doc handling

**Why**:

- Your goal: "Chỉ hiển thị nội dung file doc lên thôi"
- JSON ALREADY HAS all content from doc!
- Focus on CRUD (main requirement)
- Can add source preview later if needed

**Timeline**: 1-2 days

---

### **Phase 2: OPTIONAL - Add Source Preview** (If Needed)

**Build**:

1. ✅ Text-only preview for .doc
2. ✅ Mammoth rendering for .docx
3. ✅ "View Source" button in UI

**When**:

- Users request to see original formatting
- Need to verify OCR accuracy
- Legal compliance requires source viewing

**Timeline**: +1 day

---

## 📊 Decision Matrix

| Requirement     | Option 1: JSON Only | Option 2: JSON + Preview | Option 3: Full Render |
| --------------- | ------------------- | ------------------------ | --------------------- |
| Display content | ✅ JSON             | ✅ JSON + Text           | ✅ JSON + Full HTML   |
| CRUD operations | ✅                  | ✅                       | ✅                    |
| .doc support    | N/A                 | ⚠️ Text only             | ✅ Full               |
| .docx support   | N/A                 | ✅ Full                  | ✅ Full               |
| Complexity      | ⭐ Low              | ⭐⭐ Medium              | ⭐⭐⭐⭐ High         |
| Performance     | ⭐⭐⭐ Fast         | ⭐⭐ Good                | ⭐ Slow               |
| Setup           | Simple              | Moderate                 | Complex               |
| Time            | 1-2 days            | 3-4 days                 | 6-8 days              |

---

## ✅ Recommended Action Plan

### **NOW - Phase 1**:

```bash
# 1. Build JSON Display Endpoint
GET /api/collections/{col}/documents/{id}/content
→ Return processed JSON

# 2. Build JSON CRUD
PUT /api/collections/{col}/documents/{id}/json
→ Update document JSON

# 3. Trigger Rebuild
POST /api/rebuild
→ Re-embed after JSON changes
```

**Focus**: CRUD on JSON (your main goal)  
**Skip**: Complex rendering (not needed)  
**Result**: Working system in 1-2 days

---

### **LATER - Phase 2** (If Users Request):

```bash
# Add optional source preview
GET /api/collections/{col}/documents/{id}/preview/source
→ Simple text extraction for .doc
→ Mammoth for .docx
```

**Only if**: Users need to see original formatting  
**Effort**: +1 day

---

## 🎯 Conclusion

**YOUR USE CASE**:

- ✅ Replace documents (upload workflow)
- ✅ Display content (from JSON)
- ✅ CRUD JSON (edit processed data)
- ✅ Rebuild vectorDB

**BEST APPROACH**: **JSON-First Display**

**Why**:

1. JSON already has all content
2. No rendering complexity
3. Focus on CRUD (main requirement)
4. Fast to implement
5. Can add source preview later

**NOT RECOMMENDED**: Complex .doc rendering (overkill)

---

**Next Step**: Implement JSON display + CRUD endpoints?
