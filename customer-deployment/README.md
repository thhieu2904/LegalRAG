# 🚀 LegalRAG - Hệ Thống Hỏi Đáp Pháp Luật

## � Yêu Cầu Hệ Thống

- **Docker** và **Docker Compose** đã cài đặt
- **NVIDIA Container Toolkit** (cho GPU support)
- **GPU**: NVIDIA RTX 3060 6GB hoặc tương đương
- **RAM**: 8GB+, **Disk**: 25GB trống

## 🚀 Hướng Dẫn Chi Tiết

### Bước 1: Tạo thư mục làm việc

```bash
# Tạo thư mục mới (Windows)
mkdir LegalRAG
cd LegalRAG

# Hoặc (Linux/Mac)
mkdir LegalRAG && cd LegalRAG
```

### Bước 2: Tạo file docker-compose.yml

**Tạo file mới tên `docker-compose.yml` với nội dung:**

```yaml
name: legalrag
services:
  # Frontend Service - Production
  frontend:
    container_name: legalrag-frontend
    image: thhieu/legalrag-frontend:latest
    ports:
      - "5173:5173"
    depends_on:
      - rag-service
      - identifill-service
    networks:
      - legalrag-network

  # RAG Service with GPU Support - Production
  rag-service:
    container_name: legalrag-rag-service
    image: thhieu/legalrag-rag-service:latest
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - HF_CACHE_DIR=/app/data/models/hf_cache
      - CUDA_VISIBLE_DEVICES=0
      - ENVIRONMENT=docker
      - LEGALRAG_BASE_PATH=/app
      - LEGALRAG_DATA_PATH=/app/data
    volumes:
      - rag_data:/app/data
      - ./.env:/app/.env
    networks:
      - legalrag-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Identifill Service (CCCD Scanner) - Production
  identifill-service:
    container_name: legalrag-identifill-service
    image: thhieu/legalrag-identifill-service:latest
    ports:
      - "8002:8002"
    environment:
      - PYTHONPATH=/app
      - ENVIRONMENT=docker
      - RAG_SERVICE_URL=http://rag-service:8000
    volumes:
      - identifill_models:/app/models
    networks:
      - legalrag-network

volumes:
  rag_data:
  identifill_models:

networks:
  legalrag-network:
```

### Bước 3: Tạo file cấu hình .env

**Tạo file mới tên `.env` với nội dung:**

```bash
# VRAM Management - Chọn theo GPU của bạn
ENABLE_VRAM_SWAPPING=false   # false = GPU 12GB+, true = GPU 6GB

# Các cài đặt khác (không cần thay đổi)
DEBUG=false
HOST=0.0.0.0
PORT=8000
MAX_TOKENS=1200
TEMPERATURE=0.1
CONTEXT_LENGTH=5888
N_CTX=5888
N_GPU_LAYERS=-1
```

### Bước 4: Chạy hệ thống

```bash
# Pull images từ Docker Hub và chạy
docker-compose up -d

# Xem logs để theo dõi quá trình khởi động (QUAN TRỌNG)
docker-compose logs -f rag-service
```

**⏳ Chờ đợi:** Lần đầu sẽ mất **10-15 phút** để download models (22GB)

**✅ Thành công khi thấy:** `🎉 LegalRAG API started successfully!`

### Bước 5: Kiểm tra và sử dụng

```bash
# Kiểm tra tất cả services đã chạy
docker-compose ps

# Test API
curl http://localhost:8000/health
```

**🎯 Truy cập hệ thống:**

- **Web Interface**: http://localhost:5173
- **RAG API**: http://localhost:8000
- **CCCD Scanner**: http://localhost:8002

## 🛠️ Quản Lý Hệ Thống

### Dừng hệ thống

```bash
docker-compose down
```

### Khởi động lại

```bash
docker-compose up -d
```

### Xem logs lỗi

```bash
# Xem logs tất cả services
docker-compose logs

# Xem logs riêng RAG service
docker-compose logs -f rag-service
```

### Update hệ thống

```bash
# Pull phiên bản mới
docker-compose pull

# Restart với images mới
docker-compose up -d
```

## 🔧 Troubleshooting

### GPU không được nhận diện

```bash
# Kiểm tra GPU
nvidia-smi

# Kiểm tra Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

### Hết VRAM

```bash
# Sửa file .env:
ENABLE_VRAM_SWAPPING=true

# Restart
docker-compose restart rag-service
```

### Port bị chiếm

```bash
# Thay đổi port trong docker-compose.yml:
ports:
  - "3000:5173"  # Frontend
  - "8001:8000"  # RAG API
  - "8003:8002"  # CCCD Scanner
```

### Xem logs

```bash
docker-compose logs -f
```

### Update hệ thống

```bash
docker-compose pull
docker-compose up -d
```

---

_Powered by Docker Images: thhieu/legalrag-frontend, thhieu/legalrag-rag-service, thhieu/legalrag-identifill-service_
