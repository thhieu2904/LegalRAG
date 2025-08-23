# HIỆN TẠI - VI PHẠM SEPARATION OF CONCERNS

┌─────────────────────────────────────────────────────────────┐
│ router_questions.json (LỘN XỘN - LÀMP NHIỀU VIỆC) │
├─ Data: questions, variants ✅ ĐÚNG │
├─ Metadata: title, code ❌ DUPLICATE │  
├─ Business Logic: smart_filters ❌ SAI CHỖ │
├─ Configuration: confidence_threshold ❌ SAI CHỖ │  
├─ Collection Mapping: expected_collection ❌ DERIVED │
└─ Runtime Attributes: key_attributes ❌ SAI CHỖ │
└─────────────────────────────────────────────────────────────┘

# NÊN LÀ - ĐÚNG SEPARATION OF CONCERNS

┌─────────────────────────────────────────────────────────────┐
│ questions.json (CHỈ DATA) │
├─ main_question: "..." ✅ ĐÚNG │
└─ question_variants: [...] ✅ ĐÚNG │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ document.json (METADATA + CONTENT) │
├─ metadata: {title, code, agency...} ✅ SINGLE SOURCE│
└─ content_chunks: [...] ✅ ĐÚNG │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ router.py (BUSINESS LOGIC) │
├─ smart_filters = derive_from_metadata() ✅ ĐÚNG │
├─ confidence_threshold = 0.8 ✅ ĐÚNG │
└─ collection = infer_from_path() ✅ ĐÚNG │
└─────────────────────────────────────────────────────────────┘
