# Hệ Thống RAG Nâng Cao với Reranker và Context Expansion

## Tổng Quan

Hệ thống RAG đã được nâng cấp với quy trình truy vấn thông minh hơn, từ việc lấy nhiều nguồn rời rạc sang một quy trình có hệ thống: **Tìm kiếm → Chắt lọc → Mở rộng → Tổng hợp**.

## Kiến Trúc Mới

### 1. Reranker Service (`reranker_service.py`)

- **Model**: AITeamVN/Vietnamese_Reranker
- **Chức năng**: Đánh giá lại độ liên quan của documents với query
- **Ưu điểm**: Chính xác hơn nhiều so với vector similarity thông thường

### 2. Context Expansion Service (`context_expansion_service.py`)

- **Chức năng**: Mở rộng ngữ cảnh xung quanh chunk "hạt nhân"
- **Cách hoạt động**: Tìm và lấy các chunks trước/sau trong cùng document
- **Kết quả**: Ngữ cảnh liền mạch, đầy đủ cho LLM

### 3. Enhanced RAG Service

- Tích hợp toàn bộ quy trình mới
- Hỗ trợ monitoring và debugging chi tiết
- Fallback graceful khi các service phụ không khả dụng

## Quy Trình Truy Vấn Mới

### Bước 1: Tìm Kiếm Rộng

```python
broad_search_k = 30          # Thay vì 5 như trước
similarity_threshold = 0.3   # Threshold thấp để không bỏ sót
```

- Tìm 20-30 documents với ngưỡng tương đồng thấp (0.3)
- Đảm bảo không bỏ sót thông tin tiềm năng
- Routing thông minh để tìm đúng collection

### Bước 2: Reranking

```python
reranker = RerankerService()
core_document = reranker.get_best_document(query, broad_docs)
```

- Sử dụng Vietnamese Reranker để đánh giá lại
- Tìm ra 1 document "hạt nhân" chính xác nhất
- Rerank score thường chính xác hơn vector similarity

### Bước 3: Mở Rộng Ngữ Cảnh

```python
expansion_service = ContextExpansionService(vectordb)
expanded_chunks = expansion_service.expand_context(core_document, expansion_size=1)
```

- Tìm chunks trước và sau chunk hạt nhân trong cùng document
- Tạo ngữ cảnh liền mạch từ 3 chunks (trước-hạt nhân-sau)
- Giữ nguyên thứ tự và luồng logic của văn bản gốc

### Bước 4: Tổng Hợp Câu Trả Lời

```python
coherent_context = expansion_service.create_coherent_context(expanded_chunks)
```

- Nối các chunks thành một khối văn bản mạch lạc
- Cung cấp cho LLM ngữ cảnh chất lượng cao, tập trung
- Kết quả: Câu trả lời chính xác và đầy đủ hơn

## So Sánh Với Hệ Thống Cũ

| Aspect           | Hệ Thống Cũ           | Hệ Thống Mới                  |
| ---------------- | --------------------- | ----------------------------- |
| **Tìm kiếm**     | 5 docs, threshold=0.7 | 30 docs, threshold=0.3        |
| **Chọn lọc**     | Vector similarity     | Vietnamese Reranker           |
| **Ngữ cảnh**     | Nhiều chunks rời rạc  | 1 khối liền mạch              |
| **Độ chính xác** | Trung bình            | Cao hơn đáng kể               |
| **Tốc độ LLM**   | Chậm (nhiều context)  | Nhanh hơn (context tập trung) |
| **Stability**    | Dễ quá tải            | Ổn định hơn                   |

## Cách Sử Dụng

### 1. Cài Đặt

```bash
# Linux/Mac
cd backend
bash scripts/setup_enhanced_rag.sh

# Windows
cd backend
scripts\setup_enhanced_rag.bat
```

### 2. API Calls (Không Thay Đổi)

```python
# API endpoint vẫn giữ nguyên
response = rag_service.query(
    question="Quy trình cấp hộ tịch như thế nào?",
    broad_search_k=30,           # Mới: số docs tìm kiếm rộng
    similarity_threshold=0.3,    # Mới: threshold thấp hơn
    context_expansion_size=1,    # Mới: số chunks mở rộng
    use_routing=True
)
```

### 3. Monitoring Mới

```python
process_info = response['process_info']
print(f"Broad docs: {process_info['broad_docs_count']}")
print(f"Core rerank score: {process_info['core_document_rerank_score']}")
print(f"Expanded chunks: {process_info['expanded_chunks_count']}")
print(f"Reranker used: {process_info['reranker_used']}")
```

## Testing

### Chạy Test Suite

```bash
cd backend
python tests/test_new_rag_system.py
```

### Test Cases

1. **Reranker Service Test**: Kiểm tra reranker model
2. **Context Expansion Test**: Test logic mở rộng ngữ cảnh
3. **Full System Test**: Test toàn bộ quy trình với queries thực tế

## Performance Improvements

### Dự Kiến

- **Độ chính xác**: +30-50% (nhờ reranker)
- **Tốc độ phản hồi**: +20-30% (context tập trung)
- **Stability**: Ít lỗi hơn 50% (ít data gửi frontend)
- **User Experience**: Câu trả lời mạch lạc, đầy đủ hơn

### Monitoring Metrics

```python
health = rag_service.get_health_status()
# Kiểm tra:
# - health['reranker_loaded']
# - health['context_expansion_available']
# - process_info trong response
```

## Troubleshooting

### Reranker Không Hoạt Động

```python
if not rag_service.reranker_service.is_loaded():
    print("Reranker failed to load, using similarity fallback")
```

### Context Expansion Lỗi

- Hệ thống tự động fallback về core document
- Không ảnh hưởng đến khả năng trả lời câu hỏi

### Model Download

- Vietnamese Reranker (~400MB) sẽ được tải tự động lần đầu
- Cache tại `data/models/rerank/` hoặc HuggingFace cache

## Next Steps

1. **Monitor Performance**: Thu thập metrics sau triển khai
2. **Fine-tune Parameters**: Điều chỉnh `broad_search_k`, `expansion_size`
3. **A/B Testing**: So sánh với hệ thống cũ trên queries thực tế
4. **Feedback Integration**: Cải thiện dựa trên phản hồi người dùng

## Dependencies Mới

- **sentence-transformers**: Đã có, bao gồm CrossEncoder
- **AITeamVN/Vietnamese_Reranker**: Tự động tải khi cần

Không cần cài đặt thêm package nào khác!
