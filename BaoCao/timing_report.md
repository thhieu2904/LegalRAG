# Kết quả đo thời gian RAG Pipeline

> Thời gian: 2025-12-28T00:34:36.897265

## Thông tin chung

| Thông số | Giá trị |
|----------|---------|
| Tổng số câu hỏi | 25 |
| Có timing đầy đủ | 23 |
| Yêu cầu clarification | 2 |

## Bảng 4.12 - Phân tích thời gian theo bước

| Bước | Thời gian TB | Std | Min | Max | Tỷ lệ |
|------|-------------|-----|-----|-----|-------|
| Embedding query | 89 ms | ±24 | 68 | 159 | 0.7% |
| Vector search | 6 ms | ±1 | 6 | 8 | 0.1% |
| Reranking | 11,696 ms | ±1,817 | 9,752 | 15,664 | 90.4% |
| LLM Generation | 1,071 ms | ±362 | 594 | 2,040 | 8.3% |
| Other | 78 ms | - | - | - | 0.6% |
| **Tổng** | **12,940 ms** | **±1,849** | **10,741** | **16,973** | **100%** |

## Nhận xét

- Các bước Embedding (0.7%), Vector Search (0.1%), Reranking (90.4%) chiếm tổng cộng 91.2% - cho thấy retrieval pipeline hiệu quả.
- Thời gian phản hồi trung bình (12,940ms) vượt ngưỡng 10s, cần tối ưu bằng local LLM hoặc streaming.

---
*Dữ liệu được đo tự động bởi test_timing.py*
