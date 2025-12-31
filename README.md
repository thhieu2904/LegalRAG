# LegalRAG

Hệ thống hỏi-đáp pháp luật Việt Nam sử dụng công nghệ Retrieval-Augmented Generation (RAG).

## Tổng quan

LegalRAG là hệ thống chatbot hỏi-đáp pháp luật, hỗ trợ công dân tra cứu thông tin về các thủ tục hành chính, quy trình pháp lý, và các văn bản pháp luật Việt Nam. Hệ thống sử dụng kiến trúc microservices, kết hợp tìm kiếm ngữ nghĩa (semantic search) với mô hình ngôn ngữ lớn (LLM) để tạo câu trả lời chính xác và có trích dẫn nguồn.

### Chức năng chính

- Hỏi-đáp pháp luật bằng ngôn ngữ tự nhiên
- Tìm kiếm ngữ nghĩa trong kho văn bản pháp luật
- Hiển thị nguồn trích dẫn (văn bản, điều khoản)
- Điền biểu mẫu thủ tục hành chính
- Quản lý tài liệu và bộ thủ tục (admin)

## Kiến trúc hệ thống

```
                            ┌─────────────────┐
                            │    Frontend     │
                            │  (React + TS)   │
                            │      :3000      │
                            └────────┬────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │  Admin Service  │    │  Query Service  │    │  Form Service   │
    │   (FastAPI)     │    │   (FastAPI)     │    │   (FastAPI)     │
    │      :8001      │    │      :8002      │    │      :8015      │
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                      │                      │
             │         ┌────────────┼────────────┐         │
             │         │            │            │         │
             ▼         ▼            ▼            ▼         ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                    Internal Services                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
    │  │  Embedding  │  │   Vector    │  │   Rerank    │           │
    │  │   :8011     │  │   :8012     │  │   :8013     │           │
    │  └─────────────┘  └─────────────┘  └─────────────┘           │
    │  ┌─────────────┐  ┌─────────────┐                             │
    │  │     LLM     │  │   Storage   │                             │
    │  │   :8014     │  │   :8010     │                             │
    │  └─────────────┘  └─────────────┘                             │
    └───────────────────────────────────────────────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   PostgreSQL    │    │     MinIO       │    │   GPU (CUDA)    │
    │   + pgvector    │    │  Object Store   │    │ Embedding/Rerank│
    │      :5432      │    │   :9000/:9001   │    │                 │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Các microservices

| Service           | Port | Chức năng                                        |
| ----------------- | ---- | ------------------------------------------------ |
| Frontend          | 3000 | Giao diện người dùng (React + TypeScript + Vite) |
| Admin Service     | 8001 | Quản lý tài liệu, xác thực admin, dashboard      |
| Query Service     | 8002 | Điều phối RAG, xử lý hỏi-đáp, quản lý session    |
| Storage Service   | 8010 | Lưu trữ file (MinIO), trích xuất text PDF/DOCX   |
| Embedding Service | 8011 | Tạo vector embedding, chunking text              |
| Vector Service    | 8012 | Tìm kiếm vector (pgvector), CRUD chunks          |
| Rerank Service    | 8013 | Xếp hạng lại kết quả tìm kiếm                    |
| LLM Service       | 8014 | Sinh câu trả lời (Gemini API)                    |
| Form Service      | 8015 | Render và điền biểu mẫu DOCX                     |

## Yêu cầu hệ thống

### Phần cứng

- RAM: 16GB (khuyến nghị 32GB)
- GPU: NVIDIA với CUDA (4GB VRAM cho embedding + rerank)
- Lưu trữ: 50GB

### Phần mềm

- Docker và Docker Compose
- NVIDIA Container Toolkit (cho GPU)
- Gemini API key (cho LLM service)

## Cài đặt và chạy

### 1. Clone repository

```bash
git clone <repository-url>
cd LegalRAG
```

### 2. Cấu hình environment

Tạo file `.env` trong thư mục `llm-service`:

```env
GEMINI_API_KEY=your-api-key-here
```

### 3. Khởi động hệ thống

```bash
docker compose up -d
```

### 4. Truy cập

- Giao diện người dùng: http://localhost:3000
- Admin dashboard: http://localhost:3000/admin
- MinIO Console: http://localhost:9001 (minioadmin / minioadmin123)

## Cấu trúc thư mục

```
LegalRAG/
├── frontend/           # Giao diện React + TypeScript
├── admin-service/      # API quản lý tài liệu
├── query-service/      # API hỏi-đáp RAG
├── storage-service/    # Lưu trữ và trích xuất text
├── embedding-service/  # Tạo vector embedding
├── vector-service/     # Tìm kiếm vector
├── rerank-service/     # Xếp hạng kết quả
├── llm-service/        # Sinh câu trả lời
├── form-service/       # Xử lý biểu mẫu
├── docs/               # Tài liệu và văn bản pháp luật
├── scripts/            # Scripts tiện ích
├── prod/               # Cấu hình production
├── BaoCao/             # Scripts đánh giá hệ thống
├── schema_new.sql      # Database schema
└── docker-compose.yml  # Cấu hình Docker
```

## Công nghệ sử dụng

### Backend

- Python 3.11+
- FastAPI
- PostgreSQL 16 với pgvector
- MinIO (S3-compatible storage)

### AI/ML

- Embedding: `dangvantuan/vietnamese-document-embedding` (768 chiều)
- Reranker: `BAAI/bge-reranker-v2-m3`
- LLM: Google Gemini API

### Frontend

- React 18
- TypeScript
- Vite
- shadcn/ui

## Database

Hệ thống sử dụng PostgreSQL với extension pgvector để lưu trữ và tìm kiếm vector. Các bảng chính:

- `collections`: Bộ thủ tục (nhóm tài liệu)
- `documents`: Văn bản pháp luật
- `chunks`: Đoạn text với vector embedding
- `forms`: Biểu mẫu thủ tục
- `query_sessions`: Phiên hội thoại
- `query_logs`: Log truy vấn
- `admin_users`: Tài khoản quản trị

## License

MIT License
