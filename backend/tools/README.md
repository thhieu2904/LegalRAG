# LegalRAG Backend Tools

Bộ công cụ cần thiết cho LegalRAG system setup và maintenance.

## 🚀 Quick Setup cho máy mới (3 bước đơn giản)

### Bước 1: Download AI Models

```bash
cd backend
python tools/download_models.py
```

**Mục đích**: Download các AI models cần thiết về đúng vị trí

- Vietnamese embedding model
- Reranker model
- Vietnamese LLM model

**Lưu ý**: Bước này cần internet và có thể mất vài phút

---

### Bước 2: Setup hệ thống hoàn chỉnh

```bash
cd backend
python tools/setup_system.py
```

**Mục đích**: Setup toàn bộ hệ thống

- Tạo cấu trúc thư mục
- Kiểm tra documents
- Kiểm tra models
- Build vector database
- Test hệ thống

---

### Bước 3: Build Router Cache (optional, để startup nhanh)

```bash
cd backend
python tools/build_router_cache.py
```

**Mục đích**: Tạo cache để hệ thống khởi động nhanh (0.06s thay vì 30-60s)

## 📋 Individual Tools (cho advanced users)

### download_models.py

**Purpose**: Download AI models về đúng vị trí

**Usage**:

```bash
python tools/download_models.py              # Download missing models
python tools/download_models.py --force      # Force re-download all
python tools/download_models.py --verify-only # Only verify existing models
```

**Models downloaded**:

- `keepitreal/vietnamese-sbert` (embedding)
- `BAAI/bge-reranker-base` (reranker)
- `vinai/phobert-base-v2` (Vietnamese LLM)

---

### setup_system.py

**Purpose**: Setup hệ thống hoàn chỉnh trên máy mới

**Usage**:

```bash
python tools/setup_system.py                 # Normal setup
python tools/setup_system.py --force-rebuild # Force rebuild vector DB
```

**What it does**:

1. ✅ Tạo cấu trúc thư mục cần thiết
2. ✅ Kiểm tra documents tồn tại
3. ✅ Verify models đã download
4. ✅ Build vector database từ documents
5. ✅ Test hệ thống hoạt động

**Prerequisites**:

- Documents trong `data/documents/`
- Models đã download (chạy `download_models.py` trước)

---

### build_router_cache.py

**Purpose**: Build router cache để startup nhanh

**Usage**:

```bash
python tools/build_router_cache.py
```

**Benefits**:

- ✅ Fast startup: 0.06s instead of 30-60s
- ✅ Pre-computed embeddings
- ✅ Smart routing decisions

**Output**: Cache files trong `data/cache/`

---

### generate_router_examples.py

**Purpose**: Tạo router examples từ documents (đã integrated vào setup_system.py)

**Usage**:

```bash
python tools/generate_router_examples.py
```

**Output**: Router examples trong `data/router_examples/`

---

## 🔧 Troubleshooting

### Lỗi "Models not found"

```bash
python tools/download_models.py --force
```

### Lỗi "No documents found"

- Đảm bảo documents JSON trong `data/documents/quy_trinh_*/`
- Check structure: `data/documents/quy_trinh_cap_ho_tich_cap_xa/*.json`

### Vector database không build được

```bash
python tools/setup_system.py --force-rebuild
```

### Startup chậm

```bash
python tools/build_router_cache.py
```

## 📊 System Requirements

- Python 3.11+
- Conda environment: `LegalRAG_v1`
- Internet (for model download)
- ~2GB disk space (for models)
- GPU optional (but recommended)

## 🎯 Recommended Workflow cho máy mới

1. **First time setup**:

   ```bash
   cd backend
   conda activate LegalRAG_v1
   python tools/download_models.py     # Download models
   python tools/setup_system.py       # Setup everything
   python tools/build_router_cache.py # Build cache (optional)
   ```

2. **Start system**:

   ```bash
   python main.py
   ```

3. **Rebuild when needed**:
   ```bash
   python tools/setup_system.py --force-rebuild
   ```

Mỗi tool hoạt động độc lập và có thể chạy riêng lẻ khi cần thiết.

---

### 2. enhance_filter_keywords.py

**Purpose**: Phân tích và cải thiện filter keywords cho "trinh sát & chỉ điểm"

**Usage**:

```bash
cd backend
python tools/enhance_filter_keywords.py
python tools/enhance_filter_keywords.py --interactive
```

**Benefits**: Optimize keywords cho kế hoạch filtered search

---

### 3. build_router_cache.py

**Purpose**: Tạo cache cho Enhanced Smart Query Router sử dụng Vietnamese embedding model

**Usage**:

```bash
cd backend
python tools/build_router_cache.py
```

**Output**: `data/cache/router_cache.pkl` (1.10 MB, 272 câu hỏi vectors)

**Benefits**: Giảm startup time từ 30-60s xuống 0.06s

---

### 2. build_document_vectordb.py

**Purpose**: Xây dựng vector database từ documents trong `data/documents/`

**Usage**:

```bash
cd backend
python tools/build_document_vectordb.py
```

**Output**: Vector database trong `data/vectordb/`

**Note**: Cần có JSON documents trong `data/documents/`

---

## 🎯 Workflow cho máy mới

### Option 1: Complete Setup (Recommended)

```bash
cd backend

# Download models first (one-time)
python scripts/fresh_install_setup.py

# Complete setup in one command
python tools/complete_setup.py

# Start application
python main.py
```

### Option 2: Manual Setup

```bash
cd backend

# Step 1: Download models
python scripts/fresh_install_setup.py

# Step 2: Build vector database
python tools/build_document_vectordb.py

# Step 3: Build router cache
python tools/build_router_cache.py

# Step 4: Start application
python main.py
```

## ✅ Verification

Sau khi setup, bạn sẽ có:

- `data/vectordb/` - Vector database
- `data/cache/router_cache.pkl` - Router cache
- App startup trong ~0.06s thay vì 30-60s
