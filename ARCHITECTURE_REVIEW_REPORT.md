# 🚨 ARCHITECTURE REVIEW REPORT - DOCUMENT PREVIEW IMPLEMENTATION

**Date**: October 11, 2025  
**Reviewer**: AI Assistant  
**Status**: ⚠️ **CRITICAL ARCHITECTURE VIOLATION DETECTED**

---

## 🎯 Executive Summary

**PROBLEM IDENTIFIED**: Rendering logic (mammoth) đặt sai service!

### Current Implementation (❌ WRONG):

```
Frontend → Admin Service → RAG Service (render DOCX→HTML with mammoth) → Admin Service → Frontend
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      ❌ WRONG LAYER!
```

### Should Be (✅ CORRECT):

```
Frontend → Admin Service (render DOCX→HTML with mammoth) → RAG Service (serve raw file) → Admin Service → Frontend
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^
                         ✅ Presentation Layer              ✅ Data Layer
```

---

## 📋 Detailed Findings

### 1️⃣ **Mammoth Placement Analysis**

#### ❌ Current State - RAG Service (WRONG)

**File**: `rag_service/app/api/internal_documents.py`

```python
import mammoth  # ❌ Should NOT be here!

async def render_docx_to_html(docx_path: Path) -> str:
    """Convert DOCX file to HTML using mammoth"""
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)  # ❌ Wrong service!
        return result.value
```

**File**: `rag_service/requirements.txt`

```
mammoth==1.6.0  # ❌ Should NOT be here!
```

**Why This Is Wrong:**

- RAG Service = Data Layer (should only handle storage/retrieval)
- Rendering = Presentation Logic (belongs to Admin Service)
- Violates Single Responsibility Principle
- Makes RAG Service dependent on rendering library

---

#### ✅ Should Be - Admin Service (CORRECT)

**File**: `admin_service/requirements.txt`

```
mammoth==1.6.0  # ✅ Already here (good!)
```

**What's Missing**: Implementation in Admin Service to:

1. Call RAG Service to get RAW DOCX bytes
2. Render DOCX→HTML locally with mammoth
3. Return HTML to Frontend

---

### 2️⃣ **Service Responsibilities**

| Service           | Current (Wrong)              | Should Be (Correct)        |
| ----------------- | ---------------------------- | -------------------------- |
| **RAG Service**   | ❌ Serve files + Render HTML | ✅ Serve raw files only    |
| **Admin Service** | ❌ Proxy rendered HTML       | ✅ Get files + Render HTML |
| **Mammoth**       | ❌ In RAG Service            | ✅ In Admin Service        |

---

### 3️⃣ **Code Locations**

#### Files Using Mammoth (WRONG):

1. **`rag_service/app/api/internal_documents.py`** (Line 15)

   ```python
   import mammoth  # ❌ REMOVE THIS
   ```

2. **`rag_service/app/api/internal_documents.py`** (Lines 133-155)

   ```python
   async def render_docx_to_html(docx_path: Path) -> str:
       # ❌ REMOVE THIS ENTIRE FUNCTION
       result = mammoth.convert_to_html(docx_file)
   ```

3. **`rag_service/requirements.txt`** (Line 87)
   ```
   mammoth==1.6.0  # ❌ REMOVE THIS LINE
   ```

#### Files That Should Use Mammoth (MISSING):

1. **`admin_service/app/services/document_renderer.py`**

   - ❌ Currently DELETED (was removed earlier)
   - ✅ Should RECREATE with RAG API integration

2. **`admin_service/requirements.txt`** (Line 17)
   - ✅ Already has `mammoth==1.6.0` (KEEP THIS)

---

### 4️⃣ **Comparison with IdentiFill Service**

**IdentiFill Service** already does this CORRECTLY:

**File**: `identifill_service/app/services/forms/form_renderer.py`

```python
import mammoth  # ✅ Presentation layer service uses mammoth

class FormRenderingService:
    def render_form_to_html(self):
        # 1. Get DOCX from RAG Service via HTTP
        response = await client.get(f"{rag_url}/api/forms/file/...")
        docx_bytes = response.content

        # 2. Render locally with mammoth
        result = mammoth.convert_to_html(BytesIO(docx_bytes))
        return result.value
```

**Why This Works:**

- IdentiFill = Presentation service → Uses mammoth ✅
- RAG Service = Data service → Serves raw files ✅
- Clear separation of concerns ✅

---

## 🔧 Required Changes

### **Phase 1: Fix RAG Service (Remove Rendering)**

#### Change 1.1: Update `internal_documents.py`

**Remove mammoth, return RAW bytes instead**

```python
# BEFORE (❌ Wrong)
import mammoth
async def render_docx_to_html(docx_path: Path) -> str:
    result = mammoth.convert_to_html(docx_file)
    return result.value

# AFTER (✅ Correct)
async def get_docx_bytes(docx_path: Path) -> bytes:
    async with aiofiles.open(docx_path, 'rb') as f:
        return await f.read()
```

#### Change 1.2: Update Response Model

```python
# BEFORE (❌ Wrong)
class DocumentContentResponse(BaseModel):
    content_type: str  # "html" or "json"
    content: Any  # HTML string or JSON object

# AFTER (✅ Correct)
class DocumentFileResponse(BaseModel):
    content_type: str  # "docx" or "json"
    content: bytes | dict  # Raw bytes or JSON data
    filename: str
```

#### Change 1.3: Remove from requirements.txt

```diff
# rag_service/requirements.txt
- mammoth==1.6.0
```

---

### **Phase 2: Fix Admin Service (Add Rendering)**

#### Change 2.1: Recreate `document_renderer.py`

**File**: `admin_service/app/services/document_renderer.py` (NEW)

```python
import mammoth
from io import BytesIO

class DocumentRenderer:
    def __init__(self, rag_client):
        self.rag_client = rag_client

    async def render_docx_to_html(self, collection: str, doc_id: str) -> str:
        # 1. Get raw DOCX from RAG Service
        response = await self.rag_client.get_document_file(
            collection=collection,
            doc_id=doc_id,
            file_type="docx"
        )
        docx_bytes = response["content"]

        # 2. Render locally with mammoth
        result = mammoth.convert_to_html(BytesIO(docx_bytes))
        return result.value
```

#### Change 2.2: Update `rag_client.py`

```python
async def get_document_file(
    self,
    collection: str,
    doc_id: str,
    file_type: str  # "docx" or "json"
) -> Dict[str, Any]:
    """Get RAW file content from RAG Service"""
    endpoint = f"/documents/collections/{collection}/documents/{doc_id}/file"
    params = {"type": file_type}
    return await self._make_request("GET", endpoint, params=params)
```

#### Change 2.3: Update `documents.py`

```python
from ..services.document_renderer import DocumentRenderer

@router.get("/.../preview/{doc_type}")
async def preview_document(...):
    renderer = DocumentRenderer(get_rag_client())

    if doc_type == "docx":
        html = await renderer.render_docx_to_html(collection_name, doc_id)
        return {"success": True, "html": html, "type": "docx"}
```

---

## 📊 Impact Analysis

### Services Affected:

1. ✅ **RAG Service** - Simplify (remove mammoth)
2. ✅ **Admin Service** - Add rendering logic
3. ❌ **IdentiFill Service** - No change (already correct)
4. ❌ **Frontend** - No change

### Dependencies:

- Remove: `rag_service/requirements.txt` → mammoth
- Keep: `admin_service/requirements.txt` → mammoth ✅
- Keep: `identifill_service/requirements.txt` → mammoth ✅

### Docker Build Impact:

- RAG Service: Rebuild needed (remove mammoth)
- Admin Service: Rebuild needed (add code)
- Estimated time: ~15 minutes total

---

## 🎯 Architectural Principles Violated

### 1. **Separation of Concerns**

- ❌ Data layer (RAG) doing presentation work
- ✅ Should: Each layer handles its responsibility

### 2. **Single Responsibility Principle**

- ❌ RAG Service: Storage + Rendering
- ✅ Should: RAG = Storage, Admin = Rendering

### 3. **Dependency Direction**

- ❌ Data layer depends on presentation library
- ✅ Should: Presentation depends on data, not vice versa

### 4. **Reusability**

- ❌ If another service needs rendering, must duplicate in RAG
- ✅ Should: Rendering logic centralized in presentation layer

---

## 🚀 Recommended Action Plan

### **Option A: Quick Fix (Recommended for now)**

1. ⏸️ **PAUSE** current Docker build
2. 🔧 Apply all changes from Phase 1 & 2 above
3. 🐳 Rebuild both services
4. 🧪 Test with corrected architecture
5. 📝 Update documentation

**Effort**: ~30 minutes  
**Risk**: Low (well-defined changes)

### **Option B: Continue Current Build**

1. ⚠️ Let build finish (for testing only)
2. 🧪 Test to verify it works functionally
3. 🔧 Then apply architectural fix
4. 🐳 Rebuild again with correct architecture

**Effort**: ~45 minutes (build twice)  
**Risk**: Medium (technical debt if not fixed)

---

## 📝 Conclusion

**Verdict**: Architecture violation detected. Current implementation works but violates best practices.

**Recommendation**: Apply Option A - Fix architecture before proceeding.

**Key Insight**: Follow IdentiFill Service pattern - it already does this correctly!

---

## 🔗 References

- ✅ **Correct Pattern**: `identifill_service/app/services/forms/form_renderer.py`
- ❌ **Current Wrong**: `rag_service/app/api/internal_documents.py`
- 📚 **Separation of Concerns**: https://en.wikipedia.org/wiki/Separation_of_concerns

---

**Report Generated**: October 11, 2025  
**Next Steps**: Await user decision on Option A vs Option B
