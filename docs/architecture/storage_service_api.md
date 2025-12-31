# Storage Service Architecture

# ============================

## 🎯 **Purpose**

Service riêng biệt để quản lý tất cả file operations với MinIO, cách ly storage logic khỏi RAG Service.

## 🏗️ **Service Structure**

```
storage_service/
├── Dockerfile
├── requirements.txt
├── main.py
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── documents.py      # Document file operations
│   │   ├── forms.py          # Form file operations
│   │   ├── upload.py         # File upload endpoints
│   │   └── health.py         # Health check
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # MinIO + DB config
│   │   └── database.py       # PostgreSQL connection
│   ├── services/
│   │   ├── __init__.py
│   │   ├── minio_service.py  # MinIO operations wrapper
│   │   └── metadata_service.py # DB metadata operations
│   └── models/
│       ├── __init__.py
│       └── schemas.py        # Pydantic models
└── tests/
```

## 📡 **API Endpoints**

### **1. Document Operations**

#### GET /documents/{bo_luat_ma}/{doc_id}/{file_type}

Get document file from MinIO

**Parameters:**

- `bo_luat_ma`: Mã bộ luật (e.g., 'bo_luat_ho_tich')
- `doc_id`: Document ID (e.g., 'DOC_001')
- `file_type`: File type ('json', 'original', 'metadata')

**Response:**

```json
{
  "success": true,
  "data": {
    "content": "<file content or presigned URL>",
    "metadata": {
      "size": 125000,
      "last_modified": "2024-01-15T10:30:00Z",
      "content_type": "application/json"
    }
  }
}
```

#### GET /documents/presigned-url/{bo_luat_ma}/{doc_id}/{file_type}

Get presigned URL for direct frontend access

**Query Parameters:**

- `expires_in`: Expiration time in seconds (default: 3600)

**Response:**

```json
{
  "success": true,
  "url": "http://minio:9000/legal-documents/...",
  "expires_at": "2024-01-15T11:30:00Z"
}
```

#### POST /documents/upload

Upload new document to MinIO and create DB record

**Request Body:**

```json
{
  "bo_luat_id": 1,
  "ma_van_ban": "DOC_001",
  "ten_van_ban": "Quy trình cấp giấy khai sinh",
  "files": {
    "json_content": "<base64 or multipart>",
    "original_file": "<base64 or multipart>",
    "metadata": {...}
  }
}
```

#### PUT /documents/{van_ban_id}

Update document file (versioned)

#### DELETE /documents/{van_ban_id}

Delete document (soft delete in DB, mark in MinIO)

### **2. Form Operations**

#### GET /forms/{loai_mau_don}/{ten_file}

Get form file from MinIO

**Response:**

```json
{
  "success": true,
  "data": {
    "file_url": "http://minio:9000/...",
    "mapping_config": {...}
  }
}
```

#### GET /forms/by-document/{van_ban_id}

Get all forms linked to a document (via FK relationship)

**Response:**

```json
{
  "success": true,
  "forms": [
    {
      "id": 1,
      "ten_mau_don": "khai_sinh.docx",
      "file_url": "http://minio:9000/...",
      "mapping_config": {...}
    }
  ]
}
```

#### POST /forms/upload

Upload new form and create mapping

**Request Body:**

```json
{
  "van_ban_id": 1,
  "ten_mau_don": "khai_sinh.docx",
  "loai_mau_don": "ho_tich",
  "form_file": "<multipart>",
  "mapping_config": {...}
}
```

### **3. Batch Operations**

#### POST /documents/batch-upload

Upload multiple documents in one request

#### GET /documents/list

List all documents with pagination and filtering

**Query Parameters:**

- `bo_luat_id`: Filter by bộ luật
- `page`: Page number
- `limit`: Items per page
- `search`: Search query

### **4. Health & Metadata**

#### GET /health

Health check for MinIO and PostgreSQL connections

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "minio": "connected",
    "postgresql": "connected"
  }
}
```

#### GET /storage/stats

Get storage statistics

**Response:**

```json
{
  "total_documents": 150,
  "total_forms": 45,
  "storage_size_bytes": 5000000,
  "by_bo_luat": {
    "bo_luat_ho_tich": 50,
    "bo_luat_bao_hiem": 100
  }
}
```

## 🔧 **Core Services Implementation**

### MinIO Service (`minio_service.py`)

```python
from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class MinIOService:
    """Wrapper cho MinIO operations"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Ensure required buckets exist"""
        buckets = ["legal-documents", "legal-forms", "legal-cache"]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info(f"✅ Created bucket: {bucket}")

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """Upload file to MinIO"""
        try:
            self.client.fput_object(bucket, object_name, file_path)
            logger.info(f"✅ Uploaded: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"❌ Upload failed: {e}")
            return False

    def upload_data(self, bucket: str, object_name: str, data: BinaryIO, length: int, content_type: str = "application/octet-stream") -> bool:
        """Upload binary data to MinIO"""
        try:
            self.client.put_object(bucket, object_name, data, length, content_type)
            logger.info(f"✅ Uploaded data: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"❌ Upload failed: {e}")
            return False

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """Download file from MinIO"""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            logger.info(f"✅ Downloaded: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"❌ Download failed: {e}")
            return False

    def get_object(self, bucket: str, object_name: str) -> Optional[bytes]:
        """Get object content as bytes"""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"❌ Get object failed: {e}")
            return None

    def get_presigned_url(self, bucket: str, object_name: str, expires: timedelta = timedelta(hours=1)) -> Optional[str]:
        """Get presigned URL for object"""
        try:
            url = self.client.presigned_get_object(bucket, object_name, expires=expires)
            return url
        except S3Error as e:
            logger.error(f"❌ Presigned URL failed: {e}")
            return None

    def delete_object(self, bucket: str, object_name: str) -> bool:
        """Delete object from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"✅ Deleted: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"❌ Delete failed: {e}")
            return False

    def list_objects(self, bucket: str, prefix: str = "") -> list:
        """List objects in bucket with prefix"""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"❌ List objects failed: {e}")
            return []

    def get_object_stat(self, bucket: str, object_name: str) -> Optional[dict]:
        """Get object metadata"""
        try:
            stat = self.client.stat_object(bucket, object_name)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "etag": stat.etag
            }
        except S3Error as e:
            logger.error(f"❌ Stat object failed: {e}")
            return None
```

### Metadata Service (`metadata_service.py`)

```python
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class MetadataService:
    """Service for PostgreSQL metadata operations"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_document(self, bo_luat_id: int, ma_van_ban: str, ten_van_ban: str,
                             minio_paths: dict) -> int:
        """Create new document record"""
        query = insert(van_ban_luat).values(
            bo_luat_id=bo_luat_id,
            ma_van_ban=ma_van_ban,
            ten_van_ban=ten_van_ban,
            minio_bucket=minio_paths.get("bucket"),
            minio_path=minio_paths.get("base_path"),
            json_path=minio_paths.get("json_path"),
            original_path=minio_paths.get("original_path")
        ).returning(van_ban_luat.c.id)

        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar()

    async def get_document_by_id(self, van_ban_id: int) -> Optional[dict]:
        """Get document by ID"""
        query = select(van_ban_luat).where(van_ban_luat.c.id == van_ban_id)
        result = await self.db.execute(query)
        return result.mappings().first()

    async def get_document_by_ma(self, ma_van_ban: str) -> Optional[dict]:
        """Get document by ma_van_ban"""
        query = select(van_ban_luat).where(van_ban_luat.c.ma_van_ban == ma_van_ban)
        result = await self.db.execute(query)
        return result.mappings().first()

    async def list_documents(self, bo_luat_id: Optional[int] = None,
                           limit: int = 50, offset: int = 0) -> List[dict]:
        """List documents with filtering"""
        query = select(van_ban_luat)
        if bo_luat_id:
            query = query.where(van_ban_luat.c.bo_luat_id == bo_luat_id)
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.mappings().all()

    async def create_form(self, van_ban_id: int, ten_mau_don: str,
                         loai_mau_don: str, minio_path: str,
                         mapping_config: dict) -> int:
        """Create new form record"""
        query = insert(mau_don).values(
            van_ban_id=van_ban_id,
            ten_mau_don=ten_mau_don,
            loai_mau_don=loai_mau_don,
            minio_bucket="legal-forms",
            minio_path=minio_path,
            mapping_config=mapping_config
        ).returning(mau_don.c.id)

        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar()

    async def get_forms_by_document(self, van_ban_id: int) -> List[dict]:
        """Get all forms for a document"""
        query = select(mau_don).where(mau_don.c.van_ban_id == van_ban_id)
        result = await self.db.execute(query)
        return result.mappings().all()
```

## 🔌 **Integration with RAG Service**

### RAG Service calls Storage Service via HTTP:

```python
# In RAG Service
import httpx

class StorageClient:
    """Client for Storage Service"""

    def __init__(self, base_url: str = "http://storage-service:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_document_json(self, bo_luat_ma: str, doc_id: str) -> dict:
        """Get document JSON content"""
        response = await self.client.get(
            f"{self.base_url}/documents/{bo_luat_ma}/{doc_id}/json"
        )
        return response.json()

    async def get_form_by_document(self, van_ban_id: int) -> list:
        """Get forms for document"""
        response = await self.client.get(
            f"{self.base_url}/forms/by-document/{van_ban_id}"
        )
        return response.json()
```

## 🐳 **Docker Compose Integration**

```yaml
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  storage-service:
    build: ./storage_service
    ports:
      - "8001:8001"
    environment:
      MINIO_ENDPOINT: "minio:9000"
      MINIO_ACCESS_KEY: "minioadmin"
      MINIO_SECRET_KEY: "minioadmin"
      DATABASE_URL: "postgresql://user:pass@postgres:5432/legalrag"
    depends_on:
      - minio
      - postgres
```

## 📊 **Benefits**

1. **Separation of Concerns**: Storage logic isolated from RAG logic
2. **Scalability**: Can scale storage service independently
3. **Security**: Centralized access control for MinIO
4. **Maintainability**: Easier to update storage logic without touching RAG
5. **Reusability**: Other services can also use Storage Service
6. **Testability**: Easier to mock storage operations
