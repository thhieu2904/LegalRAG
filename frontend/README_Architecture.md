# Legal RAG Frontend

Giao diện người dùng cho hệ thống Legal RAG - Trợ lý pháp luật AI.

## Kiến trúc

### Cấu trúc thư mục

```
src/
├── components/           # Các component tái sử dụng
│   ├── chat/            # Các component cho chat interface
│   │   ├── ChatInterface.tsx    # Component chính cho chat
│   │   ├── ChatHeader.tsx       # Header của chat
│   │   ├── ChatMessage.tsx      # Component hiển thị tin nhắn
│   │   ├── ChatInput.tsx        # Input để gửi tin nhắn
│   │   └── index.ts             # Export các component
│   └── ui/              # UI components cơ bản
│       ├── button.tsx           # Button component
│       ├── input.tsx            # Input component
│       ├── avatar.tsx           # Avatar component
│       ├── scroll-area.tsx      # Scroll area component
│       └── index.ts             # Export UI components
├── hooks/               # React hooks tùy chỉnh
│   └── useChat.ts       # Hook quản lý state chat
├── pages/               # Các trang của ứng dụng
│   └── ChatPageFinal.tsx # Trang chat chính
├── services/            # Các service gọi API
│   └── chatService.ts   # Service gọi API chat
├── App.tsx              # Component gốc
└── main.tsx             # Entry point
```

### Nguyên tắc thiết kế

#### 1. Tách biệt logic và UI (Separation of Concerns)

- **UI Components**: Chỉ quan tâm đến việc hiển thị và tương tác người dùng
- **Hooks**: Quản lý state và business logic
- **Services**: Xử lý giao tiếp với API

#### 2. Tái sử dụng (Reusability)

- Các UI component cơ bản trong `components/ui/`
- Chat components có thể tái sử dụng cho các dự án khác
- Hook `useChat` có thể sử dụng cho nhiều loại chat interface

#### 3. Dễ bảo trì (Maintainability)

- Mỗi component có trách nhiệm rõ ràng
- TypeScript để type safety
- Naming convention nhất quán

#### 4. Khả năng mở rộng (Extensibility)

- Interface rõ ràng cho props
- Support custom handlers
- Error handling tích hợp

## Components

### ChatInterface

Component chính cho chat interface, kết hợp tất cả các component con.

**Props:**

- `onSendMessage?: (message: string) => Promise<string> | string` - Handler khi gửi tin nhắn
- `initialMessage?: string` - Tin nhắn chào mừng
- `onError?: (error: Error) => void` - Handler khi có lỗi

### ChatHeader

Component header hiển thị thông tin trung tâm và trợ lý AI.

### ChatMessage

Component hiển thị từng tin nhắn trong chat.

**Props:**

- `message: string` - Nội dung tin nhắn
- `isBot: boolean` - Tin nhắn từ bot hay user
- `timestamp: string` - Thời gian gửi

### ChatInput

Component input để gửi tin nhắn.

**Props:**

- `onSendMessage: (message: string) => void` - Callback khi gửi tin nhắn
- `disabled?: boolean` - Disable input khi đang loading

## Hooks

### useChat

Hook quản lý state chat, bao gồm messages, loading state, và functions để gửi tin nhắn.

**Return:**

- `messages` - Danh sách tin nhắn
- `isLoading` - Trạng thái loading
- `sendMessage` - Function gửi tin nhắn
- `addMessage` - Function thêm tin nhắn
- `clearMessages` - Function xóa tất cả tin nhắn

## Services

### ChatService

Service để giao tiếp với backend API.

**Methods:**

- `sendMessage(message: string)` - Gửi tin nhắn và nhận phản hồi
- `resetSession()` - Reset session
- `getSessionId()` - Lấy session ID hiện tại

## Cấu hình

### Environment Variables

```
VITE_API_BASE_URL=http://localhost:8000  # URL của backend API
```

### Dependencies chính

- React 19+ với TypeScript
- Tailwind CSS cho styling
- Lucide React cho icons
- Axios để gọi API

## Cách sử dụng

### Cài đặt

```bash
npm install
```

### Phát triển

```bash
npm run dev
```

### Build

```bash
npm run build
```

## Tùy chỉnh

### Thay đổi theme

Chỉnh sửa file `tailwind.config.js` để thay đổi màu sắc và styling.

### Tùy chỉnh API endpoint

Thay đổi `VITE_API_BASE_URL` trong file `.env`.

### Thêm tính năng mới

1. Tạo component mới trong thư mục tương ứng
2. Export component trong file `index.ts`
3. Sử dụng TypeScript interface để đảm bảo type safety
4. Thêm unit tests nếu cần

## Lưu ý phát triển

### Performance

- Sử dụng `useCallback` và `useMemo` khi cần thiết
- Lazy loading cho các component nặng
- Optimize bundle size

### Accessibility

- Semantic HTML
- Proper ARIA labels
- Keyboard navigation support

### SEO

- Proper meta tags
- Structured data
- Performance optimization
