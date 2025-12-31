# MinIO Storage Structure for LegalRAG

# =========================================

## 🗂️ **Bucket Organization**

MinIO sẽ thay thế file system hiện tại với các buckets sau:

```
minio://
├── legal-documents/          # Bucket chính cho văn bản luật
│   ├── bo_luat_dan_su/       # Bộ Luật Dân Sự
│   │   ├── DOC_001/
│   │   │   ├── original.json           # RAG content (structured)
│   │   │   ├── original.docx          # Original document
│   │   │   └── metadata.json          # Document metadata
│   │   ├── DOC_002/
│   │   └── ...
│   ├── bo_luat_ho_tich/      # Bộ Luật Hộ Tịch
│   │   ├── DOC_001/
│   │   └── ...
│   └── bo_luat_bao_hiem/     # Bộ Luật Bảo Hiểm
│       └── ...
│
├── legal-forms/              # Bucket cho mẫu đơn
│   ├── ho_tich/              # Forms theo loại
│   │   ├── khai_sinh.docx
│   │   ├── khai_tu.docx
│   │   └── mapping/
│   │       ├── khai_sinh_mapping.json
│   │       └── khai_tu_mapping.json
│   ├── bao_hiem/
│   └── dan_su/
│
└── legal-cache/              # Bucket cho cache (optional)
    ├── embeddings/           # Cached embeddings (backup)
    └── processed/            # Processed documents cache
```

## 📋 **Path Convention**

### Document Path Pattern:

```
/{bucket}/{bo_luat_ma}/{doc_id}/{file_type}
```

**Examples:**

- JSON content: `/legal-documents/bo_luat_ho_tich/DOC_001/original.json`
- Original file: `/legal-documents/bo_luat_ho_tich/DOC_001/original.docx`
- Metadata: `/legal-documents/bo_luat_ho_tich/DOC_001/metadata.json`

### Form Path Pattern:

```
/{bucket}/{loai_mau_don}/{ten_file}
```

**Examples:**

- Form file: `/legal-forms/ho_tich/khai_sinh.docx`
- Form mapping: `/legal-forms/ho_tich/mapping/khai_sinh_mapping.json`

## 🔗 **Database Link Pattern**

### PostgreSQL `van_ban_luat` table sẽ lưu paths:

```sql
-- Example row
{
  "id": 1,
  "ma_van_ban": "DOC_001",
  "ten_van_ban": "Quy trình cấp giấy khai sinh",
  "minio_bucket": "legal-documents",
  "minio_path": "/bo_luat_ho_tich/DOC_001/",
  "json_path": "/bo_luat_ho_tich/DOC_001/original.json",
  "original_path": "/bo_luat_ho_tich/DOC_001/original.docx"
}
```

### PostgreSQL `mau_don` table sẽ lưu form paths:

```sql
-- Example row
{
  "id": 1,
  "van_ban_id": 1,
  "ten_mau_don": "khai_sinh.docx",
  "minio_bucket": "legal-forms",
  "minio_path": "/ho_tich/khai_sinh.docx",
  "mapping_config": {
    "scan_ho_ten": "field_ten_tre",
    "scan_ngay_sinh": "field_ngay_sinh",
    ...
  }
}
```

## 🔒 **Access Control (MinIO Policies)**

### 1. Public Read Policies (for forms)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "*" },
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::legal-forms/*"]
    }
  ]
}
```

### 2. Private Policies (for documents)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::storage-service:user" },
      "Action": ["s3:*"],
      "Resource": ["arn:aws:s3:::legal-documents/*"]
    }
  ]
}
```

## 📊 **Metadata JSON Structure**

### Document Metadata (`metadata.json`):

```json
{
  "doc_id": "DOC_001",
  "title": "Quy trình cấp giấy khai sinh",
  "type": "quy_trinh",
  "bo_luat": "bo_luat_ho_tich",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "version": "1.0",
  "checksum": "sha256:abc123...",
  "file_size": 125000,
  "page_count": 5
}
```

### Form Mapping (`mapping.json`):

```json
{
  "form_type": "khai_sinh",
  "field_mappings": {
    "scan_ho_ten": {
      "target_field": "field_ten_tre",
      "field_type": "text",
      "required": true
    },
    "scan_ngay_sinh": {
      "target_field": "field_ngay_sinh",
      "field_type": "date",
      "format": "DD/MM/YYYY",
      "required": true
    },
    "scan_gioi_tinh": {
      "target_field": "field_gioi_tinh",
      "field_type": "select",
      "options": ["Nam", "Nữ"],
      "required": true
    }
  }
}
```

## 🚀 **Migration Strategy**

### Phase 1: Setup MinIO Infrastructure

1. Deploy MinIO server (Docker/standalone)
2. Create buckets with proper policies
3. Configure access credentials

### Phase 2: Data Migration

1. **Documents Migration**:

   ```
   Local: data/storage/collections/{collection}/documents/DOC_XXX/
   → MinIO: legal-documents/{bo_luat_ma}/DOC_XXX/
   ```

2. **Forms Migration**:

   ```
   Local: data/storage/collections/{collection}/documents/DOC_XXX/forms/
   → MinIO: legal-forms/{loai_mau_don}/
   ```

3. **Update Database**:
   - Insert records vào `van_ban_luat` với MinIO paths
   - Insert records vào `mau_don` với MinIO paths

### Phase 3: Service Integration

1. Create Storage Service (API cho MinIO access)
2. Update RAG Service to use Storage Service
3. Update Admin Service to manage MinIO files

## 🔧 **MinIO Client Configuration**

### Python (using `minio` library):

```python
from minio import Minio

# Initialize MinIO client
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False  # Set True for HTTPS
)

# Upload file example
minio_client.fput_object(
    "legal-documents",
    "bo_luat_ho_tich/DOC_001/original.json",
    "/local/path/to/file.json"
)

# Download file example
minio_client.fget_object(
    "legal-documents",
    "bo_luat_ho_tich/DOC_001/original.json",
    "/local/path/to/download.json"
)

# Get presigned URL (for frontend access)
url = minio_client.presigned_get_object(
    "legal-forms",
    "ho_tich/khai_sinh.docx",
    expires=timedelta(hours=1)
)
```

## 📈 **Benefits of MinIO Structure**

1. **Versioning**: MinIO supports object versioning natively
2. **Access Control**: Fine-grained bucket policies
3. **Scalability**: Easy to scale storage independently
4. **Backup**: Built-in replication and backup features
5. **S3 Compatible**: Can migrate to AWS S3 easily later
6. **Performance**: Better than file system for concurrent access
7. **CDN Integration**: Can add CDN layer for forms delivery

## 🔍 **Example Queries**

### Get document file from database + MinIO:

```python
# 1. Query database for path
doc = db.query("SELECT minio_bucket, json_path FROM van_ban_luat WHERE ma_van_ban = 'DOC_001'")

# 2. Get file from MinIO
content = minio_client.get_object(doc.minio_bucket, doc.json_path)
```

### Get form file linked to document:

```python
# 1. Query database for form path (with FK relationship)
form = db.query("""
    SELECT m.minio_bucket, m.minio_path, m.mapping_config
    FROM mau_don m
    JOIN van_ban_luat v ON m.van_ban_id = v.id
    WHERE v.ma_van_ban = 'DOC_001'
""")

# 2. Get form file from MinIO
form_content = minio_client.get_object(form.minio_bucket, form.minio_path)

# 3. Get presigned URL for frontend
form_url = minio_client.presigned_get_object(form.minio_bucket, form.minio_path)
```
