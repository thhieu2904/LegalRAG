# PHÂN TÍCH: NÊN VIẾT LẠI HAY TÁI CẤU TRÚC?

# ============================================

## 🔍 **ĐÁNH GIÁ KIẾN TRÚC HIỆN TẠI**

### **Source tham khảo (Reference Implementation)**

```
Monolithic RAG Service (single service)
├── ✅ Code structure RẤT TỐT
│   ├── Services phân chia rõ ràng (vector, rag_engine, router, reranker)
│   ├── Separation of concerns tốt
│   ├── Config management đầy đủ
│   └── Session management hoàn chỉnh
│
├── ⚠️ Vấn đề kiến trúc
│   ├── Tất cả services trong 1 process (monolithic)
│   ├── ChromaDB embedded (không scale được)
│   ├── File system storage (không có version control)
│   └── Không có service discovery/load balancing
│
└── 💡 Core logic RẤT TỐT (nên giữ lại)
    ├── RAG pipeline logic (search → rerank → expand → synthesize)
    ├── Router logic (query routing với confidence levels)
    ├── Session management (stateful conversation)
    └── Clarification system (4-level clarification)
```

### **LegalRAG hiện tại**

```
Current RAG Service
├── ❌ Có nhiều lỗi (như anh nói)
├── ⚠️ Cấu trúc tương tự Source tham khảo nhưng có bugs
└── 🔄 Cần refactor/rewrite
```

---

## 🎯 **QUYẾT ĐỊNH: HYBRID APPROACH**

**KẾT LUẬN: KHÔNG CẦN VIẾT LẠI HOÀN TOÀN, chỉ cần:**

1. ✅ **Copy code tốt từ Source tham khảo** (services layer)
2. ✅ **Refactor thành microservices architecture** (infrastructure layer)
3. ✅ **Thay đổi storage backend** (PostgreSQL + MinIO thay vì ChromaDB + FileSystem)

---

## 📐 **KIẾN TRÚC MỚI ĐỀ XUẤT: MICROSERVICES**

### **Tách RAG Service thành 5 microservices:**

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway (Optional)                    │
│                     Port 8080 - nginx/traefik                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌──────────▼─────────┐    ┌─────────▼────────┐
│  RAG Orchestrator  │    │  Storage Service   │    │  Vector Service  │
│    Port 8000       │    │    Port 8001       │    │    Port 8002     │
└────────┬───────────┘    └────────┬───────────┘    └─────────┬────────┘
         │                         │                           │
         │                         │                           │
┌────────▼───────────┐    ┌───────▼────────┐      ┌──────────▼─────────┐
│  Session Service   │    │  Router Service │      │  Reranker Service  │
│    Port 8003       │    │    Port 8004    │      │    Port 8005       │
└────────────────────┘    └─────────────────┘      └────────────────────┘
         │                         │                           │
         └─────────────────────────┴───────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         │                                                     │
┌────────▼─────────┐                              ┌───────────▼────────┐
│   PostgreSQL     │                              │      MinIO         │
│   (pgvector)     │                              │   (File Storage)   │
│   Port 5432      │                              │   Port 9000        │
└──────────────────┘                              └────────────────────┘
```

---

## 🎨 **CHI TIẾT TỪNG SERVICE**

### **1. RAG Orchestrator Service** (Port 8000)

**Vai trò:** Điều phối toàn bộ RAG pipeline, API gateway cho frontend

**Trách nhiệm:**

- Nhận query từ frontend
- Điều phối các services (router → vector → reranker → LLM)
- Trả response về frontend
- Quản lý LLM inference (PhoGPT)

**Code từ Source tham khảo:**

```python
# Giữ lại logic từ rag_engine.py
├── app/services/rag_engine.py      # Core RAG orchestration
├── app/services/language_model.py  # LLM inference
├── app/services/context.py         # Context expansion
├── app/services/clarification.py   # Clarification logic
└── app/api/rag.py                  # API endpoints
```

**Dependencies:**

- Calls: `router-service`, `vector-service`, `reranker-service`, `session-service`, `storage-service`
- Uses: LLM model (local GGUF file)

**Docker:**

```yaml
rag-orchestrator:
  build: ./rag_orchestrator
  ports:
    - "8000:8000"
  environment:
    - ROUTER_SERVICE_URL=http://router-service:8004
    - VECTOR_SERVICE_URL=http://vector-service:8002
    - RERANKER_SERVICE_URL=http://reranker-service:8005
    - SESSION_SERVICE_URL=http://session-service:8003
    - STORAGE_SERVICE_URL=http://storage-service:8001
  volumes:
    - ./data/models/llm_dir:/app/models # LLM models
```

---

### **2. Storage Service** (Port 8001)

**Vai trò:** Quản lý tất cả file operations (MinIO + PostgreSQL metadata)

**Trách nhiệm:**

- CRUD operations cho documents (MinIO)
- CRUD operations cho forms (MinIO)
- Metadata management (PostgreSQL)
- Presigned URL generation

**Code:** NEW SERVICE (cần viết mới)

```python
├── app/services/minio_service.py      # MinIO wrapper
├── app/services/metadata_service.py   # PostgreSQL metadata
├── app/api/documents.py               # Document endpoints
└── app/api/forms.py                   # Form endpoints
```

**Dependencies:**

- Connects: MinIO, PostgreSQL
- No internal service calls

**Docker:**

```yaml
storage-service:
  build: ./storage_service
  ports:
    - "8001:8001"
  environment:
    - MINIO_ENDPOINT=minio:9000
    - DATABASE_URL=postgresql://user:pass@postgres:5432/legalrag
  depends_on:
    - minio
    - postgres
```

---

### **3. Vector Service** (Port 8002)

**Vai trò:** Vector search với pgvector

**Trách nhiệm:**

- Embedding generation (Vietnamese_Embedding_v2)
- Vector similarity search (pgvector)
- Context expansion (prev/next chunks)
- Collection filtering

**Code từ Source tham khảo:**

```python
# Adapt từ vector.py, thay ChromaDB → pgvector
├── app/services/vector_service.py     # NEW: pgvector wrapper
├── app/services/embedding_service.py  # Embedding generation
└── app/api/search.py                  # Vector search endpoints
```

**Dependencies:**

- Connects: PostgreSQL (pgvector)
- Uses: Embedding model (CPU)

**Docker:**

```yaml
vector-service:
  build: ./vector_service
  ports:
    - "8002:8002"
  environment:
    - DATABASE_URL=postgresql://user:pass@postgres:5432/legalrag
    - EMBEDDING_MODEL=AITeamVN/Vietnamese_Embedding_v2
  volumes:
    - ./data/models/hf_cache:/app/models # Embedding model cache
  depends_on:
    - postgres
```

---

### **4. Router Service** (Port 8004)

**Vai trò:** Query routing để xác định collection/document đúng

**Trách nhiệm:**

- Query classification (routing to collections)
- Confidence scoring (high/medium/low)
- Example questions matching
- Router questions database management

**Code từ Source tham khảo:**

```python
# Giữ nguyên logic từ router.py
├── app/services/router.py             # Router logic (KEEP)
├── app/services/query_router.py       # Query classification
└── app/api/routing.py                 # Routing endpoints
```

**Dependencies:**

- Calls: `vector-service` (for embedding)
- Connects: PostgreSQL (router questions)

**Docker:**

```yaml
router-service:
  build: ./router_service
  ports:
    - "8004:8004"
  environment:
    - DATABASE_URL=postgresql://user:pass@postgres:5432/legalrag
    - VECTOR_SERVICE_URL=http://vector-service:8002
  depends_on:
    - postgres
    - vector-service
```

---

### **5. Reranker Service** (Port 8005)

**Vai trò:** Reranking chunks với Vietnamese_Reranker

**Trách nhiệm:**

- Rerank search results
- Cross-encoder scoring
- Top-K selection

**Code từ Source tham khảo:**

```python
# Giữ nguyên logic từ reranker.py
├── app/services/reranker.py           # Reranker logic (KEEP)
└── app/api/rerank.py                  # Reranking endpoints
```

**Dependencies:**

- Uses: Reranker model (GPU)

**Docker:**

```yaml
reranker-service:
  build: ./reranker_service
  ports:
    - "8005:8005"
  environment:
    - RERANKER_MODEL=AITeamVN/Vietnamese_Reranker
  volumes:
    - ./data/models/hf_cache:/app/models
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

### **6. Session Service** (Port 8003)

**Vai trò:** Session management và chat history

**Trách nhiệm:**

- Session CRUD operations
- Conversation history storage
- Session state management (stateful routing)

**Code từ Source tham khảo:**

```python
# Adapt từ session_manager.py
├── app/services/session_manager.py    # Session logic (ADAPT)
└── app/api/sessions.py                # Session endpoints
```

**Dependencies:**

- Connects: PostgreSQL (session table)

**Docker:**

```yaml
session-service:
  build: ./session_service
  ports:
    - "8003:8003"
  environment:
    - DATABASE_URL=postgresql://user:pass@postgres:5432/legalrag
  depends_on:
    - postgres
```

---

## 🔄 **DATA FLOW MỚI**

### **Query Processing Flow:**

```
1. Frontend → RAG Orchestrator (8000)
   POST /chat { "query": "Làm giấy khai sinh cần gì?" }

2. RAG Orchestrator → Session Service (8003)
   GET /sessions/{session_id}
   → Lấy session context

3. RAG Orchestrator → Router Service (8004)
   POST /route { "query": "...", "session_context": {...} }
   → Xác định collection/document
   ← { "collection": "ho_tich", "confidence": 0.92 }

4. RAG Orchestrator → Vector Service (8002)
   POST /search { "query": "...", "collection": "ho_tich", "k": 20 }
   → Vector search với pgvector
   ← { "chunks": [...], "similarities": [...] }

5. RAG Orchestrator → Reranker Service (8005)
   POST /rerank { "query": "...", "chunks": [...] }
   → Rerank chunks
   ← { "reranked_chunks": [...], "scores": [...] }

6. RAG Orchestrator (local LLM inference)
   → Context expansion + LLM generation
   ← Generated answer

7. RAG Orchestrator → Storage Service (8001)
   GET /forms/by-document/{doc_id}
   → Lấy forms liên quan
   ← { "forms": [...] }

8. RAG Orchestrator → Session Service (8003)
   PUT /sessions/{session_id}
   → Update session history

9. RAG Orchestrator → Frontend
   ← { "answer": "...", "forms": [...], "confidence": 0.92 }
```

---

## 🚀 **MIGRATION STRATEGY**

### **Phase 1: Infrastructure Setup** (Week 1)

1. Setup PostgreSQL với pgvector extension
2. Setup MinIO
3. Run migration scripts (ChromaDB → pgvector, FileSystem → MinIO)

### **Phase 2: Build Core Services** (Week 2-3)

1. ✅ **Storage Service** (NEW - viết mới)
2. ✅ **Vector Service** (ADAPT từ vector.py)
3. ✅ **Session Service** (ADAPT từ session_manager.py)

### **Phase 3: Build Processing Services** (Week 3-4)

4. ✅ **Router Service** (COPY từ router.py)
5. ✅ **Reranker Service** (COPY từ reranker.py)

### **Phase 4: Build Orchestrator** (Week 4-5)

6. ✅ **RAG Orchestrator** (ADAPT từ rag_engine.py)

### **Phase 5: Testing & Integration** (Week 5-6)

7. Integration testing
8. Performance testing
9. Frontend integration

---

## 🎯 **TẠI SAO MICROSERVICES TỐT HƠN MONOLITHIC?**

### **Benefits:**

| Aspect              | Monolithic (hiện tại)           | Microservices (đề xuất)       |
| ------------------- | ------------------------------- | ----------------------------- |
| **Scalability**     | ❌ Không scale được từng phần   | ✅ Scale độc lập từng service |
| **Deployment**      | ❌ Deploy all or nothing        | ✅ Deploy từng service riêng  |
| **Development**     | ⚠️ Conflict khi nhiều người dev | ✅ Teams độc lập              |
| **Fault Isolation** | ❌ 1 bug crash toàn bộ          | ✅ Service fails độc lập      |
| **Technology**      | ❌ Locked vào 1 stack           | ✅ Polyglot (Python/Go/Rust)  |
| **Resource Usage**  | ❌ Tất cả dùng chung RAM/GPU    | ✅ Allocate resources riêng   |
| **Maintenance**     | ⚠️ Khó maintain code lớn        | ✅ Services nhỏ dễ maintain   |

### **Specific Benefits cho LegalRAG:**

1. **VRAM Management:**

   - Embedding service (CPU only) - no GPU needed
   - Reranker service (GPU) - dedicated VRAM
   - LLM service (GPU) - dedicated VRAM
   - → Không bị competition cho VRAM

2. **Scaling:**

   - Router service có thể chạy nhiều instances (stateless)
   - Vector service có thể scale horizontally
   - Storage service có thể scale independently

3. **Development:**

   - Team 1: Storage + Vector (storage layer)
   - Team 2: Router + Reranker (processing layer)
   - Team 3: Orchestrator (orchestration layer)

4. **Testing:**
   - Unit test từng service riêng
   - Mock services dễ dàng
   - Integration testing có isolation

---

## 📋 **DECISION MATRIX**

### **Option A: Viết lại hoàn toàn từ đầu**

- ❌ Mất thời gian (3-6 tháng)
- ❌ Mất logic đã có sẵn (router, clarification, session)
- ❌ Risk cao (có thể introduce bugs mới)
- ✅ Code sạch 100%

### **Option B: Copy Source tham khảo + Refactor sang microservices** ⭐ **ĐỀ XUẤT**

- ✅ Giữ được logic tốt (1-2 tháng)
- ✅ Rủi ro thấp (code đã proven)
- ✅ Upgrade infrastructure (pgvector + MinIO)
- ✅ Modernize architecture (microservices)
- ⚠️ Cần adapt code (không quá khó)

### **Option C: Refactor in-place (không tách services)**

- ⚠️ Vẫn giữ monolithic architecture
- ⚠️ Không scale được
- ✅ Nhanh nhất (2 tuần)
- ❌ Không giải quyết vấn đề dài hạn

---

## 🎯 **KẾT LUẬN VÀ HÀNH ĐỘNG**

### **QUYẾT ĐỊNH CUỐI CÙNG:**

👉 **Option B: Copy Source tham khảo + Build Microservices**

### **ROADMAP CỤ THỂ:**

#### **Step 1: Setup Infrastructure** (Week 1)

```bash
# Setup PostgreSQL + pgvector
docker-compose up postgres

# Setup MinIO
docker-compose up minio

# Run migration scripts
python tools/migrate_chromadb_to_pgvector.py
python tools/migrate_filesystem_to_minio.py
```

#### **Step 2: Build Services theo thứ tự** (Week 2-5)

```
Priority 1: Storage Service (foundation)
Priority 2: Vector Service (core search)
Priority 3: Session Service (state management)
Priority 4: Router Service (routing logic)
Priority 5: Reranker Service (quality improvement)
Priority 6: RAG Orchestrator (orchestration)
```

#### **Step 3: Integration** (Week 5-6)

- Service-to-service communication testing
- End-to-end testing
- Performance benchmarking
- Frontend integration

---

## 📝 **NEXT STEPS**

Anh muốn em:

1. ✅ **Bắt đầu viết code cho từng service?** (em sẽ bắt đầu từ Storage Service)
2. ✅ **Tạo docker-compose.yml cho toàn bộ stack?**
3. ✅ **Viết migration scripts (ChromaDB → pgvector, FileSystem → MinIO)?**
4. ✅ **Tạo folder structure cho tất cả services?**

Anh chọn bắt đầu từ đâu nhé? 🚀
