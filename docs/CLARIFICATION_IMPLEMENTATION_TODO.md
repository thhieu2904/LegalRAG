# 🎯 CLARIFICATION SYSTEM - IMPLEMENTATION TODO

**Ngày**: 24/11/2025  
**Branch**: `refactor_rag`  
**Scope**: Phase 1 - Simple Document Clarification

---

## 📊 PHÂN TÍCH CODEBASE HIỆN TẠI

### ✅ Những gì ĐÃ CÓ:

1. **Vector Service có sẵn document_ids filter**

   - File: `vector-service/src/database.py` (line 213-245)
   - Method: `search_similar(..., document_ids: Optional[List[str]])`
   - ✅ Ready to use - không cần sửa!

2. **Rerank Service đã implement document-first logic**

   - Returns ALL chunks from best document
   - Sử dụng `rerank_score` làm confidence

3. **Query Service có structure rõ ràng**

   - File: `query-service/src/main.py` (358 lines)
   - Flow: embed → search → rerank → generate
   - Small talk detection đã có (line 240-258)

4. **PostgreSQL database đã connect được**

   - Database: `legalrag`
   - User: `legalrag`
   - Table: `documents` (id UUID, title VARCHAR)
   - Current data: 1 document = "01. Đăng ký khai sinh"

5. **Config đã có thresholds (CHƯA DÙNG)**
   - `LOW_CONFIDENCE_THRESHOLD=0.5`
   - `MEDIUM_CONFIDENCE_THRESHOLD=0.65`
   - `HIGH_CONFIDENCE_THRESHOLD=0.8`

### ❌ Những gì THIẾU:

1. **PostgreSQL connection trong query-service**

   - Hiện chỉ dùng HTTP clients (httpx)
   - Cần add `psycopg2` để query documents table

2. **Models cho clarification**

   - `DocumentOption` (document info for user selection)
   - `ConfirmRequest` (user's document selection)
   - Update `QueryResponse` (add clarification fields)

3. **Logic check confidence & group documents**

   - Check `max_rerank_score < THRESHOLD`
   - Group chunks by `document_id`
   - Fetch titles from PostgreSQL

4. **Endpoint `/query/confirm`**

   - Accept document selection
   - Re-query with filter
   - Generate answer

5. **Database helper module**
   - `query-service/src/database.py` (NEW FILE)
   - PostgreSQL connection pool
   - Batch fetch document titles

---

## 🔨 IMPLEMENTATION PLAN

### **Phase 1: Setup & Models** (2 hours)

#### ✅ TODO 1.1: Add PostgreSQL dependency

**File**: `query-service/requirements.txt`

```diff
+ psycopg2-binary==2.9.9
```

**Action**:

- Add dependency
- Rebuild Docker image

**Test**: `docker exec legalrag-query pip list | grep psycopg2`

---

#### ✅ TODO 1.2: Add PostgreSQL config

**File**: `query-service/src/config.py`

**Changes**:

```python
class Settings(BaseSettings):
    # ... existing ...

    # PostgreSQL for document metadata
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "legalrag"
    POSTGRES_PASSWORD: str = "legalrag"
    POSTGRES_DB: str = "legalrag"

    # Clarification threshold (reuse existing)
    CLARIFICATION_THRESHOLD: float = 0.7  # Below this → show options
```

**File**: `query-service/.env`

```diff
+ # PostgreSQL connection (for document metadata)
+ POSTGRES_HOST=postgres
+ POSTGRES_PORT=5432
+ POSTGRES_USER=legalrag
+ POSTGRES_PASSWORD=legalrag
+ POSTGRES_DB=legalrag
+
+ # Clarification (reuse existing thresholds)
+ CLARIFICATION_THRESHOLD=0.7
```

**Test**: Print `settings.POSTGRES_HOST` in startup

---

#### ✅ TODO 1.3: Create database helper module

**File**: `query-service/src/database.py` (NEW)

**Content**:

```python
"""
PostgreSQL Database Helper
Fetch document metadata from main database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    """PostgreSQL client for document metadata"""

    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname
        }

    def fetch_document_titles(self, doc_ids: List[str]) -> Dict[str, str]:
        """
        Batch fetch document titles

        Args:
            doc_ids: List of document UUIDs

        Returns:
            Dict mapping document_id → title
        """
        if not doc_ids:
            return {}

        try:
            conn = psycopg2.connect(**self.config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Use ANY for PostgreSQL array matching
            cursor.execute(
                "SELECT id, title FROM documents WHERE id = ANY(%s)",
                (doc_ids,)
            )

            results = cursor.fetchall()

            # Convert to dict
            title_map = {str(row['id']): row['title'] for row in results}

            cursor.close()
            conn.close()

            logger.info(f"✅ Fetched {len(title_map)} document titles")
            return title_map

        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            return {}
```

**Test**:

```python
client = DatabaseClient(...)
titles = client.fetch_document_titles(["2dee00cd-99a1-4b96-9c1a-121274266f46"])
assert "khai sinh" in titles.values()[0].lower()
```

---

#### ✅ TODO 1.4: Update models

**File**: `query-service/src/main.py`

**Add new models** (after line 20):

```python
class DocumentOption(BaseModel):
    """Document option for clarification"""
    document_id: str
    title: str
    chunk_count: int
    confidence: float
    preview: str


class ConfirmRequest(BaseModel):
    """User confirms document selection"""
    question: str
    document_id: str
    history: Optional[List[dict]] = None  # For Phase 2
```

**Update QueryResponse** (line 33):

```python
class QueryResponse(BaseModel):
    """Query response with optional clarification"""
    success: bool
    question: str
    answer: Optional[str] = None  # ← Changed to Optional

    # Clarification fields
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    document_options: Optional[List[DocumentOption]] = None

    sources: List[SearchResult]
    tokens_used: int
```

**Test**: Import models, no syntax errors

---

### **Phase 2: Core Logic** (3 hours)

#### ✅ TODO 2.1: Initialize database client

**File**: `query-service/src/main.py`

**Add after line 16** (after imports):

```python
from .database import DatabaseClient

# Global clients
http_client = None
db_client = None  # NEW
```

**Update startup** (line 72):

```python
@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global http_client, db_client

    http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize PostgreSQL client
    db_client = DatabaseClient(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB
    )

    logger.info("✅ Query Service started (with DB client)")
```

**Test**: Start service, check logs for "with DB client"

---

#### ✅ TODO 2.2: Add helper function - group_chunks_by_document

**File**: `query-service/src/main.py`

**Add after line 200** (after generate_answer):

```python
def group_chunks_by_document(chunks: List[dict]) -> Dict[str, List[dict]]:
    """
    Group chunks by document_id

    Args:
        chunks: List of chunks with document_id field

    Returns:
        Dict mapping document_id → list of chunks
    """
    from collections import defaultdict

    groups = defaultdict(list)
    for chunk in chunks:
        doc_id = chunk.get('document_id')
        if doc_id:
            groups[doc_id].append(chunk)

    return dict(groups)
```

**Test**:

```python
chunks = [
    {"document_id": "uuid-1", "content": "A"},
    {"document_id": "uuid-1", "content": "B"},
    {"document_id": "uuid-2", "content": "C"},
]
groups = group_chunks_by_document(chunks)
assert len(groups) == 2
assert len(groups["uuid-1"]) == 2
```

---

#### ✅ TODO 2.3: Update /query endpoint - Add confidence check

**File**: `query-service/src/main.py`

**Location**: After line 287 (after rerank step)

**Add confidence check logic**:

```python
# Step 3: Rerank documents for better relevance
logger.info("Step 3: Reranking documents...")
reranked_results = await rerank_documents(request.question, search_results, top_k=5)

# === NEW: Step 3.5: Check confidence ===
max_score = max(r.get('rerank_score', 0) for r in reranked_results)
logger.info(f"📊 Max confidence: {max_score:.3f}")

if max_score < settings.CLARIFICATION_THRESHOLD:
    # LOW CONFIDENCE → CLARIFICATION FLOW
    logger.info("❓ Low confidence → Showing document options")

    # Group by document
    doc_groups = group_chunks_by_document(reranked_results)

    # Fetch titles
    doc_ids = list(doc_groups.keys())
    titles = db_client.fetch_document_titles(doc_ids)

    # Create options
    options = []
    for doc_id, chunks in doc_groups.items():
        max_chunk_score = max(c.get('rerank_score', 0) for c in chunks)

        options.append(DocumentOption(
            document_id=doc_id,
            title=titles.get(doc_id, "Văn bản"),
            chunk_count=len(chunks),
            confidence=max_chunk_score,
            preview=chunks[0].get('content', '')[:150] + "..."
        ))

    # Sort by confidence
    options.sort(key=lambda x: x.confidence, reverse=True)

    return QueryResponse(
        success=True,
        question=request.question,
        answer=None,  # ← NULL when clarifying
        needs_clarification=True,
        clarification_message="Tôi tìm thấy các văn bản có thể liên quan. Bạn muốn xem văn bản nào?",
        document_options=options[:3],  # Top 3
        sources=[],
        tokens_used=0
    )

# HIGH CONFIDENCE → Continue with existing flow
logger.info("✅ High confidence → Answering directly")

# Step 4: Build context from reranked results (EXISTING CODE)
context_parts = []
...
```

**Test**:

- Query với confidence < 0.7 → Nhận clarification
- Query với confidence ≥ 0.7 → Nhận answer trực tiếp

---

### **Phase 3: Confirmation Endpoint** (2 hours)

#### ✅ TODO 3.1: Create /query/confirm endpoint

**File**: `query-service/src/main.py`

**Add after /query endpoint** (before root endpoint):

```python
@app.post("/query/confirm", response_model=QueryResponse)
async def query_confirm(request: ConfirmRequest):
    """
    Handle user's document selection

    Flow:
    1. Embed original question
    2. Search with document_id filter
    3. Rerank filtered results
    4. Generate answer
    """

    logger.info(f"✅ User confirmed document: {request.document_id}")

    # Step 1: Embed
    embedding = await embed_text(request.question)
    if not embedding:
        raise HTTPException(503, "Embedding service unavailable")

    # Step 2: Search with document filter
    response = await http_client.post(
        f"{settings.VECTOR_SERVICE_URL}/search",
        json={
            "embedding": embedding,
            "top_k": 20,  # More results for better context
            "threshold": 0.3,  # Lower threshold (already filtered)
            "document_ids": [request.document_id]  # ← FILTER!
        }
    )

    if response.status_code != 200:
        logger.error(f"Vector search failed: {response.text}")
        raise HTTPException(503, "Vector search failed")

    search_results = response.json().get("results", [])

    if not search_results:
        return QueryResponse(
            success=True,
            question=request.question,
            answer="Xin lỗi, không tìm thấy thông tin trong văn bản đã chọn.",
            needs_clarification=False,
            sources=[],
            tokens_used=0
        )

    # Step 3: Rerank (all chunks from same document)
    reranked_results = await rerank_documents(
        request.question,
        search_results,
        top_k=5
    )

    # Step 4: Build context
    context_parts = []
    for result in reranked_results:
        content = result['content']
        section = result.get('section_title', '')

        if section:
            context_parts.append(f"[{section}]\n{content}")
        else:
            context_parts.append(content)

    context = "\n\n---\n\n".join(context_parts)

    # Step 5: Generate answer
    answer = await generate_answer(request.question, context)

    if not answer:
        raise HTTPException(503, "LLM service unavailable")

    return QueryResponse(
        success=True,
        question=request.question,
        answer=answer,
        needs_clarification=False,
        sources=[
            SearchResult(
                content=r['content'],
                similarity=r.get('rerank_score', 0)
            )
            for r in reranked_results
        ],
        tokens_used=0
    )
```

**Test**:

```bash
curl -X POST http://localhost:8002/query/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "question": "kết hôn cần gì",
    "document_id": "2dee00cd-99a1-4b96-9c1a-121274266f46"
  }'
```

---

#### ✅ TODO 3.2: Update root endpoint docs

**File**: `query-service/src/main.py`

**Update root()** (line 345):

```python
@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "query-service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "POST /query",
            "query_confirm": "POST /query/confirm",  # NEW
            "docs": "/docs"
        }
    }
```

---

### **Phase 4: Testing & Deployment** (2 hours)

#### ✅ TODO 4.1: Create test script

**File**: `query-service/test_clarification.py` (NEW)

```python
"""
Test clarification flow
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8002"

async def test_low_confidence():
    """Test: Low confidence → Clarification"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={"question": "giấy tờ"}  # Vague question
        )

        data = response.json()
        print("Test 1: Low confidence")
        print(f"  needs_clarification: {data.get('needs_clarification')}")
        print(f"  options: {len(data.get('document_options', []))}")
        assert data['needs_clarification'] == True
        print("  ✅ PASS\n")

async def test_high_confidence():
    """Test: High confidence → Direct answer"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={"question": "điều kiện đăng ký khai sinh"}  # Specific
        )

        data = response.json()
        print("Test 2: High confidence")
        print(f"  needs_clarification: {data.get('needs_clarification')}")
        print(f"  answer: {data.get('answer')[:50]}...")
        assert data['needs_clarification'] == False
        print("  ✅ PASS\n")

async def test_confirmation():
    """Test: User confirms document"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/query/confirm",
            json={
                "question": "thủ tục khai sinh",
                "document_id": "2dee00cd-99a1-4b96-9c1a-121274266f46"
            }
        )

        data = response.json()
        print("Test 3: Confirmation")
        print(f"  answer: {data.get('answer')[:50]}...")
        assert data['answer'] is not None
        print("  ✅ PASS\n")

async def main():
    await test_low_confidence()
    await test_high_confidence()
    await test_confirmation()
    print("🎉 All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run**: `python query-service/test_clarification.py`

---

#### ✅ TODO 4.2: Update Dockerfile & rebuild

**File**: `query-service/Dockerfile`

**Check if psycopg2-binary is installed**:

```dockerfile
# Should have:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Rebuild**:

```bash
cd D:\Personal\LegalRAG
docker-compose build query-service
docker-compose up -d query-service
```

**Test**: `docker logs legalrag-query --tail 20`

---

#### ✅ TODO 4.3: Integration test with real data

**Test scenarios**:

1. **Scenario 1: Low confidence (vague)**

   ```
   Question: "giấy tờ"
   Expected: needs_clarification=True, 1-3 options
   ```

2. **Scenario 2: High confidence (specific)**

   ```
   Question: "điều kiện đăng ký khai sinh"
   Expected: needs_clarification=False, direct answer
   ```

3. **Scenario 3: Confirmation**
   ```
   Question: "thủ tục khai sinh"
   Document: "01. Đăng ký khai sinh"
   Expected: Answer with filtered context
   ```

---

### **Phase 5: Documentation** (1 hour)

#### ✅ TODO 5.1: Update API docs

**File**: `query-service/README.md`

**Add section**:

````markdown
## Clarification Flow

When confidence is low (<0.7), system shows document options:

### Request:

```json
POST /query
{
  "question": "giấy tờ"
}
```
````

### Response (Clarification):

```json
{
  "success": true,
  "question": "giấy tờ",
  "answer": null,
  "needs_clarification": true,
  "clarification_message": "Tôi tìm thấy các văn bản...",
  "document_options": [
    {
      "document_id": "uuid",
      "title": "Đăng ký khai sinh",
      "chunk_count": 15,
      "confidence": 0.65,
      "preview": "..."
    }
  ]
}
```

### User Confirms:

```json
POST /query/confirm
{
  "question": "giấy tờ",
  "document_id": "uuid"
}
```

### Response (Answer):

```json
{
  "success": true,
  "answer": "Giấy tờ cần thiết...",
  "needs_clarification": false
}
```

````

---

#### ✅ TODO 5.2: Update CHANGELOG
**File**: `CHANGELOG.md`

```markdown
## [Unreleased] - 2025-11-24

### Added
- **Clarification System**: Smart document selection when confidence < 0.7
- `/query/confirm` endpoint for user document selection
- PostgreSQL integration for document metadata
- `DocumentOption` and `ConfirmRequest` models

### Changed
- `QueryResponse.answer` now Optional (NULL when clarifying)
- `/query` endpoint checks confidence before answering

### Technical
- Added `psycopg2-binary` dependency
- Created `database.py` module for PostgreSQL queries
- Batch fetch document titles (1 query for all docs)
````

---

## 📋 CHECKLIST TỔNG HỢP

### ✅ Code Changes

- [ ] Add `psycopg2-binary` to requirements.txt
- [ ] Add PostgreSQL config to config.py & .env
- [ ] Create `database.py` with DatabaseClient
- [ ] Add models: DocumentOption, ConfirmRequest
- [ ] Update QueryResponse (answer → Optional)
- [ ] Initialize db_client in startup
- [ ] Add `group_chunks_by_document` helper
- [ ] Update `/query` with confidence check
- [ ] Create `/query/confirm` endpoint
- [ ] Update root endpoint docs

### ✅ Testing

- [ ] Unit test: group_chunks_by_document
- [ ] Unit test: DatabaseClient.fetch_document_titles
- [ ] Integration test: Low confidence → clarification
- [ ] Integration test: High confidence → direct answer
- [ ] Integration test: User confirmation → filtered answer
- [ ] Load test: 100 concurrent requests

### ✅ Deployment

- [ ] Rebuild Docker image
- [ ] Update docker-compose.yml (if needed)
- [ ] Deploy to staging
- [ ] Smoke test on staging
- [ ] Deploy to production

### ✅ Documentation

- [ ] Update README.md with clarification flow
- [ ] Update API docs
- [ ] Update CHANGELOG.md
- [ ] Create troubleshooting guide

---

## 🎯 SUCCESS CRITERIA

1. **Functional**:

   - ✅ Low confidence queries show 1-3 document options
   - ✅ High confidence queries answer directly
   - ✅ User can select document and get filtered answer
   - ✅ No errors in logs

2. **Performance**:

   - ✅ Clarification response < 500ms
   - ✅ Confirmation response < 2s (full RAG pipeline)
   - ✅ Database query < 50ms (batch fetch)

3. **UX**:
   - ✅ Clear message: "Tôi tìm thấy các văn bản..."
   - ✅ Document titles readable (not UUIDs)
   - ✅ Confidence scores shown
   - ✅ Preview text helpful

---

## 🚀 TIMELINE

- **Day 1 Morning** (2h): Phase 1 - Setup & Models
- **Day 1 Afternoon** (3h): Phase 2 - Core Logic
- **Day 2 Morning** (2h): Phase 3 - Confirmation Endpoint
- **Day 2 Afternoon** (3h): Phase 4 - Testing & Deployment
- **Day 3 Morning** (1h): Phase 5 - Documentation

**Total**: ~11 hours over 3 days

---

## 🔧 TROUBLESHOOTING

### Issue: Database connection failed

```
Check: settings.POSTGRES_HOST, POSTGRES_PORT
Test: docker exec legalrag-postgres psql -U legalrag -d legalrag -c "\l"
```

### Issue: No clarification triggered

```
Check: settings.CLARIFICATION_THRESHOLD
Debug: Print max_score in logs
Adjust: Lower threshold if needed
```

### Issue: Empty document_options

```
Check: db_client.fetch_document_titles returns data
Debug: Print doc_ids before fetch
Verify: Documents exist in database
```

---

**Ready to start? Let's begin with Phase 1! 🎯**
