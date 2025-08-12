# Test Suite

Thư mục này chứa tất cả các test cases và integration tests của hệ thống.

## Test Categories

### API Tests

- `test_api.py` - Test các endpoint API
- `final_system_test.py` - Integration test toàn hệ thống
- `quick_test.py` - Test nhanh các chức năng cơ bản

### Component Tests

- `test_content_aware.py` - Test content-aware processor
- `test_improvements.py` - Test các cải tiến
- `test_json_system.py` - Test JSON processing system
- `test_json_system_fixed.py` - Test JSON system với fixes

### Search Tests

- `test_search_comprehensive.py` - Test tìm kiếm toàn diện
- `test_search_optimized.py` - Test tìm kiếm tối ưu
- `test_search_thresholds.py` - Test ngưỡng tìm kiếm

## Cách chạy Tests

### Chạy tất cả tests:

```bash
pytest tests/
```

### Chạy test cụ thể:

```bash
python tests/test_api.py
python tests/quick_test.py
```

### Integration test:

```bash
python tests/final_system_test.py
```

## Test Requirements

- Đảm bảo hệ thống đã được khởi tạo
- Models đã được download
- Vector database đã có data
- API server đang chạy (cho API tests)

## CI/CD

Trong production pipeline, chạy:

```bash
pytest tests/test_api.py tests/final_system_test.py
```

## Coverage

Để check test coverage:

```bash
pytest --cov=app tests/
```
