# 🚀 LegalRAG - Hệ Thống Hỏi Đáp Pháp Luật Việt Nam

## 📋 Yêu Cầu Hệ Thống

### Hardware

- **GPU**: NVIDIA RTX 3060 6GB (hoặc tương đương)
- **RAM**: Tối thiểu 8GB, khuyến nghị 16GB+
- **Disk**: 20GB dung lượng trống (cho models và data)

### Software

- **Docker** và **Docker Compose** đã cài đặt
- **NVIDIA Container Toolkit** cho GPU support
- **Windows 10/11**, **Ubuntu 20.04+**, hoặc **CentOS 7+**

## 🔧 Cài Đặt

### Bước 1: Chuẩn bị

```bash
# Clone hoặc copy toàn bộ folder LegalRAG về máy
# Đảm bảo có đầy đủ các folders: frontend/, rag_service/, identifill_service/

# Kiểm tra Docker và GPU
docker --version
docker-compose --version
nvidia-smi
```

### Bước 2: Cấu hình

```bash
# 1. Copy template config
cp customer-deployment/config/rag-service.env.template rag_service/.env

# 2. Chỉnh sửa rag_service/.env nếu cần:
#    - ENABLE_VRAM_SWAPPING=true (cho GPU 6GB)
#    - ENABLE_VRAM_SWAPPING=false (cho GPU 12GB+)
```

### Bước 3: Khởi chạy

```bash
# Build và chạy tất cả services
docker-compose up -d

# Xem logs để theo dõi quá trình khởi động
docker-compose logs -f rag-service

# Chờ thông báo: "🎉 LegalRAG API started successfully!"
```

### Bước 4: Kiểm tra

```bash
# Test RAG Service
curl http://localhost:8000/health

# Test Frontend
# Mở browser: http://localhost:5173
```

## 📱 Sử Dụng

### Web Interface

- **Frontend**: http://localhost:5173
- **RAG API**: http://localhost:8000
- **CCCD Scanner**: http://localhost:8002

### Tính năng chính

- ✅ Hỏi đáp pháp luật Việt Nam
- ✅ Quét CCCD QR code
- ✅ Download biểu mẫu pháp lý
- ✅ Hỗ trợ giọng nói (Speech-to-Text)

## 🛠️ Bảo trì

### Dừng hệ thống

```bash
docker-compose down
```

### Xem logs

```bash
# Xem logs tất cả services
docker-compose logs

# Xem logs riêng RAG service
docker-compose logs -f rag-service
```

### Update hệ thống

```bash
# Pull code mới
git pull

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup dữ liệu

```bash
# Backup models và vectordb
cp -r rag_service/data ./backup-$(date +%Y%m%d)
```

## ❗ Troubleshooting

### GPU không được nhận diện

```bash
# Kiểm tra NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Cài đặt NVIDIA Container Toolkit (Ubuntu)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update
sudo apt-get install nvidia-container-runtime
sudo systemctl restart docker
```

### Service không khởi động

```bash
# Xem logs chi tiết
docker-compose logs rag-service

# Kiểm tra cấu hình
cat rag_service/.env

# Restart service
docker-compose restart rag-service
```

### Hết VRAM

```bash
# Chuyển sang VRAM swapping mode
# Sửa rag_service/.env:
ENABLE_VRAM_SWAPPING=true

# Restart
docker-compose restart rag-service
```

## 📞 Hỗ trợ

- **GitHub Issues**: [LegalRAG Issues](https://github.com/thhieu2904/LegalRAG)
- **Email**: support@legalrag.com

---

_© 2025 LegalRAG Team. Vietnamese Legal Document Q&A System._
