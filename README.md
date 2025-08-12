# LegalRAG

Hệ thống hỏi-đáp thông minh về thủ tục hành chính sử dụng RAG (Retrieval-Augmented Generation) với PhoGPT-4B và ChromaDB.

## Tính năng chính

- 🤖 **PhoGPT-4B**: Mô hình ngôn ngữ lớn tiếng Việt từ HuggingFace
- 🔍 **RAG System**: Kết hợp tìm kiếm và sinh text cho câu trả lời chính xác
- 📚 **ChromaDB**: Vector database để lưu trữ và tìm kiếm semantic
- 📄 **Document Processing**: Xử lý tài liệu Word (.doc/.docx) tự động
- 🚀 **FastAPI**: Backend API hiện đại, nhanh chóng
- 🐳 **Docker Ready**: Triển khai dễ dàng trong môi trường doanh nghiệp
- 💾 **Self-contained**: Models và data được lưu nội bộ

## Cấu trúc dự án

```
LegalRAG/
├── backend/                 # Backend API (FastAPI)
│   ├── app/                # Core application
│   │   ├── api/            # API routes
│   │   ├── core/           # Cấu hình
│   │   ├── models/         # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── data/               # Data storage
│   │   ├── documents/      # Tài liệu đã xử lý
│   │   ├── models/         # LLM models
│   │   ├── vectordb/       # ChromaDB
│   │   └── cache/          # Cache
│   ├── scripts/            # Utility scripts
│   ├── tests/              # Test suite
│   ├── tools/              # Development tools
│   ├── main.py            # Entry point (Production)
│   └── requirements.txt   # Dependencies
├── frontend/               # Frontend (React + TypeScript)
├── docs/                   # Documentation
└── [config files]         # Git, license, etc.
```

## Khởi động nhanh

### Bước 1: Setup Backend

```bash
cd backend

# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

### Bước 2: Khởi động server

```bash
# Activate virtual environment
# Windows: venv\Scripts\activate.bat
# Linux/Mac: source venv/bin/activate

# Start server
python main.py
```

### Bước 3: Test API

Truy cập:

- API Documentation: http://localhost:8000/docs
- Test script: `python test_api.py`

## Sử dụng Docker

```bash
cd backend
docker-compose up --build
```

## API Usage

### Hỏi đáp

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Thủ tục đăng ký khai sinh cần giấy tờ gì?",
    "max_tokens": 2048,
    "temperature": 0.7,
    "top_k": 5
  }'
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

## Tài liệu được xử lý

Hệ thống đã được huấn luyện trên các tài liệu về:

- **Hộ tịch cấp xã**: Đăng ký khai sinh, kết hôn, khai tử, giám hộ...
- **Chứng thực**: Chứng thực hợp đồng, di chúc, bản sao giấy tờ...
- **Nuôi con nuôi**: Quy trình đăng ký nuôi con nuôi trong nước và quốc tế

## Yêu cầu hệ thống

- **RAM**: 8GB+ (khuyến nghị 16GB)
- **Storage**: 10GB+ cho models và data
- **CPU**: 4+ cores
- **Python**: 3.8+
- **OS**: Windows, Linux, macOS

## Đóng góp

Dự án được phát triển bởi Nguyễn Thanh Hiếu.

## License

MIT License - xem file [LICENSE](LICENSE)
