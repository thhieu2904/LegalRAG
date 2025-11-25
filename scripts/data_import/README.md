# LegalRAG Data Import Tools

# ===========================

Thư mục này chứa các công cụ để import dữ liệu vào hệ thống LegalRAG.

## 📁 Cấu trúc thư mục

```
scripts/data_import/
├── Dockerfile.converter     # Docker image với LibreOffice
├── import_data.py          # Script Python import chính
├── collections_mapping.json # Mapping thư mục → collection
├── cleanup_old_data.sql    # SQL script xóa dữ liệu cũ
├── input/                  # (mount từ docs/Văn bản pháp luật)
├── output/                 # PDFs đã convert
└── logs/                   # Log files
```

## 🚀 Cách sử dụng

### Bước 1: Khởi động các services chính

```bash
# Đảm bảo PostgreSQL và MinIO đang chạy
docker compose up -d postgres-vector minio
```

### Bước 2: Chạy import

```bash
# Build và chạy import service
docker compose -f docker-compose.import.yml up --build

# Hoặc chỉ xem dry-run (không thay đổi dữ liệu)
docker compose -f docker-compose.import.yml run --rm data-import python import_data.py --dry-run
```

### Bước 3: Kiểm tra kết quả

```bash
# Xem logs
cat scripts/data_import/logs/import_*.log

# Kiểm tra database
docker exec -it legalrag-postgres psql -U legalrag -d legalrag -c "SELECT name, display_name, document_count FROM collections;"
```

## 🧹 Xóa dữ liệu test cũ

### Option 1: Chạy SQL script

```bash
docker exec -i legalrag-postgres psql -U legalrag -d legalrag < scripts/data_import/cleanup_old_data.sql
```

### Option 2: Dùng import tool (tự động cleanup trước khi import)

Script `import_data.py` sẽ tự động xóa dữ liệu cũ trước khi import.

## 📋 Mapping Collections

File `collections_mapping.json` chứa mapping giữa tên thư mục và collection trong database:

| Thư mục                  | Collection Name          | Display Name             |
| ------------------------ | ------------------------ | ------------------------ |
| QUY TRINH CONG CHUNG     | quy_trinh_cong_chung     | Quy trình công chứng     |
| QUY TRINH HỘ TỊCH CẤP XÃ | quy_trinh_ho_tich_cap_xa | Quy trình hộ tịch cấp Xã |
| ...                      | ...                      | ...                      |

## ⚠️ Lưu ý

1. **File format**: Script chuyển đổi `.doc` và `.docx` → `.pdf`
2. **Encoding**: Hỗ trợ tiếng Việt với font Noto
3. **Timeout**: Mỗi file có timeout 2 phút để convert
4. **Chunks**: Sau khi import, cần chạy embedding service để tạo chunks

## 🔄 Workflow đầy đủ

1. **Import documents** → Script này
2. **Generate chunks** → Cần tích hợp với embedding-service
3. **Create embeddings** → embedding-service xử lý

Hiện tại script chỉ thực hiện bước 1. Bước 2-3 cần được trigger riêng.
