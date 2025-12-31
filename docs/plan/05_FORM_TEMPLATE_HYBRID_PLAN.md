# Form Template Hybrid System - Implementation Plan (Simplified)

> **Mục tiêu**: Backend detect + suggest, Frontend/Admin quyết định, System execute

## 📋 Overview

### Philosophy

- **Backend đơn giản**: Chỉ detect patterns, tạo template, fill data
- **Frontend xử lý logic**: Preview, chọn fields, merge paragraphs, edge cases
- **Tái sử dụng code hiện có**: `scan_xxx`, `form_xxx` pattern đã hoạt động tốt

### ✅ Đã có sẵn (KHÔNG CẦN THAY ĐỔI)

| Component           | Location                                     | Purpose                                       |
| ------------------- | -------------------------------------------- | --------------------------------------------- |
| `FormRenderer`      | `form-service/src/services/form_renderer.py` | DOCX → HTML với placeholders                  |
| `FormFiller`        | `form-service/src/services/form_filler.py`   | Fill `{{scan_xxx}}`, `{{form_xxx}}`           |
| `CCCDScanner`       | `form-service/src/services/cccd_scanner.py`  | Extract → `scan_ho_ten`, `scan_ngay_sinh`,... |
| `POST /render`      | `form-service/main.py`                       | API render template                           |
| `POST /fill`        | `form-service/main.py`                       | API fill template                             |
| `user_forms.py`     | `admin-service/src/routers/`                 | List/download/delete filled forms             |
| `form_templates.py` | `admin-service/src/routers/`                 | analyze/create/get fields                     |

---

## 🔄 Workflow (Simplified)

### Admin Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Frontend: Upload DOCX (lưu memory/state)                    │
│         ↓                                                        │
│  2. Frontend: Call /analyze → nhận detected_fields              │
│         ↓                                                        │
│  3. Frontend: Render preview (mammoth.js) + show fields         │
│         ↓                                                        │
│  4. Frontend: Admin chọn/sửa/merge/bỏ fields (JS handling)      │
│         ↓                                                        │
│  5. Frontend: Confirm → gửi file + confirmed_fields             │
│         ↓                                                        │
│  6. Backend: /create → chèn {{placeholders}} → lưu MinIO        │
│         ↓                                                        │
│  7. Admin: Lưu template_path vào DB (endpoint đã có)            │
└─────────────────────────────────────────────────────────────────┘
```

### User Fill Flow (đã có sẵn)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Query → Lấy form template_path từ DB                        │
│         ↓                                                        │
│  2. POST /render → DOCX → HTML với {{scan_xxx}}, {{form_xxx}}   │
│         ↓                                                        │
│  3. Frontend: Hiển thị form, auto-fill từ CCCD scan             │
│         ↓                                                        │
│  4. POST /fill → data → filled DOCX với dot-padding             │
│         ↓                                                        │
│  5. Download/Save to MinIO                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Files Cần Thay Đổi (Minimal)

```
form-service/src/services/
├── form_filler.py         # [UPDATE] MIN_DOTS = 1, keep_dots option
└── template_processor.py  # [KEEP] Đã có, chỉ cần verify

admin-service/src/routers/
└── form_templates.py      # [KEEP] Đã đủ: analyze, create, get fields
```

---

## ✅ TODO Tasks (Backend ~15 phút)

### Task 1: Update MIN_DOTS = 1 ⭐

- **File**: `form-service/src/services/form_filler.py`
- **Line 32**: `MIN_PADDING_DOTS = 6` → `MIN_PADDING_DOTS = 1`
- **Reason**: Chỉ cần 1 dot để giữ format
- **Effort**: 2 min

### Task 2: Add keep_dots option (Optional)

- **File**: `form-service/src/services/form_filler.py`
- **Change**: Add parameter để bỏ dots hoàn toàn nếu cần
- **Effort**: 10 min

### Task 3: Frontend xử lý merge paragraphs

- **Location**: Frontend code (React/Vue)
- **Logic**:
  - Admin select nhiều detected fields
  - Click "Merge" → Frontend gộp thành 1 field với combined paragraph_indices
  - Gửi confirmed_fields với merged info
- **Backend không cần endpoint mới**: Chỉ cần xử lý `paragraph_indices` array

### Task 4: Verify placeholder naming convention

- **Current**: `{{ho_ten}}`, `{{ngay_sinh}}`
- **Existing**: `{{scan_ho_ten}}`, `{{form_nghe_nghiep}}`
- **Decision**: Giữ prefix `scan_`/`form_` hay bỏ?
  - `scan_xxx` = Auto-fill từ CCCD
  - `form_xxx` = User nhập tay
  - Plain = Generic

---

## 📊 Effort Estimation (Thực tế)

| Task              | Effort   | Priority |
| ----------------- | -------- | -------- |
| MIN_DOTS = 1      | 2 min    | ⭐ HIGH  |
| keep_dots option  | 10 min   | MEDIUM   |
| Frontend merge UI | Frontend | MEDIUM   |
| Verify naming     | 5 min    | LOW      |

**Backend thực tế: ~15 phút**

---

## 🧪 Verified Test Cases

Từ `test_edge_cases.py` - **8/8 passed**:

| Case                       | Result                  |
| -------------------------- | ----------------------- |
| Value ngắn hơn dots        | ✅ Giữ remaining dots   |
| Value dài hơn dots         | ✅ Value + minimum dots |
| Không có dots              | ✅ Replace trực tiếp    |
| Multiple placeholders/line | ✅ Cả 2 được fill       |
| Value rất ngắn             | ✅ Value + nhiều dots   |
| Value rỗng                 | ✅ Giữ dots             |
| Special characters         | ✅ Không bị escape      |
| Missing data               | ✅ Giữ {{placeholder}}  |

---

## ⚠️ Edge Cases → Frontend/Admin Handles

| Edge Case       | Backend          | Frontend/Admin  |
| --------------- | ---------------- | --------------- |
| Dots nhiều dòng | Detect từng line | Merge nếu cần   |
| Field sai label | Suggest name     | Edit name       |
| Thiếu field     | Return detected  | Add manual      |
| Thừa field      | Return all       | Remove unwanted |

---

## 📝 Summary

**Nguyên tắc**:

1. Backend đã có đủ logic → chỉ tinh chỉnh nhỏ (MIN_DOTS)
2. Logic phức tạp (merge, select) → Frontend xử lý
3. Tái sử dụng `scan_xxx`/`form_xxx` pattern đang hoạt động tốt
4. Không tạo endpoint thừa - dùng những gì đã có
