# LegalRAG System Optimization Summary

## 🔧 Cấu Hình Tối Ưu Đã Thực Hiện

### Hardware-Specific Tuning

- **MAX_TOKENS**: `1024` - Tối ưu để giảm VRAM usage
- **CONTEXT_LENGTH**: `3072` tokens - Cân bằng performance và chất lượng
- **N_CTX**: `3072` - Đồng bộ với CONTEXT_LENGTH
- **N_GPU_LAYERS**: `32` - Tối ưu cho GPU của bạn (không dùng -1 auto)
- **N_BATCH**: `384` - Tối ưu batch processing

### Query Strategy Optimization

- **BROAD_SEARCH_K**: `30` - Tìm kiếm nhiều documents để không bỏ sót (có thể gây nghẽn GPU khi rerank)
- **SIMILARITY_THRESHOLD**: `0.4` - Lọc chặt hơn để chỉ lấy documents chất lượng cao
- **DEFAULT_SIMILARITY_THRESHOLD**: `0.4` - Đồng bộ với SIMILARITY_THRESHOLD

## 🚨 CRITICAL BUG FIX: Reranking Logic Error

### ❌ Lỗi Nghiêm Trọng Đã Được Phát Hiện:

**Vấn đề**: Hệ thống tìm kiếm 30 documents nhưng chỉ rerank 10 documents đầu tiên
**Hậu quả**: Các tài liệu chính xác có thể nằm ở vị trí 11-30 và bị loại bỏ oan uổng
**Triệu chứng**: Rerank score cực thấp (0.0163) báo hiệu không có tài liệu liên quan trong top 10

### ✅ Đã Sửa:

```python
# TRƯỚC (BUG):
max_rerank_docs = min(10, len(broad_search_results))  # CHỈ RERANK 10/30
docs_to_rerank = broad_search_results[:max_rerank_docs]

# SAU (FIXED):
docs_to_rerank = broad_search_results  # RERANK TẤT CẢ 30 DOCUMENTS
```

### 🛡️ Thêm Validation:

- Kiểm tra rerank score < 0.1 và cảnh báo
- Log chi tiết để monitor chất lượng kết quả

### Thay Đổi Quan Trọng Nhất

**TRƯỚC**: Chỉ lấy 1 chunk sau rerank → context hạn chế
**SAU**: Lấy 1 chunk cao nhất sau rerank → Load toàn bộ document chứa chunk đó

### Flow Mới:

```
1. Broad Search (30 documents, similarity ≥ 0.4)
2. Rerank (lấy 1 chunk có điểm cao nhất)
3. Find Source Document (từ chunk metadata)
4. Load Full Document (từ file JSON gốc)
5. Send Complete Context (toàn bộ document) to LLM
```

### Code Changes:

#### 1. OptimizedEnhancedRAGService

- **File**: `app/services/optimized_enhanced_rag_service.py`
- **Key Change**: `top_k=1` trong rerank + `include_full_document=True`
- **Result**: Lấy 1 nucleus chunk cao nhất, sau đó expand thành full document

#### 2. Enhanced Context Expansion

- **File**: `app/services/enhanced_context_expansion_service.py`
- **Key Function**: `_load_full_document()` - Load toàn bộ nội dung từ file JSON
- **Strategy**: Nucleus chunk → Source file → Full document content
- **Format**: Structured với metadata header + phân chia sections rõ ràng

#### 3. Environment Configuration

- **File**: `.env`
- **Updates**: Comments cập nhật để phản ánh tối ưu hóa mới
- **Key Values**: Tất cả đã được tinh chỉnh theo hardware specs

## 📈 Expected Benefits

### Performance

- **GPU Utilization**: Tối ưu với 32 layers thay vì auto-detect
- **Memory Management**: Context window 3072 tokens cho 6GB VRAM
- **Speed**: Batch size 384 tối ưu throughput

### Quality

- **Context Richness**: Full document thay vì fragment chunks
- **Answer Quality**: LLM nhận context đầy đủ, cấu trúc rõ ràng
- **Consistency**: Threshold 0.4 đảm bảo chỉ lấy documents liên quan

### User Experience

- **Comprehensive Answers**: Đầy đủ thông tin từ whole document
- **Structured Response**: Format document với headers và sections
- **Faster Processing**: GPU layers và batch size được tối ưu

## 🚀 Usage

### API Call Example:

```python
response = await optimized_query(
    OptimizedQueryRequest(
        query="Thủ tục khai sinh như thế nào?",
        use_full_document_expansion=True,  # KEY: Enables full document loading
        max_context_length=3000
    )
)
```

### Response Format:

```json
{
  "type": "answer",
  "answer": "Chi tiết đầy đủ từ toàn bộ document...",
  "context_info": {
    "nucleus_chunks": 1,
    "context_length": 2847,
    "source_collections": ["ho_tich_cap_xa"],
    "source_documents": ["path/to/document.json"]
  }
}
```

## ✅ Verification

Chạy test để xác nhận cấu hình:

```bash
cd backend
python test_config_summary.py
```

---

**Tóm tắt**: System đã được tối ưu hoá toàn diện từ hardware specs đến query strategy. Key innovation là chuyển từ "chunk-based" sang "document-based" context expansion, giúp LLM có đầy đủ thông tin để đưa ra câu trả lời chính xác và hoàn chỉnh hơn.
