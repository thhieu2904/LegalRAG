# 🚀 Hướng dẫn khởi động nhanh LegalRAG

## Khởi động với Conda

```bash
# 1. Kích hoạt conda environment
conda activate your-env-name

# 2. Di chuyển vào backend
cd backend

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. Tạo file .env
cp .env.example .env

# 5. Khởi động server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Test API

```bash
# Health check
curl http://localhost:8000/api/health

# Query example
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Thủ tục đăng ký khai sinh cần giấy tờ gì?"}'
```

## Web Interface

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

- **Model download**: First run will download ~4.9GB PhoGPT model
- **Memory**: Need 8GB+ RAM
- **Port**: Default 8000, change in .env if needed
