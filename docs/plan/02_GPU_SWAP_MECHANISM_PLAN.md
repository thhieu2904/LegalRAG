# 📋 KẾ HOẠCH: GPU Memory Swap Mechanism

> **Status**: 🔄 **IN ANALYSIS - READY FOR IMPLEMENTATION**
>
> **Mục tiêu**: Tạo cơ chế swap GPU memory giữa LLM và Rerank khi VRAM giới hạn (6GB), với khả năng tắt swap trên server có đủ VRAM (12GB+).

---

## 📊 PHÂN TÍCH TỪ rag_service_old (Completed)

### Findings từ Source Code Analysis

**1. Config Pattern** (`rag_service_old/app/core/config.py`):

```python
class Settings(BaseSettings):
    enable_vram_swapping: bool = False  # Control flag
    n_gpu_layers: int = -1  # Full GPU offload for LLM
```

**2. RerankerService Pattern** (`rag_service_old/app/services/reranker.py`):

```python
class RerankerService:
    def __init__(self):
        if not settings.enable_vram_swapping:
            self._load_model()  # Load immediately
        else:
            logger.info("Swapping mode: Load on-demand")

    def ensure_loaded(self):
        """Called before reranking"""
        if not self.model_loaded:
            self._load_model()

    def unload_model(self):
        """Called after reranking to free VRAM"""
        del self.model
        gc.collect()
        torch.cuda.empty_cache()
```

**3. LLMService Pattern** (`rag_service_old/app/services/language_model.py`):

```python
class LLMService:
    def __init__(self):
        if not settings.enable_vram_swapping:
            self._load_model()
        else:
            logger.info("Swapping mode: Load on-demand")

    def ensure_loaded(self):
        if not self.model_loaded:
            self._load_model()

    def unload_model(self):
        del self.model
        gc.collect()
        torch.cuda.empty_cache()
```

**4. RAG Engine Orchestration** (`rag_service_old/app/services/rag_engine.py`):

```python
# Phase 1: Reranking
if hasattr(self.llm_service, 'unload_model'):
    self.llm_service.unload_model()  # Free VRAM for reranker

# ... rerank logic ...

if hasattr(self.reranker_service, 'unload_model'):
    self.reranker_service.unload_model()  # Free VRAM for LLM

# Phase 2: LLM Generation
# LLM loads automatically via ensure_loaded()
```

**5. VectorDB/Embedding** (`rag_service_old/app/services/vector.py`):

```python
def get_optimal_device(self):
    if settings.enable_vram_swapping:
        return 'cpu'  # CPU để save VRAM cho LLM+Rerank
    else:
        return 'cuda' if torch.cuda.is_available() else 'cpu'
```

---

## 🔍 PHÂN TÍCH CHI TIẾT VẤN ĐỀ KỸ THUẬT

### Vấn đề cốt lõi

Hiện tại hệ thống chạy 3 AI models trên GPU:

| Model                           | Size        | Priority              | Reason               |
| ------------------------------- | ----------- | --------------------- | -------------------- |
| **LLM** (Vistral-7B Q4)         | ~4.5GB VRAM | ⭐ **GPU** (bắt buộc) | CPU quá chậm         |
| **Rerank** (bge-reranker-v2-m3) | ~1.5GB VRAM | ⭐ **GPU** (ưu tiên)  | CPU chậm 2-3x        |
| **Embedding** (bge-m3)          | ~1.5GB VRAM | ✅ **CPU** (OK)       | Chỉ embed query ngắn |

**Dev Laptop VRAM: 6GB** → Cần swap Rerank và LLM, Embedding chạy CPU.

### Hiện trạng Docker Compose

```yaml
# Embedding: GPU enabled
embedding-service:
  environment:
    DEVICE: cuda # ← Đang dùng GPU

# Rerank: CPU only (để tránh OOM)
rerank-service:
  environment:
    DEVICE: cpu # ← Buộc phải dùng CPU vì thiếu VRAM

# LLM: GPU enabled (bắt buộc cho performance)
llm-service:
  environment:
    N_GPU_LAYERS: -1 # ← All layers on GPU
```

**Vấn đề hiện tại**: Rerank phải chạy CPU → **chậm đáng kể** (2-3x slower).

---

## 1. PHÂN TÍCH HIỆN TRẠNG

### 1.1 Kiến trúc hiện tại (Microservices)

```
┌─────────────────────────────────────────────────────────────────┐
│                   SEPARATE SERVICES (Current)                    │
├─────────────────────────────────────────────────────────────────┤
│  embedding-service (port 8011)                                   │
│  ├── Model: bge-m3 (768 dims)                                   │
│  ├── Framework: SentenceTransformer                             │
│  └── Device: CUDA (default)                                     │
│                                                                 │
│  rerank-service (port 8013)                                     │
│  ├── Model: BAAI/bge-reranker-v2-m3                             │
│  ├── Framework: CrossEncoder (sentence-transformers)            │
│  └── Device: CPU (current) / CUDA (desired)                     │
│                                                                 │
│  llm-service (port 8006)                                        │
│  ├── Model: Vistral-7B-Q4 (GGUF)                                │
│  ├── Framework: llama-cpp-python                                │
│  └── Device: CUDA (n_gpu_layers=-1)                             │
└─────────────────────────────────────────────────────────────────┘
```

**Vấn đề:**

- 3 services riêng biệt → không thể share GPU context
- Mỗi service load model vào VRAM riêng
- Không có cơ chế swap giữa các services

### 1.2 Kiến trúc cũ (rag_service_old) - Monolith

```python
# rag_service_old/app/core/config.py
class Settings(BaseSettings):
    enable_vram_swapping: bool = False  # ✅ Đã có flag này

# rag_service_old/app/services/reranker.py
class RerankerService:
    def __init__(self):
        if not settings.enable_vram_swapping:
            # Non-swapping mode: Load immediately
            self._load_model()
        else:
            # Swapping mode: Load on-demand
            logger.info("🔄 Swapping mode: Reranker model will load on-demand")

    def ensure_loaded(self):
        if not self.model_loaded:
            self._load_model()

    def unload_model(self):
        del self.model
        torch.cuda.empty_cache()
        gc.collect()

# rag_service_old/app/services/language_model.py
class LLMService:
    # Same pattern: enable_vram_swapping controls load behavior
```

**Ưu điểm của monolith:**

- ✅ Share memory context
- ✅ Có thể swap models trong cùng process
- ✅ Đã implement sẵn `unload_model()`, `ensure_loaded()`

---

## 2. CHIẾN LƯỢC: HYBRID APPROACH

### 2.1 Quyết định kiến trúc

**Giữ microservices nhưng thêm swap coordination.**

Lý do:

- Không cần merge tất cả services thành 1 (effort lớn)
- Có thể điều phối swap thông qua query-service (orchestrator)
- Mỗi service tự quản lý model loading/unloading
- Swap logic nằm ở query-service (central point)

### 2.2 Kiến trúc mới

```
┌─────────────────────────────────────────────────────────────────┐
│                    GPU SWAP ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ENV: GPU_SWAP_MODE=true (8GB VRAM - Laptop/Dev)               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  embedding-service (ALWAYS CPU in swap mode)              │  │
│  │  └── Device: CPU (to save VRAM for LLM+Rerank)           │  │
│  │                                                           │  │
│  │  query-service (Orchestrator with Swap Logic)             │  │
│  │  ├── Before rerank: POST /rerank/prepare (load model)    │  │
│  │  ├── After rerank:  POST /rerank/release (unload model)  │  │
│  │  ├── Before LLM:    POST /llm/prepare (load model)       │  │
│  │  └── After LLM:     POST /llm/release (unload model)     │  │
│  │                                                           │  │
│  │  rerank-service                                           │  │
│  │  ├── POST /prepare  → Load model to GPU                  │  │
│  │  ├── POST /rerank   → Must be loaded first               │  │
│  │  └── POST /release  → Unload model, free VRAM            │  │
│  │                                                           │  │
│  │  llm-service                                              │  │
│  │  ├── POST /prepare  → Load model to GPU                  │  │
│  │  ├── POST /generate → Must be loaded first               │  │
│  │  └── POST /release  → Unload model, free VRAM            │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ENV: GPU_SWAP_MODE=false (16GB+ VRAM - Server/Production)     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ALL SERVICES: Load at startup, never unload              │  │
│  │  ├── embedding-service: GPU                               │  │
│  │  ├── rerank-service: GPU                                  │  │
│  │  └── llm-service: GPU                                     │  │
│  │                                                           │  │
│  │  query-service: No swap coordination needed               │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. MEMORY ESTIMATION

### 3.1 Model Sizes

| Service           | Model              | GPU Memory | Notes             |
| ----------------- | ------------------ | ---------- | ----------------- |
| embedding-service | bge-m3 (768d)      | ~1.5 GB    | Có thể chạy CPU   |
| rerank-service    | bge-reranker-v2-m3 | ~1.5 GB    | Cần GPU cho speed |
| llm-service       | Vistral-7B Q4      | ~4.5 GB    | Bắt buộc GPU      |

### 3.2 Swap Mode Memory Flow (6GB VRAM Laptop)

```
Query Flow (GPU_SWAP_MODE=true):

1. User sends question
   GPU: Empty (0 GB used)

2. Embed question (embedding on CPU - bge-m3)
   GPU: Empty (0 GB used) ← Embedding chạy CPU

3. Vector search (no GPU needed)
   GPU: Empty (0 GB used)

4. Load Rerank → GPU (bge-reranker-v2-m3)
   GPU: Rerank (1.5 GB)

5. Rerank documents
   GPU: Rerank (1.5 GB peak during inference)

6. Unload Rerank → Free VRAM
   GPU: Empty (0 GB)

7. Load LLM → GPU (Vistral-7B Q4)
   GPU: LLM (4.5 GB)

8. Generate answer
   GPU: LLM (4.5 GB peak during generation)

9. Keep LLM loaded for next query (optional)
   GPU: LLM (4.5 GB) or Empty

Peak VRAM: ~4.5 GB (fits in 6GB with headroom)
```

### 3.3 No-Swap Mode Memory (12GB+ Server)

```
Startup (All models loaded permanently):
- Embedding: 1.5 GB (GPU)
- Rerank: 1.5 GB (GPU)
- LLM: 4.5 GB (GPU)
- Total: ~7.5 GB

Required VRAM: 12GB+ recommended (8GB marginal)
```

---

## 📐 VRAM BUDGET ANALYSIS

### 6GB VRAM Laptop (GPU_SWAP_MODE=true)

| Phase     | Model on GPU | VRAM Used | Headroom  |
| --------- | ------------ | --------- | --------- |
| Idle      | None         | 0 GB      | 6 GB      |
| Reranking | Rerank only  | 1.5 GB    | 4.5 GB ✅ |
| LLM Gen   | LLM only     | 4.5 GB    | 1.5 GB ✅ |
| Peak      | LLM (max)    | ~5 GB     | 1 GB ✅   |

✅ **Fits 6GB VRAM** - Rerank và LLM never loaded simultaneously.

### 12GB+ Server (GPU_SWAP_MODE=false)

| Phase   | Models on GPU | VRAM Used | Headroom  |
| ------- | ------------- | --------- | --------- |
| Startup | All 3 models  | 7.5 GB    | 4.5 GB ✅ |
| Query   | All 3 models  | ~8 GB     | 4 GB ✅   |

✅ **Fits 12GB+ VRAM** - No swapping needed.

---

## 4. IMPLEMENTATION PLAN

### 4.1 ENV Configuration

```bash
# .env (shared across services)

# =============================================================================
# GPU SWAP MODE CONFIGURATION
# =============================================================================
# true  = Swap mode (8GB VRAM): Load/unload models on demand
# false = No-swap mode (16GB+ VRAM): All models loaded permanently
GPU_SWAP_MODE=true

# =============================================================================
# DEVICE CONFIGURATION (per service)
# =============================================================================
# Embedding device (can be CPU in swap mode to save VRAM)
EMBEDDING_DEVICE=cpu  # cpu | cuda

# Rerank device (GPU for speed, swapped in swap mode)
RERANK_DEVICE=cuda    # cpu | cuda

# LLM device (always GPU for reasonable speed)
LLM_DEVICE=cuda       # cpu | cuda (cpu is very slow)
LLM_GPU_LAYERS=-1     # -1 = all layers on GPU
```

### 4.2 Rerank Service Changes

**File: `rerank-service/src/main.py`**

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
import torch
import gc
from sentence_transformers import CrossEncoder

# Settings
GPU_SWAP_MODE = os.getenv("GPU_SWAP_MODE", "false").lower() == "true"
DEVICE = os.getenv("RERANK_DEVICE", "cuda")

# Global model state
model: Optional[CrossEncoder] = None
model_loaded: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle"""
    global model, model_loaded

    if not GPU_SWAP_MODE:
        # Non-swap mode: Load immediately at startup
        logger.info("🚀 Non-swap mode: Loading Rerank model at startup")
        load_model()
    else:
        logger.info("🔄 Swap mode: Rerank model will load on-demand")

    yield

    # Cleanup on shutdown
    unload_model()


app = FastAPI(lifespan=lifespan)


def load_model():
    """Load reranker model to GPU"""
    global model, model_loaded

    if model_loaded:
        logger.info("Model already loaded")
        return

    logger.info(f"Loading reranker model to {DEVICE}...")
    start = time.time()

    model = CrossEncoder(
        "BAAI/bge-reranker-v2-m3",
        device=DEVICE,
        max_length=2304
    )

    model_loaded = True
    logger.info(f"✅ Reranker loaded in {time.time()-start:.2f}s")


def unload_model():
    """Unload model to free GPU memory"""
    global model, model_loaded

    if model is None:
        return

    logger.info("🔄 Unloading reranker model...")

    # Move to CPU first (optional, helps with memory release)
    if hasattr(model, 'model') and DEVICE == 'cuda':
        model.model.cpu()

    del model
    model = None
    model_loaded = False

    # Force cleanup
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    logger.info("✅ Reranker unloaded, VRAM freed")


@app.post("/prepare")
async def prepare_model():
    """
    Load model to GPU (for swap mode).
    Called by query-service before reranking.
    """
    if not GPU_SWAP_MODE:
        return {"status": "ok", "message": "Non-swap mode, model always loaded"}

    load_model()
    return {"status": "ok", "loaded": True}


@app.post("/release")
async def release_model():
    """
    Unload model from GPU (for swap mode).
    Called by query-service after reranking.
    """
    if not GPU_SWAP_MODE:
        return {"status": "ok", "message": "Non-swap mode, model stays loaded"}

    unload_model()
    return {"status": "ok", "unloaded": True}


@app.post("/rerank")
async def rerank(request: RerankRequest):
    """Rerank documents"""
    global model

    # Ensure model is loaded
    if not model_loaded:
        if GPU_SWAP_MODE:
            load_model()  # Auto-load in swap mode
        else:
            raise HTTPException(503, "Model not loaded")

    # ... existing rerank logic ...
```

### 4.3 LLM Service Changes

**File: `llm-service/src/main.py`**

```python
from llama_cpp import Llama
import gc
import torch

# Settings
GPU_SWAP_MODE = os.getenv("GPU_SWAP_MODE", "false").lower() == "true"
DEVICE = os.getenv("LLM_DEVICE", "cuda")
GPU_LAYERS = int(os.getenv("LLM_GPU_LAYERS", "-1"))

# Global model state
llm: Optional[Llama] = None
model_loaded: bool = False


def load_model():
    """Load LLM to GPU"""
    global llm, model_loaded

    if model_loaded:
        return

    logger.info(f"Loading LLM to {DEVICE}...")
    start = time.time()

    n_gpu_layers = GPU_LAYERS if DEVICE == "cuda" else 0

    llm = Llama(
        model_path=settings.MODEL_PATH,
        n_ctx=settings.N_CTX,
        n_gpu_layers=n_gpu_layers,
        n_threads=settings.N_THREADS,
        n_batch=settings.N_BATCH,
        use_mmap=True,
        verbose=False
    )

    model_loaded = True
    logger.info(f"✅ LLM loaded in {time.time()-start:.2f}s")


def unload_model():
    """Unload LLM to free GPU memory"""
    global llm, model_loaded

    if llm is None:
        return

    logger.info("🔄 Unloading LLM...")

    # llama-cpp-python: need to delete and recreate
    del llm
    llm = None
    model_loaded = False

    # Force cleanup
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    logger.info("✅ LLM unloaded, VRAM freed")


@app.post("/prepare")
async def prepare_model():
    """Load model for swap mode"""
    if not GPU_SWAP_MODE:
        return {"status": "ok", "message": "Non-swap mode"}

    load_model()
    return {"status": "ok", "loaded": True}


@app.post("/release")
async def release_model():
    """Unload model for swap mode"""
    if not GPU_SWAP_MODE:
        return {"status": "ok", "message": "Non-swap mode"}

    unload_model()
    return {"status": "ok", "unloaded": True}
```

### 4.4 Query Service Orchestration

**File: `query-service/src/main.py`**

```python
# Settings
GPU_SWAP_MODE = os.getenv("GPU_SWAP_MODE", "false").lower() == "true"


async def prepare_rerank():
    """Prepare rerank service (load model if swap mode)"""
    if not GPU_SWAP_MODE:
        return

    try:
        response = await http_client.post(
            f"{settings.RERANK_SERVICE_URL}/prepare",
            timeout=60.0  # Model loading can take time
        )
        if response.status_code != 200:
            logger.warning(f"Rerank prepare failed: {response.text}")
    except Exception as e:
        logger.error(f"Rerank prepare error: {e}")


async def release_rerank():
    """Release rerank service (unload model if swap mode)"""
    if not GPU_SWAP_MODE:
        return

    try:
        await http_client.post(
            f"{settings.RERANK_SERVICE_URL}/release",
            timeout=30.0
        )
    except Exception as e:
        logger.warning(f"Rerank release error: {e}")


async def prepare_llm():
    """Prepare LLM service (load model if swap mode)"""
    if not GPU_SWAP_MODE:
        return

    try:
        response = await http_client.post(
            f"{settings.LLM_SERVICE_URL}/prepare",
            timeout=120.0  # LLM loading takes longer
        )
        if response.status_code != 200:
            logger.warning(f"LLM prepare failed: {response.text}")
    except Exception as e:
        logger.error(f"LLM prepare error: {e}")


async def release_llm():
    """Release LLM service (unload model if swap mode)"""
    if not GPU_SWAP_MODE:
        return

    try:
        await http_client.post(
            f"{settings.LLM_SERVICE_URL}/release",
            timeout=30.0
        )
    except Exception as e:
        logger.warning(f"LLM release error: {e}")


@app.post("/query")
async def query(request: QueryRequest):
    """Query with swap coordination"""

    # ... embedding step (CPU, no swap needed) ...

    # ... vector search (no GPU needed) ...

    # Step 3: Rerank with swap coordination
    if GPU_SWAP_MODE:
        logger.info("🔄 Preparing rerank (swap mode)...")
        await prepare_rerank()

    reranked_results, document_scores = await rerank_documents(...)

    if GPU_SWAP_MODE:
        logger.info("🔄 Releasing rerank, preparing LLM...")
        await release_rerank()

    # Step 4: Generate answer with swap coordination
    if GPU_SWAP_MODE:
        await prepare_llm()

    answer = await generate_answer(...)

    # Note: We can keep LLM loaded for next query (common case)
    # Only release if we want to free memory for rerank

    # ... rest of response handling ...
```

### 4.5 Embedding Service Changes

**File: `embedding-service/src/main.py`**

```python
# Settings
GPU_SWAP_MODE = os.getenv("GPU_SWAP_MODE", "false").lower() == "true"
DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")

def get_device():
    """Get device based on mode"""
    if GPU_SWAP_MODE:
        # Swap mode: Always use CPU to save VRAM for LLM+Rerank
        logger.info("🔄 Swap mode: Embedding on CPU")
        return "cpu"

    # Non-swap mode: Use configured device
    if DEVICE == "cuda" and torch.cuda.is_available():
        return "cuda"
    return "cpu"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model

    device = get_device()
    logger.info(f"Loading embedding model to {device}...")

    model = SentenceTransformer(
        settings.MODEL_NAME,
        device=device
    )

    logger.info(f"✅ Embedding model loaded on {device}")
    yield

    # Cleanup
    del model
```

---

## 5. DOCKER COMPOSE CONFIGURATION

### 5.1 docker-compose.yml (Swap Mode - Development)

```yaml
version: "3.8"

services:
  embedding-service:
    build: ./embedding-service
    environment:
      - GPU_SWAP_MODE=true
      - EMBEDDING_DEVICE=cpu # CPU in swap mode
    # No GPU reservation needed
    ports:
      - "8011:8011"

  rerank-service:
    build: ./rerank-service
    environment:
      - GPU_SWAP_MODE=true
      - RERANK_DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "8013:8013"

  llm-service:
    build: ./llm-service
    environment:
      - GPU_SWAP_MODE=true
      - LLM_DEVICE=cuda
      - LLM_GPU_LAYERS=-1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "8006:8006"

  query-service:
    build: ./query-service
    environment:
      - GPU_SWAP_MODE=true
    ports:
      - "8005:8005"
```

### 5.2 docker-compose.prod.yml (No-Swap Mode - Production)

```yaml
version: "3.8"

services:
  embedding-service:
    build: ./embedding-service
    environment:
      - GPU_SWAP_MODE=false
      - EMBEDDING_DEVICE=cuda # GPU in production
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  rerank-service:
    build: ./rerank-service
    environment:
      - GPU_SWAP_MODE=false
      - RERANK_DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  llm-service:
    build: ./llm-service
    environment:
      - GPU_SWAP_MODE=false
      - LLM_DEVICE=cuda
      - LLM_GPU_LAYERS=-1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  query-service:
    build: ./query-service
    environment:
      - GPU_SWAP_MODE=false
```

---

## 6. PERFORMANCE CONSIDERATIONS

### 6.1 Latency Impact (Swap Mode)

| Operation         | Time (estimate) | Notes                          |
| ----------------- | --------------- | ------------------------------ |
| Load Rerank → GPU | 2-5 seconds     | First time slower (cache cold) |
| Unload Rerank     | <1 second       | `torch.cuda.empty_cache()`     |
| Load LLM → GPU    | 5-10 seconds    | GGUF is fast to load           |
| Unload LLM        | <1 second       |                                |

**Total overhead per query: ~8-16 seconds** (in swap mode)

### 6.2 Optimization Strategies

```python
# Strategy 1: Keep LLM loaded (most common operation)
# Only release LLM when switching to rerank

# Strategy 2: Lazy release
# Keep last used model loaded, only release when other model needed

# Strategy 3: Predictive loading
# If query text is long, likely needs LLM → start loading while reranking

class SwapOptimizer:
    def __init__(self):
        self.current_loaded: Optional[str] = None  # "rerank" | "llm" | None

    async def ensure_rerank_ready(self):
        if self.current_loaded == "rerank":
            return  # Already loaded

        if self.current_loaded == "llm":
            await release_llm()

        await prepare_rerank()
        self.current_loaded = "rerank"

    async def ensure_llm_ready(self):
        if self.current_loaded == "llm":
            return  # Already loaded

        if self.current_loaded == "rerank":
            await release_rerank()

        await prepare_llm()
        self.current_loaded = "llm"
```

### 6.3 Monitoring

```python
# Add metrics for swap operations
swap_metrics = {
    "rerank_load_count": 0,
    "rerank_load_time_total": 0.0,
    "llm_load_count": 0,
    "llm_load_time_total": 0.0,
    "swap_overhead_per_query": 0.0
}

@app.get("/metrics")
async def get_swap_metrics():
    return swap_metrics
```

---

## 7. IMPLEMENTATION TIMELINE

### Phase 1: Prepare Services (2 ngày)

| Task                                     | Service           | Priority |
| ---------------------------------------- | ----------------- | -------- |
| 1. Add GPU_SWAP_MODE env reading         | All services      | ⭐ HIGH  |
| 2. Implement `/prepare` endpoint         | rerank-service    | ⭐ HIGH  |
| 3. Implement `/release` endpoint         | rerank-service    | ⭐ HIGH  |
| 4. Implement `load_model()`              | rerank-service    | ⭐ HIGH  |
| 5. Implement `unload_model()`            | rerank-service    | ⭐ HIGH  |
| 6. Repeat for llm-service                | llm-service       | ⭐ HIGH  |
| 7. Update embedding-service device logic | embedding-service | HIGH     |

### Phase 2: Query Service Orchestration (1 ngày)

| Task                                  | File                  | Priority |
| ------------------------------------- | --------------------- | -------- |
| 1. Add swap helper functions          | query-service/main.py | ⭐ HIGH  |
| 2. Update `/query` endpoint with swap | query-service/main.py | ⭐ HIGH  |
| 3. Update `/query/confirm` with swap  | query-service/main.py | HIGH     |
| 4. Add SwapOptimizer (optional)       | query-service/main.py | MEDIUM   |

### Phase 3: Docker & Testing (1 ngày)

| Task                                        | Priority |
| ------------------------------------------- | -------- |
| 1. Update docker-compose.yml (swap mode)    | ⭐ HIGH  |
| 2. Create docker-compose.prod.yml (no-swap) | HIGH     |
| 3. Test swap mode on 8GB GPU                | ⭐ HIGH  |
| 4. Test no-swap mode on 16GB+ GPU           | HIGH     |
| 5. Measure latency overhead                 | MEDIUM   |

---

## 8. TESTING PLAN

### 8.1 Unit Tests

```python
# test_swap.py

async def test_rerank_prepare_release():
    """Test rerank model prepare/release cycle"""
    # Prepare
    response = await client.post("/prepare")
    assert response.status_code == 200

    # Verify loaded
    status = await client.get("/health")
    assert status.json()["model_loaded"] == True

    # Release
    response = await client.post("/release")
    assert response.status_code == 200

    # Verify unloaded
    status = await client.get("/health")
    assert status.json()["model_loaded"] == False


async def test_swap_sequence():
    """Test full swap sequence: rerank → llm"""
    # Load rerank
    await rerank_client.post("/prepare")

    # Check GPU memory
    vram_used_after_rerank = get_gpu_memory()
    assert vram_used_after_rerank > 0

    # Release rerank, load llm
    await rerank_client.post("/release")
    await llm_client.post("/prepare")

    # Check GPU memory
    vram_used_after_llm = get_gpu_memory()
    assert vram_used_after_llm > vram_used_after_rerank  # LLM larger
```

### 8.2 Integration Tests

```python
async def test_query_with_swap():
    """Test full query flow with swap mode"""
    response = await client.post("/query", json={
        "question": "Thủ tục đăng ký khai sinh?",
        "session_id": "test-123"
    })

    assert response.status_code == 200
    assert response.json()["answer"] is not None
```

### 8.3 Performance Tests

```python
async def test_swap_latency():
    """Measure swap overhead"""
    start = time.time()

    # Full query with swap
    await client.post("/query", json={...})

    total_time = time.time() - start

    # Log for analysis
    print(f"Total query time with swap: {total_time:.2f}s")

    # Overhead should be acceptable
    assert total_time < 30  # Max 30s with swap
```

---

## 9. ROLLBACK PLAN

### 9.1 Disable Swap Mode

```bash
# Simply set env to false
GPU_SWAP_MODE=false

# Services will load models at startup and never unload
```

### 9.2 Remove Swap Code

```python
# If swap doesn't work, just remove prepare/release calls from query-service
# Services work independently without coordination
```

---

## 10. SUMMARY

| Aspect           | Swap Mode (6GB VRAM) | No-Swap Mode (12GB+)   |
| ---------------- | -------------------- | ---------------------- |
| Embedding        | **CPU** (always)     | GPU                    |
| Rerank           | GPU (on-demand swap) | GPU (permanent)        |
| LLM              | GPU (on-demand swap) | GPU (permanent)        |
| Peak VRAM        | ~4.5 GB              | ~7.5 GB                |
| Latency overhead | +8-16s per query     | 0s                     |
| Best for         | Dev Laptop, 6GB VRAM | Production, 12GB+ VRAM |

**Kết quả mong đợi:**

- ✅ Chạy được trên **6GB VRAM** với swap mode
- ✅ Embedding chạy CPU (chỉ embed query ngắn, không cần GPU)
- ✅ Rerank và LLM swap trên GPU (không bao giờ load đồng thời)
- ✅ Không thay đổi behavior trên server có đủ VRAM
- ✅ Dễ dàng switch qua ENV variable
- ✅ Maintain microservices architecture (không merge thành monolith)

---

## 🔧 NEXT STEPS: IMPLEMENTATION

**Phase 1 - Rerank Service** (Estimated: 2-3 hours):

1. [ ] Add `GPU_SWAP_MODE` env reading
2. [ ] Implement `/prepare` endpoint (load model)
3. [ ] Implement `/release` endpoint (unload model)
4. [ ] Update `load_model()` with swap logic
5. [ ] Implement `unload_model()` with proper VRAM cleanup

**Phase 2 - LLM Service** (Estimated: 2-3 hours):

1. [ ] Same pattern as Rerank Service
2. [ ] Handle llama-cpp-python model lifecycle

**Phase 3 - Embedding Service** (Estimated: 1 hour):

1. [ ] Force CPU when `GPU_SWAP_MODE=true`

**Phase 4 - Query Service Orchestration** (Estimated: 2-3 hours):

1. [ ] Add swap helper functions
2. [ ] Update `/query` endpoint with swap coordination
3. [ ] Implement SwapOptimizer (lazy release strategy)

**Phase 5 - Testing** (Estimated: 2-3 hours):

1. [ ] Test on 6GB VRAM laptop
2. [ ] Measure swap overhead latency
3. [ ] Verify no-swap mode on higher VRAM
