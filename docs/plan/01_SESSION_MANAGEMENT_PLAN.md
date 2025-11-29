# ✅ KẾ HOẠCH: Session Management & Document Pinning

> **Status**: ✅ **COMPLETED** (2025-11-29)
>
> **Mục tiêu**: Chuyển hoàn toàn logic session/pinning về backend để phù hợp kiến trúc client-server và tích hợp với database logging.

---

## IMPLEMENTATION SUMMARY

### Completed Tasks:

- ✅ Backend session ID generation (YYYYMMDD_NNNN format)
- ✅ New API endpoints: `/session/start`, `/session/clear`, `/session/info/{id}`
- ✅ Session persistence to PostgreSQL immediately on creation
- ✅ Frontend simplified - receives session from backend
- ✅ Fixed session continuity bug (sessions saved to DB on creation)
- ✅ Fixed `used_pinned_document` response consistency

### Key Changes:

- `query-service/src/main.py`: Added session generation, new endpoints, auto-save on new session
- `frontend/src/stores/chatStore.ts`: Simplified to receive session from backend
- `frontend/src/services/query/queryService.ts`: Added session API functions

---

## 1. PHÂN TÍCH HIỆN TRẠNG

### 1.1 Frontend hiện tại (`chatStore.ts`)

```typescript
// Session ID được tạo ở frontend
const generateSessionId = (): string => {
  // Format: YYYYMMDD_NNNN (e.g., 20251127_0001)
};

// Lưu trong sessionStorage (per-tab)
sessionStorage.setItem("legalrag_session_id", sessionId);
localStorage.setItem("legalrag_session_counter", counter);
```

**Vấn đề:**

- ❌ Logic phân tán giữa frontend và backend
- ❌ Frontend phải quản lý counter (không cần thiết)
- ❌ Khó sync session across tabs/devices
- ❌ Không có cách explicit "unpin" document

### 1.2 Backend hiện tại (`query-service/main.py`)

```python
# ConversationState lưu trong PostgreSQL
@dataclass
class ConversationState:
    session_id: str
    active_document_id: Optional[str] = None
    active_document_title: Optional[str] = None
    last_question: Optional[str] = None
    last_confidence: float = 0.0
    conversation_turns: int = 0
```

**Đã có sẵn:**

- ✅ PostgreSQL storage (`query_sessions` table)
- ✅ ConversationState dataclass
- ✅ `save_conversation_state()` / `get_conversation_state()`
- ✅ Follow-up detection với pattern matching

---

## 2. THIẾT KẾ MỚI: Backend-Driven Session

### 2.1 Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
├─────────────────────────────────────────────────────────────────┤
│  • Gửi device_fingerprint (optional) để backend nhận diện       │
│  • Nhận session_id từ backend response                          │
│  • Lưu session_id vào sessionStorage (chỉ để gửi lại)          │
│  • Hiển thị pinned document badge (từ response)                 │
│  • Button "Chủ đề mới" → gọi POST /session/clear                │
│                                                                 │
│  KHÔNG CÓ:                                                       │
│  • generateSessionId() logic                                     │
│  • Counter management                                            │
│  • Pinning logic                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (query-service)                       │
├─────────────────────────────────────────────────────────────────┤
│  SESSION MANAGEMENT:                                             │
│  • POST /session/start → Tạo session mới, trả về session_id     │
│  • POST /session/clear → Clear pinned document (explicit unpin)  │
│  • GET  /session/info  → Lấy thông tin session hiện tại         │
│                                                                 │
│  QUERY ENDPOINTS:                                                │
│  • POST /query         → Tự động tạo session nếu chưa có        │
│  • POST /query/confirm → Pin document đã chọn                    │
│                                                                 │
│  SMART TOPIC DETECTION:                                          │
│  • Embedding similarity giữa câu hỏi mới và last_question       │
│  • Auto-unpin khi topic change detected (similarity < 0.4)       │
│  • Pattern matching (existing) + semantic check (new)            │
│                                                                 │
│  DATABASE:                                                       │
│  • query_sessions: Lưu session + context                         │
│  • query_logs: Log mọi query với session_id                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Database Schema (đã có trong schema_new.sql)

```sql
-- Đã có sẵn, chỉ cần sử dụng
CREATE TABLE IF NOT EXISTS query_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_identifier VARCHAR(200),  -- IP hoặc fingerprint
    user_agent TEXT,
    conversation_turns INTEGER DEFAULT 0,
    topics TEXT[],
    context JSONB DEFAULT '{}',  -- Lưu ConversationState
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);
```

**Context JSONB structure:**

```json
{
  "active_document_id": "uuid-xxx",
  "active_document_title": "Đăng ký khai sinh",
  "last_question": "phí bao nhiêu?",
  "last_question_embedding": [0.123, -0.456, ...],  // NEW: Để detect topic change
  "last_confidence": 0.85,
  "conversation_turns": 3
}
```

---

## 3. API ENDPOINTS MỚI

### 3.1 POST /session/start (Tùy chọn)

```python
@app.post("/session/start")
async def start_session(
    user_agent: Optional[str] = Header(None),
    x_device_fingerprint: Optional[str] = Header(None)
):
    """
    Tạo session mới (explicit).
    Frontend có thể gọi khi cần session ID trước khi hỏi.

    Returns: { session_id: "20251128-001", expires_at: "..." }
    """
```

### 3.2 POST /session/clear ⭐ QUAN TRỌNG

```python
class ClearSessionRequest(BaseModel):
    session_id: str

@app.post("/session/clear")
async def clear_session(request: ClearSessionRequest):
    """
    Clear pinned document mà KHÔNG xóa chat history.
    User có thể bắt đầu chủ đề mới mà vẫn giữ lịch sử chat.

    Use case:
    - User đang hỏi về "Đăng ký khai sinh"
    - Muốn hỏi về "Cấp CCCD" → Click "Chủ đề mới"
    - System clear pinned doc, lần hỏi tiếp sẽ search full corpus
    """
    state = get_conversation_state(request.session_id)
    state.clear()  # Clear active_document_id, active_document_title
    save_conversation_state(state)

    return {
        "success": True,
        "message": "Đã xóa ngữ cảnh văn bản. Bạn có thể hỏi về chủ đề mới.",
        "session_id": request.session_id
    }
```

### 3.3 GET /session/info

```python
@app.get("/session/info")
async def get_session_info(session_id: str):
    """
    Lấy thông tin session để frontend hiển thị.

    Returns:
    {
        "session_id": "20251128-001",
        "has_pinned_document": true,
        "pinned_document": {
            "id": "uuid-xxx",
            "title": "Đăng ký khai sinh"
        },
        "conversation_turns": 5,
        "last_question": "phí bao nhiêu?",
        "expires_at": "2025-11-28T15:30:00"
    }
    """
```

### 3.4 Enhanced /query Response

```python
class QueryResponse(BaseModel):
    success: bool
    question: str
    answer: Optional[str] = None

    # Session info (NEW - always included)
    session_id: str  # Backend-generated session ID
    session_info: SessionInfo  # Full session context

    # Clarification
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    document_options: Optional[List[DocumentOption]] = None

    # Pinning (existing)
    used_pinned_document: bool = False
    pinned_document_title: Optional[str] = None

    sources: List[SearchResult]
    tokens_used: int

class SessionInfo(BaseModel):
    """Session info returned in every response"""
    has_pinned_document: bool
    pinned_document_id: Optional[str] = None
    pinned_document_title: Optional[str] = None
    conversation_turns: int
    can_clear: bool  # True if has pinned doc (enable "Clear" button)
```

---

## 4. SMART TOPIC DETECTION (Semantic)

### 4.1 Cải tiến `should_use_pinned_document()`

```python
async def should_use_pinned_document(
    question: str,
    state: ConversationState,
    embedding_client: httpx.AsyncClient
) -> bool:
    """
    Decide whether to use pinned document or search full corpus.

    NEW: Sử dụng embedding similarity để detect topic change.
    """
    if not state.is_valid():
        return False

    # === METHOD 1: Pattern matching (fast, cheap) ===
    # Check explicit topic change phrases
    new_topic_indicators = [
        r"(muốn hỏi về|hỏi về|cho tôi biết về)",
        r"(chuyển sang|đổi qua|hỏi cái khác)",
        r"(thủ tục khác|văn bản khác)",
    ]

    q_lower = question.lower()
    for pattern in new_topic_indicators:
        if re.search(pattern, q_lower):
            logger.info(f"📌 Explicit topic change detected: {pattern}")
            state.clear()
            return False

    # === METHOD 2: Semantic similarity (accurate, more expensive) ===
    # Only if we have cached embedding from last question
    if state.last_question_embedding:
        # Embed current question
        new_embedding = await embed_text_cached(question, embedding_client)

        if new_embedding:
            similarity = cosine_similarity(
                new_embedding,
                state.last_question_embedding
            )

            # LOW SIMILARITY = Topic change
            if similarity < 0.4:
                logger.info(f"📌 Semantic topic change detected (sim={similarity:.3f} < 0.4)")
                state.clear()
                return False

            # HIGH SIMILARITY = Same topic (follow-up)
            if similarity > 0.7:
                logger.info(f"📌 Strong topic continuity (sim={similarity:.3f} > 0.7)")
                return True

    # === METHOD 3: Length heuristic (fallback) ===
    # Short questions are usually follow-ups
    if len(question) < 30:
        logger.info(f"📌 Short question ({len(question)} chars) → follow-up")
        return True

    # === METHOD 4: Document title keyword check ===
    if state.active_document_title:
        title_keywords = extract_keywords(state.active_document_title)
        if any(kw.lower() in question.lower() for kw in title_keywords):
            logger.info(f"📌 Question mentions pinned doc title keywords")
            return True

    # Default for medium-length questions: use pinned
    if len(question) < 80:
        return True

    # Long questions might be new topics
    logger.info("📌 Long question → searching full corpus to be safe")
    return False


def extract_keywords(title: str) -> List[str]:
    """Extract meaningful keywords from document title."""
    # Remove numbering like "01. "
    title = re.sub(r'^\d+\.\s*', '', title)

    # Split by common separators
    words = re.split(r'[\s,;\-–]+', title)

    # Filter short words and stopwords
    stopwords = {'thủ', 'tục', 'về', 'và', 'của', 'tại', 'cho', 'với'}
    keywords = [w for w in words if len(w) > 2 and w.lower() not in stopwords]

    return keywords


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import numpy as np
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

### 4.2 Cache Embedding cho Performance

```python
# In-memory cache với TTL
from functools import lru_cache
import time

_embedding_cache = {}
_cache_ttl = 300  # 5 minutes

async def embed_text_cached(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
    """Embed text with caching to reduce API calls."""
    cache_key = hash(text)

    if cache_key in _embedding_cache:
        cached_time, embedding = _embedding_cache[cache_key]
        if time.time() - cached_time < _cache_ttl:
            return embedding

    # Call embedding service
    embedding = await embed_text(text)

    if embedding:
        _embedding_cache[cache_key] = (time.time(), embedding)

    return embedding
```

---

## 5. FRONTEND CHANGES

### 5.1 Simplified chatStore.ts

```typescript
// BEFORE (complex)
const generateSessionId = (): string => {
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const counterKey = "legalrag_session_counter";
  const dateKey = "legalrag_session_date";
  // ... counter logic
};

// AFTER (simple)
interface SessionInfo {
  session_id: string;
  has_pinned_document: boolean;
  pinned_document_title?: string;
  conversation_turns: number;
  can_clear: boolean;
}

let currentSession: SessionInfo | null = null;

// Get session from last response or create new
const getSessionId = (): string | undefined => {
  const stored = sessionStorage.getItem("legalrag_session_id");
  return stored || undefined;
};

// Save session from response
const updateSession = (sessionInfo: SessionInfo) => {
  currentSession = sessionInfo;
  sessionStorage.setItem("legalrag_session_id", sessionInfo.session_id);
};

// Clear pinned document (explicit unpin)
const clearPinnedDocument = async () => {
  const sessionId = getSessionId();
  if (!sessionId) return;

  const response = await fetch("/api/session/clear", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (response.ok) {
    const data = await response.json();
    // Update local state
    if (currentSession) {
      currentSession.has_pinned_document = false;
      currentSession.pinned_document_title = undefined;
      currentSession.can_clear = false;
    }
  }
};
```

### 5.2 UI Component: Pinned Document Badge

```tsx
// PinnedDocumentBadge.tsx
interface Props {
  sessionInfo: SessionInfo | null;
  onClear: () => void;
}

const PinnedDocumentBadge: React.FC<Props> = ({ sessionInfo, onClear }) => {
  if (!sessionInfo?.has_pinned_document) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 rounded-lg">
      <span className="text-blue-600">📌</span>
      <span className="text-sm text-blue-800">
        Đang xem: <strong>{sessionInfo.pinned_document_title}</strong>
      </span>
      <button
        onClick={onClear}
        className="ml-2 text-xs text-blue-600 hover:text-blue-800 underline"
      >
        Chủ đề mới
      </button>
    </div>
  );
};
```

---

## 6. IMPLEMENTATION PLAN

### Phase 1: Backend (2-3 ngày)

| Task                                                  | File                        | Priority |
| ----------------------------------------------------- | --------------------------- | -------- |
| 1. Add `/session/clear` endpoint                      | `query-service/src/main.py` | ⭐ HIGH  |
| 2. Add `/session/info` endpoint                       | `query-service/src/main.py` | MEDIUM   |
| 3. Add `session_info` to QueryResponse                | `query-service/src/main.py` | ⭐ HIGH  |
| 4. Implement semantic topic detection                 | `query-service/src/main.py` | HIGH     |
| 5. Add `last_question_embedding` to ConversationState | `query-service/src/main.py` | HIGH     |
| 6. Add embedding caching                              | `query-service/src/main.py` | MEDIUM   |

### Phase 2: Frontend (1-2 ngày)

| Task                                 | File                               | Priority |
| ------------------------------------ | ---------------------------------- | -------- |
| 1. Simplify session management       | `frontend/src/stores/chatStore.ts` | ⭐ HIGH  |
| 2. Use session_info from response    | `frontend/src/stores/chatStore.ts` | HIGH     |
| 3. Add PinnedDocumentBadge component | `frontend/src/components/`         | HIGH     |
| 4. Add "Chủ đề mới" button           | `frontend/src/components/`         | HIGH     |

### Phase 3: Testing (1 ngày)

| Test Case                  | Expected Behavior                         |
| -------------------------- | ----------------------------------------- |
| New session                | Backend generates session_id              |
| Follow-up question (short) | Uses pinned document                      |
| Topic change (explicit)    | Clears pinned, searches corpus            |
| Topic change (semantic)    | Auto-detects, searches corpus             |
| "Chủ đề mới" button        | Clears pinned, next query searches corpus |
| Session expiry (30 min)    | Auto-clear, new session                   |

---

## 7. MIGRATION NOTES

### 7.1 Backward Compatibility

- Frontend có thể gửi session_id cũ, backend sẽ tìm trong database
- Nếu không tìm thấy, tạo session mới với ID cũ

### 7.2 Database Migration

- Không cần migration (schema đã đúng)
- Có thể cleanup old sessions: `DELETE FROM query_sessions WHERE expires_at < NOW()`

### 7.3 Rollback Plan

- Giữ lại `generateSessionId()` trong frontend (commented out)
- Có thể rollback bằng cách uncomment và bỏ dùng session_info từ response

---

## 8. METRICS & MONITORING

### 8.1 Log Events

```python
# Log khi session được tạo
logger.info(f"📌 New session created: {session_id}")

# Log khi pinned document được set
logger.info(f"📌 Document pinned: {doc_title} (session={session_id})")

# Log khi topic change detected
logger.info(f"📌 Topic change detected (sim={similarity:.3f}), clearing pinned doc")

# Log khi user explicitly clears
logger.info(f"📌 User cleared pinned document (session={session_id})")
```

### 8.2 Query Analytics

- `query_logs.query_type`: 'initial', 'follow_up', 'confirm', 'clarification'
- `query_logs.metadata.used_pinned_document`: boolean
- `query_logs.metadata.topic_change_detected`: boolean

---

## 9. SUMMARY

| Aspect                | Before                  | After                     |
| --------------------- | ----------------------- | ------------------------- |
| Session ID generation | Frontend                | Backend                   |
| Counter management    | Frontend (localStorage) | Backend (DB)              |
| Pinning logic         | Backend                 | Backend (unchanged)       |
| Topic detection       | Pattern matching        | Pattern + Semantic        |
| Explicit unpin        | Refresh page            | "Chủ đề mới" button       |
| Session storage       | sessionStorage + DB     | DB only (frontend caches) |
| Logging               | Partial                 | Full (query_logs)         |

**Kết quả mong đợi:**

- ✅ Logic tập trung ở backend → dễ maintain, debug
- ✅ Semantic topic detection → tự động clear khi chuyển chủ đề
- ✅ Explicit "Chủ đề mới" button → user control
- ✅ Full logging → analytics, improvement
- ✅ Phù hợp kiến trúc client-server
