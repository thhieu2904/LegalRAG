# 🔍 Chi Tiết Phân Tích: .doc vs .docx Rendering Solutions

**Date**: October 11, 2025  
**Context**: Document Preview Feature - Format Support Analysis

---

## 📊 Tổng Quan Vấn Đề

### Tình Huống Hiện Tại:

- **Dataset**: 100% documents là `.doc` (Office 97-2003 format)
- **Mammoth**: Chủ yếu support `.docx` (Office 2007+ ZIP-based)
- **Error**: `'NoneType' object has no attribute 'children'` khi render `.doc`

### Mục Tiêu:

**"Mình chỉ cần hiển thị lên thôi"** - Display documents, không cần edit

---

## 🔧 Cách IdentiFill Service Xử Lý Forms

### 1️⃣ **Form Rendering** (form_renderer.py)

**Pattern**: Fetch từ RAG → Render với Mammoth → Trả HTML

```python
# identifill_service/app/services/forms/form_renderer.py

class FormRenderingService:
    async def convert_docx_to_html(
        self,
        collection_id: str,
        doc_id: str,
        form_filename: str
    ) -> Dict[str, Any]:
        """
        Convert DOCX → HTML using Mammoth

        Flow:
        1. Download file từ RAG Service (HTTP)
        2. Stream vào memory (BytesIO)
        3. Mammoth convert → HTML
        4. Post-process (fix checkboxes, placeholders)
        5. Return HTML string
        """

        # 1. Fetch file từ RAG Service
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{rag_url}/api/forms/file/{collection_id}/{doc_id}/{form_filename}/download"
            ) as response:
                file_content = await response.read()

        # 2. Convert với Mammoth (in-memory)
        docx_stream = io.BytesIO(file_content)
        result = mammoth.convert_to_html(docx_stream)
        html_content = result.value

        # 3. Post-process HTML
        html_content = self._post_process_html(html_content)

        return {"html_content": html_content}
```

**Key Points**:

- ✅ Fetch file qua HTTP (không trực tiếp read file)
- ✅ In-memory processing (BytesIO)
- ✅ Mammoth CHỈ dùng cho DOCX
- ✅ Post-processing cho checkboxes, placeholders

---

### 2️⃣ **Template Filling** (template_filling_service.py)

**Pattern**: Edit DOCX → Fill placeholders → Return filled DOCX

```python
# identifill_service/app/services/template_filling_service.py

from docx import Document  # python-docx library

class TemplateFillingService:
    def extract_placeholders_from_docx(self, docx_content: bytes):
        """
        Extract {{placeholder}} từ DOCX
        Dùng python-docx để READ nội dung
        """
        temp_file = io.BytesIO(docx_content)
        doc = Document(temp_file)  # python-docx

        # Extract text from paragraphs & tables
        for paragraph in doc.paragraphs:
            all_text += paragraph.text

        for table in doc.tables:
            # Extract from tables
```

**Key Points**:

- ✅ `python-docx` dùng cho READ/WRITE DOCX
- ✅ Dùng cho TEMPLATE EDITING, không phải rendering
- ❌ KHÔNG render ra HTML

---

### 3️⃣ **Dependencies**

```txt
# identifill_service/requirements.txt

mammoth==1.6.0           # DOCX → HTML rendering
python-docx>=1.1.1       # DOCX reading/editing (template filling)
```

**Vai Trò**:

- **Mammoth**: DOCX → HTML (for display)
- **python-docx**: DOCX editing (for template filling)

---

## 🎯 Solutions Cho Document Preview

### ❌ **Option 1: python-docx CHO RENDERING**

**Q**: "python-docx có làm được không?"

**A**: ❌ **KHÔNG** - python-docx KHÔNG render HTML

```python
from docx import Document

doc = Document("file.docx")

# python-docx CHỈ cho phép:
✅ doc.paragraphs[0].text          # Read text
✅ doc.tables[0].cell(0,0).text    # Read table
✅ doc.add_paragraph("New text")   # Write content
✅ doc.save("output.docx")         # Save DOCX

# python-docx KHÔNG có:
❌ doc.to_html()                   # NO HTML conversion
❌ doc.render_html()               # NO rendering method
```

**Kết Luận**: `python-docx` là library cho **EDITING**, không phải **RENDERING**

---

### ✅ **Option 2A: MAMMOTH với .doc Support** (RECOMMENDED)

**Giải Pháp**: Thêm fallback renderer cho `.doc` format

#### Implementation:

```python
# admin_service/app/services/document_renderer.py

import mammoth
from io import BytesIO

class DocumentRenderer:
    async def render_docx_to_html(self, collection: str, doc_id: str) -> str:
        # 1. Get file bytes từ RAG Service
        file_bytes = await self.rag_client.get_document_file(
            collection=collection,
            doc_id=doc_id,
            file_type="docx"
        )

        # 2. Detect file format
        signature = file_bytes[:2]
        is_doc = signature == b'\xD0\xCF'   # .doc (OLE2)
        is_docx = signature == b'PK'         # .docx (ZIP)

        # 3. Choose renderer
        if is_docx:
            # Use Mammoth (works well with .docx)
            return await self._render_with_mammoth(file_bytes)
        elif is_doc:
            # Use fallback renderer for .doc
            return await self._render_doc_fallback(file_bytes)
        else:
            raise ValueError(f"Unknown format: {signature.hex()}")

    async def _render_with_mammoth(self, file_bytes: bytes) -> str:
        """Render .docx with Mammoth"""
        docx_file = BytesIO(file_bytes)
        result = mammoth.convert_to_html(docx_file)
        return result.value

    async def _render_doc_fallback(self, file_bytes: bytes) -> str:
        """
        Fallback renderer for .doc files

        Options:
        A) LibreOffice headless conversion
        B) Antiword library
        C) pywin32 COM automation (Windows only)
        D) Simple text extraction with python-docx
        """
        # See detailed implementations below
```

---

### ✅ **Option 2B: .doc Fallback Implementations**

#### **Solution 2B-1: LibreOffice Headless** (BEST for Production)

**Pros**:

- ✅ Hỗ trợ TẤT CẢ formats (.doc, .docx, .odt, .pdf)
- ✅ High fidelity conversion
- ✅ Cross-platform (Linux, Windows, Mac)
- ✅ No Python dependencies

**Cons**:

- ⚠️ Requires LibreOffice installed
- ⚠️ Slower (subprocess call)

**Implementation**:

```python
import subprocess
import tempfile
from pathlib import Path

async def _render_doc_fallback(self, file_bytes: bytes) -> str:
    """Convert .doc → HTML using LibreOffice"""

    # 1. Write .doc to temp file
    with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as tmp_doc:
        tmp_doc.write(file_bytes)
        tmp_doc_path = Path(tmp_doc.name)

    try:
        # 2. Convert to HTML with LibreOffice
        tmp_html_path = tmp_doc_path.with_suffix('.html')

        subprocess.run([
            'soffice',  # or 'libreoffice'
            '--headless',
            '--convert-to', 'html',
            '--outdir', str(tmp_doc_path.parent),
            str(tmp_doc_path)
        ], check=True, timeout=30)

        # 3. Read converted HTML
        html_content = tmp_html_path.read_text(encoding='utf-8')

        return html_content

    finally:
        # Cleanup
        tmp_doc_path.unlink(missing_ok=True)
        tmp_html_path.unlink(missing_ok=True)
```

**Docker Setup**:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-core \
    && rm -rf /var/lib/apt/lists/*
```

---

#### **Solution 2B-2: Antiword Library** (Lightweight)

**Pros**:

- ✅ Nhẹ, nhanh
- ✅ Cross-platform
- ✅ Simple text extraction

**Cons**:

- ❌ Không preserve formatting (no bold, italics, tables)
- ❌ Text-only output
- ❌ Limited .doc support

**Implementation**:

```python
import subprocess

async def _render_doc_fallback(self, file_bytes: bytes) -> str:
    """Extract text from .doc using antiword"""

    with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # Run antiword to extract text
        result = subprocess.run(
            ['antiword', tmp_path],
            capture_output=True,
            text=True,
            check=True
        )

        text_content = result.stdout

        # Wrap in basic HTML
        html = f"""
        <div class="doc-content">
            <pre>{text_content}</pre>
        </div>
        """

        return html

    finally:
        Path(tmp_path).unlink(missing_ok=True)
```

**Docker Setup**:

```dockerfile
RUN apt-get update && apt-get install -y antiword
```

---

#### **Solution 2B-3: Python-docx Text Extraction** (Pure Python)

**Pros**:

- ✅ Pure Python, no external dependencies
- ✅ Cross-platform
- ✅ Fast

**Cons**:

- ⚠️ Limited .doc support (may fail)
- ❌ No formatting preservation
- ❌ Text-only

**Implementation**:

```python
from docx import Document

async def _render_doc_fallback(self, file_bytes: bytes) -> str:
    """
    Extract text from .doc using python-docx
    May work for some .doc files
    """
    try:
        doc_file = BytesIO(file_bytes)
        doc = Document(doc_file)

        # Extract all text
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(f"<p>{para.text}</p>")

        # Extract tables
        tables_html = []
        for table in doc.tables:
            table_html = "<table border='1'>"
            for row in table.rows:
                table_html += "<tr>"
                for cell in row.cells:
                    table_html += f"<td>{cell.text}</td>"
                table_html += "</tr>"
            table_html += "</table>"
            tables_html.append(table_html)

        # Combine
        html_content = f"""
        <div class="doc-content">
            {''.join(paragraphs)}
            {''.join(tables_html)}
        </div>
        """

        return html_content

    except Exception as e:
        logger.error(f"python-docx failed for .doc: {e}")
        # Fallback: Show error message
        return f"""
        <div class="error">
            <h3>Cannot render .doc file</h3>
            <p>Error: {str(e)}</p>
            <p>Please convert to .docx format</p>
        </div>
        """
```

---

### ✅ **Option 3: Client-Side Rendering** (Mammoth.js)

**Pattern**: Send raw bytes to frontend → Render in browser

**Pros**:

- ✅ No server-side processing
- ✅ Faster server response
- ✅ Works with .docx

**Cons**:

- ❌ Still doesn't support .doc
- ❌ Requires frontend changes
- ❌ Larger frontend bundle

**Implementation**:

```typescript
// frontend/src/utils/documentRenderer.ts

import mammoth from "mammoth";

export async function renderDocx(fileBytes: ArrayBuffer): Promise<string> {
  const result = await mammoth.convertToHtml({ arrayBuffer: fileBytes });
  return result.value;
}

// Usage in component
const response = await fetch(
  `/api/collections/${collection}/documents/${docId}/file?type=docx`
);
const fileBytes = await response.arrayBuffer();
const html = await renderDocx(fileBytes);
```

---

## 📊 Comparison Matrix

| Solution          | .doc Support | .docx Support | Complexity | Performance | Formatting |
| ----------------- | ------------ | ------------- | ---------- | ----------- | ---------- |
| **Mammoth only**  | ❌           | ✅            | Low        | Fast        | Excellent  |
| **+ LibreOffice** | ✅           | ✅            | Medium     | Slow        | Excellent  |
| **+ Antiword**    | ⚠️ Text only | ✅            | Low        | Fast        | Poor       |
| **+ python-docx** | ⚠️ Limited   | ✅            | Low        | Fast        | Poor       |
| **Client-side**   | ❌           | ✅            | Medium     | Fast        | Good       |

---

## 🎯 RECOMMENDED APPROACH

### **Option: Dual Renderer Pattern** (Like IdentiFill)

```python
class DocumentRenderer:
    """
    Dual renderer:
    - .docx → Mammoth (high quality)
    - .doc → LibreOffice fallback (for legacy files)
    """

    async def render_document_to_html(
        self,
        collection: str,
        doc_id: str
    ) -> Dict[str, Any]:
        # 1. Get file bytes
        file_bytes = await self.rag_client.get_document_file(...)

        # 2. Detect format
        signature = file_bytes[:2]

        # 3. Route to appropriate renderer
        if signature == b'PK':  # .docx
            html = await self._render_with_mammoth(file_bytes)
            renderer = "mammoth"
        elif signature == b'\xD0\xCF':  # .doc
            html = await self._render_with_libreoffice(file_bytes)
            renderer = "libreoffice"
        else:
            raise ValueError("Unknown file format")

        return {
            "html": html,
            "renderer": renderer,
            "format": "docx" if signature == b'PK' else "doc"
        }
```

---

## 🚀 Implementation Steps

### Phase 1: Add Format Detection

```python
# Update document_renderer.py
async def render_docx_to_html(self, collection: str, doc_id: str):
    file_bytes = await self.rag_client.get_document_file(...)

    # Detect format
    signature = file_bytes[:2]
    file_format = self._detect_format(signature)

    if file_format == "docx":
        return await self._render_docx(file_bytes)
    elif file_format == "doc":
        return await self._render_doc(file_bytes)
```

### Phase 2: Add LibreOffice Renderer

```bash
# Update Dockerfile
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-core
```

```python
# Add to document_renderer.py
async def _render_doc(self, file_bytes: bytes) -> str:
    # LibreOffice conversion
    return await self._convert_with_libreoffice(file_bytes)
```

### Phase 3: Test Both Formats

```python
# test/test_document_formats.py
async def test_docx_rendering():
    # Test with .docx file
    html = await renderer.render_document("collection", "DOC_001")
    assert "<html>" in html or "<p>" in html

async def test_doc_rendering():
    # Test with .doc file
    html = await renderer.render_document("collection", "DOC_002")
    assert "<html>" in html or "<p>" in html
```

---

## ✅ Final Recommendation

**BEST SOLUTION for LegalRAG**:

1. ✅ **Keep Mammoth** for .docx (when available)
2. ✅ **Add LibreOffice** for .doc fallback
3. ✅ **Pattern học từ IdentiFill**:
   - Fetch qua HTTP
   - In-memory processing
   - Post-processing HTML

**Why**:

- ✅ Support cả .doc VÀ .docx
- ✅ High fidelity rendering
- ✅ Production-ready (LibreOffice stable)
- ✅ Consistent với IdentiFill pattern
- ✅ Không cần convert toàn bộ dataset

**Effort**: ~2-3 hours implementation + testing

---

**Next Step**: Implement dual renderer pattern với LibreOffice fallback?
