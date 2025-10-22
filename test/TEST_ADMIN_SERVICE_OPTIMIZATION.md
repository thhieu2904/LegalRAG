# 🧪 Testing Admin Service Volume Configuration

## Kiểm Tra Sau Khi Sửa

### 1. Rebuild Docker Images

```bash
# Rebuild admin service image
docker-compose -f docker-compose.dev.yml build admin-service
```

### 2. Khởi Động Services

```bash
# Khởi động toàn bộ dev environment
docker-compose -f docker-compose.dev.yml up -d

# Hoặc nếu đã chạy, restart admin service
docker-compose -f docker-compose.dev.yml restart admin-service
```

### 3. Kiểm Tra Logs Admin Service

```bash
# Xem logs để verify path configuration
docker-compose -f docker-compose.dev.yml logs admin-service

# Kết quả mong đợi:
# AdminPathConfig initialized:
#   Environment: docker
#   Base data dir: /app/data/storage
#   Storage dir: /app/data/storage
#   Collections dir: /app/data/storage/collections
#   ✅ Admin service: Lightweight read-only mode (NO models, NO vectordb)
```

### 4. Verify Collections API

```bash
# Test API to list collections
curl http://localhost:8001/api/collections

# Kết quả mong đợi:
{
  "success": true,
  "data": [
    {
      "name": "collection_name",
      "display_name": "...",
      "document_count": X,
      ...
    }
  ],
  "source": "shared_storage"
}
```

### 5. Verify Health Check

```bash
curl http://localhost:8001/health

# Kết quả:
{
  "status": "healthy",
  "service": "admin",
  "environment": "docker",
  "collections_dir": "/app/data/storage/collections",
  "collections_exist": true
}
```

### 6. Check Docker Volume Mounts

```bash
# Xem volumes được mount
docker inspect legalrag-admin-service-dev | grep -A 20 "Mounts"

# Kết quả mong đợi:
# Mounts: [
#   {
#     "Type": "bind",
#     "Source": ".../rag_service/data/storage",
#     "Destination": "/app/data/storage",
#     "Mode": "ro",  # ← read-only
#     "RW": false
#   },
#   ...
# ]
```

## 7. Verify Lightweight Memory Usage

```bash
# Check memory usage
docker stats legalrag-admin-service-dev

# Kết quả mong đợi:
# MEM USAGE / LIMIT    MEM %
# ~100-150MiB / ...    ~2-3%  ← Rất nhẹ!
```

## 8. Verify Admin Cannot Access Models (Security Test)

```bash
# Exec vào container
docker-compose -f docker-compose.dev.yml exec admin-service bash

# Thử tìm models (không tìm thấy)
ls /app/data/models 2>&1
# kết quả: ls: cannot access '/app/data/models': No such file or directory

# Thử tìm vectordb (không tìm thấy)
ls /app/data/vectordb 2>&1
# kết quả: ls: cannot access '/app/data/vectordb': No such file or directory

# Nhưng collections có
ls /app/data/storage/collections
# kết quả: [collections list]

# Exit
exit
```

## 9. Integration Test

```bash
# Test full flow:
# 1. Admin service reads collections
# 2. Admin service reads documents
# 3. Admin service calls RAG service for questions

# From admin-service container
curl http://localhost:8000/health  # Access RAG service
# kết quả: should work (RAG service healthy)
```

## Troubleshooting

### Issue 1: Collections not found

```
ERROR: Collections directory not found: /app/data/storage/collections
```

**Fix:**

- Verify RAG service created collections in `rag_service/data/storage/collections`
- Or run RAG service first to populate collections

### Issue 2: Permission denied

```
PermissionError: [Errno 13] Permission denied: '/app/data/storage/...'
```

**Fix:**

- Should not happen with `:ro` (read-only)
- Verify docker-compose.dev.yml has `- ./rag_service/data/storage:/app/data/storage:ro`

### Issue 3: Mount not working in Windows

```
bind mount source does not exist: [path]
```

**Fix:**

- On Windows, use WSL2 backend
- Verify paths use forward slashes
- Or use Docker Desktop settings to share drive

### Issue 4: Admin service taking long to start

```
AdminPathConfig initialized...
[hangs or slow]
```

**Possible causes:**

- Volume mount from mounted network drive
- Check disk I/O: `docker stats`

**Solution:**

- Verify data structure is correct
- Use local volume if possible
- Check network drive performance

## Performance Comparison

### Before Optimization

```bash
docker-compose -f docker-compose.dev.yml up admin-service
# Time to start: ~5-10 seconds (mount all data)
# Volume size: ~6.5GB (mounted)
# Memory: ~150MiB
```

### After Optimization

```bash
docker-compose -f docker-compose.dev.yml up admin-service
# Time to start: ~1-2 seconds (mount only storage)
# Volume size: ~50-100MB (actual usage)
# Memory: ~100-120MiB (more efficient)
```

## 📋 Verification Checklist

- [ ] Admin service starts successfully
- [ ] Logs show correct paths (/app/data/storage)
- [ ] Collections API works
- [ ] Health check returns healthy
- [ ] Admin cannot access /app/data/models
- [ ] Admin cannot access /app/data/vectordb
- [ ] Memory usage is < 200MiB
- [ ] Admin can read documents
- [ ] Admin can read questions
- [ ] Admin can call RAG API

## 🎯 Expected Architecture After Fix

```
Admin Service
├─ Port 8001
├─ Memory: ~100-150MiB ✅
├─ Volume:
│  ├─ /app/data/storage (ro) ← ChỈ storage, không models
│  ├─ /app/app (rw)
│  └─ /app/main.py (rw)
├─ Dependencies:
│  ├─ FastAPI ✅
│  ├─ Pydantic ✅
│  ├─ httpx ✅
│  └─ NO ML libraries ✅
├─ Security:
│  ├─ Read-only storage ✅
│  ├─ No model access ✅
│  └─ No vectordb access ✅
└─ Performance:
   ├─ Fast startup ✅
   ├─ Minimal I/O ✅
   └─ Low resource usage ✅
```
