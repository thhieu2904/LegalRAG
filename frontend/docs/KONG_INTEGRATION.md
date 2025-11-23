# 🔌 Kong Gateway Integration Guide

## Overview

Frontend kết nối với backend services **thông qua Kong Gateway**, không kết nối trực tiếp với services.

```
Frontend (localhost:5173)
    ↓
Kong Gateway (localhost:8000)
    ↓
├─ /query/*  → Query Service (port 8006)
├─ /admin/*  → Admin Service (port 8007)
└─ /auth/*   → Auth Service (port 8005)
```

## Architecture

### Kong Gateway Routes

| Frontend Request               | Kong Route | Backend Service    | Backend Endpoint               |
| ------------------------------ | ---------- | ------------------ | ------------------------------ |
| `POST /query/chat`             | `/query/*` | query-service:8006 | `POST /chat`                   |
| `POST /query/search`           | `/query/*` | query-service:8006 | `POST /search`                 |
| `GET /query/health`            | `/query/*` | query-service:8006 | `GET /health`                  |
| `POST /admin/process-document` | `/admin/*` | admin-service:8007 | `POST /admin/process-document` |
| `GET /admin/health`            | `/admin/*` | admin-service:8007 | `GET /admin/health`            |

**Note**: Query service uses `strip_path: true`, so `/query/chat` → `/chat` in backend.

## Configuration

### Environment Variables

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000  # Kong Gateway

# .env.production
VITE_API_BASE_URL=https://api.yourdomain.com  # Production Kong
```

### API Client

```typescript
// src/services/api/client.ts
export const apiClient = axios.create({
  baseURL: API_BASE_URL, // http://localhost:8000
  timeout: 120000, // 2 minutes for LLM
});
```

### Endpoints

```typescript
// src/services/api/endpoints.ts
export const ENDPOINTS = {
  QUERY: {
    CHAT: '/query/chat', // → Kong → query-service:8006/chat
    SEARCH: '/query/search', // → Kong → query-service:8006/search
    HEALTH: '/query/health', // → Kong → query-service:8006/health
  },
  ADMIN: {
    PROCESS_DOCUMENT: '/admin/process-document',
    HEALTH: '/admin/health',
  },
};
```

## Setup & Testing

### 1. Start Services

```bash
# Start all services (including Kong Gateway)
cd d:\Personal\AI_Center\aicenter-rag
docker-compose up -d

# Check services status
docker-compose ps

# View Kong logs
docker-compose logs -f kong-gateway
```

### 2. Verify Kong Gateway

```bash
# Check Kong health
curl http://localhost:8001/status

# Check Kong routes
curl http://localhost:8001/services
curl http://localhost:8001/routes
```

### 3. Test Backend via Kong

```bash
# Test query service health
curl http://localhost:8000/query/health

# Test admin service health
curl http://localhost:8000/admin/health

# Test chat endpoint
curl -X POST http://localhost:8000/query/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Lập trình hướng đối tượng là gì?",
    "history": [],
    "top_k": 5,
    "threshold": 0.7,
    "filters": {}
  }'
```

### 4. Run Frontend Test Script

```bash
cd frontend

# Install dependencies (if not already)
npm install

# Run Kong connection test
node scripts/test-kong-connection.js
```

### 5. Start Frontend

```bash
# Development mode
npm run dev

# Frontend will connect to Kong at localhost:8000
```

## Testing ChatPage

### Manual Testing Steps

1. **Start Services**:

   ```bash
   docker-compose up -d
   ```

2. **Start Frontend**:

   ```bash
   cd frontend
   npm run dev
   ```

3. **Open Browser**:

   ```
   http://localhost:5173/chat
   ```

4. **Test Chat Flow**:
   - Type a question in ChatInput
   - Click Send or press Enter
   - Verify request goes through Kong Gateway
   - Check response displays in ChatHistory
   - Verify source citations show up

### Expected Flow

```
User types "OOP là gì?"
    ↓
ChatInput → ChatPage.handleSendMessage
    ↓
chatStore.sendMessage
    ↓
queryService.sendChatMessage
    ↓
axios.post(http://localhost:8000/query/chat)
    ↓
Kong Gateway
    ↓
Query Service (port 8006) → /chat
    ↓
Embedding Service → Vector Service → LLM Service
    ↓
Response with answer + sources
    ↓
ChatHistory renders message
    ↓
User sees AI response with citations
```

## Debugging

### Check Kong Logs

```bash
# View Kong access logs
docker-compose logs -f kong-gateway

# You should see requests like:
# POST /query/chat HTTP/1.1" 200
```

### Check Backend Logs

```bash
# Query service logs
docker-compose logs -f query-service

# You should see:
# 📨 Nhận request chat: Lập trình hướng đối tượng là gì?
```

### Network Tab (Browser DevTools)

1. Open DevTools (F12)
2. Go to Network tab
3. Send a chat message
4. Check request:
   - URL: `http://localhost:8000/query/chat`
   - Method: POST
   - Status: 200
   - Response: JSON with answer and sources

### Common Issues

**Issue 1: CORS Error**

```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Solution**: Check Kong CORS plugin in `kong.yml`:

```yaml
plugins:
  - name: cors
    config:
      origins:
        - http://localhost:5173
```

**Issue 2: Connection Refused**

```
Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Solution**:

- Check Kong is running: `docker-compose ps kong-gateway`
- Check Kong port: `docker-compose port kong-gateway 8000`

**Issue 3: 404 Not Found**

```
{"message":"no Route matched with those values"}
```

**Solution**:

- Check route configuration in `kong.yml`
- Verify endpoint path matches Kong routes

**Issue 4: 500 Internal Server Error**

```
{"message":"An unexpected error occurred"}
```

**Solution**:

- Check backend service logs: `docker-compose logs query-service`
- Verify all dependent services are running (embedding, vector, llm)

## Kong Gateway Ports

- **8000**: Proxy port (client requests) - **USE THIS**
- **8001**: Admin API (management)
- **8443**: Proxy port (HTTPS)
- **8444**: Admin API (HTTPS)

## Security Notes

### Current Setup (Development)

- ✅ CORS enabled for localhost
- ⚠️ JWT temporarily disabled for testing
- ⚠️ Rate limiting: 20 req/min per service

### Production Setup (TODO)

- [ ] Enable JWT authentication
- [ ] Use HTTPS (ports 8443/8444)
- [ ] Stricter CORS (specific domains)
- [ ] Lower rate limits
- [ ] Add API key authentication
- [ ] Enable request logging
- [ ] Add distributed tracing (correlation-id)

## Next Steps

1. ✅ Test ChatPage with Kong Gateway
2. ✅ Verify all endpoints work
3. ✅ Test error handling
4. ⏳ Implement JWT authentication
5. ⏳ Add loading states
6. ⏳ Add retry logic
7. ⏳ Add request caching

## Resources

- Kong Documentation: https://docs.konghq.com/
- Kong Gateway Config: `kong-gateway/config/kong.yml`
- Docker Compose: `docker-compose.yml`
- Frontend API Client: `frontend/src/services/api/client.ts`
