# 🚀 SSE Streaming Implementation Plan

## Tổng quan

Tài liệu này mô tả chi tiết kế hoạch triển khai **Server-Sent Events (SSE) Streaming** cho LegalRAG, cho phép response từ LLM được stream realtime về frontend thay vì đợi full response.

**Mục tiêu:**

- Giảm perceived latency từ 5-30s → ~1s (first token)
- UX tương tự ChatGPT/Claude
- Backward compatible với endpoint hiện tại
- Fallback graceful khi streaming không khả dụng

---

## 1. Kiến trúc hiện tại vs Mới

### 1.1 Flow hiện tại (Blocking)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              CURRENT FLOW                                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Timeline: ════════════════════════════════════════════════════════════════►    │
│                                                                                  │
│  Frontend:  [POST /query]──────────────────────────────────[JSON Response]       │
│                    │                                              │              │
│                    │         ⏳ 5-30 seconds blocking             │              │
│                    │         (User sees loading spinner)          │              │
│                    ▼                                              │              │
│                                                                                  │
│  Query      [Receive]→[Embed]→[Search]→[Rerank]→[Call LLM]→[Return]             │
│  Service       │        100ms   200ms    300ms   3-25s        │                  │
│                │                                              │                  │
│                ▼                                              ▼                  │
│  LLM        [Receive prompt]────────[Generate ALL tokens]────[Return full text] │
│  Service              │               (blocking)                    │            │
│                       └─────────────────────────────────────────────┘            │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Flow mới (SSE Streaming)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              SSE STREAMING FLOW                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Timeline: ════════════════════════════════════════════════════════════════►    │
│                                                                                  │
│  Frontend:  [POST /chat]──[sources]──[token]──[token]──[token]──...──[done]     │
│                    │          │         │        │        │            │         │
│                    │          │       "Theo"   "quy"   "định"   ...   "."        │
│                    │          │         ▲        ▲        ▲            ▲         │
│                    ▼          ▼         │        │        │            │         │
│                                                                                  │
│  Query      [Embed+Search+Rerank]──────[Stream from LLM]───────────────┘         │
│  Service         ~600ms                       │                                  │
│                                               │                                  │
│                    ┌──────────────────────────┘                                  │
│                    ▼                                                             │
│  LLM        [Generate token]→[yield]→[Generate token]→[yield]→...→[done]        │
│  Service           │            │            │            │                      │
│                    └────────────┴────────────┴────────────┘                      │
│                         Tokens streamed as generated                             │
│                                                                                  │
│  ✨ User sees text appearing in real-time!                                       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Endpoint Design

### 2.1 Naming Strategy

**Quyết định: Dùng endpoint mới `/chat` thay vì `/query/stream`**

| Aspect       | `/query` (cũ)                     | `/chat` (mới)     |
| ------------ | --------------------------------- | ----------------- |
| Method       | POST                              | POST              |
| Response     | JSON (blocking)                   | SSE (streaming)   |
| Use case     | API integrations, backward compat | Real-time chat UI |
| Request body | Giống nhau                        | Giống nhau        |

**Lý do chọn `/chat`:**

- Ngắn gọn, semantic (chat = conversation)
- Không gây nhầm lẫn với `/query`
- Dễ route ở frontend

### 2.2 SSE Event Format

```
event: sources
data: {"documents": [{"id": "...", "title": "..."}], "chunks_used": 5}

event: token
data: Theo

event: token
data: quy

event: token
data: định

...

event: done
data: {"tokens_used": 234, "took_ms": 1523}
```

### 2.3 Request/Response Schema

**Request (giống /query):**

```typescript
interface ChatRequest {
  question: string;
  session_id?: string | null;
  top_k?: number;
  threshold?: number;
  history?: HistoryMessage[];
}
```

**SSE Events:**

```typescript
// Event: sources (sent first, after retrieval)
interface SourcesEvent {
  documents: Array<{
    id: string;
    title: string;
    relevance: number;
  }>;
  chunks_used: number;
  session_id: string;
  used_pinned_document: boolean;
  pinned_document_title?: string;
}

// Event: token (sent for each token)
type TokenEvent = string; // Raw token text

// Event: done (sent last)
interface DoneEvent {
  tokens_used: number;
  took_ms: number;
}

// Event: error (if something fails)
interface ErrorEvent {
  error: string;
  code: string;
}

// Event: clarification (if ambiguous query)
interface ClarificationEvent {
  message: string;
  options: DocumentOption[];
}
```

---

## 3. Implementation Details

### 3.1 LLM Service Changes

**File: `llm-service/src/main.py`**

```python
# NEW ENDPOINT - thêm vào cuối file, KHÔNG sửa endpoint cũ

from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

@app.post("/generate-rag-stream")
async def generate_rag_stream(request: RAGGenerateRequest):
    """
    Stream RAG response token by token.

    Returns: text/event-stream với SSE format
    """
    provider = get_llm_provider()

    if not provider.is_ready:
        raise HTTPException(
            status_code=503,
            detail=f"LLM provider ({provider.provider_name}) not ready"
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Build prompt
            formatted_prompt = prompt_builder.build_prompt_for_provider(
                question=request.question,
                context=request.context,
                history=request.history,
                provider=settings.llm_provider
            )

            token_count = 0

            # Stream tokens
            async for token in provider.generate_stream(
                prompt=formatted_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ):
                token_count += 1
                yield f"data: {token}\n\n"

            # Done
            yield f"event: done\ndata: {token_count}\n\n"

        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

**File: `llm-service/src/providers/gemini_provider.py`**

```python
# THÊM method mới vào class GeminiProvider

async def generate_stream(
    self,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """Stream tokens từ Gemini API."""
    if not self.is_ready or self._model is None:
        raise RuntimeError("Gemini client not initialized")

    max_tokens = max_tokens or settings.gemini_max_output_tokens
    temperature = temperature or settings.gemini_temperature

    generation_config = self._genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens
    )

    # Gemini streaming
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: self._model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=True  # Enable streaming!
        )
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text
```

**File: `llm-service/src/providers/local_provider.py`**

```python
# THÊM method mới vào class LocalProvider

async def generate_stream(
    self,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """Stream tokens từ llama-cpp."""
    if not self.is_ready or self._model is None:
        raise RuntimeError("Model not loaded")

    max_tokens = max_tokens or settings.max_tokens
    temperature = temperature or settings.temperature

    # llama-cpp-python đã hỗ trợ streaming native
    for output in self._model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True  # Enable streaming!
    ):
        token = output["choices"][0]["text"]
        if token:
            yield token
```

### 3.2 Query Service Changes

**File: `query-service/src/main.py`**

```python
# THÊM imports
from sse_starlette.sse import EventSourceResponse
import json

# THÊM endpoint mới - KHÔNG sửa /query endpoint

@app.post("/chat")
async def chat_stream(request: QueryRequest):
    """
    SSE Streaming endpoint for chat.

    Flow:
    1. Embed + Search + Rerank (same as /query)
    2. Stream "sources" event with document info
    3. Stream "token" events from LLM
    4. Stream "done" event with stats

    Falls back to clarification if needed (non-streaming).
    """
    start_time = time.time()

    async def event_generator():
        try:
            # === PHASE 1: Context Retrieval (same logic as /query) ===
            session_id, is_new_session = get_or_create_session_id(request.session_id)
            state = get_conversation_state(session_id)

            if is_new_session:
                save_conversation_state(state)

            # Check small talk
            if is_small_talk(request.question):
                yield {
                    "event": "token",
                    "data": "Xin chào! Tôi là trợ lý AI tra cứu văn bản pháp luật. Bạn có thể hỏi tôi về các thủ tục hành chính như đăng ký khai sinh, kết hôn, cấp CCCD. Tôi sẵn sàng hỗ trợ bạn!"
                }
                yield {
                    "event": "done",
                    "data": json.dumps({"tokens_used": 0, "took_ms": int((time.time() - start_time) * 1000)})
                }
                return

            # Embed + Search + Rerank
            use_pinned = should_use_pinned_document(request.question, state)
            embedding = await embed_text(request.question)

            if use_pinned and state.active_document_id:
                search_results = await search_pinned_document(embedding, state.active_document_id)
            else:
                search_results = await search_vectors(embedding)

            if not search_results:
                yield {
                    "event": "token",
                    "data": "Xin lỗi, tôi không tìm thấy thông tin liên quan. Vui lòng thử lại với câu hỏi khác."
                }
                yield {
                    "event": "done",
                    "data": json.dumps({"tokens_used": 0, "took_ms": int((time.time() - start_time) * 1000)})
                }
                return

            reranked_results, document_scores = await rerank_documents(
                request.question, search_results, top_k=settings.RERANK_TOP_K
            )

            # Check clarification
            max_score = max(r.get('rerank_score', 0) for r in reranked_results)

            if max_score < settings.CLARIFICATION_THRESHOLD and document_scores:
                # Need clarification - send as special event
                titles_map = db_client.fetch_document_titles([d['document_id'] for d in document_scores])
                options = [
                    {
                        "document_id": d['document_id'],
                        "title": titles_map.get(d['document_id'], "Văn bản"),
                        "confidence": d.get('avg_score', 0)
                    }
                    for d in document_scores[:3]
                ]
                yield {
                    "event": "clarification",
                    "data": json.dumps({
                        "message": "Tôi tìm thấy nhiều văn bản liên quan. Bạn muốn xem văn bản nào?",
                        "options": options,
                        "session_id": session_id
                    })
                }
                return

            # === PHASE 2: Send sources event ===
            sources = []
            for r in reranked_results[:5]:
                sources.append({
                    "id": r.get('document_id'),
                    "title": r.get('document_title', 'Văn bản'),
                    "relevance": r.get('rerank_score', 0)
                })

            yield {
                "event": "sources",
                "data": json.dumps({
                    "documents": sources,
                    "chunks_used": len(reranked_results),
                    "session_id": session_id,
                    "used_pinned_document": use_pinned,
                    "pinned_document_title": state.active_document_title if use_pinned else None
                })
            }

            # === PHASE 3: Stream from LLM ===
            context = build_context(reranked_results)
            history = request.history if request.history else None

            tokens_used = 0

            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{settings.LLM_SERVICE_URL}/generate-rag-stream",
                    json={
                        "question": request.question,
                        "context": context,
                        "history": history
                    },
                    timeout=120.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            token = line[6:]  # Remove "data: " prefix
                            tokens_used += 1
                            yield {"event": "token", "data": token}
                        elif line.startswith("event: done"):
                            pass  # Will send our own done event
                        elif line.startswith("event: error"):
                            yield {"event": "error", "data": line.split("data: ")[1] if "data: " in line else "Unknown error"}
                            return

            # Update session state (pin document if confident)
            if not use_pinned and max_score >= settings.PIN_THRESHOLD and reranked_results:
                top_doc = reranked_results[0]
                state.active_document_id = top_doc.get('document_id')
                state.active_document_title = top_doc.get('document_title')
                save_conversation_state(state)

            # === PHASE 4: Done ===
            took_ms = int((time.time() - start_time) * 1000)
            yield {
                "event": "done",
                "data": json.dumps({
                    "tokens_used": tokens_used,
                    "took_ms": took_ms,
                    "session_id": session_id
                })
            }

            # Log query
            if db_client:
                db_client.log_query(
                    session_id=session_id,
                    query_text=request.question,
                    response_type="streaming_answer",
                    tokens_used=tokens_used,
                    latency_ms=took_ms
                )

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e), "code": "INTERNAL_ERROR"})
            }

    return EventSourceResponse(event_generator())
```

**File: `query-service/requirements.txt`**

```
# THÊM dependency
sse-starlette==1.8.2
```

### 3.3 Frontend Changes

**File: `frontend/src/services/query/queryService.ts`**

```typescript
// THÊM function mới

export interface StreamCallbacks {
  onSources?: (sources: SourcesEvent) => void;
  onToken?: (token: string) => void;
  onDone?: (stats: DoneEvent) => void;
  onError?: (error: ErrorEvent) => void;
  onClarification?: (clarification: ClarificationEvent) => void;
}

/**
 * Stream chat response using SSE
 */
export const streamChatMessage = async (
  request: ChatRequest,
  callbacks: StreamCallbacks
): Promise<void> => {
  const response = await fetch(`${QUERY_SERVICE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No reader available");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          const eventType = line.slice(7);
          // Next line should be data
          continue;
        }

        if (line.startsWith("data: ")) {
          const data = line.slice(6);

          // Parse based on context (simple heuristic)
          try {
            const parsed = JSON.parse(data);

            if (parsed.documents) {
              callbacks.onSources?.(parsed);
            } else if (parsed.options) {
              callbacks.onClarification?.(parsed);
            } else if (parsed.tokens_used !== undefined) {
              callbacks.onDone?.(parsed);
            } else if (parsed.error) {
              callbacks.onError?.(parsed);
            }
          } catch {
            // Plain text token
            callbacks.onToken?.(data);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};
```

**File: `frontend/src/stores/chatStore.ts`**

```typescript
// THÊM vào interface ChatState
streamMessage: (message: string, filters: FilterOptions) => Promise<void>;

// THÊM implementation
streamMessage: async (question: string, _filters: FilterOptions) => {
  const { messages, addMessage, updateMessage, setLoading, setError } = get();

  // Create user message
  const userMessage: ChatMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: question,
    timestamp: new Date(),
  };
  addMessage(userMessage);

  // Create placeholder for AI response
  const aiMessageId = (Date.now() + 1).toString();
  const aiMessage: ChatMessage = {
    id: aiMessageId,
    role: 'assistant',
    content: '',
    timestamp: new Date(),
  };
  addMessage(aiMessage);

  setLoading(true);
  setError(null);

  try {
    const sessionId = getCurrentSessionId();
    const history = buildHistoryForAPI(messages);

    await streamChatMessage(
      {
        question,
        session_id: sessionId,
        history: history.length > 0 ? history : undefined,
      },
      {
        onSources: (sources) => {
          // Update message with sources
          updateMessage(aiMessageId, {
            sources: sources.documents.map(d => ({
              document_id: d.id,
              document_title: d.title,
              similarity: d.relevance,
            })),
          });

          // Save session ID
          if (sources.session_id) {
            saveSessionId(sources.session_id);
          }
        },

        onToken: (token) => {
          // Append token to message content
          const current = get().messages.find(m => m.id === aiMessageId);
          if (current) {
            updateMessage(aiMessageId, {
              content: current.content + token,
            });
          }
        },

        onDone: (stats) => {
          updateMessage(aiMessageId, {
            tokens: stats.tokens_used,
            took_ms: stats.took_ms,
          });
        },

        onError: (error) => {
          updateMessage(aiMessageId, {
            content: `Đã xảy ra lỗi: ${error.error}`,
          });
          setError(error.error);
        },

        onClarification: (clarification) => {
          updateMessage(aiMessageId, {
            content: clarification.message,
            needs_clarification: true,
            document_options: clarification.options,
            originalQuestion: question,
          });
        },
      }
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Lỗi không xác định';
    setError(errorMessage);

    // Fallback to sync
    console.warn('Streaming failed, falling back to sync:', error);
    const current = get().messages.find(m => m.id === aiMessageId);
    if (current && !current.content) {
      // Remove empty AI message and retry with sync
      set(state => ({
        messages: state.messages.filter(m => m.id !== aiMessageId)
      }));
      return get().sendMessage(question, _filters);
    }
  } finally {
    setLoading(false);
  }
},
```

**File: `frontend/src/pages/ChatPage/index.tsx`**

```typescript
// Sửa handleSendMessage để dùng streaming

const handleSendMessage = async (message: string, filters: FilterOptions) => {
  try {
    // Prefer streaming, fallback handled inside streamMessage
    await streamMessage(message, filters);
  } catch (error) {
    addToast({
      type: "error",
      message:
        error instanceof Error
          ? error.message
          : "Đã xảy ra lỗi khi gửi tin nhắn",
    });
  }
};
```

---

## 4. Backward Compatibility

### 4.1 API Compatibility Matrix

| Client       | Backend     | Behavior                     |
| ------------ | ----------- | ---------------------------- |
| Old Frontend | Old Backend | ✅ Uses `/query`             |
| Old Frontend | New Backend | ✅ Uses `/query` (unchanged) |
| New Frontend | Old Backend | ✅ Fallback to `/query`      |
| New Frontend | New Backend | ✅ Uses `/chat` (streaming)  |
| External API | Any Backend | ✅ Uses `/query` (unchanged) |

### 4.2 Fallback Logic

```typescript
// Frontend: Automatic fallback
const sendMessage = async (question: string) => {
  try {
    // 1. Try streaming first
    await streamMessage(question);
  } catch (streamError) {
    console.warn("Streaming failed:", streamError);

    // 2. Fallback to sync
    await sendMessageSync(question);
  }
};
```

### 4.3 Feature Detection

```typescript
// Optional: Check if streaming is available
const checkStreamingSupport = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${QUERY_SERVICE_URL}/chat`, {
      method: "OPTIONS",
    });
    return response.ok;
  } catch {
    return false;
  }
};
```

---

## 5. Docker Configuration

### 5.1 docker-compose.gemini.yml updates

```yaml
# Không cần thay đổi cấu hình Docker
# SSE hoạt động qua HTTP bình thường
# Chỉ cần đảm bảo không có proxy buffering

services:
  query-service:
    environment:
      # Thêm flag để enable streaming
      ENABLE_STREAMING: "true"
```

### 5.2 Nginx considerations (nếu có)

```nginx
# Disable buffering for SSE
location /chat {
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

---

## 6. Testing

### 6.1 Manual Testing

```bash
# Test SSE endpoint với curl
curl -N -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"question": "thủ tục đăng ký khai sinh"}'

# Expected output:
# event: sources
# data: {"documents": [...], "session_id": "20251206_0001"}
#
# event: token
# data: Theo
#
# event: token
# data: quy
# ...
# event: done
# data: {"tokens_used": 234, "took_ms": 1523}
```

### 6.2 Unit Tests

```python
# query-service/tests/test_streaming.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_stream_basic():
    async with AsyncClient(base_url="http://localhost:8002") as client:
        async with client.stream(
            "POST",
            "/chat",
            json={"question": "xin chào"}
        ) as response:
            events = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line)

            assert any("token" in e for e in events)
            assert any("done" in e for e in events)
```

---

## 7. Implementation Checklist

### Phase 1: LLM Service (2-3 giờ)

- [ ] Thêm `generate_stream` method vào `BaseLLMProvider`
- [ ] Implement `generate_stream` cho `GeminiProvider`
- [ ] Implement `generate_stream` cho `LocalProvider`
- [ ] Thêm `/generate-rag-stream` endpoint
- [ ] Test với curl

### Phase 2: Query Service (3-4 giờ)

- [ ] Thêm `sse-starlette` vào requirements.txt
- [ ] Implement `/chat` endpoint
- [ ] Handle clarification flow trong streaming
- [ ] Test với curl
- [ ] Test session management

### Phase 3: Frontend (3-4 giờ)

- [ ] Thêm `streamChatMessage` function
- [ ] Thêm `streamMessage` action vào chatStore
- [ ] Update ChatPage để dùng streaming
- [ ] Implement fallback logic
- [ ] Test real-time token display
- [ ] Test clarification flow

### Phase 4: Integration & Polish (2-3 giờ)

- [ ] End-to-end testing
- [ ] Performance benchmarking
- [ ] Error handling edge cases
- [ ] Documentation updates

---

## 8. Rollback Plan

Nếu có vấn đề, rollback đơn giản:

1. **Frontend**: Đổi `streamMessage` → `sendMessage` trong ChatPage
2. **Backend**: Các endpoint cũ (`/query`, `/generate-rag`) không bị ảnh hưởng

```typescript
// Quick rollback in ChatPage
const handleSendMessage = async (message: string, filters: FilterOptions) => {
  // await streamMessage(message, filters);  // Comment out
  await sendMessage(message, filters); // Use sync
};
```

---

## 9. Performance Expectations

| Metric              | Before (Sync) | After (SSE) | Improvement |
| ------------------- | ------------- | ----------- | ----------- |
| Time to first token | 5-30s         | ~1s         | 5-30x       |
| Perceived latency   | 5-30s         | ~1s         | 5-30x       |
| Total response time | 5-30s         | 5-30s       | Same        |
| Server resources    | Same          | Same        | Same        |

**Note:** Total time không thay đổi, nhưng UX cải thiện đáng kể vì user thấy text xuất hiện ngay.

---

## 10. Future Enhancements

Sau khi SSE hoạt động, có thể mở rộng:

1. **TTS Integration**: Stream audio cùng với text
2. **Cancel Support**: Cho phép user cancel mid-stream
3. **Retry Logic**: Tự động retry nếu stream bị ngắt
4. **Progress Indicators**: Hiển thị % completion
5. **Voice Service**: Tách thành service riêng cho voice interaction

---

_Last updated: 2024-12-06_
_Author: GitHub Copilot_
_Status: Planning_
