# Form Data Conflict Management Implementation

## 📋 Tổng quan

Triển khai hệ thống quản lý conflict giữa dữ liệu CCCD scan và manual input trong IntegratedFormPage.

## 🔧 Architecture Components

### 1. useFormDataManager Hook

**File**: `frontend/src/hooks/useFormDataManager.ts`

**Chức năng chính**:

- Quản lý state cho CCCD data và manual data
- Track các field đã được user edit
- Detect conflicts khi có QR scan mới
- Cung cấp interface thống nhất cho form data management

**Key Methods**:

```typescript
interface UseFormDataManagerReturn {
  // State
  cccdData: CCCDData | null;
  manualData: Record<string, string>;
  userEditedFields: Set<string>;

  // Actions
  handleManualDataChange: (fieldName: string, value: string) => void;
  handleQRScanResult: (
    data: CCCDData,
    onConflict?: (conflicts: string[]) => Promise<boolean>
  ) => Promise<void>;
  resetQRScan: () => void;
  resetAllData: () => void;
  getFinalData: () => Record<string, string>;
  isFieldEdited: (fieldName: string) => boolean;
  getFieldValue: (fieldName: string) => string;
  getFieldSource: (fieldName: string) => "manual" | "cccd" | "empty";
}
```

### 2. ConflictDialog Component

**Files**:

- `frontend/src/components/forms/ConflictDialog.tsx`
- `frontend/src/components/forms/ConflictDialog.css`

**Chức năng**:

- Hiển thị dialog khi có conflicts
- So sánh dữ liệu CCCD vs Manual
- Cho phép user chọn giữ manual data hoặc dùng CCCD data

**Props Interface**:

```typescript
interface ConflictDialogProps {
  isOpen: boolean;
  conflicts: ConflictField[];
  onResolve: (shouldOverride: boolean) => void;
  onClose: () => void;
}

interface ConflictField {
  fieldName: string;
  displayName: string;
  cccdValue: string;
  manualValue: string;
}
```

### 3. Updated IntegratedFormPage

**File**: `frontend/src/pages/IntegratedFormPage.tsx`

**Thay đổi chính**:

- Sử dụng `useFormDataManager` hook thay vì state riêng lẻ
- Tích hợp `ConflictDialog` để xử lý conflicts
- Cải thiện status indicators hiển thị edit status
- Conflict resolution flow hoàn chỉnh

## 🔄 User Flow

### 1. Normal Flow (Không có conflicts)

```
User nhập manual data → State updated
User quét CCCD → No conflicts → CCCD data loaded
Download → Merge data (manual priority) → Word file
```

### 2. Conflict Flow

```
User nhập manual data → State updated, fields tracked
User quét CCCD → Conflicts detected → ConflictDialog shows
User chọn:
  - "Giữ thông tin thủ công" → Manual data preserved
  - "Dùng dữ liệu CCCD" → Manual data overridden
Download → Final merged data → Word file
```

## 🎯 Key Features

### 1. Conflict Detection

- Automatic detection khi CCCD scan có dữ liệu trùng với manual input
- Track user-edited fields để chỉ detect conflicts cho fields đã edit

### 2. Data Priority

- Manual data có priority cao hơn CCCD data trong final merge
- User có thể override manual data bằng CCCD data khi có conflict

### 3. Visual Indicators

- **🎯 Đã quét CCCD**: Hiển thị khi có CCCD data
- **✏️ Có X thông tin thủ công**: Hiển thị số field manual
- **📝 Đã chỉnh sửa X trường**: Hiển thị số field đã edit
- Download button text thay đổi theo trạng thái data

### 4. Form Integration

- FormRenderer đã support cả `placeholder_form_` và `placeholder_scan_`
- EditablePlaceholder components tự động update manual data
- Real-time sync giữa UI và state management

## 🔧 Technical Implementation

### State Management Flow

```
useFormDataManager Hook
├── cccdData (CCCDData | null)
├── manualData (Record<string, string>)
├── userEditedFields (Set<string>)
└── Methods for data manipulation

IntegratedFormPage
├── Form loading states
├── Conflict dialog states
├── Integration với FormRenderer
└── Download logic
```

### Conflict Resolution Pattern

```typescript
// Async conflict resolution với Promise pattern
const handleConflictResolution = async (
  conflicts: string[]
): Promise<boolean> => {
  return new Promise((resolve) => {
    setCurrentConflicts(conflicts);
    setShowConflictDialog(true);
    setConflictResolver(() => resolve);
  });
};

// QR scan với conflict callback
await handleQRData(data, handleConflictResolution);
```

## 🎨 Styling

### ConflictDialog CSS

- Overlay với backdrop blur
- Smooth animations (slideIn)
- Responsive design
- Color coding cho manual vs CCCD data
- Hover effects cho buttons

### Status Indicators

- **auto-fill-status**: Green for CCCD data
- **manual-fill-status**: Gray for manual input
- **edit-status**: Purple for edited fields

## 🚀 Benefits

1. **Better UX**: User không bị surprised khi CCCD overwrite manual data
2. **Data Control**: User có full control về data source priority
3. **Visual Feedback**: Clear indicators về data status
4. **Maintainable**: Clean separation of concerns với hook pattern
5. **Extensible**: Dễ dàng thêm features mới cho form data management

## 🔍 Future Enhancements

1. **Field-level conflict resolution**: Cho phép user chọn từng field thay vì all-or-nothing
2. **Data validation**: Validate data trước khi merge
3. **Backup/restore**: Cho phép user restore về trạng thái trước
4. **Auto-save**: Tự động save manual data vào localStorage
5. **Smart suggestions**: Suggest data dựa trên pattern recognition

## 📝 Code Quality Notes

- TypeScript interfaces đầy đủ cho type safety
- Error handling cho async operations
- Console logging cho debugging
- Clean up resources (React roots, event listeners)
- Responsive design patterns
- Accessibility considerations trong dialog
