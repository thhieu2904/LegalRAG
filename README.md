# 🐳 LegalRAG Docker Setup

## 📋 Simple Docker Setup

Dự án có 3 services: Frontend (React), RAG Service (Python + GPU), Identifill Service (Python).

## 🚀 Quick Start

### 1. Prerequisites

- Docker Desktop with NVIDIA Container Toolkit
- NVIDIA GPU với drivers

### 2. Check GPU Support

```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

### 3. Build và Run

```bash
# Build tất cả services
docker-compose build

# Chạy tất cả services
docker-compose up

# Hoặc build + run cùng lúc
docker-compose up --build
```

## 🔍 Services

- **Frontend**: http://localhost:5173
- **RAG Service**: http://localhost:8000 (GPU-accelerated)
- **Identifill Service**: http://localhost:8002

## 🛠️ Docker Commands để học

### Build từng service riêng

```bash
# Frontend
docker-compose build frontend

# RAG Service
docker-compose build rag-service

# Identifill Service
docker-compose build identifill-service
```

### Xem logs

```bash
# Tất cả services
docker-compose logs -f

# Service cụ thể
docker-compose logs -f rag-service
```

### Stop/Start

```bash
# Stop tất cả
docker-compose down

# Start lại
docker-compose up

# Restart service cụ thể
docker-compose restart rag-service
```

### Debug container

```bash
# Vào shell của container
docker-compose exec rag-service bash
docker-compose exec frontend sh

# Check resource usage
docker stats
```

## 📁 Structure

```
├── docker-compose.yml        # Main orchestration
├── frontend/
│   └── Dockerfile           # Node.js build
├── rag_service/
│   ├── Dockerfile           # GPU Python build
│   └── requirements.txt     # Dependencies
└── identifill_service/
    ├── Dockerfile           # Python build
    └── requirements.txt     # Dependencies
```

## 🐛 Troubleshooting

### GPU không hoạt động

```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi
```

### Build failed

```bash
# Clean build
docker-compose down
docker system prune -f
docker-compose build --no-cache
```

### Port conflicts

```bash
# Check ports
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```
