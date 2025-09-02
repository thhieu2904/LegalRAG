# 🏗️ CLEAN ARCHITECTURE CHO REACT MICROSERVICE

## 1. Cấu trúc thư mục chuẩn

```
src/
├── domain/                 # DOMAIN LAYER - Business Logic
│   ├── entities/          # Entities (User, Message, OCRData)
│   ├── repositories/      # Repository Interfaces
│   └── services/          # Domain Services
├── application/           # APPLICATION LAYER - Use Cases
│   ├── use-cases/        # Business Use Cases
│   └── services/         # Application Services
├── infrastructure/        # INFRASTRUCTURE LAYER - External
│   ├── api/              # API Clients
│   ├── storage/          # Local Storage, Cache
│   └── services/         # External Services
├── presentation/          # PRESENTATION LAYER - UI
│   ├── components/       # Reusable Components
│   ├── pages/           # Page Components
│   ├── hooks/           # Custom Hooks
│   ├── contexts/        # React Contexts
│   └── layouts/         # Layout Components
├── shared/               # SHARED UTILITIES
│   ├── constants/       # App Constants
│   ├── types/          # Shared Types
│   └── utils/          # Utility Functions
└── main.tsx             # Entry Point
```

## 2. Nguyên tắc Dependency Inversion

- **Domain Layer**: Không phụ thuộc vào layer nào khác
- **Application Layer**: Chỉ phụ thuộc vào Domain
- **Infrastructure Layer**: Implement interfaces từ Domain/Application
- **Presentation Layer**: Chỉ phụ thuộc vào Application Layer

## 3. Microservice Communication

### Service-to-Service Communication:

- **Synchronous**: HTTP/REST APIs
- **Asynchronous**: Event-driven architecture
- **Error Handling**: Centralized error boundaries
- **Authentication**: JWT tokens, service mesh

### Frontend Service Integration:

```typescript
// Infrastructure Layer - API Clients
class ChatAPIClient implements IChatRepository {
  async sendMessage(message: string): Promise<string> {
    return await httpClient.post("/api/chat", { message });
  }
}

class OCRAPIClient implements IOCRRepository {
  async processImage(file: File): Promise<OCRData> {
    return await httpClient.post("/api/ocr", formData);
  }
}

// Application Layer - Service Configuration
export const configureServices = () => {
  const chatRepo = new ChatAPIClient();
  const ocrRepo = new OCRAPIClient();
  const notificationService = new ToastNotificationService();

  return {
    sendMessageUseCase: new SendMessageUseCase(chatRepo, notificationService),
    processImageUseCase: new ProcessImageUseCase(ocrRepo, notificationService),
  };
};
```

## 4. Page Management Strategy

### Traditional HTML vs React SPA:

**HTML Approach:**

- Multiple .html files
- Server-side routing
- Page reloads

**React SPA Approach (Recommended):**

- Single HTML file
- Client-side routing (React Router)
- Component-based pages
- Lazy loading for performance

### Page Organization:

```typescript
// Domain-based page grouping
pages/
├── chat/
│   ├── ChatPage.tsx
│   └── ChatHistoryPage.tsx
├── admin/
│   ├── AdminDashboardPage.tsx
│   ├── AdminUsersPage.tsx
│   └── AdminSettingsPage.tsx
├── ocr/
│   ├── OCRUploadPage.tsx
│   └── OCRHistoryPage.tsx
└── shared/
    ├── HomePage.tsx
    └── NotFoundPage.tsx
```

## 5. State Management Strategy

### Local State (React hooks):

- Component-specific state
- Form data
- UI state (loading, errors)

### Global State (Context API/Zustand):

- User authentication
- Application settings
- Cross-component data

### Server State (React Query):

- API data caching
- Background updates
- Optimistic updates

## 6. Error Handling Strategy

```typescript
// Error Boundary for each microservice
<ChatErrorBoundary>
  <ChatPage />
</ChatErrorBoundary>

<OCRErrorBoundary>
  <OCRPage />
</OCRErrorBoundary>
```

## 7. Testing Strategy

```
__tests__/
├── unit/           # Unit tests for use cases, services
├── integration/    # API integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test data fixtures
```
