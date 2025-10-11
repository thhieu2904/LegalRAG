# Phase 3 UI Flow - Visual Guide

## 🎨 User Interface Changes

### Before Phase 3 (View Only)

```
┌─────────────────────────────────────────────────────────────┐
│ Questions Manager                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Collections → Documents → Questions (READ ONLY)            │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📄 Câu hỏi chính                                      │ │
│  │ ────────────────────────────────────────────────────  │ │
│  │ Luật Doanh nghiệp có những quy định gì?              │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📚 Biến thể câu hỏi (5)                              │ │
│  │ ────────────────────────────────────────────────────  │ │
│  │ 1. Quy định về doanh nghiệp là gì?                   │ │
│  │ 2. Luật Doanh nghiệp nói về điều gì?                 │ │
│  │ 3. Nội dung chính của Luật DN?                       │ │
│  │ 4. Luật DN có gì đặc biệt?                           │ │
│  │ 5. Tìm hiểu về Luật Doanh nghiệp                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ❌ NO EDIT FUNCTIONALITY                                  │
└─────────────────────────────────────────────────────────────┘
```

---

### After Phase 3 (View + Edit Mode)

#### View Mode (Default)

```
┌─────────────────────────────────────────────────────────────┐
│ Questions Manager                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Collections → Documents → Questions                        │
│                                                             │
│                                    ┌─────────────────────┐  │
│                                    │ ✏️  Chỉnh sửa      │  │ ← NEW BUTTON
│                                    └─────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📄 Câu hỏi chính                                      │ │
│  │ ────────────────────────────────────────────────────  │ │
│  │ Luật Doanh nghiệp có những quy định gì?              │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📚 Biến thể câu hỏi (5)                              │ │
│  │ ────────────────────────────────────────────────────  │ │
│  │ 1. Quy định về doanh nghiệp là gì?                   │ │
│  │ 2. Luật Doanh nghiệp nói về điều gì?                 │ │
│  │ 3. Nội dung chính của Luật DN?                       │ │
│  │ 4. Luật DN có gì đặc biệt?                           │ │
│  │ 5. Tìm hiểu về Luật Doanh nghiệp                     │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

#### Edit Mode (After clicking "Chỉnh sửa")

```
┌─────────────────────────────────────────────────────────────┐
│ Questions Manager                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Chỉnh sửa câu hỏi: Luật Doanh nghiệp 2020                 │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Câu hỏi chính                                         │ │
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ Luật Doanh nghiệp có những quy định gì?          │ │ │ ← EDITABLE
│  │ │                                                   │ │ │   TEXTAREA
│  │ │                                                   │ │ │
│  │ └───────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Biến thể câu hỏi (5)                                  │ │
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ 1. Quy định về doanh nghiệp là gì?           [X] │ │ │ ← REMOVE
│  │ └───────────────────────────────────────────────────┘ │ │   BUTTON
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ 2. Luật Doanh nghiệp nói về điều gì?         [X] │ │ │
│  │ └───────────────────────────────────────────────────┘ │ │
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ 3. Nội dung chính của Luật DN?               [X] │ │ │
│  │ └───────────────────────────────────────────────────┘ │ │
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ 4. Luật DN có gì đặc biệt?                   [X] │ │ │
│  │ └───────────────────────────────────────────────────┘ │ │
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ 5. Tìm hiểu về Luật Doanh nghiệp             [X] │ │ │
│  │ └───────────────────────────────────────────────────┘ │ │
│  │                                                       │ │
│  │ ┌───────────────────────────────────────────────────┐ │ │
│  │ │ Nhập biến thể mới...                             │ │ │ ← ADD NEW
│  │ └───────────────────────────────────────────────────┘ │ │   VARIANT
│  │                             [+ Thêm biến thể]         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ☐ Rebuild vector database sau khi lưu               │ │ ← REBUILD
│  └───────────────────────────────────────────────────────┘ │   TRIGGER
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ 💾 Lưu thay đổi  │  │ ✕ Hủy           │               │ ← ACTIONS
│  └──────────────────┘  └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

#### Edit Mode - With Rebuild Progress

```
┌─────────────────────────────────────────────────────────────┐
│ Questions Manager                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Đã lưu thay đổi thành công!                            │ ← SUCCESS
│                                                             │   MESSAGE
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🔄 Đang rebuild database... 67%                       │ │ ← REBUILD
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │   PROGRESS
│  │ ████████████████████████████░░░░░░░░░░░░░░░░          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  [Automatically refreshes when complete]                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 State Transitions

```
┌─────────────┐     Click "Chỉnh sửa"      ┌─────────────┐
│             │  ───────────────────────>   │             │
│  VIEW MODE  │                             │  EDIT MODE  │
│             │  <───────────────────────   │             │
└─────────────┘     Click "Hủy"             └─────────────┘
                    (no changes)                    │
                                                    │
                                         Click "Lưu thay đổi"
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │ API Call to       │
                                        │ Admin Service     │
                                        └───────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │ Update JSONL      │
                                        │ in RAG Service    │
                                        └───────────────────┘
                                                    │
                                   ┌────────────────┴────────────────┐
                                   │                                 │
                          Rebuild = false                   Rebuild = true
                                   │                                 │
                                   ▼                                 ▼
                        ┌──────────────────┐              ┌─────────────────┐
                        │ Success Message  │              │ Trigger Rebuild │
                        │ → Refresh Data   │              │ → Track Progress│
                        │ → Back to View   │              │ → Show Progress │
                        └──────────────────┘              │ → Success Msg   │
                                                          │ → Refresh Data  │
                                                          │ → Back to View  │
                                                          └─────────────────┘
```

---

## 📱 Component Hierarchy

```
QuestionsManager (Parent Component)
│
├── [VIEW MODE - default state]
│   ├── Button: "Chỉnh sửa" (onClick → setIsEditing(true))
│   ├── Card: Main Question Display
│   └── Card: Variants List Display
│
└── [EDIT MODE - when isEditing = true]
    └── QuestionsEditor (Child Component)
        ├── Props:
        │   ├── collection: string
        │   ├── docId: string
        │   ├── documentTitle: string
        │   ├── currentMainQuestion: string
        │   ├── currentVariants: string[]
        │   ├── onSaveSuccess: () => void
        │   └── onCancel: () => void
        │
        ├── State:
        │   ├── mainQuestion: string
        │   ├── variants: string[]
        │   ├── newVariant: string
        │   ├── triggerRebuild: boolean
        │   ├── isSaving: boolean
        │   ├── saveError: string | null
        │   ├── saveSuccess: boolean
        │   └── rebuildStatus: number | null
        │
        ├── UI Elements:
        │   ├── Textarea: Main question editor
        │   ├── Variants List:
        │   │   ├── Display variant with remove button
        │   │   └── Input + Button: Add new variant
        │   ├── Checkbox: Rebuild trigger
        │   ├── Button: "Lưu thay đổi" (disabled when saving)
        │   ├── Button: "Hủy" (disabled when saving)
        │   ├── Alert: Success message (auto-dismiss 3s)
        │   ├── Alert: Error message
        │   └── Progress Bar: Rebuild status (0-100%)
        │
        └── Actions:
            ├── handleSave() → API call → onSaveSuccess callback
            ├── handleCancel() → onCancel callback
            ├── addVariant() → Update variants array
            ├── removeVariant(index) → Update variants array
            └── pollRebuildStatus() → Update progress bar
```

---

## 🎨 Visual Components Used

### shadcn/ui Components

- ✅ `Card` - Container for sections
- ✅ `CardContent` - Inner content padding
- ✅ `Button` - Actions (Save, Cancel, Edit, Add)
- ✅ `Input` - Text input for new variants
- ✅ `Textarea` - Multi-line editor for main question
- ✅ `Badge` - Tags (e.g., "Câu hỏi chính", variant numbers)

### lucide-react Icons

- ✅ `Edit` - Edit button icon
- ✅ `Save` - Save button icon
- ✅ `X` - Remove/Cancel icons
- ✅ `RefreshCw` - Rebuild progress spinner (animated)
- ✅ `Plus` - Add variant icon
- ✅ `CheckCircle` - Success message icon
- ✅ `AlertCircle` - Error message icon

### Tailwind CSS Classes

- ✅ `bg-green-50`, `border-green-200` - Success states
- ✅ `bg-red-50`, `border-red-200` - Error states
- ✅ `bg-blue-50`, `border-blue-200` - Rebuild progress
- ✅ `animate-spin` - Loading spinner
- ✅ `transition-all duration-300` - Smooth animations
- ✅ `hover:bg-gray-100` - Interactive feedback

---

## 🔗 API Endpoints Integration

### Questions CRUD

```typescript
// View questions
GET /collections/{collection}/documents/{docId}/questions
→ QuestionsManager.loadQuestions()

// Update questions
PUT /collections/{collection}/documents/{docId}/questions
Body: { main_question, variants, rebuild }
→ QuestionsEditor.handleSave()

// Update variants only
PATCH /collections/{collection}/documents/{docId}/questions/variants
Body: { variants, rebuild }
→ (Not used in current UI, but available)

// Delete questions
DELETE /collections/{collection}/documents/{docId}/questions?rebuild=true
→ (Not exposed in UI yet, but API ready)
```

### Rebuild Management

```typescript
// Trigger rebuild
POST /rebuild/trigger
Body: { scope, collection?, doc_id? }
→ QuestionsEditor.handleSave() (when checkbox checked)

// Check rebuild status
GET /rebuild/status
→ QuestionsEditor.pollRebuildStatus() (every 2 seconds)

// Cancel rebuild
POST /rebuild/cancel
→ (Not exposed in UI yet, but API ready)
```

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│ User clicks     │
│ "Chỉnh sửa"     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ QuestionsManager                                │
│ ─────────────────────────────────────────────── │
│ setIsEditing(true)                              │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ QuestionsEditor                             │ │
│ │ ────────────────────────────────────────────│ │
│ │ Props:                                      │ │
│ │ - currentMainQuestion: string               │ │
│ │ - currentVariants: string[]                 │ │
│ │                                             │ │
│ │ State:                                      │ │
│ │ - mainQuestion ← currentMainQuestion        │ │
│ │ - variants ← currentVariants                │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         │
         │ User edits
         ▼
┌─────────────────────────────────────────────────┐
│ QuestionsEditor                                 │
│ ─────────────────────────────────────────────── │
│ State updates:                                  │
│ - setMainQuestion(new text)                     │
│ - setVariants([...variants, newVariant])        │
│ - setTriggerRebuild(checked)                    │
└────────┬────────────────────────────────────────┘
         │
         │ Click "Lưu thay đổi"
         ▼
┌─────────────────────────────────────────────────┐
│ API Call                                        │
│ ─────────────────────────────────────────────── │
│ PUT /collections/{collection}/documents/        │
│     {docId}/questions                           │
│ Body: {                                         │
│   main_question: mainQuestion,                  │
│   variants: variants,                           │
│   rebuild: triggerRebuild                       │
│ }                                               │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ Admin Service (Port 8001)                       │
│ ─────────────────────────────────────────────── │
│ Validates request → Forwards to RAG Service     │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ RAG Service (Port 8000)                         │
│ ─────────────────────────────────────────────── │
│ 1. Update questions.jsonl file                  │
│ 2. (Optional) Trigger rebuild                   │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ Response                                        │
│ ─────────────────────────────────────────────── │
│ {                                               │
│   update_result: { ... },                       │
│   rebuild_status: {                             │
│     status: "in_progress",                      │
│     progress: 0                                 │
│   }                                             │
│ }                                               │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ QuestionsEditor - Success Handler               │
│ ─────────────────────────────────────────────── │
│ setSaveSuccess(true)                            │
│ setRebuildStatus(0) ← Start progress tracking  │
│                                                 │
│ Poll every 2 seconds:                           │
│   GET /rebuild/status                           │
│   → setRebuildStatus(progress)                  │
│   → Update progress bar (0% → 100%)             │
│                                                 │
│ When progress = 100%:                           │
│   → Auto-hide progress bar after 2s             │
│   → Show success message                        │
│   → Call onSaveSuccess()                        │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ QuestionsManager - Refresh Handler              │
│ ─────────────────────────────────────────────── │
│ setIsEditing(false) ← Back to view mode         │
│ loadQuestions(selectedDocument) ← Reload data   │
└─────────────────────────────────────────────────┘
```

---

## 🎯 Key User Interactions

### 1. Edit Main Question

```
Action: User types in textarea
State Update: setMainQuestion(event.target.value)
Validation: Required field (cannot be empty)
```

### 2. Add Variant

```
Action: User types in input + clicks "Thêm biến thể"
State Update: setVariants([...variants, newVariant])
Clear Input: setNewVariant("")
Validation: Cannot add empty variant
```

### 3. Remove Variant

```
Action: User clicks [X] button on variant
State Update: setVariants(variants.filter((_, i) => i !== index))
Effect: Variant removed from list
```

### 4. Toggle Rebuild

```
Action: User checks/unchecks checkbox
State Update: setTriggerRebuild(!triggerRebuild)
Effect: Rebuild will be triggered after save (if checked)
```

### 5. Save Changes

```
Action: User clicks "Lưu thay đổi"
Validation: mainQuestion must not be empty
State: setIsSaving(true)
API Call: updateQuestions(collection, docId, mainQuestion, variants, triggerRebuild)
Success:
  → setSaveSuccess(true)
  → Start rebuild progress tracking (if rebuild enabled)
  → Show success message
  → Call onSaveSuccess() after 1.5s
Error:
  → setSaveError(error message)
  → Show error alert
Finally:
  → setIsSaving(false)
```

### 6. Cancel Editing

```
Action: User clicks "Hủy"
State: No state updates (discard changes)
Callback: onCancel() → setIsEditing(false)
Effect: Switch back to view mode
```

---

## ✅ Phase 3 Complete - Ready for Testing!

All UI components implemented and integrated successfully. Zero compilation errors. Ready for browser testing.
