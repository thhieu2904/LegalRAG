# 🗓️ PROJECT ROADMAP & TIMELINE

## 📅 VISUAL TIMELINE

```
Week 1: Backend Implementation (Phase 1)
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Day 1 (2.5h):      Database + Service Setup        │
│ ├─ 1.1: Database.py             [████████░░] 30m   │
│ ├─ 1.2: StorageService.py       [████████░░] 45m   │
│ ├─ 1.3: Schemas.py              [██████░░░░] 15m   │
│ └─ 1.4: Config update           [██████░░░░] 10m   │
│                                                     │
│ Day 2 (1.5h):      API + Integration               │
│ ├─ 1.5: Create forms.py         [████████░░] 45m   │
│ ├─ 1.6: Update main.py          [██████░░░░] 20m   │
│ └─ 1.7: Testing                 [████████░░] 30m   │
│                                                     │
└─────────────────────────────────────────────────────┘

Week 2: Frontend Implementation (Phase 2)
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Day 1 (2h):        API + Hooks                      │
│ ├─ 2.1: API Service             [████████░░] 30m   │
│ └─ 2.2: Custom Hooks            [████████░░] 45m   │
│                                                     │
│ Day 2 (2h):        Components                       │
│ ├─ 2.3: UI Components           [██████░░░░] 90m   │
│ └─ 2.4: Dashboard Page          [██████░░░░] 45m   │
│                                                     │
│ Day 3 (1.5h):      Integration + Polish            │
│ ├─ 2.5: Admin Integration       [██████░░░░] 30m   │
│ ├─ 2.6: Styling                 [██████░░░░] 30m   │
│ └─ 2.7: Testing & QA            [██████░░░░] 45m   │
│                                                     │
└─────────────────────────────────────────────────────┘

Total: ~10-11 hours
```

---

## 🔄 WORKFLOW DIAGRAM

```
PHASE 1: BACKEND
═══════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────┐
│                    identifill_service/                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  app/core/database.py                                       │
│  ├─ Database class (SQLite)                                │
│  │  ├─ init_db() [cccd_users, stored_forms tables]          │
│  │  ├─ save_cccd_user()                                     │
│  │  ├─ add_form_record()                                    │
│  │  ├─ get_forms_by_cccd()                                  │
│  │  └─ get_database_stats()                                 │
│  └─ db = Database() [singleton]                            │
│                          ↓                                  │
│                                                              │
│  app/services/form_storage_service.py                       │
│  ├─ FormStorageService class                               │
│  │  ├─ save_form()      ┐                                  │
│  │  ├─ get_forms()      │─── Calls db methods              │
│  │  ├─ delete_form()    │                                  │
│  │  └─ get_stats()      ┘                                  │
│  └─ Manages filesystem: data/scanned_documents/            │
│                          ↓                                  │
│                                                              │
│  app/api/v1/forms.py                                        │
│  ├─ POST   /save          [saveForm]                       │
│  ├─ GET    /list/{cccd}   [listForms]                      │
│  ├─ GET    /download      [downloadForm]                   │
│  ├─ DELETE /delete        [deleteForm]                     │
│  └─ GET    /stats         [getStats]                       │
│                          ↓                                  │
│                                                              │
│  main.py                                                    │
│  └─ Include forms router                                   │
│     app.include_router(forms_router)                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘


DATA STORAGE
═══════════════════════════════════════════════════════════

data/
├─ legalrag.db [SQLite Database]
│  ├─ cccd_users (metadata)
│  │  ├─ scan_cccd (PK)
│  │  ├─ scan_ho_ten
│  │  └─ timestamps
│  │
│  └─ stored_forms (file tracking)
│     ├─ file_id (PK)
│     ├─ scan_cccd (FK)
│     ├─ form_name, file_name
│     └─ timestamps
│
└─ scanned_documents/ [File Storage]
   └─ {scan_cccd}/
      └─ forms/
         ├─ contract_20251025_103000.docx
         └─ request_20251025_145500.docx


PHASE 2: FRONTEND
═══════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────┐
│                       frontend/src/                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  api/form-storage-api.ts                                    │
│  ├─ saveForm()                                             │
│  ├─ listForms()                                            │
│  ├─ downloadForm()                                         │
│  ├─ deleteForm()                                           │
│  └─ getStats()                                             │
│         ↓ (Calls Backend API)                              │
│                                                              │
│  hooks/useFormStorage.ts                                    │
│  ├─ state: isLoading, error, forms, stats                 │
│  ├─ saveScanResult()                                       │
│  ├─ loadForms()                                            │
│  ├─ downloadForm()                                         │
│  ├─ deleteForm()                                           │
│  └─ loadStats()                                            │
│         ↓ (Used by components)                             │
│                                                              │
│  components/storage/                                        │
│  ├─ DocumentSearcher.tsx                                   │
│  │  └─ Input CCCD → onSearch callback                      │
│  │                                                          │
│  ├─ FormsList.tsx                                          │
│  │  └─ Display forms → Download/Delete actions            │
│  │                                                          │
│  ├─ StorageStats.tsx                                       │
│  │  └─ Show statistics cards                               │
│  │                                                          │
│  └─ StorageModal.tsx                                       │
│     └─ Confirm delete, view details                        │
│         ↓ (Composed into page)                             │
│                                                              │
│  pages/StorageManagement.tsx                               │
│  ├─ Main container                                         │
│  ├─ Orchestrates all components                            │
│  ├─ Handles state + callbacks                              │
│  └─ Manages routing                                        │
│         ↓ (Added to admin panel)                           │
│                                                              │
│  pages/AdminPanel.tsx (UPDATED)                            │
│  └─ New Tab: "📋 Stored Documents"                         │
│     └─ <StorageManagement />                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘


DATA FLOW
═══════════════════════════════════════════════════════════

1. SEARCH FORMS:
   User Input (CCCD)
   → DocumentSearcher
   → useFormStorage.loadForms()
   → formStorageAPI.listForms()
   → Backend GET /list/{cccd}
   → Database query
   → Return forms list
   → FormsList component

2. DOWNLOAD FORM:
   User Click "Download"
   → FormsList
   → useFormStorage.downloadForm()
   → formStorageAPI.downloadForm()
   → Backend GET /download/{cccd}/{filename}
   → Filesystem read
   → Browser download

3. DELETE FORM:
   User Click "Delete"
   → StorageModal confirm
   → useFormStorage.deleteForm()
   → formStorageAPI.deleteForm()
   → Backend DELETE /delete/{cccd}/{file_id}/{filename}
   → Filesystem delete
   → Database delete
   → Reload forms list

4. VIEW STATS:
   useFormStorage.loadStats()
   → formStorageAPI.getStats()
   → Backend GET /stats
   → Database aggregate query
   → StorageStats display
```

---

## 📊 DEPENDENCY DIAGRAM

```
PHASE 1 Dependencies:
┌─────────────────────────────────────────┐
│        config.py (Settings)             │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│        database.py (SQLite)             │
│  ← Needs: config.py for paths           │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│    form_storage_service.py              │
│  ← Needs: database.py for DB ops        │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│      forms.py (API Endpoints)           │
│  ← Needs: form_storage_service.py       │
│           schemas.py                    │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│    main.py (Application Entry)          │
│  ← Needs: forms.py router               │
└─────────────────────────────────────────┘


PHASE 2 Dependencies:
┌─────────────────────────────────────────┐
│   axios-config.ts (Backend Config)      │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│   form-storage-api.ts (API Service)     │
│  ← Needs: axios-config.ts               │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  useFormStorage.ts (Custom Hook)        │
│  ← Needs: form-storage-api.ts           │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
┌──────────────────┐  ┌──────────────────┐
│ FormsList.tsx    │  │ DocumentSearcher │
│ StorageStats.tsx │  │ StorageModal.tsx │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └─────────┬───────────┘
                   ↓
         ┌──────────────────────┐
         │StorageManagement.tsx │
         │ (Main Page)          │
         └────────┬─────────────┘
                  │
                  ↓
         ┌──────────────────────┐
         │ AdminPanel.tsx       │
         │ (Add Tab)            │
         └──────────────────────┘
```

---

## 🔧 BUILD ORDER (MUST FOLLOW THIS)

### PHASE 1 BUILD ORDER (Sequential):

1. ✅ Update `config.py` (no dependencies)
2. ✅ Create `database.py` (depends on config)
3. ✅ Create `form_storage_service.py` (depends on database)
4. ✅ Update `schemas.py` (independent)
5. ✅ Create `forms.py` (depends on service + schemas)
6. ✅ Update `main.py` (depends on forms router)
7. ✅ Test all (depends on all above)

### PHASE 2 BUILD ORDER (Sequential):

1. ✅ Create `form-storage-api.ts` (independent)
2. ✅ Create `useFormStorage.ts` (depends on API)
3. ✅ Create components (depend on hook)
4. ✅ Create `StorageManagement.tsx` (depends on components)
5. ✅ Update `AdminPanel.tsx` (depends on management)
6. ✅ Style & polish
7. ✅ Test all

---

## ⏱️ TIME ESTIMATE

```
PHASE 1 - BACKEND
├─ 1.1: Database           30 min    ████░
├─ 1.2: Service            45 min    ██████░
├─ 1.3: Schemas            15 min    ██░
├─ 1.4: Config             10 min    █░
├─ 1.5: API Endpoints      45 min    ██████░
├─ 1.6: Main.py            20 min    ███░
├─ 1.7: Testing            30 min    ████░
└─ SUBTOTAL                195 min   ≈ 3.25 hours

PHASE 2 - FRONTEND
├─ 2.1: API Service        30 min    ████░
├─ 2.2: Hooks              45 min    ██████░
├─ 2.3: Components         90 min    ██████████
├─ 2.4: Dashboard          45 min    ██████░
├─ 2.5: Admin Integration  30 min    ████░
├─ 2.6: Styling            30 min    ████░
├─ 2.7: Testing            45 min    ██████░
└─ SUBTOTAL                315 min   ≈ 5.25 hours

TOTAL PROJECT: 510 min ≈ 8.5 hours
```

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Complete When:

- ✅ `data/legalrag.db` exists with correct schema
- ✅ All 5 endpoints respond with 200 OK
- ✅ Files saved to `data/scanned_documents/`
- ✅ Database records created correctly
- ✅ cURL tests all pass
- ✅ No console errors in Python

### Phase 2 Complete When:

- ✅ New tab visible in Admin Panel
- ✅ Can search forms by CCCD
- ✅ Can download .docx files
- ✅ Can delete forms
- ✅ Stats show correct data
- ✅ Responsive on mobile/desktop
- ✅ No console errors in browser

---

## 🚀 READY TO START?

**Next: Begin with Task 1.1** 🎯

When you complete each task, check off the corresponding checkbox in:
📋 `plan/TODO_CHECKLIST_DETAILED.md`

Good luck! 💪
