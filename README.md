# 🏛️ LegalRAG - Hệ thống Trợ lý Pháp luật AI

> **Hệ thống hỏi-đáp thông minh về thủ tục hành chính** sử dụng công nghệ RAG (Retrieval-Augmented Generation) với PhoGPT-4B và ChromaDB.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-19.1.1-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)

---

## ✨ Tính năng chính

### 🤖 **AI Core**

- **PhoGPT-4B**: Mô hình ngôn ngữ lớn tiếng Việt từ VinAI Research
- **Smart Query Router**: Định tuyến câu hỏi thông minh với cache system
- **Multi-turn Clarification**: Hỏi lại làm rõ khi câu hỏi mơ hồ
- **VRAM-optimized**: Tối ưu bộ nhớ GPU cho hiệu năng cao

### � **RAG System**

- **ChromaDB**: Vector database semantic search
- **Context Expansion**: Mở rộng ngữ cảnh thông minh
- **Result Reranking**: Xếp hạng kết quả với cross-encoder
- **Document Processing**: Xử lý tài liệu JSON tự động

### 🌐 **Modern Web Interface**

- **React 19** + TypeScript với Vite
- **Tailwind CSS**: Giao diện đẹp, responsive
- **Real-time Chat**: WebSocket cho trải nghiệm mượt mà
- **Loading States**: UX tối ưu với loading indicators

### 🚀 **Production Ready**

- **FastAPI**: Backend hiệu năng cao
- **Docker Support**: Containerization hoàn chỉnh
- **Self-contained**: Models và data lưu nội bộ
- **Monitoring**: Logging và health checks

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Services   │
│                 │    │                 │    │                 │
│ • React 19      │◄──►│ • FastAPI       │◄──►│ • PhoGPT-4B     │
│ • TypeScript    │    │ • Smart Router  │    │ • ChromaDB      │
│ • Tailwind CSS  │    │ • RAG Engine    │    │ • Reranker      │
│ • Lucide Icons  │    │ • Context Exp.  │    │ • Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 📁 Cấu trúc dự án

```
LegalRAG_Fixed/
├── 🎨 frontend/                    # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/              # Chat interface components
│   │   │   │   ├── ChatInterfaceUnified.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── ...
│   │   │   └── ui/                # Reusable UI components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── services/              # API services
│   │   └── types/                 # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts
│
├── 🔧 backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── api/                   # API routes
│   │   │   ├── routes.py          # Main endpoints
│   │   │   └── optimized_routes.py
│   │   ├── services/              # Business logic
│   │   │   ├── rag_engine.py      # RAG orchestration
│   │   │   ├── smart_router.py    # Query routing
│   │   │   ├── language_model.py  # LLM interface
│   │   │   ├── vector_database.py # Vector operations
│   │   │   └── smart_clarification.py
│   │   ├── core/
│   │   │   └── config.py          # Configuration
│   │   └── models/
│   │       └── schemas.py         # Pydantic models
│   │
│   ├── data/                      # Data storage
│   │   ├── documents/             # Processed documents
│   │   ├── models/                # LLM models
│   │   ├── vectordb/              # ChromaDB storage
│   │   ├── router_examples_smart_v3/  # Training data
│   │   └── cache/                 # Cache storage
│   │
│   ├── tools/                     # Development tools
│   │   ├── 1_setup_models.py      # Model setup
│   │   ├── 2_build_vectordb_unified.py
│   │   ├── 3_generate_smart_router.py
│   │   └── 4_build_router_cache.py
│   │
│   ├── archive/                   # Legacy code and backups
│   ├── main.py                    # Entry point
│   ├── requirements.txt           # Python dependencies
│   ├── docker-compose.yml         # Docker setup
│   └── Dockerfile
│
├── � scripts/                    # Development scripts
│   ├── tests/                     # Test suite
│   │   ├── test_*.py             # Functional tests
│   │   └── test_query.json       # Test data
│   ├── debug/                     # Debug utilities
│   │   ├── debug_*.py            # Debug scripts
│   │   └── simple_llm_test.py    # Simple LLM test
│   └── phase1_summary_report.py   # Project reports
│
├── �📚 docs/                       # Comprehensive documentation
│   ├── QUICKSTART.md             # Quick start guide
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── CONFIG_SYSTEM.md          # Configuration docs
│   ├── ENHANCED_RAG_SYSTEM.md    # RAG system details
│   └── *.md                      # Other technical docs
└── 🔧 [config files]             # Git, license, etc.
```

---

## 🚀 Khởi động nhanh

### 🔧 Yêu cầu hệ thống

| Component   | Minimum  | Recommended |
| ----------- | -------- | ----------- |
| **RAM**     | 8GB      | 16GB+       |
| **Storage** | 10GB     | 20GB+       |
| **CPU**     | 4 cores  | 8+ cores    |
| **GPU**     | Optional | RTX 3060+   |
| **Python**  | 3.8+     | 3.11+       |

### 1️⃣ **Backend Setup**

```bash
cd backend

# Tạo virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Setup models và data
python tools/1_setup_models.py
python tools/2_build_vectordb_unified.py
python tools/3_generate_smart_router.py

# Khởi động server
python main.py
```

### 2️⃣ **Frontend Setup**

```bash
cd frontend

# Cài đặt dependencies
npm install

# Khởi động dev server
npm run dev
```

### 3️⃣ **Truy cập ứng dụng**

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🐳 Docker Deployment

```bash
# Backend with Docker Compose
cd backend
docker-compose up --build

# Hoặc build riêng lẻ
docker build -t legalrag-backend .
docker run -p 8000:8000 legalrag-backend
```

---

## 📡 API Usage

### 🤖 **Chat Query**

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Thủ tục đăng ký khai sinh cần giấy tờ gì?",
    "max_tokens": 2048,
    "temperature": 0.7,
    "conversation_id": "unique-session-id"
  }'
```

### 📊 **Health Check**

```bash
curl http://localhost:8000/api/v1/health
```

### 🔄 **Clarification Response**

```bash
curl -X POST "http://localhost:8000/api/v1/clarification" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "unique-session-id",
    "selected_option": "ho_tich_cap_xa",
    "original_question": "thủ tục đăng ký"
  }'
```

---

## 📚 Tài liệu được hỗ trợ

Hệ thống đã được huấn luyện trên các lĩnh vực:

### 🏛️ **Hộ tịch cấp xã** (35+ thủ tục)

- Đăng ký khai sinh, kết hôn, khai tử
- Đăng ký giám hộ, chấm dứt giám hộ
- Thay đổi, cải chính thông tin hộ tịch
- Cấp bản sao, xác nhận hộ tịch

### 📋 **Chứng thực** (12+ thủ tục)

- Chứng thực hợp đồng, di chúc
- Chứng thực bản sao giấy tờ
- Chứng thực chữ ký, dịch thuật
- Cấp bản sao từ sổ gốc

### 👨‍👩‍👧‍👦 **Nuôi con nuôi** (3+ thủ tục)

- Đăng ký việc nuôi con nuôi trong nước
- Giải quyết nuôi con nuôi có yếu tố nước ngoài
- Đăng ký lại việc nuôi con nuôi

---

## 🛠️ Development

### 🧪 **Testing**

```bash
# Run comprehensive tests
cd scripts/tests
python test_enhanced_rag.py
python test_smart_router.py
python test_clarification_fix.py

# Debug specific issues
cd scripts/debug
python debug_llm_hallucination.py
python simple_llm_test.py
```

### 📊 **Monitoring**

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# View logs
docker-compose logs -f backend
```

### 🔧 **Configuration**

Tùy chỉnh trong `backend/.env`:

```env
# LLM Settings
LLM_MODEL_NAME=VinAI/PhoGPT-4B-Chat
MAX_TOKENS=2048
TEMPERATURE=0.7

# Vector DB
CHROMA_PERSIST_DIRECTORY=./data/vectordb
COLLECTION_NAME=legal_documents

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🤝 Đóng góp

1. **Fork** repository
2. **Tạo branch** cho feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to branch (`git push origin feature/AmazingFeature`)
5. **Tạo Pull Request**

---

## 📄 License

Dự án được phát hành dưới [MIT License](LICENSE).

---

## 👨‍💻 Tác giả

**Nguyễn Thanh Hiếu** - _Lead Developer_

- GitHub: [@thhieu2904](https://github.com/thhieu2904)
- Email: thhieu2904@gmail.com

---

## 🙏 Acknowledgments

- **VinAI Research** cho PhoGPT-4B model
- **ChromaDB** team cho vector database
- **FastAPI** và **React** communities
- **Trung tâm Phục vụ Hành chính Công** xã Long Phú

---

<p align="center">
  <strong>🏛️ LegalRAG - Đưa công nghệ AI vào phục vụ dân</strong>
</p>
