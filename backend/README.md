# VRAM-Optimized LegalRAG Backend

## 🎯 Kiến trúc VRAM-Optimized

Hệ thống RAG tối ưu hóa VRAM với phân bổ thông minh giữa CPU và GPU:

```
Embedding Model (CPU) → Broad Search → Reranker (GPU) → Context Expansion → LLM (GPU)
```

### 🏗️ Phân bổ tài nguyên:

- **Embedding Model**: CPU (tiết kiệm VRAM, xử lý query ngắn)
- **LLM (PhoGPT-4B)**: GPU (song song hóa, context dài)
- **Reranker**: GPU (so sánh chéo nhiều chunks)

### 🧠 Tính năng thông minh:

1. **Ambiguous Query Detection** - Phát hiện câu hỏi mơ hồ tự động
2. **Nucleus Context Expansion** - Mở rộng ngữ cảnh từ chunk hạt nhân
3. **Session Management** - Quản lý hội thoại thông minh
4. **VRAM Optimization** - Sử dụng tối ưu bộ nhớ GPU

## 📁 Cấu trúc Project

```
backend/
├── main.py                          # 🚀 Entry point chính
├── summary_test.py                   # 🧪 Test suite chính
├── .env                             # ⚙️ Cấu hình
├── app/
│   ├── api/
│   │   └── optimized_routes.py      # 🌐 API v2 endpoints
│   ├── services/
│   │   ├── optimized_enhanced_rag_service.py  # 🎯 Service chính
│   │   ├── ambiguous_query_service.py         # 🧠 Xử lý câu hỏi mơ hồ
│   │   ├── enhanced_context_expansion_service.py # 📖 Mở rộng ngữ cảnh
│   │   ├── vectordb_service.py      # 💾 Vector DB (CPU embedding)
│   │   ├── llm_service.py          # 🤖 LLM (GPU)
│   │   └── reranker_service.py     # 🎯 Reranker (GPU)
│   └── core/
│       └── config.py               # ⚙️ Configuration
├── data/
│   ├── documents/                  # 📄 Source documents
│   ├── vectordb/                   # 💾 ChromaDB
│   └── models/                     # 🤖 AI models
└── archive/                        # 📦 Old files
```

## 🚀 Quick Start

### 1. Khởi chạy server:

```bash
conda activate LegalRAG_v1
cd backend
python main.py
```

### 2. Test hệ thống:

```bash
python summary_test.py
```

### 3. API Endpoints:

- **Health Check**: `GET /api/v2/health`
- **Query**: `POST /api/v2/optimized-query`
- **Session Create**: `POST /api/v2/session/create`
- **Session Info**: `GET /api/v2/session/{session_id}`
- **Clarification**: `POST /api/v2/clarify`
- **Documentation**: `GET /docs`

## 📊 API Response Example

### Ambiguous Query Detection:

```json
{
  "type": "clarification_needed",
  "category": "general_procedure",
  "confidence": 1.0,
  "clarification": {
    "template": "Bạn muốn hỏi về thủ tục gì cụ thể?",
    "options": ["Thủ tục A", "Thủ tục B", ...]
  },
  "generated_questions": ["Câu hỏi làm rõ 1", "Câu hỏi làm rõ 2", ...],
  "session_id": "uuid",
  "processing_time": 0.15
}
```

### Clear Query Response:

```json
{
  "type": "answer",
  "answer": "Detailed answer based on documents...",
  "context_info": {
    "nucleus_chunks": 5,
    "context_length": 2847,
    "source_collections": ["ho_tich_cap_xa"],
    "source_documents": ["document1.pdf", "document2.pdf"]
  },
  "session_id": "uuid",
  "processing_time": 2.34
}
```

## 🔧 Core Services

### OptimizedEnhancedRAGService

**Vị trí**: `app/services/optimized_enhanced_rag_service.py`

- VRAM-optimized architecture
- Ambiguous query detection
- Nucleus context expansion
- Session management

### Supporting Services:

- `VectorDBService` - ChromaDB với embedding CPU
- `LLMService` - PhoGPT-4B trên GPU
- `RerankerService` - Vietnamese Reranker trên GPU
- `AmbiguousQueryService` - Phát hiện câu hỏi mơ hồ
- `EnhancedContextExpansionService` - Mở rộng ngữ cảnh

## 🎛️ Configuration

Key environment variables in `.env`:

```bash
# VRAM Optimization
EMBEDDING_MODEL_NAME=AITeamVN/Vietnamese_Embedding_v2
RERANKER_MODEL_NAME=AITeamVN/Vietnamese_Reranker
LLM_MODEL_PATH=data/models/llm_dir/PhoGPT-4B-Chat-Q4_K_M.gguf

# Performance Settings
MAX_TOKENS=1024
TEMPERATURE=0.2
CONTEXT_LENGTH=4096
BROAD_SEARCH_K=15
SIMILARITY_THRESHOLD=0.35

# Features
USE_ROUTING=true
USE_RERANKER=true
```

## 📈 Performance Metrics

- **VRAM Usage**: ~4-5GB (optimized from ~7-8GB)
- **Query Processing**: ~0.15s (ambiguous detection)
- **Answer Generation**: ~2-3s (with context expansion)
- **Collections**: 3 collections, 262 documents
- **Accuracy**: High precision với reranker + context expansion

## 🧪 Testing

```bash
# Full system test
python summary_test.py

# Manual API test
curl -X POST "http://localhost:8000/api/v2/optimized-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "thủ tục như thế nào"}'
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v2/health

---

🔥 **VRAM-Optimized LegalRAG** - Intelligent legal Q&A system with optimized resource allocation

## Troubleshooting

### Model download fails

```bash
# Download thủ công
mkdir -p data/models
wget -O data/models/PhoGPT-4B-Chat-q8_0.gguf \
  https://huggingface.co/nguyenviet/PhoGPT-4B-Chat-GGUF/resolve/main/PhoGPT-4B-Chat-q8_0.gguf
```

### Memory issues

- Giảm `n_ctx` trong config
- Tăng swap space
- Sử dụng model nhỏ hơn

### Performance tuning

- Tăng `n_threads` theo số CPU cores
- Điều chỉnh `chunk_size` và `top_k`
- Sử dụng SSD cho vector database

## API Documentation

Khi server đang chạy, truy cập:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
