# Admin Service - API Testing Guide

## 📋 Service Information

**Base URL**: `http://localhost:8001`  
**Version**: 3.0.0  
**Description**: Complete document and collection management with CRUD operations

## 🔑 All Available Endpoints

### Health Check

- `GET /health` - Service health status

### Collection Management

- `GET /admin/collections` - List all collections
- `POST /admin/collections` - Create new collection
- `PATCH /admin/collections/{id}` - Update collection metadata
- `DELETE /admin/collections/{id}` - Delete collection (soft delete)

### Document Management

- `GET /admin/documents` - List documents with filters
- `GET /admin/documents/{id}` - Get document details
- `POST /admin/process-document` - Upload and process new document
- `PATCH /admin/documents/{id}` - Update document title
- `DELETE /admin/documents/{id}` - Delete document
- `POST /admin/documents/{id}/replace` - Replace document with new file

## 🧪 PowerShell Test Commands

### 1. Create Collection

```powershell
# Create "Quy trình cấp hộ tịch" collection
$body = @{
    name = "quy_trinh_cap_ho_tich"
    display_name = "Quy trình cấp hộ tịch"
    description = "Thủ tục cấp giấy khai sinh, đăng ký kết hôn"
    icon = "file-text"
    color = "#3b82f6"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/admin/collections" -Method POST -Body $body -ContentType "application/json"
```

**Expected Response:**

```json
{
  "success": true,
  "collection": {
    "id": "uuid-string",
    "name": "quy_trinh_cap_ho_tich",
    "display_name": "Quy trình cấp hộ tịch",
    "description": "Thủ tục cấp giấy khai sinh, đăng ký kết hôn",
    "icon": "file-text",
    "color": "#3b82f6",
    "created_at": "2025-11-20T12:00:00"
  }
}
```

### 2. List Collections

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/admin/collections" -Method GET
```

**Expected Response:**

```json
{
  "success": true,
  "collections": [
    {
      "id": "uuid",
      "name": "quy_trinh_cap_ho_tich",
      "display_name": "Quy trình cấp hộ tịch",
      "description": "...",
      "icon": "file-text",
      "color": "#3b82f6",
      "document_count": 0,
      "total_chunks": 0,
      "is_active": true,
      "created_at": "2025-11-20T12:00:00",
      "updated_at": "2025-11-20T12:00:00"
    }
  ]
}
```

### 3. Update Collection

```powershell
# Update display name and description
$collectionId = "your-collection-uuid-here"
$body = @{
    display_name = "Quy trình cấp hộ tịch (Updated)"
    description = "Updated description"
    color = "#10b981"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/admin/collections/$collectionId" -Method PATCH -Body $body -ContentType "application/json"
```

**Expected Response:**

```json
{
  "success": true,
  "collection": {
    "id": "uuid",
    "name": "quy_trinh_cap_ho_tich",
    "display_name": "Quy trình cấp hộ tịch (Updated)",
    "description": "Updated description",
    "icon": "file-text",
    "color": "#10b981",
    "updated_at": "2025-11-20T12:05:00"
  }
}
```

### 4. Upload Document

```powershell
# Upload PDF document to collection
$collectionId = "your-collection-uuid-here"
$filePath = "D:\Documents\sample.pdf"

$form = @{
    file = Get-Item -Path $filePath
    collection_id = $collectionId
    title = "Nghị định 68/2018/NĐ-CP"
}

Invoke-RestMethod -Uri "http://localhost:8001/admin/process-document" -Method POST -Form $form
```

**Expected Response:**

```json
{
  "success": true,
  "file_id": "document-uuid",
  "file_path": "collections/quy_trinh_cap_ho_tich/uuid_sample.pdf",
  "file_size": 123456,
  "text": "extracted text...",
  "text_stats": {
    "pages": 15,
    "characters": 45000,
    "words": 5000
  },
  "metadata": {
    "document_code": "68/2018/NĐ-CP",
    "dates": ["15/5/2018"],
    "organizations": ["Bộ Tư pháp"],
    "sections": ["Điều 1", "Điều 2"],
    "extraction_confidence": 0.75
  },
  "message": "Successfully processed sample.pdf - 34 chunks inserted"
}
```

### 5. List Documents

```powershell
# List all documents
Invoke-RestMethod -Uri "http://localhost:8001/admin/documents" -Method GET

# Filter by collection
$collectionId = "your-collection-uuid"
Invoke-RestMethod -Uri "http://localhost:8001/admin/documents?collection_id=$collectionId" -Method GET

# Filter by status
Invoke-RestMethod -Uri "http://localhost:8001/admin/documents?status=completed" -Method GET

# Pagination
Invoke-RestMethod -Uri "http://localhost:8001/admin/documents?limit=10&offset=0" -Method GET
```

**Expected Response:**

```json
{
    "success": true,
    "total": 5,
    "limit": 100,
    "offset": 0,
    "documents": [
        {
            "id": "uuid",
            "collection_id": "collection-uuid",
            "title": "Nghị định 68/2018/NĐ-CP",
            "filename": "sample.pdf",
            "file_size": 123456,
            "status": "completed",
            "chunk_count": 34,
            "metadata": {...},
            "created_at": "2025-11-20T12:00:00",
            "processed_at": "2025-11-20T12:02:00"
        }
    ]
}
```

### 6. Get Document Detail

```powershell
$documentId = "your-document-uuid"
Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId" -Method GET
```

**Expected Response:**

```json
{
    "success": true,
    "document": {
        "id": "uuid",
        "collection_id": "collection-uuid",
        "title": "Nghị định 68/2018/NĐ-CP",
        "filename": "sample.pdf",
        "file_path": "collections/.../sample.pdf",
        "file_size": 123456,
        "status": "completed",
        "chunk_count": 34,
        "actual_chunks": 34,
        "metadata": {...},
        "created_at": "2025-11-20T12:00:00",
        "processed_at": "2025-11-20T12:02:00",
        "updated_at": "2025-11-20T12:02:00"
    }
}
```

### 7. Update Document Title

```powershell
$documentId = "your-document-uuid"
$body = @{
    title = "Nghị định 68/2018/NĐ-CP (Phiên bản cập nhật)"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId" -Method PATCH -Body $body -ContentType "application/json"
```

**Expected Response:**

```json
{
  "success": true,
  "document": {
    "id": "uuid",
    "title": "Nghị định 68/2018/NĐ-CP (Phiên bản cập nhật)",
    "updated_at": "2025-11-20T12:10:00"
  }
}
```

### 8. Delete Document

```powershell
$documentId = "your-document-uuid"
Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId" -Method DELETE
```

**Expected Response:**

```json
{
  "success": true,
  "message": "Document 'Nghị định 68/2018/NĐ-CP' deleted",
  "document_id": "uuid",
  "deleted_chunks": 34,
  "file_deleted": true,
  "file_path": "collections/.../sample.pdf"
}
```

### 9. Replace Document

```powershell
# Replace document with new PDF
$documentId = "your-document-uuid"
$newFilePath = "D:\Documents\updated.pdf"

$form = @{
    file = Get-Item -Path $newFilePath
    keep_title = "true"  # Keep existing title
}

Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId/replace" -Method POST -Form $form
```

**Expected Response:**

```json
{
  "success": true,
  "message": "Document replaced successfully",
  "document_id": "uuid",
  "old_chunks_deleted": 34,
  "new_chunks_created": 42,
  "document": {
    "id": "uuid",
    "title": "Nghị định 68/2018/NĐ-CP",
    "chunk_count": 42,
    "updated_at": "2025-11-20T12:15:00"
  }
}
```

### 10. Delete Collection

```powershell
# ⚠️ WARNING: This will soft delete the collection and all documents
$collectionId = "your-collection-uuid"
Invoke-RestMethod -Uri "http://localhost:8001/admin/collections/$collectionId" -Method DELETE
```

**Expected Response:**

```json
{
  "success": true,
  "message": "Collection 'Quy trình cấp hộ tịch' deleted (soft delete)",
  "collection_id": "uuid",
  "deleted_documents": 5,
  "deleted_chunks_estimate": 156
}
```

## 📊 Complete Workflow Test

### Full End-to-End Test

```powershell
# 1. Create collection
$createCollection = @{
    name = "test_collection"
    display_name = "Test Collection"
    description = "Test collection for API testing"
} | ConvertTo-Json

$collection = Invoke-RestMethod -Uri "http://localhost:8001/admin/collections" -Method POST -Body $createCollection -ContentType "application/json"
$collectionId = $collection.collection.id

Write-Host "✅ Created collection: $collectionId"

# 2. Upload document
$form = @{
    file = Get-Item -Path "D:\Personal\LegalRAG\test.pdf"
    collection_id = $collectionId
    title = "Test Document"
}

$upload = Invoke-RestMethod -Uri "http://localhost:8001/admin/process-document" -Method POST -Form $form
$documentId = $upload.file_id

Write-Host "✅ Uploaded document: $documentId ($($upload.text_stats.pages) pages, $($upload.metadata.chunk_count) chunks)"

# 3. Verify document
$doc = Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId" -Method GET
Write-Host "✅ Document verified: $($doc.document.title) - Status: $($doc.document.status)"

# 4. Update document title
$updateTitle = @{
    title = "Test Document (Updated)"
} | ConvertTo-Json

$updated = Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId" -Method PATCH -Body $updateTitle -ContentType "application/json"
Write-Host "✅ Updated document title: $($updated.document.title)"

# 5. List documents in collection
$docs = Invoke-RestMethod -Uri "http://localhost:8001/admin/documents?collection_id=$collectionId" -Method GET
Write-Host "✅ Collection has $($docs.total) documents"

# 6. Delete document
$deleted = Invoke-RestMethod -Uri "http://localhost:8001/admin/documents/$documentId" -Method DELETE
Write-Host "✅ Deleted document: $($deleted.deleted_chunks) chunks removed"

# 7. Delete collection
$deletedCol = Invoke-RestMethod -Uri "http://localhost:8001/admin/collections/$collectionId" -Method DELETE
Write-Host "✅ Deleted collection: $($deletedCol.deleted_documents) documents removed"

Write-Host "`n🎉 All tests passed!"
```

## 🔍 Error Handling

### Common Error Responses

**400 Bad Request:**

```json
{
  "detail": "Invalid collection_id (must be UUID)"
}
```

**404 Not Found:**

```json
{
  "detail": "Collection not found"
}
```

**409 Conflict:**

```json
{
  "detail": "Collection with name 'quy_trinh_cap_ho_tich' already exists"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Database insert failed: ..."
}
```

## 📝 Database Verification

### Check Collections in PostgreSQL

```sql
-- List all collections
SELECT id, name, display_name, document_count, is_deleted
FROM collections
ORDER BY created_at DESC;

-- Get collection with documents
SELECT
    c.id,
    c.name,
    c.display_name,
    c.document_count,
    COUNT(d.id) as actual_documents
FROM collections c
LEFT JOIN documents d ON c.id = d.collection_id AND d.is_deleted = FALSE
WHERE c.is_deleted = FALSE
GROUP BY c.id, c.name, c.display_name, c.document_count;
```

### Check Documents

```sql
-- List documents with chunk count
SELECT
    d.id,
    d.title,
    d.status,
    d.chunk_count,
    COUNT(ch.id) as actual_chunks
FROM documents d
LEFT JOIN chunks ch ON d.id = ch.document_id
WHERE d.is_deleted = FALSE
GROUP BY d.id, d.title, d.status, d.chunk_count;
```

## 🎯 Testing Checklist

- [ ] Create collection with valid data
- [ ] Create collection with duplicate name (should fail 409)
- [ ] List collections (should show all active collections)
- [ ] Update collection display_name
- [ ] Upload document to collection (full pipeline test)
- [ ] List documents in collection
- [ ] Get document detail
- [ ] Update document title
- [ ] Delete document (verify chunks deleted)
- [ ] Replace document with new PDF
- [ ] Delete collection (verify cascade delete)
- [ ] Verify soft delete (deleted items not in list)
- [ ] Check database consistency (document_count matches)

## 🚀 Production Deployment Notes

### Required Environment Variables

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legalrag
POSTGRES_USER=legalrag
POSTGRES_PASSWORD=legalrag_password

# Service URLs
STORAGE_SERVICE_URL=http://storage-service:8010
EMBEDDING_SERVICE_URL=http://embedding-service:8011
VECTOR_SERVICE_URL=http://vector-service:8012

# Admin API Key (for embedding service)
ADMIN_API_KEY=admin-secret-key-change-in-production

# Service Port
SERVICE_PORT=8001
```

### Security Recommendations

1. **Add Authentication**: Implement JWT or API key authentication for all admin endpoints
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Input Validation**: Strict validation for all user inputs
4. **CORS**: Configure CORS properly for production frontend
5. **Logging**: Implement comprehensive audit logging
6. **File Size Limits**: Enforce maximum file upload size
7. **Database Transactions**: Ensure atomic operations for complex workflows

## 📚 Integration with Frontend

### Required API Calls for UI

**Collection Management Page:**

1. Load collections: `GET /admin/collections`
2. Create collection: `POST /admin/collections`
3. Update collection: `PATCH /admin/collections/{id}`
4. Delete collection: `DELETE /admin/collections/{id}`

**Document Management Page:**

1. Load collections (dropdown): `GET /admin/collections`
2. Load documents: `GET /admin/documents?collection_id={id}`
3. Upload document: `POST /admin/process-document` (FormData)
4. Get document detail: `GET /admin/documents/{id}`
5. Update title: `PATCH /admin/documents/{id}`
6. Delete document: `DELETE /admin/documents/{id}`
7. Replace document: `POST /admin/documents/{id}/replace` (FormData)

### Sample Frontend Integration (JavaScript)

```javascript
// Create collection
async function createCollection(name, displayName, description) {
  const response = await fetch("http://localhost:8001/admin/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, display_name: displayName, description }),
  });
  return await response.json();
}

// Upload document
async function uploadDocument(collectionId, title, file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("collection_id", collectionId);
  formData.append("title", title);

  const response = await fetch("http://localhost:8001/admin/process-document", {
    method: "POST",
    body: formData,
  });
  return await response.json();
}

// Delete document
async function deleteDocument(documentId) {
  const response = await fetch(
    `http://localhost:8001/admin/documents/${documentId}`,
    {
      method: "DELETE",
    }
  );
  return await response.json();
}
```

## 🔗 Related Documentation

- [Admin Service Complete Spec](./ADMIN_SERVICE_COMPLETE_SPEC.md)
- [Schema Documentation](../schema_new.sql)
- [Architecture Overview](./ARCHITECTURE.md)
