# Scripts Directory

Thư mục chứa các script chính thức cho hệ thống RAG.

## Files hiện có:

### 🔧 Core Scripts

- **`rebuild.py`** - 🎯 SCRIPT CHÍNH để rebuild vector database
- **`rebuild_vectordb.py`** - Script rebuild vectordb cơ bản
- **`initialize_system.py`** - Khởi tạo hệ thống
- **`download_models.py`** - Download models cần thiết

### 🚀 Setup Scripts

- **`setup.sh`** - Setup script cho Linux/Mac
- **`setup.bat`** - Setup script cho Windows

### 📋 Documentation

- **`README.md`** - File này
- **`REBUILD_README.md`** - Hướng dẫn rebuild

## Script đã được archive:

- Các debug script và script cũ đã được di chuyển vào `../archive/old_scripts/`

## Cách sử dụng:

### Rebuild Vector Database (QUAN TRỌNG NHẤT):

```bash
# Rebuild toàn bộ database với context enhancement
python scripts/rebuild.py
```

### Download Models:

```bash
# Download các model cần thiết
python scripts/download_models.py
```

### Initialize System:

```bash
# Khởi tạo system lần đầu
python scripts/initialize_system.py
```

## Lưu ý:

- **`rebuild.py`** là script quan trọng nhất để rebuild database
- Chạy script này sau khi có thay đổi về document processing
- Đảm bảo môi trường conda được activate trước khi chạy
