# 🎨 Questions Editor - UX Improvement

## ✨ Thay đổi UX (Phase 3.1)

### ❌ UX Cũ (Checkbox - Dễ bị miss)

```
┌─────────────────────────────────────────────────────┐
│ 📝 Câu hỏi chính                                    │
│ [Textarea]                                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 📚 Biến thể câu hỏi                                 │
│ 1. Variant 1                                   [X]  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ⚠️ CHECKBOX (dễ bỏ qua - background màu vàng)       │
│ ☐ Rebuild VectorDB sau khi lưu                     │
└─────────────────────────────────────────────────────┘

[Lưu thay đổi]  [Hủy]
```

**Vấn đề**:

- ❌ User dễ bỏ qua checkbox
- ❌ Không rõ rebuild có tác động gì
- ❌ Không có feedback khi rebuild

---

### ✅ UX Mới (Modal Confirmation)

#### Bước 1: Edit như bình thường

```
┌─────────────────────────────────────────────────────┐
│ Chỉnh sửa câu hỏi                     [Hủy] [Lưu]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ⚠️ Có thay đổi chưa được lưu                       │
│                                                     │
│ 📝 Câu hỏi chính                                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Edit textarea]                                 │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ 📚 Biến thể câu hỏi (5)                            │
│ 1. Variant 1 [Input field]                    [X]  │
│ 2. Variant 2 [Input field]                    [X]  │
│ [Input: Nhập biến thể mới...]        [+ Thêm]     │
└─────────────────────────────────────────────────────┘
```

#### Bước 2: Click "Lưu thay đổi" → Modal xuất hiện

```
┌─────────────────────────────────────────────────────┐
│ 🔄 Xác nhận lưu thay đổi                      [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Bạn có muốn rebuild vector database sau khi lưu?   │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 💾 Chỉ lưu thay đổi                            │ │
│ │ Lưu nhanh, rebuild sau. Thích hợp khi đang     │ │
│ │ chỉnh sửa nhiều documents.                     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ⚡ Lưu & Rebuild ngay                          │ │ ← RECOMMENDED
│ │ Áp dụng thay đổi vào chat ngay lập tức.       │ │
│ │ Khuyến nghị!                                   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│           [Hủy]  [Chỉ lưu]  [⚡ Lưu & Rebuild]     │
└─────────────────────────────────────────────────────┘
```

#### Bước 3: Nếu chọn "Lưu & Rebuild" → Progress bar

```
┌─────────────────────────────────────────────────────┐
│ 🔄 Xác nhận lưu thay đổi                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 🔄 Đang rebuild vector database...                 │
│ Vui lòng đợi...                                    │
│                                                     │
│ ████████████████████░░░░░░░░░░░░░░░░░░ 67%         │
│                                                     │
│              67% hoàn thành                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Bước 4: Hoàn thành

```
┌─────────────────────────────────────────────────────┐
│ 🔄 Xác nhận lưu thay đổi                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ✅ Rebuild hoàn thành!                             │
│ Vui lòng đợi...                                    │
│                                                     │
│ ██████████████████████████████████████ 100%         │
│                                                     │
│             100% hoàn thành                         │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ✅ Rebuild hoàn thành thành công!              │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ [Modal tự động đóng sau 2s]                        │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Lợi ích của UX mới

### 1. **Không thể bỏ qua**

- ✅ Modal bắt buộc phải chọn
- ✅ Hiển thị rõ ràng 2 options
- ✅ Giải thích chi tiết từng option

### 2. **User-friendly**

- ✅ Mô tả rõ từng lựa chọn
- ✅ Recommendation rõ ràng (border xanh, text "Khuyến nghị!")
- ✅ Icon trực quan (💾 vs ⚡)

### 3. **Feedback tốt**

- ✅ Progress bar real-time
- ✅ Status message
- ✅ Success confirmation
- ✅ Auto-close khi hoàn thành

### 4. **Flexible workflow**

- ✅ Có thể "Chỉ lưu" nếu đang edit nhiều docs
- ✅ Có thể "Lưu & Rebuild" để apply ngay
- ✅ Có thể "Hủy" nếu đổi ý

---

## 📊 So sánh

| Feature           | UX Cũ (Checkbox)     | UX Mới (Modal)     |
| ----------------- | -------------------- | ------------------ |
| Dễ bỏ qua         | ❌ Rất dễ            | ✅ Không thể       |
| Giải thích        | ⚠️ Text nhỏ          | ✅ Chi tiết        |
| Recommendation    | ❌ Không có          | ✅ Rõ ràng         |
| Progress tracking | ⚠️ Inline (khó thấy) | ✅ Modal focus     |
| User choice       | ❌ Phải remember     | ✅ Forced decision |

---

## 🧪 Test Workflow

### Test 1: Lưu không rebuild

1. ✅ Edit questions → Click "Lưu thay đổi"
2. ✅ Modal xuất hiện
3. ✅ Click "Chỉ lưu"
4. ✅ Modal đóng → Quay về view mode
5. ✅ Check: `rebuild=false` trong API call

### Test 2: Lưu với rebuild

1. ✅ Edit questions → Click "Lưu thay đổi"
2. ✅ Modal xuất hiện
3. ✅ Click "⚡ Lưu & Rebuild"
4. ✅ Progress bar xuất hiện: 0% → 100%
5. ✅ Success message → Auto-close sau 2s
6. ✅ Check: `rebuild=true` trong API call
7. ✅ Check: `rebuild_status.json` updated

### Test 3: Cancel từ modal

1. ✅ Edit questions → Click "Lưu thay đổi"
2. ✅ Modal xuất hiện
3. ✅ Click "Hủy"
4. ✅ Modal đóng → Vẫn ở edit mode
5. ✅ Changes vẫn còn (không bị mất)

### Test 4: Progress tracking

1. ✅ Click "⚡ Lưu & Rebuild"
2. ✅ Progress bar xuất hiện
3. ✅ Polling mỗi 2 giây
4. ✅ Progress tăng dần: 0% → 25% → 50% → 75% → 100%
5. ✅ Success message khi 100%
6. ✅ Auto-close sau 2s

---

## 🔧 Technical Implementation

### Component State

```typescript
// Modal states
const [showRebuildModal, setShowRebuildModal] = useState(false);
const [rebuildProgress, setRebuildProgress] = useState<number | null>(null);
const [rebuildStatus, setRebuildStatus] = useState<string>("");

// Change detection
const hasChanges =
  mainQuestion !== currentMainQuestion ||
  JSON.stringify(variants) !== JSON.stringify(currentVariants);
```

### Save Flow

```typescript
// Step 1: Show modal
handleSaveClick() → setShowRebuildModal(true)

// Step 2a: Save only
handleSaveOnly() → updateQuestions(..., false) → onSaveSuccess()

// Step 2b: Save & rebuild
handleSaveAndRebuild() →
  updateQuestions(..., true) →
  Poll getRebuildStatus() every 2s →
  Update progress bar →
  Auto-close when 100%
```

### Modal Rendering

```tsx
{showRebuildModal && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <Card>
      {rebuildProgress === null ? (
        // Show options
      ) : (
        // Show progress
      )}
    </Card>
  </div>
)}
```

---

## 📝 Files Changed

### Modified

- ✅ `frontend/src/components/admin/questions/QuestionsEditor.tsx` (replaced)
  - Removed checkbox
  - Added modal confirmation
  - Added progress tracking UI
  - Improved change detection

### Backup

- ✅ `frontend/src/components/admin/questions/QuestionsEditor_old_backup.tsx`

---

## 🚀 Deployment

### Docker

```bash
# Frontend hot-reload sẽ tự động pick up changes
# Hoặc restart container:
docker-compose -f docker-compose.dev.yml restart frontend
```

### Production

```bash
# Rebuild frontend image
docker-compose -f docker-compose.dev.yml build frontend --no-cache
```

---

## ✅ Summary

**Phase 3.1 - UX Improvement COMPLETE!**

- ✅ Removed easy-to-miss checkbox
- ✅ Added modal confirmation với clear options
- ✅ Added progress tracking UI
- ✅ Added change detection indicator
- ✅ Improved user experience significantly

**Test now**: `http://localhost:5173` → Questions Manager → Edit → Lưu thay đổi 🎉
