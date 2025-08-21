## Frontend Updates for 4-Level Clarification System

### ✅ Changes Made:

1. **ClarificationOptions.tsx** - Updated to handle new action types:

   - `show_document_questions` → Purple styling (medium-high confidence)
   - `proceed_with_document` → Orange styling
   - `proceed_with_collection` → Blue styling (existing)
   - `manual_input` → Green styling (default)

2. **ContextInfoModal.tsx** - Updated confidence level display:
   - 80%+ → Green "Cao" (High)
   - 65%+ → Blue "Khá cao" (Medium-High) ✅ NEW
   - 50%+ → Yellow "Trung bình" (Medium)
   - <50% → Red "Thấp" (Low)

### 🧪 Testing Checklist:

1. **Test Query**: "Tôi muốn hỏi khi lập di chúc thì có phần phải đóng phí khi chứng thực không"

2. **Expected Flow**:

   - Should get confidence ~0.744-0.799 (Medium-High)
   - Should show purple "Xem câu hỏi về Thủ tục chứng thực di chúc" option
   - Clicking should trigger `show_document_questions` action
   - Should get list of specific questions about di chúc
   - No more "Có lỗi khi tải câu hỏi cho 'None'" error

3. **UI Elements to Check**:
   - Option styling (purple for medium-high)
   - Confidence display (should show "Khá cao" for 65%+)
   - No console errors with new action type
   - Smooth flow through clarification steps

### ⚠️ Potential Issues to Watch:

- Frontend TypeScript might not recognize new action types
- CSS styling might need tweaking for purple color scheme
- Console errors if new action isn't handled properly
