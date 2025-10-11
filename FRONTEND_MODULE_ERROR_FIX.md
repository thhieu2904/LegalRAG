# 🔧 Frontend Module Export Error - Fix Applied

**Error**: `Uncaught SyntaxError: The requested module '/src/api/document-preview-api.ts' does not provide an export named 'DocumentPreviewResponse'`

**Root Cause**: Vite dev server module cache + TypeScript `verbatimModuleSyntax` option

---

## ✅ Fixes Applied

### **1. Changed Import Style in DocumentPreviewPage.tsx**

**Before** (Mixed import):

```typescript
import {
  getDocumentPreview,
  DocumentPreviewResponse, // Type mixed with value
} from "../api/document-preview-api";
```

**After** (Separate type import):

```typescript
import { getDocumentPreview } from "../api/document-preview-api";
import type { DocumentPreviewResponse } from "../api/document-preview-api";
```

**Why**: TypeScript `verbatimModuleSyntax` requires type-only imports to be explicit

---

### **2. Fixed TypeScript Lint Error**

**Before**:

```typescript
catch (err: any) {  // ❌ any not allowed
  setError(err.response?.data?.detail);
}
```

**After**:

```typescript
catch (err) {
  const error = err as { response?: { data?: { detail?: string } } };
  setError(error.response?.data?.detail || "Failed to load document preview");
}
```

---

### **3. Cleared Vite Cache**

```bash
docker exec legalrag-frontend-dev sh -c "rm -rf /app/node_modules/.vite"
```

**Result**: Vite dev server restarted with clean cache

---

## 🧪 Verification Steps

### **Step 1: Hard Refresh Browser**

```
Chrome/Edge: Ctrl + Shift + R
Firefox: Ctrl + F5
```

**This is CRITICAL** - Browser has cached the old module

---

### **Step 2: Check Browser Console**

Open DevTools (F12) and look for:

**✅ Success**:

```
✅ All exports loaded successfully!
```

**❌ Still Error**:

```
Uncaught SyntaxError: The requested module...
```

---

### **Step 3: If Still Error - Nuclear Option**

```bash
# Stop all containers
docker-compose -f docker-compose.dev.yml down

# Remove frontend container completely
docker rm legalrag-frontend-dev

# Rebuild frontend with no cache
docker-compose -f docker-compose.dev.yml build --no-cache frontend

# Start all services
docker-compose -f docker-compose.dev.yml up -d
```

---

## 📋 Current State

### **Files Modified**:

1. ✅ `frontend/src/pages/DocumentPreviewPage.tsx`

   - Changed to type-only import for `DocumentPreviewResponse`
   - Fixed TypeScript lint error

2. ✅ `frontend/src/api/document-preview-api.ts`

   - Already correct (exports verified)

3. ✅ Vite cache cleared

---

## 🎯 Next Steps

**After applying fixes above:**

1. **Open browser**: http://localhost:5173/admin
2. **Hard refresh**: `Ctrl + Shift + R`
3. **Navigate**: Database tab
4. **Click**: "📄 DOC" button
5. **Expected**: Preview opens in new tab ✅

---

## 🔍 If Error Persists

### **Debug Checklist**:

1. **Check Vite is running**:

```bash
docker-compose -f docker-compose.dev.yml logs frontend
# Should see: "VITE v7.1.1 ready"
```

2. **Check file exists**:

```bash
docker exec legalrag-frontend-dev ls -la /app/src/api/document-preview-api.ts
# Should exist
```

3. **Check import in browser**:

   - Open DevTools → Network tab
   - Filter: `document-preview-api`
   - Check response shows exports

4. **Check TypeScript compilation**:

```bash
docker exec legalrag-frontend-dev npm run build
# Should complete without errors
```

---

## 💡 Why This Happened

**Root Causes**:

1. **Vite HMR Cache**: Vite caches module transformations
2. **TypeScript Config**: `verbatimModuleSyntax` requires explicit type imports
3. **Browser Cache**: Browser caches module responses

**Solutions Applied**:

1. ✅ Separated type import (TypeScript requirement)
2. ✅ Cleared Vite cache (server-side)
3. ⏳ Need hard refresh (client-side) ← **YOU NEED TO DO THIS**

---

## 🚀 Quick Fix Commands

```bash
# If error persists, run these in order:

# 1. Restart frontend container
docker-compose -f docker-compose.dev.yml restart frontend

# 2. Clear Vite cache and restart
docker exec legalrag-frontend-dev sh -c "rm -rf /app/node_modules/.vite"
docker-compose -f docker-compose.dev.yml restart frontend

# 3. Nuclear option - rebuild frontend
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache frontend
docker-compose -f docker-compose.dev.yml up -d

# 4. Then in browser: Ctrl + Shift + R (hard refresh)
```

---

## ✅ Expected Result

After hard refresh, you should see:

1. **No console errors** in DevTools
2. **DOC button clickable** in Database Manager
3. **Preview page loads** when clicking DOC/JSON
4. **Content displays** correctly

---

## 📞 If Still Not Working

Let me know and I'll:

1. Check the exact error message in browser console
2. Verify frontend logs
3. Test the API endpoints directly
4. Rebuild frontend with additional debugging

---

**IMPORTANT**: **Bạn cần hard refresh browser** (`Ctrl + Shift + R`) sau khi mình đã fix code! 🔄
