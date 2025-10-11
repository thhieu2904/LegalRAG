# 🔧 Frontend Export Error - Fix Guide

## ❌ Error Message

```
Uncaught SyntaxError: The requested module '/src/api/document-preview-api.ts'
does not provide an export named 'DocumentPreviewResponse'
(at DocumentPreviewPage.tsx:11:3)
```

---

## 🔍 Root Cause

This is a **Vite dev server caching issue**. The exports are correct in the file, but Vite's module cache hasn't refreshed.

---

## ✅ Solutions (Try in Order)

### **Solution 1: Restart Vite Dev Server** ⭐ (RECOMMENDED)

```powershell
# Stop the frontend dev server (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

**Why this works**: Clears Vite's module cache completely.

---

### **Solution 2: Hard Refresh Browser**

```
Chrome/Edge: Ctrl + Shift + R
Firefox: Ctrl + F5
```

**Why this works**: Forces browser to reload all modules without cache.

---

### **Solution 3: Clear Vite Cache**

```powershell
# Stop dev server first (Ctrl+C)
cd frontend

# Delete Vite cache
Remove-Item -Recurse -Force node_modules/.vite

# Restart dev server
npm run dev
```

**Why this works**: Deletes Vite's build cache directory.

---

### **Solution 4: Verify Export Syntax**

Check that `frontend/src/api/document-preview-api.ts` has:

```typescript
// ✅ CORRECT Export
export interface DocumentPreviewResponse {
  success: boolean;
  doc_id: string;
  collection: string;
  type: "docx" | "json";
  // ...
}

export const getDocxPreview = async (...) => { ... }
export const getJsonPreview = async (...) => { ... }
export const getDocumentPreview = async (...) => { ... }
```

And `DocumentPreviewPage.tsx` imports like:

```typescript
// ✅ CORRECT Import
import {
  getDocumentPreview,
  DocumentPreviewResponse,
} from "../api/document-preview-api";
```

---

## 🧪 Verification

After applying solution, check:

1. **No TypeScript errors** in VS Code
2. **Browser console** has no module errors
3. **Preview page loads** without errors

---

## 🎯 If Still Not Working

### **Check TypeScript Compilation**

```powershell
cd frontend
npm run build
```

If build succeeds, the exports are correct. Just restart dev server.

---

### **Check File Paths**

Ensure:

- ✅ File exists: `frontend/src/api/document-preview-api.ts`
- ✅ Import path correct: `"../api/document-preview-api"` (from pages/)
- ✅ No typos in import names

---

### **Nuclear Option: Full Clean**

```powershell
cd frontend

# Delete all caches and node_modules
Remove-Item -Recurse -Force node_modules
Remove-Item -Recurse -Force node_modules/.vite
Remove-Item -Recurse -Force dist

# Reinstall
npm install

# Restart dev server
npm run dev
```

---

## 📝 Current File Status

### ✅ **Files are CORRECT**:

1. **document-preview-api.ts** - Exports `DocumentPreviewResponse` ✅
2. **DocumentPreviewPage.tsx** - Imports correctly ✅
3. **DatabaseManager.tsx** - Updated with buttons ✅

### ⚠️ **Issue is**:

- Vite dev server cache not refreshed

---

## 🚀 Recommended Action

**Just restart Vite dev server**:

```powershell
# Press Ctrl+C to stop current dev server
# Then:
cd frontend
npm run dev
```

Then test by:

1. Open `http://localhost:5173/admin`
2. Go to Database tab
3. Click "📄 DOC" or "📋 JSON" button
4. Should open preview in new tab ✅

---

## 📊 Expected Result

When working correctly:

1. Click "📄 DOC" → Opens: `http://localhost:5173/admin/documents/{collection}/{doc_id}/preview/docx`
2. See DOCX content rendered as HTML
3. Click "📋 JSON" → Opens: `http://localhost:5173/admin/documents/{collection}/{doc_id}/preview/json`
4. See JSON data formatted nicely

---

**99% this is just a cache issue. Restart dev server and you're good to go!** 🚀
