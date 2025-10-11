# 🚀 Quick Start - Document Preview Testing

## Kiểm tra implementation mới cho tính năng xem nội dung DOC/JSON

### ⚡ Bước 1: Install Dependencies

#### Admin Service

```bash
cd admin_service
pip install -r requirements.txt
```

**Kiểm tra dependencies mới**:

```bash
pip list | grep mammoth  # Phải thấy: mammoth==1.6.0
pip list | grep aiofiles # Phải thấy: aiofiles==23.2.1
```

#### Frontend (không cần install thêm)

```bash
cd frontend
npm install  # Nếu chưa install
```

---

### 🔧 Bước 2: Start Services

#### Terminal 1: Admin Service

```bash
cd admin_service
python main.py
```

✅ **Expected Output**:

```
🚀 Starting LegalRAG Admin Service...
✅ Admin Service initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

✅ **Expected Output**:

```
VITE v4.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

### 🧪 Bước 3: Test Flow

#### 3.1. Truy cập Admin Page

```
URL: http://localhost:5173/admin
```

1. Click vào **"Database"** trong sidebar
2. Chọn collection **"Bộ thủ tục"** (hoặc collection nào có documents)
3. Xem danh sách documents

#### 3.2. Test DOC Preview

1. Tìm document có badge **"👁 DOC"** (màu tím)
2. Click vào badge "DOC"
3. ✨ **Expected**: Mở trang mới với URL:
   ```
   http://localhost:5173/admin/documents/Bo_thu_tuc/DOC_xxx/preview/docx
   ```
4. **Should see**:
   - Header với breadcrumb: Admin / Bo_thu_tuc / DOC_xxx
   - Nút "Quay lại" và "Tải xuống"
   - Nội dung Word document được render thành HTML
   - Footer với thông tin file

#### 3.3. Test JSON Preview

1. Quay lại admin page (nút "Quay lại" hoặc browser back)
2. Click vào badge **"👁 JSON"** (màu cam)
3. ✨ **Expected**: Mở trang mới với URL:
   ```
   http://localhost:5173/admin/documents/Bo_thu_tuc/DOC_xxx/preview/json
   ```
4. **Should see**:
   - JSON content được format đẹp với syntax highlighting
   - Có thể scroll để xem toàn bộ
   - Nút download để tải JSON file

---

### 🐛 Troubleshooting

#### ❌ Error: "Failed to load document preview"

**Check 1**: Admin Service có đang chạy không?

```bash
curl http://localhost:8001/health
# Expected: {"status": "healthy"}
```

**Check 2**: Collection và doc_id có đúng không?

```bash
# List collections
curl http://localhost:8001/api/collections

# List documents trong collection
curl http://localhost:8001/collections/Bo_thu_tuc/documents
```

**Check 3**: File có tồn tại không?

```bash
# Windows
dir data\collections\Bo_thu_tuc\documents\DOC_*\*.docx
dir data\collections\Bo_thu_tuc\documents\DOC_*\*.json

# Linux/Mac
ls data/collections/Bo_thu_tuc/documents/DOC_*/*.docx
ls data/collections/Bo_thu_tuc/documents/DOC_*/*.json
```

#### ❌ Error: "mammoth module not found"

```bash
cd admin_service
pip install mammoth==1.6.0 aiofiles==23.2.1
```

#### ❌ CORS Error trong browser console

**Check**: Admin Service CORS config có đúng không?

```python
# admin_service/main.py
allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",  # ← Phải có dòng này
    ...
]
```

#### ❌ Routing Error: 404 Not Found

**Check**: Route có được add vào `App.tsx` chưa?

```bash
grep -n "DocumentPreviewPage" frontend/src/App.tsx
# Expected: thấy import và route definition
```

---

### 🧪 API Testing (Direct)

#### Test DOCX Endpoint

```bash
# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:8001/collections/Bo_thu_tuc/documents/DOC_001/preview/docx"

# Linux/Mac
curl http://localhost:8001/collections/Bo_thu_tuc/documents/DOC_001/preview/docx
```

**Expected Response**:

```json
{
  "success": true,
  "doc_id": "DOC_001",
  "collection": "Bo_thu_tuc",
  "type": "docx",
  "filename": "...",
  "html": "<html>...</html>",
  "messages": []
}
```

#### Test JSON Endpoint

```bash
curl http://localhost:8001/collections/Bo_thu_tuc/documents/DOC_001/preview/json
```

**Expected Response**:

```json
{
  "success": true,
  "doc_id": "DOC_001",
  "collection": "Bo_thu_tuc",
  "type": "json",
  "filename": "...",
  "data": { ... }  // Full JSON content
}
```

---

### ✅ Success Criteria

Feature hoạt động đúng khi:

1. ✅ Click vào "DOC" badge → Mở trang mới với nội dung Word
2. ✅ Click vào "JSON" badge → Mở trang mới với JSON data
3. ✅ Breadcrumb navigation hiển thị đúng
4. ✅ Nút "Quay lại" hoạt động (back to admin)
5. ✅ Nút "Tải xuống" download được file
6. ✅ Browser back button hoạt động
7. ✅ URL có thể bookmark/share
8. ✅ Loading state hiển thị khi đang fetch
9. ✅ Error message hiển thị khi có lỗi

---

### 📊 Performance Check

#### Admin Service Logs

```
📄 Rendering DOCX to HTML: document.docx
✅ Preview request completed in 150ms
```

#### Browser Console

```javascript
// Should see logs from axios-config.ts
🚀 Admin API Call: GET /collections/.../preview/docx
✅ Admin API Success: 200
```

---

### 🎯 Next Testing Steps

1. **Test với nhiều documents**: Thử với các documents khác nhau
2. **Test error cases**:
   - Document không tồn tại
   - Collection không tồn tại
   - File bị lỗi/corrupt
3. **Test performance**: Document lớn (>1MB)
4. **Test UX**:
   - Responsive trên mobile
   - Print preview
   - Copy/paste nội dung

---

### 📝 Checklist

- [ ] Admin Service started successfully
- [ ] Frontend dev server running
- [ ] Can access admin page
- [ ] Can see document list
- [ ] DOC badge is clickable (purple with eye icon)
- [ ] JSON badge is clickable (orange with eye icon)
- [ ] DOC preview page opens correctly
- [ ] JSON preview page opens correctly
- [ ] Back button works
- [ ] Download button works
- [ ] No console errors
- [ ] No CORS errors

---

## 🎉 Success!

Nếu tất cả các test đều pass, feature đã **READY FOR PRODUCTION**! 🚀

Có thể tiến hành commit và deploy.
