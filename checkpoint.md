## 📊 PHÂN TÍCH LẠI

### **1. Phân quyền Service**

| Service                                                                                                                                                                         | Vai trò                 | Quyền                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------------------------- |
| [query-service](vscode-file://vscode-app/c:/Users/thhieu/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)      | User facing - Chat, Q&A | **Read-only** forms metadata (từ DB)      |
| [admin-service](vscode-file://vscode-app/c:/Users/thhieu/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)      | Admin facing - Quản lý  | **Full CRUD** - bao gồm xem forms đã điền |
| [identifill-service](vscode-file://vscode-app/c:/Users/thhieu/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html) | Internal - Xử lý form   | Render, Fill, Scan CCCD                   |
| [storage-service](vscode-file://vscode-app/c:/Users/thhieu/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)    | Internal - File storage | Upload/Download files từ MinIO            |

### **2. Lưu trữ Form đã điền - Đơn giản hóa**

**Thay vì tạo bảng phức tạp** , lưu trực tiếp vào MinIO với naming convention:

- MinIO Structure:
  user*forms/
  ├── {session_id}/ # Nhóm theo session
  │ ├── {cccd}*{form-name}.docx # Nếu có CCCD
  │ └── {form-name}.docx # Nếu không có CCCD

**Ví dụ:**

- user_forms/
  ├── 20251130_0001/
  │ ├── 079203012345_to-khai-khai-sinh.docx
  │ └── 079203012345_giay-uy-quyen.docx
  ├── 20251130_0002/
  │ └── to-khai-ket-hon.docx # Không có CCCD

**Ưu điểm:**

- ✅ Không cần bảng mới trong PostgreSQL
- ✅ Tìm kiếm theo tên file dễ dàng (list files với prefix)
- ✅ Admin-service có thể list/download trực tiếp từ storage-service
- ✅ Đơn giản, không over-engineer

---

## 🔄 FLOW MỚI (ĐIỀU CHỈNH)

┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND │
│ User Chat → Forms trong sourceList → Click "Điền form" │
└──────┬──────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│ QUERY-SERVICE (8002) │
│ • GET /forms/render → Forward to identifill → Return HTML │
│ • POST /forms/fill → Forward to identifill → Return DOCX │
│ • POST /forms/save → Forward to storage (user_forms/{session}/...)│
│ • ❌ KHÔNG có endpoint xem forms đã điền │
└──────┬──────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│ IDENTIFILL-SERVICE (8005) │
│ • POST /render → Download template từ storage → DOCX → HTML │
│ • POST /fill → Fill placeholders → Return DOCX bytes │
│ • POST /cccd/scan → Parse QR → Return scan data │
└─────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│ STORAGE-SERVICE (8010) │
│ • GET /download?file_path=forms/{doc_id}/... (Template) │
│ • POST /upload?folder=user_forms/{session_id} (Filled form) │
│ • GET /list?prefix=user_forms/ (For admin) │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ADMIN-SERVICE (8001) │
│ • GET /admin/user-forms → List từ storage (user_forms/\*) │
│ • GET /admin/user-forms/{session_id} → List forms của session │
│ • GET /admin/user-forms/download?path=... → Download form đã điền │
│ • DELETE /admin/user-forms/{path} → Xoá form đã điền │
└─────────────────────────────────────────────────────────────────────┘

---

## 📋 KẾ HOẠCH IMPLEMENTATION

### **Phase 1: done**

### **Phase 2: done**

### **Phase 3: done**

### **Phase 4: Không cần sửa Schema**

- Không thêm bảng mới
- Dùng MinIO folder structure làm "database"

---

## ❓ XÁC NHẬN CUỐI

1. **Naming convention:** [{session*id}/{cccd}*{form-name}.docx](vscode-file://vscode-app/c:/Users/thhieu/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html) - OK?
2. **Về CCCD trong tên file:**
   - Nếu có scan CCCD → `079203012345_to-khai-khai-sinh.docx`
   - Nếu không có → `to-khai-khai-sinh.docx`
   - Bạn có muốn thêm timestamp không? VD: `079203012345_to-khai-khai-sinh_20251130_1430.docx`
3. **Bắt đầu implement Phase 1?** (Tạo identifill_service mới)
