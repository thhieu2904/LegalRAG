# Services Refactoring Plan

## 🎯 Current Issues
1. **Complex names**: `optimized_enhanced_rag_service.py`, `cached_enhanced_smart_query_router.py`
2. **Scattered logic**: Multiple services could be combined
3. **Hard-to-remember function names**: Simple logic with complex names

## 🔄 Proposed Refactoring

### Phase 1: Rename Core Services
```
BEFORE → AFTER

optimized_enhanced_rag_service.py → rag_service.py (main service)
vectordb_service.py → vector_service.py (shorter)
llm_service.py → llm_service.py (keep)
reranker_service.py → reranker_service.py (keep)
```

### Phase 2: Router Consolidation
```
BEFORE → AFTER

enhanced_smart_query_router.py → query_router.py (main router)  
cached_enhanced_smart_query_router.py → router_cache.py (cache layer)
query_router.py → archive (basic version)
```

### Phase 3: Context Services Merge
```
BEFORE → AFTER

enhanced_context_expansion_service.py → context_service.py (simplified)
```

### Phase 4: Function Name Simplification

**RAGService** (was OptimizedEnhancedRAGService):
```python
# BEFORE
async def process_enhanced_context_aware_query_with_ambiguity_detection(...)

# AFTER  
async def answer_query(...)
async def chat(...)
async def search_documents(...)
```

**QueryRouter** (was EnhancedSmartQueryRouter):
```python
# BEFORE
def route_query_to_appropriate_collection_with_confidence_scoring(...)

# AFTER
def route(query: str) → RoutingResult
def get_best_collection(query: str) → str
```

**VectorService** (was VectorDBService):
```python
# BEFORE
def retrieve_relevant_documents_with_similarity_scoring(...)

# AFTER
def search(query: str, collection: str) → List[Document]
def similarity_search(query: str, k: int = 5) → List[Document]
```

## 🚀 Benefits

1. **Shorter imports**: `from app.services.rag_service import RAGService`
2. **Clearer purpose**: `router_cache.py` vs `cached_enhanced_smart_query_router.py`
3. **Simpler APIs**: `rag.answer_query()` vs `rag.process_enhanced_context_aware_query()`
4. **Better maintenance**: Fewer files, clearer responsibilities

## ⚠️ Implementation Strategy

1. **Create new files** with better names
2. **Copy + simplify** logic from old files  
3. **Update imports** in main.py and routes
4. **Test thoroughly** before removing old files
5. **Move old files** to archive

Would you like to proceed with this refactoring?
