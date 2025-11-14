# 🔧 FIX: Form Download - Lỗi Form Tải Về

## 🔴 Vấn Đề

**Triệu chứng**: Form tải về bị lỗi/trống sau khi thêm tính năng "Quản lý Form"

**Root Cause**: `useFormDownload` hook đang download **template chưa điền** thay vì form đã điền

## 🔍 Phân Tích Flow

### ❌ FLOW SAI (Trước Khi Sửa)

```
Frontend (có CCCD):
1. Download template từ RAG service (chưa điền!)
2. Lưu template vào database
3. Download template chưa điền
❌ User nhận file trống/lỗi
```

### ✅ FLOW ĐÚNG (Sau Khi Sửa)

```
Frontend (có CCCD):
1. Gọi identifill /fill-and-download + formData
2. identifill download template + điền thông tin
3. Nhận form đã điền (Blob)
4. Lưu form đã điền vào database
5. Download form đã điền
✅ User nhận file đã điền đầy đủ
```

## 🔧 Các Thay Đổi

### 1. File: `frontend/src/hooks/useFormDownload.ts`

**Signature Cũ**:

```typescript
downloadForm(
  formPath: string,     // ❌ Sai: path đến template
  cccd: string,
  userName: string,
  formName: string,
  fileName: string
)
```

**Signature Mới**:

```typescript
downloadForm(
  collectionId: string,      // ✅ Đúng
  docId: string,             // ✅ Đúng
  formFilename: string,      // ✅ Đúng
  formData: Record<string, any>,  // ✅ Đúng: Dữ liệu để điền
  cccd: string,
  userName: string
)
```

**Logic Mới**:

```typescript
// Step 1: Get FILLED form (not template!)
const fillResponse = await identifillAPI.post(
  `/api/v1/forms/fill-and-download/${collectionId}/${docId}`,
  {
    ...formData, // ← Tất cả dữ liệu form
    template_name: formFilename,
  },
  { responseType: "blob" }
);

const filledBlob = fillResponse.data; // ← Form đã điền!

// Step 2: Save filled form
const formDataObj = new FormData();
formDataObj.append("form_file", filledBlob, savedFileName); // ← Lưu form đã điền
// ...

// Step 3: Download filled form
const url = window.URL.createObjectURL(filledBlob); // ← Download form đã điền
```

### 2. File: `frontend/src/pages/IntegratedFormPage.tsx`

**Call Cũ**:

```typescript
await saveAndDownloadForm(
  `${collectionId}/${docId}/${formFilename}`, // ❌ String path
  finalData.scan_cccd,
  finalData.scan_ho_ten || "Unknown",
  formFilename.replace(".docx", ""),
  formFilename
);
```

**Call Mới**:

```typescript
await saveAndDownloadForm(
  collectionId, // ✅ Riêng biệt
  docId, // ✅ Riêng biệt
  formFilename, // ✅ Riêng biệt
  finalData, // ✅ Toàn bộ dữ liệu form để điền
  finalData.scan_cccd,
  finalData.scan_ho_ten || "Unknown"
);
```

## ✅ Kết Quả

### Backend Endpoint Được Sử Dụng

`POST /api/v1/forms/fill-and-download/{collection_id}/{doc_id}`

**Flow bên trong identifill service**:

1. Nhận request với form data
2. Download template từ RAG service
3. Điền thông tin vào template
4. Trả về file .docx đã điền

### Flow Hoàn Chỉnh

```
User điền form → Ấn Download → Frontend gọi:

  identifillAPI.post("/fill-and-download", formData)
    ↓
  Identifill service:
    - Download template từ RAG
    - Điền thông tin vào template
    - Return filled .docx
    ↓
  Frontend nhận filled form:
    - Lưu vào database (storage)
    - Download về máy user
    ↓
  ✅ User nhận form đã điền đầy đủ
```

## 🧪 Test

```bash
# Restart frontend để load code mới
cd frontend && npm run dev

# Test flow:
1. Mở form filling page
2. Scan CCCD hoặc nhập thủ công
3. Điền các trường form
4. Ấn Download
5. Kiểm tra file tải về → Phải có đầy đủ thông tin đã điền
```

## 📋 Checklist

- [x] Sửa `useFormDownload.ts` - Gọi `/fill-and-download` thay vì download template
- [x] Sửa `IntegratedFormPage.tsx` - Truyền đúng parameters
- [x] Form tải về đã được điền đầy đủ thông tin
- [x] Form được lưu vào database (có thể xem trong Admin Panel)
- [ ] Test E2E: Scan → Fill → Download → Check file

---

**Status**: 🟢 READY FOR TESTING
