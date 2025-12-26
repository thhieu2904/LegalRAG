# EVALUATION SCRIPTS - HƯỚNG DẪN SỬ DỤNG

## 📋 MỤC ĐÍCH

Scripts này giúp bạn thu thập metrics cho báo cáo luận văn **mà KHÔNG cần sửa code backend**.

## 📂 CẤU TRÚC

```
scripts/evaluation/
├── README.md                    # File này
├── requirements.txt             # Dependencies
├── test_set.json               # Test queries với ground truth
├── 1_create_test_set.py        # Tạo test set
├── 2_run_evaluation.py         # Chạy evaluation tự động
├── 3_analyze_database.py       # Phân tích query_logs từ DB
├── 4_generate_report.py        # Tạo báo cáo PDF/Markdown
└── utils.py                    # Helper functions
```

## 🚀 CÁCH DÙNG NHANH

### Bước 1: Cài đặt dependencies
```bash
cd scripts/evaluation
pip install -r requirements.txt
```

### Bước 2: Tạo test set (hoặc dùng mẫu có sẵn)
```bash
python 1_create_test_set.py
```

### Bước 3: Chạy evaluation
```bash
python 2_run_evaluation.py
```

### Bước 4: Phân tích database
```bash
python 3_analyze_database.py
```

### Bước 5: Tạo báo cáo
```bash
python 4_generate_report.py
```

Output: `evaluation_report.md` và `evaluation_report.pdf`

---

## 📊 METRICS THU THẬP ĐƯỢC

### Từ API Testing (`2_run_evaluation.py`)
- Precision@5, Recall@5, MRR, Hit Rate
- Latency breakdown (embedding, search, rerank, generation)
- Faithfulness, Relevancy (nếu có LLM judge)

### Từ Database (`3_analyze_database.py`)
- User ratings (từ `query_logs.user_rating`)
- Query patterns (most frequent queries)
- Performance trends (latency over time)
- Error rates

---

## ⚙️ CẤU HÌNH

File `config.json`:
```json
{
  "api_base_url": "http://localhost:8002",
  "db_connection": {
    "host": "localhost",
    "port": 5432,
    "database": "legalrag",
    "user": "postgres",
    "password": "postgres"
  },
  "test_set_size": 50,
  "top_k": 5
}
```

---

## 📈 OUTPUT MẪU

```
EVALUATION REPORT
==========================================

1. RETRIEVAL METRICS
   - Precision@5:  0.82 ✅ (target: >0.7)
   - Recall@5:     0.76 ✅ (target: >0.7)
   - MRR:          0.74 ✅ (target: >0.7)
   - Hit Rate@5:   0.94 ✅ (target: >0.9)

2. PERFORMANCE
   - Avg Latency:  3,200 ms ✅ (target: <5,000 ms)
   - P95 Latency:  4,800 ms ✅
   - P99 Latency:  5,500 ms

3. USER EXPERIENCE (from database)
   - Total Queries:  1,247
   - Avg Rating:     4.3/5.0 ✅
   - Rating ≥4:      78%

4. LATENCY BREAKDOWN
   - Embedding:      150 ms (4.7%)
   - Vector Search:   80 ms (2.5%)
   - Reranking:      450 ms (14.1%)
   - Generation:   2,520 ms (78.7%)
```

---

## ⚠️ LƯU Ý

1. **Hệ thống phải đang chạy**: Docker Compose phải up
2. **Database accessible**: PostgreSQL port 5432 mở
3. **API reachable**: Query-service port 8002 hoạt động
4. **Không ảnh hưởng production**: Scripts chỉ READ, không WRITE

---

## 🔧 TROUBLESHOOTING

### Lỗi: Connection refused
```bash
# Check services đang chạy
docker ps

# Start services
docker compose up -d
```

### Lỗi: Database connection failed
```bash
# Check PostgreSQL
docker exec -it legalrag-postgres-1 psql -U postgres -d legalrag

# Update config.json với credentials đúng
```

### Lỗi: No data in query_logs
- Chạy vài queries trên frontend trước
- Hoặc dùng test data mẫu
