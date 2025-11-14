# Schema Migration Guide - LegalRAG v2.0

## Tổng quan thay đổi

### Từ: Simple Structure (v1.0)

```
documents → chunks (vectors)
users
forms
```

### Sang: Hierarchical Structure (v2.0)

```
collections (bộ thủ tục)
  └─→ documents (văn bản)
        ├─→ chunks (vectors) - required
        └─→ forms (biểu mẫu) - optional
users (CCCD data)
admin_users (authentication)
query_sessions (conversation tracking)
query_logs + admin_logs + system_metrics
```

---

## Chi tiết thay đổi

### 1. **Collections** (MỚI)

Bảng mới để nhóm documents thành các bộ thủ tục

**Lý do**:

- User cần browse theo bộ thủ tục (quy trình cấp hộ tịch, bồi thường NN...)
- Dễ quản lý và phân loại documents
- Routing queries đến đúng collection

**Cấu trúc**:

```sql
collections (
    id UUID PRIMARY KEY,
    name VARCHAR(200) UNIQUE,  -- "quy_trinh_cap_ho_tich"
    display_name VARCHAR(500),  -- "Quy trình cấp hộ tịch"
    description TEXT,
    icon, color, category,
    document_count INT,  -- cached
    is_active BOOLEAN
)
```

**Ví dụ**:

```sql
INSERT INTO collections VALUES
('uuid', 'quy_trinh_cap_ho_tich', 'Quy trình cấp hộ tịch', '...', 'file-text', '#3b82f6');
```

### 2. **Documents** (CẬP NHẬT)

Thêm foreign key đến collections + metadata mở rộng

**Thay đổi chính**:

```sql
-- THÊM
collection_id UUID REFERENCES collections(id)  -- QUAN TRỌNG!
document_code VARCHAR(200)  -- "01/2015/NĐ-CP"
issuing_authority VARCHAR(500)  -- "Chính phủ"
executing_agency VARCHAR(500)  -- "Sở Tư pháp"
document_type VARCHAR(100)  -- "Nghị định"
issue_date DATE
effective_date DATE
expiry_date DATE
file_hash VARCHAR(64)  -- SHA256 để tránh trùng
mime_type VARCHAR(100)
error_message TEXT  -- Lý do failed
processed_at TIMESTAMP

-- GIỮ NGUYÊN
id, filename, file_path, file_size, status, chunk_count
created_at, updated_at, is_deleted
```

**Ràng buộc**:

- `UNIQUE(collection_id, document_code)` - không trùng mã trong cùng bộ thủ tục
- `ON DELETE CASCADE` - xóa collection → xóa toàn bộ documents

### 3. **Chunks** (CẬP NHẬT NHẸ)

Thêm metadata fields

**Thay đổi**:

```sql
-- THÊM
section_title VARCHAR(500)  -- "Điều 1", "Mục 2.3"
source_reference VARCHAR(200)  -- "Điều 5, khoản 2"
metadata JSONB

-- GIỮ NGUYÊN
id, document_id, chunk_index, content, embedding(384)
```

**Index HNSW** (QUAN TRỌNG):

```sql
CREATE INDEX idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 4. **Forms** (CẬP NHẬT)

Liên kết trực tiếp với document

**Thay đổi**:

```sql
-- THÊM
document_id UUID REFERENCES documents(id)  -- Liên kết 1:N
form_code VARCHAR(200)  -- "MẪU 01-HS"
template_path, preview_path
fields JSONB  -- Field definitions
validation_rules JSONB
instructions TEXT

-- XÓA
user_id (không còn cần ở đây)

-- GIỮ NGUYÊN
id, form_name, form_type, metadata
```

**Ràng buộc**:

- `UNIQUE(document_id, form_code)` - không trùng mã form trong document

### 5. **Admin Users** (MỚI)

Authentication cho admin

**Cấu trúc**:

```sql
admin_users (
    id UUID,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(200) UNIQUE,
    hashed_password VARCHAR(255),  -- bcrypt
    full_name, role,
    is_active, is_superuser,
    last_login, login_count
)
```

**Sử dụng**: JWT authentication cho admin operations

### 6. **Query Sessions** (MỚI)

Tracking conversations

**Cấu trúc**:

```sql
query_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_identifier, user_agent,
    conversation_turns INT,
    topics TEXT[],
    context JSONB,
    created_at, last_accessed, expires_at
)
```

### 7. **Logs & Metrics** (MỚI)

Analytics và audit trail

**Bảng mới**:

- `query_logs` - Log mọi query
- `admin_logs` - Audit trail cho admin actions
- `system_metrics` - Performance metrics

---

## Migration Steps

### Bước 1: Backup dữ liệu cũ

```bash
# Backup PostgreSQL
pg_dump -h localhost -U legalrag -d legalrag > backup_v1.sql

# Backup ChromaDB (nếu có)
cp -r data/vectordb backup_vectordb_v1/

# Backup MinIO
mc cp -r minio/legal-documents backup_minio_v1/
```

### Bước 2: Tạo database mới

```bash
# Drop database cũ (CẨN THẬN!)
psql -h localhost -U legalrag -c "DROP DATABASE IF EXISTS legalrag;"

# Tạo mới
psql -h localhost -U legalrag -c "CREATE DATABASE legalrag;"

# Chạy schema mới
psql -h localhost -U legalrag -d legalrag < schema_new.sql
```

### Bước 3: Migrate data

#### 3.1 Tạo collections từ folder structure

```python
import os
from pathlib import Path

collections_dir = Path("data/storage/collections")

for collection_folder in collections_dir.iterdir():
    if collection_folder.is_dir():
        collection_name = collection_folder.name
        display_name = collection_name.replace('_', ' ').title()

        # Insert collection
        cursor.execute("""
            INSERT INTO collections (name, display_name)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (collection_name, display_name))
```

#### 3.2 Migrate documents

```python
# Từ documents cũ → documents mới với collection_id
for old_doc in old_documents:
    # Xác định collection từ file path hoặc metadata
    collection_name = extract_collection_from_path(old_doc.file_path)

    # Lấy collection_id
    collection_id = get_collection_id(collection_name)

    # Insert document mới
    cursor.execute("""
        INSERT INTO documents
        (collection_id, title, filename, file_path, file_size, status, chunk_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (collection_id, old_doc.title, old_doc.filename, ...))
```

#### 3.3 Migrate chunks (giữ nguyên embeddings)

```python
# Chunks có thể giữ nguyên nếu document_id mapping đúng
# CHỈ cần thêm metadata fields nếu có

for old_chunk in old_chunks:
    new_document_id = document_id_mapping[old_chunk.document_id]

    cursor.execute("""
        INSERT INTO chunks
        (document_id, chunk_index, content, embedding)
        VALUES (%s, %s, %s, %s::vector)
    """, (new_document_id, old_chunk.chunk_index,
          old_chunk.content, old_chunk.embedding))
```

#### 3.4 Migrate forms

```python
# Forms cần link lại với documents
for old_form in old_forms:
    # Tìm document tương ứng
    document_id = find_document_by_form(old_form)

    cursor.execute("""
        INSERT INTO forms
        (document_id, form_name, form_type, fields)
        VALUES (%s, %s, %s, %s::jsonb)
    """, (document_id, old_form.form_name, ...))
```

### Bước 4: Rebuild vector index

```bash
# Sau khi migrate xong, rebuild HNSW index
psql -h localhost -U legalrag -d legalrag <<EOF
REINDEX INDEX idx_chunks_embedding_hnsw;
ANALYZE chunks;
EOF
```

### Bước 5: Verify migration

```sql
-- Kiểm tra số lượng
SELECT COUNT(*) FROM collections;  -- Phải > 0
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM chunks;
SELECT COUNT(*) FROM forms;

-- Kiểm tra relationships
SELECT
    c.name,
    c.document_count AS cached_count,
    COUNT(d.id) AS actual_count
FROM collections c
LEFT JOIN documents d ON c.id = d.collection_id
GROUP BY c.id, c.name, c.document_count;

-- Phải match!
```

---

## API Changes

### Trước (v1.0)

```
POST /upload → documents table
GET /documents → list all documents
POST /query → search all chunks
```

### Sau (v2.0)

```
# Collections API
GET /collections → list collections
GET /collections/{id} → collection details
GET /collections/{id}/documents → documents in collection

# Documents API
POST /collections/{id}/documents → upload to collection
GET /documents → list all (with collection info)
GET /documents/{id} → document details
DELETE /documents/{id} → delete document

# Forms API
GET /documents/{id}/forms → forms for document
POST /documents/{id}/forms → create form

# Query API
POST /query → query all collections
POST /query?collection={name} → query specific collection

# Admin API (NEW - requires authentication)
POST /admin/login → JWT token
GET /admin/metrics → system metrics
GET /admin/logs → query/admin logs
```

---

## Service Updates Needed

### 1. admin-service

```python
# CẬP NHẬT
- Thêm CollectionCRUD endpoints
- Upload phải chỉ định collection_id
- List documents có filter by collection
- Authentication middleware (JWT)

# VÍ DỤ
@router.post("/collections/{collection_id}/documents")
async def upload_document(
    collection_id: UUID,
    file: UploadFile,
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Upload to storage
    # Create document with collection_id
    # Process chunks
    ...
```

### 2. query-service

```python
# CẬP NHẬT
- Hỗ trợ collection filtering
- Join với collections trong search results

# VÍ DỤ
@router.post("/query")
async def query(request: QueryRequest):
    # Embed question
    embedding = await embed_text(request.question)

    # Search with optional collection filter
    results = await search_similar_chunks(
        embedding,
        collection_filter=request.collection_filter
    )

    # Results bao gồm collection_name
    ...
```

### 3. vector-service

```python
# CẬP NHẬT search function
@router.post("/search")
async def search(
    embedding: List[float],
    collection_id: Optional[UUID] = None,
    top_k: int = 10
):
    # SQL với JOIN collections
    query = """
        SELECT c.*, d.title, col.name as collection_name
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        JOIN collections col ON d.collection_id = col.id
        WHERE ($1::uuid IS NULL OR d.collection_id = $1)
        ORDER BY c.embedding <=> $2::vector
        LIMIT $3
    """
    results = await db.fetch(query, collection_id, embedding, top_k)
    ...
```

### 4. frontend

```typescript
// CẬP NHẬT
// 1. Collection browser
const CollectionList = () => {
    const { data: collections } = useQuery('/collections')
    return collections.map(col => (
        <CollectionCard
            name={col.display_name}
            icon={col.icon}
            documentCount={col.document_count}
            onClick={() => navigate(`/collections/${col.id}`)}
        />
    ))
}

// 2. Document list với collection context
const DocumentList = ({ collectionId }) => {
    const { data: documents } = useQuery(
        `/collections/${collectionId}/documents`
    )
    ...
}

// 3. Query với collection filter
const SearchBar = () => {
    const [selectedCollection, setSelectedCollection] = useState(null)

    const handleSearch = async (question) => {
        const result = await api.post('/query', {
            question,
            collection_filter: selectedCollection
        })
        ...
    }
}
```

---

## Testing Checklist

- [ ] Collections CRUD

  - [ ] Create collection
  - [ ] List collections
  - [ ] Update collection
  - [ ] Delete collection (cascade documents)

- [ ] Documents CRUD

  - [ ] Upload document to collection
  - [ ] List documents (all + by collection)
  - [ ] Get document details
  - [ ] Update document metadata
  - [ ] Delete document (cascade chunks)

- [ ] Vector Search

  - [ ] Search all collections
  - [ ] Search specific collection
  - [ ] Verify similarity scores
  - [ ] Check HNSW index performance

- [ ] Forms

  - [ ] Create form for document
  - [ ] List forms for document
  - [ ] Update form
  - [ ] Delete form

- [ ] Admin Functions

  - [ ] Login/authentication
  - [ ] View logs
  - [ ] View metrics
  - [ ] Audit trail

- [ ] Query Pipeline
  - [ ] Simple query
  - [ ] Query with collection filter
  - [ ] Conversation tracking (sessions)
  - [ ] Logging enabled

---

## Rollback Plan

Nếu migration thất bại:

```bash
# 1. Stop services
docker compose down

# 2. Restore database
psql -h localhost -U legalrag -c "DROP DATABASE legalrag;"
psql -h localhost -U legalrag -c "CREATE DATABASE legalrag;"
psql -h localhost -U legalrag -d legalrag < backup_v1.sql

# 3. Restore vector DB
rm -rf data/vectordb
cp -r backup_vectordb_v1 data/vectordb

# 4. Restore MinIO
mc rm -r --force minio/legal-documents
mc cp -r backup_minio_v1 minio/legal-documents

# 5. Revert code
git checkout v1.0

# 6. Restart
docker compose up
```

---

## Performance Considerations

### Indexes cần thiết

```sql
-- Collections
CREATE INDEX idx_collections_name ON collections(name);
CREATE INDEX idx_collections_active ON collections(is_active);

-- Documents
CREATE INDEX idx_documents_collection ON documents(collection_id);
CREATE INDEX idx_documents_code ON documents(document_code);
CREATE INDEX idx_documents_status ON documents(status);

-- Chunks (QUAN TRỌNG NHẤT!)
CREATE INDEX idx_chunks_embedding_hnsw ON chunks
USING hnsw (embedding vector_cosine_ops);

-- Query logs (cho analytics)
CREATE INDEX idx_query_logs_created ON query_logs(created_at);
CREATE INDEX idx_query_logs_collection ON query_logs(collection_routed);
```

### Caching strategy

- Cache collection list (rarely changes)
- Cache document counts per collection
- Cache frequently queried chunks

### Monitoring

```sql
-- Query performance
SELECT
    metric_type,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value
FROM system_metrics
WHERE metric_type = 'query_response_time'
GROUP BY metric_type;

-- Popular collections
SELECT
    collection_routed,
    COUNT(*) as query_count
FROM query_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY collection_routed
ORDER BY query_count DESC;
```

---

**Hoàn thành migration guide! Xem `schema_new.sql` và `admin-service/src/models.py` để implement.**
