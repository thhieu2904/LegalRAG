# 📚 Admin Components Structure

## 🏗️ **Cấu trúc thư mục mới**

```
src/components/admin/
├── 📁 database/           # Database management
│   ├── AdminCollections.tsx   # Collections listing
│   ├── AdminDocuments.tsx     # Documents management
│   ├── DatabaseManager.tsx    # Integrated view (collections + documents)
│   └── index.ts               # Exports
├── 📁 questions/          # Questions management
│   ├── AdminQuestions.tsx     # Questions listing & filtering
│   └── index.ts               # Exports
├── 📁 shared/             # Shared components (future)
│   └── ...
├── Database.tsx           # Legacy entry point -> DatabaseManager
└── admin-components.css   # Styling
```

## 🎯 **Tính năng đã fix**

### ✅ **1. Tổ chức thư mục theo chức năng**

- **database/**: Collections & Documents management
- **questions/**: Questions management
- **shared/**: Shared components (sẵn sàng cho future features)

### ✅ **2. Logic "Xem document" hoạt động**

- **DatabaseManager.tsx**: Component tích hợp collections + documents
- **Thao tác**: Click vào collection → Load documents từ API → Hiển thị danh sách
- **Navigation**: Back button để quay về collections list
- **Search**: Tìm kiếm trong cả collections và documents

## 🚀 **Cách sử dụng**

### **Database Management**

```typescript
import DatabaseManager from "./database/DatabaseManager";
// Hoặc legacy
import Database from "./Database";
```

### **Questions Management**

```typescript
import { AdminQuestions } from "./questions";
```

### **Individual Components**

```typescript
import { AdminCollections, AdminDocuments } from "./database";
```

## 📋 **Features của DatabaseManager**

### **Collections View**

- ✅ Grid layout với collection cards
- ✅ Search collections by name/description
- ✅ Document count và metadata status
- ✅ Click để xem documents

### **Documents View**

- ✅ List documents từ selected collection
- ✅ Full metadata display (title, code, agency, dates, fees)
- ✅ Document status indicators (DOC, JSON, Questions, Forms)
- ✅ Search documents by title/code/agency
- ✅ Back to collections navigation

### **API Integration**

- ✅ Real-time data từ Admin Service (port 8001)
- ✅ Error handling với user-friendly messages
- ✅ Loading states với skeletons
- ✅ Auto-refresh functionality

## 📊 **Data Flow**

```
DatabaseManager
├── Collections View
│   ├── fetchCollections() → 13 collections
│   └── Click collection → loadDocuments(collection)
└── Documents View
    ├── fetchCollectionDocuments(name) → Documents list
    ├── Back button → Return to collections
    └── Search → Filter documents locally
```

## 🎨 **Styling**

Tất cả components sử dụng:

- **Tailwind CSS**: Utility classes
- **admin-components.css**: Custom styles cho admin UI
- **Shadcn/ui**: Consistent component library
- **Lucide icons**: Modern icon set

## 🔗 **API Endpoints sử dụng**

- `GET /api/collections` - List all collections
- `GET /api/collections/{name}/documents` - Get documents for collection
- `GET /api/questions` - List questions (AdminQuestions component)

All endpoints trả về cấu trúc:

```json
{
  "success": true,
  "data": [...],
  "total": number,
  "message": "..."
}
```
