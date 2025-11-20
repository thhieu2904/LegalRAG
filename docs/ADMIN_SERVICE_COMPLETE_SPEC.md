# Admin Service - Complete Specification & Implementation Plan

## 📋 Overview

Admin Service là trung tâm quản lý toàn bộ dữ liệu LegalRAG system. Service này cần được hoàn thiện với đầy đủ CRUD operations cho Collections và Documents.

## 🎯 Required Features (Critical)

### 1. Collection Management

#### 1.1 Create Collection ✅ (TO IMPLEMENT)

```
POST /admin/collections
Body: {
    "name": "quy_trinh_cap_ho_tich",  // Slug (unique)
    "display_name": "Quy trình cấp hộ tịch",
    "description": "Thủ tục cấp giấy khai sinh, đăng ký kết hôn",
    "icon": "file-text",  // Optional
    "color": "#3b82f6"    // Optional
}

Response: {
    "success": true,
    "collection": {
        "id": "uuid",
        "name": "quy_trinh_cap_ho_tich",
        "display_name": "Quy trình cấp hộ tịch",
        "created_at": "ISO timestamp"
    }
}
```

**Schema Reference (schema_new.sql):**

```sql
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) UNIQUE NOT NULL,
    display_name VARCHAR(500) NOT NULL,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);
```

#### 1.2 Delete Collection ✅ (TO IMPLEMENT)

```
DELETE /admin/collections/{collection_id}

Response: {
    "success": true,
    "message": "Collection deleted (soft delete)",
    "deleted_documents": 5,  // Number of documents marked as deleted
    "deleted_chunks": 156    // Number of chunks deleted via CASCADE
}
```

**Implementation Notes:**

- **Soft delete**: Set `is_deleted = TRUE`, `deleted_at = NOW()`
- **Cascade**: PostgreSQL CASCADE will auto-delete associated documents/chunks
- **Frontend warning**: Show count of documents that will be affected

#### 1.3 List Collections ✅ (ALREADY IMPLEMENTED - NEEDS UPDATE)

Current implementation needs enhancement to match schema structure:

```sql
-- Current query uses documents table
-- Should query collections table directly:
SELECT
    id,
    name,
    display_name,
    description,
    document_count,
    total_chunks,
    is_active,
    created_at,
    updated_at
FROM collections
WHERE is_deleted = FALSE
ORDER BY updated_at DESC
```

### 2. Document Management

#### 2.1 Create Document ✅ (ALREADY IMPLEMENTED)

- **Current endpoint**: `POST /admin/process-document`
- **Status**: Working perfectly (34 chunks created successfully in test)
- **No changes needed** ✓

#### 2.2 Delete Document ✅ (TO IMPLEMENT)

```
DELETE /admin/documents/{document_id}

Response: {
    "success": true,
    "message": "Document deleted",
    "document_id": "uuid",
    "deleted_chunks": 34,  // Chunks deleted via CASCADE
    "file_deleted": true   // File removed from MinIO
}
```

**Implementation Steps:**

1. Get document info (file_path)
2. Soft delete document: `UPDATE documents SET is_deleted = TRUE, deleted_at = NOW()`
3. Chunks auto-deleted via `ON DELETE CASCADE`
4. Call Storage-Service to delete file from MinIO
5. Decrement `collections.document_count` (via trigger)

#### 2.3 List Documents ✅ (ALREADY IMPLEMENTED)

- **Current endpoint**: `GET /admin/documents`
- **Filters**: collection_id, status, pagination
- **Status**: Working ✓

#### 2.4 Get Document Detail ✅ (ALREADY IMPLEMENTED)

- **Current endpoint**: `GET /admin/documents/{document_id}`
- **Status**: Working ✓

## 🔧 Optional Features (Enhancement)

### 3. Collection Update

#### 3.1 Update Collection Name/Display

```
PATCH /admin/collections/{collection_id}
Body: {
    "display_name": "Quy trình cấp hộ tịch mới",  // Optional
    "description": "Updated description",         // Optional
    "icon": "file-check",                         // Optional
    "color": "#10b981"                            // Optional
}

Response: {
    "success": true,
    "collection": {
        "id": "uuid",
        "name": "quy_trinh_cap_ho_tich",  // Cannot change slug
        "display_name": "Quy trình cấp hộ tịch mới",
        "updated_at": "ISO timestamp"
    }
}
```

**Important**: `name` (slug) should NOT be changeable to avoid breaking references

### 4. Document Update

#### 4.1 Update Document Metadata (Title only)

```
PATCH /admin/documents/{document_id}
Body: {
    "title": "Nghị định 68/2018/NĐ-CP (Updated)"  // Only title changeable
}

Response: {
    "success": true,
    "document": {
        "id": "uuid",
        "title": "Nghị định 68/2018/NĐ-CP (Updated)",
        "updated_at": "ISO timestamp"
    }
}
```

**Implementation:**

```sql
UPDATE documents
SET title = %s, updated_at = NOW()
WHERE id = %s;
```

**Important**:

- **KHÔNG đụng chạm chunks** (chunks có `document_id` foreign key, không ảnh hưởng)
- Chỉ sửa `title` field, không sửa `filename`, `file_path`
- Metadata extraction (`metadata` JSONB) không thay đổi

#### 4.2 Replace Document (Advanced)

```
POST /admin/documents/{document_id}/replace
Body: {
    file: <new_pdf_file>,
    keep_title: true  // Optional, giữ nguyên title cũ
}

Response: {
    "success": true,
    "message": "Document replaced",
    "old_chunks_deleted": 34,
    "new_chunks_created": 42,
    "document": {...}
}
```

**Implementation Flow:**

1. Get existing document info (collection_id, title, document_id)
2. **Delete old chunks**: `DELETE FROM chunks WHERE document_id = %s` (explicit delete before cascade)
3. **Update document**: Set `status = 'processing'`, `chunk_count = 0`
4. **Delete old file**: Call Storage-Service DELETE
5. **Upload new file**: Call Storage-Service UPLOAD (same document_id)
6. **Run full pipeline**: Extract → Chunk → Embed → Insert chunks
7. **Update document**: Set `status = 'completed'`, `chunk_count = N`, new metadata

**Critical**:

- Keep same `document_id` to maintain collection relationship
- Keep same `title` if `keep_title = true`
- All chunks replaced with new content
- File replaced in MinIO with same path pattern

## 📊 Database Schema Analysis (from schema_new.sql)

### Key Tables

```sql
collections (
    id UUID PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,      -- Slug identifier
    display_name VARCHAR(500) NOT NULL,     -- Display name
    description TEXT,
    document_count INTEGER DEFAULT 0,       -- Auto-updated by trigger
    total_chunks INTEGER DEFAULT 0,         -- Could be calculated
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,       -- Soft delete
    deleted_at TIMESTAMP
)

documents (
    id UUID PRIMARY KEY,
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    title VARCHAR(1000) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'pending',   -- pending, processing, completed, failed
    chunk_count INTEGER DEFAULT 0,          -- Auto-updated by trigger
    metadata JSONB DEFAULT '{}',            -- Auto-extracted metadata
    is_deleted BOOLEAN DEFAULT FALSE,       -- Soft delete
    deleted_at TIMESTAMP
)

chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    section_title VARCHAR(500),
    source_reference VARCHAR(200),
    embedding vector(768),                  -- 768-D Vietnamese embedding
    metadata JSONB DEFAULT '{}'
)
```

### Important Relationships

1. **Collections → Documents**: `1:N` (CASCADE delete)
2. **Documents → Chunks**: `1:N` (CASCADE delete)
3. **Triggers**: Auto-update `document_count`, `chunk_count`

### Soft Delete Pattern

**Collections:**

```sql
-- Soft delete
UPDATE collections
SET is_deleted = TRUE, deleted_at = NOW(), updated_at = NOW()
WHERE id = %s;

-- List (exclude deleted)
SELECT * FROM collections WHERE is_deleted = FALSE;
```

**Documents:**

```sql
-- Soft delete
UPDATE documents
SET is_deleted = TRUE, deleted_at = NOW(), updated_at = NOW()
WHERE id = %s;

-- Chunks auto-deleted by CASCADE (hard delete)
-- File deleted from MinIO
```

## 🚀 Implementation Priority

### Phase 1: Critical Features (Must Have)

1. ✅ **Create Collection** - `POST /admin/collections`
2. ✅ **Delete Collection** - `DELETE /admin/collections/{id}`
3. ✅ **Update List Collections** - Fix `GET /admin/collections` to query collections table
4. ✅ **Delete Document** - `DELETE /admin/documents/{id}`

### Phase 2: Optional Features (Nice to Have)

5. ⭐ **Update Collection** - `PATCH /admin/collections/{id}`
6. ⭐ **Update Document Title** - `PATCH /admin/documents/{id}`
7. ⭐ **Replace Document** - `POST /admin/documents/{id}/replace`

## 🔗 Service Dependencies

### Admin Service Calls:

1. **Storage-Service**:

   - `POST /upload` - Upload file to MinIO
   - `POST /extract-text` - Extract text from PDF
   - `DELETE /files/{file_path}` - Delete file from MinIO (TO IMPLEMENT)

2. **Embedding-Service**:

   - `POST /chunk-and-embed` - Create chunks with embeddings

3. **Vector-Service**:

   - `POST /insert-batch` - Insert chunks to PostgreSQL

4. **PostgreSQL Direct**:
   - Admin has direct DB access (AICenter pattern)
   - All metadata operations via SQL

## 🎨 Frontend Requirements

### Collection Management UI

**Screens needed:**

1. **Collections List** - Display all collections with stats
2. **Create Collection Dialog** - Form with name, display_name, description
3. **Delete Collection Confirmation** - Warning about documents to be deleted
4. **Edit Collection Dialog** (Optional) - Update display_name, description

**API Calls:**

```javascript
// List
GET / admin / collections;

// Create
POST / admin / collections;
{
  name, display_name, description, icon, color;
}

// Update (optional)
PATCH / admin / collections / { id };
{
  display_name, description;
}

// Delete
DELETE / admin / collections / { id };
```

### Document Management UI

**Screens needed:**

1. **Documents List** - Filter by collection, status
2. **Upload Document** - Select collection, enter title, upload file
3. **Delete Document Confirmation** - Warning about chunks to be deleted
4. **Edit Document Title** (Optional) - Simple title update
5. **Replace Document** (Optional) - Upload new file, keep metadata

**API Calls:**

```javascript
// List
GET /admin/documents?collection_id={uuid}&status={status}

// Upload (existing)
POST /admin/process-document
FormData: { file, collection_id, title }

// Delete
DELETE /admin/documents/{id}

// Update title (optional)
PATCH /admin/documents/{id}
{ title }

// Replace (optional)
POST /admin/documents/{id}/replace
FormData: { file, keep_title }
```

## 📝 Error Handling

### Collection Errors

- `400`: Invalid UUID format
- `409`: Collection name already exists (UNIQUE constraint)
- `404`: Collection not found
- `500`: Database error

### Document Errors

- `400`: Invalid collection_id, missing file
- `404`: Document not found
- `500`: Storage service error, database error, embedding error

## 🔐 Security Considerations

1. **API Key**: All admin endpoints should require authentication
2. **Validation**: Strict input validation for UUIDs, file types
3. **Soft Delete**: Never hard delete collections (preserve audit trail)
4. **File Cleanup**: Ensure MinIO files are deleted when documents removed
5. **Transaction Safety**: Use database transactions for multi-step operations

## 📈 Monitoring & Logging

Required logs:

- Collection created/deleted
- Document uploaded/deleted
- Chunks inserted/deleted
- File operations (upload/delete)
- Pipeline errors

## 🧪 Testing Checklist

### Collection Tests

- [ ] Create collection with valid data
- [ ] Create collection with duplicate name (should fail)
- [ ] Delete collection with documents (soft delete)
- [ ] List collections (exclude deleted)
- [ ] Update collection display_name

### Document Tests

- [ ] Upload document to valid collection
- [ ] Delete document (verify chunks deleted)
- [ ] List documents with filters
- [ ] Update document title
- [ ] Replace document with new PDF

## 🔄 Migration Notes

Current code already has:

- ✅ Document upload pipeline (working)
- ✅ Metadata extraction (working)
- ✅ List documents endpoint (working)
- ✅ Get document detail endpoint (working)

Needs to be added:

- ❌ Collection CRUD endpoints (4 endpoints)
- ❌ Delete document endpoint (1 endpoint)
- ❌ Update endpoints (optional, 3 endpoints)
- ❌ Replace document endpoint (optional, 1 endpoint)

**Estimated work**: ~200 lines of code for critical features, ~300 lines for all features

## 🎯 Success Criteria

System is production-ready when:

1. ✅ Admin can create/delete collections
2. ✅ Admin can delete documents (with chunks cleanup)
3. ✅ Frontend can list collections from collections table
4. ✅ All operations properly update counters (triggers)
5. ✅ Files properly deleted from MinIO
6. ✅ Soft delete working correctly
7. ✅ No orphaned data in database
8. ✅ Proper error handling and logging
