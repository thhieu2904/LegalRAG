# ✅ ChatPage Integration Verification Checklist

## Pre-requisites

- [ ] Docker & Docker Compose installed
- [ ] Node.js >= 18 installed
- [ ] All services have `.env` files configured
- [ ] Ports 5173, 8000, 8001 available

## Backend Setup Verification

### 1. Kong Gateway

- [ ] Kong is running: `docker-compose ps kong-gateway`
- [ ] Kong health check passes: `curl http://localhost:8001/status`
- [ ] Kong routes configured: `curl http://localhost:8001/routes | jq`
- [ ] CORS plugin active: Check `kong.yml` for CORS config

### 2. Query Service

- [ ] Query service running: `docker-compose ps query-service`
- [ ] Direct access works: `curl http://localhost:8006/health`
- [ ] Via Kong works: `curl http://localhost:8000/query/health`
- [ ] Logs show no errors: `docker-compose logs query-service`

### 3. Dependent Services

- [ ] Embedding service healthy: `curl http://localhost:8004/health`
- [ ] Vector service healthy: `curl http://localhost:8003/health`
- [ ] LLM service healthy: `curl http://localhost:8008/health`
- [ ] PostgreSQL + pgvector running: `docker-compose ps postgres`

## Frontend Configuration Verification

### 1. Environment Variables

- [ ] `.env.development` exists with Kong URL
- [ ] `VITE_API_BASE_URL=http://localhost:8000`
- [ ] File copied from `.env.example` if missing

### 2. API Configuration

- [ ] `api.constants.ts` uses Kong base URL
- [ ] `endpoints.ts` has correct routes
- [ ] `apiClient` timeout set to 120s (LLM operations)

### 3. Services

- [ ] `queryService.ts` imports from correct paths
- [ ] `sendChatMessage` function exists and exports
- [ ] Types imported from `@/types`

### 4. Store

- [ ] `chatStore.ts` has `sendMessage` method
- [ ] `sendMessage` calls `sendChatMessage` API
- [ ] Error handling implemented
- [ ] Loading states managed

### 5. Components

- [ ] ChatInput component exists and works
- [ ] ChatHistory component exists and works
- [ ] ChatMessage component renders markdown
- [ ] SourceList component shows citations
- [ ] All components have proper types

## Integration Testing

### Test 1: Basic Connectivity

```bash
# Run test script
node frontend/scripts/test-kong-connection.js

Expected: All 4 tests pass (2 health checks, 1 search, 1 chat)
```

- [ ] Query health check passes
- [ ] Admin health check passes
- [ ] Search endpoint works
- [ ] Chat endpoint works

### Test 2: Frontend Build

```bash
cd frontend
npm run build

Expected: Build succeeds without errors
```

- [ ] TypeScript compilation succeeds
- [ ] No type errors
- [ ] No linting errors
- [ ] Build output created in `dist/`

### Test 3: Development Server

```bash
cd frontend
npm run dev

Expected: Server starts on http://localhost:5173
```

- [ ] Vite server starts successfully
- [ ] No console errors
- [ ] Can access http://localhost:5173

### Test 4: ChatPage Rendering

```
Navigate to: http://localhost:5173/chat
```

- [ ] Page loads without errors
- [ ] EmptyState shows with suggestions
- [ ] ChatInput renders with filters
- [ ] No console errors in DevTools

### Test 5: Message Sending (Basic)

```
1. Type "test" in ChatInput
2. Click Send button
```

- [ ] Message appears in ChatHistory immediately (optimistic UI)
- [ ] Request sent to Kong: Check Network tab
- [ ] Request URL: `http://localhost:8000/query/chat`
- [ ] Request method: POST
- [ ] Request headers include Content-Type: application/json

### Test 6: Message Sending (Full Flow)

```
1. Type "Lập trình hướng đối tượng là gì?"
2. Click Send
3. Wait for response
```

- [ ] User message appears (blue, right-aligned)
- [ ] TypingIndicator shows while waiting
- [ ] AI response appears (gray, left-aligned)
- [ ] Response is formatted with markdown
- [ ] Sources show below AI message
- [ ] SourceCard components render correctly
- [ ] Similarity scores display
- [ ] Timestamps show correctly

### Test 7: Filters

```
1. Click Filter button
2. Select "Khoa: CNTT"
3. Select "Môn: CSC101"
4. Send message
```

- [ ] Filter section expands/collapses
- [ ] Filter badge shows count (e.g., "2 bộ lọc")
- [ ] Request includes filters in body
- [ ] Response respects filters

### Test 8: Error Handling

```
1. Stop query service: docker-compose stop query-service
2. Try to send message
```

- [ ] Toast error notification appears
- [ ] Error message is user-friendly
- [ ] Message doesn't get stuck in "sending" state
- [ ] Can retry after service restarts

### Test 9: Loading States

```
1. Send message
2. Observe loading states
```

- [ ] Send button shows spinner while loading
- [ ] Send button disabled while loading
- [ ] Input disabled while loading
- [ ] TypingIndicator appears
- [ ] Loading state clears after response

### Test 10: Auto-scroll

```
1. Send multiple messages (5+)
2. Check scroll behavior
```

- [ ] Scrolls to bottom when new message arrives
- [ ] Smooth scroll animation
- [ ] Maintains scroll position when typing

## Network Verification (Browser DevTools)

### Request Details

```
URL: http://localhost:8000/query/chat
Method: POST
Status: 200 OK
```

**Request Headers:**

- [ ] `Content-Type: application/json`
- [ ] `Accept: application/json`
- [ ] Origin: `http://localhost:5173` (for CORS)

**Request Payload:**

```json
{
  "question": "Lập trình hướng đối tượng là gì?",
  "history": [],
  "top_k": 5,
  "threshold": 0.7,
  "filters": {}
}
```

- [ ] Payload structure matches schema
- [ ] All required fields present
- [ ] Filters object included (even if empty)

**Response:**

```json
{
  "question": "...",
  "answer": "...",
  "sources": [...],
  "citations": [...],
  "tokens_used": 123,
  "took_ms": 456
}
```

- [ ] Response has all required fields
- [ ] Sources array present
- [ ] Tokens and timing included

### Console Verification

- [ ] No CORS errors
- [ ] No 404 errors
- [ ] No type errors
- [ ] No React warnings
- [ ] No unhandled promise rejections

## Performance Checks

### Response Times

- [ ] Health check: < 100ms
- [ ] Search: < 2s
- [ ] Chat (with LLM): < 10s
- [ ] UI updates: immediate (optimistic)

### UI Responsiveness

- [ ] Input lag: none
- [ ] Scroll smooth: 60fps
- [ ] No layout shifts
- [ ] No flash of unstyled content

## Edge Cases

### Empty States

- [ ] Empty message rejected (button disabled)
- [ ] No messages shows EmptyState
- [ ] No sources handled gracefully

### Long Content

- [ ] Long messages wrap correctly
- [ ] Long markdown renders properly
- [ ] Many sources (10+) paginate or scroll
- [ ] Character limit enforced (1000 chars)

### Network Issues

- [ ] Timeout handled (120s)
- [ ] Connection error shows toast
- [ ] Retry doesn't duplicate messages
- [ ] Offline detection (optional)

## Security Checks

### Current (Development)

- [ ] Kong CORS allows localhost:5173
- [ ] No JWT required (testing mode)
- [ ] Rate limiting: 20 req/min
- [ ] No sensitive data in console logs

### TODO (Production)

- [ ] Enable JWT authentication
- [ ] Remove console.logs
- [ ] Use environment-specific URLs
- [ ] Enable HTTPS
- [ ] Add request signing

## Documentation Verification

- [ ] `KONG_INTEGRATION.md` created
- [ ] API flow documented
- [ ] Troubleshooting guide included
- [ ] Test script documented
- [ ] Environment setup explained

## Final Checks

- [ ] All TypeScript errors resolved
- [ ] All ESLint warnings addressed
- [ ] All tests in checklist pass
- [ ] ChatPage works end-to-end
- [ ] Ready for Phase 6 (Admin Feature)

---

## Sign-off

**Tested by:** ********\_********  
**Date:** ********\_********  
**Status:** ☐ PASS ☐ FAIL  
**Notes:**

---

---

---

## Next Steps After Verification

1. ✅ Mark Phase 5 as complete
2. 📝 Document any issues found
3. 🐛 Create tickets for bugs
4. 🚀 Proceed to Phase 6: Admin Feature
5. 🔄 Plan JWT authentication integration
