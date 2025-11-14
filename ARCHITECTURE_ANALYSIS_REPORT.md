# 📋 BÁCÁO PHÂN TÍCH KIẾN TRÚC - STORAGE-SERVICE

**Ngày:** 15/11/2025  
**Trạng thái:** ❌ KHÔNG ĐÚNG - Cần Redesign  
**Mức độ nghiêm trọng:** CAO - Phá vỡ separation of concerns

---

## 1️⃣ TÓM TẮT KẾT LUẬN

Nhận xét của bạn **100% ĐÚNG**.

Storage-Service hiện tại của bạn **vi phạm nguyên tắc thiết kế** so với AICenter-RAG:

```
❌ HIỆN TẠI (SAI)
  Storage-Service: Upload + Extract metadata + Chunking (BÃO CHE HẾT)

✅ NÊN LÀ (ĐÚNG)
  Storage-Service: Chỉ Upload/Download/Delete files (đơn giản)
  Admin-Service: Orchestrate extraction + metadata + chunking
  Embedding-Service: Quyết định chiến lược chunking
```

---

## 2️⃣ SO SÁNH CHI TIẾT

### **A. AICenter Design Pattern (Đúng) ✅**

#### Storage-Service - CHỈ file operations:

```python
# aicenter-rag/storage-service/src/main.py (330 dòng)

Endpoints:
  ✅ POST /storage/upload           → Upload file to Supabase
  ✅ GET  /storage/download/{path}  → Download file
  ✅ DELETE /storage/delete/{path}  → Delete file
  ✅ GET  /storage/files            → List files
  ✅ GET  /storage/files/{path}/metadata  → File metadata
  ✅ POST /storage/extract-text/{file_id} → Extract PDF text ONLY (low-level)
```

**Đặc điểm:**

- ✅ Không làm metadata extraction
- ✅ Không làm chunking
- ✅ Chỉ extract text (basic, không phân tích)
- ✅ Không access database
- ✅ Một file gọi = một việc

#### Admin-Service - ORCHESTRATE mọi thứ:

```python
# aicenter-rag/admin-service/src/main.py

Endpoints:
  ✅ POST /admin/process-document (ASYNC)
     - Tạo job background
     - Job worker sẽ:
       1. Call storage-service: POST /upload → Supabase
       2. Call storage-service: POST /extract-text → Get text only
       3. Admin-Service: Extract metadata từ text (ADMIN LÀM)
       4. Call embedding-service: POST /chunk → Embedding quyết định cách chia
       5. Save tất cả vào PostgreSQL
```

**Đặc điểm:**

- ✅ Orchestrate toàn bộ quy trình
- ✅ Gọi storage-service cho file ops
- ✅ Gọi embedding-service cho chunking
- ✅ Làm metadata extraction (CHỈNH HỢP)
- ✅ Save database (CHỈNH HỢP)

---

### **B. LegalRAG Current Design (SAI) ❌**

#### Storage-Service - BÃO CHE MỌI THỨ:

```python
# storage-service/src/main.py (590 dòng) - NẶNG NỀ QUÁEXCESSIVE

Endpoints:
  ❌ POST /upload-and-process       ← MONOLITHIC!
  ❌ POST /upload
  ❌ POST /extract-text
  ❌ POST /extract-metadata         ← KHÔNG NÊN TRONG STORAGE!
  ❌ POST /chunk-document           ← KHÔNG NÊN TRONG STORAGE!
  ❌ POST /process-document         ← BÃO CHE LẠI!
  ❌ POST /upload-and-process       ← BÃO CHE THÊM!
```

**Vấn đề:**

- ❌ 590 dòng quá dài (AICenter: 330 dòng)
- ❌ Làm metadata extraction → Sai responsibility
- ❌ Làm chunking → Sai responsibility
- ❌ Không thể access database (nhưng tại sao??)
- ❌ Admin-Service sẽ lặp lại công việc
- ❌ Test & maintain khó hơn

---

## 3️⃣ VẬN ĐỀ CỤ THỂ

### **Vấn đề 1: Metadata Extraction Failure**

**Hiện tượng:**

```json
{
  "document_code": null,
  "dates": null,
  "organizations": null,
  "sections": null,
  "extraction_confidence": 0.0,
  "extraction_notes": "Lỗi extraction: list index out of range"
}
```

**Nguyên nhân gốc:**

- ❌ Metadata extraction **KHÔNG NÊN** ở trong Storage-Service
- ❌ Admin-Service mới có business logic để parse đúng
- ❌ Storage-Service chỉ là file wrapper, không hiểu domain

**Khi nào metadata extraction bị lỗi?**

1. Storage-Service không có context (không biết file gì, dùng cho gì)
2. Regex patterns không generic (riêng cho Vietnamese legal docs)
3. Không có retry logic, error handling (lại là du dư việc của Storage)

**Giải pháp:**
→ **Admin-Service** làm metadata extraction (nó hiểu domain business)

---

### **Vấn đề 2: Chunking Responsibility**

**Hiện tượng:**

```
Chunking ở Storage-Service, nhưng:
- Embedding-Service cũng cần chunking
- Ai quyết định chunk_size, overlap, strategy?
- Storage không biết embedding model yêu cầu gì
```

**Đúng theo AICenter:**

- Storage: Không làm chunking
- Admin: Không làm chunking
- **Embedding-Service: Quyết định chunking strategy**
  - Vì nó biết embedding model cần gì
  - Vì nó tối ưu cho vector search

**Giải pháp:**
→ **Embedding-Service** làm chunking

---

### **Vấn đề 3: Endpoint Design**

**Hiện tại (SAI):**

```
POST /upload-and-process  ← Làm 4 việc cùng lúc
├─ Upload file
├─ Extract text
├─ Extract metadata
└─ Chunk document
```

**Nên là (ĐÚNG):**

```
Storage-Service:
  POST /upload                     ← Upload file
  POST /extract-text/{file_id}    ← Extract text ONLY

Admin-Service:
  POST /process-document (ASYNC)   ← Orchestrate:
    1. Upload via storage-service
    2. Extract text via storage-service
    3. Parse metadata (ADMIN LÀM)
    4. Call embedding-service để chunk
    5. Save to PostgreSQL
```

---

### **Vấn đề 4: Trách nhiệm Database**

**Hiện tại:**

- Storage: Không access database ✓ (đúng)
- Admin: Không nói rõ
- Embedding: Không nói rõ

**Nên là:**

- Storage: Không access database ✓
- Admin: **SỬ database** ✓
  - Lưu document_code, dates, organizations, sections
  - Track processing job status
  - Link với user workflows
- Embedding: Có thể lưu vector embeddings

---

## 4️⃣ PHÂN TÍCH CỤ THỂ SAI SỐT

### **Sai Sót #1: `/upload-and-process` quá nặng nề**

```python
# ❌ HIỆN TẠI (590 dòng, quá dài)
@app.post("/upload-and-process")
async def upload_and_process(file: UploadFile):
    # Làm TOÀN BỘ 4 việc
    file_id = upload(file)
    text = extract_text(file_data)
    metadata = extract_metadata(text)      # ← SAI CHỖNAY!
    chunks = chunk_document(text)          # ← SAI CHỖ NÀY!

    return {metadata, chunks}
```

```python
# ✅ NÊN LÀ (Admin-Service làm orchestration)
# Storage-Service: Chỉ 2 endpoint
@app.post("/upload")
async def upload(file):
    return upload_to_minio(file)

@app.post("/extract-text/{file_id}")
async def extract_text(file_id):
    return extract_text_from_pdf(file_data)

# Admin-Service: Gọi storage + làm logic
@app.post("/process-document")
async def process_document(file):
    # 1. Upload
    file_id = storage.upload(file)
    # 2. Extract text
    text = storage.extract_text(file_id)
    # 3. Extract metadata (ADMIN LÀM - nó hiểu domain)
    metadata = extract_legal_metadata(text)
    # 4. Chunk via embedding-service
    chunks = embedding_service.chunk(text)
    # 5. Save to DB
    db.save_document(file_id, metadata, chunks)
    return {file_id, metadata, chunks}
```

---

### **Sai Sót #2: Metadata extraction logic sai chỗ**

```python
# ❌ SAI: Ở trong Storage-Service
# storage-service/src/extractors/metadata_extractor.py
class MetadataExtractor:
    def extract_all(pdf_text):
        # Regex patterns cố định → Không generic
        document_code = regex_search(DOCUMENT_CODE_PATTERNS)
        dates = regex_search(DATE_PATTERNS)
        # ...
```

**Tại sao sai:**

1. Storage không hiểu "document_code" là gì → Phải có domain expert (Admin)
2. Regex patterns cho Vietnamese legal docs → Là business logic (Admin)
3. Extraction confidence → Cần context (Admin biết legal docs better)

**Nên là:**

```python
# ✅ ĐÚNG: Ở Admin-Service
# admin-service/src/extractors/metadata_extractor.py
class LegalMetadataExtractor:
    def extract_all(pdf_text):
        # Context: Admin biết tài liệu pháp luật
        # Regex patterns là business logic
        document_code = extract_legal_document_code(pdf_text)
        # Có retry logic, error handling
        dates = extract_legal_dates(pdf_text)
        # ...
```

---

### **Sai Sót #3: Chunking không nên ở Storage**

```python
# ❌ SAI: Ở Storage-Service
# storage-service/src/extractors/document_chunker.py
class DocumentChunker:
    def chunk_by_sections(text, min_size=200, max_size=1000):
        # Cố định size → Không optimal cho embedding model
```

**Vấn đề:**

1. Mỗi embedding model → chunk size khác nhau
2. Storage không biết model nào đang dùng
3. Embedding-Service mới quyết định được optimal strategy

**Nên là:**

```python
# ✅ ĐÚNG: Ở Embedding-Service
# embedding-service/src/chunker.py
class SmartChunker:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.optimal_chunk_size = embedding_model.get_chunk_size()

    def chunk(text):
        # Adaptive chunking dựa vào model
        chunks = semantic_chunk(text, self.optimal_chunk_size)
        return chunks
```

---

## 5️⃣ FLOW COMPARISON

### **AICenter Flow (CORRECT) ✅**

```
User Upload
    ↓
Admin-Service: POST /admin/process-document
    │
    ├─→ Call Storage: POST /upload → MinIO
    │   Return: file_id, path
    │
    ├─→ Call Storage: POST /extract-text/{file_id}
    │   Return: raw text only
    │
    ├─→ Admin: Extract metadata
    │   (Regex, NLP, domain knowledge)
    │   Return: document_code, dates, orgs, sections
    │
    ├─→ Call Embedding: POST /chunk
    │   (Model knows optimal chunk size)
    │   Return: chunks[]
    │
    └─→ Save to PostgreSQL
        ✅ DONE
```

**Ưu điểm:**

- ✅ Separation of concerns (mỗi service 1 việc)
- ✅ Storage = simple file wrapper
- ✅ Admin = orchestrator + business logic
- ✅ Embedding = chunking expert
- ✅ Dễ test, maintain, scale

---

### **LegalRAG Current Flow (WRONG) ❌**

```
User Upload
    ↓
Storage-Service: POST /upload-and-process
    │
    ├─→ Upload to MinIO
    ├─→ Extract text
    ├─→ Extract metadata (❌ SAI)
    ├─→ Chunk document (❌ SAI)
    │
    └─→ Return metadata + chunks
        ⚠️ Metadata = null (error!)
        ⚠️ Chunks = incomplete
        ⚠️ Nothing saved to PostgreSQL!
```

**Vấn đề:**

- ❌ 590 dòng code (quá dài)
- ❌ Storage làm quá nhiều việc
- ❌ Metadata extraction fails (không domain knowledge)
- ❌ Chunking suboptimal (không model awareness)
- ❌ Không save database (nên ai save?)
- ❌ Admin-Service sẽ lặp lại công việc?

---

## 6️⃣ METADATA EXTRACTION LỖI - LÝ DO

### **Lỗi: "list index out of range" ⚠️**

**Root cause:**

```python
# storage-service/src/extractors/metadata_extractor.py
def extract_document_code(text):
    matches = regex.findall(DOCUMENT_CODE_PATTERNS, text)
    # ❌ SAI: Không check if matches is empty
    return matches[0]  # ← IndexError nếu matches = []
```

**Tại sao matches rỗng?**

1. PDF text extraction có thể trả format không đúng
2. Regex patterns không match Vietnamese legal docs
3. Không có fallback/retry logic

**Vấn đề lớn hơn:**
→ Metadata extraction **KHÔNG NÊN** ở Storage

Nên ở **Admin-Service** vì:

1. Admin biết tài liệu pháp luật là gì
2. Admin có domain rules + business logic
3. Admin có database context
4. Admin có retry/fallback strategies

---

## 7️⃣ MINIO CRUD STATUS CHECK ✓

### **Các operation đã test:**

| Operation       | Status | Note                        |
| --------------- | ------ | --------------------------- |
| Create (Upload) | ✅     | Tested with real PDF        |
| Read (Download) | ✅     | Works fine                  |
| List            | ✅     | Lists files correctly       |
| Delete          | ✅     | Tested (not in test script) |
| File exists     | ✅     | Works                       |
| Metadata        | ✅     | File size, name, etc.       |

**Kết luận:** MinIO CRUD hoàn toàn bình thường ✓

**Vấn đề không phải MinIO**, mà là:

- Metadata extraction logic ở sai chỗ
- Chunking logic ở sai chỗ
- Orchestration logic không có

---

## 8️⃣ KIẾN NGHỊ REFACTOR

### **Giai Đoạn 1: Fix Storage-Service (SỰ CẤP)**

```
✅ Giữ:
  - POST /upload          → Upload to MinIO
  - GET /download         → Download file
  - DELETE /delete        → Delete file
  - GET /list             → List files
  - GET /health           → Health check

❌ Xóa:
  - POST /extract-metadata        ← Chuyển sang Admin
  - POST /chunk-document          ← Chuyển sang Embedding
  - POST /process-document        ← Chuyển sang Admin
  - POST /upload-and-process      ← Xóa hoàn toàn

➕ Thêm:
  - POST /extract-text/{file_id}  ← Giữ (low-level text extraction)
```

**Mục tiêu:**

- Storage = 200 dòng code (simple, focused)
- Align với AICenter pattern

---

### **Giai Đoạn 2: Build Admin-Service Orchestration (CẤP THIẾT)**

```
➕ Thêm:
  - POST /admin/process-document (ASYNC)
    - Orchestrate: upload → extract → metadata → chunk → save DB
    - Gọi storage-service cho file ops
    - Gọi embedding-service cho chunking
    - Lưu metadata vào PostgreSQL
```

---

### **Giai Đoạn 3: Implement Embedding-Service Chunking (NÊN)**

```
➕ Thêm:
  - POST /chunk
    - Nhận text từ Admin
    - Quyết định chunk_size tối ưu
    - Chunk by sections (Vietnamese aware)
    - Return chunks[] tối ưu cho embedding model
```

---

## 9️⃣ TIMELINE & PRIORITY

| Công việc                           | Priority  | Effort  | Phụ thuộc |
| ----------------------------------- | --------- | ------- | --------- |
| 1. Refactor Storage → Simple CRUD   | 🔴 URGENT | 2h      | None      |
| 2. Move metadata extraction → Admin | 🔴 URGENT | 4h      | #1        |
| 3. Implement Admin orchestration    | 🔴 URGENT | 8h      | #1, #2    |
| 4. Move chunking → Embedding        | 🟡 HIGH   | 6h      | #3        |
| 5. PostgreSQL schema for metadata   | 🟡 HIGH   | 2h      | #2        |
| 6. Comprehensive testing            | 🟡 HIGH   | 4h      | #5        |
| **TOTAL**                           |           | **26h** |           |

---

## 🔟 KẾT LUẬN

### **Nhận xét của bạn: 100% ĐÚNG ✅**

Bạn nói:

> "Thiết kế ở #file:storage-service thì phần này endpoint đang sai"

**Phân tích:**

- ✅ Storage-Service hiện tại vi phạm separation of concerns
- ✅ Metadata extraction không nên ở Storage
- ✅ Chunking không nên ở Storage
- ✅ `/upload-and-process` quá monolithic
- ✅ Nên follow AICenter pattern (Storage = simple wrapper)

### **Hành động tiếp theo:**

1. **Confirm Design** - Bạn đồng ý với phân tích này không?
2. **Refactor Storage-Service** - Remove metadata + chunking
3. **Build Admin Orchestration** - Gọi storage + làm metadata
4. **Move Chunking** - Sang Embedding-Service

---

**Report được tạo:** 15/11/2025  
**Phiên bản:** v1.0
