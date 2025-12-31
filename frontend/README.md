# LegalRAG Frontend

Giao diện người dùng cho hệ thống hỏi-đáp pháp luật LegalRAG.

## Công nghệ

- React 18
- TypeScript
- Vite
- shadcn/ui (component library)
- React Router
- Zustand (state management)
- React Hook Form + Zod (form validation)

## Cài đặt

```bash
npm install
```

## Chạy development server

```bash
npm run dev
```

Truy cập: http://localhost:5173

## Build production

```bash
npm run build
```

## Cấu trúc thư mục

```
src/
├── components/     # UI components (140+ components)
├── pages/          # Route pages
├── layouts/        # Layout components
├── hooks/          # Custom React hooks
├── services/       # API service calls
├── stores/         # Zustand state stores
├── types/          # TypeScript type definitions
├── utils/          # Utility functions
├── constants/      # App constants
├── styles/         # Global styles
├── assets/         # Static assets
└── lib/            # Third-party library configs
```

## Các trang chính

### Người dùng

- `/` - Trang chủ, giao diện chat hỏi-đáp
- `/collections` - Danh sách bộ thủ tục
- `/documents` - Xem tài liệu

### Admin

- `/admin/login` - Đăng nhập admin
- `/admin/dashboard` - Dashboard quản trị
- `/admin/collections` - Quản lý bộ thủ tục
- `/admin/documents` - Quản lý tài liệu
- `/admin/forms` - Quản lý biểu mẫu

## Biến môi trường

Tạo file `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_APP_TITLE=LegalRAG System
```
