# 📋 Phân Tích Chi Tiết - Vấn Đề 1 & 2

## Vấn Đề 1: Hai Nút Download Dupli

### Hiện Tại:

```
✅ IntegratedFormPage.tsx
   └─ handleDownloadFilledForm()
      └─ Gọi: POST /api/v1/forms/fill-and-download/{collectionId}/{docId}

⚠️ FormRenderer.tsx (DUPLICATE - MỚI TẠO)
   └─ handleDownloadForm()
      └─ Gọi: useFormDownload hook
         └─ Fetch RAG + Save to storage + Browser download
```

### Vấn Đề:

- 2 nút download gây confuse UX
- Nút cũ (IntegratedFormPage) không lưu vào storage
- Nút mới (FormRenderer) là feature mới nhưng bị duplicate

### Giải Pháp Đề Xuất:

**Giữ nút cũ, tích hợp chức năng mới:**

```typescript
// IntegratedFormPage.tsx - handleDownloadFilledForm() được cập nhật:
const handleDownloadFilledForm = async () => {
  // 1. Kiểm tra nếu có scan_cccd (user đã quét)
  if (cccdData?.scan_cccd) {
    // 2. Gọi useFormDownload hook để:
    //    - Fetch form từ RAG
    //    - Save vào storage (admin thấy được)
    //    - Trigger browser download
    await downloadForm(
      formPath,
      cccdData.scan_cccd,
      cccdData.scan_ho_ten,
      formFilename.replace(".docx", ""),
      formFilename
    );
  } else {
    // Fallback: Download không lưu storage (nếu user chỉ điền không quét)
    // Giữ logic cũ
  }
};
```

### Files Cần Xóa:

- ❌ `frontend/src/components/forms/FormRenderer.tsx` - Xóa download button + handler
- ✅ Giữ `useFormDownload` hook (để dùng trong IntegratedFormPage)
- ✅ Giữ `storage-api.ts` service

---

## Vấn Đề 2: Admin Quản Lý Saved Forms

### Hiện Tại:

```
❌ Admin Panel KHÔNG có section quản lý saved forms
   Current sections:
   - Dashboard
   - Voice
   - Bộ thủ tục (Collections/Documents)
   - Câu hỏi (Questions)
   - Hệ thống (System)

❌ Admin API KHÔNG có endpoints cho saved forms:
   - Không lấy danh sách CCCD
   - Không lấy danh sách form per CCCD
   - Không download form đã lưu
```

### Backend Status:

```
✅ identifill_service CÓ database + filesystem:
   - SQLite: stored_forms table (form_id, scan_cccd, filename, file_size, ...)
   - Filesystem: data/scanned_documents/{CCCD}/forms/{filename}.docx

✅ API endpoints (Identifill):
   - POST /api/v1/storage/save (save form)
   - GET /api/v1/storage/list/{scan_cccd} (list per CCCD)
   - GET /api/v1/storage/download/{scan_cccd}/{file_id} (download)
   - DELETE /api/v1/storage/delete/{scan_cccd}/{file_id} (delete)
   - GET /api/v1/storage/stats (statistics)

❌ Admin Service KHÔNG expose endpoints:
   - Không proxy/forward storage endpoints
   - Không có storage_management.py API router
```

### Giải Pháp:

#### BƯỚC 1: Backend - Admin Service

**Tạo:** `admin_service/app/api/storage_management.py`

```python
# Endpoints:
- GET /api/v1/storage/all → Danh sách tất cả CCCD + form counts
- GET /api/v1/storage/cccd/{scan_cccd} → Chi tiết CCCD + list forms
- GET /api/v1/storage/form/{scan_cccd}/{filename} → Download form
- GET /api/v1/storage/stats → Thống kê tổng
```

**Cập nhật:** `admin_service/main.py`

```python
# Include router
from app.api import storage_management
app.include_router(storage_management.router)
```

#### BƯỚC 2: Frontend - Admin API Service

**Cập nhật:** `frontend/src/api/admin-api.ts`

```typescript
// Add new interfaces:
-StoredFormInfo -
  StoredCCCDInfo -
  StorageStats -
  // Add new functions:
  fetchStorageStats() -
  fetchAllStoredForms() -
  fetchFormsBycccd(scan_cccd) -
  downloadStoredForm(scan_cccd, filename);
```

#### BƯỚC 3: Frontend - UI Component

**Tạo:** `frontend/src/components/admin/StorageManager.tsx`

```typescript
// Component structure (tương tự DatabaseManager):

View 1: Danh sách CCCD Users
├─ Table with columns:
│  ├─ CCCD
│  ├─ Tên người dùng
│  ├─ Số form
│  ├─ Dung lượng
│  └─ Actions (View)

View 2: Chi tiết form per CCCD
├─ Filter by form name (Khai_sinh, Hóa_đơn, etc)
├─ Table with columns:
│  ├─ Tên form
│  ├─ Dung lượng
│  ├─ Ngày tải
│  ├─ Lần cập nhật
│  └─ Actions (View, Download, Delete)

View 3: Form Preview (optional)
├─ Display form PDF/HTML
├─ Download button
```

#### BƯỚC 4: Admin Page

**Cập nhật:** `frontend/src/pages/AdminPage.tsx`

```typescript
// Add new section:
navigationItems.push({
  key: "storage" as AdminSection,
  label: "Quản lý Form",
  icon: "📁"
})

// Add case in renderActiveComponent:
case "storage":
  return <StorageManager />;
```

---

## Roadmap Chi Tiết

### Phase 1: Fix Frontend (Today)

1. ✏️ Cập nhật IntegratedFormPage.tsx:

   - Import useFormDownload hook
   - Kiểm tra scan_cccd trong handleDownloadFilledForm
   - Nếu có → gọi downloadForm hook (auto-save)
   - Nếu không → keep old behavior (no save)

2. ❌ Xóa duplicate:
   - Loại bỏ download button khỏi FormRenderer.tsx
   - Giữ useFormDownload hook

### Phase 2: Backend Storage API (Admin Service)

1. ✅ Tạo `storage_management.py` router
2. ✅ Include router trong main.py
3. ✅ Test endpoints với Postman/curl

### Phase 3: Frontend Admin API Service

1. ✅ Cập nhật admin-api.ts với storage functions
2. ✅ Add TypeScript interfaces

### Phase 4: Frontend UI Component

1. ✅ Tạo StorageManager.tsx component
2. ✅ Add vào AdminPage navigation
3. ✅ Style theo DatabaseManager pattern
4. ✅ Test end-to-end

---

## Code Examples

### IntegratedFormPage.tsx - Updated handleDownloadFilledForm

```typescript
import { useFormDownload } from "../hooks/useFormDownload";

const handleDownloadFilledForm = async () => {
  if (!collectionId || !docId || !formFilename) {
    alert("Thông tin form không đầy đủ");
    return;
  }

  const { downloadForm: saveAndDownloadForm } = useFormDownload();
  const finalData = getFinalData();

  setIsDownloading(true);
  try {
    // Nếu user đã quét CCCD -> Save + Download
    if (cccdData?.scan_cccd) {
      console.log("📥 Saving form to storage...");
      await saveAndDownloadForm(
        `${collectionId}/${docId}/${formFilename}`,
        cccdData.scan_cccd,
        cccdData.scan_ho_ten || "Unknown User",
        formFilename.replace(".docx", ""),
        formFilename
      );
      return; // Done - hook handles download
    }

    // Fallback: Download không lưu (nếu chỉ điền không quét)
    const response = await fetch(
      `http://localhost:8002/api/v1/forms/fill-and-download/${collectionId}/${docId}`,
      {
        method: "POST",
        body: JSON.stringify({ ...finalData, template_name: formFilename }),
      }
    );
    // ... rest of old code
  } finally {
    setIsDownloading(false);
  }
};
```

### StorageManager.tsx Structure

```typescript
export default function StorageManager() {
  const [view, setView] = useState<"list" | "detail">("list");
  const [selectedCCCD, setSelectedCCCD] = useState<string | null>(null);
  const [storedForms, setStoredForms] = useState<StoredFormInfo[]>([]);
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [loading, setLoading] = useState(false);

  // Load data functions...

  return view === "list" ? (
    <div className="storage-list">{/* CCCD Users List */}</div>
  ) : (
    <div className="storage-detail">{/* Forms per CCCD */}</div>
  );
}
```

---

## Summary

| Vấn Đề                      | Status     | Action                                        |
| --------------------------- | ---------- | --------------------------------------------- |
| 2 nút download              | ⚠️ Dupli   | Keep old, integrate new in IntegratedFormPage |
| Admin không see saved forms | ❌ Missing | Build StorageManager UI + backend APIs        |
| API support                 | ⚠️ Partial | Identifill có, Admin cần expose               |
| Frontend API wrapper        | ❌ Missing | Update admin-api.ts                           |
| UI component                | ❌ Missing | Create StorageManager.tsx                     |
