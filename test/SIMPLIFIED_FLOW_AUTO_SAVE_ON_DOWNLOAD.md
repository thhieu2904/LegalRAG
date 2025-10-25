# 📝 Form Storage Flow - Simplified (Auto-Save on Download)

## 🎯 Tổng Quan - Simplified Flow

**File được lưu TỰ ĐỘNG KHI người dùng ấn "Download Form"**

- ❌ Không có nút "Save" riêng biệt
- ✅ Chỉ có nút "Download"
- ✅ Khi download → tự động lưu vào storage
- ✅ Admin có thể tra cứu sau này

---

## 🔄 Simplified Flow: Download → Auto-Save

### 1️⃣ **Người Dùng Quét CCCD & Xem Form**

```
Frontend:
├─ User scans CCCD → Get scan_cccd, scan_ho_ten
├─ Fetch form from RAG: GET /api/forms/file/.../Khai_sinh.docx
├─ Display form as HTML/PDF
└─ Show only 2 buttons:
   ├─ ✏️ Edit Form (fill data)
   └─ 📥 Download Form (NEW ACTION - save + download)
```

### 2️⃣ **Người Dùng Ấn "📥 Download Form"** ← KEY MOMENT

```
Frontend Action:
├─ Get form file from RAG service
├─ Send to backend with:
│  ├─ form_file (binary data)
│  ├─ scan_cccd
│  ├─ scan_ho_ten
│  └─ form_name
└─ Simultaneously:
   ├─ Save to storage (backend) ← AUTOMATIC
   └─ Download to browser ← AUTOMATIC
```

### 3️⃣ **Backend: Save + Return File**

```
POST /api/v1/storage/save (Auto-triggered)
├─ Save file to: data/scanned_documents/{CCCD}/forms/
├─ Save metadata to: SQLite database
└─ Return: file_id, file_name

Then:
├─ Browser downloads file automatically
└─ User sees: ✅ "Downloaded successfully"
```

---

## 📊 Comparison: Old vs New Flow

### ❌ OLD Flow (Too Complex - DISCARDED)

```
1. User views form
2. User clicks "Save Form" button → Saves to storage
3. Later: User clicks "Download" → Downloads from storage
Problem: 2 steps, extra button, user confusion
```

### ✅ NEW Flow (Simple - RECOMMENDED)

```
1. User views form
2. User clicks "Download Form" button → Saves + Downloads automatically
Benefit: 1 step, simpler, automatic saving
```

---

## 🔑 Key Architecture Changes

### Frontend Components (Phase 2)

```typescript
// OLD - NOT USED
❌ <button onClick={saveForm}>💾 Save Form</button>

// NEW - SIMPLE
✅ <button onClick={downloadForm}>📥 Download Form</button>

async function downloadForm() {
  // 1. Get form from RAG service
  const formContent = await getFormFromRAG(formPath);

  // 2. Send to storage API (auto-save)
  const response = await fetch('http://localhost:8002/api/v1/storage/save', {
    method: 'POST',
    body: formData  // includes form_file, scan_cccd, etc.
  });

  const result = await response.json();

  // 3. Download file to browser
  downloadFile(formContent, result.file_name);

  // User now has file locally + saved in storage for later admin access
}
```

### Backend Endpoints (Already Ready)

```
✅ POST /api/v1/storage/save
   └─ Triggered by Download button
   └─ Saves file + metadata
   └─ Returns file_id and file_name

✅ GET /api/v1/storage/list/{scan_cccd}
   └─ For admin dashboard to view saved forms

✅ DELETE /api/v1/storage/delete/{scan_cccd}/{file_id}/{file_name}
   └─ For admin to manage/delete forms
```

---

## 💾 Data Flow Diagram

```
User Scans CCCD
    ↓
Views Khai_sinh.docx
    ↓
Clicks "📥 Download"
    ↓
┌─────────────────────────────────────┐
│ AUTOMATIC SAVE + DOWNLOAD           │
├─────────────────────────────────────┤
│ 1. Get form from RAG service        │
│    GET /api/forms/file/...          │
│                                      │
│ 2. Save to Storage (AUTOMATIC)      │
│    POST /api/v1/storage/save        │
│    └─ data/scanned_documents/...    │
│    └─ legalrag.db entry             │
│                                      │
│ 3. Download to Browser (AUTOMATIC)  │
│    └─ Khai_sinh_20251025_124533.docx│
└─────────────────────────────────────┘
    ↓
User sees file downloaded
+ File also saved in backend storage
+ Admin can retrieve anytime
```

---

## 📋 Implementation Checklist (Phase 2)

### Frontend Components to Create

- [ ] Form Display Component

  - Display form as HTML/PDF
  - Show user data (CCCD, name)
  - Show Edit & Download buttons

- [ ] Download Handler
  ```typescript
  async downloadForm(formPath, cccd, userName, formType) {
    // Get from RAG
    const formData = await fetchFromRAG(formPath);

    // Auto-save via storage API
    const saveResponse = await saveToStorage({
      form_file: formData,
      scan_cccd: cccd,
      scan_ho_ten: userName,
      form_name: formType
    });

    // Download to browser
    triggerBrowserDownload(formData, fileName);
  }
  ```

### Backend (Already Complete ✅)

- ✅ POST /api/v1/storage/save - Ready
- ✅ GET /api/v1/storage/list - Ready
- ✅ DELETE /api/v1/storage/delete - Ready
- ✅ GET /api/v1/storage/stats - Ready
- ✅ Database & File Storage - Ready

---

## 🎯 User Experience

### Before (What User Sees)

```
1. Scan CCCD
2. View Form
3. Edit Form
4. Click "Save Form" → "Form saved"
5. Click "Download" → File downloads
```

### After (Simplified)

```
1. Scan CCCD
2. View Form
3. Edit Form (optional)
4. Click "Download Form" → File downloads + auto-saved in backend
```

---

## 🔐 Admin Panel (Future)

Later, admin can:

```
GET /api/v1/storage/list/{scan_cccd}
└─ See all forms user downloaded/saved

GET /api/v1/storage/download/{scan_cccd}/{file_name}
└─ Download form to verify

DELETE /api/v1/storage/delete/{scan_cccd}/{file_id}/{file_name}
└─ Delete if needed

GET /api/v1/storage/stats
└─ View storage statistics
```

---

## 🚀 Summary

| Aspect                      | Status                                 |
| --------------------------- | -------------------------------------- |
| **Backend Ready?**          | ✅ YES - All 5 endpoints               |
| **Auto-save Logic**         | ✅ Already implemented                 |
| **Frontend Implementation** | ⏳ Phase 2                             |
| **Complexity**              | ✅ SIMPLIFIED - No extra "Save" button |
| **Admin Management**        | ✅ Can query/delete via API            |

---

## ✅ Benefits of This Simplified Approach

1. **Simpler UI** - One button instead of two
2. **Automatic** - No user confusion about when/where to save
3. **Consistent** - Every download automatically saves
4. **Admin-friendly** - All downloads tracked in database
5. **Audit Trail** - Admin can see when/what was saved
6. **No Duplicate Logic** - Save and download happen together
