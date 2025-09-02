# 🏗️ CẤU TRÚC FRONTEND ĐƠN GIẢN CHO MICROSERVICE

## Cấu trúc thư mục đề xuất:

```
src/
├── api/                    # ⭐ TẤT CẢ API CALLS TẬP TRUNG
│   ├── axios-config.ts     # Cấu hình axios chung
│   ├── rag-api.ts          # Tất cả API calls đến RAG service
│   ├── ocr-api.ts          # Tất cả API calls đến OCR service
│   └── index.ts            # Export tất cả API services
├── pages/                  # ⭐ CÁC TRANG CHÍNH
│   ├── ChatPage.tsx        # Chat với RAG service
│   ├── AdminPage.tsx       # Quản lý RAG service
│   ├── OCRPage.tsx         # Xử lý OCR service
│   └── HomePage.tsx        # Trang chủ
├── components/             # ⭐ COMPONENTS TÁI SỬ DỤNG
│   ├── chat/              # Components cho chat
│   ├── admin/             # Components cho admin
│   ├── ocr/               # Components cho OCR
│   └── ui/                # UI components cơ bản
├── hooks/                 # Custom hooks
├── types/                 # TypeScript types
├── utils/                 # Utility functions
├── App.tsx               # Main app với routing
└── main.tsx              # Entry point
```

## Nguyên tắc đơn giản:

### 1. Page-Based Management (giống HTML truyền thống)

- **1 Page = 1 Chức năng chính**
- **1 Page = 1 Service backend**
- Dễ hiểu, dễ maintain

### 2. API Service tập trung

- **Tất cả endpoint trong api/ folder**
- **Không ai được tự gọi axios trực tiếp**
- **Centralized error handling**

### 3. Component theo chức năng

- Chat components cho ChatPage
- Admin components cho AdminPage
- OCR components cho OCRPage
