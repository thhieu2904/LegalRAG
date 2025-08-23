"""
🎯 KIẾN TRÚC CHUẨN PRODUCTION-READY
"""

# ===== 1. DATA LAYER (Chỉ lưu trữ thuần túy) =====

# File: /documents/DOC_001/document.json  
{
  "metadata": {
    "id": "DOC_001",
    "title": "Đăng ký việc nuôi con nuôi trong nước",
    "code": "QT 01/CX-HCTP",
    "executing_agency": "Ủy ban nhân dân cấp xã",
    "fee_vnd": 400000,
    "processing_time_days": 30,
    "collection": "nuoi_con_nuoi"  // ✅ Single source of truth
  },
  "content_chunks": [...],  // Content thuần túy
}

# File: /documents/DOC_001/questions.json (MỚI - ĐƠN GIẢN)
{
  "main_question": "Thủ tục đăng ký việc nuôi con nuôi trong nước là gì?",
  "question_variants": [
    "Tôi muốn nhận con nuôi thì cần những điều kiện gì?",
    "Hồ sơ xin nhận con nuôi gồm những gì?"
  ]
}

# ===== 2. BUSINESS LOGIC LAYER (Code thuần túy) =====

# File: router/filter_engine.py (MỚI)
class FilterEngine:
    @staticmethod
    def derive_smart_filters(metadata: Dict) -> Dict:
        """Derive filters from metadata - KHÔNG CẦN LƯU file"""
        return {
            "exact_title": [metadata.get("title")],
            "procedure_code": [metadata.get("code")], 
            "agency": [metadata.get("executing_agency")],
            "cost_range": FilterEngine._derive_cost_range(metadata.get("fee_vnd")),
            "processing_speed": FilterEngine._derive_speed(metadata.get("processing_time_days"))
        }
    
    @staticmethod
    def _derive_cost_range(fee: int) -> str:
        if fee == 0: return "free" 
        elif fee < 100000: return "low"
        elif fee < 500000: return "medium"
        else: return "high"

# File: router/collection_mapper.py (MỚI)  
class CollectionMapper:
    @staticmethod
    def infer_collection(document_path: str) -> str:
        """Infer collection from path - KHÔNG CẦN LƯU file"""
        return Path(document_path).parent.parent.name

# ===== 3. SERVICE LAYER (Business operations) =====

# File: services/document_service.py (CẢI TIẾN)
class DocumentService:
    def get_document_with_questions(self, doc_id: str) -> DocumentWithQuestions:
        # ✅ Single source of truth
        metadata = self._load_document_metadata(doc_id) 
        questions = self._load_questions(doc_id)
        
        # ✅ Derive tại runtime - KHÔNG lưu file
        smart_filters = FilterEngine.derive_smart_filters(metadata)
        collection = CollectionMapper.infer_collection(doc_path) 
        
        return DocumentWithQuestions(
            metadata=metadata,
            questions=questions, 
            smart_filters=smart_filters,  # Runtime only
            collection=collection         # Runtime only
        )

# ===== 4. CONFIGURATION LAYER (Centralized) =====

# File: config/router_config.py (MỚI)
class RouterConfig:
    HIGH_CONFIDENCE_THRESHOLD = 0.80
    MEDIUM_CONFIDENCE_THRESHOLD = 0.65
    MIN_CONFIDENCE_THRESHOLD = 0.50
    
    FILTER_MAPPINGS = {
        "agency_mapping": {
            "Ủy ban nhân dân cấp xã": "commune",
            "Ủy ban nhân dân cấp huyện": "district", 
            "Ủy ban nhân dân cấp tỉnh": "province"
        }
    }

# ===== 5. API LAYER (Clean interfaces) =====

# File: api/router_api.py (CẢI TIẾN)
@router.get("/documents/{doc_id}/questions")
async def get_document_questions(doc_id: str):
    """✅ Clean API - logic in service layer"""
    doc_with_questions = document_service.get_document_with_questions(doc_id)
    return {
        "questions": doc_with_questions.questions,
        "metadata": doc_with_questions.metadata,
        # Filters derived tại runtime - KHÔNG lưu DB  
        "derived_filters": doc_with_questions.smart_filters
    }
