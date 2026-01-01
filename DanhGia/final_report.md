# KẾT QUẢ ĐÁNH GIÁ HỆ THỐNG LEGALRAG

> Báo cáo tự động - 2025-12-28T00:51:32.792214

## 1. Tổng quan đánh giá

| Thông số | Giá trị |
|----------|---------|
| Số câu hỏi test | 25 |
| API endpoint | http://localhost:8002 |

---

## 2. Kết quả Retrieval - Mức Chunk

> Đánh giá khả năng tìm đúng **đoạn văn** liên quan (yêu cầu ground truth chunk IDs)

| Metric | Mean | Std | Min | Max | Mục tiêu | Đạt |
|--------|------|-----|-----|-----|----------|-----|
| **Precision@5** | 0.260 | ±0.123 | 0.000 | 0.500 | > 0.60 | ❌ |
| **Recall@5** | 0.920 | ±0.277 | 0.000 | 1.000 | > 0.60 | ✅ |
| **F1-Score** | 0.398 | ±0.162 | 0.000 | 0.667 | > 0.60 | ❌ |

*Số queries có ground truth: 25*

---

## 3. Kết quả Retrieval - Mức Document

> Đánh giá khả năng tìm đúng **văn bản** liên quan

| Metric | Giá trị | Chi tiết | Mục tiêu | Đạt |
|--------|---------|----------|----------|-----|
| **Hit Rate** | 92.0% | 23/25 | > 80% | ✅ |
| **MRR** | 0.920 | ±0.277 | > 0.70 | ✅ |
| **Top-1 Accuracy** | 92.0% | 23/25 | > 70% | ✅ |

---

## 4. Chất lượng câu trả lời

| Metric | Giá trị | Chi tiết | Ghi chú |
|--------|---------|----------|---------|
| **Answer Rate** | 92.0% | 23/25 | Câu hỏi được trả lời trực tiếp |
| **Clarification Rate** | 8.0% | 2/25 | Câu hỏi cần làm rõ |

---

## 5. Hiệu năng hệ thống

| Metric | Giá trị | Mục tiêu | Đạt |
|--------|---------|----------|-----|
| **Thời gian phản hồi TB** | 2930 ms | < 10,000 ms | ✅ |
| **Độ lệch chuẩn** | ±681 ms | - | - |
| **Thời gian Min** | 1453 ms | - | - |
| **Thời gian Max** | 4116 ms | < 15,000 ms | ✅ |
| **P95 Latency** | 4082 ms | - | - |

### 5.1. Phân tích thời gian từng bước

| Bước | Thời gian TB | Tỷ lệ |
|------|-------------|-------|
| Embedding query | 139 ms | 4.7% |
| Vector search | 6 ms | 0.2% |
| Reranking | 1783 ms | 60.8% |
| LLM Generation | 987 ms | 33.7% |
| Other | 16 ms | 0.5% |
| **Tổng** | **2930 ms** | **100%** |

*Dữ liệu từ 23 queries có timing đầy đủ*

---

## 6. Phân tích theo danh mục

| Danh mục | Hit Rate | Số queries | Latency TB |
|----------|----------|------------|------------|
| ho-tich | 92.9% | 14 | 2730 ms |
| doanh-nghiep | 66.7% | 3 | 2817 ms |
| nuoi-con-nuoi | 100.0% | 5 | 3414 ms |
| bao-hiem-y-te | 100.0% | 3 | 3173 ms |

---

## 7. Chi tiết từng câu hỏi

| # | Danh mục | Câu hỏi | P@5 | R@5 | F1 | Hit | Lat | KQ |
|---|----------|---------|-----|-----|-----|-----|-----|-----|
| 1 | ho-tich | Thời hạn giải quyết đăng ký khai si... | 0.33 | 1.00 | 0.50 | ✅ | 4082 | OK |
| 2 | ho-tich | Cha mẹ có trách nhiệm đăng ký khai ... | 0.33 | 1.00 | 0.50 | ✅ | 1928 | OK |
| 3 | ho-tich | Thời hạn xác minh tình trạng hôn nh... | 0.33 | 1.00 | 0.50 | ✅ | 1453 | OK |
| 4 | ho-tich | Trường hợp cha mẹ lựa chọn quốc tịc... | 0.20 | 1.00 | 0.33 | ✅ | 1877 | OK |
| 5 | ho-tich | Đối tượng nào được thực hiện thủ tụ... | 0.20 | 1.00 | 0.33 | ✅ | 3001 | OK |
| 6 | ho-tich | Điều kiện độ tuổi để đăng ký kết hô... | 0.20 | 1.00 | 0.33 | ✅ | 2526 | OK |
| 7 | ho-tich | Khi nộp hồ sơ đăng ký kết hôn, bên ... | 0.25 | 1.00 | 0.40 | ✅ | 2933 | OK |
| 8 | ho-tich | Thời hạn giải quyết việc xác minh t... | 0.00 | 0.00 | 0.00 | ❌ | 2070 | Clarif |
| 9 | ho-tich | Cơ quan nào thực hiện đăng ký khai ... | 0.20 | 1.00 | 0.33 | ✅ | 2767 | OK |
| 10 | ho-tich | Thời hạn đăng ký khai tử là bao nhi... | 0.20 | 1.00 | 0.33 | ✅ | 2780 | OK |
| 11 | ho-tich | Những trường hợp nào được miễn lệ p... | 0.20 | 1.00 | 0.33 | ✅ | 2902 | OK |
| 12 | ho-tich | Khi đăng ký khai tử cho người chết ... | 0.20 | 1.00 | 0.33 | ✅ | 4116 | OK |
| 13 | ho-tich | Khi đăng ký giám hộ, nếu nộp bản sa... | 0.33 | 1.00 | 0.50 | ✅ | 2797 | OK |
| 14 | ho-tich | Tờ khai đăng ký giám hộ theo mẫu nà... | 0.20 | 1.00 | 0.33 | ✅ | 2984 | OK |
| 15 | doanh-nghiep | Lệ phí đăng ký thành lập hộ kinh do... | 0.50 | 1.00 | 0.67 | ✅ | 3056 | OK |
| 16 | doanh-nghiep | Thành phần hồ sơ đăng ký thành lập ... | 0.50 | 1.00 | 0.67 | ✅ | 3382 | OK |
| 17 | doanh-nghiep | Trường hợp ủy quyền thực hiện thủ t... | 0.00 | 0.00 | 0.00 | ❌ | 2014 | Clarif |
| 18 | nuoi-con-nuoi | Những trường hợp nào được miễn lệ p... | 0.40 | 1.00 | 0.57 | ✅ | 3314 | OK |
| 19 | nuoi-con-nuoi | Thời gian kiểm tra hồ sơ và lấy ý k... | 0.40 | 1.00 | 0.57 | ✅ | 2980 | OK |
| 20 | nuoi-con-nuoi | Những trường hợp nào không được nhậ... | 0.20 | 1.00 | 0.33 | ✅ | 3667 | OK |
| 21 | nuoi-con-nuoi | Hồ sơ đăng ký nuôi con nuôi trong n... | 0.33 | 1.00 | 0.50 | ✅ | 3925 | OK |
| 22 | nuoi-con-nuoi | Thời hạn xác minh hoàn cảnh gia đìn... | 0.20 | 1.00 | 0.33 | ✅ | 3187 | OK |
| 23 | bao-hiem-y-te | Khi khám bệnh bảo hiểm y tế, trẻ em... | 0.25 | 1.00 | 0.40 | ✅ | 3401 | OK |
| 24 | bao-hiem-y-te | Phiếu chuyển cơ sở khám bệnh chữa b... | 0.20 | 1.00 | 0.33 | ✅ | 2882 | OK |
| 25 | bao-hiem-y-te | Người đã hiến bộ phận cơ thể khi kh... | 0.33 | 1.00 | 0.50 | ✅ | 3236 | OK |

---

## 8. Nhận xét và đánh giá

- **F1-Score thấp** (0.398): Cần cải thiện embedding hoặc chunking strategy.
- **Hit Rate cao** (92.0%): Hầu hết câu hỏi tìm đúng văn bản liên quan.
- **Thời gian phản hồi nhanh** (2930ms): Đáp ứng tốt yêu cầu < 10s.
- **Clarification Rate 8.0%**: Hệ thống yêu cầu làm rõ khi câu hỏi mơ hồ - đây là tính năng thiết kế, không phải lỗi.

---
*Báo cáo được tạo tự động bởi LegalRAG Evaluation Script*
