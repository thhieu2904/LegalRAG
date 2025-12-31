# BaoCao - Đánh giá hệ thống LegalRAG

Thư mục này chứa scripts và dữ liệu để đánh giá hệ thống cho Chương 4 của luận văn.

## Cách chạy

### Bước 1: Cài đặt dependencies

```bash
cd BaoCao
pip install -r requirements.txt
```

### Bước 2: Đảm bảo hệ thống đang chạy

```bash
docker compose up -d
```

### Bước 3: Chạy evaluation

```bash
python run_evaluation.py
```

## Cấu trúc files

| File                | Mô tả                                   |
| ------------------- | --------------------------------------- |
| `test_set.json`     | 20 câu hỏi test với chunk IDs thực tế   |
| `config.json`       | Cấu hình API và database                |
| `run_evaluation.py` | Script chính - chạy test và tạo báo cáo |
| `requirements.txt`  | Dependencies                            |

## Output

Sau khi chạy, bạn sẽ có:

| File                      | Mô tả                       | Dùng cho          |
| ------------------------- | --------------------------- | ----------------- |
| `evaluation_results.json` | Kết quả chi tiết từng query | Debug, phân tích  |
| `final_report.md`         | Báo cáo Markdown            | Copy vào luận văn |

## Metrics được đo

### Retrieval (Truy xuất)

- Precision@5: % kết quả đúng trong top 5
- Recall@5: % thông tin đúng được tìm thấy trong top 5
- F1-Score: Trung bình điều hòa của P và R
- MRR: Vị trí kết quả đúng đầu tiên
- Hit Rate@5: % câu hỏi có ít nhất 1 kết quả đúng

### Performance (Hiệu năng)

- Latency Mean: Thời gian phản hồi trung bình
- Latency P95: 95% queries nhanh hơn giá trị này

## FAQ

### Metrics nào quan trọng nhất?

Cho luận văn RAG, quan trọng nhất là:

1. F1-Score (cân bằng Precision và Recall)
2. Hit Rate@5 (có tìm được thông tin đúng không)
3. Latency (hệ thống có nhanh không)

### Target values?

| Metric     | Target | Giải thích                      |
| ---------- | ------ | ------------------------------- |
| F1-Score   | > 0.70 | Tốt                             |
| Hit Rate@5 | > 90%  | Hầu hết queries có kết quả đúng |
| Latency    | < 10s  | Người dùng không phải chờ lâu   |
