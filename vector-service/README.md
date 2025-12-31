# Vector-Service - LegalRAG PostgreSQL Vector Storage

Vector-Service quản lý PostgreSQL pgvector storage cho LegalRAG, hỗ trợ CRUD operations và semantic similarity search với Vietnamese embeddings (768-D).

## ✅ Adaptation Complete (v2.0 - LegalRAG Compatible)

### Changes from Original (AiCenter-style)

- **Embedding Dimension**: 384-D → **768-D** (Vietnamese model)
- **Table**: `vector_chunks` → **`chunks`** (match schema_new.sql)
- **Delete Logic**: Soft delete (is_deleted flag) → **Hard delete** (CASCADE)
- **New Fields**: Added `section_title`, `source_reference`, `token_count`
- **Search Results**: Now include section fields + metadata

## 🏗️ Architecture

```
Admin-Service → Embedding-Service (768-D chunks) → Vector-Service → PostgreSQL pgvector
                                                                      ↓
                                                                   chunks table
                                                                   (HNSW index)
```

## 📊 Database Schema

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    section_title VARCHAR(500),      -- "Điều 1", "Mục 2.3"
    source_reference VARCHAR(200),   -- "Điều 1, khoản 1"
    embedding vector(768),           -- Vietnamese model
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- HNSW index for fast similarity search
CREATE INDEX idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## 🚀 API Endpoints

### 1. Health Check

```bash
GET /health
GET /

Response:
{
  "status": "healthy",
  "db": "connected",
  "pgvector": "available"
}
```

### 2. Insert Single Vector

```bash
POST /insert

Body:
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "chunk_index": 0,
  "content": "Điều 1. Phạm vi điều chỉnh...",
  "section_title": "Điều 1",
  "source_reference": "Điều 1",
  "embedding": [0.123, 0.456, ...],  // 768-dimensional
  "token_count": 150,
  "metadata": {
    "page_number": 5,
    "confidence": 0.95
  }
}

Response:
{
  "success": true,
  "vector_id": "chunk-uuid",
  "message": "Vector inserted successfully"
}
```

### 3. Insert Batch Vectors

```bash
POST /insert-batch

Body:
{
  "vectors": [
    {
      "document_id": "doc-uuid",
      "chunk_index": 0,
      "content": "...",
      "section_title": "Điều 1",
      "source_reference": "Điều 1",
      "embedding": [...],  // 768-dimensional
      "token_count": 150,
      "metadata": {}
    },
    ...
  ]
}

Response:
{
  "success": true,
  "inserted": 45,
  "failed": 0,
  "total": 45
}
```

### 4. Semantic Similarity Search

```bash
POST /search

Body:
{
  "embedding": [0.123, 0.456, ...],  // 768-dimensional query vector
  "top_k": 10,
  "threshold": 0.7,
  "document_ids": ["doc-uuid-1", "doc-uuid-2"]  // Optional filter
}

Response:
{
  "results": [
    {
      "vector_id": "chunk-uuid",
      "document_id": "doc-uuid",
      "chunk_index": 0,
      "content": "Điều 1. Phạm vi điều chỉnh...",
      "section_title": "Điều 1",
      "source_reference": "Điều 1",
      "similarity": 0.92,
      "metadata": {
        "page_number": 5
      }
    },
    ...
  ],
  "total": 10
}
```

### 5. Delete Vectors by Document ID

```bash
POST /delete

Body:
{
  "document_ids": ["doc-uuid-1", "doc-uuid-2"]
}

Response:
{
  "success": true,
  "deleted": 45,
  "message": "Deleted 45 vectors"
}
```

### 6. Count Vectors

```bash
GET /count
GET /count?document_id=doc-uuid

Response:
{
  "total": 1234
}
```

## 🧪 Quick Test

### Setup Database

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=legalrag \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Create schema
sleep 5
docker exec -i postgres-pgvector psql -U postgres -d legalrag < migrations/schema.sql
```

### Run Service

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalrag
EMBEDDING_DIMENSION=768
API_KEY=test-api-key
EOF

# Start service
python src/main.py
```

### Test Insert & Search

```python
import requests
import numpy as np

BASE_URL = "http://localhost:8003"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key"
}

# Generate test embedding (768-dimensional)
test_embedding = np.random.rand(768).tolist()

# Insert
response = requests.post(
    f"{BASE_URL}/insert",
    headers=headers,
    json={
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "content": "Điều 1. Test content...",
        "section_title": "Điều 1",
        "source_reference": "Điều 1",
        "embedding": test_embedding,
        "token_count": 50,
        "metadata": {"page_number": 1}
    }
)
print("Insert:", response.json())

# Search
response = requests.post(
    f"{BASE_URL}/search",
    headers=headers,
    json={
        "embedding": test_embedding,
        "top_k": 5,
        "threshold": 0.5
    }
)
print("Search:", response.json())
```

## 🔗 Integration with LegalRAG Pipeline

### Admin-Service → Vector-Service Flow

```python
# In admin-service job_processor.py STEP 5

# Get embeddings from embedding-service
embedding_response = requests.post(
    "http://embedding-service:8004/chunk-and-embed",
    json={"text": cleaned_text}
)

chunks = embedding_response.json()["chunks"]

# Build vectors for vector-service
vectors = []
for chunk in chunks:
    vectors.append({
        "document_id": document_id,
        "chunk_index": chunk["index"],
        "content": chunk["content"],
        "section_title": chunk.get("section_title"),  # From embedding-service
        "source_reference": chunk.get("source_reference"),  # From embedding-service
        "embedding": chunk["embedding"],  # 768-dimensional
        "token_count": chunk.get("token_count"),
        "metadata": {
            "collection_id": collection_id,
            "document_title": title,
            "filename": filename,
            "page_number": chunk.get("page_number")
        }
    })

# Insert batch to vector-service
response = requests.post(
    "http://vector-service:8003/insert-batch",
    headers={"X-API-Key": os.getenv("VECTOR_SERVICE_API_KEY")},
    json={"vectors": vectors}
)
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/dbname
EMBEDDING_DIMENSION=768  # Vietnamese model dimension

# Optional
API_KEY=your-secret-api-key  # For authentication
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## 📝 Next Steps

1. ✅ Vector-Service adapted for LegalRAG (768-D, section fields, hard delete)
2. ⏳ Test with PostgreSQL pgvector (setup + insert + search)
3. ⏳ Update Admin-Service STEP 5 to call vector-service with full metadata
4. ⏳ Update Embedding-Service to extract section_title, source_reference
5. ⏳ Full integration test (Upload → Extract → Chunk → Embed → Vector-Service)

## 🐛 Troubleshooting

**"vector dimension mismatch"**

- Check EMBEDDING_DIMENSION in .env matches model output (should be 768)
- Verify embedding-service uses `dangvantuan/vietnamese-document-embedding`

**"relation chunks does not exist"**

- Run migrations: `docker exec -i postgres-pgvector psql -U postgres -d legalrag < migrations/schema.sql`

**Slow search performance**

- Verify HNSW index created: `\d chunks` in psql
- Consider tuning m/ef_construction based on dataset size

## 📚 References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Vietnamese Embedding Model](https://huggingface.co/dangvantuan/vietnamese-document-embedding)
