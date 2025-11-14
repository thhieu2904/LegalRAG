# 📝 Form Storage Flow - Khi Nào File Được Lưu?

## 🎯 Tổng Quan

**File được lưu NGAY KHI người dùng ấn vào nút "Lưu Form" hoặc "Download Form"**, không phải chỉ khi ấn download. Dưới đây là chi tiết flow:

---

## 🔄 Flow Hoàn Chỉnh: Từ RAG Service → Storage → Frontend

### 1️⃣ **Người Dùng Quét CCCD & Xem Form** (Frontend)

```
┌─────────────────────────────────────────────────────────────┐
│ User Action: Scan CCCD + View Form (Khai_sinh.docx)        │
├─────────────────────────────────────────────────────────────┤
│ Frontend:                                                    │
│ ├─ Show CCCD data (scan_cccd, scan_ho_ten)                 │
│ ├─ Fetch form from RAG: GET /api/forms/file/.../           │
│ ├─ Display form as HTML                                     │
│ └─ Show "✏️ Edit", "💾 Save Form", "📥 Download" buttons   │
└─────────────────────────────────────────────────────────────┘
```

### 2️⃣ **Người Dùng Ấn "💾 Save Form"** ← ⭐ KEY MOMENT!

**BẮT ĐẦU LƯU TRỮ NGAY TẠI ĐÂY!**

```
┌──────────────────────────────────────────────────────────────┐
│ User Action: Click "Save Form" button                        │
├──────────────────────────────────────────────────────────────┤
│ Frontend Code:                                               │
│                                                              │
│ const saveForm = async () => {                              │
│   const formData = new FormData();                           │
│   formData.append('form_file', documentFile);               │
│   formData.append('scan_cccd', userData.scan_cccd);         │
│   formData.append('scan_ho_ten', userData.scan_ho_ten);     │
│   formData.append('form_name', formType);  // "Khai_sinh"   │
│                                                              │
│   // CALL STORAGE API                                       │
│   const response = await fetch(                             │
│     'http://localhost:8002/api/v1/storage/save',            │
│     {                                                        │
│       method: 'POST',                                        │
│       body: formData                                         │
│     }                                                        │
│   );                                                         │
│                                                              │
│   const result = await response.json();                      │
│   console.log('✅ Form saved:', result.file_id);            │
│ };                                                           │
└──────────────────────────────────────────────────────────────┘
```

### 3️⃣ **Storage API Nhận Request & Lưu File** ⭐

```
┌──────────────────────────────────────────────────────────────┐
│ Backend: POST /api/v1/storage/save                           │
├──────────────────────────────────────────────────────────────┤
│ identifill_service/app/api/v1/storage.py:                    │
│                                                              │
│ @router.post("/save", response_model=FormSaveResponse)      │
│ async def save_document(                                     │
│     form_file: UploadFile = File(...),                       │
│     scan_cccd: str = Form(...),  // "079987654321"          │
│     scan_ho_ten: str = Form(...),  // "Trần Thị Hà"        │
│     form_name: str = Form(...)  // "Khai_sinh"              │
│ ):                                                           │
│     # SAVE TO FILESYSTEM                                    │
│     result = storage.save_form(                             │
│         scan_cccd=scan_cccd,                                 │
│         scan_ho_ten=scan_ho_ten,                             │
│         form_name=form_name,                                 │
│         form_content=await form_file.read()                 │
│     )                                                        │
│     return FormSaveResponse(**result)                        │
│                                                              │
│ Response (JSON):                                             │
│ {                                                            │
│   "success": true,                                           │
│   "file_id": "a93a8a5b-...",                                │
│   "file_name": "Khai_sinh_20251025_124533.docx",            │
│   "message": "Form saved successfully"                       │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
```

### 4️⃣ **FormStorageService Thực Thi Lưu Trữ** 💾

```
┌──────────────────────────────────────────────────────────────┐
│ Service Layer: form_storage_service.py                       │
├──────────────────────────────────────────────────────────────┤
│ save_form() operation:                                       │
│                                                              │
│ 1️⃣  Create directory:                                       │
│    data/scanned_documents/079987654321/forms/               │
│                                                              │
│ 2️⃣  Generate unique filename:                              │
│    Khai_sinh_20251025_124533.docx (timestamp-based)         │
│                                                              │
│ 3️⃣  Write file to filesystem:                              │
│    data/scanned_documents/079987654321/forms/               │
│    Khai_sinh_20251025_124533.docx (202 bytes)               │
│                                                              │
│ 4️⃣  Record in database:                                    │
│    INSERT INTO stored_forms (                               │
│      file_id, scan_cccd, form_name,                         │
│      file_name, file_size, created_at                       │
│    ) VALUES (                                                │
│      'a93a8a5b-...', '079987654321', 'Khai_sinh',          │
│      'Khai_sinh_20251025_124533.docx', 202,                 │
│      '2025-10-25T12:45:33.290825'                           │
│    );                                                        │
└──────────────────────────────────────────────────────────────┘
```

### 5️⃣ **Frontend Nhận Thông Báo Thành Công**

```
┌──────────────────────────────────────────────────────────────┐
│ User sees notification:                                      │
│ ✅ "Form saved successfully!"                                │
│ File ID: a93a8a5b-...                                        │
│ Stored as: Khai_sinh_20251025_124533.docx                    │
└──────────────────────────────────────────────────────────────┘
```

### 6️⃣ **Người Dùng Ấn "📥 Download Form"** (Optional)

```
Nếu user muốn download form đã lưu, họ ấn download button:

Frontend:
├─ GET /api/v1/storage/download/079987654321/Khai_sinh_20251025_124533.docx
└─ Browser downloads file

Backend:
├─ Tìm file trong filesystem
├─ Read binary content
└─ Return FileResponse (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
```

---

## 📊 Thời Điểm Lưu File

| Thời Điểm                | Sự Kiện                               | Kết Quả               |
| ------------------------ | ------------------------------------- | --------------------- |
| **Người dùng ấn "Save"** | ✅ **File được lưu NGAY**             | Filesystem + Database |
| Người dùng ấn "Download" | ❌ Chỉ retrieve, không lưu thêm       | Tải về máy client     |
| Người dùng đóng form     | ❌ Không lưu (chỉ nếu bấm Save trước) | Không thay đổi        |

---

## 🔒 Storage Architecture (Hybrid: SQLite + FileSystem)

```
identifill_service/
└── data/
    ├── 📄 legalrag.db (SQLite database)
    │   ├── Table: cccd_users
    │   │   ├── scan_cccd (PK)
    │   │   ├── scan_ho_ten
    │   │   └── timestamps
    │   │
    │   └── Table: stored_forms
    │       ├── file_id (PK) - UUID
    │       ├── scan_cccd (FK)
    │       ├── form_name
    │       ├── file_name
    │       ├── file_size
    │       └── created_at
    │
    └── scanned_documents/
        ├── 079987654321/
        │   └── forms/
        │       └── Khai_sinh_20251025_124533.docx (202 bytes)
        │
        ├── 123456789012/
        │   └── forms/
        │       ├── Khai_tu_nhan_20251025_122858.docx
        │       └── request_20251025_122420.docx
        │
        └── [more CCCDs...]/
            └── forms/
```

---

## 🔑 Key Points

### ✅ File Được Lưu Khi:

1. ✅ Người dùng ấn **"💾 Save Form"** button
2. ✅ Frontend gửi POST request tới `/api/v1/storage/save`
3. ✅ Backend xác thực & tạo directory nếu chưa tồn tại
4. ✅ File được write vào filesystem
5. ✅ Metadata được save vào SQLite database

### ❌ File KHÔNG Được Lưu Khi:

- ❌ Người dùng chỉ xem form (không ấn Save)
- ❌ Người dùng ấn "Download" (chỉ retrieve)
- ❌ Người dùng đóng form mà không save

### 💾 Data Persistence:

- **Filesystem**: Binary .docx files tồn tại vĩnh viễn
- **Database**: Metadata tồn tại vĩnh viễn
- **Mounted Volume**: Docker volume `./identifill_service/data:/app/data` đảm bảo dữ liệu persist qua container restarts

---

## 🌐 API Endpoints Liên Quan

| Endpoint                                                   | Phương Thức | Mục Đích                 |
| ---------------------------------------------------------- | ----------- | ------------------------ |
| `/api/v1/storage/save`                                     | **POST**    | **Lưu form** (Save ngay) |
| `/api/v1/storage/list/{scan_cccd}`                         | GET         | Liệt kê các form đã lưu  |
| `/api/v1/storage/download/{scan_cccd}/{file_name}`         | GET         | Tải về form đã lưu       |
| `/api/v1/storage/delete/{scan_cccd}/{file_id}/{file_name}` | DELETE      | Xóa form đã lưu          |
| `/api/v1/storage/stats`                                    | GET         | Xem thống kê lưu trữ     |

---

## 📋 Request/Response Example

### ➡️ Save Form (Save ngay khi user ấn Save)

**Request:**

```http
POST /api/v1/storage/save
Content-Type: multipart/form-data

form_file: [binary data của Khai_sinh.docx]
scan_cccd: 079987654321
scan_ho_ten: Trần Thị Hà
form_name: Khai_sinh
```

**Response (200 OK):**

```json
{
  "success": true,
  "file_id": "a93a8a5b-1466-4f1f-a2ce-75c8892185b8",
  "file_name": "Khai_sinh_20251025_124533.docx",
  "message": "Form saved successfully"
}
```

### ⬇️ Download Form Later

**Request:**

```http
GET /api/v1/storage/download/079987654321/Khai_sinh_20251025_124533.docx
```

**Response (200 OK):**

```
[Binary .docx file content - 202 bytes]
Content-Disposition: attachment; filename="Khai_sinh_20251025_124533.docx"
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

---

## 🚀 Tóm Tắt

> **File được lưu NGAY KHI NGƯỜI DÙNG ẤN "SAVE FORM"**
>
> - ✅ Không phải chờ đến khi download
> - ✅ Lưu vào filesystem (data/scanned_documents/)
> - ✅ Lưu metadata vào database (legalrag.db)
> - ✅ Có thể retrieve/download bất cứ lúc nào sau đó
> - ✅ Persistent qua container restarts (Docker volumes)
