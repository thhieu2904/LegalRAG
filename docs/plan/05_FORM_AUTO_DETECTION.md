# FORM SERVICE - AUTO-DETECT FILLABLE FIELDS

## Vấn đề

Form templates cần chỉnh sửa thủ công để thêm `{{placeholder}}`. Không scalable khi số lượng form tăng.

## Giải pháp đã triển khai

### FormTemplateConverter Service

File: `form-service/src/services/form_template_converter.py`

**Features:**

1. ✅ Auto-detect patterns có dots (`Label: .......`)
2. ✅ Auto-detect patterns không có dots (dựa trên `FILLABLE_LABELS`)
3. ✅ Date patterns (`ngày ... tháng ... năm ...`)
4. ✅ Smart naming (`scan_xxx`, `form_xxx`, `date_xxx`)
5. ✅ Handle duplicates (\_2, \_3, etc.)

**Test Results:**

- Input: `forms gốc.docx` (Tờ khai khai sinh)
- Output: **32 fields detected** (coverage ~89%)

### Usage

```python
from src.services.form_template_converter import FormTemplateConverter

with open('form_goc.docx', 'rb') as f:
    content = f.read()

converter = FormTemplateConverter(enable_no_dots_detection=True)
result = converter.convert(content)

if result.success:
    with open('form_converted.docx', 'wb') as f:
        f.write(result.converted_doc)
    print(f"Detected {result.stats['total_fields']} fields")
```

## Hướng đi tiếp theo

### Short-term: Enhance Auto-Detection

- Mở rộng `FILLABLE_LABELS` cho nhiều loại form
- Context-aware naming (mẹ, cha differentiation)

### Medium-term: Form Schema System

- Định nghĩa schema cho từng loại form phổ biến
- Auto-match form type từ title

### Long-term: AI-Assisted

- Sử dụng LLM để identify edge cases
- Generate meaningful placeholder names

## Files

| File                                                   | Description     |
| ------------------------------------------------------ | --------------- |
| `form-service/src/services/form_template_converter.py` | Main converter  |
| `scripts/read_forms.py`                                | Analysis script |
| `scripts/test_converter.py`                            | Test script     |

## Next Steps

- [ ] Add API endpoints (`/api/form/analyze`, `/api/form/convert`)
- [ ] Expand FILLABLE_LABELS
- [ ] Context-aware naming
- [ ] Build admin UI for review
