# Development Tools

Thư mục này chứa các công cụ debug và phân tích dành cho developers.

## Debug Tools

### Database Debug

- `debug_vectordb.py` - Debug vector database
- `debug_collections.py` - Debug collections trong ChromaDB
- `debug_collection_content.py` - Xem nội dung collections
- `debug_document.py` - Debug xử lý documents
- `debug_search.py` - Debug tìm kiếm

### Analysis Tools

- `analyze_chunks.py` - Phân tích chunks từ documents
- `chunk_viewer.py` - Xem preview chunks
- `compare_processors.py` - So sánh các processors khác nhau
- `verify_embeddings.py` - Kiểm tra tính toàn vẹn embeddings

### Simple Tools

- `simple_debug.py` - Debug đơn giản
- `simple_rebuild_test.py` - Test rebuild nhanh

## Cách sử dụng

Chạy từ thư mục `backend/`:

```bash
# Debug vector database
python tools/debug_vectordb.py

# Xem chunks
python tools/chunk_viewer.py

# Phân tích embeddings
python tools/verify_embeddings.py
```

## Lưu ý

- Các tools này KHÔNG dành cho production
- Chỉ sử dụng khi development hoặc troubleshooting
- Một số tools có thể cần custom configuration
- Backup dữ liệu trước khi chạy các tools modify data
