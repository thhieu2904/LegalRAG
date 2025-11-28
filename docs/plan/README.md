# 📋 LegalRAG - Implementation Plan Overview

> **Phiên bản**: v1.0  
> **Ngày tạo**: 2025-11-28  
> **Branch**: refactor_rag

---

## 🎯 MỤC TIÊU TỔNG QUAN

Giải quyết 2 vấn đề chính của hệ thống LegalRAG:

1. **Session Management & Document Pinning** - Cải thiện UX khi user hỏi follow-up
2. **GPU Memory Swap Mechanism** - Hỗ trợ chạy trên GPU 8GB VRAM

---

## 📁 CẤU TRÚC TÀI LIỆU

```
docs/plan/
├── README.md                         # File này (tổng quan)
├── 01_SESSION_MANAGEMENT_PLAN.md     # Chi tiết Session/Pinning
└── 02_GPU_SWAP_MECHANISM_PLAN.md     # Chi tiết GPU Swap
```

---

## 📊 TỔNG HỢP THAY ĐỔI

### Issue 1: Session Management & Document Pinning

| Component         | Thay đổi                                         | Độ phức tạp |
| ----------------- | ------------------------------------------------ | ----------- |
| **query-service** | Thêm `/session/clear`, `/session/info` endpoints | Trung bình  |
| **query-service** | Semantic topic detection (embedding similarity)  | Cao         |
| **query-service** | Enhanced QueryResponse với session_info          | Thấp        |
| **frontend**      | Simplify session management                      | Thấp        |
| **frontend**      | Thêm "Chủ đề mới" button                         | Thấp        |

**Effort estimate**: 4-5 ngày

### Issue 2: GPU Memory Swap Mechanism

| Component             | Thay đổi                                   | Độ phức tạp |
| --------------------- | ------------------------------------------ | ----------- |
| **rerank-service**    | Thêm `/prepare`, `/release` endpoints      | Trung bình  |
| **rerank-service**    | Implement `load_model()`, `unload_model()` | Trung bình  |
| **llm-service**       | Thêm `/prepare`, `/release` endpoints      | Trung bình  |
| **llm-service**       | Implement `load_model()`, `unload_model()` | Trung bình  |
| **embedding-service** | Conditional CPU/GPU based on swap mode     | Thấp        |
| **query-service**     | Swap orchestration logic                   | Cao         |
| **docker-compose**    | Tạo 2 config: dev (swap) và prod (no-swap) | Thấp        |

**Effort estimate**: 4-5 ngày

---

## 🔄 IMPLEMENTATION ORDER

### Recommended sequence:

```
Week 1: GPU Swap (ưu tiên vì blocking development)
├── Day 1-2: Implement swap in rerank-service & llm-service
├── Day 3: Query-service orchestration
├── Day 4: Docker config & testing
└── Day 5: Optimization & monitoring

Week 2: Session Management
├── Day 1-2: Backend endpoints & semantic detection
├── Day 3: Frontend changes
├── Day 4: Integration testing
└── Day 5: Polish & documentation
```

### Lý do ưu tiên GPU Swap:

1. **Blocking issue**: Không chạy được trên laptop dev 8GB VRAM
2. **Independent**: Không phụ thuộc vào Session changes
3. **Infrastructure**: Cần hoạt động trước khi phát triển features khác

---

## 🧪 TESTING CHECKLIST

### GPU Swap Mode

- [ ] Swap mode works on 8GB GPU
- [ ] No-swap mode works on 16GB+ GPU
- [ ] Latency overhead < 20s per query (swap mode)
- [ ] No memory leak after 100 queries
- [ ] Graceful handling when prepare fails

### Session Management

- [ ] New session created for new tab
- [ ] Follow-up questions use pinned document
- [ ] "Chủ đề mới" clears pinned document
- [ ] Semantic topic detection auto-clears when similarity < 0.4
- [ ] Session expires after 30 minutes

---

## ⚙️ ENV CONFIGURATION SUMMARY

```bash
# =============================================================================
# GPU SWAP MODE (Issue 2)
# =============================================================================
GPU_SWAP_MODE=true|false        # true for 8GB, false for 16GB+
EMBEDDING_DEVICE=cpu|cuda       # cpu in swap mode
RERANK_DEVICE=cuda              # always cuda for speed
LLM_DEVICE=cuda                 # always cuda
LLM_GPU_LAYERS=-1               # all layers on GPU

# =============================================================================
# SESSION CONFIG (Issue 1) - Already in query-service
# =============================================================================
SESSION_EXPIRY_MINUTES=30       # Session expiration time
TOPIC_CHANGE_THRESHOLD=0.4      # Semantic similarity threshold
```

---

## 📝 MIGRATION NOTES

### Breaking Changes: **NONE**

- Existing sessions continue to work
- Existing API contracts unchanged
- New endpoints are additions, not modifications

### Backward Compatibility

1. **Frontend**: Old session_id format still accepted
2. **Backend**: Creates new session if old one not found
3. **GPU**: Defaults to no-swap mode (existing behavior)

---

## 🚀 QUICK START

### Sau khi implement:

```bash
# Development (8GB GPU) - với swap
docker-compose up -d

# Production (16GB+ GPU) - không swap
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📚 REFERENCE FILES

### Tham khảo từ rag_service_old:

| File                                              | Nội dung tham khảo                  |
| ------------------------------------------------- | ----------------------------------- |
| `rag_service_old/app/core/config.py`              | `enable_vram_swapping` pattern      |
| `rag_service_old/app/services/reranker.py`        | `unload_model()`, `ensure_loaded()` |
| `rag_service_old/app/services/language_model.py`  | LLM load/unload pattern             |
| `rag_service_old/app/services/vector.py`          | Device selection based on swap mode |
| `rag_service_old/app/services/session_manager.py` | Session persistence pattern         |

### Schema reference:

| Table            | Usage                              |
| ---------------- | ---------------------------------- |
| `query_sessions` | Session storage with context JSONB |
| `query_logs`     | Query logging với session_id       |

---

## 🎉 SUCCESS CRITERIA

### GPU Swap

- [x] Chạy được trên RTX 3060 6GB (laptop dev)
- [x] Không ảnh hưởng performance trên server 16GB+
- [x] Dễ switch qua ENV variable

### Session Management

- [x] User có thể explicit "Chủ đề mới" để reset pinned doc
- [x] System tự detect topic change và reset
- [x] Full logging cho analytics
- [x] Consistent experience across tabs/devices

---

## 🤝 CONTRIBUTORS

- **Analysis & Planning**: Claude (Anthropic)
- **Implementation**: [Your Name]

---

_Last updated: 2025-11-28_
