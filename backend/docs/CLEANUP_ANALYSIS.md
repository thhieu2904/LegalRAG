# Cleanup Analysis Report - LegalRAG Backend

## Phân tích hiện trạng sử dụng file (18/1/2025)

### ✅ Files ĐANG SỬ DỤNG (Không được move)

#### Main Application Chain

- `main.py` → imports `OptimizedEnhancedRAGService`
- `app/api/optimized_routes.py` → được import trong main.py
- `app/services/optimized_enhanced_rag_service.py` → Core service hiện tại

#### Essential Services (Used by OptimizedEnhancedRAGService)

- `app/services/vectordb_service.py` → Vector database operations
- `app/services/llm_service.py` → LLM integration
- `app/services/reranker_service.py` → Document reranking
- `app/services/enhanced_smart_query_router.py` → Query routing
- `app/services/enhanced_context_expansion_service.py` → Context enhancement

#### Cache System (New - Working)

- `scripts/build_router_cache.py` → Cache builder (Vietnamese model)
- `app/services/cached_enhanced_smart_query_router.py` → Fast cached router
- `data/cache/router_cache.pkl` → Cache data (1.10 MB, 272 questions)

### ❌ Files CẦN CLEANUP (Legacy/Unused)

#### Legacy API Routes (Không được sử dụng)

```
app/api/routes.py              → Old basic routes
app/api/enhanced_routes.py     → Old enhanced routes
app/api/optimized_enhanced_routes.py → Duplicate of optimized_routes.py?
```

#### Legacy Services (Có thể không dùng)

```
app/services/smart_query_router.py       → Old router (trước enhanced)
app/services/ambiguous_query_service.py  → Possibly replaced
app/services/query_router.py             → Basic router
```

#### JSON Processor Files (Có thể legacy)

```
app/services/json_document_processor.py → Possibly unused
```

### 🔄 CẦN KIỂM TRA THÊM

#### Files cần verify usage:

1. **optimized_enhanced_routes.py** vs **optimized_routes.py** → Có duplicate không?
2. **enhanced_smart_query_router.py** → Có được cached router thay thế không?
3. **ambiguous_query_service.py** → Có được RouterBasedAmbiguousQueryService thay thế không?

## ✅ CLEANUP COMPLETED (18/1/2025)

### ✅ Phase 1: Moved Legacy API Routes

```
archive/api_routes_legacy/
├── routes.py                    ✅ MOVED
├── enhanced_routes.py           ✅ MOVED
└── optimized_enhanced_routes.py ✅ MOVED (duplicate)
```

### ✅ Phase 2: Moved Legacy Services

```
archive/services_legacy/
├── smart_query_router.py        ✅ MOVED (old router)
├── ambiguous_query_service.py   ✅ MOVED (replaced by RouterBased version)
└── json_document_processor.py   ✅ MOVED (unused)
```

### ⚠️ Services CANNOT MOVE (Still imported)

```
app/services/query_router.py     ❌ RESTORED (still imported by optimized_enhanced_rag_service)
```

### 🎯 CURRENT STATUS: 6 files cleaned up, app still working!

### Phase 1: Move Legacy API Routes

```
archive/api_routes_legacy/
├── routes.py                    (old basic)
├── enhanced_routes.py           (old enhanced)
└── optimized_enhanced_routes.py (if duplicate)
```

### Phase 2: Move Legacy Services

```
archive/services_legacy/
├── smart_query_router.py        (old router)
├── ambiguous_query_service.py   (if replaced)
├── query_router.py              (basic router)
└── json_document_processor.py   (if unused)
```

### Phase 3: Documentation Archive

```
archive/docs_legacy/
├── Old analysis files
└── Old README versions
```

## ⚠️ CẢNH BÁO

1. **KHÔNG** move file nào trong essential services chain
2. **PHẢI** test sau mỗi move để đảm bảo app vẫn hoạt động
3. **BACKUP** trước khi cleanup
4. **VERIFY** imports trước khi move

## Next Steps

1. Verify exact usage của optimized_enhanced_routes.py
2. Test cached router có thể thay thế enhanced router không
3. Check ambiguous service dependencies
4. Tạo backup và test cleanup từng phase
