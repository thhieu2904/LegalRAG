# 🧪 JSON CRUD Testing Guide - LOCAL DEV (6GB VRAM)

> **Environment**: Local Development với Conda (KHÔNG dùng Docker)
> **VRAM**: 6GB (dev machine)
> **Setup**: Chạy services riêng lẻ với conda environments

---

## 📋 Prerequisites Check

### 1. Conda Environments

```powershell
# Check available environments
conda info --envs

# Should see:
# LegalRAG               D:\env\conda\LegalRAG
# identifill_env         D:\env\conda\identifill_env
```

### 2. GPU Check

```powershell
# Check NVIDIA GPU
nvidia-smi

# Should show ~6GB VRAM available
```

---

## 🚀 Step-by-Step Testing

### Step 1: Start RAG Service (Terminal 1)

```powershell
# Activate conda environment
conda activate LegalRAG

# Navigate to rag_service
cd D:\Personal\LegalRAG_OCR\rag_service

# Start service
python main.py

# Expected output:
# 🚀 Starting LegalRAG API...
# ✅ Internal JSON Documents API endpoints enabled
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Wait for**: "Application startup complete" message

### Step 2: Start Admin Service (Terminal 2 - NEW)

```powershell
# Activate conda environment (có thể dùng LegalRAG hoặc tạo mới)
conda activate LegalRAG

# Navigate to admin_service
cd D:\Personal\LegalRAG_OCR\admin_service

# Start service
python main.py

# Expected output:
# 🚀 Starting LegalRAG Admin Service...
# INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Port Note**: Admin service chạy port **8001** (khác RAG service port 8000)

---

## 🧪 API Testing with PowerShell

### Test 1: Health Check

```powershell
# RAG Service health
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json

# Admin Service health
Invoke-RestMethod -Uri "http://localhost:8001/health" | ConvertTo-Json
```

### Test 2: Get JSON Document (RAG Internal API)

```powershell
# Test RAG Internal API directly
$headers = @{
    "X-Internal-API-Key" = "dev-internal-key"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/internal/json/collections/Bo_thu_tuc/documents/DOC_001" -Headers $headers | ConvertTo-Json -Depth 10
```

### Test 3: Get JSON via Admin API

```powershell
# Test Admin API (this calls RAG Internal API)
Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents/DOC_001/json" | ConvertTo-Json -Depth 10
```

### Test 4: Update JSON Document

```powershell
# Prepare JSON data
$jsonData = @{
    data = @{
        id = "DOC_001"
        title = "Test Updated Title"
        sections = @(
            @{
                section_id = "SEC_001"
                title = "Section 1"
                content = "Updated content"
            }
        )
        metadata = @{
            updated_by = "test"
            updated_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        }
    }
    trigger_rebuild = $false  # Set to $true to trigger cache rebuild
} | ConvertTo-Json -Depth 10

# Send PUT request
Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents/DOC_001/json" `
    -Method PUT `
    -ContentType "application/json" `
    -Body $jsonData | ConvertTo-Json
```

### Test 5: List Backups

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents/DOC_001/json/backups" | ConvertTo-Json -Depth 10
```

### Test 6: Restore from Backup

```powershell
# First, get backup filename from Test 5
$restoreData = @{
    backup_filename = "DOC_001.json.backup.20251012_143022"  # Replace with actual filename
    trigger_rebuild = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents/DOC_001/json/restore" `
    -Method POST `
    -ContentType "application/json" `
    -Body $restoreData | ConvertTo-Json
```

### Test 7: Trigger Rebuild Manually

```powershell
$rebuildData = @{
    scope = "document"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents/DOC_001/json/rebuild" `
    -Method POST `
    -ContentType "application/json" `
    -Body $rebuildData | ConvertTo-Json
```

### Test 8: Check Rebuild Status

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents/DOC_001/json/rebuild/status" | ConvertTo-Json
```

---

## 🐛 Troubleshooting

### Issue 1: RAG Service won't start

```powershell
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <process_id> /F
```

### Issue 2: Admin Service won't start

```powershell
# Check if port 8001 is already in use
netstat -ano | findstr :8001

# Kill process if needed
taskkill /PID <process_id> /F
```

### Issue 3: Internal API Key Error (403)

Check `rag_service/app/core/config.py`:

```python
internal_api_key: str = "dev-internal-key"  # Should match header
```

### Issue 4: Collection/Document Not Found (404)

```powershell
# Check available collections
Invoke-RestMethod -Uri "http://localhost:8001/api/collections" | ConvertTo-Json

# Check documents in collection
Invoke-RestMethod -Uri "http://localhost:8001/api/collections/Bo_thu_tuc/documents" | ConvertTo-Json
```

### Issue 5: VRAM Out of Memory

```powershell
# Check GPU usage
nvidia-smi

# If VRAM is full, restart RAG Service
# Services are designed for 6GB VRAM with CPU embedding
```

---

## 📊 Expected Results

### ✅ Successful GET Response

```json
{
  "success": true,
  "data": {
    "id": "DOC_001",
    "title": "Document Title",
    "sections": [...]
  },
  "collection": "Bo_thu_tuc",
  "doc_id": "DOC_001"
}
```

### ✅ Successful UPDATE Response

```json
{
  "success": true,
  "message": "JSON document updated for DOC_001",
  "backup_created": true,
  "backup_path": "data/storage/collections/Bo_thu_tuc/documents/DOC_001/DOC_001.json.backup.20251012_143022",
  "rebuild_triggered": false
}
```

### ✅ Successful BACKUP LIST Response

```json
{
  "success": true,
  "data": [
    {
      "filename": "DOC_001.json.backup.20251012_143022",
      "timestamp": "20251012_143022",
      "size": 15234,
      "created_at": "2025-10-12T14:30:22"
    }
  ],
  "total": 1
}
```

---

## 🔍 Verification Steps

### 1. Check Backup Created

```powershell
# Navigate to document directory
cd D:\Personal\LegalRAG_OCR\rag_service\data\storage\collections\Bo_thu_tuc\documents\DOC_001

# List backup files
Get-ChildItem -Filter "*.backup.*"
```

### 2. Check Rebuild Status File

```powershell
# Navigate to cache directory
cd D:\Personal\LegalRAG_OCR\rag_service\data\cache

# Check rebuild status
Get-Content rebuild_status.json | ConvertFrom-Json | ConvertTo-Json
```

### 3. Verify JSON Content Changed

```powershell
# Read current JSON
Get-Content D:\Personal\LegalRAG_OCR\rag_service\data\storage\collections\Bo_thu_tuc\documents\DOC_001\DOC_001.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 📝 Testing Checklist

- [ ] ✅ RAG Service started successfully (port 8000)
- [ ] ✅ Admin Service started successfully (port 8001)
- [ ] ✅ Health checks pass for both services
- [ ] ✅ GET JSON document works (Admin API)
- [ ] ✅ GET JSON document works (RAG Internal API)
- [ ] ✅ UPDATE JSON creates backup
- [ ] ✅ UPDATE JSON modifies file correctly
- [ ] ✅ LIST backups shows created backups
- [ ] ✅ RESTORE from backup works
- [ ] ✅ REBUILD trigger works (optional - may take time)
- [ ] ✅ REBUILD status tracking works

---

## 🎯 Performance Notes (6GB VRAM)

- **Embedding Model**: Runs on CPU (saves VRAM)
- **LLM Model**: Runs on GPU
- **Reranker**: Runs on GPU
- **Expected VRAM Usage**: ~4-5GB
- **Rebuild Time**:
  - Single document: 1-2 seconds
  - Collection: 10-30 seconds
  - All collections: 1-5 minutes

---

## 🚀 Next Steps After Testing

1. ✅ Verify all endpoints work correctly
2. ✅ Test error scenarios (invalid data, missing files)
3. ✅ Test rebuild functionality
4. 🔄 Develop Frontend UI (Monaco Editor integration)
5. 📚 Update API documentation

---

**Testing Date**: 2025-10-12  
**Environment**: Local Dev with Conda (6GB VRAM)  
**Services**: RAG (port 8000) + Admin (port 8001)
