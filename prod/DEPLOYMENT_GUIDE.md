# ============================================================================

# LegalRAG - Docker Hub Deployment Guide

# ============================================================================

# Polyrepo architecture with 9 microservices

# Complete guide: Build → Push → Deploy

# ============================================================================

## 📋 Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LegalRAG Microservices                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Frontend (3000)                                                           │
│      ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User-facing APIs                                                   │   │
│  │  ├── Admin Service (8001) - Document management                     │   │
│  │  └── Query Service (8002) - RAG Q&A                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Internal Services (801X)                                           │   │
│  │  ├── Storage Service (8010)  - MinIO wrapper                        │   │
│  │  ├── Embedding Service (8011) - Vietnamese Embedding [GPU]          │   │
│  │  ├── Vector Service (8012)   - pgvector operations                  │   │
│  │  ├── Rerank Service (8013)   - BGE Reranker [GPU]                   │   │
│  │  ├── LLM Service (8014)      - Vistral-7B [GPU]                     │   │
│  │  └── Form Service (8015)     - Form processing                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│      ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Infrastructure                                                     │   │
│  │  ├── PostgreSQL + pgvector (5432)                                   │   │
│  │  └── MinIO S3 (9000/9001)                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🐳 Danh sách 9 Services cần build

| #   | Service           | Dockerfile                     | Image Name           | GPU |
| --- | ----------------- | ------------------------------ | -------------------- | --- |
| 1   | admin-service     | `admin-service/Dockerfile`     | `legalrag-admin`     | ❌  |
| 2   | query-service     | `query-service/Dockerfile`     | `legalrag-query`     | ❌  |
| 3   | storage-service   | `storage-service/Dockerfile`   | `legalrag-storage`   | ❌  |
| 4   | vector-service    | `vector-service/Dockerfile`    | `legalrag-vector`    | ❌  |
| 5   | embedding-service | `embedding-service/Dockerfile` | `legalrag-embedding` | ✅  |
| 6   | rerank-service    | `rerank-service/Dockerfile`    | `legalrag-rerank`    | ✅  |
| 7   | llm-service       | `llm-service/Dockerfile`       | `legalrag-llm`       | ✅  |
| 8   | form-service      | `form-service/Dockerfile`      | `legalrag-form`      | ❌  |
| 9   | frontend          | `frontend/Dockerfile`          | `legalrag-frontend`  | ❌  |

---

## 🔧 BƯỚC 1: Chuẩn bị máy Dev

### 1.1 Đăng nhập Docker Hub

```powershell
# Đăng nhập Docker Hub (dùng token thay vì password nếu bật 2FA)
docker login

# Hoặc với token
docker login -u thhieu --password-stdin
# Paste token và Enter
```

### 1.2 Tạo repository trên Docker Hub

Truy cập https://hub.docker.com và tạo 9 repositories:

- `thhieu/legalrag-admin`
- `thhieu/legalrag-query`
- `thhieu/legalrag-storage`
- `thhieu/legalrag-vector`
- `thhieu/legalrag-embedding`
- `thhieu/legalrag-rerank`
- `thhieu/legalrag-llm`
- `thhieu/legalrag-form`
- `thhieu/legalrag-frontend`

---

## 🏗️ BƯỚC 2: Build & Push Images (Máy Dev)

### 2.1 Script Build & Push tất cả services

Chạy từ thư mục gốc `D:\Personal\LegalRAG`:

```powershell
# Biến cấu hình
$DOCKERHUB_USER = "thhieu"
$TAG = "latest"  # Hoặc dùng: "v1.0.0", "$(git rev-parse --short HEAD)"

# ============================================
# BUILD VÀ PUSH TẤT CẢ SERVICES
# ============================================

# 1. Admin Service
Write-Host "🔨 Building admin-service..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-admin:$TAG -f admin-service/Dockerfile ./admin-service
docker push ${DOCKERHUB_USER}/legalrag-admin:$TAG

# 2. Query Service
Write-Host "🔨 Building query-service..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-query:$TAG -f query-service/Dockerfile ./query-service
docker push ${DOCKERHUB_USER}/legalrag-query:$TAG

# 3. Storage Service
Write-Host "🔨 Building storage-service..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-storage:$TAG -f storage-service/Dockerfile ./storage-service
docker push ${DOCKERHUB_USER}/legalrag-storage:$TAG

# 4. Vector Service
Write-Host "🔨 Building vector-service..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-vector:$TAG -f vector-service/Dockerfile ./vector-service
docker push ${DOCKERHUB_USER}/legalrag-vector:$TAG

# 5. Embedding Service
Write-Host "🔨 Building embedding-service..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-embedding:$TAG -f embedding-service/Dockerfile ./embedding-service
docker push ${DOCKERHUB_USER}/legalrag-embedding:$TAG

# 6. Rerank Service (CPU runtime - GPU được cấu hình qua env)
Write-Host "🔨 Building rerank-service..." -ForegroundColor Cyan
docker build --target runtime -t ${DOCKERHUB_USER}/legalrag-rerank:$TAG -f rerank-service/Dockerfile ./rerank-service
docker push ${DOCKERHUB_USER}/legalrag-rerank:$TAG

# 7. LLM Service (GPU runtime)
Write-Host "🔨 Building llm-service (GPU)..." -ForegroundColor Cyan
docker build --target runtime-gpu -t ${DOCKERHUB_USER}/legalrag-llm:$TAG -f llm-service/Dockerfile ./llm-service
docker push ${DOCKERHUB_USER}/legalrag-llm:$TAG

# 8. Form Service
Write-Host "🔨 Building form-service..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-form:$TAG -f form-service/Dockerfile ./form-service
docker push ${DOCKERHUB_USER}/legalrag-form:$TAG

# 9. Frontend
Write-Host "🔨 Building frontend..." -ForegroundColor Cyan
docker build -t ${DOCKERHUB_USER}/legalrag-frontend:$TAG -f frontend/Dockerfile ./frontend
docker push ${DOCKERHUB_USER}/legalrag-frontend:$TAG

Write-Host "✅ All images pushed successfully!" -ForegroundColor Green
```

### 2.2 Build từng service riêng lẻ

```powershell
# Ví dụ: Chỉ build và push admin-service
$DOCKERHUB_USER = "thhieu"
$TAG = "latest"

docker build -t ${DOCKERHUB_USER}/legalrag-admin:$TAG -f admin-service/Dockerfile ./admin-service
docker push ${DOCKERHUB_USER}/legalrag-admin:$TAG
```

### 2.3 Xác nhận images đã push

```powershell
# Liệt kê images local
docker images | Select-String "legalrag"

# Kiểm tra trên Docker Hub
# Truy cập: https://hub.docker.com/u/thhieu
```

---

## 💾 BƯỚC 3: Export Database (Máy Dev)

### 3.1 Export toàn bộ database với pg_dump

```powershell
# Export database đầy đủ (schema + data + vectors)
docker exec legalrag-postgres pg_dump -U legalrag -d legalrag --no-owner --no-acl > backup_full.sql

# Kiểm tra file backup
Get-Item backup_full.sql | Select-Object Name, Length, LastWriteTime
```

### 3.2 Export database chia nhỏ (nếu file quá lớn)

```powershell
# Export schema only
docker exec legalrag-postgres pg_dump -U legalrag -d legalrag --schema-only --no-owner > backup_schema.sql

# Export data only (không có vectors - nhẹ hơn)
docker exec legalrag-postgres pg_dump -U legalrag -d legalrag --data-only --no-owner --exclude-table-data='chunks' > backup_data_no_vectors.sql

# Export chunks với vectors (có thể lớn)
docker exec legalrag-postgres pg_dump -U legalrag -d legalrag --data-only --no-owner --table='chunks' > backup_chunks.sql
```

### 3.3 Kiểm tra số lượng dữ liệu

```powershell
# Kiểm tra số collections, documents, chunks
docker exec legalrag-postgres psql -U legalrag -d legalrag -c "
SELECT
    (SELECT COUNT(*) FROM collections) as collections,
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM chunks) as chunks,
    (SELECT COUNT(*) FROM forms) as forms;
"
```

**Kỳ vọng:** 11 collections, ~150 documents, ~1000+ chunks

---

## 📦 BƯỚC 4: Export MinIO Data (Máy Dev)

### 4.1 Export toàn bộ bucket MinIO

```powershell
# Cài mc (MinIO Client) nếu chưa có
# Download từ: https://dl.min.io/client/mc/release/windows-amd64/mc.exe

# Cấu hình alias
mc alias set local http://localhost:9000 minioadmin minioadmin123

# Tạo backup bucket vào thư mục local
mc mirror local/legal-documents ./minio_backup/legal-documents

# Nén backup
Compress-Archive -Path ./minio_backup -DestinationPath minio_backup.zip
```

---

## 🖥️ BƯỚC 5: Deploy lên Server

### 5.1 Copy files lên server

```powershell
# Copy 4 files cần thiết lên server
scp prod/docker-compose.yml user@server:/home/user/legalrag/
scp prod/.env user@server:/home/user/legalrag/
scp backup_full.sql user@server:/home/user/legalrag/
scp minio_backup.zip user@server:/home/user/legalrag/
```

### 5.2 Trên Server: Pull và khởi chạy

```bash
cd /home/user/legalrag

# 1. Pull tất cả images
docker compose pull

# 2. Khởi động infrastructure trước (PostgreSQL, MinIO)
docker compose up -d postgres minio
sleep 30  # Chờ khởi động

# 3. Restore database
docker exec -i legalrag-postgres psql -U legalrag -d legalrag < backup_full.sql

# 4. Setup MinIO bucket
docker exec legalrag-minio mc alias set local http://localhost:9000 minioadmin minioadmin123
docker exec legalrag-minio mc mb local/legal-documents --ignore-existing

# 5. Restore MinIO data (nếu có)
unzip minio_backup.zip
docker cp minio_backup/legal-documents/. legalrag-minio:/data/legal-documents/

# 6. Khởi động tất cả services
docker compose up -d

# 7. Kiểm tra logs
docker compose logs -f
```

### 5.3 Kiểm tra health của services

```bash
# Kiểm tra tất cả containers
docker compose ps

# Kiểm tra health endpoints
curl http://localhost:8001/health  # Admin
curl http://localhost:8002/health  # Query
curl http://localhost:8010/health  # Storage
curl http://localhost:8011/health  # Embedding
curl http://localhost:8012/health  # Vector
curl http://localhost:8013/health  # Rerank
curl http://localhost:8014/health  # LLM
curl http://localhost:8015/health  # Form

# Frontend
curl http://localhost:3000/
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### Models không được đóng gói trong image

3 ML services (embedding, rerank, llm) sẽ **tự động tải models** khi khởi động lần đầu:

| Service           | Model                                       | Size   | Download Time |
| ----------------- | ------------------------------------------- | ------ | ------------- |
| embedding-service | `dangvantuan/vietnamese-document-embedding` | ~1.5GB | 5-10 min      |
| rerank-service    | `BAAI/bge-reranker-v2-m3`                   | ~2GB   | 5-10 min      |
| llm-service       | `ggml-vistral-7B-chat-q4_0.gguf`            | ~4GB   | 10-20 min     |

**Lần chạy đầu tiên sẽ mất 20-40 phút** để tải models. Các lần sau sẽ dùng cache.

### Kiểm tra GPU

```bash
# Kiểm tra NVIDIA driver
nvidia-smi

# Kiểm tra Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

### Yêu cầu VRAM

- **Minimum:** 12GB VRAM (tất cả 3 models trên GPU)
- **Recommended:** 16GB+ VRAM

---

## 🔄 CẬP NHẬT SERVICE

### Cập nhật một service

```bash
# Trên máy Dev: Build và push phiên bản mới
docker build -t thhieu/legalrag-admin:v1.0.1 -f admin-service/Dockerfile ./admin-service
docker push thhieu/legalrag-admin:v1.0.1

# Trên Server: Pull và restart
docker compose pull admin-service
docker compose up -d admin-service
```

### Cập nhật tất cả

```bash
docker compose pull
docker compose up -d
```

---

## 🛠️ TROUBLESHOOTING

### Service không khởi động

```bash
# Xem logs chi tiết
docker compose logs embedding-service

# Kiểm tra healthcheck
docker inspect legalrag-embedding | jq '.[0].State.Health'
```

### Models không tải được

```bash
# Kiểm tra network trong container
docker exec legalrag-embedding curl -I https://huggingface.co

# Kiểm tra cache directory
docker exec legalrag-embedding ls -la /app/models/
```

### Database connection failed

```bash
# Kiểm tra PostgreSQL
docker exec legalrag-postgres pg_isready -U legalrag

# Test connection từ service
docker exec legalrag-vector python -c "import psycopg2; psycopg2.connect('host=postgres user=legalrag password=legalrag123 dbname=legalrag')"
```

---

## 📊 PORT SUMMARY

| Port | Service       | Type     |
| ---- | ------------- | -------- |
| 3000 | Frontend      | User     |
| 8001 | Admin API     | User     |
| 8002 | Query API     | User     |
| 8010 | Storage       | Internal |
| 8011 | Embedding     | Internal |
| 8012 | Vector        | Internal |
| 8013 | Rerank        | Internal |
| 8014 | LLM           | Internal |
| 8015 | Form          | Internal |
| 5432 | PostgreSQL    | Infra    |
| 9000 | MinIO API     | Infra    |
| 9001 | MinIO Console | Infra    |
