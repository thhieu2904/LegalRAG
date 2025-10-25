# Phase 2 - Visual Architecture & Data Flow

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│                     Port 3000 / Vite Dev                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         FormRenderer Component (450 lines)              │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  1. Display Form HTML (from RAG service)                │  │
│  │  2. Pre-fill fields with CCCD data                      │  │
│  │  3. Render download button                              │  │
│  │     └─> Calls handleDownloadForm on click               │  │
│  │  4. Show notifications (success/error/info)             │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ▲                                    │                  │
│         │                                    ▼                  │
│  ┌──────────────────┐             ┌──────────────────────┐    │
│  │ useFormDownload  │             │  State Management    │    │
│  │  Hook (84 lines) │             ├──────────────────────┤    │
│  ├──────────────────┤             │ • notification       │    │
│  │ • downloadForm() │◄────────────│ • downloadLoading    │    │
│  │ • loading        │             │ • htmlContent        │    │
│  │ • error          │             │ • formMetadata       │    │
│  └──────────────────┘             └──────────────────────┘    │
│         │                                    ▲                  │
│         └────────────────────────────────────┘                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Storage API Service (80 lines - axios)             │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • saveFormToStorage()                                    │  │
│  │ • listSavedForms()                                       │  │
│  │ • downloadSavedForm()                                    │  │
│  │ • deleteSavedForm()                                      │  │
│  │ • getStorageStats()                                      │  │
│  │ • checkStorageHealth()                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                                   │
         │ HTTP                              │ HTTP
         ▼                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  RAG Service (Port 8000)                              │   │
│  │  GET /forms/file/{formPath}                           │   │
│  │  └─> Returns: Binary .docx file                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                    │
│                           ▼                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Identifill Service (Port 8002)                       │   │
│  │  POST /api/v1/storage/save                            │   │
│  │  ├─> Receive FormData (file + CCCD + metadata)        │   │
│  │  ├─> Validate CCCD (12 digits)                        │   │
│  │  ├─> Create directory:                                │   │
│  │  │   data/scanned_documents/{CCCD}/forms/             │   │
│  │  ├─> Save file to filesystem                          │   │
│  │  ├─> Save metadata to SQLite                          │   │
│  │  └─> Return success (200)                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                    │
│                           ▼                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  SQLite Database (legalrag.db)                        │   │
│  │  ├─ Table: cccd_users                                 │   │
│  │  │  (scan_cccd, scan_ho_ten, metadata)                │   │
│  │  ├─ Table: stored_forms                               │   │
│  │  │  (form_id, scan_cccd, filename, file_size,         │   │
│  │  │   created_at, updated_at)                          │   │
│  │  └─ Index: scan_cccd (for fast lookup)                │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Filesystem Storage                                   │   │
│  │  data/scanned_documents/                              │   │
│  │  ├─ 079987654321/forms/                               │   │
│  │  │  ├─ Khai_sinh.docx                                 │   │
│  │  │  └─ Hoa_don.docx                                   │   │
│  │  └─ 079123456789/forms/                               │   │
│  │     └─ Giay_chung_chi.docx                            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow - Download Process

```
USER CLICKS DOWNLOAD BUTTON
         │
         ▼
┌─────────────────────────────────────────────┐
│ handleDownloadForm() callback executes      │
├─────────────────────────────────────────────┤
│ • Get form path, CCCD, user name            │
│ • Show "Saving..." notification             │
│ • Extract data from component state         │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ downloadForm() hook (3-step process)        │
├─────────────────────────────────────────────┤
│                                             │
│ STEP 1: Fetch Form from RAG                 │
│ ────────────────────────────────────────    │
│ GET /forms/file/collectionId/docId/file    │
│        │                                   │
│        ▼                                   │
│ Response: Binary DOCX file                 │
│ (202 bytes for Khai_sinh.docx)             │
│                                             │
│ STEP 2: Save to Backend Storage             │
│ ────────────────────────────────────────    │
│ POST /api/v1/storage/save                  │
│ Body: FormData                              │
│   • form_file: Blob(DOCX data)              │
│   • scan_cccd: "079987654321"               │
│   • scan_ho_ten: "Nguyễn Văn A"             │
│   • form_name: "Khai_sinh"                  │
│   • filename: "Khai_sinh.docx"              │
│        │                                   │
│        ▼                                   │
│ Response: {                                 │
│   success: true,                            │
│   message: "Form saved successfully",       │
│   form_path: "..."                          │
│ }                                           │
│                                             │
│ STEP 3: Trigger Browser Download            │
│ ────────────────────────────────────────    │
│ Create Blob URL from file data              │
│ Create <a> element with download            │
│ Click to download                           │
│ Revoke Blob URL                             │
│        │                                   │
│        ▼                                   │
│ File downloaded to ~/Downloads/             │
│                                             │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ Backend Processing (Storage Service)        │
├─────────────────────────────────────────────┤
│ 1. Validate CCCD format (12 digits)         │
│ 2. Create directory structure:              │
│    data/scanned_documents/                  │
│    └─ 079987654321/forms/                   │
│ 3. Save file to filesystem                  │
│ 4. Create/Update metadata in SQLite         │
│ 5. Return success response                  │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ Frontend Success Handler                    │
├─────────────────────────────────────────────┤
│ • Show "✅ Downloaded and saved!"           │
│ • Update button state (normal)              │
│ • Auto-clear notification (3 seconds)       │
└─────────────────────────────────────────────┘
         │
         ▼
DOWNLOAD COMPLETE ✅
  • File in Downloads folder
  • Metadata in SQLite
  • File in Filesystem
```

---

## 🎨 UI Components

```
┌────────────────────────────────────────────────────────────┐
│  FormRenderer Component                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ NOTIFICATION (if showing)                            │ │
│  │ ┌──────────────────────────────────────────────────┐ │ │
│  │ │ ✅ Biểu mẫu đã được tải xuống và lưu!           │ │ │
│  │ │ (slides down, auto-clears in 3s)               │ │ │
│  │ └──────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ FORM HEADER                                          │ │
│  │ ┌─────────────────────────────────────────────────┐ │ │
│  │ │ Left Section          │    Right Section        │ │ │
│  │ │ 📋 Khai_sinh.docx     │  ┌──────────────────┐  │ │ │
│  │ │ collections/doc123    │  │ ⬇️ Tải xuống    │  │ │ │
│  │ │                       │  │ (hover: darker)  │  │ │ │
│  │ │                       │  └──────────────────┘  │ │ │
│  │ └─────────────────────────────────────────────────┘ │ │
│  │ (Layout: Flexbox, space-between, responsive)        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ FORM CONTENT (A4-sized)                              │ │
│  │ ┌──────────────────────────────────────────────────┐ │ │
│  │ │                                                  │ │ │
│  │ │  KHAI SINH Ş - DECLARATION OF BIRTH              │ │ │
│  │ │                                                  │ │ │
│  │ │  Ngày sinh: ______________ (pre-filled)         │ │ │
│  │ │  Họ tên: Nguyễn Văn A (pre-filled)              │ │ │
│  │ │  Địa chỉ: ______________________________        │ │ │
│  │ │                                                  │ │ │
│  │ │  Chữ ký: _______________  Ngày: _______        │ │ │
│  │ │                                                  │ │ │
│  │ └──────────────────────────────────────────────────┘ │ │
│  │ (A4 ratio: 1:1.414, responsive sizing)             │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ DEBUG INFO (development only)                        │ │
│  │ ┌──────────────────────────────────────────────────┐ │ │
│  │ │ 🔧 Debug Info ▼                                 │ │ │
│  │ │ {                                                │ │ │
│  │ │   "form_filename": "Khai_sinh.docx",            │ │ │
│  │ │   "collection_id": "collections",               │ │ │
│  │ │   "doc_id": "doc123"                            │ │ │
│  │ │ }                                                │ │ │
│  │ └──────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📱 Responsive Layout

```
DESKTOP (> 768px)
┌─────────────────────────────────────┐
│ 📋 Form Name        [⬇️ Download]  │
│ path/to/form                        │
├─────────────────────────────────────┤
│                                     │
│  [FORM CONTENT]                     │
│                                     │
└─────────────────────────────────────┘

MOBILE (< 768px)
┌──────────────────────┐
│ 📋 Form Name        │
│ path/to/form        │
├──────────────────────┤
│ [⬇️ Download]       │ (full width)
├──────────────────────┤
│                      │
│  [FORM CONTENT]      │
│                      │
└──────────────────────┘
```

---

## 🔄 State Management

```
Component State:
┌──────────────────────────────────────────────────────┐
│ const [htmlContent, setHtmlContent] = useState("")   │
│ const [loading, setLoading] = useState(true)         │
│ const [error, setError] = useState("")               │
│ const [formMetadata, setFormMetadata] = useState()   │
│                                                      │
│ Hook State:                                          │
│ const { downloadForm, loading, error } = useHook()  │
│                                                      │
│ Notification State:                                  │
│ const [notification, setNotification] = useState()   │
│ {                                                    │
│   type: "success" | "error" | "info",               │
│   message: string                                    │
│ }                                                    │
│                                                      │
│ Ref State:                                           │
│ const reactRootsRef = useRef(new Map())             │
│ const isHydratedRef = useRef(false)                 │
│ const formContentRef = useRef()                     │
│ const htmlSetRef = useRef(false)                    │
└──────────────────────────────────────────────────────┘
```

---

## 🎯 Event Flow

```
User Action → Component Update → API Call → Backend Processing → UI Update

DOWNLOAD BUTTON CLICK
    │
    ▼
handleDownloadForm() {
    • setNotification("info")
    • Get form metadata
    • Call downloadForm()
}
    │
    ├─► Success Path
    │   ├─> Blob created
    │   ├─> Download triggered
    │   ├─> setNotification("success")
    │   └─> setTimeout → clear notification
    │
    └─► Error Path
        ├─> Catch error
        ├─> setNotification("error")
        └─> User sees error message
```

---

## 📝 CSS Class Hierarchy

```
.form-renderer                          (main container)
├─ .form-notification                   (notification)
│  ├─ .form-notification-success        (variant)
│  ├─ .form-notification-error          (variant)
│  └─ .form-notification-info           (variant)
│
├─ .form-header                         (header)
│  ├─ .form-header-left                 (left section)
│  │  ├─ .form-title                    (title)
│  │  └─ .form-path                     (path)
│  └─ .form-header-actions              (right section)
│     └─ .download-button               (button)
│
├─ .form-content                        (form body)
│  ├─ p.center                          (alignment)
│  ├─ p.right
│  ├─ p.left
│  ├─ p.justify
│  ├─ h1, h2, h3                        (headers)
│  ├─ table, tr, td                     (tables)
│  └─ [editable placeholders]           (hydrated components)
│
├─ .form-debug                          (debug section)
│  ├─ details
│  └─ summary
│
├─ .form-renderer.loading               (loading state)
│  ├─ .loading-spinner
│  └─ p
│
└─ .form-renderer.error                 (error state)
   └─ .error-content
```

---

## 🔗 API Endpoints Summary

```
RAG SERVICE (Port 8000)
GET /forms/file/{collectionId}/{docId}/{filename}
    └─> Returns: Binary DOCX file

IDENTIFILL SERVICE (Port 8002)
POST /api/v1/storage/save
    ├─> Body: FormData (file + metadata)
    └─> Returns: { success, message, form_path }

GET /api/v1/storage/list/{scan_cccd}
    └─> Returns: List of saved forms

GET /api/v1/storage/download/{scan_cccd}/{file_id}
    └─> Returns: File for download

DELETE /api/v1/storage/delete/{scan_cccd}/{file_id}
    └─> Returns: { success, message }

GET /api/v1/storage/stats
    └─> Returns: Storage statistics

GET /api/v1/storage/health
    └─> Returns: Service health check
```

---

**Visual Documentation Complete** ✅

This architecture supports:

- ✅ Scalability (modular components)
- ✅ Maintainability (clear separation)
- ✅ Extensibility (easy to add features)
- ✅ Reliability (error handling)
- ✅ Performance (optimized flow)
