# Form Template Hybrid System - Implementation Report

**Date**: December 2, 2025  
**Status**: Planning Complete, Ready for Implementation

---

## 📋 Executive Summary

**Goal**: Bổ sung form template processing vào flow hiện có, cho phép admin review và confirm fields trước khi lưu.

**Approach**:

- Form-service xử lý detect & create template
- Admin-service orchestrate workflow và lưu DB
- Frontend xử lý UI review/confirm

**Impact**: Không thay đổi flow hiện tại, chỉ bổ sung tính năng mới

---

## 🎯 Workflow Design

### Current Flow (Giữ nguyên)

```
Admin → Upload DOCX → Admin-service → MinIO → Save DB
```

### New Flow (Bổ sung)

```
Admin → Upload DOCX → Admin-service
                           ↓
                    Form-service /process-template (detect fields)
                           ↓
                    Frontend (review, confirm)
                           ↓
                    Form-service /create-template (insert placeholders)
                           ↓
                    Admin-service → MinIO → Save DB
```

---

## ✅ TODO Tasks

### Backend Tasks

#### Task 1: Update MIN_DOTS = 1 ⭐

**File**: `form-service/src/services/form_filler.py`  
**Change**: Line 32, `MIN_PADDING_DOTS = 6` → `MIN_PADDING_DOTS = 1`  
**Reason**: Chỉ cần 1 dot để giữ format  
**Effort**: 2 minutes  
**Status**: ⬜ Not Started

#### Task 2: Add /process-template endpoint

**File**: `form-service/main.py`  
**Purpose**: Detect fillable fields from uploaded DOCX  
**Input**:

```python
file: UploadFile
```

**Output**:

```python
{
    "success": True,
    "detected_fields": [
        {
            "id": "field_1",
            "label": "Họ tên",
            "suggested_name": "ho_ten",
            "field_type": "dots",
            "paragraph_index": 5,
            "confidence": 0.95
        },
        ...
    ],
    "total_fields": 15
}
```

**Implementation**: Use existing `TemplateProcessor.analyze()`  
**Effort**: 30 minutes  
**Status**: ⬜ Not Started

#### Task 3: Add /create-template endpoint

**File**: `form-service/main.py`  
**Purpose**: Create template with {{placeholders}} at confirmed positions  
**Input**:

```python
file: UploadFile  # Original DOCX
confirmed_fields: str  # JSON array
# Example: [{"paragraph_index": 5, "field_name": "ho_ten", "label": "Họ tên"}, ...]
```

**Output**:

```python
{
    "success": True,
    "template_bytes": "base64...",  # Template DOCX with placeholders
    "placeholders": ["ho_ten", "ngay_sinh", ...]
}
```

**Implementation**: Use existing `TemplateProcessor.create_template()`  
**Effort**: 30 minutes  
**Status**: ⬜ Not Started

#### Task 4: Update admin-service form upload flow

**File**: `admin-service` (forms router)  
**Changes**:

1. When admin uploads form DOCX:
   - Call form-service `/process-template`
   - Return detected fields to frontend
2. After admin confirms:
   - Call form-service `/create-template`
   - Upload result to MinIO (existing logic)
   - Save path to DB (existing logic)

**Effort**: 1 hour  
**Status**: ⬜ Not Started

---

### Frontend Tasks

#### Task 5: Form Template Review UI

**Location**: Frontend (React/Vue)  
**Features**:

1. **Preview**: Use mammoth.js to render DOCX → HTML
2. **Fields List**: Show detected fields with:
   - ☑ Checkbox to select/deselect
   - ✏️ Edit field name
   - 🔗 Merge multiple fields
3. **Actions**:
   - "Add Field" button (manual add)
   - "Confirm" button (submit confirmed_fields)

**Mock UI**:

```
┌─────────────────────────────────────────────────────────────┐
│  📄 Template Preview            │ 📝 Detected Fields        │
│  ┌───────────────────────────┐  │                           │
│  │ PHIẾU ĐĂNG KÝ              │  │ ☑ ho_ten (Họ tên)        │
│  │ Họ tên: .................  │  │ ☑ ngay_sinh (Ngày sinh)  │
│  │ Ngày sinh: ...............│  │ ☐ dia_chi (detected)     │
│  └───────────────────────────┘  │                           │
│                                  │ [+ Add Field]             │
│                                  │ [Confirm]                 │
└─────────────────────────────────────────────────────────────┘
```

**Effort**: Frontend team  
**Status**: ⬜ Not Started

---

### Testing Tasks

#### Task 6: Integration Test

**Scenario**: Full admin workflow

1. Upload hotich.docx → Detect 20 fields
2. Admin uncheck 3 fields, merge 2 fields
3. Confirm → Create template with 17 placeholders
4. Save to DB
5. User fills form → Verify works correctly

**Effort**: 30 minutes  
**Status**: ⬜ Not Started

---

## 📊 Effort Summary

| Category  | Tasks       | Estimated Effort         |
| --------- | ----------- | ------------------------ |
| Backend   | 4 tasks     | ~2 hours                 |
| Frontend  | 1 task      | Frontend team            |
| Testing   | 1 task      | 30 minutes               |
| **Total** | **6 tasks** | **~2.5 hours (backend)** |

---

## 🔧 Technical Details

### Existing Components (Reuse)

| Component                             | Location                                          | Status                          |
| ------------------------------------- | ------------------------------------------------- | ------------------------------- |
| `TemplateProcessor.analyze()`         | `form-service/src/services/template_processor.py` | ✅ Ready                        |
| `TemplateProcessor.create_template()` | `form-service/src/services/template_processor.py` | ✅ Ready                        |
| `FormFiller` with dot-padding         | `form-service/src/services/form_filler.py`        | ✅ Ready (need MIN_DOTS update) |
| Admin upload to MinIO                 | `admin-service`                                   | ✅ Ready                        |
| Admin save to DB                      | `admin-service`                                   | ✅ Ready                        |

### New Endpoints

**form-service**:

```
POST /process-template  → Detect fields
POST /create-template   → Insert placeholders
```

**admin-service**:

- No new endpoints needed
- Update existing form upload flow to call form-service

---

## 🧪 Test Results

### Unit Tests (Already Passed)

From `scripts/test_edge_cases.py`:

- ✅ 8/8 edge cases passed
- ✅ Dot-padding logic verified
- ✅ Value overflow handled correctly

### Integration Tests (Pending)

From `scripts/hybrid_template_processor.py`:

- ✅ Template detection works (20 fields from hotich.docx)
- ✅ Template creation works (21 placeholders)
- ⏳ Full workflow needs testing after implementation

---

## 📝 Implementation Priority

```
Priority 1 (Must Have):
  1. Task 1: MIN_DOTS = 1
  2. Task 2: /process-template endpoint
  3. Task 3: /create-template endpoint
  4. Task 4: Admin-service integration

Priority 2 (Should Have):
  5. Task 5: Frontend UI

Priority 3 (Nice to Have):
  6. Task 6: Integration tests
```

---

## 🎯 Success Criteria

- [ ] Admin có thể upload DOCX và xem detected fields
- [ ] Admin có thể chọn/bỏ/merge fields
- [ ] System tạo template với {{placeholders}} đúng vị trí
- [ ] Template được lưu MinIO và DB như bình thường
- [ ] User có thể fill template và download filled DOCX
- [ ] Dot-padding hoạt động đúng (1 dot minimum)

---

## ⚠️ Notes

1. **Không thay đổi flow hiện tại**: Bổ sung thêm option, không bắt buộc
2. **Frontend flexibility**: Admin có thể skip detect và upload trực tiếp nếu muốn
3. **Backward compatible**: Templates cũ vẫn hoạt động bình thường
4. **scan_xxx vs plain**: Giữ nguyên convention hiện tại

---

## 📅 Next Steps

1. **Review TODO list** với team
2. **Implement Task 1-4** (backend, ~2 hours)
3. **Frontend implement Task 5** (parallel)
4. **Test Task 6** khi có UI
5. **Deploy và monitor**

---

**Report End**
