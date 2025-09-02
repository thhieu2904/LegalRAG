# 🔧 CẤU TRÚC PAGES ĐÚNG CÁCH

## ❌ Cách cũ (phức tạp):

```
pages/
├── simple/          # ← Thừa folder này!
│   ├── ChatPage.tsx
│   ├── AdminPage.tsx
│   └── OCRPage.tsx
└── admin/           # ← Bị trùng lặp
    ├── AdminDashboard.tsx
    └── ...
```

## ✅ Cách mới (đơn giản):

```
pages/
├── ChatPage.tsx     # Chat với RAG service
├── AdminPage.tsx    # Quản lý RAG service
├── OCRPage.tsx      # Xử lý OCR service
└── HomePage.tsx     # Trang chủ (optional)
```

## Import sạch sẽ:

```tsx
// App.tsx
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";
import OCRPage from "./pages/OCRPage";
```

**Nguyên tắc**: 1 page = 1 file, không cần folder con phức tạp!
