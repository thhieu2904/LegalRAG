# 🚀 LegalRAG v1.0.2 - Server Deployment Guide

## ✅ Tại Sao Build Nhanh?

### Docker Layer Caching Magic! 🎩

Khi bạn build lại RAG service (~3.5GB) chỉ mất **23 giây** vì:

```dockerfile
# Dockerfile có 11 layers (steps):
[1/11] FROM nvidia/cuda...          ✅ CACHED (không thay đổi)
[2/11] RUN apt-get install python   ✅ CACHED (không thay đổi)
[3/11] RUN ln -sf python3.11        ✅ CACHED (không thay đổi)
[4/11] WORKDIR /app                 ✅ CACHED (không thay đổi)
[5/11] COPY requirements.txt        ✅ CACHED (không thay đổi)
[6/11] RUN pip install torch        ✅ CACHED (~2GB, không cần tải lại!)
[7/11] RUN ldconfig cuda-stubs      ✅ CACHED (không thay đổi)
[8/11] RUN pip install llama-cpp    ✅ CACHED (không thay đổi)
[9/11] RUN pip install requirements ✅ CACHED (không thay đổi)
[10/11] COPY . .                    🔄 NEW (bạn xóa forms/, code thay đổi)
[11/11] RUN mkdir -p data           🔄 NEW (chạy lại vì step 10 mới)
```

**Kết quả**: Chỉ có 2 layers cuối phải chạy lại! (~1 giây)

### Nếu Bạn Thay Đổi Gì?

| Thay Đổi                               | Build Time | Lý Do                        |
| -------------------------------------- | ---------- | ---------------------------- |
| Xóa file `.py` trong `app/`            | ~5s        | Chỉ COPY lại code            |
| Thêm dependency vào `requirements.txt` | ~5-10 phút | Phải cài lại tất cả packages |
| Đổi base image (FROM ...)              | ~30 phút   | Phải build lại từ đầu        |
| Chỉnh code Python                      | ~5s        | Chỉ COPY lại                 |

**Tip**: Đặt những thứ ít thay đổi (requirements, system packages) lên trên Dockerfile!

## 📦 Files Đã Xóa

Bạn đã xóa folder `data/forms/` - **ĐÚNG RỒI**! ✅

Lý do:

- Forms không phải là static data
- Sẽ được generate bởi admin service khi cần
- Giảm kích thước Docker image
- Tránh conflict với production data

## 🚢 Deploy Lên Server Production

### Bước 1: Chuẩn Bị Files

Trên máy local, chỉ cần copy **2 files** sang server:

```bash
# Files cần thiết:
prod/
├── docker-compose.yml   ← Service configuration
└── .env                 ← (Optional) Custom environment variables
```

### Bước 2: Copy Sang Server

```bash
# Option 1: SCP
scp prod/docker-compose.yml user@server:/path/to/LegalRAG/
scp prod/.env user@server:/path/to/LegalRAG/  # nếu có

# Option 2: Git pull (khuyến nghị)
# Trên server:
cd /path/to/LegalRAG
git pull origin docker  # Pull latest code
cd prod
```

### Bước 3: Pull Images Từ DockerHub

```bash
# SSH vào server
ssh user@production-server

# Navigate to deployment directory
cd /path/to/LegalRAG/prod

# Pull tất cả images từ DockerHub
docker-compose pull

# Expected output:
# Pulling frontend          ... done
# Pulling rag-service       ... done  (3.5GB - hơi lâu)
# Pulling identifill-service ... done
# Pulling admin-service     ... done
```

**Lưu ý**: Pull lần đầu sẽ mất **10-15 phút** (download ~4.5GB total)

### Bước 4: Start Services

```bash
# Stop old version (if running)
docker-compose down

# Start v1.0.2
docker-compose up -d

# Check status
docker-compose ps
```

### Bước 5: Verify

```bash
# Health checks
curl http://localhost:8000/health  # RAG
curl http://localhost:8001/health  # Admin
curl http://localhost:8002/health  # Identifill

# Check logs
docker-compose logs -f rag-service
```

## 📋 Deployment Checklist

### Trên Server (Lần Đầu)

- [ ] **Install Docker & Docker Compose**

  ```bash
  # Ubuntu
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```

- [ ] **Install NVIDIA Container Toolkit**

  ```bash
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
  sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
  sudo systemctl restart docker
  ```

- [ ] **Verify GPU**
  ```bash
  nvidia-smi
  docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
  ```

### Mỗi Lần Deploy

- [ ] Copy `docker-compose.yml` sang server (hoặc git pull)
- [ ] Copy `.env` nếu có custom config
- [ ] Run `docker-compose pull`
- [ ] Run `docker-compose down` (stop old)
- [ ] Run `docker-compose up -d` (start new)
- [ ] Verify health checks
- [ ] Test frontend: http://server-ip:5173

## 🔄 Update Sau Này

Khi có version mới (v1.0.3, v1.0.4...):

```bash
# 1. Update docker-compose.yml (change image tags)
# 2. Pull new images
docker-compose pull

# 3. Restart services
docker-compose down && docker-compose up -d

# Data trong volumes sẽ được giữ nguyên! ✅
```

## 💾 Persistent Data

Các volumes sau sẽ tự động được tạo và **giữ nguyên** qua các lần restart:

```yaml
volumes:
  rag_data:# Chứa:
    # - AI models (embedding, LLM, reranker)
    # - Vector database (ChromaDB)
    # - Legal documents
    # - Upload cache
```

**Lưu ý**: Ngay cả khi bạn `docker-compose down`, data vẫn an toàn!

## 🎯 Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services (keep data)
docker-compose down

# View logs
docker-compose logs -f

# View logs của 1 service
docker-compose logs -f rag-service

# Restart 1 service
docker-compose restart rag-service

# Check resource usage
docker stats

# Remove EVERYTHING (including data) ⚠️
docker-compose down -v
```

## 🔍 Troubleshooting

### "Cannot connect to Docker daemon"

```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
# Logout and login again
```

### "Port already in use"

```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :5173

# Kill process or change port in docker-compose.yml
```

### "NVIDIA GPU not found"

```bash
# Check driver
nvidia-smi

# Restart docker
sudo systemctl restart docker

# Reinstall nvidia-container-toolkit
```

## ✅ Tóm Tắt

**Đúng rồi!** Deployment của bạn chỉ cần:

1. ✅ Copy `docker-compose.yml` + `.env` (hoặc git pull)
2. ✅ `docker-compose pull` (download images từ DockerHub)
3. ✅ `docker-compose up -d` (start services)

**Không cần**:

- ❌ Build lại trên server (images đã có sẵn trên DockerHub)
- ❌ Copy code (đã embedded trong images)
- ❌ Install Python/dependencies (đã có trong images)
- ❌ Copy models (sẽ tự download vào volume lần đầu chạy)

**Build nhanh** vì Docker cache layers thông minh! 🚀

---

**Next Deployment**: Chỉ cần `git pull && docker-compose pull && docker-compose up -d` thôi! 🎉
