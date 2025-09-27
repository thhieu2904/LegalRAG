# 📋 HƯỚNG DẪN CHI TIẾT CHO ANH EM

## 🎯 TÓM TẮT: Chỉ cần 2 file + 1 lệnh!

1. **Tạo thư mục** → **Copy 2 files** → **Chạy docker-compose up -d**
2. **Chờ 10-15 phút** download models
3. **Vào http://localhost:5173** sử dụng!

---

## 📝 TỪNG BƯỚC CHI TIẾT

### Bước 1: Chuẩn bị thư mục

```bash
# Windows (Command Prompt hoặc PowerShell)
mkdir LegalRAG
cd LegalRAG

# Hoặc tạo bằng File Explorer, sau đó mở Terminal tại thư mục đó
```

### Bước 2: Tạo file docker-compose.yml

**Cách 1: Copy paste**

- Tạo file mới tên `docker-compose.yml`
- Copy nội dung từ file `customer-deployment/docker-compose.yml`
- Paste vào và Save

**Cách 2: Download trực tiếp**

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/thhieu2904/LegalRAG/docker/customer-deployment/docker-compose.yml
```

### Bước 3: Tạo file .env

**Tạo file mới tên `.env` với nội dung:**

```bash
ENABLE_VRAM_SWAPPING=false
DEBUG=false
HOST=0.0.0.0
PORT=8000
MAX_TOKENS=1200
TEMPERATURE=0.1
CONTEXT_LENGTH=5888
N_CTX=5888
N_GPU_LAYERS=-1
```

**⚠️ LUU Ý QUAN TRỌNG:**

- `ENABLE_VRAM_SWAPPING=false` → Dành cho GPU 12GB+
- `ENABLE_VRAM_SWAPPING=true` → Dành cho GPU 6GB

### Bước 4: Chạy hệ thống

```bash
# Chạy lệnh này trong thư mục chứa docker-compose.yml
docker-compose up -d
```

**QUAN TRỌNG - Theo dõi quá trình:**

```bash
# Xem logs để biết khi nào xong
docker-compose logs -f rag-service
```

**Dấu hiệu THÀNH CÔNG:**

- Thấy dòng: `🎉 LegalRAG API started successfully!`
- CPU usage giảm xuống
- Không còn downloading models

### Bước 5: Kiểm tra

```bash
# Kiểm tra containers đang chạy
docker-compose ps

# Test API
curl http://localhost:8000/health
```

### Bước 6: Sử dụng

- Mở browser: **http://localhost:5173**
- Hỏi đáp pháp luật: **"Làm CCCD cần giấy tờ gì?"**
- Test CCCD scanner: Upload ảnh CCCD

---

## ⏱️ TIMELINE DỰ KIẾN

- **Phút 0-2**: Pull images từ Docker Hub
- **Phút 2-12**: Download AI models (PhoGPT 2.5GB, Vietnamese models)
- **Phút 12-15**: Khởi động và load models lên GPU
- **Phút 15+**: ✅ Sẵn sàng sử dụng!

---

## 🆘 KHI GẶP LỖI

### Lỗi GPU

```bash
# Cài NVIDIA Container Toolkit
# Windows: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
# Ubuntu: sudo apt install nvidia-container-toolkit
```

### Lỗi VRAM

```bash
# Sửa .env thành:
ENABLE_VRAM_SWAPPING=true

# Restart:
docker-compose restart rag-service
```

### Lỗi Port

```bash
# Thay port khác trong docker-compose.yml nếu bị conflict
```

---

## 🎊 KẾT QUẢ CUỐI

Anh em sẽ có **hệ thống y hệt máy dev**, bao gồm:

- ✅ Frontend React đầy đủ tính năng
- ✅ RAG API với PhoGPT-4B
- ✅ CCCD Scanner với AI
- ✅ Tất cả models và data tự động setup

**🔥 EXACTLY như máy của mình!**
