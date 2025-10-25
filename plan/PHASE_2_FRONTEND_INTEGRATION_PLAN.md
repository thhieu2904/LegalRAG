# 🎨 Phase 2: Frontend Integration - Comprehensive Plan

**Date:** October 25, 2025  
**Objective:** Integrate form storage with React frontend (Simplified auto-save on download)

---

## 🎯 Phase 2 Overview

### Main Feature

- **Auto-Save on Download**: When user clicks "Download Form" button, file automatically saves to storage + downloads to browser
- **No separate "Save" button** - Simpler UX
- **Admin can later retrieve/manage** saved forms via API

---

## 📊 Phase 2 Task Breakdown

### 2.1 Create React Hook for Form Download

**File:** `frontend/src/hooks/useFormDownload.ts`

- Function: `downloadFormWithAutoSave()`
- Logic:
  1. Fetch form from RAG service
  2. POST to storage API (`/api/v1/storage/save`)
  3. Trigger browser download
  4. Show success notification

### 2.2 Create Storage Service Client

**File:** `frontend/src/api/storage-api.ts`

- Function: `saveFormToStorage()`
- Function: `listSavedForms()`
- Function: `downloadSavedForm()`
- Function: `deleteSavedForm()`
- Function: `getStorageStats()`

### 2.3 Update Form Component

**File:** `frontend/src/components/FormViewer.tsx`

- Add "Download Form" button (single button)
- Call `useFormDownload` hook
- Show loading state
- Show success/error notifications

### 2.4 Create Forms Management Dashboard (Optional)

**File:** `frontend/src/components/FormManagement.tsx`

- List saved forms for current CCCD
- Show storage statistics
- Delete saved forms
- Download previously saved forms

### 2.5 Create Notifications

**File:** `frontend/src/components/StorageNotification.tsx`

- Success: "Form downloaded and saved successfully!"
- Error: "Failed to save form"
- Info: "Saving form..."

---

## 🔧 Technical Details

### Step 1: Create useFormDownload Hook

```typescript
// frontend/src/hooks/useFormDownload.ts

import { useState } from "react";
import { ragAPI } from "@/api/axios-config";
import { storageAPI } from "@/api/storage-api";

export function useFormDownload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadForm = async (
    formPath: string,
    cccd: string,
    userName: string,
    formName: string,
    fileName: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      // Step 1: Get form content from RAG service
      console.log("📥 Downloading form from RAG service...");
      const formResponse = await ragAPI.get(`/forms/file/${formPath}`, {
        responseType: "blob",
      });
      const formContent = formResponse.data;

      // Step 2: Save to storage API
      console.log("💾 Saving to storage...");
      const formData = new FormData();
      formData.append("form_file", formContent, fileName);
      formData.append("scan_cccd", cccd);
      formData.append("scan_ho_ten", userName);
      formData.append("form_name", formName);

      const saveResponse = await storageAPI.post("/save", formData);

      console.log("✅ Form saved:", saveResponse.data);

      // Step 3: Trigger browser download
      console.log("📥 Triggering browser download...");
      const url = window.URL.createObjectURL(formContent);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);

      return {
        success: true,
        fileId: saveResponse.data.file_id,
        fileName: saveResponse.data.file_name,
      };
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || err.message;
      setError(errorMsg);
      console.error("❌ Error:", errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { downloadForm, loading, error };
}
```

### Step 2: Create Storage API Service

```typescript
// frontend/src/api/storage-api.ts

import axios from "axios";

export const storageAPI = axios.create({
  baseURL: "http://localhost:8002/api/v1/storage",
});

// Interceptor for logging
storageAPI.interceptors.response.use(
  (response) => {
    console.log(`✅ Storage API Success: ${response.status}`);
    return response;
  },
  (error) => {
    console.error(`❌ Storage API Error: ${error.response?.status}`);
    return Promise.reject(error);
  }
);

export async function saveFormToStorage(
  formFile: Blob,
  cccd: string,
  userName: string,
  formName: string,
  fileName: string
) {
  const formData = new FormData();
  formData.append("form_file", formFile, fileName);
  formData.append("scan_cccd", cccd);
  formData.append("scan_ho_ten", userName);
  formData.append("form_name", formName);

  return storageAPI.post("/save", formData);
}

export async function listSavedForms(cccd: string) {
  return storageAPI.get(`/list/${cccd}`);
}

export async function downloadSavedForm(cccd: string, fileName: string) {
  return storageAPI.get(`/download/${cccd}/${fileName}`, {
    responseType: "blob",
  });
}

export async function deleteSavedForm(
  cccd: string,
  fileId: string,
  fileName: string
) {
  return storageAPI.delete(`/delete/${cccd}/${fileId}/${fileName}`);
}

export async function getStorageStats() {
  return storageAPI.get("/stats");
}
```

### Step 3: Update Form Component

```typescript
// frontend/src/components/FormViewer.tsx

import { useFormDownload } from "@/hooks/useFormDownload";
import { useState } from "react";

export function FormViewer({
  formPath,
  cccd,
  userName,
  formName,
  htmlContent,
}: FormViewerProps) {
  const { downloadForm, loading, error } = useFormDownload();
  const [notification, setNotification] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const handleDownload = async () => {
    try {
      setNotification({
        type: "info",
        message: "Saving and downloading form...",
      });

      const fileName = `${formName}_${new Date().getTime()}.docx`;
      await downloadForm(formPath, cccd, userName, formName, fileName);

      setNotification({
        type: "success",
        message: "✅ Form downloaded and saved successfully!",
      });
    } catch (err) {
      setNotification({
        type: "error",
        message: "❌ Failed to download form. Please try again.",
      });
    }
  };

  return (
    <div className="form-viewer">
      {notification && (
        <div className={`notification notification-${notification.type}`}>
          {notification.message}
        </div>
      )}

      <div className="form-header">
        <h2>📄 {formName}</h2>
        <div className="user-info">
          <p>CCCD: {cccd}</p>
          <p>Họ tên: {userName}</p>
        </div>
      </div>

      <div
        className="form-content"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />

      <div className="form-actions">
        <button
          className="btn btn-primary"
          onClick={handleDownload}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span> Downloading...
            </>
          ) : (
            <>📥 Download Form</>
          )}
        </button>
      </div>
    </div>
  );
}
```

---

## 📋 Implementation Checklist

### Phase 2.1: Setup & Hooks

- [ ] Create `frontend/src/hooks/useFormDownload.ts`
- [ ] Create `frontend/src/api/storage-api.ts`
- [ ] Update `frontend/src/api/axios-config.ts` (add storageAPI export)

### Phase 2.2: Components

- [ ] Update `frontend/src/components/FormViewer.tsx`
- [ ] Add Download button
- [ ] Add notification system
- [ ] Add loading states

### Phase 2.3: Styling

- [ ] Add CSS for download button
- [ ] Add CSS for notifications
- [ ] Responsive design

### Phase 2.4: Testing

- [ ] Test with real form (Khai_sinh.docx)
- [ ] Verify file saves to backend
- [ ] Verify browser download works
- [ ] Verify notifications show correctly

### Phase 2.5: Optional - Dashboard

- [ ] Create `frontend/src/components/FormManagement.tsx`
- [ ] List saved forms
- [ ] Show storage stats
- [ ] Delete forms

---

## 📁 Files to Create/Modify

### NEW FILES:

```
frontend/src/
├── hooks/
│   └── useFormDownload.ts (NEW)
├── api/
│   └── storage-api.ts (NEW)
└── components/
    └── FormManagement.tsx (OPTIONAL)
```

### MODIFIED FILES:

```
frontend/src/
├── api/
│   └── axios-config.ts (update exports)
└── components/
    └── FormViewer.tsx (update with download button)
```

---

## 🔗 API Integration Points

### Backend Endpoints Used:

```
✅ POST /api/v1/storage/save
   └─ Called when user downloads form

✅ GET /api/v1/storage/list/{scan_cccd}
   └─ For dashboard (optional)

✅ GET /api/v1/storage/download/{scan_cccd}/{file_name}
   └─ For dashboard (optional)

✅ DELETE /api/v1/storage/delete/{scan_cccd}/{file_id}/{file_name}
   └─ For dashboard (optional)

✅ GET /api/v1/storage/stats
   └─ For dashboard (optional)
```

---

## 🎨 UI/UX Changes

### Before (Current)

```
[Form Display]
- Form HTML rendered
- No download option
- No storage integration
```

### After (Phase 2)

```
┌─────────────────────────────────────┐
│ Form Display                        │
├─────────────────────────────────────┤
│ 📄 Khai_sinh                        │
│ CCCD: 079123456789                  │
│ Họ tên: Nguyễn Văn A                │
│                                     │
│ [Form Content HTML]                 │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📥 Download Form                │ │ ← NEW BUTTON
│ └─────────────────────────────────┘ │
│                                     │
│ ✅ Form saved and downloaded!       │ ← NOTIFICATION
└─────────────────────────────────────┘
```

---

## 🧪 Testing Strategy

### Unit Tests

- [ ] `useFormDownload` hook
- [ ] Storage API functions

### Integration Tests

- [ ] Download button flow
- [ ] API communication
- [ ] File download trigger

### End-to-End Tests

- [ ] User downloads form
- [ ] Form appears in storage
- [ ] Admin can retrieve it

---

## ⏱️ Estimated Timeline

| Task              | Estimated Time |
| ----------------- | -------------- |
| Setup & Hooks     | 30 min         |
| Components        | 45 min         |
| Styling           | 30 min         |
| Testing           | 45 min         |
| **Total Phase 2** | **2.5 hours**  |

---

## 🚀 Next Actions

1. **Immediate**: Create hook and API service
2. **Then**: Update form component
3. **Then**: Add styling and notifications
4. **Finally**: Test with real forms

---

## 📝 Notes

- Backend is **100% ready** ✅
- Only frontend changes needed
- Simplified flow (no separate save button)
- Auto-save on download
- Admin can manage forms via API later
