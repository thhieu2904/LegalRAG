# Hướng Dẫn Triển Khai LegalRAG v1.0.2

## 📋 Thông Tin Phiên Bản

- **Phiên bản**: v1.0.2
- **Ngày phát hành**: 12/10/2025
- **Thay đổi chính**: Loại bỏ TTS Service, sử dụng Web Speech API của trình duyệt

## 🎯 Tính Năng

### Hệ Thống Hiện Tại

1. **Frontend** - Giao diện người dùng

   - Hệ thống chat tư vấn pháp luật
   - Quản lý tài liệu
   - Scan CCCD tự động
   - **Giọng đọc**: Microsoft An (Vietnamese) - Web Speech API

2. **RAG Service** - Trả lời câu hỏi pháp luật

   - Tìm kiếm ngữ nghĩa trong tài liệu
   - Tạo câu trả lời với LLM
   - Hỗ trợ GPU NVIDIA

3. **Admin Service** - Quản lý dữ liệu

   - Upload tài liệu
   - Quản lý câu hỏi mẫu
   - Xem preview tài liệu

4. **Identifill Service** - Xử lý CCCD
   - Quét QR code CCCD
   - Tự động điền form

## 🖥️ Yêu Cầu Hệ Thống

### Phần Cứng

- **CPU**: 4 cores trở lên
- **RAM**: 16GB tối thiểu (khuyến nghị 32GB)
- **GPU**: NVIDIA RTX 3060 (12GB VRAM) hoặc tốt hơn
- **Ổ cứng**: 50GB trống

### Phần Mềm

- **OS**: Ubuntu 22.04 LTS hoặc Windows 11
- **Docker**: 24.0+ với NVIDIA Container Toolkit
- **NVIDIA Driver**: 535+ hỗ trợ CUDA 12.1

## 🚀 Triển Khai Nhanh

### Bước 1: Chuẩn Bị

```bash
# Clone repository
git clone https://github.com/thhieu2904/LegalRAG.git
cd LegalRAG/prod

# Kiểm tra GPU
nvidia-smi
```

### Bước 2: Khởi Động

```bash
# Chạy tất cả services
docker-compose up -d

# Kiểm tra trạng thái
docker-compose ps

# Xem logs
docker-compose logs -f
```

### Bước 3: Truy Cập

- **Frontend**: http://localhost:5173
- **RAG API**: http://localhost:8000/docs
- **Admin API**: http://localhost:8001/docs
- **Identifill API**: http://localhost:8002/docs

## 📊 Kiểm Tra Health Check

```bash
# RAG Service
curl http://localhost:8000/health

# Admin Service
curl http://localhost:8001/health

# Identifill Service
curl http://localhost:8002/health
```

Kết quả mong đợi:

```json
{
  "status": "healthy",
  "service": "LegalRAG Service",
  "version": "1.0.2"
}
```

## 🔧 Cấu Hình

### Tùy Chỉnh docker-compose.yml

```yaml
# Thay đổi port Frontend
frontend:
  ports:
    - "3000:5173" # Thay vì 5173:5173

# Tăng memory cho RAG Service
rag-service:
  deploy:
    resources:
      limits:
        memory: 16G # Thay vì 10G
```

### Biến Môi Trường

Tạo file `.env` trong thư mục `prod/`:

```env
# GPU Configuration
CUDA_VISIBLE_DEVICES=0

# RAG Service
HF_CACHE_DIR=/app/data/models/hf_cache
LEGALRAG_DATA_PATH=/app/data

# Admin Service
RAG_SERVICE_URL=http://rag-service:8000
```

## 🗂️ Quản Lý Dữ Liệu

### Backup Volume

```bash
# Backup dữ liệu RAG
docker run --rm -v legalrag_rag_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/rag_data_backup.tar.gz /data

# Restore
docker run --rm -v legalrag_rag_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/rag_data_backup.tar.gz -C /
```

### Xóa Dữ Liệu

```bash
# Dừng services
docker-compose down

# Xóa volumes (CẢNH BÁO: Mất toàn bộ dữ liệu!)
docker volume rm legalrag_rag_data

# Khởi động lại
docker-compose up -d
```

## 🔄 Nâng Cấp

### Từ v0.1.1 lên v1.0.2

```bash
# Dừng version cũ
docker-compose down

# Pull images mới
docker-compose pull

# Khởi động version mới
docker-compose up -d

# Dữ liệu được giữ nguyên trong volume
```

## 🐛 Xử Lý Sự Cố

### RAG Service không khởi động

```bash
# Kiểm tra GPU
nvidia-smi

# Kiểm tra logs
docker logs legalrag-rag-service

# Khởi động lại
docker-compose restart rag-service
```

### Lỗi "Out of Memory"

```bash
# Giảm batch size trong code hoặc
# Tăng memory limit trong docker-compose.yml

rag-service:
  deploy:
    resources:
      limits:
        memory: 16G  # Tăng từ 10G
```

### Frontend không kết nối được API

```bash
# Kiểm tra network
docker network inspect legalrag_legalrag-network

# Kiểm tra services có chạy không
docker-compose ps

# Restart tất cả
docker-compose restart
```

## 📱 Sử Dụng

### 1. Tư Vấn Pháp Luật

1. Truy cập http://localhost:5173
2. Đăng nhập (nếu cần)
3. Nhập câu hỏi vào chat box
4. Nhấn Enter hoặc nút Gửi
5. Bật icon 🔊 để nghe câu trả lời (giọng An)

### 2. Quét CCCD

1. Click vào tab "Identifill"
2. Upload ảnh CCCD (mặt sau)
3. Hệ thống tự động đọc QR code
4. Thông tin tự động điền vào form

### 3. Quản Lý Tài Liệu (Admin)

1. Đăng nhập với tài khoản admin
2. Tab "Documents" → Upload file PDF
3. Hệ thống tự động xử lý và index
4. Tài liệu có thể tìm kiếm qua chat

## 🎤 Giọng Đọc (TTS)

### Web Speech API (Hiện Tại)

- **Giọng**: Microsoft An - Vietnamese (Vietnam)
- **Hoạt động**: Offline trong trình duyệt
- **Chất lượng**: Cao, phát âm chuẩn
- **Tốc độ**: Tức thì, không cần tải model

### Cách Bật/Tắt

1. Click icon 🔊 ở góc phải màn hình
2. Toggle ON/OFF
3. Khi bật, mỗi câu trả lời sẽ tự động đọc

## 📈 Giám Sát

### Xem Logs Realtime

```bash
# Tất cả services
docker-compose logs -f

# Chỉ RAG service
docker-compose logs -f rag-service

# Tail 100 dòng cuối
docker-compose logs --tail=100 rag-service
```

### Theo Dõi Resource

```bash
# CPU, Memory, GPU
docker stats

# Chỉ RAG service
docker stats legalrag-rag-service
```

## 🔐 Bảo Mật

### Production Checklist

- [ ] Thay đổi default passwords
- [ ] Bật HTTPS với SSL/TLS
- [ ] Cấu hình firewall
- [ ] Giới hạn CORS origins
- [ ] Enable authentication
- [ ] Regular backup dữ liệu

## 📞 Hỗ Trợ

- **GitHub Issues**: https://github.com/thhieu2904/LegalRAG/issues
- **Docker Hub**: https://hub.docker.com/u/thhieu
- **Email**: thhieu2904@gmail.com

## 📝 Changelog

### v1.0.2 (12/10/2025)

- ❌ Removed experimental F5-TTS service
- ✅ Simplified architecture (4 services)
- ✅ Reduced memory requirements
- ✅ Faster startup time
- ✅ Stable Web Speech API for Vietnamese TTS

### v0.1.1 (Previous)

- Initial production release
- 5 services including experimental TTS
- GPU sharing between RAG and TTS

---

**LegalRAG v1.0.2** - Hệ thống tư vấn pháp luật thông minh với AI
