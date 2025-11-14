# 🚀 LEGALRAG IMPROVEMENT IMPLEMENTATION PLAN

## Multi-Phase Refactoring with Todo Tracking & Verification

**Status**: In Progress  
**Updated**: Oct 25, 2025  
**Objective**: Fix duplicate download buttons + Build admin storage management

---

## 📋 PHASE A: Frontend Duplication Fix (30-45 min)

### Goal: Consolidate duplicate download buttons into single integrated button

### A.1: Analyze FormRenderer.tsx Download Logic ✅

**Status**: ANALYZING

- [x] Located download button at lines 405-424
- [x] Located handleDownloadForm() at lines 318-368
- [x] Confirmed it uses useFormDownload hook ✅
- [x] Verified it saves to storage ✅

**Key Finding**: FormRenderer version is CORRECT - it:

- Uses `downloadForm()` from `useFormDownload` hook
- Saves to identifill_service storage
- Shows notifications

---

### A.2: Integrate useFormDownload into IntegratedFormPage.tsx

**Status**: READY TO IMPLEMENT
**File**: `frontend/src/pages/IntegratedFormPage.tsx`

**Changes Required**:

1. Add import for `useFormDownload` hook (line ~20)
2. Modify `handleDownloadFilledForm()` to support CONDITIONAL download:
   - IF cccdData.scan_cccd exists → use NEW flow (save + download)
   - ELSE → use OLD flow (download only)

**Code Diff**:

```typescript
// ADD IMPORT (line ~20)
+ import { useFormDownload } from "../hooks/useFormDownload";

// REPLACE handleDownloadFilledForm (lines 141-195)
  const handleDownloadFilledForm = async () => {
    if (!collectionId || !docId || !formFilename) {
      alert("Thông tin form không đầy đủ");
      return;
    }

    const finalData = getFinalData();
    const { downloadForm: saveAndDownloadForm } = useFormDownload(); // NEW

    setIsDownloading(true);
    try {
      console.log("🔄 Bắt đầu tải file Word...");

      // ✅ NEW: Check if user has CCCD data
      if (cccdData?.scan_cccd) {
        console.log("📥 User has CCCD - using save + download flow");
        await saveAndDownloadForm(
          `${collectionId}/${docId}/${formFilename}`,
          cccdData.scan_cccd,
          cccdData.scan_ho_ten || "Unknown",
          formFilename.replace('.docx', ''),
          formFilename
        );
        console.log("✅ File saved and downloaded");
        return;
      }

      // ❌ Fallback: No CCCD, use old flow (download only)
      console.log("⚠️ No CCCD data - using download-only flow");
      const response = await fetch(
        `http://localhost:8002/api/v1/forms/fill-and-download/${collectionId}/${docId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...finalData,
            template_name: formFilename,
          }),
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${formFilename}_filled.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        console.log("✅ File downloaded successfully");
      } else {
        const errorText = await response.text();
        console.error("❌ Error:", errorText);
        alert(`Lỗi tải file: ${errorText}`);
      }
    } catch (error) {
      console.error("❌ Connection error:", error);
      alert("Lỗi kết nối đến server");
    } finally {
      setIsDownloading(false);
    }
  };
```

**Todo**:

- [ ] Add import line
- [ ] Replace handleDownloadFilledForm function
- [ ] Test with CCCD scan data
- [ ] Test without CCCD (fallback)

---

### A.3: Remove Duplicate Download Button from FormRenderer.tsx

**Status**: READY TO IMPLEMENT
**File**: `frontend/src/components/forms/FormRenderer.tsx`

**Why Remove?**:

- IntegratedFormPage is the main entry point
- FormRenderer is embedded in IntegratedFormPage
- Having 2 buttons causes UX confusion
- All logic will be in parent component

**Changes Required**:

1. Remove download button JSX (lines 405-424)
2. Remove notification display (lines 390-408)
3. Remove handleDownloadForm callback (lines 318-368)
4. Remove notification state (lines 59-63)
5. KEEP useFormDownload import (might be used elsewhere)

**Code Removed**:

```typescript
// REMOVE: Lines 59-63 (notification state)
- const [notification, setNotification] = useState<{
-   type: "success" | "error" | "info";
-   message: string;
- } | null>(null);

// REMOVE: Line 57-58 (downloadLoading)
- const { downloadForm, loading: downloadLoading } = useFormDownload();
  // CHANGE TO (keep import for other uses):
+ // import { useFormDownload } from "../../hooks/useFormDownload"; // Kept for potential reuse

// REMOVE: Lines 318-368 (handleDownloadForm callback)
- const handleDownloadForm = useCallback(async () => { ... }, [...dependencies]);

// REMOVE: Lines 390-408 (Notification display JSX)
- {notification && (
-   <div className={`form-notification form-notification-${notification.type}`}>
-     <p>{notification.message}</p>
-   </div>
- )}

// REMOVE: Lines 409-429 (Download button in form header)
- {formMetadata && (
-   <div className="form-header">
-     <div className="form-header-left">...</div>
-     <div className="form-header-actions">
-       <button onClick={handleDownloadForm} disabled={downloadLoading} ...>
-         Download button
-       </button>
-     </div>
-   </div>
- )}
```

**Todo**:

- [ ] Remove notification state (lines 59-63)
- [ ] Keep useFormDownload import (for possible reuse)
- [ ] Remove downloadForm hook call (line 57-58)
- [ ] Remove handleDownloadForm function (lines 318-368)
- [ ] Remove notification display JSX (lines 390-408)
- [ ] Remove download button from form header (lines 409-429)
- [ ] Verify component still renders correctly

---

### A.4: Verification - Test Phase A

**File**: `frontend/src/pages/IntegratedFormPage.tsx`

**Test Case 1: With CCCD Data**

```bash
Steps:
1. Start frontend + services
2. Navigate to form page
3. Click QR scan button
4. Scan CCCD or use test data
5. Fill form fields
6. Click "Download" button
7. VERIFY:
   - File is downloaded to browser
   - Notification shows "✅ Biểu mẫu đã được tải xuống và lưu thành công!"
   - Form appears in admin storage later
```

**Test Case 2: Without CCCD Data**

```bash
Steps:
1. Navigate to form WITHOUT scanning CCCD
2. Fill form with manual data only
3. Click "Download" button
4. VERIFY:
   - File is downloaded (no CCCD in filename/storage)
   - Old behavior (download only, no storage save)
   - No error message
```

**Test Case 3: FormRenderer No Download Button**

```bash
Steps:
1. Inspect FormRenderer component in DevTools
2. VERIFY:
   - No download button visible
   - No notification elements
   - Form still renders correctly
   - Placeholders still work
```

**Todo**:

- [ ] Test Case 1 - With CCCD data
- [ ] Test Case 2 - Without CCCD data
- [ ] Test Case 3 - FormRenderer cleanup
- [ ] Verify no console errors
- [ ] Verify localStorage token still works

---

## 📍 PHASE B: Backend - Expose Storage API (45-60 min)

### Goal: Create admin router to expose identifill storage APIs

### B.1: Create admin_service Storage Router

**Status**: READY TO IMPLEMENT
**File**: `admin_service/app/api/storage_management.py`

**Purpose**: Bridge between frontend admin panel and identifill_service storage APIs

**Implementation**:

```python
"""
Storage Management Router for Admin Panel
- Aggregates data from identifill_service storage API
- Provides unified endpoints for admin UI
- Handles authentication/authorization
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

# Identifill service config
IDENTIFILL_BASE_URL = "http://localhost:8002"

# ✅ GET /api/v1/storage/all-cccd-users
# Returns: List of CCCD users who have saved forms
@router.get("/all-cccd-users")
async def get_all_cccd_users():
    """
    Get all CCCD users with statistics
    Response: [
      {
        "scan_cccd": "079987654321",
        "scan_ho_ten": "Nguyễn Văn A",
        "form_count": 3,
        "total_size_mb": 0.45,
        "created_at": "2025-10-25T10:30:00",
        "updated_at": "2025-10-25T15:45:00"
      }
    ]
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Get all stats from identifill
            response = await client.get(f"{IDENTIFILL_BASE_URL}/api/v1/storage/stats")
            response.raise_for_status()

            stats = response.json()
            logger.info(f"✅ Retrieved storage stats: {len(stats.get('users', []))} users")

            return stats.get('users', [])
    except httpx.HTTPError as e:
        logger.error(f"❌ Error fetching from identifill: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch storage data: {str(e)}")


# ✅ GET /api/v1/storage/cccd/{scan_cccd}
# Returns: Forms saved for specific CCCD
@router.get("/cccd/{scan_cccd}")
async def get_forms_by_cccd(scan_cccd: str):
    """
    Get all forms saved for a specific CCCD
    Response: {
      "scan_cccd": "079987654321",
      "scan_ho_ten": "Nguyễn Văn A",
      "forms": [
        {
          "filename": "Khai_sinh.docx",
          "file_size": 45600,
          "created_at": "2025-10-25T10:30:00",
          "updated_at": "2025-10-25T10:30:00"
        }
      ]
    }
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{IDENTIFILL_BASE_URL}/api/v1/storage/list/{scan_cccd}"
            )
            response.raise_for_status()

            forms = response.json()
            logger.info(f"✅ Retrieved {len(forms.get('forms', []))} forms for CCCD: {scan_cccd}")

            return forms
    except httpx.HTTPError as e:
        logger.error(f"❌ Error fetching forms for CCCD {scan_cccd}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch forms: {str(e)}")


# ✅ GET /api/v1/storage/stats
# Returns: Overall storage statistics
@router.get("/stats")
async def get_storage_stats():
    """
    Get overall storage statistics
    Response: {
      "total_users": 5,
      "total_forms": 12,
      "total_size_mb": 5.23,
      "users": [...]
    }
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{IDENTIFILL_BASE_URL}/api/v1/storage/stats"
            )
            response.raise_for_status()

            stats = response.json()
            logger.info(f"✅ Retrieved storage statistics")

            return stats
    except httpx.HTTPError as e:
        logger.error(f"❌ Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


# ✅ POST /api/v1/storage/download
# Proxies download request to identifill service
@router.post("/download")
async def download_form(scan_cccd: str = Query(...), filename: str = Query(...)):
    """
    Download a form from storage
    Query params:
    - scan_cccd: User CCCD
    - filename: Form filename
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{IDENTIFILL_BASE_URL}/api/v1/storage/download/{scan_cccd}/{filename}",
                follow_redirects=True
            )
            response.raise_for_status()

            logger.info(f"✅ Downloaded form: {filename} for CCCD: {scan_cccd}")

            return {
                "success": True,
                "filename": filename,
                "size": len(response.content)
            }
    except httpx.HTTPError as e:
        logger.error(f"❌ Error downloading form: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download: {str(e)}")


# ✅ DELETE /api/v1/storage/delete
# Deletes a saved form
@router.delete("/delete")
async def delete_form(scan_cccd: str = Query(...), filename: str = Query(...)):
    """
    Delete a saved form
    Query params:
    - scan_cccd: User CCCD
    - filename: Form filename
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{IDENTIFILL_BASE_URL}/api/v1/storage/delete/{scan_cccd}/{filename}"
            )
            response.raise_for_status()

            logger.info(f"✅ Deleted form: {filename} for CCCD: {scan_cccd}")

            return {
                "success": True,
                "message": f"Form {filename} deleted successfully"
            }
    except httpx.HTTPError as e:
        logger.error(f"❌ Error deleting form: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")
```

**Todo**:

- [ ] Create `admin_service/app/api/storage_management.py` file
- [ ] Add all 5 router functions
- [ ] Add proper error handling
- [ ] Add logging with emojis
- [ ] Add docstrings

---

### B.2: Register Storage Router in Admin Service

**Status**: READY TO IMPLEMENT
**File**: `admin_service/main.py`

**Current Code** (line ~30-40):

```python
from app.api import (
    collections,
    documents,
    questions,
    json_documents,
    analytics,
)

app.include_router(collections.router)
app.include_router(documents.router)
app.include_router(questions.router)
app.include_router(json_documents.router)
app.include_router(analytics.router)
```

**Updated Code**:

```python
from app.api import (
    collections,
    documents,
    questions,
    json_documents,
    analytics,
    storage_management,  # NEW
)

app.include_router(collections.router)
app.include_router(documents.router)
app.include_router(questions.router)
app.include_router(json_documents.router)
app.include_router(analytics.router)
app.include_router(storage_management.router)  # NEW
```

**Todo**:

- [ ] Add import for storage_management
- [ ] Add app.include_router() call
- [ ] Verify no syntax errors

---

### B.3: Verification - Test Phase B

**Status**: READY TO TEST

**Test B.1: Storage Stats Endpoint**

```bash
curl -X GET http://localhost:8001/api/v1/storage/stats
# Expected: { "total_users": X, "total_forms": Y, ... }
```

**Test B.2: Get All CCCD Users**

```bash
curl -X GET http://localhost:8001/api/v1/storage/all-cccd-users
# Expected: [{ "scan_cccd": "...", "form_count": X, ... }]
```

**Test B.3: Get Forms by CCCD**

```bash
curl -X GET http://localhost:8001/api/v1/storage/cccd/079987654321
# Expected: { "forms": [{ "filename": "...", "file_size": X, ... }] }
```

**Test B.4: Error Handling**

```bash
curl -X GET http://localhost:8001/api/v1/storage/cccd/INVALID
# Expected: Error response (identifill returns 404, admin returns 500)
```

**Todo**:

- [ ] Start admin_service: `python main.py`
- [ ] Test all 5 endpoints with curl
- [ ] Verify response formats match expectations
- [ ] Check console logs for errors
- [ ] Verify identifill_service is running on port 8002

---

## 📊 PHASE C: Frontend API Service (20-30 min)

### Goal: Add storage functions to admin API wrapper

### C.1: Update admin-api.ts with Storage Functions

**Status**: READY TO IMPLEMENT
**File**: `frontend/src/api/admin-api.ts`

**Add at end of file (before export statements)**:

```typescript
// ✅ Storage Management APIs (NEW - Oct 25, 2025)

export interface StoredFormInfo {
  filename: string;
  file_size: number;
  created_at: string;
  updated_at: string;
}

export interface StoredCCCDInfo {
  scan_cccd: string;
  scan_ho_ten: string;
  form_count?: number;
  total_size_mb?: number;
  created_at?: string;
  updated_at?: string;
}

export interface StorageStats {
  total_users: number;
  total_forms: number;
  total_size_mb: number;
  users: StoredCCCDInfo[];
}

export interface FormsBycccdResponse {
  scan_cccd: string;
  scan_ho_ten: string;
  forms: StoredFormInfo[];
}

/**
 * Get all CCCD users with storage statistics
 * @returns List of users who have saved forms
 */
export async function fetchAllStoredUsers(): Promise<StoredCCCDInfo[]> {
  try {
    console.log("📥 Fetching all stored users...");
    const response = await adminAPI.get<{ data: StoredCCCDInfo[] }>(
      "/storage/all-cccd-users"
    );
    console.log(`✅ Retrieved ${response.data.data?.length || 0} users`);
    return response.data.data || [];
  } catch (error) {
    console.error("❌ Error fetching users:", error);
    throw error;
  }
}

/**
 * Get storage statistics
 * @returns Overall storage stats
 */
export async function fetchStorageStats(): Promise<StorageStats> {
  try {
    console.log("📊 Fetching storage statistics...");
    const response = await adminAPI.get<StorageStats>("/storage/stats");
    console.log("✅ Retrieved storage stats");
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching stats:", error);
    throw error;
  }
}

/**
 * Get forms saved for specific CCCD
 * @param scan_cccd CCCD number
 * @returns Forms for this CCCD
 */
export async function fetchFormsByCCCD(
  scan_cccd: string
): Promise<FormsBycccdResponse> {
  try {
    console.log(`📋 Fetching forms for CCCD: ${scan_cccd}...`);
    const response = await adminAPI.get<FormsBycccdResponse>(
      `/storage/cccd/${scan_cccd}`
    );
    console.log(
      `✅ Retrieved ${
        response.data.forms?.length || 0
      } forms for CCCD: ${scan_cccd}`
    );
    return response.data;
  } catch (error) {
    console.error(`❌ Error fetching forms for CCCD ${scan_cccd}:`, error);
    throw error;
  }
}

/**
 * Download a saved form from storage
 * @param scan_cccd CCCD number
 * @param filename Form filename
 */
export async function downloadStoredForm(
  scan_cccd: string,
  filename: string
): Promise<Blob> {
  try {
    console.log(`⬇️ Downloading form: ${filename} for CCCD: ${scan_cccd}...`);
    const response = await adminAPI.post(
      "/storage/download",
      {},
      {
        params: { scan_cccd, filename },
        responseType: "blob",
      }
    );
    console.log(`✅ Downloaded form: ${filename}`);
    return response.data;
  } catch (error) {
    console.error(`❌ Error downloading form ${filename}:`, error);
    throw error;
  }
}

/**
 * Delete a saved form
 * @param scan_cccd CCCD number
 * @param filename Form filename
 */
export async function deleteStoredForm(
  scan_cccd: string,
  filename: string
): Promise<{ success: boolean; message: string }> {
  try {
    console.log(`🗑️ Deleting form: ${filename} for CCCD: ${scan_cccd}...`);
    const response = await adminAPI.delete("/storage/delete", {
      params: { scan_cccd, filename },
    });
    console.log(`✅ Deleted form: ${filename}`);
    return response.data;
  } catch (error) {
    console.error(`❌ Error deleting form ${filename}:`, error);
    throw error;
  }
}
```

**Todo**:

- [ ] Open `frontend/src/api/admin-api.ts`
- [ ] Add interfaces at end
- [ ] Add 5 new functions
- [ ] Verify imports are correct
- [ ] Save file

---

## 🎨 PHASE D: Frontend UI Component (1-1.5 hours)

### Goal: Build StorageManager component and integrate into AdminPage

### D.1: Create StorageManager Component Structure

**Status**: READY TO IMPLEMENT
**Path**: `frontend/src/components/admin/StorageManager.tsx`

**Component Architecture**:

```
StorageManager (Main Container)
├─ State: view ('list' | 'detail')
├─ State: selectedCCCD
├─ State: storedUsers
├─ State: loading, error
│
├─ View 1: StorageList (All CCCD users)
│  ├─ Table: CCCD | Name | # Forms | Size | Actions
│  ├─ Search by CCCD
│  ├─ Click row → switch to View 2
│  └─ Sorting/pagination
│
├─ View 2: StorageDetail (Forms per CCCD)
│  ├─ Back button
│  ├─ Table: Name | Size | Date | Updated | Actions (Download/Delete)
│  ├─ Filter by form name
│  ├─ Delete confirmation modal
│  └─ Download handler
│
└─ Error Handling
   ├─ Connection errors
   ├─ Retry button
   └─ Empty state messages
```

**Implementation**:

```typescript
/**
 * Storage Manager - Admin Panel Component
 * Allows viewing and managing saved forms by CCCD users
 * Features: List users, view forms per user, download/delete, statistics
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  fetchAllStoredUsers,
  fetchStorageStats,
  fetchFormsByCCCD,
  downloadStoredForm,
  deleteStoredForm,
  type StoredCCCDInfo,
  type FormsBycccdResponse,
  type StorageStats,
} from "../../api/admin-api";
import "./StorageManager.css";
import {
  Download,
  Trash2,
  ArrowLeft,
  RefreshCw,
  Search,
  AlertCircle,
} from "lucide-react";

type ViewType = "list" | "detail";

interface DeleteConfirmation {
  show: boolean;
  filename?: string;
  cccd?: string;
}

export const StorageManager: React.FC = () => {
  // State management
  const [view, setView] = useState<ViewType>("list");
  const [selectedCCCD, setSelectedCCCD] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  // Data states
  const [storedUsers, setStoredUsers] = useState<StoredCCCDInfo[]>([]);
  const [formsBycccd, setFormsBycccd] = useState<FormsBycccdResponse | null>(
    null
  );
  const [stats, setStats] = useState<StorageStats | null>(null);

  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmation>({
    show: false,
  });

  // Load initial data on mount
  useEffect(() => {
    loadUsersList();
  }, []);

  // Load all users
  const loadUsersList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("📊 Loading storage users...");
      const users = await fetchAllStoredUsers();
      const statsData = await fetchStorageStats();
      setStoredUsers(users);
      setStats(statsData);
      console.log(`✅ Loaded ${users.length} users`);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to load storage data";
      setError(errorMsg);
      console.error("❌ Error loading users:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load forms for specific CCCD
  const loadFormsBycccd = useCallback(async (cccd: string) => {
    setLoading(true);
    setError(null);
    try {
      console.log(`📋 Loading forms for CCCD: ${cccd}...`);
      const forms = await fetchFormsByCCCD(cccd);
      setFormsBycccd(forms);
      setSelectedCCCD(cccd);
      setView("detail");
      setSearchTerm("");
      console.log(`✅ Loaded ${forms.forms.length} forms`);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to load forms";
      setError(errorMsg);
      console.error("❌ Error loading forms:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Download form
  const handleDownloadForm = useCallback(
    async (cccd: string, filename: string) => {
      setDownloadingFile(filename);
      try {
        console.log(`⬇️ Downloading ${filename}...`);
        const blob = await downloadStoredForm(cccd, filename);

        // Trigger browser download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        console.log(`✅ Downloaded: ${filename}`);
      } catch (err) {
        console.error("❌ Download error:", err);
        setError(
          err instanceof Error ? err.message : "Failed to download form"
        );
      } finally {
        setDownloadingFile(null);
      }
    },
    []
  );

  // Delete form with confirmation
  const handleDeleteForm = useCallback(
    async (cccd: string, filename: string) => {
      setDeleteConfirm({ show: true, cccd, filename });
    },
    []
  );

  // Confirm deletion
  const confirmDelete = useCallback(async () => {
    if (!deleteConfirm.cccd || !deleteConfirm.filename) return;

    try {
      console.log(
        `🗑️ Deleting ${deleteConfirm.filename} for CCCD ${deleteConfirm.cccd}...`
      );
      await deleteStoredForm(deleteConfirm.cccd, deleteConfirm.filename);

      // Refresh forms list
      if (selectedCCCD) {
        await loadFormsBycccd(selectedCCCD);
      }

      setDeleteConfirm({ show: false });
      console.log("✅ Form deleted successfully");
    } catch (err) {
      console.error("❌ Delete error:", err);
      setError(err instanceof Error ? err.message : "Failed to delete form");
    }
  }, [deleteConfirm, selectedCCCD, loadFormsBycccd]);

  // Go back to users list
  const handleBackToList = useCallback(() => {
    setView("list");
    setSelectedCCCD(null);
    setFormsBycccd(null);
    setSearchTerm("");
  }, []);

  // Filtered forms based on search
  const filteredForms = formsBycccd?.forms.filter((form) =>
    form.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="storage-manager">
      {/* Error notification */}
      {error && (
        <div className="storage-error">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="error-close"
            aria-label="Close error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Statistics Bar */}
      {stats && view === "list" && (
        <div className="storage-stats">
          <div className="stat-item">
            <span className="stat-label">👥 Người dùng</span>
            <span className="stat-value">{stats.total_users}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">📄 Tổng form</span>
            <span className="stat-value">{stats.total_forms}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">💾 Dung lượng</span>
            <span className="stat-value">
              {stats.total_size_mb.toFixed(2)} MB
            </span>
          </div>
        </div>
      )}

      {/* View 1: Users List */}
      {view === "list" && (
        <div className="storage-view-users">
          <div className="view-header">
            <h2>📁 Quản lý Form Lưu trữ</h2>
            <button
              onClick={loadUsersList}
              className="refresh-button"
              disabled={loading}
              title="Làm mới dữ liệu"
            >
              <RefreshCw size={18} />
            </button>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Đang tải dữ liệu...</p>
            </div>
          ) : storedUsers.length === 0 ? (
            <div className="empty-state">
              <p>📭 Chưa có form được lưu trữ</p>
            </div>
          ) : (
            <div className="users-table-wrapper">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>CCCD</th>
                    <th>Họ tên</th>
                    <th className="text-center"># Form</th>
                    <th className="text-right">Dung lượng</th>
                    <th className="text-center">Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {storedUsers.map((user) => (
                    <tr key={user.scan_cccd} className="user-row">
                      <td className="cccd-cell">{user.scan_cccd}</td>
                      <td className="name-cell">{user.scan_ho_ten}</td>
                      <td className="count-cell text-center">
                        {user.form_count || 0}
                      </td>
                      <td className="size-cell text-right">
                        {(user.total_size_mb || 0).toFixed(2)} MB
                      </td>
                      <td className="action-cell text-center">
                        <button
                          onClick={() => loadFormsBycccd(user.scan_cccd)}
                          className="view-button"
                          title="Xem form"
                        >
                          👁️ Xem
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* View 2: Forms Detail */}
      {view === "detail" && formsBycccd && (
        <div className="storage-view-detail">
          <div className="view-header">
            <button onClick={handleBackToList} className="back-button">
              <ArrowLeft size={18} /> Quay lại
            </button>
            <h2>
              📋 Form của {formsBycccd.scan_ho_ten} ({formsBycccd.scan_cccd})
            </h2>
            <button
              onClick={() => loadFormsBycccd(formsBycccd.scan_cccd)}
              className="refresh-button"
              disabled={loading}
            >
              <RefreshCw size={18} />
            </button>
          </div>

          {/* Search filter */}
          <div className="search-box">
            <Search size={18} />
            <input
              type="text"
              placeholder="Tìm kiếm form..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Đang tải form...</p>
            </div>
          ) : filteredForms && filteredForms.length === 0 ? (
            <div className="empty-state">
              <p>📭 Chưa có form nào</p>
            </div>
          ) : (
            <div className="forms-table-wrapper">
              <table className="forms-table">
                <thead>
                  <tr>
                    <th>Tên form</th>
                    <th className="text-right">Dung lượng</th>
                    <th>Ngày tạo</th>
                    <th>Cập nhật</th>
                    <th className="text-center">Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredForms?.map((form) => (
                    <tr key={form.filename} className="form-row">
                      <td className="name-cell">{form.filename}</td>
                      <td className="size-cell text-right">
                        {(form.file_size / 1024).toFixed(2)} KB
                      </td>
                      <td className="date-cell">
                        {new Date(form.created_at).toLocaleDateString("vi-VN")}
                      </td>
                      <td className="date-cell">
                        {new Date(form.updated_at).toLocaleDateString("vi-VN")}
                      </td>
                      <td className="action-cell text-center">
                        <button
                          onClick={() =>
                            handleDownloadForm(
                              formsBycccd.scan_cccd,
                              form.filename
                            )
                          }
                          disabled={downloadingFile === form.filename}
                          className="download-button"
                          title="Tải xuống"
                        >
                          <Download size={16} />
                          {downloadingFile === form.filename ? "..." : "Tải"}
                        </button>
                        <button
                          onClick={() =>
                            handleDeleteForm(
                              formsBycccd.scan_cccd,
                              form.filename
                            )
                          }
                          className="delete-button"
                          title="Xóa"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm.show && (
        <div
          className="modal-overlay"
          onClick={() => setDeleteConfirm({ show: false })}
        >
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>⚠️ Xác nhận xóa</h3>
            <p>
              Bạn có chắc chắn muốn xóa form:{" "}
              <strong>{deleteConfirm.filename}</strong>?
            </p>
            <div className="modal-actions">
              <button
                onClick={() => setDeleteConfirm({ show: false })}
                className="modal-cancel"
              >
                Hủy
              </button>
              <button onClick={confirmDelete} className="modal-confirm">
                Xóa
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

**Todo**:

- [ ] Create file `frontend/src/components/admin/StorageManager.tsx`
- [ ] Add full component code
- [ ] Verify no TypeScript errors
- [ ] Import lucide-react icons

---

### D.2: Create StorageManager.css Styling

**Status**: READY TO IMPLEMENT
**File**: `frontend/src/components/admin/StorageManager.css`

**Content**:

```css
/* Storage Manager Styles */

.storage-manager {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  min-height: 500px;
}

/* Error notification */
.storage-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  font-size: 14px;
}

.error-close {
  margin-left: auto;
  background: none;
  border: none;
  color: #c33;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  line-height: 1;
}

/* Statistics bar */
.storage-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  background: white;
  padding: 16px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

/* View headers */
.view-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0;
  font-size: 18px;
  flex: 1;
}

.back-button,
.refresh-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.back-button:hover,
.refresh-button:hover {
  background: #f0f0f0;
}

.back-button:disabled,
.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Search box */
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
}

/* Loading state */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px 24px;
  color: #666;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top-color: #0066cc;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px 24px;
  background: white;
  border-radius: 6px;
  color: #999;
}

/* Tables */
.users-table-wrapper,
.forms-table-wrapper {
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.users-table,
.forms-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.users-table thead,
.forms-table thead {
  background: #f8f9fa;
  border-bottom: 2px solid #e9ecef;
}

.users-table th,
.forms-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.users-table tbody tr,
.forms-table tbody tr {
  border-bottom: 1px solid #e9ecef;
  transition: background 0.2s;
}

.users-table tbody tr:hover,
.forms-table tbody tr:hover {
  background: #f8f9fa;
}

.users-table td,
.forms-table td {
  padding: 12px 16px;
  color: #666;
}

.cccd-cell {
  font-family: monospace;
  font-weight: 500;
  color: #333;
}

.name-cell {
  font-weight: 500;
}

.count-cell {
  font-weight: 600;
  color: #0066cc;
}

.size-cell {
  color: #999;
  font-size: 12px;
}

.date-cell {
  font-size: 12px;
  color: #999;
}

.action-cell {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* Buttons */
.view-button,
.download-button,
.delete-button {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.view-button:hover {
  background: #e3f2fd;
  border-color: #0066cc;
  color: #0066cc;
}

.download-button:hover:not(:disabled) {
  background: #e8f5e9;
  border-color: #4caf50;
  color: #2e7d32;
}

.download-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.delete-button:hover {
  background: #ffebee;
  border-color: #f44336;
  color: #c62828;
}

/* Text alignment utilities */
.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  padding: 24px;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-dialog h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.modal-dialog p {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.modal-cancel,
.modal-confirm {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.modal-cancel:hover {
  background: #f0f0f0;
}

.modal-confirm {
  background: #f44336;
  color: white;
  border-color: #f44336;
}

.modal-confirm:hover {
  background: #d32f2f;
}

/* Responsive */
@media (max-width: 768px) {
  .storage-stats {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }

  .view-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .users-table,
  .forms-table {
    font-size: 12px;
  }

  .users-table th,
  .forms-table th,
  .users-table td,
  .forms-table td {
    padding: 8px 12px;
  }

  .modal-dialog {
    max-width: 90%;
    margin: 16px;
  }
}
```

**Todo**:

- [ ] Create file `frontend/src/components/admin/StorageManager.css`
- [ ] Add all CSS styles
- [ ] Save file

---

### D.3: Update AdminPage to Include Storage Section

**Status**: READY TO IMPLEMENT
**File**: `frontend/src/pages/AdminPage.tsx`

**Current Navigation Structure** (line ~30-50):

```typescript
// Add import
import StorageManager from "../components/admin/StorageManager"; // NEW

// Add to navigation items (line ~...)
const navigationItems = [
  { key: "dashboard", label: "📊 Dashboard", icon: "📊" },
  { key: "voice", label: "🎤 Voice", icon: "🎤" },
  { key: "database", label: "💾 Database", icon: "💾" },
  { key: "questions", label: "❓ Questions", icon: "❓" },
  { key: "storage", label: "📁 Quản lý Form", icon: "📁" }, // NEW
  { key: "system", label: "⚙️ System", icon: "⚙️" },
];

// Add case in switch (line ~...)
const renderActiveComponent = () => {
  switch (activeSection) {
    case "dashboard":
      return <Dashboard />;
    case "voice":
      return <Voice />;
    case "database":
      return <Database />;
    case "questions":
      return <Questions />;
    case "storage": // NEW
      return <StorageManager />; // NEW
    case "system":
      return <System />;
    default:
      return <Dashboard />;
  }
};
```

**Todo**:

- [ ] Add import for StorageManager
- [ ] Add storage section to navigationItems
- [ ] Add storage case in renderActiveComponent
- [ ] Test navigation
- [ ] Verify component loads without errors

---

### D.4: Verification - Test Phase D

**Status**: READY TO TEST

**Test D.1: StorageManager Component Loads**

```bash
Steps:
1. Start frontend: cd frontend && npm run dev
2. Navigate to admin panel
3. Click "📁 Quản lý Form" button
4. VERIFY:
   - Component loads without errors
   - Shows statistics (users, forms, storage)
   - Shows table of CCCD users
```

**Test D.2: View Users List**

```bash
Steps:
1. Admin panel → Storage section
2. VERIFY:
   - Table shows all users with CCCD
   - Displays form count per user
   - Displays storage size per user
   - Search/filter works
```

**Test D.3: View Forms per CCCD**

```bash
Steps:
1. Click "👁️ Xem" button next to a user
2. VERIFY:
   - Shows forms for that CCCD
   - Back button returns to list
   - Filter box searches by form name
   - Table shows filename, size, created/updated dates
```

**Test D.4: Download Form from Storage**

```bash
Steps:
1. In forms detail view, click "⬇️ Tải" button
2. VERIFY:
   - File downloads to browser
   - File is correctly named
   - File opens correctly in Word
```

**Test D.5: Delete Form with Confirmation**

```bash
Steps:
1. Click "🗑️" button next to a form
2. VERIFY:
   - Confirmation modal appears
   - Shows form filename
   - Can click Cancel or Delete
   - After delete, form list updates
```

**Todo**:

- [ ] Test D.1 - Component loads
- [ ] Test D.2 - Users list displays
- [ ] Test D.3 - Forms per CCCD
- [ ] Test D.4 - Download functionality
- [ ] Test D.5 - Delete functionality
- [ ] Verify no console errors
- [ ] Check error handling (try invalid CCCD)

---

## ✅ FINAL VERIFICATION CHECKLIST

### Phase A Complete: Frontend Consolidation

- [ ] IntegratedFormPage has conditional download logic
- [ ] FormRenderer download button removed
- [ ] FormRenderer notification state removed
- [ ] All imports correct
- [ ] No TypeScript errors
- [ ] Download works with CCCD
- [ ] Download works without CCCD
- [ ] No console errors

### Phase B Complete: Backend Router

- [ ] storage_management.py created
- [ ] All 5 endpoints implemented
- [ ] Registered in admin_service main.py
- [ ] Service starts without errors
- [ ] All endpoints respond correctly
- [ ] Error handling works

### Phase C Complete: API Wrapper

- [ ] All interfaces added
- [ ] All 5 functions implemented
- [ ] Proper error handling
- [ ] Logging with emojis
- [ ] TypeScript types correct
- [ ] No import errors

### Phase D Complete: UI Component

- [ ] StorageManager.tsx created
- [ ] StorageManager.css created
- [ ] AdminPage updated with navigation
- [ ] Component loads in admin panel
- [ ] All views working (list, detail)
- [ ] Download/delete/search working
- [ ] No console errors
- [ ] Responsive design works

---

## 📝 SUMMARY

| Phase     | Component              | Status | Effort | Priority |
| --------- | ---------------------- | ------ | ------ | -------- |
| **A**     | Frontend Consolidation | Ready  | 45 min | High     |
| **B**     | Backend Storage Router | Ready  | 45 min | High     |
| **C**     | API Wrapper            | Ready  | 20 min | High     |
| **D**     | UI Component           | Ready  | 90 min | High     |
| **Total** | All Improvements       | Ready  | ~3.5h  | Complete |

---

## 🚀 NEXT STEPS

1. **Start Phase A**: Update IntegratedFormPage, remove FormRenderer download
2. **Test Phase A**: Verify download logic with/without CCCD
3. **Start Phase B**: Create storage_management.py, register in main.py
4. **Test Phase B**: Curl test all endpoints
5. **Start Phase C**: Add storage functions to admin-api.ts
6. **Start Phase D**: Create StorageManager component
7. **Test Phase D**: Test all UI functionality
8. **Integration Test**: Full E2E flow from form download → admin view → download
9. **Deployment**: Commit, push, deploy

---

## ⏰ Timeline Estimate

- **Phase A**: 30-45 minutes (with testing)
- **Phase B**: 40-50 minutes (with testing)
- **Phase C**: 15-20 minutes
- **Phase D**: 1-1.5 hours (with testing)
- **Integration & Final Test**: 30-45 minutes

**Total: ~3-4 hours** for complete implementation

---

**Ready to begin implementation! 🚀**
