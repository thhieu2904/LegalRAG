# PHASE 1: TỐI ƯU HÓA TÍN HIỆU - LỘ TRÌNH CỤ THỂ

## 🎯 VẤN ĐỀ HIỆN TẠI

**Nhiễu từ Metadata khi tạo embeddings**:

- File `safe_cache_rebuild.py` đang dump **TẤT CẢ metadata** vào fused text
- Các thông tin chung chung (ngày tháng, cơ quan, legal_basis) làm "pha loãng" ý nghĩa cốt lõi
- Title (quan trọng nhất) bị lấn át bởi noise metadata

**Kết quả**: Router confidence cao (0.8084) nhưng chọn sai document vì embeddings nhiễu

## 🚀 PHASE 1: GIẢI PHÁP CỤ THỂ

### Step 1: Cải thiện Fused Text Generation

**File cần sửa**: `tools/safe_cache_rebuild.py`

**Hiện tại** (gây nhiễu):

```python
# Add metadata if available
if metadata:
    metadata_items = []
    for k, v in metadata.items():  # ❌ DUMP HẾT METADATA
        if isinstance(v, (str, list)) and str(v).strip():
            metadata_items.append(f"{k}: {str(v)}")
```

**Sửa thành** (filtered, weighted):

```python
# Add ONLY important metadata fields
important_fields = ['title', 'code', 'requirements_conditions']
if metadata:
    metadata_items = []

    # Title gets highest priority (first position)
    if 'title' in metadata:
        metadata_items.append(f"TITLE: {metadata['title']}")

    # Add other important fields
    for field in ['code', 'requirements_conditions']:
        if field in metadata and str(metadata[field]).strip():
            metadata_items.append(f"{field}: {metadata[field]}")
```

### Step 2: Weighted Fused Text Structure

**Thay đổi thứ tự priority**:

**Hiện tại**:

```
questions | METADATA: all_fields | CONTENT: content
```

**Sửa thành**:

```
TITLE: title | questions | key_metadata | content_summary
```

### Step 3: GPU Optimization

**File cần sửa**: `tools/safe_cache_rebuild.py` - function `generate_embeddings_safe`

**Thêm GPU support**:

```python
# Force GPU usage for embedding generation
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer(model_path, device=device)
logger.info(f"🎮 Using {device.upper()} for embedding generation")
```

## 📋 IMPLEMENTATION CHECKLIST

### ✅ Step 1: Sửa Metadata Filtering (10 phút)

- [ ] Sửa `_create_fused_text_like_vectordb()` trong `safe_cache_rebuild.py`
- [ ] Chỉ giữ title, code, requirements_conditions
- [ ] Title được ưu tiên đầu tiên

### ✅ Step 2: GPU Optimization (5 phút)

- [ ] Thêm GPU detection vào `generate_embeddings_safe()`
- [ ] Force model chạy trên GPU

### ✅ Step 3: Rebuild Cache (2-3 phút)

- [ ] Chạy `python tools/safe_cache_rebuild.py`
- [ ] Verify cache mới được tạo

### ✅ Step 4: Test & Validate (5 phút)

- [ ] Test lại query: "tôi cần làm giấy khai sinh cho con trai tôi, cha nó là người nước ngoài"
- [ ] Verify DOC_002 được chọn thay vì DOC_008

## 🎯 EXPECTED RESULTS

### Trước (hiện tại):

- Router confidence: 0.8084 → DOC_008 (SAI)
- Reranker score: 0.0079 (thấp vì conflict)

### Sau Phase 1:

- Router confidence: 0.75-0.85 → DOC_002 (ĐÚNG)
- Reranker score: > 0.1 (cao hơn vì align)
- Giảm confusion giữa similar documents

## 🔧 CODE CHANGES NEEDED

### 1. File: `tools/safe_cache_rebuild.py`

**Function**: `_create_fused_text_like_vectordb()`
**Change**: Filter metadata, prioritize title

### 2. File: `tools/safe_cache_rebuild.py`

**Function**: `generate_embeddings_safe()`
**Change**: Add GPU support

### 3. Run command:

```bash
cd rag_service/tools
python safe_cache_rebuild.py
```

## ⏱️ TIMELINE

**Total time**: ~20 phút

- Code changes: 15 phút
- Cache rebuild: 2-3 phút
- Testing: 2-3 phút

## 🚨 RISK MITIGATION

- **Backup current cache** trước khi rebuild
- **Test với multiple queries** để ensure không regression
- **Compare old vs new embeddings** để verify improvement

---

**Đây chính là Phase 1 đúng nghĩa - clean signal before complex routing!**
