# Plan: LLM Provider Pattern + TTS Auto-read

> **Mục tiêu:** Tích hợp Gemini API và TTS auto-read vào LegalRAG
> **Phương pháp:** Provider Pattern trong 1 service duy nhất
> **Ngày tạo:** 2024-12-01

---

## Tổng quan

| Phase       | Nội dung             | Độ ưu tiên | Effort     |
| ----------- | -------------------- | ---------- | ---------- |
| **Phase 1** | LLM Provider Pattern | Cao        | Trung bình |
| **Phase 2** | TTS Auto-read        | Trung bình | Thấp       |

---

# PHASE 1: LLM Provider Pattern

## Mục tiêu

- Chuyển đổi giữa Vistral local và Gemini API chỉ bằng 1 ENV variable
- Không ảnh hưởng query-service (giữ nguyên API contract)
- Dễ mở rộng thêm providers khác (OpenAI, Claude...)

## Cấu trúc thư mục

```
llm-service/
├── src/
│   ├── config.py              # + llm_provider, gemini_* settings
│   ├── main.py                # Factory pattern chọn provider
│   ├── models.py              # Giữ nguyên
│   ├── providers/             # THƯ MỤC MỚI
│   │   ├── __init__.py        # Export providers
│   │   ├── base.py            # Abstract BaseLLMProvider
│   │   ├── local_provider.py  # Wrap Vistral (code từ main.py hiện tại)
│   │   └── gemini_provider.py # Gemini API client
│   └── services/
│       └── prompt_builder.py  # + build_prompt_for_provider()
├── prompts/                   # Giữ nguyên - dùng chung
│   ├── system_prompt.txt
│   └── citation_rules.txt
├── requirements.txt           # + google-generativeai, tenacity
└── .env                       # + LLM_PROVIDER, GEMINI_*
```

## Các bước thực hiện

### Bước 1.1: Cập nhật Config

**File:** `llm-service/src/config.py`

**Thêm settings:**

```python
# LLM Provider Selection
llm_provider: str = "local"  # "local" | "gemini"

# Gemini Settings (chỉ dùng khi llm_provider = "gemini")
gemini_api_key: Optional[str] = None
gemini_model: str = "gemini-2.5-flash-lite"
gemini_temperature: float = 0.3
gemini_max_output_tokens: int = 1024
gemini_top_p: float = 0.95
gemini_top_k: int = 40
```

**Checklist:**

- [ ] Thêm `llm_provider` field
- [ ] Thêm các `gemini_*` fields
- [ ] Giữ nguyên tất cả local settings hiện tại

---

### Bước 1.2: Tạo Provider Structure

#### 1.2.1: Tạo `providers/__init__.py`

**File:** `llm-service/src/providers/__init__.py`

```python
from .base import BaseLLMProvider
from .local_provider import LocalProvider
from .gemini_provider import GeminiProvider

__all__ = ["BaseLLMProvider", "LocalProvider", "GeminiProvider"]
```

**Checklist:**

- [ ] Tạo folder `providers/`
- [ ] Tạo file `__init__.py`

---

#### 1.2.2: Tạo `providers/base.py`

**File:** `llm-service/src/providers/base.py`

**Nội dung:**

- Abstract class `BaseLLMProvider`
- Method `generate(prompt, **kwargs) -> dict`
- Method `health_check() -> dict`
- Property `provider_name -> str`

**Response format chuẩn:**

```python
{
    "success": True,
    "text": "Generated response...",
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150,
    "finish_reason": "stop",
    "provider": "local" | "gemini"
}
```

**Checklist:**

- [ ] Tạo abstract class với ABC
- [ ] Define interface methods
- [ ] Define response format

---

#### 1.2.3: Tạo `providers/local_provider.py`

**File:** `llm-service/src/providers/local_provider.py`

**Nội dung:**

- Move code load Vistral từ `main.py` hiện tại
- Implement `BaseLLMProvider`
- Sử dụng `prompt_builder.build_prompt()` với format `[INST]...[/INST]`

**Logic:**

```python
class LocalProvider(BaseLLMProvider):
    def __init__(self):
        # Load Vistral model với llama-cpp-python

    async def generate(self, prompt: str, **kwargs) -> dict:
        # Gọi model.generate()
        # Return response theo format chuẩn

    async def health_check(self) -> dict:
        # Kiểm tra model đã load chưa
```

**Checklist:**

- [ ] Move code từ `main.py` lifespan
- [ ] Move code từ `generate_text()` endpoint
- [ ] Implement interface methods
- [ ] Test standalone

---

#### 1.2.4: Tạo `providers/gemini_provider.py`

**File:** `llm-service/src/providers/gemini_provider.py`

**Tham khảo:** `docs/thamkhao/llm-service/src/services/gemini_client.py`

**Nội dung:**

- Sử dụng `google-generativeai` SDK
- Retry logic với `tenacity` (3 attempts, exponential backoff)
- Implement `BaseLLMProvider`
- Sử dụng `prompt_builder.build_prompt_gemini()` (plain text)

**Logic:**

```python
class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(...))
    async def generate(self, prompt: str, **kwargs) -> dict:
        # Gọi Gemini API
        # Return response theo format chuẩn

    async def health_check(self) -> dict:
        # Test API với "Xin chào"
```

**Checklist:**

- [ ] Setup Gemini client
- [ ] Implement retry logic
- [ ] Implement generate với async
- [ ] Implement health_check
- [ ] Handle errors gracefully

---

### Bước 1.3: Cập nhật Prompt Builder

**File:** `llm-service/src/services/prompt_builder.py`

**Thêm method:**

```python
def build_prompt_for_provider(
    self,
    question: str,
    context: str,
    history: Optional[List[Dict]] = None,
    provider: str = "local"  # "local" | "gemini"
) -> str:
    if provider == "gemini":
        return self._build_prompt_gemini(question, context, history)
    else:
        return self.build_prompt(question, context, history)  # Existing method

def _build_prompt_gemini(self, question, context, history) -> str:
    # Plain text format (không cần [INST]...[/INST])
    # System prompt + context + history + question
```

**Checklist:**

- [ ] Thêm `build_prompt_for_provider()` method
- [ ] Thêm `_build_prompt_gemini()` private method
- [ ] Giữ nguyên `build_prompt()` cho backward compatibility

---

### Bước 1.4: Refactor Main

**File:** `llm-service/src/main.py`

**Thay đổi:**

1. Remove code load model trực tiếp
2. Add factory function `get_llm_provider()`
3. Cập nhật endpoints để gọi provider

**Factory pattern:**

```python
from src.providers import LocalProvider, GeminiProvider

llm_provider: Optional[BaseLLMProvider] = None

def get_llm_provider() -> BaseLLMProvider:
    global llm_provider
    if llm_provider is None:
        if settings.llm_provider == "gemini":
            llm_provider = GeminiProvider()
        else:
            llm_provider = LocalProvider()
    return llm_provider
```

**Endpoints giữ nguyên contract:**

```python
@app.post("/generate-rag")
async def generate_rag(request: RAGGenerateRequest):
    provider = get_llm_provider()
    prompt = prompt_builder.build_prompt_for_provider(
        question=request.question,
        context=request.context,
        history=request.history,
        provider=settings.llm_provider
    )
    result = await provider.generate(prompt)
    return GenerateResponse(**result)

@app.get("/health")
async def health_check():
    provider = get_llm_provider()
    health = await provider.health_check()
    return {
        "status": health["status"],
        "provider": settings.llm_provider,
        **health
    }
```

**Checklist:**

- [ ] Remove inline model loading
- [ ] Add factory function
- [ ] Update `/generate-rag` endpoint
- [ ] Update `/health` endpoint
- [ ] Update lifespan (startup/shutdown)

---

### Bước 1.5: Cập nhật Dependencies

**File:** `llm-service/requirements.txt`

**Thêm:**

```
# Gemini Provider (optional - only needed when LLM_PROVIDER=gemini)
google-generativeai>=0.3.0
tenacity>=8.2.0
```

**Checklist:**

- [ ] Thêm google-generativeai
- [ ] Thêm tenacity
- [ ] Test pip install

---

### Bước 1.6: Cập nhật ENV

**File:** `llm-service/.env`

**Thêm:**

```env
# Provider Selection
LLM_PROVIDER=local

# Gemini Settings (khi LLM_PROVIDER=gemini)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_OUTPUT_TOKENS=1024
```

**Checklist:**

- [ ] Thêm vào `.env`
- [ ] Cập nhật `.env.example`

---

## Testing Phase 1

### Test 1: Local Provider

```bash
# .env
LLM_PROVIDER=local

# Start service
cd llm-service
python -m src.main

# Test endpoint
curl -X POST http://localhost:8014/generate-rag \
  -H "Content-Type: application/json" \
  -d '{"question": "Test", "context": "Test context"}'
```

### Test 2: Gemini Provider

```bash
# .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key

# Start service
python -m src.main

# Test endpoint
curl -X POST http://localhost:8014/generate-rag \
  -H "Content-Type: application/json" \
  -d '{"question": "Test", "context": "Test context"}'
```

### Test 3: Health Check

```bash
curl http://localhost:8014/health
# Expected: {"status": "healthy", "provider": "gemini", ...}
```

---

## Phase 1 Checklist tổng hợp

- [ ] **1.1** Cập nhật `config.py`
- [ ] **1.2.1** Tạo `providers/__init__.py`
- [ ] **1.2.2** Tạo `providers/base.py`
- [ ] **1.2.3** Tạo `providers/local_provider.py`
- [ ] **1.2.4** Tạo `providers/gemini_provider.py`
- [ ] **1.3** Cập nhật `prompt_builder.py`
- [ ] **1.4** Refactor `main.py`
- [ ] **1.5** Cập nhật `requirements.txt`
- [ ] **1.6** Cập nhật `.env`
- [ ] **Test** Local Provider
- [ ] **Test** Gemini Provider
- [ ] **Test** Health Check

---

# PHASE 2: TTS Auto-read

## Mục tiêu

- Khi `ttsEnabled=true` → AI response tự động đọc
- User chỉ thấy UI tối giản (pause/stop)
- Mọi settings do Admin quản lý qua VoiceSettings

## Cấu trúc thư mục

```
frontend/src/
├── hooks/
│   └── useTTS.ts              # HOOK MỚI
└── components/
    ├── admin/VoiceSettings/
    │   └── VoiceSettings.tsx  # + auto-detect "An"
    └── chat/
        ├── ChatMessage/
        │   └── ChatMessage.tsx # + TTS controls
        └── ChatContainer.tsx   # + auto-trigger (hoặc MainChat)
```

## Các bước thực hiện

### Bước 2.1: Tạo useTTS Hook

**File:** `frontend/src/hooks/useTTS.ts`

**Interface:**

```typescript
interface UseTTSReturn {
  speak: (text: string) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  isSupported: boolean;
}

export function useTTS(): UseTTSReturn;
```

**Logic:**

1. Đọc settings từ `localStorage('voiceSettings')`
2. Lấy `ttsVoice`, `ttsSpeed`, `ttsVolume`
3. Wrap `window.speechSynthesis` API
4. Tìm voice theo tên (ưu tiên "An" nếu không chọn)

**Checklist:**

- [ ] Tạo file `useTTS.ts`
- [ ] Implement speak/pause/resume/stop
- [ ] Handle voice selection
- [ ] Handle settings từ localStorage
- [ ] Export hook

---

### Bước 2.2: Auto-detect Giọng "An"

**File:** `frontend/src/components/admin/VoiceSettings/VoiceSettings.tsx`

**Thay đổi:**

```typescript
// Trong useEffect load voices
const loadVoices = () => {
  const voices = speechSynthesis.getVoices();
  setAvailableVoices(voices);

  // Auto-select "Microsoft An Online" nếu chưa chọn
  if (!settings.ttsVoice && voices.length > 0) {
    const anVoice = voices.find(
      (v) => v.name.includes("An") && v.lang.startsWith("vi")
    );
    if (anVoice) {
      updateSetting("ttsVoice", anVoice.name);
    }
  }
};
```

**Checklist:**

- [ ] Cập nhật logic auto-select
- [ ] Ưu tiên tìm "Microsoft An Online"
- [ ] Fallback về giọng vi-VN đầu tiên

---

### Bước 2.3: UI Tối Giản trong ChatMessage

**File:** `frontend/src/components/chat/ChatMessage/ChatMessage.tsx`

**Thêm:**

```tsx
// Import hook
import { useTTS } from "@/hooks/useTTS";

// Trong component
const { isSpeaking, isPaused, pause, resume, stop } = useTTS();

// UI chỉ hiện khi đang đọc
{
  isSpeaking && (
    <div className={styles.ttsControls}>
      <span className={styles.ttsIcon}>🔊</span>
      {isPaused ? (
        <button onClick={resume} title="Tiếp tục">
          ▶️
        </button>
      ) : (
        <button onClick={pause} title="Tạm dừng">
          ⏸️
        </button>
      )}
      <button onClick={stop} title="Dừng">
        🛑
      </button>
    </div>
  );
}
```

**Checklist:**

- [ ] Import useTTS hook
- [ ] Thêm TTS controls UI
- [ ] Style cho controls
- [ ] Chỉ hiện khi đang đọc

---

### Bước 2.4: Auto-trigger TTS

**File:** Component cha (ChatContainer hoặc MainChat)

**Logic:**

```typescript
import { useTTS } from "@/hooks/useTTS";

// Trong component
const { speak } = useTTS();
const lastMessageRef = useRef<string | null>(null);

useEffect(() => {
  // Lấy settings
  const stored = localStorage.getItem("voiceSettings");
  const settings = stored ? JSON.parse(stored) : {};

  if (!settings.ttsEnabled) return;

  // Tìm message AI mới nhất
  const lastAIMessage = messages
    .filter((m) => m.role === "assistant")
    .slice(-1)[0];

  if (lastAIMessage && lastAIMessage.content !== lastMessageRef.current) {
    lastMessageRef.current = lastAIMessage.content;
    speak(lastAIMessage.content);
  }
}, [messages, speak]);
```

**Checklist:**

- [ ] Import useTTS hook
- [ ] Detect new AI message
- [ ] Check ttsEnabled setting
- [ ] Trigger speak()
- [ ] Prevent duplicate reads

---

### Bước 2.5: CSS Styles

**File:** `frontend/src/components/chat/ChatMessage/ChatMessage.module.css`

**Thêm:**

```css
.ttsControls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: var(--color-surface);
  border-radius: 4px;
  font-size: 0.875rem;
}

.ttsIcon {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.ttsControls button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1rem;
}

.ttsControls button:hover {
  opacity: 0.7;
}
```

**Checklist:**

- [ ] Thêm styles cho TTS controls
- [ ] Animation cho icon đang đọc
- [ ] Responsive design

---

## Testing Phase 2

### Test 1: VoiceSettings

1. Mở VoiceSettings từ Sidebar
2. Kiểm tra giọng "An" được auto-select
3. Bật `ttsEnabled`
4. Điều chỉnh speed/volume

### Test 2: Auto-read

1. Gửi câu hỏi trong chat
2. Kiểm tra AI response tự động đọc
3. Kiểm tra UI controls hiện lên

### Test 3: Controls

1. Click Pause → đọc tạm dừng
2. Click Resume → tiếp tục đọc
3. Click Stop → dừng hẳn

### Test 4: Settings thay đổi

1. Đổi voice trong VoiceSettings
2. Đổi speed/volume
3. Kiểm tra AI response mới áp dụng settings

---

## Phase 2 Checklist tổng hợp

- [ ] **2.1** Tạo `useTTS.ts` hook
- [ ] **2.2** Auto-detect giọng "An" trong VoiceSettings
- [ ] **2.3** Thêm TTS controls vào ChatMessage
- [ ] **2.4** Auto-trigger trong parent component
- [ ] **2.5** CSS styles
- [ ] **Test** VoiceSettings
- [ ] **Test** Auto-read
- [ ] **Test** Controls
- [ ] **Test** Settings thay đổi

---

# Tổng kết

## Thứ tự triển khai

1. **Phase 1** trước (LLM Provider) - Quan trọng hơn, ảnh hưởng backend
2. **Phase 2** sau (TTS) - Frontend only, độc lập

## Rollback Plan

### Phase 1

- Nếu Gemini có vấn đề: đổi `LLM_PROVIDER=local` trong ENV
- Không cần restart query-service

### Phase 2

- Nếu TTS có vấn đề: tắt `ttsEnabled` trong VoiceSettings
- Không ảnh hưởng chức năng chat

## Timeline ước tính

| Phase                | Thời gian    |
| -------------------- | ------------ |
| Phase 1.1-1.2        | 2-3 giờ      |
| Phase 1.3-1.4        | 2-3 giờ      |
| Phase 1.5-1.6 + Test | 1-2 giờ      |
| Phase 2.1-2.2        | 1-2 giờ      |
| Phase 2.3-2.5 + Test | 1-2 giờ      |
| **Tổng**             | **7-12 giờ** |
