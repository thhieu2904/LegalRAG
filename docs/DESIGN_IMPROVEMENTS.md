# LegalRAG Design Improvements Report

**Date**: November 23, 2025  
**Status**: Analysis & Recommendations  
**Priority**: High

---

## 🎯 OVERVIEW

Hai vấn đề thiết kế cốt lõi cần giải quyết:

1. **Low Confidence Clarification**: Khi similarity < 0.5, cần hỏi lại user thông minh
2. **Rerank Same-Document Logic**: Đảm bảo chỉ trả về chunks từ 1 văn bản duy nhất

---

## 📊 CASE 1: Low Confidence Clarification Strategy

### Problem Statement

- **Current**: Khi similarity < 0.5 → "No relevant documents found"
- **Issue**: User experience kém, mất thông tin có thể hữu ích
- **Goal**: Smart clarification như `clarification.py` nhưng đơn giản hơn

### Proposed Solution: 3-Layer Clarification

#### Layer 1: Document Grouping (0.3-0.5 confidence)

```
User Query: "làm thủ tục gì để kết hôn"
Similarity: 0.45 (LOW)

Response:
┌─────────────────────────────────────────┐
│ Tôi tìm thấy 5 đoạn văn bản có thể     │
│ liên quan đến câu hỏi của bạn:          │
│                                          │
│ 1. [Đăng ký kết hôn] - 3 đoạn          │
│    - Thủ tục kết hôn (47%)              │
│    - Hồ sơ kết hôn (44%)                │
│    - Địa điểm đăng ký (39%)             │
│                                          │
│ 2. [Ly hôn] - 2 đoạn                   │
│    - Điều kiện ly hôn (35%)             │
│    - Thủ tục ly hôn (33%)               │
│                                          │
│ Bạn muốn tìm hiểu về:                   │
│ [1] Đăng ký kết hôn                     │
│ [2] Ly hôn                              │
│ [3] Cả hai                              │
│ [4] Không phải những thứ này            │
└─────────────────────────────────────────┘
```

#### Layer 2: Question Drilling (if user picks option)

```
User picks: [1] Đăng ký kết hôn

Response:
┌─────────────────────────────────────────┐
│ Về đăng ký kết hôn, bạn muốn biết:     │
│                                          │
│ [A] Thủ tục đăng ký như thế nào?        │
│ [B] Cần giấy tờ gì?                     │
│ [C] Đăng ký ở đâu?                      │
│ [D] Mất bao lâu?                        │
│ [E] Lệ phí bao nhiêu?                   │
└─────────────────────────────────────────┘
```

#### Layer 3: Direct Answer

```
User picks: [B] Cần giấy tờ gì?

Response: [Full RAG answer với context từ chunks về hồ sơ kết hôn]
```

### Implementation Plan

#### Step 1: Add Clarification Models

```python
# query-service/src/models.py

class DocumentGroup(BaseModel):
    """Group of chunks from same document"""
    document_title: str
    document_id: str
    chunk_count: int
    chunks: List[Dict[str, Any]]
    max_similarity: float
    avg_similarity: float

class ClarificationOption(BaseModel):
    """User selection option"""
    id: str
    label: str
    description: str

class ClarificationResponse(BaseModel):
    """Low confidence clarification response"""
    success: bool = True
    question: str
    clarification_type: str  # "document_grouping" | "question_drilling"
    message: str
    document_groups: Optional[List[DocumentGroup]] = None
    options: List[ClarificationOption]
    session_id: str  # Track clarification conversation
```

#### Step 2: Add Clarification Logic to Query Service

```python
# query-service/src/main.py

from .clarification import ClarificationService

clarification_service = ClarificationService()

@app.post("/query")
async def query(request: QueryRequest):
    # ... existing code ...

    search_results = await search_vectors(embedding)

    if not search_results:
        return no_results_response()

    # Check confidence
    max_similarity = max(r.get('similarity', 0) for r in search_results)

    # LOW CONFIDENCE: Document grouping clarification
    if max_similarity < settings.LOW_CONFIDENCE_THRESHOLD:
        return clarification_service.generate_document_grouping(
            question=request.question,
            search_results=search_results,
            session_id=request.session_id
        )

    # MEDIUM: Direct answer but may ask follow-up
    elif max_similarity < settings.MEDIUM_CONFIDENCE_THRESHOLD:
        # Generate answer + suggest related topics
        pass

    # HIGH: Direct answer
    else:
        # Normal RAG flow
        pass
```

#### Step 3: Create Clarification Service

```python
# query-service/src/clarification.py

class ClarificationService:
    def generate_document_grouping(
        self,
        question: str,
        search_results: List[Dict],
        session_id: str
    ) -> ClarificationResponse:
        """
        Group chunks by document and create clarification options
        """
        # 1. Group by document_id
        groups = self._group_by_document(search_results)

        # 2. Rank groups by relevance
        ranked_groups = self._rank_groups(groups)

        # 3. Create options
        options = [
            ClarificationOption(
                id=f"doc_{group.document_id}",
                label=group.document_title,
                description=f"{group.chunk_count} đoạn văn bản liên quan"
            )
            for group in ranked_groups[:3]  # Top 3
        ]

        # 4. Add meta options
        options.extend([
            ClarificationOption(
                id="all",
                label="Tất cả các văn bản trên",
                description="Tìm kiếm trong tất cả"
            ),
            ClarificationOption(
                id="none",
                label="Không phải những thứ này",
                description="Tôi cần tìm thứ khác"
            )
        ])

        return ClarificationResponse(
            question=question,
            clarification_type="document_grouping",
            message="Tôi tìm thấy các văn bản có thể liên quan:",
            document_groups=ranked_groups,
            options=options,
            session_id=session_id or generate_session_id()
        )
```

### Advantages

✅ **User-friendly**: Không bỏ query mơ hồ, hỗ trợ user refine  
✅ **Transparent**: User thấy rõ hệ thống tìm được gì  
✅ **Scalable**: Dễ thêm Layer 2 (question drilling) sau  
✅ **Stateless**: Có thể làm với session_id hoặc không

### Disadvantages

❌ **Complexity**: Cần state management nếu multi-turn  
❌ **Extra API calls**: Frontend cần handle clarification flow  
❌ **UX design**: Cần thiết kế UI/UX cho clarification options

### Effort Estimate

- **Backend**: 4-6 hours (models + service + tests)
- **Frontend**: 6-8 hours (clarification UI components)
- **Testing**: 2-3 hours
- **Total**: ~15 hours

---

## 🎯 CASE 2: Rerank Same-Document Logic

### Problem Statement

- **Current**: Rerank service trả về top 5 chunks bất kể từ document nào
- **Issue**: LLM nhận chunks từ nhiều văn bản → context rối, hallucination
- **Goal**: Chỉ trả về chunks từ **1 văn bản duy nhất** (top scoring document)

### Current Rerank Flow

```
Input: 10 chunks
[Doc A - chunk 1] similarity: 0.67
[Doc A - chunk 2] similarity: 0.65
[Doc B - chunk 1] similarity: 0.64  ← Problem: Mixed documents
[Doc A - chunk 3] similarity: 0.63
[Doc B - chunk 2] similarity: 0.62
...

Rerank Output: Top 5
[Doc A - chunk 1] rerank: 0.82
[Doc B - chunk 1] rerank: 0.79  ← WRONG: Different document
[Doc A - chunk 2] rerank: 0.77
[Doc A - chunk 3] rerank: 0.71
[Doc B - chunk 2] rerank: 0.68  ← WRONG: Different document
```

### Proposed Solution: Document-First Reranking

#### Algorithm

```
1. Group search results by document_id
2. Calculate aggregate score for each document
   - Option A: Max rerank score
   - Option B: Average top-3 rerank scores
   - Option C: Weighted sum (position + rerank)
3. Pick TOP document
4. Return ALL chunks from that document (up to RERANK_TOP_K)
```

#### Implementation

**Step 1: Update Rerank Request Model**

```python
# rerank-service/src/models.py

class RerankRequest(BaseModel):
    query: str
    documents: List[str]  # Chunk contents
    document_ids: List[str]  # NEW: Track which doc each chunk belongs to
    top_k: int = 5
    same_document_only: bool = True  # NEW: Filter to single document
```

**Step 2: Add Document Filtering Logic**

```python
# rerank-service/src/reranker.py

class VietnameseReranker:
    def rerank_with_document_filter(
        self,
        query: str,
        documents: List[str],
        document_ids: List[str],
        top_k: int = 5,
        same_document_only: bool = True
    ) -> List[RerankResult]:
        """
        Rerank and filter to single document
        """
        # 1. Rerank all chunks
        all_results = self._rerank_all(query, documents)

        if not same_document_only:
            return all_results[:top_k]

        # 2. Group by document
        doc_groups = defaultdict(list)
        for i, result in enumerate(all_results):
            doc_id = document_ids[result.index]
            doc_groups[doc_id].append(result)

        # 3. Calculate document scores
        doc_scores = {}
        for doc_id, chunks in doc_groups.items():
            # Option B: Average top-3
            top_3 = sorted(chunks, key=lambda x: x.score, reverse=True)[:3]
            doc_scores[doc_id] = sum(c.score for c in top_3) / len(top_3)

        # 4. Pick best document
        best_doc = max(doc_scores.items(), key=lambda x: x[1])[0]

        # 5. Return chunks from best document only
        best_chunks = doc_groups[best_doc]
        return sorted(best_chunks, key=lambda x: x.score, reverse=True)[:top_k]
```

**Step 3: Update Query Service to Pass document_ids**

```python
# query-service/src/main.py

async def rerank_documents(query: str, documents: List[dict], top_k: int = 5):
    # Extract document IDs
    doc_ids = [doc.get('document_id', 'unknown') for doc in documents]
    doc_texts = [doc.get('content', '') for doc in documents]

    response = await http_client.post(
        f"{settings.RERANK_SERVICE_URL}/rerank",
        json={
            "query": query,
            "documents": doc_texts,
            "document_ids": doc_ids,  # NEW
            "top_k": top_k,
            "same_document_only": settings.RERANK_SAME_DOCUMENT_ONLY  # NEW
        }
    )

    # ... process results
```

### Example Output

```
BEFORE (mixed documents):
[Doc A - chunk 1] rerank: 0.82
[Doc B - chunk 1] rerank: 0.79  ❌
[Doc A - chunk 2] rerank: 0.77
[Doc A - chunk 3] rerank: 0.71
[Doc B - chunk 2] rerank: 0.68  ❌

AFTER (single document):
Document A selected (avg score: 0.77)
[Doc A - chunk 1] rerank: 0.82
[Doc A - chunk 2] rerank: 0.77
[Doc A - chunk 3] rerank: 0.71
[Doc A - chunk 5] rerank: 0.69
[Doc A - chunk 4] rerank: 0.65
```

### Advantages

✅ **Coherent context**: LLM nhận context từ 1 văn bản duy nhất  
✅ **Less hallucination**: Không mix thông tin từ nhiều nguồn  
✅ **Better citations**: Dễ trích dẫn khi tất cả từ 1 document  
✅ **Configurable**: ENV flag để bật/tắt

### Disadvantages

❌ **May miss relevant info**: Nếu câu hỏi cần nhiều documents  
❌ **Score bias**: Document với nhiều chunks có lợi thế

### Mitigation

- Add `ALLOW_MULTI_DOCUMENT` mode cho query đặc biệt
- Frontend có button "Tìm trong tất cả văn bản" nếu không hài lòng
- Log document selection để analyze quality

### Effort Estimate

- **Backend rerank service**: 2-3 hours
- **Query service integration**: 1-2 hours
- **Testing**: 1-2 hours
- **Total**: ~6 hours

---

## 🚀 IMPLEMENTATION PRIORITY

### Phase 1: Quick Wins (This week)

✅ ENV configuration (DONE)

- [ ] Rerank same-document logic (6 hours)
- [ ] Test với existing documents

### Phase 2: Enhanced UX (Next sprint)

- [ ] Low confidence clarification - Backend (6 hours)
- [ ] Low confidence clarification - Frontend (8 hours)
- [ ] Integration testing (3 hours)

### Phase 3: Polish & Scale

- [ ] Multi-document mode toggle
- [ ] Advanced question drilling
- [ ] Analytics dashboard for clarification effectiveness

---

## 📝 NOTES & CONSIDERATIONS

### About Clarification.py

File `clarification.py` reference là từ RAG V1 với:

- ✅ Good: 5-layer confidence system, smart question generation
- ❌ Complex: Cache management, collection routing, nhiều dependencies
- ✅ Take: Concept of document grouping và question drilling
- ❌ Leave: Heavy collection logic, không phù hợp single-collection setup hiện tại

### About Rerank Build Error

Cần check Dockerfile rerank-service:

- Có thể là CUDA library version mismatch
- Có thể cần downgrade transformers/torch version
- Log: "unable to locate package libcudnn8"

**Recommended fix**: Use CPU-only image cho rerank (model nhỏ, CPU đủ nhanh)

---

## 🎯 DECISION POINTS

### For Low Confidence Clarification

**Question**: Multi-turn conversation hay single-shot clarification?

- **Multi-turn**: Phức tạp hơn, cần session management
- **Single-shot**: Đơn giản, stateless, nhưng kém interactive

**Recommendation**: Bắt đầu với single-shot, có thể upgrade sau

### For Rerank Same-Document

**Question**: Strict (luôn 1 document) hay flexible (có toggle)?

- **Strict**: An toàn, dễ kiểm soát quality
- **Flexible**: User experience tốt hơn cho edge cases

**Recommendation**: Default strict, có ENV flag để override nếu cần

---

## 📊 SUCCESS METRICS

### Clarification

- **User satisfaction**: % users chọn option vs bỏ qua
- **Conversion rate**: % clarification → successful answer
- **False positive**: % clarification không cần thiết (user annoyed)

### Same-Document Rerank

- **Hallucination rate**: Giảm mentions về unrelated topics
- **Citation accuracy**: % citations đúng văn bản
- **User feedback**: Thumbs up/down on answers

---

## 🔗 RELATED FILES

- `/query-service/src/config.py` - ENV settings (UPDATED)
- `/query-service/.env` - Thresholds configuration (UPDATED)
- `/rerank-service/src/main.py` - Rerank logic (TO UPDATE)
- `/rerank-service/src/reranker.py` - Core reranker (TO UPDATE)
- `/query-service/src/main.py` - Query flow (TO UPDATE)

---

**End of Report**  
Đọc xong có questions hoặc muốn implement phần nào thì báo nhé! 🚀
