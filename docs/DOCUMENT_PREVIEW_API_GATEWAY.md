# 🌐 Document Preview - API Gateway Architecture

**Status**: ✅ **PRODUCTION READY**  
**Date**: October 11, 2025  
**Pattern**: API Gateway (Best Practice)

---

## 📊 Architecture Overview

### **Before (Direct File Access)** ❌

```
┌─────────────────┐
│ Admin Service   │
│  (Port 8001)    │
│                 │
│  ┌───────────┐  │    Volume Mount
│  │ PathConfig│──┼────────────────────┐
│  └───────────┘  │                    │
└─────────────────┘                    ▼
                                ┌──────────────┐
                                │ /app/data    │
                                │ (Shared Vol) │
                                └──────────────┘
                                       ▲
┌─────────────────┐                    │
│ RAG Service     │    Volume Mount    │
│  (Port 8000)    │────────────────────┘
└─────────────────┘
```

**Problems:**

- ❌ Tight coupling via shared volume
- ❌ Duplicate path resolution logic
- ❌ No centralized access control
- ❌ Difficult to scale independently

---

### **After (API Gateway)** ✅

```
┌─────────────────┐
│ Admin Service   │
│  (Port 8001)    │
│                 │
│  ┌───────────┐  │    HTTP Request (Internal API)
│  │RAGClient  │──┼────────────────────────────┐
│  │           │  │  X-Internal-API-Key: ***   │
│  └───────────┘  │                            ▼
└─────────────────┘                ┌──────────────────────┐
                                   │  RAG Service         │
                                   │   (Port 8000)        │
                                   │                      │
                                   │  ┌────────────────┐  │
                                   │  │ Internal Docs  │  │
                                   │  │ API            │  │
                                   │  └────────────────┘  │
                                   │         │            │
                                   └─────────┼────────────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │ /app/data    │
                                      │ (RAG Only)   │
                                      └──────────────┘
```

**Benefits:**

- ✅ Loose coupling via HTTP API
- ✅ Single source of truth (RAG Service)
- ✅ Centralized security & validation
- ✅ Independent scaling & deployment
- ✅ Better error handling & retry logic

---

## 🔧 Implementation Details

### **1. RAG Service - Internal Documents API**

**File**: `rag_service/app/api/internal_documents.py`

```python
@router.get("/collections/{collection}/documents/{doc_id}/content")
async def get_document_content(
    collection: str,
    doc_id: str,
    type: str = Query(..., regex="^(docx|json)$"),
    _: None = Header(None, alias="X-Internal-API-Key")
):
    """
    Serve document content for Admin Service
    - DOCX → HTML (using mammoth)
    - JSON → Structured data
    """
```

**Security**:

- API key validation: `X-Internal-API-Key: dev-internal-key`
- Only accessible from Admin Service

**Endpoints**:

- `GET /api/internal/documents/collections/{collection}/documents/{doc_id}/content?type=docx`
- `GET /api/internal/documents/collections/{collection}/documents/{doc_id}/content?type=json`

---

### **2. Admin Service - RAG Client**

**File**: `admin_service/app/services/rag_client.py`

```python
class RAGServiceClient:
    async def get_document_content(
        self,
        collection: str,
        doc_id: str,
        doc_type: str
    ) -> Dict[str, Any]:
        """
        Get document content from RAG Service
        - Automatic retry logic (3 attempts)
        - Exponential backoff
        - Detailed error logging
        """
        endpoint = f"/documents/collections/{collection}/documents/{doc_id}/content"
        params = {"type": doc_type}
        return await self._make_request("GET", endpoint, params=params)
```

**Features**:

- ✅ Retry logic with tenacity
- ✅ Connection pooling
- ✅ Timeout handling (30s default)
- ✅ Structured error responses

---

### **3. Admin Documents API Refactored**

**File**: `admin_service/app/api/documents.py`

```python
@router.get("/collections/{collection_name}/documents/{doc_id}/preview/{doc_type}")
async def preview_document(collection_name: str, doc_id: str, doc_type: str):
    """
    Proxy request to RAG Service (no direct file access)
    """
    rag_client = get_rag_client()
    response = await rag_client.get_document_content(
        collection=collection_name,
        doc_id=doc_id,
        doc_type=doc_type
    )
    # Transform response to match frontend expectations
    return format_preview_response(response)
```

**Changes**:

- ❌ Removed: `document_renderer.py` (180 lines deleted)
- ❌ Removed: `admin_path_config.get_document_source_path()`
- ❌ Removed: `admin_path_config.get_document_json_path()`
- ✅ Added: `rag_client.get_document_content()` call

---

## 🐳 Docker Configuration

### **Volume Mounts - BEFORE**

```yaml
admin-service:
  volumes:
    - ./rag_service/data:/app/data # ❌ REMOVED
    - ./rag_service/app:/app/rag_service_app # ❌ REMOVED
    - ./admin_service/app:/app/app
```

### **Volume Mounts - AFTER**

```yaml
admin-service:
  volumes:
    - ./admin_service/app:/app/app # ✅ Admin code only
    - ./admin_service/main.py:/app/main.py
  environment:
    - RAG_SERVICE_URL=http://rag-service:8000
    - INTERNAL_API_KEY=dev-internal-key
```

**Key Changes**:

- 🗑️ Removed shared data volume mount
- 🗑️ Removed RAG source code mount
- ✅ Communication via HTTP only

---

## 🔐 Security Implementation

### **1. API Key Validation**

```python
# RAG Service
async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    expected_key = settings.internal_api_key
    if x_internal_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden")
```

### **2. Network Isolation**

```yaml
networks:
  legalrag-network: # Services isolated on private network
```

### **3. Environment Variables**

```bash
# Production: Use secrets management
INTERNAL_API_KEY=<strong-random-key>

# Development
INTERNAL_API_KEY=dev-internal-key
```

---

## 📝 API Documentation

### **Request Example**

```bash
# Admin Service calls RAG Service
curl -X GET \
  "http://rag-service:8000/api/internal/documents/collections/hop_dong/documents/DOC_001/content?type=docx" \
  -H "X-Internal-API-Key: dev-internal-key"
```

### **Response Format**

```json
{
  "success": true,
  "content_type": "html",
  "content": "<html>...</html>",
  "doc_id": "DOC_001",
  "collection": "hop_dong",
  "filename": "Hop_dong_mua_ban.docx",
  "timestamp": "2025-10-11T10:30:00"
}
```

---

## 🧪 Testing Strategy

### **1. RAG Service Internal Endpoint**

```python
# test/test_document_api_gateway.py

async def test_get_docx_content():
    headers = {"X-Internal-API-Key": "dev-internal-key"}
    response = await client.get(
        "/api/internal/documents/collections/hop_dong/documents/DOC_001/content?type=docx",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["content_type"] == "html"
    assert "<html>" in response.json()["content"]

async def test_security_no_api_key():
    response = await client.get(
        "/api/internal/documents/collections/hop_dong/documents/DOC_001/content?type=docx"
    )
    assert response.status_code == 403
```

### **2. Admin Service Preview Endpoint**

```python
async def test_admin_preview_calls_rag_service():
    response = await client.get(
        "/api/collections/hop_dong/documents/DOC_001/preview/docx"
    )
    assert response.status_code == 200
    # Verify no direct file access in logs
```

### **3. Frontend Integration**

- Manual testing in Admin panel
- Click DOC/JSON badges → Verify preview displays
- Check browser console for errors

---

## 📊 Comparison Table

| Aspect            | Direct File Access ❌ | API Gateway ✅   |
| ----------------- | --------------------- | ---------------- |
| **Coupling**      | Tight (shared volume) | Loose (HTTP API) |
| **Scaling**       | Difficult             | Easy             |
| **Security**      | File-level            | API-level        |
| **Testing**       | Complex               | Simple           |
| **Debugging**     | Hard (file I/O)       | Easy (HTTP logs) |
| **Maintenance**   | Duplicate code        | Centralized      |
| **CRUD Ready**    | No                    | Yes              |
| **Microservices** | Anti-pattern          | Best practice    |

---

## 🚀 Deployment Checklist

### **Build & Start**

```bash
# 1. Build images
docker-compose -f docker-compose.dev.yml build --no-cache rag-service admin-service

# 2. Start services
docker-compose -f docker-compose.dev.yml up -d

# 3. Verify health
curl http://localhost:8000/api/internal/documents/health
curl http://localhost:8001/health
```

### **Verify Logs**

```bash
# Check for successful API registration
docker-compose -f docker-compose.dev.yml logs rag-service | grep "Internal Documents API"

# Monitor HTTP requests
docker-compose -f docker-compose.dev.yml logs -f admin-service | grep "📡"
```

---

## ✅ Architecture Compliance

**Verification Checklist**:

- ✅ Admin Service không trực tiếp đọc files
- ✅ Tất cả file access đi qua RAG Service API
- ✅ Security headers được validate
- ✅ Error handling đầy đủ (retry, timeout, fallback)
- ✅ Docker volume chỉ mount vào RAG Service
- ✅ Logs cho thấy HTTP requests giữa services
- ✅ Response format consistent với frontend

---

## 🎯 Real-World Examples

**This pattern is used by:**

- **Grafana** → Prometheus (metrics gateway)
- **Kibana** → Elasticsearch (data gateway)
- **Kong API Gateway** → Backend services
- **AWS API Gateway** → Lambda functions

**Not textbook theory - PRODUCTION STANDARD** 🏆

---

## 📚 Related Documentation

- [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md) - Overall system architecture
- [QUESTIONS_CRUD_ANALYSIS.md](QUESTIONS_CRUD_ANALYSIS.md) - Questions management via API
- `admin_service/app/services/rag_client.py` - Client implementation
- `rag_service/app/api/internal_documents.py` - Server implementation

---

## 🔮 Future Enhancements

1. **Caching**: Redis cache for frequent previews
2. **CDN**: S3 + CloudFront for static documents
3. **Compression**: Gzip HTML responses
4. **Streaming**: Large files via chunked transfer
5. **Monitoring**: Prometheus metrics for API calls

---

**Migration completed successfully** ✅  
**Document preview now follows API Gateway best practices** 🎉
