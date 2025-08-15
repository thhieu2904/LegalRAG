# 📚 LegalRAG Documentation

> **Comprehensive documentation for LegalRAG system**

## 📖 **Table of Contents**

- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Deployment Guide](#deployment-guide)
- [Configuration](#configuration)
- [Development](#development)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- 8GB+ RAM
- 10GB+ Storage

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
python tools/1_setup_models.py
python tools/2_build_vectordb_unified.py
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🏗️ System Architecture

### Core Components

#### **RAG Engine**

- **Vector Database**: ChromaDB with semantic search
- **LLM**: PhoGPT-4B for Vietnamese language
- **Smart Router**: Intelligent query routing with cache
- **Context Expansion**: Enhanced context understanding

#### **AI Services**

- **Query Classification**: Automatic query categorization
- **Multi-turn Clarification**: Ask for clarification when ambiguous
- **Result Reranking**: Cross-encoder for better results
- **VRAM Optimization**: Efficient GPU memory usage

#### **Web Interface**

- **React 19**: Modern frontend framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Responsive design
- **Real-time Chat**: WebSocket communication

### Data Flow

```
User Query → Smart Router → RAG Engine → LLM → Response
     ↑                                           ↓
     └────── Clarification ← Context Analysis ←──┘
```

---

## 🐳 Deployment Guide

### Docker Deployment

```bash
# Backend only
cd backend
docker-compose up --build

# Full stack deployment
docker build -t legalrag-backend backend/
docker build -t legalrag-frontend frontend/
```

### Production Configuration

```env
# .env file
LLM_MODEL_NAME=VinAI/PhoGPT-4B-Chat
API_HOST=0.0.0.0
API_PORT=8000
CHROMA_PERSIST_DIRECTORY=./data/vectordb
```

### Monitoring

- Health check: `/api/v1/health`
- Metrics: Built-in FastAPI metrics
- Logs: Structured JSON logging

---

## ⚙️ Configuration

### Backend Config (`backend/app/core/config.py`)

```python
# LLM Settings
MAX_TOKENS = 2048
TEMPERATURE = 0.7
TOP_K = 5

# Vector Database
COLLECTION_NAME = "legal_documents"
EMBEDDING_MODEL = "VinAI/PhoBERT-base"

# API Settings
CORS_ORIGINS = ["http://localhost:5173"]
```

### Frontend Config (`frontend/vite.config.ts`)

```typescript
export default defineConfig({
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

---

## 🛠️ Development

### Project Structure

```
LegalRAG_Fixed/
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── scripts/           # Dev scripts & tests
├── docs/              # Documentation
└── README.md          # Main readme
```

### Testing

```bash
# Core functionality tests
cd scripts/tests
python test_enhanced_rag.py
python test_smart_router.py
python test_clarification_fix.py

# Debug utilities
cd scripts/debug
python debug_llm_hallucination.py
python simple_llm_test.py
```

### API Testing

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Thủ tục đăng ký khai sinh cần giấy tờ gì?",
    "conversation_id": "test-123"
  }'
```

---

## 📋 Supported Documents

### Administrative Procedures

#### **Hộ tịch cấp xã** (Civil Status - Commune level)

- Birth registration (Đăng ký khai sinh)
- Marriage registration (Đăng ký kết hôn)
- Death registration (Đăng ký khai tử)
- Guardianship registration (Đăng ký giám hộ)

#### **Chứng thực** (Notarization)

- Contract notarization (Chứng thực hợp đồng)
- Document copy certification (Chứng thực bản sao)
- Signature certification (Chứng thực chữ ký)
- Translation certification (Chứng thực dịch thuật)

#### **Nuôi con nuôi** (Adoption)

- Domestic adoption registration
- International adoption procedures
- Adoption re-registration

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

### Code Standards

- Python: PEP 8, type hints
- TypeScript: Strict mode, ESLint
- Documentation: Keep docs updated

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

## 👨‍💻 Author

**Nguyễn Thanh Hiếu**

- GitHub: [@thhieu2904](https://github.com/thhieu2904)
- Email: thhieu2904@gmail.com

---

_Last updated: August 15, 2025_
