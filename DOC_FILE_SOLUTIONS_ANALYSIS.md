# 📊 Phân Tích: Giải Pháp Hiển Thị File .doc

**Date**: October 11, 2025  
**Problem**: File .doc (Office 97-2003) không đọc được bằng mammoth và python-docx  
**Error**: `file is not a Word file, content type is 'application/vnd.openxmlformats-officedocument.themeManager+xml'`

---

## 🔍 Phân Tích Vấn Đề

### **Tại sao .doc file fail?**

1. **File Format**: `.doc` là OLE2 format (Office 97-2003) - rất phức tạp
2. **Signature**: `\xD0\xCF` xác nhận đúng là .doc file
3. **python-docx**: Chỉ hỗ trợ .docx (Office 2007+), KHÔNG hỗ trợ .doc
4. **mammoth**: Optimized cho .docx, hỗ trợ .doc rất hạn chế
5. **Dataset**: 100% files của bạn là .doc (166 documents)

### **Lỗi cụ thể**:

```
'file is not a Word file, content type is application/vnd.openxmlformats-officedocument.themeManager+xml'
```

→ File có embedded XML/theme data mà python-docx không parse được

---

## 🎯 Các Giải Pháp Khả Thi

### **Option 1: Mở bằng Word trên máy** ❌

**Cách hoạt động**:

```python
import win32com.client  # pywin32

def convert_doc_to_html_with_word(doc_path):
    word = win32com.client.Dispatch("Word.Application")
    doc = word.Documents.Open(doc_path)
    html_path = doc_path.replace('.doc', '.html')
    doc.SaveAs(html_path, FileFormat=8)  # 8 = HTML
    doc.Close()
    word.Quit()
```

**✅ Ưu điểm**:

- ✅ Độ chính xác cao nhất (100%)
- ✅ Giữ nguyên formatting, tables, images
- ✅ Microsoft Word là chuẩn

**❌ Nhược điểm**:

- ❌ **CHỈ HOẠT ĐỘNG trên Windows** (không có Linux/Docker)
- ❌ **YÊU CẦU Microsoft Office** cài đặt ($$$)
- ❌ **Không portable** - không deploy được lên server Linux
- ❌ **Bảo mật**: Rủi ro khi execute Word từ web service
- ❌ **Performance**: Chậm (phải khởi động Word application)
- ❌ **Licensing**: Vi phạm license nếu dùng trên server

**Kết luận**: ❌ **KHÔNG KHẢ THI** cho production/Docker

---

### **Option 2: LibreOffice Headless** ✅ (RECOMMENDED)

**Cách hoạt động**:

```bash
# Cài LibreOffice trong Docker
apt-get install libreoffice-writer

# Convert .doc → HTML
soffice --headless --convert-to html --outdir /output /input/file.doc
```

**Python wrapper**:

```python
import subprocess

def convert_doc_to_html_libreoffice(doc_bytes):
    # Save temp file
    with open('/tmp/input.doc', 'wb') as f:
        f.write(doc_bytes)

    # Convert using LibreOffice
    subprocess.run([
        'soffice',
        '--headless',
        '--convert-to', 'html',
        '--outdir', '/tmp',
        '/tmp/input.doc'
    ])

    # Read HTML output
    with open('/tmp/input.html', 'r') as f:
        html = f.read()

    return html
```

**✅ Ưu điểm**:

- ✅ **Chạy trong Docker** - hoàn toàn portable
- ✅ **FREE & Open Source** - không cần license
- ✅ **Hỗ trợ .doc và .docx**
- ✅ **Giữ formatting tốt** (~90% accuracy)
- ✅ **Production-ready** - nhiều công ty lớn dùng
- ✅ **Stable** - được maintain tốt

**⚠️ Nhược điểm**:

- ⚠️ Docker image size tăng (~200MB)
- ⚠️ Conversion hơi chậm (~1-2 giây/file)
- ⚠️ HTML output không "clean" (có nhiều style tags)

**📦 Implementation**:

```dockerfile
# admin_service/Dockerfile
FROM python:3.11-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-core \
    && rm -rf /var/lib/apt/lists/*

# Rest of Dockerfile...
```

```python
# admin_service/app/services/document_renderer.py
import subprocess
import tempfile
import os

async def render_doc_with_libreoffice(docx_bytes: bytes) -> str:
    """Convert .doc to HTML using LibreOffice headless"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save input file
        input_path = os.path.join(tmpdir, 'input.doc')
        with open(input_path, 'wb') as f:
            f.write(docx_bytes)

        # Convert to HTML
        result = subprocess.run([
            'soffice',
            '--headless',
            '--convert-to', 'html',
            '--outdir', tmpdir,
            input_path
        ], capture_output=True, timeout=10)

        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")

        # Read HTML output
        output_path = os.path.join(tmpdir, 'input.html')
        with open(output_path, 'r', encoding='utf-8') as f:
            html = f.read()

        return html
```

**Kết luận**: ✅ **KHUYẾN NGHỊ** - Best balance giữa quality và feasibility

---

### **Option 3: Batch Convert .doc → .docx** ⭐ (SIMPLEST)

**Cách hoạt động**:

```bash
# One-time conversion tất cả .doc → .docx
for file in *.doc; do
    soffice --headless --convert-to docx "$file"
done
```

**✅ Ưu điểm**:

- ✅ **Giải quyết vấn đề gốc** - mammoth hoạt động hoàn hảo với .docx
- ✅ **ONE-TIME operation** - chỉ cần chạy 1 lần
- ✅ **Không thay đổi code** - dùng mammoth như hiện tại
- ✅ **Performance tốt** - mammoth nhanh hơn LibreOffice
- ✅ **Clean HTML** - mammoth output đẹp hơn

**⚠️ Nhược điểm**:

- ⚠️ Cần chạy conversion script một lần
- ⚠️ File size tăng nhẹ (.docx thường lớn hơn .doc)
- ⚠️ Cần backup .doc gốc

**📦 Implementation Script**:

```python
# tools/convert_doc_to_docx.py
import subprocess
import os
from pathlib import Path

def convert_all_docs_to_docx(base_dir: str):
    """
    Convert all .doc files to .docx using LibreOffice

    Args:
        base_dir: Path to collections directory
    """
    base_path = Path(base_dir)
    doc_files = list(base_path.rglob("*.doc"))

    print(f"🔍 Found {len(doc_files)} .doc files")

    for i, doc_file in enumerate(doc_files, 1):
        print(f"[{i}/{len(doc_files)}] Converting: {doc_file.name}")

        try:
            # Convert .doc → .docx
            result = subprocess.run([
                'soffice',
                '--headless',
                '--convert-to', 'docx',
                '--outdir', str(doc_file.parent),
                str(doc_file)
            ], capture_output=True, timeout=30)

            if result.returncode == 0:
                # Rename .doc → .doc.bak (backup)
                backup_path = doc_file.with_suffix('.doc.bak')
                doc_file.rename(backup_path)
                print(f"  ✅ Converted + Backed up to {backup_path.name}")
            else:
                print(f"  ❌ Failed: {result.stderr}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n🎉 Conversion complete!")

if __name__ == "__main__":
    convert_all_docs_to_docx("/app/data/storage/collections")
```

**Usage**:

```bash
# Run once in Docker container
docker exec legalrag-admin-service-dev python tools/convert_doc_to_docx.py
```

**Kết luận**: ⭐ **TỐI ƯU NHẤT** - Giải quyết vấn đề một lần, không cần thay đổi code nhiều

---

### **Option 4: antiword** (Text-only) ⚠️

**Cách hoạt động**:

```bash
apt-get install antiword
antiword file.doc > output.txt
```

**✅ Ưu điểm**:

- ✅ Nhỏ gọn (~2MB)
- ✅ Nhanh
- ✅ Stable

**❌ Nhược điểm**:

- ❌ **CHỈ TEXT** - mất hết formatting, tables, images
- ❌ Không suitable cho legal documents (cần formatting)

**Kết luận**: ⚠️ **KHÔNG PHÙ HỢP** - Legal docs cần formatting

---

### **Option 5: textract/olefile** ⚠️

**Cách hoạt động**:

```python
import textract
text = textract.process("file.doc")
```

**❌ Nhược điểm**:

- Similar to antiword - text only
- Dependencies phức tạp
- Không stable

**Kết luận**: ⚠️ **KHÔNG PHÙ HỢP**

---

## 📊 So Sánh Tổng Quan

| Solution             | Accuracy | Docker? | Speed  | Complexity | Cost | Production Ready? |
| -------------------- | -------- | ------- | ------ | ---------- | ---- | ----------------- |
| **MS Word (local)**  | 100%     | ❌      | Medium | Low        | $$$  | ❌ NO             |
| **LibreOffice**      | 90%      | ✅      | Slow   | Medium     | FREE | ✅ YES            |
| **Convert to .docx** | 95%      | ✅      | Fast\* | Low        | FREE | ✅ YES            |
| **antiword**         | 50%      | ✅      | Fast   | Low        | FREE | ⚠️ LIMITED        |
| **textract**         | 50%      | ✅      | Medium | High       | FREE | ⚠️ LIMITED        |

\*Fast after one-time conversion

---

## 🎯 Khuyến Nghị Cho Bạn

### **Giải Pháp Tối Ưu: HYBRID APPROACH**

**Phase 1: IMMEDIATE** (30 phút)

```bash
# Batch convert tất cả .doc → .docx
docker exec legalrag-admin-service-dev bash -c "
  apt-get update && apt-get install -y libreoffice-writer
  cd /app/data/storage/collections
  find . -name '*.doc' -exec soffice --headless --convert-to docx --outdir {} {} \;
"
```

**Phase 2: CODE CLEANUP**

- Keep mammoth rendering (đã hoạt động tốt)
- Remove .doc fallback code
- Update file validation to accept .docx

**Phase 3: FUTURE-PROOF** (Optional)

- Add LibreOffice fallback cho edge cases
- Auto-convert .doc uploads → .docx

---

## 🚀 Implementation Plan

### **RECOMMENDED: Batch Convert Once**

**Bước 1**: Tạo conversion script

```python
# tools/batch_convert_docs.py
import subprocess
import shutil
from pathlib import Path

def convert_all():
    collections_dir = Path("/app/data/storage/collections")

    for doc_file in collections_dir.rglob("*.doc"):
        print(f"Converting: {doc_file}")

        # Convert
        subprocess.run([
            'soffice', '--headless',
            '--convert-to', 'docx',
            '--outdir', str(doc_file.parent),
            str(doc_file)
        ])

        # Backup original
        shutil.move(str(doc_file), str(doc_file) + '.bak')

        print(f"✅ Done: {doc_file.stem}.docx")

if __name__ == "__main__":
    convert_all()
```

**Bước 2**: Run in Docker

```bash
# Install LibreOffice temporarily
docker exec legalrag-admin-service-dev apt-get update
docker exec legalrag-admin-service-dev apt-get install -y libreoffice-writer

# Run conversion
docker exec legalrag-admin-service-dev python tools/batch_convert_docs.py

# Verify
docker exec legalrag-rag-service-dev find /app/data/storage/collections -name "*.docx" | wc -l
# Should show 166 files
```

**Bước 3**: Test

```bash
# Test preview with .docx
curl "http://localhost:8001/api/collections/quy_trinh_boi_thuong_nn/documents/DOC_001/preview/docx"
# Should work perfectly with mammoth
```

---

## 💡 Kết Luận

### **TL;DR - Khuyến nghị của mình:**

1. ✅ **BEST**: Batch convert .doc → .docx (ONE-TIME)

   - Chạy 1 lần
   - Mammoth hoạt động hoàn hảo
   - Không thay đổi code
   - Production-ready

2. ⚠️ **ALTERNATIVE**: LibreOffice headless (nếu cần dynamic conversion)

   - Tốt cho upload workflow tương lai
   - Chậm hơn nhưng reliable
   - Docker-friendly

3. ❌ **KHÔNG NÊN**: MS Word local
   - Chỉ Windows
   - Không scalable
   - Licensing issues

---

## 📋 Action Items

**Bạn muốn mình làm gì bây giờ?**

**A) Batch Convert** (RECOMMENDED):

- Mình sẽ tạo script convert tất cả .doc → .docx
- Run một lần trong Docker
- Test preview
- **Timeline**: 30-45 phút

**B) LibreOffice Integration**:

- Add LibreOffice vào Docker image
- Update DocumentRenderer với LibreOffice fallback
- **Timeline**: 1-2 giờ

**C) Hybrid**:

- Batch convert existing files
- Add LibreOffice cho future uploads
- **Timeline**: 1.5-2 giờ

**Bạn chọn approach nào?** 🤔
