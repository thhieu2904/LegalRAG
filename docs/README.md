# Documentation

Thư mục này chứa tất cả tài liệu hướng dẫn và documentation của dự án LegalRAG.

## Tài liệu có sẵn

### Quick Start Guides

- `QUICKSTART.md` - Hướng dẫn khởi động nhanh phiên bản cũ
- `QUICKSTART_NEW.md` - Hướng dẫn khởi động nhanh phiên bản mới

### Development Notes

- `IMPROVEMENTS_SUMMARY.md` - Tóm tắt các cải tiến và thay đổi

## Tài liệu chính

Tài liệu chính của dự án nằm ở file `README.md` trong thư mục gốc.

## Cấu trúc hướng dẫn

1. **Setup**: Xem `../README.md` cho hướng dẫn cài đặt chi tiết
2. **Quick Start**: Sử dụng `QUICKSTART_NEW.md` cho bản mới nhất
3. **API**: Truy cập http://localhost:8000/docs khi server đang chạy
4. **Scripts**: Xem `../backend/scripts/README.md` cho các utilities
5. **Tools**: Xem `../backend/tools/README.md` cho development tools

## Production Deployment

Trong môi trường production:

```bash
cd backend
python main.py
```

hoặc

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Ghi chú

- Luôn đọc `../README.md` trước
- Kiểm tra requirements và dependencies
- Đảm bảo cấu hình môi trường đúng
