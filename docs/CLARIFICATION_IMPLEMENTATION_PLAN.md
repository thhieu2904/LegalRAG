# 🎯 CLARIFICATION SYSTEM - IMPLEMENTATION PLAN

**Date**: November 24, 2025  
**Project**: LegalRAG v2  
**Scope**: Smart Clarification cho 166 văn bản pháp luật

---

## 📊 PHÂN TÍCH HỆ THỐNG HIỆN TẠI

### Database Structure

**166 Documents** được lưu trong:

```
data/storage/collections/
├── collection_001/
│   └── metadata.json  # Danh sách documents
│       documents: [
│         {
│           "id": "doc_001",
│           "title": "Luật Hôn Nhân Gia Đình",
│           "code": "52/2014/QH13",
│           "effective_date": "2015-01-01",
│           "keywords": ["kết hôn", "ly hôn", ...],
│           ...
│         }
│       ]
└── collection_002/
    └── ...
```

**Vector Database** (PostgreSQL pgvector):

```sql
chunks:
  - id (uuid)
  - document_id (string)
  - chunk_index (int)
  - content (text)
  - section_title (text)
  - embedding (vector)
  - metadata (jsonb)
    {
      "document_title": "...",
      "document_code": "...",
      "keywords": [...],
      "processing_time": "...",
      "fee_info": "..."
    }
```

**Search Results Structure**:

```python
search_results = [
    {
        'content': 'Điều 8: Điều kiện kết hôn...',
        'document_id': 'doc_123',
        'document_title': 'Luật Hôn Nhân',
        'document_code': '52/2014/QH13',
        'similarity': 0.72,  # After vector search
        'rerank_score': 0.89,  # After rerank
        'metadata': {...}
    },
    ...
]
```

---

## 🎯 VẤN ĐỀ VÀ GIẢI PHÁP

### Vấn đề 1: ENV Configuration

**❌ Hiện tại**: Thresholds có trong config nhưng không dùng

```python
# query-service/src/config.py
LOW_CONFIDENCE_THRESHOLD: float = 0.5  # Không sử dụng
MEDIUM_CONFIDENCE_THRESHOLD: float = 0.65  # Không sử dụng
```

**✅ Giải pháp**: ENV-driven configuration với STRICT validation

```bash
# query-service/.env

# ============================================
# CLARIFICATION THRESHOLDS
# ============================================

# Confidence levels (MUST be in ascending order)
CLARITY_LOW_THRESHOLD=0.50           # Below: Không tìm thấy → Thu thập context
CLARITY_MEDIUM_THRESHOLD=0.65        # 0.50-0.65: Nhiều văn bản → Hỏi chọn
CLARITY_HIGH_THRESHOLD=0.80          # 0.65-0.80: Khá chắc → Xác nhận
                                      # Above 0.80: Rất chắc → Trả lời trực tiếp

# Clarification behavior
CLARITY_ENABLED=true                  # Enable/disable clarification
CLARITY_RESPONSE_TYPE=embedded        # "embedded" | "modal" (xem phần 3)
CLARITY_MAX_OPTIONS=5                 # Max options to show
CLARITY_GROUP_BY=document             # "document" | "collection"

# Error handling (STRICT - NO FALLBACK)
CLARITY_STRICT_MODE=true              # Raise errors instead of fallback
CLARITY_LOG_LEVEL=DEBUG               # Detailed logging for debugging
```

**Validation Code**:

```python
# query-service/src/config.py
class Settings(BaseSettings):
    # ... existing ...

    # Clarification thresholds
    CLARITY_LOW_THRESHOLD: float = 0.50
    CLARITY_MEDIUM_THRESHOLD: float = 0.65
    CLARITY_HIGH_THRESHOLD: float = 0.80
    CLARITY_ENABLED: bool = True
    CLARITY_RESPONSE_TYPE: str = "embedded"  # "embedded" | "modal"
    CLARITY_MAX_OPTIONS: int = 5
    CLARITY_GROUP_BY: str = "document"  # "document" | "collection"
    CLARITY_STRICT_MODE: bool = True
    CLARITY_LOG_LEVEL: str = "DEBUG"

    @validator('CLARITY_MEDIUM_THRESHOLD')
    def validate_medium_threshold(cls, v, values):
        if 'CLARITY_LOW_THRESHOLD' in values and v <= values['CLARITY_LOW_THRESHOLD']:
            raise ValueError(
                f"CLARITY_MEDIUM_THRESHOLD ({v}) must be > CLARITY_LOW_THRESHOLD ({values['CLARITY_LOW_THRESHOLD']})"
            )
        return v

    @validator('CLARITY_HIGH_THRESHOLD')
    def validate_high_threshold(cls, v, values):
        if 'CLARITY_MEDIUM_THRESHOLD' in values and v <= values['CLARITY_MEDIUM_THRESHOLD']:
            raise ValueError(
                f"CLARITY_HIGH_THRESHOLD ({v}) must be > CLARITY_MEDIUM_THRESHOLD ({values['CLARITY_MEDIUM_THRESHOLD']})"
            )
        return v

    @validator('CLARITY_RESPONSE_TYPE')
    def validate_response_type(cls, v):
        if v not in ['embedded', 'modal']:
            raise ValueError("CLARITY_RESPONSE_TYPE must be 'embedded' or 'modal'")
        return v
```

**🔥 CHẤP NHẬN BÁO LỖI - KHÔNG FALLBACK**:

```python
# query-service/src/clarification.py

class ClarificationError(Exception):
    """Base exception for clarification errors"""
    pass

class ThresholdConfigError(ClarificationError):
    """Threshold configuration error"""
    pass

class DocumentGroupingError(ClarificationError):
    """Error during document grouping"""
    pass

# Trong code:
if not settings.CLARITY_ENABLED:
    raise ClarificationError(
        "Clarification disabled. Set CLARITY_ENABLED=true in .env"
    )

if max_similarity < 0 or max_similarity > 1:
    raise ValueError(f"Invalid similarity score: {max_similarity}")
```

---

### Vấn đề 2: Xử lý 166 văn bản với nhiều chunks

**Thực tế**: Query "kết hôn" → 50 chunks từ 10 văn bản khác nhau

- 15 chunks: Luật Hôn Nhân (similarity 0.65-0.80)
- 12 chunks: Luật Hộ Tịch (similarity 0.55-0.70)
- 8 chunks: Bộ Luật Dân Sự (similarity 0.50-0.65)
- ...

**❌ Sai lầm thường gặp**: Hiển thị 50 chunks riêng lẻ
**✅ Đúng**: Group by document, aggregate scores, prioritize

#### Strategy: Document-First Clarification

```python
# query-service/src/clarification.py

class DocumentGroup(BaseModel):
    """Grouped chunks from same document"""
    document_id: str
    document_title: str
    document_code: str
    chunk_count: int
    max_similarity: float  # Highest chunk similarity
    avg_similarity: float  # Average similarity
    top_chunks: List[Dict]  # Top 3 chunks for preview
    all_chunk_ids: List[str]  # All chunk IDs for later retrieval

class ClarificationOption(BaseModel):
    """User selection option"""
    id: str  # "doc_001" | "collection_002" | "manual"
    type: str  # "document" | "collection" | "manual_input"
    title: str  # "Luật Hôn Nhân Gia Đình"
    description: str  # "15 đoạn văn bản (độ phù hợp: 72%)"
    confidence: float  # 0.72
    preview: Optional[str]  # Top chunk content preview
    metadata: Dict  # Document metadata

def group_by_document(
    search_results: List[Dict],
    max_options: int = 5
) -> List[DocumentGroup]:
    """
    Group chunks by document and calculate aggregate scores

    Strategy for LEGAL documents:
    1. Group by document_id
    2. Calculate aggregate score (weighted average of top-3 chunks)
    3. Sort by aggregate score
    4. Return top N documents
    """
    from collections import defaultdict

    groups = defaultdict(list)

    # Step 1: Group by document_id
    for result in search_results:
        doc_id = result.get('document_id')
        if not doc_id:
            logger.warning("Chunk missing document_id, skipping")
            continue
        groups[doc_id].append(result)

    # Step 2: Calculate aggregate scores
    document_groups = []
    for doc_id, chunks in groups.items():
        # Sort chunks by similarity descending
        sorted_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', x.get('similarity', 0)), reverse=True)

        # Take top-3 for aggregate score (legal context needs multiple chunks)
        top_3 = sorted_chunks[:3]

        # Weighted average: top chunk gets more weight
        weights = [0.5, 0.3, 0.2][:len(top_3)]
        avg_similarity = sum(
            chunk.get('rerank_score', chunk.get('similarity', 0)) * weight
            for chunk, weight in zip(top_3, weights)
        ) / sum(weights)

        # Create document group
        first_chunk = sorted_chunks[0]
        document_groups.append(DocumentGroup(
            document_id=doc_id,
            document_title=first_chunk.get('document_title', 'Văn bản'),
            document_code=first_chunk.get('document_code', ''),
            chunk_count=len(chunks),
            max_similarity=sorted_chunks[0].get('rerank_score', sorted_chunks[0].get('similarity', 0)),
            avg_similarity=avg_similarity,
            top_chunks=sorted_chunks[:3],
            all_chunk_ids=[c.get('id', c.get('chunk_id', '')) for c in sorted_chunks]
        ))

    # Step 3: Sort by aggregate score and return top N
    document_groups.sort(key=lambda g: g.avg_similarity, reverse=True)
    return document_groups[:max_options]
```

**Ví dụ output**:

```json
{
  "type": "clarification_needed",
  "confidence": 0.62,
  "message": "Tôi tìm thấy các văn bản có thể liên quan. Bạn muốn tìm hiểu về:",
  "options": [
    {
      "id": "doc_123",
      "type": "document",
      "title": "Luật Hôn Nhân Gia Đình",
      "description": "15 đoạn văn bản liên quan (độ phù hợp: 72%)",
      "confidence": 0.72,
      "preview": "Điều 8: Điều kiện kết hôn. Nam từ đủ 20 tuổi...",
      "metadata": {
        "document_code": "52/2014/QH13",
        "effective_date": "2015-01-01"
      }
    },
    {
      "id": "doc_456",
      "type": "document",
      "title": "Luật Hộ Tịch",
      "description": "12 đoạn văn bản liên quan (độ phù hợp: 63%)",
      "confidence": 0.63,
      "preview": "Điều 47: Đăng ký kết hôn...",
      "metadata": {
        "document_code": "78/2014/QH13"
      }
    },
    {
      "id": "manual",
      "type": "manual_input",
      "title": "Không phải những thứ này",
      "description": "Tôi muốn tìm thông tin khác",
      "confidence": 0.0
    }
  ]
}
```

---

### Vấn đề 3: Logic hỏi lại - Embedded vs Modal

#### Option A: Embedded Response (RECOMMENDED)

**Ưu điểm**:

- ✅ Không cần popup → UX mượt mà hơn
- ✅ Giữ ngữ cảnh conversation
- ✅ Có thể scroll xem tất cả options
- ✅ Mobile-friendly
- ✅ Dễ implement history tracking

**Flow**:

```
User: "kết hôn cần gì"
  ↓
Bot: {
  "type": "clarification_needed",
  "message": "...",
  "options": [...]
}
  ↓
Frontend: Render như 1 message bình thường với buttons
  ↓
User: Click option "Luật Hôn Nhân"
  ↓
POST /query với { "clarification_selection": "doc_123" }
  ↓
Bot: Trả lời với context từ doc_123
```

**Frontend Component** (React example):

```tsx
// frontend/src/components/chat/ClarificationMessage.tsx

interface ClarificationMessageProps {
  message: string;
  options: ClarificationOption[];
  onSelectOption: (optionId: string) => void;
}

export function ClarificationMessage({
  message,
  options,
  onSelectOption,
}: ClarificationMessageProps) {
  return (
    <div className="clarification-message">
      <div className="message-text">{message}</div>

      <div className="options-grid">
        {options.map((option) => (
          <button
            key={option.id}
            className="option-card"
            onClick={() => onSelectOption(option.id)}
          >
            <div className="option-title">{option.title}</div>
            <div className="option-description">{option.description}</div>
            {option.confidence > 0 && (
              <div className="confidence-badge">
                {Math.round(option.confidence * 100)}% phù hợp
              </div>
            )}
            {option.preview && (
              <div className="option-preview">{option.preview}</div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
```

#### Option B: Modal Popup

**Ưu điểm**:

- ✅ Focus user attention
- ✅ Rõ ràng hơn cho decision point

**Nhược điểm**:

- ❌ Ngắt quãng conversation flow
- ❌ Khó xem lại clarification history
- ❌ Mobile UX kém hơn

**Khi nào dùng Modal**:

- Critical decisions (e.g., "Bạn có chắc muốn xóa?")
- Multi-step clarification (e.g., chọn collection → chọn document)
- KHÔNG dùng cho simple clarification

**Recommendation**: **EMBEDDED** cho legal document clarification

---

## 🚀 IMPLEMENTATION PLAN - PHASE 1: CLARIFICATION

### Timeline: 2 weeks (10 working days)

### Week 1: Backend Foundation

#### Day 1-2: ENV Configuration & Models

**Files to create/modify**:

```
query-service/
├── .env                          # ADD thresholds
├── src/
│   ├── config.py                 # ADD validators
│   ├── models.py                 # ADD clarification models
│   └── clarification.py          # NEW service
```

**Tasks**:

1. ✅ Add ENV variables với validation
2. ✅ Create Pydantic models (DocumentGroup, ClarificationOption, ClarificationResponse)
3. ✅ Create ClarificationError exceptions
4. ✅ Write unit tests for config validation

**Code skeleton**:

```python
# query-service/src/clarification.py

from typing import List, Dict, Optional
from collections import defaultdict
import logging

from .config import settings
from .models import (
    DocumentGroup,
    ClarificationOption,
    ClarificationResponse,
    ClarificationError
)

logger = logging.getLogger(__name__)

class ClarificationService:
    """
    Smart clarification service for legal documents

    Confidence levels:
    - < 0.50: LOW - Không tìm thấy → Thu thập context
    - 0.50-0.65: MEDIUM - Nhiều văn bản → Hỏi chọn
    - 0.65-0.80: HIGH - Khá chắc → Xác nhận
    - > 0.80: VERY_HIGH - Rất chắc → Trả lời trực tiếp
    """

    def __init__(self):
        self.enabled = settings.CLARITY_ENABLED
        self.low_threshold = settings.CLARITY_LOW_THRESHOLD
        self.medium_threshold = settings.CLARITY_MEDIUM_THRESHOLD
        self.high_threshold = settings.CLARITY_HIGH_THRESHOLD
        self.max_options = settings.CLARITY_MAX_OPTIONS
        self.strict_mode = settings.CLARITY_STRICT_MODE

        logger.info(f"🎯 ClarificationService initialized:")
        logger.info(f"  Thresholds: LOW={self.low_threshold}, MED={self.medium_threshold}, HIGH={self.high_threshold}")
        logger.info(f"  Strict mode: {self.strict_mode}")

    def should_clarify(self, max_similarity: float) -> bool:
        """Check if clarification is needed based on confidence"""
        if not self.enabled:
            return False
        return max_similarity < self.high_threshold

    def generate_clarification(
        self,
        question: str,
        search_results: List[Dict],
        max_similarity: float
    ) -> Optional[ClarificationResponse]:
        """
        Generate clarification response based on confidence level

        Returns None if confidence is high enough (no clarification needed)
        """
        if not self.should_clarify(max_similarity):
            return None

        # LOW: No results or very low similarity
        if max_similarity < self.low_threshold:
            return self._generate_context_gathering(question)

        # MEDIUM: Multiple relevant documents
        elif max_similarity < self.medium_threshold:
            return self._generate_document_selection(
                question, search_results, max_similarity
            )

        # HIGH: Pretty confident, but confirm
        else:  # medium_threshold <= similarity < high_threshold
            return self._generate_confirmation(
                question, search_results, max_similarity
            )

    def _generate_context_gathering(
        self,
        question: str
    ) -> ClarificationResponse:
        """LOW confidence: Ask for more context"""
        # Implementation...

    def _generate_document_selection(
        self,
        question: str,
        search_results: List[Dict],
        confidence: float
    ) -> ClarificationResponse:
        """MEDIUM confidence: Show document options"""
        # Group by document
        document_groups = self._group_by_document(search_results)

        # Create options
        options = []
        for group in document_groups[:self.max_options - 1]:  # Reserve 1 for "manual"
            options.append(ClarificationOption(
                id=group.document_id,
                type="document",
                title=group.document_title,
                description=f"{group.chunk_count} đoạn văn bản (độ phù hợp: {group.avg_similarity*100:.0f}%)",
                confidence=group.avg_similarity,
                preview=group.top_chunks[0].get('content', '')[:200] + "...",
                metadata={
                    "document_code": group.document_code,
                    "chunk_count": group.chunk_count,
                    "chunk_ids": group.all_chunk_ids
                }
            ))

        # Add manual input option
        options.append(ClarificationOption(
            id="manual",
            type="manual_input",
            title="Không phải những thứ này",
            description="Tôi muốn tìm thông tin khác",
            confidence=0.0
        ))

        return ClarificationResponse(
            type="clarification_needed",
            confidence_level="medium",
            confidence=confidence,
            message="Tôi tìm thấy các văn bản có thể liên quan. Bạn muốn tìm hiểu về:",
            options=options,
            response_type=settings.CLARITY_RESPONSE_TYPE
        )

    def _generate_confirmation(
        self,
        question: str,
        search_results: List[Dict],
        confidence: float
    ) -> ClarificationResponse:
        """HIGH confidence: Confirm best match"""
        # Implementation...

    def _group_by_document(
        self,
        search_results: List[Dict]
    ) -> List[DocumentGroup]:
        """Group chunks by document and calculate aggregate scores"""
        # Implementation from above...
```

#### Day 3-4: Integration với Query Service

**Modify**:

```python
# query-service/src/main.py

from .clarification import ClarificationService

clarification_service = ClarificationService()

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # ... existing code until search results ...

    search_results = await search_vectors(embedding)

    if not search_results:
        # LOW confidence clarification
        clarification = clarification_service.generate_clarification(
            question=request.question,
            search_results=[],
            max_similarity=0.0
        )

        return QueryResponse(
            success=True,
            question=request.question,
            answer=None,
            clarification=clarification,
            sources=[],
            tokens_used=0
        )

    # Calculate max similarity
    max_similarity = max(
        r.get('rerank_score', r.get('similarity', 0))
        for r in search_results
    )

    # Check if clarification needed
    clarification = clarification_service.generate_clarification(
        question=request.question,
        search_results=search_results,
        max_similarity=max_similarity
    )

    if clarification:
        # Return clarification instead of answer
        return QueryResponse(
            success=True,
            question=request.question,
            answer=None,
            clarification=clarification,
            sources=[SearchResult(**r) for r in search_results[:5]],
            tokens_used=0
        )

    # High confidence: Generate answer directly
    # ... existing rerank + LLM code ...
```

#### Day 5: Handle Clarification Response

**New endpoint**:

```python
# query-service/src/main.py

@app.post("/query/clarify")
async def query_with_clarification(request: ClarificationSelectionRequest):
    """
    Handle user's clarification selection

    Request:
    {
        "original_question": "kết hôn cần gì",
        "selected_option_id": "doc_123",
        "selected_option_type": "document",
        "session_id": "uuid"
    }
    """
    logger.info(f"📋 User selected: {request.selected_option_id}")

    if request.selected_option_type == "manual_input":
        # User wants to rephrase
        return QueryResponse(
            success=True,
            question=request.original_question,
            answer="Vui lòng diễn đạt lại câu hỏi cụ thể hơn.",
            clarification=None,
            sources=[],
            tokens_used=0
        )

    # User selected a document
    # Re-search with document_id filter
    embedding = await embed_text(request.original_question)
    search_results = await search_vectors(
        embedding,
        filters={"document_id": request.selected_option_id}
    )

    # Now generate answer with filtered results
    reranked_results = await rerank_documents(
        request.original_question,
        search_results,
        top_k=5
    )

    # ... generate answer ...
```

### Week 2: Frontend Integration & Testing

#### Day 6-7: Frontend Components

**Files to create**:

```
frontend/src/
├── types/
│   └── clarification.ts          # TypeScript types
├── components/
│   └── chat/
│       ├── ClarificationMessage.tsx
│       └── ClarificationOption.tsx
└── hooks/
    └── useClarification.ts
```

**Implementation**:

```tsx
// frontend/src/types/clarification.ts

export interface ClarificationOption {
  id: string;
  type: "document" | "collection" | "manual_input";
  title: string;
  description: string;
  confidence: number;
  preview?: string;
  metadata?: Record<string, any>;
}

export interface ClarificationResponse {
  type: "clarification_needed";
  confidence_level: "low" | "medium" | "high";
  confidence: number;
  message: string;
  options: ClarificationOption[];
  response_type: "embedded" | "modal";
}

// frontend/src/components/chat/ClarificationMessage.tsx
// (Implementation from above)
```

#### Day 8-9: Testing

**Test scenarios**:

1. ✅ LOW confidence (similarity < 0.50)
   - Query: "giấy tờ"
   - Expected: Context gathering clarification
2. ✅ MEDIUM confidence (0.50-0.65)
   - Query: "kết hôn"
   - Expected: Document selection with 3-5 options
3. ✅ HIGH confidence (0.65-0.80)
   - Query: "điều kiện kết hôn là gì"
   - Expected: Confirmation with best match
4. ✅ VERY HIGH confidence (> 0.80)
   - Query: "nam từ bao nhiêu tuổi được kết hôn"
   - Expected: Direct answer (no clarification)

**Test code**:

```python
# tests/test_clarification.py

import pytest
from query_service.src.clarification import ClarificationService

@pytest.fixture
def service():
    return ClarificationService()

def test_low_confidence_context_gathering(service):
    clarification = service.generate_clarification(
        question="giấy tờ",
        search_results=[],
        max_similarity=0.35
    )

    assert clarification is not None
    assert clarification.confidence_level == "low"
    assert clarification.type == "clarification_needed"
    assert len(clarification.options) > 0

def test_medium_confidence_document_selection(service):
    # Mock search results from 3 documents
    search_results = [
        {"document_id": "doc_1", "document_title": "Luật Hôn Nhân", "similarity": 0.62, ...},
        {"document_id": "doc_1", "similarity": 0.60, ...},
        {"document_id": "doc_2", "document_title": "Luật Hộ Tịch", "similarity": 0.58, ...},
        # ...
    ]

    clarification = service.generate_clarification(
        question="kết hôn",
        search_results=search_results,
        max_similarity=0.62
    )

    assert clarification.confidence_level == "medium"
    assert len(clarification.options) <= 5  # Max options
    assert any(opt.type == "manual_input" for opt in clarification.options)

def test_high_confidence_direct_answer(service):
    search_results = [
        {"document_id": "doc_1", "similarity": 0.85, ...},
    ]

    clarification = service.generate_clarification(
        question="nam từ bao nhiêu tuổi được kết hôn",
        search_results=search_results,
        max_similarity=0.85
    )

    assert clarification is None  # No clarification needed
```

#### Day 10: Documentation & Deployment

**Documentation**:

- Update API docs
- Add clarification examples
- Write troubleshooting guide

**Deployment**:

```bash
# Update ENV
vim query-service/.env
# Add CLARITY_* variables

# Rebuild
docker-compose build query-service

# Deploy
docker-compose up -d query-service

# Test
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"question": "kết hôn"}'
```

---

## 🎯 PHASE 2: CONVERSATION HISTORY (Next Sprint)

### Quick Plan

**Week 1**: Backend

- Add `history` field to QueryRequest
- Update LLM Service to accept history
- Modify prompt to include conversation context

**Week 2**: Frontend

- Store conversation history in state
- Send history with each query
- Show context in UI

**Effort**: ~8 hours (simpler than clarification)

---

## 📊 SUCCESS METRICS

### Clarification Quality

- **Precision**: % clarifications that lead to satisfactory answers
- **User acceptance**: % times user selects an option (vs rephrasing)
- **Document accuracy**: % times selected document matches user intent

### Performance

- **Latency**: Clarification response < 500ms
- **Throughput**: Handle 100 req/s with clarification enabled

### Business Impact

- **Query success rate**: Increase from 60% → 85%
- **User satisfaction**: Reduce "không tìm thấy" from 30% → 10%
- **Session length**: Increase avg questions/session

---

## 🔥 CRITICAL DECISIONS

### ✅ Embedded response (NOT modal)

- Lý do: Better UX, mobile-friendly, keeps conversation flow

### ✅ Document-first grouping (NOT chunk-level)

- Lý do: 166 documents → must aggregate, legal context needs document coherence

### ✅ Strict mode (NO fallback)

- Lý do: Easier debugging, force proper config, legal domain needs reliability

### ✅ ENV-driven (NOT hardcoded)

- Lý do: Easy tuning without code changes, different environments need different thresholds

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues

**Issue 1**: Clarification not triggering

```bash
# Check ENV
docker exec legalrag-query cat /app/.env | grep CLARITY

# Check logs
docker logs legalrag-query --tail 100 | grep "ClarificationService"
```

**Issue 2**: Wrong confidence levels

```python
# Debug logging
logger.debug(f"Max similarity: {max_similarity}")
logger.debug(f"Thresholds: LOW={low}, MED={med}, HIGH={high}")
logger.debug(f"Should clarify: {should_clarify}")
```

**Issue 3**: Document grouping errors

```python
# Validate search results structure
for result in search_results:
    assert 'document_id' in result, f"Missing document_id: {result}"
    assert 'document_title' in result, f"Missing document_title: {result}"
```

---

**Ready to implement? Let's start with Phase 1 Day 1! 🚀**
