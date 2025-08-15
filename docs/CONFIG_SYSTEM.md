# LegalRAG Configuration System

## 📋 Tổng quan

Hệ thống cấu hình đã được **tách biệt hoàn toàn khỏi logic code**, sử dụng pattern Node.js với file `.env` để quản lý tất cả settings.

## 🎯 Cấu hình cuối cùng được xác nhận

### Models & Performance

- **Embedding Model**: `AITeamVN/Vietnamese_Embedding_v2` (1024 dimensions)
- **Reranker Model**: `AITeamVN/Vietnamese_Reranker` (CrossEncoder)
- **LLM Model**: `PhoGPT-4B-Chat-q4_k_m.gguf` (4-bit quantized)
- **Context Length**: `8192` tokens (~6000 Vietnamese words)
- **CPU Threads**: `6` threads (optimized for Intel 12700H - 6P cores)
- **Temperature**: `0.1` (maximum accuracy, minimal creativity for legal text)

### RAG Process Configuration

- **Broad Search K**: `30` documents (initial retrieval)
- **Similarity Threshold**: `0.3` (permissive for recall)
- **Context Expansion**: `1` adjacent chunk
- **Reranking**: `Enabled` (Vietnamese-specific reranking)
- **Query Routing**: `Enabled` (intelligent collection selection)

### All Models Local

- ✅ Models cached in `data/models/hf_cache/`
- ✅ Offline mode enabled (`HF_HUB_OFFLINE=1`)
- ✅ No internet downloads during runtime
- ✅ Local model detection working

## 🔧 Usage Examples

### Before (Hard-coded)

```python
# ❌ Hard-coded values scattered throughout code
vectordb.search_in_collection("collection", "query", top_k=5, similarity_threshold=0.3)
llm.generate_response(query, context, temperature=0.7, max_tokens=2048)
router.route_query(query, top_k=2)
```

### After (Config-based)

```python
# ✅ Clean code using config defaults
vectordb.search_in_collection("collection", "query")  # Uses config defaults
llm.generate_response(query, context)  # Uses config defaults
router.route_query(query)  # Uses config defaults

# ✅ Override when needed
vectordb.search_in_collection("collection", "query", top_k=10)  # Override specific param
```

## 📁 Configuration Management

### Single Source of Truth

```bash
# File: .env
TEMPERATURE=0.1                    # Used in: LLMService.generate_response()
DEFAULT_SEARCH_TOP_K=5             # Used in: VectorDBService.search_in_collection()
QUERY_ROUTER_TOP_K=2               # Used in: QueryRouter.route_query()
EMBEDDING_MODEL_NAME=AITeamVN/Vietnamese_Embedding_v2  # Used in: VectorDBService
```

### Verified Usage

- ✅ All 30+ config values have explicit usage comments
- ✅ All services tested and confirmed using config values
- ✅ No orphaned/unused config values
- ✅ No hardcoded magic numbers remaining in code

## 🎯 Benefits Achieved

### 1. Easy Maintenance (như Node.js)

```bash
# Change behavior by editing .env only
TEMPERATURE=0.2        # More creative responses
DEFAULT_SEARCH_TOP_K=10  # More search results
N_THREADS=8            # Use more CPU cores
```

### 2. Environment-based Configuration

```bash
# Development
DEBUG=true
TEMPERATURE=0.1

# Production
DEBUG=false
TEMPERATURE=0.05
```

### 3. No Code Changes Required

- Tune performance: Edit `.env` → Restart
- Change models: Edit `.env` → Restart
- Adjust search parameters: Edit `.env` → Restart

## 🔍 Verification Status

### ✅ All Tests Passed

- **Config Loading**: All 30+ values loaded correctly
- **Service Integration**: All services use config defaults
- **Path Resolution**: All file paths computed correctly
- **Model Loading**: All models load from local cache
- **Logic Separation**: Zero hardcoded values in business logic

### ✅ Architecture Benefits

- 🎯 Single source of truth (`.env` file)
- 🔧 Easy maintenance and tuning
- 📦 Environment-based deployment
- 🚀 No code changes for config adjustments
- 💡 Developer-friendly like Node.js projects

## 📝 Next Steps

**System is production-ready!**

To adjust any behavior:

1. Edit `.env` file
2. Restart application
3. Changes take effect immediately

**No more digging through code files to change settings!** 🎉
