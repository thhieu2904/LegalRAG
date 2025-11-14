# LegalRAG Deployment Checklist

Complete checklist for deploying and validating the LegalRAG microservices architecture.

## Pre-Deployment

### System Requirements
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] 12GB+ RAM available
- [ ] 20GB+ disk space (for models and data)
- [ ] (Optional) NVIDIA GPU with 12GB+ VRAM for LLM service
- [ ] (Optional) NVIDIA CUDA toolkit for GPU support

### Repository Setup
- [ ] Clone repository: `git clone [repo-url] LegalRAG`
- [ ] Navigate to root: `cd LegalRAG`
- [ ] Verify all services exist:
  ```bash
  ls -d admin-service admin_service embedding-service identifill_service \
       llm-service query-service storage-service vector-service
  ```
- [ ] Check main files exist:
  ```bash
  ls docker-compose.yml schema.sql QUICKSTART.md ARCHITECTURE.md
  ```

### Configuration Files
- [ ] Copy environment templates to each service `.env`:
  - [ ] `admin-service/.env`
  - [ ] `storage-service/.env`
  - [ ] `vector-service/.env`
  - [ ] `embedding-service/.env`
  - [ ] `llm-service/.env`
  - [ ] `query-service/.env`
- [ ] Review and customize each `.env` file if needed
- [ ] Verify database credentials in all services match docker-compose

## Build & Startup

### Docker Build
- [ ] Build all services: `docker compose build --no-cache`
  - Verify no build errors
  - Check all 9 services built successfully
- [ ] Check image sizes:
  ```bash
  docker images | grep legalrag
  ```
  Expected:
  - embedding-service: ~2GB (includes model weights)
  - llm-service: ~18GB (includes Gemma/Llama)
  - Other services: ~200-500MB each

### Docker Compose Up
- [ ] Start system: `docker compose up -d --build`
- [ ] Wait 60 seconds for services to initialize
- [ ] Check container status: `docker compose ps`
  - All containers should show "Up" status
  - All health checks should pass (green checkmarks)

### Wait for Readiness
- [ ] PostgreSQL ready:
  ```bash
  docker compose logs postgres-vector | grep "accepting connections"
  ```
- [ ] MinIO ready:
  ```bash
  docker compose logs minio | grep "S3-API"
  ```
- [ ] All services healthy:
  ```bash
  docker compose ps | grep -v Up
  # Should return no results (all should be Up)
  ```

## Service Validation

### Health Checks
- [ ] Storage Service: `curl http://localhost:8001/health`
  - Expected: `{"status": "healthy", "db": "ok", "services": "ok"}`
- [ ] Vector Service: `curl http://localhost:8003/health`
  - Expected: `{"status": "healthy", "db": "ok"}`
- [ ] Embedding Service: `curl http://localhost:8004/health`
  - Expected: `{"status": "healthy", "model": "loaded"}`
- [ ] LLM Service: `curl http://localhost:8006/health`
  - Expected: `{"status": "healthy", "model": "loaded"}`
- [ ] Query Service: `curl http://localhost:8005/health`
  - Expected: `{"status": "healthy", "dependencies": "ok"}`
- [ ] Admin Service: `curl http://localhost:8007/health`
  - Expected: `{"status": "healthy", "db": "ok", "services": "ok"}`

### Database Verification
- [ ] Connect to PostgreSQL:
  ```bash
  psql -h localhost -U legalrag -d legalrag -c "\dt"
  ```
  - Should show: documents, chunks, users, forms tables
- [ ] Check pgvector extension:
  ```bash
  psql -h localhost -U legalrag -d legalrag -c "CREATE EXTENSION IF NOT EXISTS vector;"
  ```
- [ ] Verify schema:
  ```bash
  psql -h localhost -U legalrag -d legalrag -c \
    "SELECT COUNT(*) FROM chunks;"
  ```
  - Should return: 0 (initially empty)

### MinIO Setup
- [ ] Access MinIO Console: http://localhost:9001
  - Username: `minioadmin`
  - Password: `minioadmin123`
- [ ] Verify bucket exists: `legal-documents`
- [ ] Create bucket if missing:
  ```bash
  docker exec legalrag-minio mc mb minio/legal-documents
  ```

## Functional Tests

### Test 1: Document Upload
```bash
# Create test document
echo "Luật Dân sự: Quyền sở hữu tài sản là quyền của người dân" > test.txt

# Upload via admin-service
curl -X POST http://localhost:8007/upload -F "file=@test.txt"

# Expected response:
# {
#   "success": true,
#   "document_id": "550e8400-...",
#   "filename": "test.txt",
#   "message": "Processed 1 chunks"
# }
```

**Checklist:**
- [ ] Upload successful (status 201)
- [ ] Got document_id back
- [ ] File appears in MinIO console
- [ ] Chunks table has new entries
- [ ] Cleanup: `rm test.txt`

### Test 2: Vector Search
```bash
# Get document_id from previous test, then search
curl -X POST http://localhost:8003/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, -0.2, 0.3, ...],  # 384 floats
    "top_k": 5
  }'

# Expected: Array of similar chunks with similarity scores
```

**Checklist:**
- [ ] Search successful
- [ ] Results returned (>0 items)
- [ ] Similarity scores in range [0, 1]

### Test 3: Query (RAG)
```bash
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quyền sở hữu là gì?",
    "top_k": 10
  }'

# Expected response:
# {
#   "answer": "Quyền sở hữu...",
#   "sources": [...],
#   "token_count": {...}
# }
```

**Checklist:**
- [ ] Query successful
- [ ] Answer generated
- [ ] Sources included with similarity scores
- [ ] Token count present
- [ ] Response time reasonable (<10 seconds)

### Test 4: Batch Operations
```bash
# Upload multiple documents
for i in {1..3}; do
  echo "Document $i content" > doc$i.txt
  curl -X POST http://localhost:8007/upload -F "file=@doc$i.txt"
done

# List all documents
curl http://localhost:8007/documents

# Expected: All 3 documents listed

# Cleanup
rm doc*.txt
```

**Checklist:**
- [ ] All uploads successful
- [ ] Document count accurate
- [ ] Each document has metadata (id, filename, created_at)

## Performance Validation

### Response Time Tests
```bash
# Measure query response time
time curl -s -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "top_k": 5}' > /dev/null
```

**Expected Performance:**
- [ ] Embedding: < 100ms
- [ ] Vector search: < 50ms (with <1000 vectors)
- [ ] LLM generation: 2-5 seconds (depends on answer length)
- [ ] Total Q&A: 5-10 seconds

### Load Test
```bash
# Send 10 concurrent queries
for i in {1..10}; do
  curl -s -X POST http://localhost:8005/query \
    -H "Content-Type: application/json" \
    -d '{"question": "test '$i'", "top_k": 5}' &
done

# Wait for all to complete
wait

# Check service logs for errors
docker compose logs query-service | tail -20
```

**Checklist:**
- [ ] All requests completed successfully
- [ ] No timeout errors
- [ ] No out-of-memory errors
- [ ] Services remain healthy

## Integration Tests

### Frontend API Integration
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Frontend runs: `npm run dev`
- [ ] Access frontend: http://localhost:3000
- [ ] Upload test document via UI
- [ ] Query documents via UI
- [ ] Verify answers are returned

### CCCD Service Integration
- [ ] Identifill service running: `curl http://localhost:8002/health`
- [ ] Test CCCD endpoint (if available)
- [ ] Verify integration with admin-service (if needed)

## Production Preparation

### Environment Configuration
- [ ] Update `.env` files with production secrets
- [ ] Change database password from default
- [ ] Change MinIO credentials from default
- [ ] Set proper service URLs (not localhost)
- [ ] Enable GPU support if available
- [ ] Set appropriate model cache directories

### Logging & Monitoring
- [ ] Check log volumes: `docker compose logs --tail=50`
- [ ] Enable log rotation (Docker daemon.json)
- [ ] Setup log aggregation (optional: ELK, Loki, etc.)

### Backup & Recovery
- [ ] Export database schema: `pg_dump -h localhost -U legalrag -d legalrag > backup.sql`
- [ ] Backup MinIO data: `mc cp -r minio/legal-documents ./backup/`
- [ ] Document recovery procedures

### Security Hardening
- [ ] Change all default credentials
- [ ] Setup firewall rules (only expose port 3000/80/443)
- [ ] Enable HTTPS (Let's Encrypt certificate)
- [ ] Setup authentication (JWT, OAuth2, etc.)
- [ ] Setup rate limiting
- [ ] Enable CORS restrictions

## Deployment Script
```bash
#!/bin/bash

# Automated deployment checklist
echo "🚀 Starting LegalRAG deployment..."

# 1. Prerequisites
echo "✓ Checking prerequisites..."
docker --version || { echo "Docker not found!"; exit 1; }
docker-compose --version || { echo "Docker Compose not found!"; exit 1; }

# 2. Build
echo "✓ Building services..."
docker compose build --no-cache || exit 1

# 3. Start
echo "✓ Starting services..."
docker compose up -d || exit 1

# 4. Wait for readiness
echo "✓ Waiting for services to be ready..."
sleep 30

# 5. Health checks
echo "✓ Running health checks..."
bash health-check.sh || exit 1

# 6. Functional tests
echo "✓ Running functional tests..."
# Add your test commands here

echo ""
echo "✅ Deployment complete!"
echo "🌐 Frontend: http://localhost:3000"
echo "📚 API Docs: http://localhost:8005/docs"
echo "💾 MinIO: http://localhost:9001"
```

## Troubleshooting

### Common Issues

#### Services won't start
```bash
# Check logs
docker compose logs [service-name]

# Rebuild images
docker compose down -v
docker compose build --no-cache
docker compose up
```

#### Out of memory
```bash
# Reduce batch sizes in .env files
BATCH_SIZE=8  # down from 32

# Or allocate more Docker memory
# Docker Desktop → Preferences → Resources → Memory: 16GB+
```

#### Database connection errors
```bash
# Check PostgreSQL is running
docker compose logs postgres-vector

# Reset database
docker compose down
docker volume rm legalrag_postgres_data
docker compose up postgres-vector

# Re-create schema
cat schema.sql | psql -h localhost -U legalrag -d legalrag
```

#### GPU/CUDA errors
```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi

# If failed, install NVIDIA Docker
# https://docs.docker.com/config/containers/resource_constraints/#gpu

# Fallback to CPU
# Edit docker-compose.yml: DEVICE=cpu in llm-service
# This will be slower but will work
```

#### Models not downloading
```bash
# Check disk space
df -h

# Check internet connection
curl https://huggingface.co

# Manual download (if offline)
# Download models from huggingface.co and copy to service volumes

# Monitor download progress
docker compose logs embedding-service | grep "downloading\|Loading\|Saved"
```

## Post-Deployment

### Validation Reports
- [ ] Run health check: `bash health-check.sh`
- [ ] Generate performance report (if benchmarking)
- [ ] Document any custom configurations
- [ ] Save deployment logs

### Documentation Updates
- [ ] Update README with actual deployment details
- [ ] Document any custom service configurations
- [ ] Update API documentation if changed
- [ ] Create runbook for operations team

### Handoff Checklist
- [ ] All services healthy and running
- [ ] Documentation up to date
- [ ] Team trained on usage
- [ ] Monitoring setup (if applicable)
- [ ] Backup procedures documented
- [ ] Support contacts assigned

---

**For step-by-step setup instructions, see QUICKSTART.md**
**For architecture details, see ARCHITECTURE.md**
**For API integration, see FRONTEND_API_INTEGRATION.md**
