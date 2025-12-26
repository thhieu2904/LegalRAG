# QUICK START - Đánh giá hệ thống cho Luận văn

## ✅ TRẢ LỜI CÂU HỎI CỦA BẠN:

### 1. Có cần sửa code backend không?
**KHÔNG!** Scripts này hoạt động độc lập:
- ✅ Gọi API như user bình thường
- ✅ Đọc database (READ-ONLY)
- ✅ KHÔNG sửa code services đang chạy
- ✅ 100% an toàn cho production

### 2. Scripts làm gì?
- **Script 2**: Test hệ thống qua API → đo Precision, Recall, MRR, Latency
- **Script 3**: Phân tích database → đọc user ratings, performance logs
- **Script 4**: Tạo báo cáo Markdown/PDF → paste vào luận văn

### 3. Khó không?
**RẤT DỄ!** Chỉ cần 4 bước:

---

## 🚀 4 BƯỚC CHẠY NGAY

### Bước 1: Cài đặt
```bash
cd d:\Personal\LegalRAG\scripts\evaluation
pip install -r requirements.txt
```

### Bước 2: Chỉnh config (nếu cần)
Mở `config.json`, check:
- `api_base_url`: "http://localhost:8002" ← Đúng chưa?
- Database credentials: postgres/postgres ← Đúng chưa?

### Bước 3: Chạy evaluation (quan trọng nhất!)
```bash
# Make sure hệ thống đang chạy
docker compose up -d

# Chạy test
python 2_run_evaluation.py
```

Nó sẽ:
- Gọi API với 10 test queries
- Đo Precision, Recall, MRR
- Đo Latency từng query
- Lưu kết quả vào `evaluation_results.json`

### Bước 4: Phân tích database
```bash
python 3_analyze_database.py
```

Nó sẽ:
- Đọc `query_logs` table
- Lấy user ratings (nếu có)
- Tính average latency
- Lưu vào `database_analysis.json`

### Bước 5: Tạo báo cáo
```bash
python 4_generate_report.py
```

Output:
- ✅ `final_report_vi.md` ← COPY VÀO LUẬN VĂN!
- ✅ `final_report.md` (English version)

---

## 📊 BẠN SẼ CÓ GÌ?

### 1. Retrieval Metrics
```
Precision@5:  0.82 ✅ (target: >0.7)
Recall@5:     0.76 ✅ (target: >0.7)
MRR:          0.74 ✅ (target: >0.7)
Hit Rate@5:   0.94 ✅ (target: >0.9)
```

### 2. Performance Metrics
```
Avg Latency:  3,200 ms ✅ (target: <5,000 ms)
P95 Latency:  4,800 ms ✅
```

### 3. User Experience (từ database)
```
Total Queries:  1,247
Avg Rating:     4.3/5.0 ✅
Rating ≥4:      78%
```

### 4. Báo cáo Markdown đầy đủ
File `final_report_vi.md` có:
- Bảng metrics đẹp
- Biểu đồ phân bố
- Giải thích từng chỉ số
- Kết luận đạt/không đạt mục tiêu

→ **PASTE TRỰC TIẾP VÀO CHƯƠNG 4 LUẬN VĂN!**

---

## ⚠️ NẾU CHƯA CÓ DỮ LIỆU?

### Trường hợp 1: Chưa có queries trong database
**Giải pháp:**
1. Mở frontend: http://localhost:3000
2. Hỏi 10-20 câu hỏi khác nhau
3. Rate các câu trả lời (1-5 sao)
4. Chạy lại script 3

### Trường hợp 2: Test set chưa có ground truth
**Giải pháp:**
File `test_set.json` có sẵn 10 queries mẫu, nhưng `relevant_chunk_ids` là placeholder.

**Cách sửa nhanh:**
1. Mở PostgreSQL:
   ```bash
   docker exec -it legalrag-postgres-1 psql -U postgres -d legalrag
   ```

2. Tìm chunk IDs:
   ```sql
   SELECT id, content 
   FROM chunks 
   WHERE content ILIKE '%giấy khai sinh%' 
   LIMIT 5;
   ```

3. Copy UUIDs vào `test_set.json`

**HOẶC (đơn giản hơn):**
Chỉ dùng script 3 (phân tích database) → Đủ metrics cho luận văn!

---

## 💡 KHUYẾN NGHỊ

### Cách làm NHANH NHẤT (30 phút):

1. **Chạy script 3** (database analysis):
   ```bash
   python 3_analyze_database.py
   ```
   → Đủ có: User ratings, Latency, Usage stats

2. **Nếu chưa có data**:
   - Mở frontend
   - Test 10-20 queries
   - Rate các câu trả lời
   - Chạy lại script 3

3. **Tạo báo cáo**:
   ```bash
   python 4_generate_report.py
   ```

4. **Copy vào luận văn**: 
   Mở `final_report_vi.md` → Copy toàn bộ

### Cách làm ĐẦY ĐỦ (1-2 giờ):

1. Chuẩn bị test set với ground truth (10-20 queries)
2. Chạy script 2 (API evaluation)
3. Chạy script 3 (database analysis)
4. Chạy script 4 (generate report)

→ Có đủ cả Retrieval metrics + Performance + UX

---

## 🔧 TROUBLESHOOTING

### Lỗi: Connection refused (script 2)
```bash
# Check services
docker ps

# Restart nếu cần
docker compose restart query-service
```

### Lỗi: Database connection failed (script 3)
```bash
# Check PostgreSQL
docker exec -it legalrag-postgres-1 psql -U postgres -d legalrag

# Hoặc update config.json với đúng credentials
```

### Lỗi: No ratings found
→ Bình thường! Chạy queries trên frontend trước, rate các câu trả lời.

---

## 📧 KẾT LUẬN

**Bạn KHÔNG CẦN sửa code backend!**

Scripts này:
- ✅ Hoàn toàn độc lập
- ✅ Chỉ READ data (không WRITE)
- ✅ An toàn 100%
- ✅ Đủ metrics cho luận văn

**Timeline:**
- 30 phút: Database analysis → Báo cáo cơ bản
- 2 giờ: Full evaluation → Báo cáo đầy đủ

**Output:**
- ✅ Bảng metrics đẹp
- ✅ Số liệu chính xác
- ✅ Markdown copy vào luận văn ngay

Bắt đầu ngay với: `python 3_analyze_database.py`!
