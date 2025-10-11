# Phase 3 Testing Guide

## 🧪 Hướng dẫn kiểm thử Phase 3 - Frontend Questions CRUD

---

## 📋 Chuẩn bị môi trường

### 1. Khởi động các services (3 terminal)

#### Terminal 1: Frontend (Vite Dev Server)

```powershell
cd frontend
npm run dev
```

**Expected Output**:

```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

#### Terminal 2: Admin Service

```powershell
cd admin_service
python main.py
```

**Expected Output**:

```
🚀 Admin Service starting on http://0.0.0.0:8001
✅ RAG Service connection: OK
INFO:     Started server process
INFO:     Application startup complete
```

#### Terminal 3: RAG Service

```powershell
conda activate LegalRAG
cd rag_service
python main.py
```

**Expected Output**:

```
🚀 Starting LegalRAG API...
✅ All services initialized successfully
INFO:     Started server process on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## ✅ Checklist kiểm thử cơ bản

### Test 1: Navigation to Questions Manager

**Mục đích**: Kiểm tra truy cập vào giao diện quản lý câu hỏi

**Bước thực hiện**:

1. Mở browser tại `http://localhost:5173`
2. Đăng nhập với tài khoản admin
3. Navigate to Admin Panel
4. Click vào "Questions Manager"

**Kết quả mong đợi**:

- ✅ Hiển thị danh sách collections (grid cards)
- ✅ Mỗi collection có số lượng documents
- ✅ Có nút "Làm mới" và thanh tìm kiếm
- ✅ Không có lỗi console

**Screenshot point**: `01_questions_manager_collections.png`

---

### Test 2: View Documents in Collection

**Mục đích**: Kiểm tra xem danh sách documents trong collection

**Bước thực hiện**:

1. Click vào một collection (ví dụ: "Luật Doanh nghiệp")
2. Chờ loading documents

**Kết quả mong đợi**:

- ✅ Hiển thị breadcrumb: Collections → Luật Doanh nghiệp
- ✅ Danh sách documents với metadata (title, doc_id, created_at)
- ✅ Nút "Xem câu hỏi" trên mỗi document
- ✅ Nút "Quay lại" để về collections

**Screenshot point**: `02_documents_list.png`

---

### Test 3: View Questions in Document

**Mục đích**: Kiểm tra xem câu hỏi của document

**Bước thực hiện**:

1. Click "Xem câu hỏi" trên một document
2. Chờ loading questions

**Kết quả mong đợi**:

- ✅ Hiển thị breadcrumb: Collections → Collection Name → Document Title
- ✅ Card màu xanh hiển thị câu hỏi chính
- ✅ Card danh sách biến thể (nếu có)
- ✅ **NÚT "Chỉnh sửa" Ở GÓC TRÊN BÊN PHẢI** ← **PHASE 3 FEATURE**
- ✅ Nút "Quay lại" để về documents

**Screenshot point**: `03_questions_view_mode.png`

---

### Test 4: Enter Edit Mode

**Mục đích**: Kiểm tra chuyển sang chế độ chỉnh sửa

**Bước thực hiện**:

1. Ở view questions, click nút "Chỉnh sửa"

**Kết quả mong đợi**:

- ✅ Giao diện chuyển sang chế độ chỉnh sửa
- ✅ Hiển thị QuestionsEditor component
- ✅ Textarea chứa câu hỏi chính (có thể edit)
- ✅ Danh sách variants với nút [X] để xóa
- ✅ Input và nút "Thêm biến thể" để thêm variant mới
- ✅ Checkbox "Rebuild vector database sau khi lưu"
- ✅ Nút "Lưu thay đổi" (màu xanh)
- ✅ Nút "Hủy" (màu xám)

**Screenshot point**: `04_edit_mode.png`

**Browser Console Check**:

```javascript
// Không có lỗi console
// State isEditing = true
```

---

### Test 5: Edit Main Question

**Mục đích**: Kiểm tra chỉnh sửa câu hỏi chính

**Bước thực hiện**:

1. Click vào textarea câu hỏi chính
2. Xóa nội dung cũ
3. Gõ câu hỏi mới: "Test câu hỏi mới - Phase 3"

**Kết quả mong đợi**:

- ✅ Textarea cập nhật real-time
- ✅ Không có lag hoặc delay
- ✅ Text hiển thị chính xác tiếng Việt (có dấu)

**Browser Console Check**:

```javascript
// State mainQuestion = "Test câu hỏi mới - Phase 3"
```

---

### Test 6: Add New Variant

**Mục đích**: Kiểm tra thêm biến thể mới

**Bước thực hiện**:

1. Scroll xuống phần "Biến thể câu hỏi"
2. Click vào input "Nhập biến thể mới..."
3. Gõ: "Variant test 1 - Phase 3"
4. Click nút "Thêm biến thể"

**Kết quả mong đợi**:

- ✅ Variant mới xuất hiện trong danh sách
- ✅ Input field được clear (trống)
- ✅ Variant có nút [X] để xóa
- ✅ Số thứ tự variant tăng lên

**Screenshot point**: `05_add_variant.png`

**Repeat Test**: Thêm thêm 2 variants nữa để test nhiều items

---

### Test 7: Remove Variant

**Mục đích**: Kiểm tra xóa biến thể

**Bước thực hiện**:

1. Click nút [X] trên một variant bất kỳ
2. Quan sát danh sách

**Kết quả mong đợi**:

- ✅ Variant bị xóa khỏi danh sách ngay lập tức
- ✅ Số thứ tự các variant còn lại tự động cập nhật
- ✅ Không có lỗi console

**Edge Case**: Thử xóa tất cả variants → Danh sách variants trống nhưng không lỗi

---

### Test 8: Toggle Rebuild Checkbox

**Mục đích**: Kiểm tra checkbox rebuild trigger

**Bước thực hiện**:

1. Click vào checkbox "Rebuild vector database sau khi lưu"
2. Quan sát trạng thái

**Kết quả mong đợi**:

- ✅ Checkbox checked/unchecked
- ✅ State triggerRebuild toggle đúng

**Browser Console Check**:

```javascript
// State triggerRebuild = true (khi checked)
```

---

### Test 9: Save Changes WITHOUT Rebuild

**Mục đích**: Kiểm tra lưu thay đổi không rebuild

**Bước thực hiện**:

1. Đảm bảo checkbox rebuild **KHÔNG được check**
2. Click nút "Lưu thay đổi"
3. Quan sát response

**Kết quả mong đợi**:

- ✅ Nút "Lưu thay đổi" disabled (loading state)
- ✅ Loading spinner hiển thị
- ✅ **Alert màu xanh "✅ Đã lưu thay đổi thành công!"**
- ✅ Alert tự động ẩn sau 3 giây
- ✅ Giao diện tự động chuyển về view mode
- ✅ Questions hiển thị với dữ liệu mới
- ✅ **KHÔNG có rebuild progress bar**

**Screenshot point**: `06_save_success.png`

**Browser Console Check**:

```javascript
// ✅ PUT /collections/{collection}/documents/{docId}/questions
// Response: { update_result: {...}, rebuild_status: null }
```

**RAG Service Log Check**:

```
✅ Questions updated for DOC_XXX
📝 Updated questions.jsonl file
```

---

### Test 10: Save Changes WITH Rebuild

**Mục đích**: Kiểm tra lưu thay đổi với rebuild trigger

**Bước thực hiện**:

1. Quay lại edit mode
2. Sửa câu hỏi: "Test với rebuild - Phase 3"
3. **CHECK checkbox "Rebuild vector database sau khi lưu"**
4. Click "Lưu thay đổi"

**Kết quả mong đợi**:

- ✅ Alert "✅ Đã lưu thay đổi thành công!"
- ✅ **XUẤT HIỆN REBUILD PROGRESS BAR**:
  ```
  🔄 Đang rebuild database... 0%
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```
- ✅ Progress bar tăng dần: 0% → 25% → 50% → 75% → 100%
- ✅ Icon spinner quay (animate-spin)
- ✅ Khi đạt 100%, progress bar tự động ẩn sau 2 giây
- ✅ Giao diện chuyển về view mode
- ✅ Questions hiển thị với dữ liệu mới

**Screenshot points**:

- `07_rebuild_0_percent.png` (0%)
- `08_rebuild_50_percent.png` (50%)
- `09_rebuild_100_percent.png` (100%)

**Browser Console Check**:

```javascript
// ✅ PUT /collections/{collection}/documents/{docId}/questions
// Response: { update_result: {...}, rebuild_status: { progress: 0, ... } }
// ✅ GET /rebuild/status (mỗi 2 giây)
// Response: { progress: 25 } → { progress: 50 } → { progress: 100 }
```

**RAG Service Log Check**:

```
✅ Questions updated for DOC_XXX
📝 Updated questions.jsonl file
🔄 Rebuild triggered for document DOC_XXX
⏳ Rebuilding vector database... 25%
⏳ Rebuilding vector database... 50%
⏳ Rebuilding vector database... 75%
✅ Rebuild completed successfully
```

---

### Test 11: Cancel Editing

**Mục đích**: Kiểm tra hủy chỉnh sửa

**Bước thực hiện**:

1. Click "Chỉnh sửa"
2. Sửa câu hỏi: "Test cancel - không lưu"
3. Thêm 2 variants mới
4. Click nút "Hủy"

**Kết quả mong đợi**:

- ✅ Giao diện chuyển về view mode
- ✅ **Câu hỏi VẪN GIỮ NGUYÊN DỮ LIỆU CŨ** (không có "Test cancel")
- ✅ Variants mới KHÔNG xuất hiện
- ✅ Không có API call nào được gửi
- ✅ Không có lỗi console

**Browser Console Check**:

```javascript
// KHÔNG có PUT request
// State isEditing = false
```

---

## 🔥 Error Handling Tests

### Test 12: Empty Main Question Validation

**Mục đích**: Kiểm tra validation khi câu hỏi chính trống

**Bước thực hiện**:

1. Click "Chỉnh sửa"
2. Xóa hết nội dung trong textarea câu hỏi chính
3. Click "Lưu thay đổi"

**Kết quả mong đợi**:

- ✅ **Alert màu đỏ "❌ Vui lòng nhập câu hỏi chính"**
- ✅ KHÔNG gửi API request
- ✅ Vẫn ở edit mode
- ✅ User có thể sửa lại

**Screenshot point**: `10_validation_error.png`

---

### Test 13: Network Error Simulation

**Mục đích**: Kiểm tra xử lý lỗi network

**Bước thực hiện**:

1. **STOP Admin Service** (Ctrl+C trong terminal 2)
2. Click "Chỉnh sửa" → Sửa câu hỏi
3. Click "Lưu thay đổi"

**Kết quả mong đợi**:

- ✅ **Alert màu đỏ với error message** (ví dụ: "Network Error" hoặc "Không thể kết nối")
- ✅ Nút "Lưu thay đổi" enabled lại
- ✅ Vẫn ở edit mode
- ✅ User có thể retry

**Screenshot point**: `11_network_error.png`

**Recovery Test**:

1. **RESTART Admin Service**
2. Click "Lưu thay đổi" lại
3. → Phải thành công

---

### Test 14: Rebuild Timeout

**Mục đích**: Kiểm tra timeout khi rebuild quá lâu

**Bước thực hiện**:

1. Mock một rebuild rất lâu (nếu có thể)
2. HOẶC chờ 2 phút không có progress update

**Kết quả mong đợi**:

- ✅ Sau 2 phút (120 giây), progress bar tự động ẩn
- ✅ Hiển thị warning trong console: "Rebuild status polling timed out"
- ✅ Giao diện vẫn hoạt động bình thường

**Browser Console Check**:

```javascript
// ⚠️ Rebuild status polling timed out
```

---

## 🎯 Edge Cases Tests

### Test 15: Document with No Variants

**Mục đích**: Kiểm tra document chỉ có main question, không có variants

**Bước thực hiện**:

1. Tìm một document chỉ có main question
2. Click "Xem câu hỏi"
3. Click "Chỉnh sửa"

**Kết quả mong đợi**:

- ✅ Textarea main question hiển thị đúng
- ✅ Danh sách variants trống (không có item nào)
- ✅ Vẫn có input "Thêm biến thể"
- ✅ Có thể thêm variants mới
- ✅ Lưu thành công

---

### Test 16: Document with Many Variants (10+)

**Mục đích**: Kiểm tra UI với nhiều variants

**Bước thực hiện**:

1. Tìm document có nhiều variants (hoặc thêm thủ công)
2. Click "Chỉnh sửa"
3. Scroll danh sách variants

**Kết quả mong đợi**:

- ✅ Danh sách scrollable (không bị overflow)
- ✅ Mỗi variant có nút [X]
- ✅ Số thứ tự hiển thị đúng (1, 2, 3, ..., 10+)
- ✅ Performance tốt (không lag khi scroll)

---

### Test 17: Rapid Add/Remove Variants

**Mục đích**: Kiểm tra state management khi thao tác nhanh

**Bước thực hiện**:

1. Click "Chỉnh sửa"
2. Thêm nhanh 5 variants liên tiếp
3. Xóa ngẫu nhiên 3 variants
4. Thêm lại 2 variants
5. Lưu

**Kết quả mong đợi**:

- ✅ State cập nhật chính xác sau mỗi action
- ✅ Không có duplicates hoặc missing items
- ✅ Số thứ tự luôn đúng
- ✅ Lưu thành công với state cuối cùng

---

### Test 18: Very Long Main Question

**Mục đích**: Kiểm tra UI với câu hỏi dài

**Bước thực hiện**:

1. Click "Chỉnh sửa"
2. Gõ câu hỏi dài ~500 ký tự
3. Lưu

**Kết quả mong đợi**:

- ✅ Textarea tự động expand/scroll
- ✅ Không bị overflow
- ✅ Lưu thành công
- ✅ View mode hiển thị đúng (có thể wrap text)

---

## 📱 Responsive Tests

### Test 19: Mobile Viewport

**Mục đích**: Kiểm tra UI trên mobile

**Bước thực hiện**:

1. Mở Chrome DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Chọn iPhone 12 Pro hoặc tương tự
4. Thực hiện workflow edit → save

**Kết quả mong đợi**:

- ✅ UI responsive, không bị horizontal scroll
- ✅ Nút "Chỉnh sửa", "Lưu", "Hủy" vẫn click được
- ✅ Textarea và input không bị overflow
- ✅ Progress bar hiển thị đúng
- ✅ Alerts hiển thị đầy đủ

---

### Test 20: Tablet Viewport

**Mục đích**: Kiểm tra UI trên tablet

**Bước thực hiện**:

1. Chọn iPad viewport trong DevTools
2. Thực hiện workflow edit → save

**Kết quả mong đợi**:

- ✅ Layout tối ưu cho tablet
- ✅ Card widths phù hợp
- ✅ Touch-friendly button sizes

---

## 🌐 Browser Compatibility Tests

### Test 21: Chrome/Edge

**Status**: ✅ Expected to work (development environment)

### Test 22: Firefox

**Bước thực hiện**:

1. Mở `http://localhost:5173` trong Firefox
2. Thực hiện toàn bộ workflow

**Kết quả mong đợi**:

- ✅ UI giống Chrome
- ✅ Tất cả features hoạt động
- ✅ Không có console errors

### Test 23: Safari (if available)

**Bước thực hiện**:

1. Mở trên Safari
2. Kiểm tra UI và functionality

---

## 🐛 Regression Tests

### Test 24: Existing Features Still Work

**Mục đích**: Đảm bảo Phase 3 không phá vỡ features cũ

**Checklist**:

- ✅ Collections view vẫn hoạt động
- ✅ Documents view vẫn hoạt động
- ✅ Questions view (read-only) vẫn hoạt động
- ✅ Search functionality vẫn hoạt động
- ✅ Refresh buttons vẫn hoạt động
- ✅ Navigation (back buttons) vẫn hoạt động

---

## 📊 Performance Tests

### Test 25: Loading Time

**Bước thực hiện**:

1. Mở DevTools → Network tab
2. Disable cache
3. Reload page
4. Measure load time

**Kết quả mong đợi**:

- ✅ Initial page load < 3 seconds
- ✅ API calls respond < 1 second
- ✅ Rebuild progress updates every 2 seconds

---

### Test 26: Memory Leaks

**Bước thực hiện**:

1. Mở DevTools → Performance tab
2. Thực hiện edit → save workflow 10 lần liên tiếp
3. Kiểm tra memory usage

**Kết quả mong đợi**:

- ✅ Memory không tăng liên tục
- ✅ useEffect cleanup hoạt động đúng
- ✅ Intervals/Timeouts được clear

---

## ✅ Acceptance Criteria

### Must Have (Critical)

- ✅ [Test 1-11] Tất cả workflow cơ bản hoạt động
- ✅ [Test 12-13] Error handling đầy đủ
- ✅ [Test 24] Không phá vỡ features cũ

### Should Have (Important)

- ✅ [Test 15-18] Edge cases được xử lý
- ✅ [Test 19-20] Responsive design
- ✅ [Test 25] Performance acceptable

### Nice to Have (Optional)

- ⏳ [Test 22-23] Cross-browser compatibility
- ⏳ [Test 26] Memory optimization

---

## 📸 Screenshot Checklist

Cần chụp các màn hình sau:

1. ✅ `01_questions_manager_collections.png`
2. ✅ `02_documents_list.png`
3. ✅ `03_questions_view_mode.png`
4. ✅ `04_edit_mode.png`
5. ✅ `05_add_variant.png`
6. ✅ `06_save_success.png`
7. ✅ `07_rebuild_0_percent.png`
8. ✅ `08_rebuild_50_percent.png`
9. ✅ `09_rebuild_100_percent.png`
10. ✅ `10_validation_error.png`
11. ✅ `11_network_error.png`

---

## 📝 Test Report Template

```markdown
# Phase 3 Testing Report

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: Windows/Mac/Linux + Chrome/Firefox/Safari
**Services**: Frontend (5173) + Admin (8001) + RAG (8000)

## Summary

- Total Tests: 26
- Passed: XX
- Failed: XX
- Skipped: XX

## Detailed Results

### Test 1: Navigation to Questions Manager

- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

### Test 2: View Documents in Collection

- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

[... continue for all tests ...]

## Issues Found

1. [Issue description]
   - Severity: Critical / Major / Minor
   - Steps to reproduce
   - Expected vs Actual behavior
   - Screenshot: [filename]

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Conclusion

Phase 3 is ✅ READY / ⏳ NEEDS FIXES / ❌ NOT READY
```

---

## 🎉 Completion Checklist

Phase 3 considered **COMPLETE** when:

- ✅ All 26 tests executed
- ✅ At least 20/26 tests pass (77% pass rate)
- ✅ All critical tests (1-13) pass
- ✅ No critical bugs found
- ✅ Screenshots captured
- ✅ Test report written

**Estimated Testing Time**: 2-3 hours

**Good luck with testing! 🚀**
