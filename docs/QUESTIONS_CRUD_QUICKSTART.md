# 🚀 Quick Start Guide - Questions CRUD Implementation

## 📋 Tóm tắt

Để implement CRUD operations cho questions, bạn cần:

1. ✅ **Admin Service**: Thêm CRUD endpoints (CREATE/UPDATE/DELETE)
2. ✅ **RAG Service**: Thêm internal endpoints (cache invalidation, VectorDB rebuild)
3. ✅ **Integration**: Admin service gọi RAG service sau mỗi update

## 🎯 Priority Implementation Order

### Phase 1: Basic CRUD (CRITICAL - 2-3 ngày)

#### Step 1.1: Implement CRUD endpoints trong Admin Service

**File:** `admin_service/app/api/questions.py`

Thêm các endpoints:

```python
# Đã có reference code trong:
# admin_service/app/api/questions_crud_example.py

POST   /api/questions/collections/{collection}/documents/{doc_id}
PUT    /api/questions/collections/{collection}/documents/{doc_id}
DELETE /api/questions/collections/{collection}/documents/{doc_id}
PATCH  /api/questions/collections/{collection}/documents/{doc_id}/variants
```

**Key features cần có:**

- ✅ Pydantic validation
- ✅ File backup before update
- ✅ Rollback on error
- ✅ UTF-8 encoding
- ✅ Error handling

**Estimated time:** 8-10 giờ

#### Step 1.2: Test CRUD locally

```bash
# Test CREATE
curl -X POST http://localhost:8001/api/questions/collections/quy_trinh_test/documents/DOC_001 \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "main_question": "Test question?",
      "question_variants": ["Variant 1", "Variant 2"]
    },
    "rebuild_vectordb": false
  }'

# Test READ (already works)
curl http://localhost:8001/api/questions/collections/quy_trinh_test/documents/DOC_001

# Test UPDATE
curl -X PUT http://localhost:8001/api/questions/collections/quy_trinh_test/documents/DOC_001 \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "main_question": "Updated question?",
      "question_variants": ["New variant 1", "New variant 2", "New variant 3"]
    },
    "rebuild_vectordb": false
  }'

# Test DELETE
curl -X DELETE http://localhost:8001/api/questions/collections/quy_trinh_test/documents/DOC_001
```

**Estimated time:** 2-4 giờ

### Phase 2: Cache Management (CRITICAL - 1-2 ngày)

#### Step 2.1: Create internal endpoints trong RAG Service

**File:** `rag_service/app/api/internal.py` (tạo mới)

```python
# Đã có reference code trong:
# rag_service/app/api/internal_example.py

POST /api/internal/cache/invalidate
POST /api/internal/vectordb/rebuild
GET  /api/internal/health
GET  /api/internal/cache/stats
```

**Estimated time:** 4-6 giờ

#### Step 2.2: Register internal router trong main.py

**File:** `rag_service/main.py`

```python
from app.api import internal

# Add after existing routers
app.include_router(internal.router)
```

**Estimated time:** 30 phút

#### Step 2.3: Integrate Admin → RAG communication

**File:** `admin_service/app/api/questions.py`

Thêm vào sau mỗi update/delete:

```python
import httpx

RAG_SERVICE_URL = "http://localhost:8000"  # Or from config

async def update_questions(...):
    # 1. Update file
    ...

    # 2. Invalidate cache
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{RAG_SERVICE_URL}/api/internal/cache/invalidate",
                json={"collection": collection, "doc_id": doc_id}
            )
    except Exception as e:
        logger.warning(f"Cache invalidation failed: {e}")
```

**Estimated time:** 2-3 giờ

#### Step 2.4: Test cache invalidation

```bash
# Terminal 1: Start RAG service
cd rag_service && python main.py

# Terminal 2: Start Admin service
cd admin_service && python main.py

# Terminal 3: Test update with cache invalidation
curl -X PUT http://localhost:8001/api/questions/... \
  -H "Content-Type: application/json" \
  -d '{"data": {...}}'

# Check logs - should see cache invalidation messages
```

**Estimated time:** 1-2 giờ

### Phase 3: VectorDB Integration (HIGH - 2-3 ngày)

#### Step 3.1: Implement selective rebuild

**File:** `rag_service/app/api/internal.py`

Implement `_rebuild_document_vectordb()` function:

```python
async def _rebuild_document_vectordb(collection: str, doc_id: str):
    # 1. Load updated questions.json
    # 2. Delete old document chunks from VectorDB
    # 3. Re-index document with new questions
    # See internal_example.py for reference
```

**Estimated time:** 6-8 giờ

#### Step 3.2: Add background processing

**File:** `admin_service/app/api/questions.py`

```python
from fastapi import BackgroundTasks

@router.put("/questions/...")
async def update_questions(
    ...,
    background_tasks: BackgroundTasks
):
    # Update file first
    ...

    # Queue VectorDB rebuild in background
    if rebuild_vectordb:
        # Call RAG service to queue rebuild
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{RAG_SERVICE_URL}/api/internal/vectordb/rebuild",
                json={
                    "collection": collection,
                    "doc_id": doc_id,
                    "async_mode": True
                }
            )
```

**Estimated time:** 4-6 giờ

#### Step 3.3: Test rebuild

```bash
# Update questions with rebuild
curl -X PUT http://localhost:8001/api/questions/collections/test/documents/DOC_001 \
  -H "Content-Type: application/json" \
  -d '{
    "data": {...},
    "rebuild_vectordb": true
  }'

# Check RAG service logs - should see rebuild messages
# Query RAG to verify new questions work
curl http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "new question variant"}'
```

**Estimated time:** 2-3 giờ

## 🔧 Configuration

### Environment Variables

**Admin Service** (`admin_service/app/core/config.py`):

```python
RAG_SERVICE_URL: str = "http://localhost:8000"
RAG_SERVICE_TIMEOUT: int = 10  # seconds
```

**RAG Service** (`rag_service/app/core/config.py`):

```python
INTERNAL_API_ENABLED: bool = True
INTERNAL_API_KEY: str = "your-secret-key"  # For security
```

### Security (IMPORTANT!)

Internal endpoints should NOT be publicly accessible!

**Option 1: Docker network isolation** (RECOMMENDED)

```yaml
# docker-compose.yml
services:
  admin_service:
    networks:
      - internal
      - public

  rag_service:
    networks:
      - internal
    # Don't expose 8000 to host!

networks:
  internal:
    driver: bridge
  public:
    driver: bridge
```

**Option 2: API Key authentication**

```python
# rag_service/app/api/internal.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=401)

router = APIRouter(dependencies=[Depends(verify_api_key)])
```

## 📊 Performance Expectations

### Single Update Operation

```
Timeline:
├─ File write:              5-10ms
├─ Validation:              < 1ms
├─ Backup:                  5-10ms
├─ Cache invalidation:      2-5ms (HTTP call)
├─ Queue VectorDB rebuild:  < 1ms
└─ Total response time:     15-30ms ✅

Background tasks:
└─ VectorDB rebuild:        1-2 seconds (doesn't block response)
```

### Batch Update (10 documents)

```
Timeline:
├─ Sequential updates:      150-300ms
├─ Cache invalidation:      20-50ms
├─ Queue rebuilds:          < 10ms
└─ Total response time:     200-400ms ✅

Background tasks:
└─ VectorDB rebuild:        10-20 seconds (all documents)
```

## 🐛 Debugging

### Common Issues

#### Issue 1: Cache not invalidating

**Symptom:** Old questions still showing in query results

**Debug:**

```bash
# Check RAG service logs
tail -f rag_service/logs/app.log | grep "cache"

# Check cache stats
curl http://localhost:8000/api/internal/cache/stats

# Manual cache clear (restart RAG service)
```

**Solution:**

- Verify Admin → RAG communication working
- Check firewall/network settings
- Verify cache invalidation endpoint called

#### Issue 2: VectorDB not rebuilding

**Symptom:** New questions not searchable

**Debug:**

```bash
# Check RAG service logs
tail -f rag_service/logs/app.log | grep "rebuild"

# Check VectorDB health
curl http://localhost:8000/api/internal/health
```

**Solution:**

- Verify rebuild endpoint called
- Check background task execution
- Manual rebuild: `python rag_service/tools/vectordb.py`

#### Issue 3: File corruption

**Symptom:** Invalid JSON, missing data

**Debug:**

```bash
# Check backup directory
ls -la data/backups/questions/

# Validate JSON
python -m json.tool data/storage/collections/.../DOC_001/questions.json
```

**Solution:**

- Restore from backup
- Improve validation logic
- Add pre-write validation

## 📝 Testing Checklist

### Unit Tests

- [ ] Validate questions format
- [ ] Validate duplicate detection
- [ ] Validate empty field handling
- [ ] Test backup/restore logic
- [ ] Test rollback on error

### Integration Tests

- [ ] Create questions → verify file created
- [ ] Update questions → verify file updated
- [ ] Delete questions → verify file deleted
- [ ] Update → verify cache invalidated
- [ ] Update → verify VectorDB rebuilt

### Performance Tests

- [ ] Single update < 30ms
- [ ] Batch update (10 docs) < 500ms
- [ ] VectorDB rebuild < 3 seconds per doc
- [ ] Concurrent updates (10 users) no corruption

### Security Tests

- [ ] Internal endpoints not publicly accessible
- [ ] API key authentication working
- [ ] Input validation preventing injection
- [ ] File path validation preventing traversal

## 🚀 Deployment

### Development Environment

```bash
# 1. Start services
cd rag_service && python main.py &
cd admin_service && python main.py &

# 2. Test CRUD
curl http://localhost:8001/api/questions/...

# 3. Check logs
tail -f rag_service/logs/app.log
tail -f admin_service/logs/app.log
```

### Production Environment

```bash
# 1. Update docker-compose.yml with internal network

# 2. Build images
docker-compose build

# 3. Deploy
docker-compose up -d

# 4. Health check
curl http://localhost:8001/health
curl http://rag_service:8000/api/internal/health  # Internal only

# 5. Monitor logs
docker-compose logs -f admin_service
docker-compose logs -f rag_service
```

## 📚 Additional Resources

- **Full Analysis:** `docs/QUESTIONS_CRUD_ANALYSIS.md`
- **Code Examples:**
  - `admin_service/app/api/questions_crud_example.py`
  - `rag_service/app/api/internal_example.py`
- **Architecture:** `.github/copilot-instructions.md`

## 🎯 Success Criteria

### Minimum Viable Product (MVP)

- ✅ CRUD endpoints working
- ✅ Cache invalidation working
- ✅ No data corruption
- ✅ Response time < 50ms

### Production Ready

- ✅ VectorDB rebuild working
- ✅ Background processing
- ✅ Error handling robust
- ✅ Security implemented
- ✅ Monitoring in place
- ✅ Documentation complete

## 👥 Team Assignment Suggestion

### 1 Developer (3 tuần)

- Week 1: Phase 1 + Phase 2
- Week 2: Phase 3 + Testing
- Week 3: Phase 4-6 + Documentation

### 2 Developers (1.5-2 tuần)

- Developer A: Admin Service (Phase 1, 4, 5)
- Developer B: RAG Service (Phase 2, 3, 6)
- Collaborate: Testing & Integration

---

**Last updated:** 11/10/2025  
**Status:** Ready for implementation  
**Priority:** HIGH
