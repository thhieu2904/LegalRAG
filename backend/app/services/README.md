# LegalRAG Services Architecture

## Clean, Simple, and Functional Service Layer

### 🎯 **Runtime Services (7 Essential Services)**

---

## 💾 **1. Vector Database**

**File:** `vector_database.py`  
**Class:** `VectorDBService`

**Purpose:** Manage ChromaDB vector storage and retrieval

- Multi-collection support (3 collections: chung_thuc, ho_tich_cap_xa, nuoi_con_nuoi)
- Vietnamese embedding with CPU optimization
- Semantic search with metadata filtering
- Document chunking and context expansion support
- **262 total chunks** from **53 JSON documents** (~4.9 chunks per document)

---

## 🧠 **2. Language Model**

**File:** `language_model.py`
**Class:** `LLMService`

**Purpose:** Handle LLM inference and generation

- PhoGPT-4B-Chat Vietnamese LLM
- GPU-optimized model loading
- Context-aware response generation
- Session management support

---

## 🎯 **3. Smart Query Router**

**File:** `smart_router.py`
**Classes:** `EnhancedSmartQueryRouter`, `RouterBasedAmbiguousQueryService`

**Purpose:** Intelligent query routing and classification

- Load router examples from `data/router_examples_smart/`
- Embeddings-based similarity matching (212 pre-computed questions)
- Multi-collection routing with confidence scoring
- Ambiguous query detection and handling
- Fast startup with embeddings cache

---

## 📊 **4. Result Reranker**

**File:** `result_reranker.py`
**Class:** `RerankerService`

**Purpose:** Rerank search results for relevance

- Vietnamese reranker model (AITeamVN/Vietnamese_Reranker)
- GPU-optimized inference
- Cross-encoder scoring for query-document pairs
- Improve search result quality

---

## 🔍 **5. Context Expander**

**File:** `context_expander.py`
**Class:** `EnhancedContextExpansionService`

**Purpose:** Expand search context for better answers

- Nucleus strategy for context expansion
- Document-level metadata analysis
- Related chunk discovery via document_id
- Context cache management

---

## ⚡ **6. RAG Engine (Main Orchestrator)**

**File:** `rag_engine.py`
**Class:** `OptimizedEnhancedRAGService`

**Purpose:** Orchestrate the complete RAG pipeline

- Integrate all services into unified workflow
- VRAM-optimized architecture (CPU embedding, GPU LLM/Reranker)
- Session management and chat history
- Query processing pipeline: Router → Vector Search → Context Expansion → LLM → Reranker
- Performance monitoring and optimization

---

## 🔧 **7. Core Initialization**

**File:** `__init__.py`

**Purpose:** Service exports and initialization

---

## 🚀 **Service Flow Architecture**

```
User Query
    ↓
[Smart Router] ← (embeddings cache: 212 questions)
    ↓ (collection + filters)
[Vector Database] ← (Vietnamese embedding CPU)
    ↓ (similar documents: 262 chunks from 53 JSON files)
[Context Expander] ← (document metadata)
    ↓ (expanded context)
[LLM Service] ← (PhoGPT-4B GPU)
    ↓ (generated response)
[Result Reranker] ← (Vietnamese reranker GPU)
    ↓
Final Answer
```

---

## 📊 **Resource Allocation**

| Service       | Device | Model                   | Purpose           |
| ------------- | ------ | ----------------------- | ----------------- |
| **Vector DB** | CPU    | Vietnamese_Embedding_v2 | VRAM optimization |
| **LLM**       | GPU    | PhoGPT-4B-Chat          | Fast inference    |
| **Reranker**  | GPU    | Vietnamese_Reranker     | Quality scoring   |
| **Router**    | CPU    | Cached embeddings       | Fast routing      |

---

## 📈 **Data Statistics**

- **JSON Documents:** 53 files
- **Vector Chunks:** 262 total chunks (~4.9 chunks per document)
- **Collections:** 3 (chung_thuc, ho_tich_cap_xa, nuoi_con_nuoi)
- **Router Questions:** 212 (cached for fast startup)

---

## 🧹 **Architecture Consolidation**

- **Document Processing** - Now integrated into unified build tool
  - ~~Process JSON documents from `data/documents/`~~
  - ~~Extract metadata and create chunks~~
  - **Consolidated into** `tools/build_vectordb_unified.py` (combines processing + vector DB building)
  - **Not needed in runtime** - vector DB already built with all processing integrated

---

## 💡 **Usage**

All services are automatically initialized in `main.py`:

```python
from app.services.rag_engine import OptimizedEnhancedRAGService

# Main service orchestrator
rag_service = OptimizedEnhancedRAGService(
    vectordb_service=vectordb_service,
    llm_service=llm_service
)
```

**Active Collections:** 3 (chung_thuc, ho_tich_cap_xa, nuoi_con_nuoi)  
**Total Documents:** 262 chunks from 53 JSON files  
**Router Questions:** 212 (cached for fast startup)  
**Startup Time:** ~10 seconds with cache

---

## 🐛 **Architecture Notes**

1. **VRAM Optimized:** Embedding on CPU, LLM+Reranker on GPU
2. **Fast Startup:** Router cache eliminates embedding generation time
3. **Multi-Collection:** Each legal domain has dedicated collection
4. **Vietnamese Optimized:** All models fine-tuned for Vietnamese legal text
5. **Clean Dependencies:** No circular imports or deprecated services
6. **Build vs Runtime:** Document processing moved to tools, runtime only handles search/generation
