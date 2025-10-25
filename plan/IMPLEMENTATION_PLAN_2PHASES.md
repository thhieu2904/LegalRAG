# 📋 IMPLEMENTATION PLAN - 2 PHASES

## 📍 OVERVIEW

```
PHASE 1: Backend Infrastructure (SQLite + File System)
├─ Database setup
├─ Form storage service
├─ API endpoints
└─ Integration với Identifill Service

PHASE 2: Frontend Dashboard (Admin Panel)
├─ New tab "Stored Documents"
├─ Display list forms by CCCD
├─ Download/Delete operations
├─ Statistics & Management
└─ Real-time sync
```

---

# 🔵 PHASE 1: BACKEND INFRASTRUCTURE

## 📌 Goals

- ✅ Setup SQLite database
- ✅ Create form storage service
- ✅ Create API endpoints
- ✅ Test locally

## 📊 Scope

- **Time**: ~2-3 hours
- **Files**: 5 new files + 2 updates
- **Testing**: cURL + Postman

---

## 📝 TODO LIST - PHASE 1

### Task 1.1: Create Database Layer

**Subtasks:**

- [ ] Create `identifill_service/app/core/database.py`
  - [ ] Database class with SQLite connection
  - [ ] init_db() with table creation (cccd_users, stored_forms)
  - [ ] CRUD methods: save_cccd_user, add_form_record, get_forms_by_cccd
  - [ ] delete_form_record, get_database_stats
  - [ ] Singleton instance: `db`
- [ ] Test database creation & schema

**Files to create:**

- `identifill_service/app/core/database.py` (220 lines)

**Output:**

- ✅ `data/legalrag.db` created
- ✅ Tables: cccd_users, stored_forms with indexes

---

### Task 1.2: Create Form Storage Service

**Subtasks:**

- [ ] Create `identifill_service/app/services/form_storage_service.py`
  - [ ] FormStorageService class
  - [ ] save_form() - lưu .docx + track DB
  - [ ] get_forms() - query từ DB
  - [ ] download_form() - lấy file từ filesystem
  - [ ] delete_form() - xóa file + DB record
  - [ ] get_stats() - statistics
- [ ] Integration với Database class

**Files to create:**

- `identifill_service/app/services/form_storage_service.py` (180 lines)

**Output:**

- ✅ Directory structure: `data/scanned_documents/{scan_cccd}/forms/`
- ✅ File storage working with DB tracking

---

### Task 1.3: Create API Endpoints

**Subtasks:**

- [ ] Create/Update `identifill_service/app/api/v1/forms.py`
  - [ ] POST `/save` - save form with multipart upload
  - [ ] GET `/list/{scan_cccd}` - list all forms for CCCD
  - [ ] GET `/download/{scan_cccd}/{file_name}` - download file
  - [ ] DELETE `/delete/{scan_cccd}/{file_id}/{file_name}` - delete form
  - [ ] GET `/stats` - get storage statistics
  - [ ] Error handling & logging
- [ ] Request/Response models in schemas.py

**Files to create/update:**

- `identifill_service/app/api/v1/forms.py` (170 lines) - NEW
- `identifill_service/app/models/schemas.py` - ADD models

**Output:**

- ✅ 5 endpoints tested & working
- ✅ Proper HTTP responses & error codes

---

### Task 1.4: Update Main Application

**Subtasks:**

- [ ] Update `identifill_service/main.py`
  - [ ] Import forms router
  - [ ] Include router: `app.include_router(forms_router, ...)`
  - [ ] Add startup event to initialize DB
  - [ ] Add logging for startup
- [ ] Update `identifill_service/app/core/config.py`
  - [ ] Add STORAGE_DIR & DATABASE_PATH

**Files to update:**

- `identifill_service/main.py` (add 10 lines)
- `identifill_service/app/core/config.py` (add 5 lines)

**Output:**

- ✅ Server starts with DB initialization
- ✅ Forms endpoints available

---

### Task 1.5: Integration & Testing

**Subtasks:**

- [ ] Test database creation
  ```bash
  sqlite3 data/legalrag.db ".tables"
  sqlite3 data/legalrag.db ".schema"
  ```
- [ ] Test save endpoint
  ```bash
  curl -X POST -F "form_file=@test.docx" \
    -F "scan_cccd=079123456789" \
    -F "scan_ho_ten=Nguyen Van A" \
    -F "form_name=contract" \
    http://localhost:8002/api/v1/forms/save
  ```
- [ ] Test list endpoint
  ```bash
  curl http://localhost:8002/api/v1/forms/list/079123456789
  ```
- [ ] Test stats endpoint
  ```bash
  curl http://localhost:8002/api/v1/forms/stats
  ```
- [ ] Verify file structure created
  ```bash
  tree data/scanned_documents/
  ```

**Verification:**

- ✅ Database file exists: `data/legalrag.db`
- ✅ Folder structure: `data/scanned_documents/079123456789/forms/`
- ✅ Files saved with correct naming
- ✅ Database records created
- ✅ All endpoints return correct responses

---

## 📁 Phase 1 File Structure

```
identifill_service/
├── app/
│   ├── api/v1/
│   │   ├── cccd.py (existing)
│   │   └── forms.py ⭐ NEW
│   ├── core/
│   │   ├── config.py (UPDATE)
│   │   └── database.py ⭐ NEW
│   ├── models/
│   │   └── schemas.py (UPDATE)
│   ├── services/
│   │   └── form_storage_service.py ⭐ NEW
│   └── __init__.py
├── main.py (UPDATE)
└── requirements.txt (no change)

data/ (AUTO-CREATED)
├── legalrag.db ⭐ SQLite
└── scanned_documents/
    └── {scan_cccd}/forms/*.docx
```

---

# 🟢 PHASE 2: FRONTEND DASHBOARD

## 📌 Goals

- ✅ Add new "Stored Documents" tab in Admin Panel
- ✅ Display forms by CCCD
- ✅ Download/Delete functionality
- ✅ Statistics & Management UI

## 📊 Scope

- **Time**: ~3-4 hours
- **Files**: 6 new files + 1 update
- **Components**: List, History, Stats, Modal

---

## 📝 TODO LIST - PHASE 2

### Task 2.1: Create API Services

**Subtasks:**

- [ ] Create `frontend/src/api/form-storage-api.ts`
  - [ ] saveForm() - POST /save
  - [ ] listForms() - GET /list/{cccd}
  - [ ] downloadForm() - GET /download/{cccd}/{file_name}
  - [ ] deleteForm() - DELETE /delete/{cccd}/{file_id}/{file_name}
  - [ ] getStats() - GET /stats
  - [ ] Error handling
- [ ] Add request/response types

**Files to create:**

- `frontend/src/api/form-storage-api.ts` (180 lines)

**Output:**

- ✅ Type-safe API calls
- ✅ Error handling

---

### Task 2.2: Create Custom Hooks

**Subtasks:**

- [ ] Create `frontend/src/hooks/useFormStorage.ts`
  - [ ] useSaveForm() - save form
  - [ ] useLoadForms() - list forms
  - [ ] useDownloadForm() - download
  - [ ] useDeleteForm() - delete
  - [ ] useFormStats() - get stats
  - [ ] State management (loading, error)
- [ ] Handle async operations with proper error states

**Files to create:**

- `frontend/src/hooks/useFormStorage.ts` (200 lines)

**Output:**

- ✅ Reusable hooks
- ✅ Loading/error states

---

### Task 2.3: Create UI Components

**Subtasks:**

#### 2.3.1: FormsList Component

- [ ] Create `frontend/src/components/storage/FormsList.tsx`
  - [ ] Display forms in table/grid
  - [ ] Show: form_name, created_at, file_size
  - [ ] Actions: download, delete, preview
  - [ ] Empty state handling
  - [ ] Loading skeleton

#### 2.3.2: StorageStats Component

- [ ] Create `frontend/src/components/storage/StorageStats.tsx`
  - [ ] Total users, total forms, storage used
  - [ ] Visual progress bar
  - [ ] Stats cards

#### 2.3.3: DocumentSearcher Component

- [ ] Create `frontend/src/components/storage/DocumentSearcher.tsx`
  - [ ] Input: CCCD number
  - [ ] Search button
  - [ ] Auto-complete (recent CCCDs)
  - [ ] Error handling

#### 2.3.4: StorageModal Component

- [ ] Create `frontend/src/components/storage/StorageModal.tsx`
  - [ ] Modal for confirm delete
  - [ ] Modal for view details
  - [ ] Modal for upload new form

**Files to create:**

- `frontend/src/components/storage/FormsList.tsx` (200 lines)
- `frontend/src/components/storage/StorageStats.tsx` (120 lines)
- `frontend/src/components/storage/DocumentSearcher.tsx` (150 lines)
- `frontend/src/components/storage/StorageModal.tsx` (120 lines)

**Output:**

- ✅ Reusable UI components
- ✅ Responsive design

---

### Task 2.4: Create Storage Dashboard

**Subtasks:**

- [ ] Create `frontend/src/pages/StorageManagement.tsx`
  - [ ] Main container component
  - [ ] Combine: Searcher + FormsList + Stats
  - [ ] State management
  - [ ] Refresh functionality
  - [ ] Breadcrumb navigation

**Files to create:**

- `frontend/src/pages/StorageManagement.tsx` (200 lines)

**Output:**

- ✅ Complete page ready

---

### Task 2.5: Integration with Admin Service

**Subtasks:**

- [ ] Update `frontend/src/pages/AdminPanel.tsx` (or similar)
  - [ ] Add new tab "Stored Documents"
  - [ ] Tab routing to StorageManagement
  - [ ] Update nav/sidebar
- [ ] Update routing if needed
  - [ ] Add route: `/admin/storage` or `/storage`
- [ ] Update navigation component
  - [ ] Add link in sidebar

**Files to update:**

- `frontend/src/pages/AdminPanel.tsx` - ADD tab
- `frontend/src/App.tsx` - ADD route (if needed)
- Navigation component - ADD link

**Output:**

- ✅ New tab visible in Admin Panel
- ✅ Navigation working

---

### Task 2.6: Styling & Polish

**Subtasks:**

- [ ] Create `frontend/src/styles/storage.css`
  - [ ] Table styles
  - [ ] Modal styles
  - [ ] Responsive design
  - [ ] Dark mode support
- [ ] Add Tailwind classes (if using Tailwind)
- [ ] Test responsive on mobile/tablet
- [ ] Accessibility checks

**Files to create:**

- `frontend/src/styles/storage.css` (150 lines)

**Output:**

- ✅ Professional looking UI
- ✅ Mobile responsive

---

### Task 2.7: Testing & Optimization

**Subtasks:**

- [ ] Test save form flow
  - [ ] Upload form → Verify saved in DB
  - [ ] Check file in filesystem
  - [ ] Verify metadata in DB
- [ ] Test list forms
  - [ ] Load same CCCD twice → should be same
  - [ ] Check performance
- [ ] Test download
  - [ ] Download form → should open correctly
  - [ ] Verify file integrity
- [ ] Test delete
  - [ ] Delete form → verify removed from DB & filesystem
  - [ ] Check stats updated
- [ ] UI/UX testing
  - [ ] All buttons working
  - [ ] Error messages clear
  - [ ] Loading states visible
- [ ] Performance
  - [ ] List 100+ forms → still fast
  - [ ] Large file download → no timeout

**Verification:**

- ✅ All features working
- ✅ No console errors
- ✅ Responsive on all devices
- ✅ Performance acceptable

---

## 📁 Phase 2 File Structure

```
frontend/src/
├── api/
│   └── form-storage-api.ts ⭐ NEW
├── components/
│   └── storage/ ⭐ NEW
│       ├── FormsList.tsx
│       ├── StorageStats.tsx
│       ├── DocumentSearcher.tsx
│       └── StorageModal.tsx
├── hooks/
│   └── useFormStorage.ts ⭐ NEW
├── pages/
│   ├── AdminPanel.tsx (UPDATE)
│   └── StorageManagement.tsx ⭐ NEW
├── styles/
│   └── storage.css ⭐ NEW
└── App.tsx (UPDATE if needed)
```

---

# 📅 TIMELINE & EFFORT

## Phase 1: Backend (2-3 hours)

| Task             | Duration      | Notes                        |
| ---------------- | ------------- | ---------------------------- |
| 1.1: Database    | 30 min        | Straightforward SQLite setup |
| 1.2: Service     | 45 min        | File ops + DB integration    |
| 1.3: API         | 45 min        | FastAPI endpoints            |
| 1.4: Integration | 20 min        | Update main + config         |
| 1.5: Testing     | 30 min        | cURL + Postman tests         |
| **TOTAL**        | **2.5 hours** |                              |

## Phase 2: Frontend (3-4 hours)

| Task             | Duration       | Notes            |
| ---------------- | -------------- | ---------------- |
| 2.1: API Service | 30 min         | Axios setup      |
| 2.2: Hooks       | 45 min         | React hooks      |
| 2.3: Components  | 90 min         | 4 components     |
| 2.4: Dashboard   | 45 min         | Main container   |
| 2.5: Integration | 30 min         | Admin panel tab  |
| 2.6: Styling     | 30 min         | CSS + responsive |
| 2.7: Testing     | 45 min         | E2E testing      |
| **TOTAL**        | **3.75 hours** |                  |

---

## 🎯 TOTAL PROJECT: ~6 hours

---

# 🚀 STARTUP COMMANDS

## Phase 1: Backend Startup

```bash
# Terminal 1: Identifill Service
cd identifill_service
conda activate identifill_env
python main.py
# Server starts at http://localhost:8002
# Database created at data/legalrag.db
```

## Phase 2: Full Startup

```bash
# Terminal 1: Frontend
cd frontend
npm run dev
# App at http://localhost:5173

# Terminal 2: Identifill Service
cd identifill_service
conda activate identifill_env
python main.py
# API at http://localhost:8002

# Terminal 3: Admin Service (if needed)
cd admin_service
python main.py
# API at http://localhost:8001
```

---

# ✅ ACCEPTANCE CRITERIA

## Phase 1

- [ ] Database file created and schema correct
- [ ] All 5 endpoints working via cURL
- [ ] Files saved in correct directory structure
- [ ] Database records created correctly
- [ ] Stats endpoint shows accurate data
- [ ] Logging clear and informative

## Phase 2

- [ ] New tab visible in Admin Panel
- [ ] Can search by CCCD number
- [ ] List forms displays correctly
- [ ] Can download form successfully
- [ ] Can delete form (removes from DB + filesystem)
- [ ] Stats display correctly
- [ ] UI responsive on mobile/desktop
- [ ] Error messages clear and helpful
- [ ] No console errors
- [ ] Performance acceptable (< 1s load for 50 forms)

---

# 📊 DELIVERABLES CHECKLIST

## Phase 1 Deliverables

- [x] Database layer with SQLite
- [x] Form storage service
- [x] API endpoints (5 total)
- [x] Configuration updates
- [x] Integration with main app
- [x] Test documentation

## Phase 2 Deliverables

- [x] API service client
- [x] Custom React hooks
- [x] 4 UI components (List, Stats, Searcher, Modal)
- [x] Main dashboard page
- [x] Integration with Admin Panel
- [x] Styling & responsive design
- [x] Test results

---

# 🔍 KEY POINTS

## Backend Decisions

✅ SQLite for metadata tracking
✅ File system for binary storage
✅ Hybrid approach for simplicity
✅ Auto-create directory structure
✅ Transaction support in DB

## Frontend Decisions

✅ TypeScript for type safety
✅ Custom hooks for reusability
✅ Component composition pattern
✅ Responsive Tailwind CSS
✅ Error handling & loading states

---

# 📞 SUPPORT

## If Issues:

**Backend Issues:**

```bash
# Check database
sqlite3 data/legalrag.db ".tables"

# Check filesystem
ls -la data/scanned_documents/

# Check logs
# See console output from Python service
```

**Frontend Issues:**

```bash
# Check API calls
# Browser DevTools → Network tab

# Check state
# Browser DevTools → React DevTools extension

# Check errors
# Browser DevTools → Console tab
```

---

**Ready to start? Let's begin with Phase 1! 🚀**
