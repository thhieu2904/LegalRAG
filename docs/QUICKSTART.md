"""
LegalRAG Microservices - Quick Start Guide
============================================

This guide helps you get the entire system running and test all services.
"""

## Prerequisites

- Docker & Docker Compose
- curl or Postman (for testing)
- 12GB+ RAM (4GB for services, 8GB for GPU LLM model)
- GPU (NVIDIA) for llm-service (optional, CPU fallback available)

## 1. Start the System

```bash
# Build all services and start
docker compose up --build

# Or start in background
docker compose up -d --build

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

Wait for all services to be healthy (health check should pass).

## 2. Test Data Ingestion

### 2.1 Upload a Sample Document

```bash
# Create a sample text file
echo "Vietnamese Legal Document Sample

Luật Dân sự năm 2015:
Điều 1: Quyền và nghĩa vụ của công dân
Điều 2: Bảo vệ quyền sở hữu
Điều 3: Hợp đồng dân sự
..." > sample.txt

# Upload via admin-service
curl -X POST http://localhost:8007/upload \
  -F "file=@sample.txt"

# Response:
# {
#   "success": true,
#   "document_id": "550e8400-e29b-41d4-a716-446655440000",
#   "filename": "sample.txt",
#   "message": "Processed 15 chunks"
# }
```

Save the `document_id` for later testing.

### 2.2 Verify File in Storage

```bash
# List files in document
curl http://localhost:8001/list?document_id=<DOCUMENT_ID>

# Response:
# {
#   "success": true,
#   "files": ["sample.txt"],
#   "document_id": "550e8400-..."
# }
```

### 2.3 Verify Vectors in Database

```bash
# List documents
curl http://localhost:8007/documents

# Response:
# {
#   "success": true,
#   "documents": [
#     {
#       "id": "550e8400-...",
#       "filename": "sample.txt",
#       "created_at": "2024-01-15T10:30:00"
#     }
#   ],
#   "total": 1
# }

# Check vector count
psql -h localhost -U legalrag -d legalrag -c \
  "SELECT COUNT(*) FROM chunks WHERE document_id = '<DOCUMENT_ID>';"
```

## 3. Test Query / RAG

### 3.1 Simple Query

```bash
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quyền sở hữu là gì?",
    "top_k": 5
  }'

# Response:
# {
#   "answer": "Based on your documents, quyền sở hữu là...",
#   "sources": [
#     {
#       "document_id": "550e8400-...",
#       "chunk_index": 2,
#       "content": "Bảo vệ quyền sở hữu...",
#       "similarity": 0.85
#     }
#   ],
#   "token_count": {
#     "prompt": 256,
#     "response": 128,
#     "total": 384
#   }
# }
```

### 3.2 Batch Queries

```bash
# Query 1
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Hợp đồng là gì?", "top_k": 10}'

# Query 2
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Quyền của công dân?", "top_k": 5}'
```

## 4. Test All Services

### 4.1 Embedding Service

```bash
# Single embedding
curl -X POST http://localhost:8004/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Quyền sở hữu tài sản"}'

# Response:
# {
#   "text": "Quyền sở hữu tài sản",
#   "embedding": [0.123, -0.456, 0.789, ...],  # 384 floats
#   "dimension": 384
# }

# Batch embedding
curl -X POST http://localhost:8004/embed-batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Hợp đồng dân sự",
      "Bảo vệ quyền",
      "Nghĩa vụ pháp lý"
    ]
  }'
```

### 4.2 Vector Service

```bash
# Check stats
curl http://localhost:8003/count

# Response:
# {
#   "total_vectors": 45,
#   "documents": 1,
#   "chunks": 45
# }

# Search by vector
curl -X POST http://localhost:8003/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.123, -0.456, ...],  # 384-dim vector
    "top_k": 5,
    "threshold": 0.7
  }'
```

### 4.3 LLM Service

```bash
curl -X POST http://localhost:8006/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Giải thích quyền sở hữu trong luật dân sự Việt Nam",
    "max_length": 512,
    "temperature": 0.7
  }'

# Response:
# {
#   "prompt": "Giải thích quyền sở hữu...",
#   "response": "Quyền sở hữu là quyền của người dân...",
#   "tokens": 256
# }
```

## 5. Health Checks

```bash
# Check all services
curl http://localhost:8001/health  # storage
curl http://localhost:8002/health  # identifill
curl http://localhost:8003/health  # vector
curl http://localhost:8004/health  # embedding
curl http://localhost:8005/health  # query
curl http://localhost:8006/health  # llm
curl http://localhost:8007/health  # admin

# All should return:
# {
#   "status": "healthy",
#   "db": "ok",
#   "services": "ok"
# }
```

## 6. Access UIs

- **MinIO Console** (File Storage): http://localhost:9001

  - Username: minioadmin
  - Password: minioadmin123

- **pgAdmin** (Database): Not included (use psql or external tools)

  - Or add pgAdmin service to docker-compose for GUI

- **Frontend**: http://localhost:3000

- **API Documentation**:
  - http://localhost:8001/docs (storage)
  - http://localhost:8004/docs (embedding)
  - http://localhost:8005/docs (query)
  - http://localhost:8007/docs (admin)

## 7. Common Issues & Fixes

### Services fail to start

```bash
# Check Docker resources
docker stats

# Increase Docker memory allocation
# Settings → Resources → Memory: 12GB+

# Restart services
docker compose down
docker compose up --build
```

### LLM service won't start (CUDA error)

```bash
# Option 1: Fall back to CPU in docker-compose.yml
# Change DEVICE=cuda to DEVICE=cpu

# Option 2: Install NVIDIA Docker runtime
# Follow: https://docs.docker.com/config/containers/resource_constraints/#gpu
```

### Vector search returns no results

```bash
# Check if documents were uploaded
curl http://localhost:8007/documents

# Verify vectors in database
psql -h localhost -U legalrag -d legalrag -c \
  "SELECT COUNT(*) FROM chunks;"

# Check embedding service
curl http://localhost:8004/health
```

### Out of memory

```bash
# Reduce batch sizes in .env files
# BATCH_SIZE=16 (default 32 for embedding)

# Or stop unneeded services
docker compose down llm-service
```

## 8. Performance Testing

```bash
# Load test with multiple documents
for i in {1..5}; do
  echo "Document $i" > doc$i.txt
  curl -X POST http://localhost:8007/upload \
    -F "file=@doc$i.txt"
done

# Measure query response time
time curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Test query", "top_k": 10}'
```

## 9. Cleanup

```bash
# Stop all services
docker compose down

# Remove data volumes (WARNING: deletes everything)
docker compose down -v

# View disk usage
docker volume ls
```

## 10. Next Steps

1. Update frontend to use new API endpoints (see FRONTEND_API_INTEGRATION.md)
2. Test with real Vietnamese legal documents (PDFs, DOCX)
3. Tune model parameters (temperature, top_k, chunk_size)
4. Add Kong Gateway for production (optional)
5. Deploy to cloud (Azure, AWS, GCP)

---

**For more details, see individual service README.md files in each service directory.**
