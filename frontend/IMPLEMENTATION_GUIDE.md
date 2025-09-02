# 📚 HƯỚNG DẪN CẤU TRÚC FRONTEND ĐƠN GIẢN

## 🎯 **Tóm tắt cấu trúc mới:**

```
src/
├── api/                    # ⭐ TẤT CẢ API CALLS TẬP TRUNG
│   ├── axios-config.ts     # Cấu hình axios cho RAG & OCR services
│   ├── rag-api.ts          # API calls đến RAG service (port 8000)
│   ├── ocr-api.ts          # API calls đến OCR service (port 8001)
│   └── index.ts            # Export tất cả APIs
├── pages/simple/           # ⭐ 3 PAGES CHÍNH
│   ├── ChatPage.tsx        # Chat với RAG service
│   ├── AdminPage.tsx       # Quản lý RAG service
│   └── OCRPage.tsx         # Xử lý OCR service
├── components/
│   └── SimpleNavigation.tsx # Navigation đơn giản
├── SimpleApp.tsx           # App chính với routing
└── main.tsx               # Entry point
```

## 🚀 **Cách sử dụng:**

### 1. **Thay thế App.tsx hiện tại:**

```tsx
// main.tsx
import { createRoot } from "react-dom/client";
import SimpleApp from "./SimpleApp.tsx"; // ← Sử dụng SimpleApp
import "./index.css";

createRoot(document.getElementById("root")!).render(<SimpleApp />);
```

### 2. **Cách gọi API trong components:**

```tsx
// ✅ ĐÚNG - Import từ api/
import { chatAPI, ocrAPI_Service, adminAPI } from '../api';

// Trong component:
const handleSendMessage = async (message: string) => {
  try {
    const response = await chatAPI.sendMessage(message);
    console.log(response);
  } catch (error) {
    console.error(error);
  }
};

// ❌ SAI - Không được tự gọi axios
import axios from 'axios';
axios.post('http://localhost:8000/chat', ...); // ❌ KHÔNG!
```

### 3. **3 Pages chính:**

| Page          | URL              | Service            | Mục đích             |
| ------------- | ---------------- | ------------------ | -------------------- |
| **ChatPage**  | `/` hoặc `/chat` | RAG Service (8000) | Chat với người dùng  |
| **AdminPage** | `/admin`         | RAG Service (8000) | Quản lý hệ thống RAG |
| **OCRPage**   | `/ocr`           | OCR Service (8001) | Xử lý ảnh CCCD       |

## 💡 **Ưu điểm của cấu trúc này:**

### ✅ **Đơn giản và dễ hiểu:**

- 1 page = 1 chức năng chính
- 1 service = 1 API file
- Routing rõ ràng như HTML truyền thống

### ✅ **API tập trung:**

- Tất cả endpoint trong thư mục `api/`
- Không ai được gọi axios trực tiếp
- Error handling tập trung
- Easy to maintain

### ✅ **Microservice ready:**

- RAG service (port 8000) → `rag-api.ts`
- OCR service (port 8001) → `ocr-api.ts`
- Dễ thêm service mới

### ✅ **Dễ mở rộng:**

- Thêm page mới: tạo file trong `pages/simple/`
- Thêm API mới: thêm vào file API tương ứng
- Thêm service mới: tạo api file mới

## 🔧 **Cách triển khai:**

### Bước 1: Backup code cũ

```bash
# Backup folder hiện tại
cp -r src src_backup
```

### Bước 2: Sử dụng cấu trúc mới

```tsx
// src/main.tsx
import SimpleApp from "./SimpleApp.tsx";
// Thay vì import App from './App.tsx';
```

### Bước 3: Test từng page

- Test `/` → ChatPage → RAG service
- Test `/admin` → AdminPage → RAG service
- Test `/ocr` → OCRPage → OCR service

## 📋 **So sánh với cấu trúc cũ:**

| Cũ                            | Mới                          | Cải thiện      |
| ----------------------------- | ---------------------------- | -------------- |
| Multiple API files scattered  | `api/` folder tập trung      | ✅ Dễ maintain |
| Components mixed with pages   | Clear page separation        | ✅ Dễ hiểu     |
| Complex routing               | Simple 3-page routing        | ✅ Đơn giản    |
| No centralized error handling | Interceptors in axios-config | ✅ Better UX   |

## 🚨 **Lưu ý quan trọng:**

1. **Không gọi axios trực tiếp** - Luôn qua API services
2. **1 page = 1 service** - ChatPage/AdminPage → RAG, OCRPage → OCR
3. **Error handling** - Đã được xử lý tự động trong axios interceptors
4. **TypeScript** - Tất cả đã có types rõ ràng

## 🎯 **Kết luận:**

Cấu trúc này **đơn giản, thực tế và phù hợp** với nhu cầu microservice của bạn. Không phức tạp như Clean Architecture nhưng vẫn đảm bảo:

- ✅ Dễ hiểu cho người mới
- ✅ Dễ maintain và mở rộng
- ✅ Phù hợp với microservice
- ✅ API tập trung và có cấu trúc

**Hãy thử nghiệm cấu trúc này và feedback nhé!** 🚀
