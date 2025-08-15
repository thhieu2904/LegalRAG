# 🛠️ Scripts & Development Tools

Thư mục chứa các scripts, tests và tools hỗ trợ development.

## 📂 Cấu trúc

```
scripts/
├── tests/                  # Test scripts
│   ├── test_*.py          # Functional tests
│   └── test_query.json    # Test data
├── debug/                 # Debug utilities
│   ├── debug_*.py         # Debug scripts
│   └── simple_llm_test.py # Simple LLM test
├── phase1_summary_report.py   # Project summary
└── README.md              # This file
```

## 🧪 Tests

Các file test cho các components:

- `test_clarification_fix.py` - Test clarification system
- `test_enhanced_prompt.py` - Test prompt engineering
- `test_rag_engine.py` - Test RAG functionality
- `test_smart_router.py` - Test routing logic
- `test_frontend_integration.py` - Test frontend integration

### Chạy tests:

```bash
cd scripts/tests
python test_<component_name>.py
```

## 🐛 Debug

Các tools debug và troubleshooting:

- `debug_llm_hallucination.py` - Debug LLM hallucination
- `debug_router.py` - Debug routing issues
- `simple_llm_test.py` - Simple LLM functionality test

### Chạy debug:

```bash
cd scripts/debug
python debug_<issue_name>.py
```

## 📊 Reports

- `phase1_summary_report.py` - Tạo báo cáo tổng kết phase 1

## 💡 Usage

Để chạy bất kỳ script nào, đảm bảo đã activate virtual environment:

```bash
# Windows
..\backend\venv\Scripts\activate

# Linux/Mac
source ../backend/venv/bin/activate

# Chạy script
python scripts/tests/test_component.py
```
