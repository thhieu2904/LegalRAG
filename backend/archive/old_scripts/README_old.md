# Scripts Utilities

Thư mục này chứa các script tiện ích để quản lý và vận hành hệ thống LegalRAG.

## Danh sách Scripts

### Setup & Initialization

- `initialize_system.py` - Khởi tạo hệ thống lần đầu
- `setup.bat` - Script setup cho Windows
- `setup.sh` - Script setup cho Linux/macOS
- `download_models.py` - Tải xuống models cần thiết

### Database Management

- `rebuild.py` - Rebuild toàn bộ vector database
- `rebuild_vectordb.py` - Rebuild vector database cơ bản
- `rebuild_optimized_vectordb.py` - Rebuild với tối ưu hóa

## Cách sử dụng

### Khởi tạo hệ thống lần đầu:

```bash
python scripts/initialize_system.py
```

### Setup môi trường:

```bash
# Windows
scripts/setup.bat

# Linux/macOS
bash scripts/setup.sh
```

### Rebuild database:

```bash
python scripts/rebuild.py
```

## Lưu ý

- Chạy scripts từ thư mục `backend/` (không phải trong thư mục scripts)
- Đảm bảo đã activate conda environment trước khi chạy
- Kiểm tra file `.env` đã được cấu hình đúng

## Production Usage

Trong môi trường production, chỉ cần sử dụng:

```bash
python main.py
# hoặc
uvicorn main:app --host 0.0.0.0 --port 8000
```

Các scripts này chỉ dành cho development và maintenance.
