# 🎯 LegalRAG - Luồng chính và Cấu trúc

## 📋 LUỒNG CHÍNH DÀNH CHO USER

### 🚀 Khởi động hệ thống:

```bash
cd backend
python main.py
```

### 🧪 Test hệ thống:

```bash
python summary_test.py
```

## 📁 CẤU TRÚC FILE CHÍNH (Chỉ những file cần thiết)

```
backend/
├── main.py                          # 🎯 ENTRY POINT - Server chính
├── summary_test.py                   # ✅ Test chính - Validate toàn hệ thống
├── .env                             # ⚙️ Cấu hình môi trường
├── requirements.txt                  # 📦 Dependencies
├── README.md                        # 📖 Documentation
│
├── app/
│   ├── api/
│   │   └── optimized_routes.py      # 🌐 API v2 endpoints
│   ├── services/                    # 🔧 Core Services
│   │   ├── optimized_enhanced_rag_service.py  # 🎯 Service chính
│   │   ├── vectordb_service.py      # 💾 Vector DB (CPU embedding)
│   │   ├── llm_service.py          # 🤖 LLM (GPU)
│   │   ├── reranker_service.py     # 🎯 Reranker (GPU)
│   │   ├── ambiguous_query_service.py    # 🧠 Ambiguous detection
│   │   ├── enhanced_context_expansion_service.py # 📖 Context expansion
│   │   ├── json_document_processor.py     # 📄 JSON processor
│   │   └── query_router.py         # 🚦 Query routing
│   ├── models/                     # 📋 Pydantic models
│   ├── core/                       # 🔧 Core configurations
│   └── utils/                      # 🛠️ Utilities
│
├── data/
│   ├── vectordb/                   # 💾 ChromaDB database
│   ├── documents/                  # 📄 Source documents
│   └── models/                     # 🤖 AI models
│
└── archive/                        # 📦 OLD FILES - Không quan tâm
```

## 🔗 FRONTEND CẤP NHẬT

### API v2 Endpoints được cập nhật:

- `GET /api/v2/health` - Health check
- `POST /api/v2/optimized-query` - Query chính
- `POST /api/v2/session/create` - Tạo session
- `GET /api/v2/session/{id}` - Thông tin session

### Files frontend đã cập nhật:

- `frontend/src/services/api.ts` - Cập nhật API v2
- `frontend/src/types/chat.ts` - Support clarification response

## ✅ CÁC FILE ĐÃ DỌN DẸP (Đã xóa):

### Backend:

- ❌ `document_processor.py` - Không dùng (chuyển JSON)
- ❌ `optimized_main.py` - Đã copy thành main.py
- ❌ `document_processor_old.py` - File cũ
- ❌ `optimized_enhanced_rag_service_old.py` - File cũ
- ❌ `download_vinai_model.py` → archive/
- ❌ `ENHANCED_README.md` → archive/

### Tất cả files test cũ đã chuyển vào `archive/`

## 🎯 CHẠY HỆ THỐNG

1. **Backend**: `python main.py`
2. **Frontend**: `npm run dev`
3. **Test**: `python summary_test.py`

---

✨ **Hệ thống clean - chỉ những file cần thiết cho VRAM-optimized LegalRAG**
