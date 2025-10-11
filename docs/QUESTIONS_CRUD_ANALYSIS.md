# 📋 Phân tích CRUD Operations cho Questions System

**Ngày tạo:** 11/10/2025  
**Mục đích:** Đánh giá khả năng thực hiện CRUD trên questions và impact lên backend

---

## 📊 TÌNH TRẠNG HIỆN TẠI

### Cấu trúc dữ liệu Questions

```
rag_service/data/storage/collections/
├── {collection_name}/
│   └── documents/
│       └── {DOC_XXX}/
│           ├── questions.json ← Target của CRUD operations
│           ├── {document}.json
│           └── {document}.docx
```

**Thống kê:**

- ✅ **13 collections** đang hoạt động
- ✅ **166 files questions.json** (trung bình ~13 docs/collection)
- ✅ File size: **< 1KB mỗi file** (rất nhẹ)

**Format chuẩn của questions.json:**

```json
{
  "main_question": "Câu hỏi chính?",
  "question_variants": ["Biến thể câu hỏi 1?", "Biến thể câu hỏi 2?", "..."]
}
```

### Services hiện có

#### 1. Admin Service (Port 8001)

**✅ Đã implement READ operations:**

- `GET /api/questions` - List tất cả questions (có filter & search)
- `GET /api/questions/collections/{collection}/documents/{doc_id}` - Get questions của document
- `GET /api/questions/collections/{collection}` - Get questions của collection
- `GET /api/questions/search?q={query}` - Search questions

**❌ CHƯA CÓ WRITE operations:**

- `POST /api/questions/collections/{collection}/documents/{doc_id}` - Tạo mới questions
- `PUT /api/questions/collections/{collection}/documents/{doc_id}` - Update questions
- `DELETE /api/questions/collections/{collection}/documents/{doc_id}` - Xóa questions
- `PATCH /api/questions/collections/{collection}/documents/{doc_id}/variants` - Update variants

**Infrastructure sẵn có:**

- ✅ PathConfig service cho path management
- ✅ Error handling và logging
- ✅ Request validation
- ✅ JSON encoding/decoding (UTF-8)

#### 2. RAG Service (Port 8000)

**Cách sử dụng questions:**

1. **VectorDB Build**: Questions được fused vào document chunks khi build index

   ```python
   # rag_service/tools/vectordb.py:188
   "questions": questions_data,  # Add questions for fused indexing
   ```

2. **Query Router**: Sử dụng questions để match user queries

   ```python
   # rag_service/app/services/router.py
   # Match questions với user input để route đúng document
   ```

3. **Cache System**: Questions được cache để tối ưu performance
   - Router cache: `data/cache/router_cache.json`
   - Metadata cache trong memory

---

## 🎯 ĐÁNH GIÁ ĐỘ KHÓ & KHẢ NĂNG

### ✅ THỰC HIỆN DỄ DÀNG (Độ khó: 3/10)

**Lý do:**

1. **Cấu trúc đơn giản**

   - JSON format rõ ràng, không phức tạp
   - Không có nested relationships phức tạp
   - Validation rules đơn giản

2. **Infrastructure sẵn có**

   - Admin service đã có routing, error handling
   - PathConfig service quản lý paths chuẩn
   - FastAPI hỗ trợ validation tốt

3. **File operations nhanh**

   - File size nhỏ (< 1KB)
   - I/O operations < 10ms
   - 166 files không phải số lượng lớn

4. **Không cần Database phức tạp**
   - File-based storage đủ
   - Không cần migration scripts
   - Rollback đơn giản (backup files)

### ⚠️ THÁCH THỨC CẦN XỬ LÝ

#### 1. **Cache Invalidation** (Priority: HIGH)

**Vấn đề:**

- RAG service cache questions trong memory
- Router cache lưu fused content (questions + metadata)
- Khi update questions, cache cũ còn tồn tại

**Giải pháp:**

```python
# Option 1: Cache invalidation API
POST /api/internal/cache/invalidate
{
  "collection": "quy_trinh_xxx",
  "doc_id": "DOC_001",
  "cache_types": ["router", "metadata"]
}

# Option 2: Auto-detect & invalidate
# Admin service gọi RAG service sau khi update
```

**Implementation:**

- Thêm endpoint trong RAG service để clear cache
- Admin service gọi endpoint này sau mỗi update
- Async processing để không block request

#### 2. **VectorDB Rebuild** (Priority: MEDIUM)

**Vấn đề:**

- Questions được fused vào document chunks trong VectorDB
- Update questions → cần rebuild affected chunks
- Rebuild toàn bộ DB = overhead lớn

**Giải pháp:**

```python
# Selective rebuild - chỉ rebuild affected document
POST /api/internal/vectordb/rebuild
{
  "collection": "quy_trinh_xxx",
  "doc_id": "DOC_001",
  "rebuild_scope": "document"  # not "collection" or "all"
}
```

**Impact estimation:**

- Full rebuild: ~2-5 phút (166 documents)
- Single document rebuild: ~1-3 giây
- **Khuyến nghị**: Selective rebuild only

#### 3. **Concurrent Access Control** (Priority: MEDIUM)

**Vấn đề:**

- Multiple admin users edit cùng lúc
- File write conflicts
- Data corruption risk

**Giải pháp:**

```python
# File locking mechanism
import fcntl  # Unix
import msvcrt  # Windows

class QuestionFileManager:
    def __init__(self):
        self._locks = {}

    async def write_with_lock(self, file_path, data):
        # Acquire lock
        # Write data
        # Release lock
        pass
```

**Alternative:**

- Optimistic locking với version field
- Last-write-wins policy (đơn giản hơn)
- Queue system cho sequential processing

#### 4. **Service Communication** (Priority: HIGH)

**Vấn đề:**

- Admin service update questions
- RAG service cần biết để invalidate cache
- Không có communication channel hiện tại

**Giải pháp:**

**Option A: HTTP API calls** (Đơn giản, khuyến nghị)

```python
# Admin service sau khi update
async def update_questions(...):
    # 1. Update file
    await _write_questions_file(...)

    # 2. Notify RAG service
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{RAG_SERVICE_URL}/api/internal/invalidate-cache",
                json={"collection": ..., "doc_id": ...}
            )
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
        # Continue anyway - cache will expire eventually
```

**Option B: Message Queue** (Phức tạp hơn, scalable hơn)

```python
# Using Redis Pub/Sub or RabbitMQ
await message_queue.publish(
    "questions.updated",
    {"collection": ..., "doc_id": ...}
)
```

**Khuyến nghị**: Dùng Option A (HTTP) cho đơn giản

#### 5. **Data Validation & Rollback** (Priority: MEDIUM)

**Vấn đề:**

- Invalid JSON format
- Empty questions
- Update fail midway

**Giải pháp:**

```python
class QuestionValidator:
    def validate(self, data: dict) -> tuple[bool, str]:
        # Check main_question exists & not empty
        if not data.get("main_question", "").strip():
            return False, "main_question is required"

        # Check question_variants is array
        if not isinstance(data.get("question_variants", []), list):
            return False, "question_variants must be array"

        # Check no duplicate variants
        variants = data.get("question_variants", [])
        if len(variants) != len(set(variants)):
            return False, "Duplicate variants found"

        return True, "OK"

async def update_questions_safely(collection, doc_id, new_data):
    # 1. Validate
    is_valid, error = validator.validate(new_data)
    if not is_valid:
        raise ValidationError(error)

    # 2. Backup current file
    backup_path = create_backup(questions_file)

    try:
        # 3. Write new data
        await write_questions(new_data)

        # 4. Invalidate cache
        await invalidate_cache(collection, doc_id)

        # 5. Success - delete backup
        delete_backup(backup_path)

    except Exception as e:
        # Rollback from backup
        restore_backup(backup_path)
        raise
```

---

## 📈 IMPACT LÊN BACKEND

### ✅ LOW IMPACT nếu thiết kế đúng

**Performance metrics (ước tính):**

```
Single question file update:
├─ File write:           5-10ms
├─ Validation:           < 1ms
├─ Cache invalidation:   2-5ms (HTTP call)
├─ Backup creation:      5-10ms
└─ Total:                15-30ms ✅

Single document VectorDB rebuild:
├─ Load document:        10-20ms
├─ Embedding:            500-1000ms (depends on length)
├─ Index update:         50-100ms
└─ Total:                ~1-2 seconds ✅

Concurrent operations (10 users):
├─ With file locking:    150-300ms (sequential)
├─ Without locking:      Risk of corruption ❌
└─ With queue:           150-300ms (sequential) ✅
```

**Memory impact:**

- File operations: Negligible (< 1MB per operation)
- Cache invalidation: Frees memory ✅
- VectorDB rebuild: Temporary spike (~50MB per document)

**CPU impact:**

- File I/O: Low (async operations)
- Validation: Minimal (simple JSON checks)
- VectorDB rebuild: Medium (embedding calculations)

### ⚠️ MEDIUM-HIGH IMPACT nếu không tối ưu

**Anti-patterns cần tránh:**

❌ **Rebuild toàn bộ VectorDB mỗi lần update**

```python
# KHÔNG NÊN:
async def update_questions(...):
    update_file(...)
    rebuild_entire_vectordb()  # 2-5 phút!!! ❌
```

❌ **Synchronous blocking operations**

```python
# KHÔNG NÊN:
@router.put("/questions/...")
def update_questions(...):  # Sync function
    time.sleep(2)  # Block toàn bộ server ❌
    return response
```

❌ **No error handling**

```python
# KHÔNG NÊN:
async def update_questions(...):
    write_file(...)  # Nếu fail, file corrupt ❌
    # Không có rollback mechanism
```

❌ **No validation**

```python
# KHÔNG NÊN:
async def update_questions(data: dict):
    write_file(data)  # Accept bất kỳ data nào ❌
```

### 🎯 Optimizations khuyến nghị

1. **Batch operations với queue**

```python
# Update nhiều questions cùng lúc
POST /api/questions/batch-update
{
  "updates": [
    {"collection": "...", "doc_id": "DOC_001", "data": {...}},
    {"collection": "...", "doc_id": "DOC_002", "data": {...}}
  ]
}

# Process trong background queue
# Rebuild VectorDB 1 lần cho tất cả affected documents
```

2. **Cache strategy tiên tiến**

```python
# Time-based cache expiration
cache_ttl = 3600  # 1 hour

# Version-based cache
cache_key = f"questions:{collection}:{doc_id}:{version}"

# Cache warming sau rebuild
async def warm_cache_after_update(collection, doc_id):
    # Preload frequently accessed data
    pass
```

3. **Async background processing**

```python
from fastapi import BackgroundTasks

@router.put("/questions/...")
async def update_questions(
    ...,
    background_tasks: BackgroundTasks
):
    # 1. Update file ngay (fast)
    await update_file(...)

    # 2. Invalidate cache ngay (fast)
    await invalidate_cache(...)

    # 3. VectorDB rebuild trong background (slow)
    background_tasks.add_task(rebuild_vectordb, collection, doc_id)

    # Return ngay, không chờ rebuild
    return {"status": "updated", "rebuild_queued": True}
```

---

## 🚀 KẾ HOẠCH TRIỂN KHAI

### Phase 1: Basic CRUD Implementation (2-3 ngày)

**Mục tiêu:** Implement core CRUD endpoints

**Tasks:**

- [ ] Create `POST /api/questions/collections/{collection}/documents/{doc_id}`
- [ ] Create `PUT /api/questions/collections/{collection}/documents/{doc_id}`
- [ ] Create `DELETE /api/questions/collections/{collection}/documents/{doc_id}`
- [ ] Add validation logic
- [ ] Add error handling
- [ ] Write unit tests

**Deliverables:**

- CRUD endpoints hoạt động
- Basic validation
- Error handling chuẩn

**Estimated effort:** 12-16 giờ

### Phase 2: Cache Management (1-2 ngày)

**Mục tiêu:** Ensure cache consistency

**Tasks:**

- [ ] Create cache invalidation endpoint trong RAG service
- [ ] Admin service call cache invalidation sau updates
- [ ] Test cache invalidation flow
- [ ] Add logging & monitoring

**Deliverables:**

- Cache invalidation API
- Admin-RAG communication
- Cache consistency verified

**Estimated effort:** 8-10 giờ

### Phase 3: VectorDB Integration (2-3 ngày)

**Mục tiêu:** Selective rebuild cho affected documents

**Tasks:**

- [ ] Create selective rebuild endpoint
- [ ] Integrate với update flow
- [ ] Implement background processing
- [ ] Test rebuild performance
- [ ] Add rebuild status tracking

**Deliverables:**

- Selective VectorDB rebuild
- Background task processing
- Performance benchmarks

**Estimated effort:** 12-16 giờ

### Phase 4: Concurrent Access Control (1-2 ngày)

**Mục tiêu:** Handle concurrent updates safely

**Tasks:**

- [ ] Implement file locking mechanism
- [ ] Add optimistic locking với versioning
- [ ] Test concurrent scenarios
- [ ] Add conflict resolution

**Deliverables:**

- Safe concurrent access
- Conflict handling
- Test coverage

**Estimated effort:** 8-10 giờ

### Phase 5: Advanced Features (2-3 ngày)

**Mục tiêu:** Batch operations & optimizations

**Tasks:**

- [ ] Batch update endpoint
- [ ] Queue system cho batch processing
- [ ] Cache warming strategy
- [ ] Performance monitoring
- [ ] Documentation

**Deliverables:**

- Batch operations
- Queue system
- Performance dashboard
- Complete documentation

**Estimated effort:** 12-16 giờ

### Phase 6: Testing & Production (2-3 ngày)

**Mục tiêu:** Production-ready deployment

**Tasks:**

- [ ] Integration tests
- [ ] Load testing
- [ ] Security review
- [ ] Backup & restore testing
- [ ] Rollout plan
- [ ] Monitoring setup

**Deliverables:**

- Test coverage > 80%
- Performance benchmarks
- Security audit passed
- Production deployment

**Estimated effort:** 12-16 giờ

---

## 📊 TỔNG KẾT

### Độ khó tổng thể: **3/10** (DỄ)

**Lý do đánh giá dễ:**

- ✅ Cấu trúc dữ liệu đơn giản
- ✅ Infrastructure sẵn có
- ✅ File operations nhanh
- ✅ Số lượng data nhỏ (166 files)
- ✅ Không cần database migration

### Impact lên Backend: **LOW** (nếu thiết kế đúng)

**Performance metrics:**

- Single update: **15-30ms** ✅
- VectorDB rebuild: **1-2s** per document ✅
- Concurrent 10 users: **150-300ms** ✅
- Memory overhead: **< 50MB** per operation ✅

### Timeline tổng cộng: **10-16 ngày làm việc**

**Breakdown:**

- Phase 1 (CRUD): 2-3 ngày
- Phase 2 (Cache): 1-2 ngày
- Phase 3 (VectorDB): 2-3 ngày
- Phase 4 (Concurrency): 1-2 ngày
- Phase 5 (Advanced): 2-3 ngày
- Phase 6 (Testing): 2-3 ngày

**Team suggestion:**

- 1 developer full-time: ~3 tuần
- 2 developers: ~1.5-2 tuần

### Khuyến nghị

#### ✅ NÊN THỰC HIỆN vì:

1. **Dễ implement** - Độ khó thấp, risk thấp
2. **Giá trị cao** - Cho phép quản lý questions linh hoạt
3. **Performance tốt** - Impact thấp nếu thiết kế đúng
4. **Scalable** - Dễ mở rộng sau này
5. **User experience** - Admin không cần edit file trực tiếp

#### ⚠️ LƯU Ý:

1. **PHẢI có cache invalidation** - Không thể skip
2. **PHẢI có validation** - Data integrity critical
3. **NÊN có file locking** - Tránh corruption
4. **NÊN có background processing** - Tránh block requests
5. **NÊN có monitoring** - Track performance

#### 🎯 Priority order:

1. **Phase 1** (CRUD) - CRITICAL
2. **Phase 2** (Cache) - CRITICAL
3. **Phase 3** (VectorDB) - HIGH
4. **Phase 4** (Concurrency) - MEDIUM
5. **Phase 5** (Advanced) - LOW
6. **Phase 6** (Testing) - HIGH

---

## 📝 NEXT STEPS

### Immediate (Tuần này):

1. Review & approve plan này
2. Setup development branch
3. Kickoff Phase 1 implementation

### Short-term (2 tuần tới):

1. Complete Phase 1-3
2. Test trong staging environment
3. Gather feedback

### Long-term (1 tháng):

1. Complete all phases
2. Production deployment
3. Monitor & optimize

---

**Tác giả:** GitHub Copilot  
**Last updated:** 11/10/2025  
**Status:** Đề xuất chờ approval
