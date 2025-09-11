"""
Optimized Enhanced RAG Service với VRAM-optimized architecture
Tích hợp:
1. Ambiguous Query Detection & Processing
2. Enhanced Context Expansion với Nucleus Strategy  
3. VRAM-optimized model placement (CPU embedding, GPU LLM/Reranker)
4. Session management
"""

import logging
import time
import uuid
import os
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from .vector import VectorDBService
from .language_model import LLMService
from .reranker import RerankerService
from .clarification import ClarificationService
from .router import QueryRouter, RouterBasedQueryService
from .context import ContextExpander
from .simple_form_detection import SimpleFormDetectionService
from .fee_service import FeeService
from .prompt_service import prompt_service, PromptType
from ..core.config import settings

# Import path_config with try/except for graceful fallback
try:
    from ..core.path_config import path_config
except ImportError:
    logger.warning("PathConfig not available, using old structure only")
    path_config = None

logger = logging.getLogger(__name__)

# 🎯 CENTRALIZED OVERRIDE SYSTEM
class OverrideType(Enum):
    """Types of routing overrides in the system"""
    FORCED_COLLECTION = "forced_collection"
    FORCED_DOCUMENT = "forced_document" 
    MANUAL_INPUT_DOCUMENT = "manual_input_document"
    MANUAL_INPUT_CLARIFICATION = "manual_input_clarification"
    SESSION_CONTEXT = "session_context"

@dataclass
class OverrideContext:
    """Centralized override context for consistent handling"""
    override_type: OverrideType
    target_collection: str
    target_document: Optional[str] = None
    confidence_level: Optional[str] = None
    confidence_score: Optional[float] = None
    inferred_filters: Dict[str, Any] = field(default_factory=dict)
    session_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set confidence based on override type if not provided"""
        if self.confidence_level is None or self.confidence_score is None:
            confidence_mappings = {
                OverrideType.FORCED_COLLECTION: ("forced_high", 0.95),
                OverrideType.FORCED_DOCUMENT: ("forced_high", 0.98),
                OverrideType.MANUAL_INPUT_DOCUMENT: ("manual_input_high", 0.92),
                OverrideType.MANUAL_INPUT_CLARIFICATION: ("manual_input_medium", 0.85),
                OverrideType.SESSION_CONTEXT: ("session_high", 0.88)
            }
            
            level, score = confidence_mappings.get(self.override_type, ("forced_high", 0.95))
            
            if self.confidence_level is None:
                self.confidence_level = level
            if self.confidence_score is None:
                self.confidence_score = score
    
    def to_routing_result(self) -> Dict[str, Any]:
        """Convert to standard routing result format"""
        return {
            "target_collection": self.target_collection,
            "confidence": self.confidence_score,
            "confidence_level": self.confidence_level,
            "inferred_filters": self.inferred_filters,
            "was_overridden": True,
            "override_type": self.override_type.value,
            "best_match": {
                "document": self.target_document,
                "question": "Overridden query"
            } if self.target_document else {}
        }

def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(v) for v in obj)
    else:
        return obj

@dataclass
class OptimizedChatSession:
    """Session chat với thông tin tối ưu với Stateful Router support"""
    session_id: str
    created_at: float
    last_accessed: float
    query_history: List[Dict[str, Any]] = field(default_factory=list)
    context_cache: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Stateful Router State
    last_successful_collection: Optional[str] = None
    last_successful_confidence: float = 0.0
    last_successful_timestamp: Optional[float] = None
    last_successful_filters: Optional[Dict[str, Any]] = None  # 🔥 NEW: Lưu filters từ session thành công
    cached_rag_content: Optional[Dict[str, Any]] = None
    consecutive_low_confidence_count: int = 0
    
    def update_successful_routing(self, collection: str, confidence: float, filters: Optional[Dict[str, Any]] = None, rag_content: Optional[Dict[str, Any]] = None):
        """Cập nhật state khi routing thành công với confidence cao"""
        self.last_successful_collection = collection
        self.last_successful_confidence = confidence
        self.last_successful_timestamp = time.time()
        self.last_successful_filters = filters  # 🔥 NEW: Lưu filters
        if rag_content:
            self.cached_rag_content = rag_content
        self.consecutive_low_confidence_count = 0  # Reset counter
        
    def should_override_confidence(self, current_confidence: float, query: str = "") -> bool:
        """
        Enhanced override logic with follow-up detection
        Ghi đè khi:
        1. Đang có ngữ cảnh tốt được lưu từ trước.
        2. Kết quả định tuyến mới không phải là "rất chắc chắn".
        3. Query hiện tại là follow-up của conversation trước.
        """
        if not self.last_successful_collection:
            return False

        # Chỉ ghi đè trong vòng 10 phút
        if self.last_successful_timestamp and (time.time() - self.last_successful_timestamp > 600):
            return False

        # Ngưỡng tin cậy "rất cao" mà chúng ta sẽ không can thiệp
        VERY_HIGH_CONFIDENCE_GATE = 0.82 
        # Ngưỡng tối thiểu của ngữ cảnh đã lưu để được coi là "tốt"
        MIN_CONTEXT_CONFIDENCE = 0.78

        # Signal 1: Low confidence (traditional approach)
        low_confidence_signal = current_confidence < VERY_HIGH_CONFIDENCE_GATE and self.last_successful_confidence >= MIN_CONTEXT_CONFIDENCE
        
        # Signal 2: Follow-up question (new approach)
        followup_signal = False
        if query:
            followup_signal = self.is_followup_question(query)
        
        # Signal 3: Recent context (within 5 minutes for follow-ups)
        recent_context_signal = self.last_successful_timestamp and (time.time() - self.last_successful_timestamp) < 300
        
        # Override if:
        # - Traditional: low confidence + good context
        # - Follow-up: is follow-up + recent context (regardless of confidence)
        should_override = bool(low_confidence_signal or (followup_signal and recent_context_signal))
        
        if should_override:
            reason = "low_confidence" if low_confidence_signal else "followup_detection"
            logger.info(f"🔥 ENHANCED OVERRIDE: {reason} - current_confidence ({current_confidence:.3f}) < {VERY_HIGH_CONFIDENCE_GATE}, context_confidence ({self.last_successful_confidence:.3f}) >= {MIN_CONTEXT_CONFIDENCE}, followup: {followup_signal}")
        
        return should_override
        
    def is_followup_question(self, query: str) -> bool:
        """
        Detect if current query is a follow-up of previous conversation
        Based on linguistic patterns common in Vietnamese follow-up questions
        """
        if not self.query_history:
            return False
            
        query_lower = query.lower().strip()
        
        # 1. Follow-up keywords (Vietnamese)
        followup_keywords = [
            'nó', 'đó', 'cái này', 'cái đó', 'mình', 'tôi', 'tớ',
            'thế', 'thế nào', 'sao', 'như thế nào', 'ra sao',
            'có cần', 'phải không', 'được không', 'có được không',
            'bao nhiêu', 'bao lâu', 'mất bao lâu', 'thời gian',
            'phí', 'tiền', 'chi phí', 'lệ phí'
        ]
        
        # Check for followup keywords
        has_followup_keyword = any(keyword in query_lower for keyword in followup_keywords)
        
        # 2. Short query (follow-ups are usually shorter)
        is_short_query = len(query.split()) < 10
        
        # 3. Question marks or question patterns
        has_question_pattern = any(word in query_lower for word in ['?', 'không', 'sao', 'thế'])
        
        # 4. Lack of specific legal terms (suggesting context dependency)
        legal_terms = [
            'đăng ký', 'khai sinh', 'hộ tịch', 'nuôi con', 'ly hôn',
            'hôn nhân', 'kết hôn', 'chung sống', 'pháp luật', 'luật',
            'thủ tục', 'giấy tờ', 'công chứng', 'dấu gia'
        ]
        has_specific_legal_terms = any(term in query_lower for term in legal_terms)
        
        # Scoring system
        score = 0
        if has_followup_keyword: score += 2
        if is_short_query: score += 1
        if has_question_pattern: score += 1
        if not has_specific_legal_terms: score += 1
        
        # Follow-up if score >= 2
        is_followup = score >= 2
        
        if is_followup:
            logger.info(f"🔄 FOLLOW-UP DETECTED: '{query}' (score: {score})")
        
        return is_followup
        
    def increment_low_confidence(self):
        """Tăng counter khi gặp confidence thấp"""
        self.consecutive_low_confidence_count += 1
        
    def clear_routing_state(self):
        """Clear state khi user chuyển chủ đề hoàn toàn"""
        self.last_successful_collection = None
        self.last_successful_confidence = 0.0
        self.last_successful_timestamp = None
        self.last_successful_filters = None  # 🔥 NEW: Clear filters cũ
        self.cached_rag_content = None
        self.consecutive_low_confidence_count = 0
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Tạo context summary để hiển thị trên frontend
        """
        context_summary = {
            "session_id": self.session_id,
            "has_active_context": False,
            "current_collection": None,
            "current_collection_display": None,
            "preserved_document": None,
            "active_filters": {},
            "confidence_level": 0.0,
            "context_age_minutes": 0,
            "query_count": len(self.query_history),
            "last_activity": self.last_accessed
        }
        
        # Collection mappings cho display names
        collection_display_map = {
            "luat_doanh_nghiep_2020": "Luật Doanh nghiệp 2020",
            "luat_dat_dai_2013": "Luật Đất đai 2013", 
            "luat_lao_dong_2019": "Luật Lao động 2019",
            "luat_hon_nhan_gia_dinh_2014": "Luật Hôn nhân và Gia đình 2014",
            "luat_dan_su_2015": "Luật Dân sự 2015",
            "luat_hinh_su_2015": "Luật Hình sự 2015",
            "luat_thue_thu_nhap_ca_nhan_2007": "Luật Thuế Thu nhập cá nhân 2007",
            "luat_bao_hiem_xa_hoi_2014": "Luật Bảo hiểm xã hội 2014"
        }
        
        # Kiểm tra có active context không
        if self.last_successful_collection and self.last_successful_timestamp:
            # Tính tuổi của context (phút)
            context_age_seconds = time.time() - self.last_successful_timestamp
            context_age_minutes = int(context_age_seconds / 60)
            
            # Context vẫn valid trong 10 phút
            if context_age_minutes <= 10:
                context_summary.update({
                    "has_active_context": True,
                    "current_collection": self.last_successful_collection,
                    "current_collection_display": collection_display_map.get(
                        self.last_successful_collection, 
                        self.last_successful_collection
                    ),
                    "confidence_level": self.last_successful_confidence,
                    "context_age_minutes": context_age_minutes,
                    "active_filters": self.last_successful_filters or {}
                })
                
                # Kiểm tra có document được preserve không
                # 🔧 FIX: Check multiple sources for document info
                preserved_document = None
                
                # Priority 1: Check session metadata for preserved document (from clarification flow)
                if self.metadata and 'preserved_document' in self.metadata:
                    preserved_doc = self.metadata['preserved_document']
                    if isinstance(preserved_doc, dict) and 'title' in preserved_doc:
                        preserved_document = preserved_doc['title']
                    elif isinstance(preserved_doc, str):
                        preserved_document = preserved_doc
                
                # Priority 2: Check current document from recent queries
                if not preserved_document and self.metadata and 'current_document' in self.metadata:
                    preserved_document = self.metadata['current_document']
                
                # Priority 3: Check successful filters
                if not preserved_document and self.last_successful_filters and "source_file" in self.last_successful_filters:
                    preserved_document = self.last_successful_filters["source_file"]
                
                if preserved_document:
                    context_summary["preserved_document"] = preserved_document
        
        return context_summary

class RAGService:
    """
    RAG Service được tối ưu VRAM và performance
    
    Kiến trúc:
    - Embedding Model: CPU (tiết kiệm VRAM cho query ngắn)
    - LLM: GPU (cần song song hóa cho context dài)  
    - Reranker: GPU (cần song song hóa cho multiple comparisons)
    """
    
    # 🎯 OVERRIDE HELPER METHODS
    def _create_override_context(
        self,
        override_type: OverrideType,
        target_collection: str,
        target_document: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> OverrideContext:
        """Create standardized override context"""
        
        # Determine confidence based on override type
        confidence_mappings = {
            OverrideType.FORCED_COLLECTION: ("forced_high", 0.95),
            OverrideType.FORCED_DOCUMENT: ("forced_high", 0.98),
            OverrideType.MANUAL_INPUT_DOCUMENT: ("manual_input_high", 0.92),
            OverrideType.MANUAL_INPUT_CLARIFICATION: ("manual_input_medium", 0.85),
            OverrideType.SESSION_CONTEXT: ("session_high", 0.88)
        }
        
        confidence_level, confidence_score = confidence_mappings.get(
            override_type, ("forced_high", 0.95)
        )
        
        # Build inferred filters based on override type
        inferred_filters = {}
        if target_document:
            inferred_filters["document_title"] = target_document
            
        # Add any additional filters from kwargs
        inferred_filters.update(kwargs.get('additional_filters', {}))
        
        return OverrideContext(
            override_type=override_type,
            target_collection=target_collection,
            target_document=target_document,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            inferred_filters=inferred_filters,
            session_data=session_data or {}
        )
    
    def _handle_manual_input_override(
        self,
        query: str,
        collection: str,
        document: Optional[str] = None,
        clarification_context: Optional[Dict[str, Any]] = None
    ) -> OverrideContext:
        """Handle manual input override scenarios"""
        
        if document:
            # Manual input with specific document
            return self._create_override_context(
                override_type=OverrideType.MANUAL_INPUT_DOCUMENT,
                target_collection=collection,
                target_document=document,
                additional_filters={"manual_input": True}
            )
        elif clarification_context:
            # Manual input with clarification context
            return self._create_override_context(
                override_type=OverrideType.MANUAL_INPUT_CLARIFICATION,
                target_collection=collection,
                session_data=clarification_context,
                additional_filters={"manual_input": True, "clarification": True}
            )
        else:
            # Basic manual input
            return self._create_override_context(
                override_type=OverrideType.FORCED_COLLECTION,
                target_collection=collection,
                additional_filters={"manual_input": True}
            )
    
    def _handle_forced_routing_override(
        self,
        collection: str,
        document: Optional[str] = None
    ) -> OverrideContext:
        """Handle forced routing scenarios"""
        
        if document:
            return self._create_override_context(
                override_type=OverrideType.FORCED_DOCUMENT,
                target_collection=collection,
                target_document=document
            )
        else:
            return self._create_override_context(
                override_type=OverrideType.FORCED_COLLECTION,
                target_collection=collection
            )
    
    def __init__(
        self,
        documents_dir: Optional[str] = None,  # Made optional, will use path_config if not provided
        vectordb_service: Optional[VectorDBService] = None,
        llm_service: Optional[LLMService] = None
    ):
        # Use new path config by default, fallback to provided documents_dir for backward compatibility
        if documents_dir is None:
            # New structure - use path_config
            self.use_new_structure = True
            self.path_config = path_config
            self.documents_dir = None  # Not used in new structure
        else:
            # Old structure - backward compatibility
            self.use_new_structure = False
            self.path_config = None
            self.documents_dir = documents_dir
            
        self.vectordb_service = vectordb_service
        self.llm_service = llm_service
        
        # Initialize supporting services
        self._initialize_services()
        
        # Chat sessions management
        self.chat_sessions: Dict[str, OptimizedChatSession] = {}
        
        # Performance metrics
        self.metrics = {
            "total_queries": 0,
            "ambiguous_detected": 0,
            "context_expansions": 0,
            "avg_response_time": 0.0
        }
        
        logger.info("✅ Optimized Enhanced RAG Service initialized")
        
    def _initialize_services(self):
        """Khởi tạo các service hỗ trợ với Enhanced Smart Router"""
        try:
            # Enhanced Smart Query Router với Example Questions Database
            embedding_model = self.vectordb_service.embedding_model
            if embedding_model is None:
                raise ValueError("VectorDB embedding model not initialized")
            self.smart_router = QueryRouter(embedding_model=embedding_model)
            logger.info("✅ Enhanced Smart Query Router initialized")
            
            # Reranker Service (GPU)
            self.reranker_service = RerankerService()
            logger.info("✅ Reranker Service initialized (GPU)")
            
            # Router-based Ambiguous Query Service (CPU)
            self.ambiguous_service = RouterBasedQueryService(
                router=self.smart_router
            )
            logger.info("✅ Router-based Ambiguous Query Service initialized (CPU)")
            
            # Smart Clarification Service
            self.clarification_service = ClarificationService()
            logger.info("✅ Smart Clarification Service initialized")
            
            # Enhanced Context Expansion Service  
            self.context_expansion_service = ContextExpander(
                vectordb_service=self.vectordb_service,
                documents_dir=self.documents_dir
            )
            logger.info("✅ Enhanced Context Expansion Service initialized")
            
            # Simple Form Detection Service - consolidated form handling
            self.form_detection_service = SimpleFormDetectionService()
            logger.info("✅ Simple Form Detection Service initialized")
            
            # Fee Service
            self.fee_service = FeeService()
            logger.info("✅ Fee Service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise
    
    # 🚀 HELPER METHODS - INTELLIGENT SYSTEM UTILITIES
    
    def _map_document_title_to_doc_folder(self, document_title: str, collection: str) -> Optional[str]:
        """
        Map document title to correct DOC_XXX folder name
        """
        try:
            import os
            # Try to find matching document folder
            collection_path = f"data/storage/collections/{collection}/documents"
            if os.path.exists(collection_path):
                for doc_folder in os.listdir(collection_path):
                    if doc_folder.startswith("DOC_"):
                        doc_path = os.path.join(collection_path, doc_folder)
                        # Check for matching document file
                        for file in os.listdir(doc_path):
                            if file.endswith('.json') and document_title in file:
                                return doc_folder
            return None
        except Exception as e:
            logger.error(f"Error mapping document title: {e}")
            return None

    def _calculate_adaptive_k(
        self, 
        confidence_level: str, 
        confidence_score: float, 
        query: str,
        session_history: Optional[List] = None
    ) -> int:
        """
        🚀 INTELLIGENT ADAPTIVE K SYSTEM
        Tính toán K thông minh dựa trên nhiều yếu tố
        """
        base_k = settings.broad_search_k  # Default: 12
        
        # 1. CONFIDENCE-BASED ADJUSTMENT
        # 🚀 FIX: Handle both score-based and level-based confidence
        if confidence_level in ['high_confidence', 'override_high', 'forced_high'] or confidence_score >= 0.8:
            confidence_multiplier = 0.5  # High confidence → search ít
        elif confidence_level in ['medium_high_confidence'] or confidence_score >= 0.7:
            confidence_multiplier = 0.7  # Medium-high confidence
        elif confidence_level in ['medium_confidence'] or confidence_score >= 0.6:
            confidence_multiplier = 1.0  # Medium confidence
        elif confidence_level in ['low_confidence', 'insufficient_context'] or confidence_score < 0.6:
            confidence_multiplier = 1.5  # Low confidence → search nhiều
        else:
            # Fallback to score-based logic
            if confidence_score >= 0.9:
                confidence_multiplier = 0.3  # Rất cao
            elif confidence_score >= 0.8:
                confidence_multiplier = 0.5  # Cao
            elif confidence_score >= 0.7:
                confidence_multiplier = 0.7  # Trung bình cao
            elif confidence_score >= 0.6:
                confidence_multiplier = 1.0  # Trung bình
            else:
                confidence_multiplier = 1.5  # Thấp
            
        # 2. QUERY COMPLEXITY ADJUSTMENT
        query_length = len(query.split())
        if query_length <= 3:
            complexity_multiplier = 0.6  # Simple query
        elif query_length <= 8:
            complexity_multiplier = 1.0  # Medium query
        else:
            complexity_multiplier = 1.3  # Complex query
            
        # 3. QUERY TYPE ADJUSTMENT
        if any(word in query.lower() for word in ['phí', 'giá', 'tiền', 'chi phí']):
            intent_multiplier = 0.7  # Specific fact question
        elif any(word in query.lower() for word in ['như thế nào', 'cách', 'thủ tục']):
            intent_multiplier = 1.2  # Process question
        elif any(word in query.lower() for word in ['tất cả', 'toàn bộ', 'chi tiết']):
            intent_multiplier = 1.4  # Comprehensive question
        else:
            intent_multiplier = 1.0  # General question
            
        # 4. SESSION HISTORY LEARNING
        session_multiplier = 1.0
        if session_history and len(session_history) > 0:
            avg_context_length = sum(h.get('context_length', 0) for h in session_history[-3:]) / min(3, len(session_history))
            if avg_context_length < 2000:
                session_multiplier = 0.8  # User prefers short answers
            elif avg_context_length > 8000:
                session_multiplier = 1.3  # User prefers detailed answers
                
        # 5. CALCULATE FINAL K
        final_k = int(base_k * confidence_multiplier * complexity_multiplier * 
                      intent_multiplier * session_multiplier)
        
        # 6. BOUNDS CHECKING
        final_k = max(3, min(50, final_k))
        
        logger.info(f"🎯 ADAPTIVE K: base={base_k}, conf={confidence_multiplier:.1f}, "
                   f"complex={complexity_multiplier:.1f}, intent={intent_multiplier:.1f}, "
                   f"session={session_multiplier:.1f} → final_k={final_k}")
        
        return final_k
    
    def _create_real_nucleus_chunks(
        self, 
        preserved_document: str, 
        collection: str, 
        doc_folder: str, 
        query: str
    ) -> List[Dict[str, Any]]:
        """
        🚀 CREATE REAL NUCLEUS CHUNKS với FULL DOCUMENT CONTENT
        Load đúng document content đầy đủ để match với full document
        🎯 PHASE 4: SYNCHRONIZE CONTENT FORMAT với context expansion
        """
        try:
            # Construct full source path with absolute path
            base_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
            full_source_path = base_path / collection / "documents" / doc_folder / f"{preserved_document}.json"
            
            if not full_source_path.exists():
                logger.error(f"❌ Source file not found: {full_source_path}")
                return []
            
            # Load document content
            with open(full_source_path, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
            
            # 🚀 PHASE 4: Load FULL DOCUMENT CONTENT với format IDENTICAL với context expansion
            content_chunks = document_data.get('content_chunks', [])
            metadata = document_data.get('metadata', {})
            
            if not content_chunks:
                logger.error(f"❌ No content chunks found in {preserved_document}")
                return []
            
            # 🎯 PHASE 4: SYNCHRONIZE CONTENT FORMAT với context expansion
            # Sử dụng EXACT format giống như _load_full_document_and_metadata
            complete_parts = []
            
            # 🧹 PHASE 4: Clean metadata formatting - IDENTICAL với context expansion
            if metadata:
                complete_parts.append("Thông tin thủ tục:")
                for key, value in metadata.items():
                    if value:  # Chỉ loại bỏ empty values
                        clean_key = key.replace('_', ' ').title()
                        complete_parts.append(f"{clean_key}: {value}")
                complete_parts.append("")  # Empty line separator
            
            # 🧹 PHASE 4: Clean content formatting - IDENTICAL với context expansion
            if content_chunks:
                complete_parts.append("Nội dung chi tiết:")
                for chunk in content_chunks:
                    if chunk.get('content'):
                        complete_parts.append(chunk['content'])
                    if chunk.get('subcontent'):
                        for sub in chunk['subcontent']:
                            if sub.get('content'):
                                complete_parts.append(sub['content'])
                complete_parts.append("")
            
            # Join tất cả content với format IDENTICAL
            full_content = "\n".join(complete_parts)
            
            # 🚀 PHASE 4: Tạo nucleus chunk với FULL CONTENT format IDENTICAL
            nucleus_chunk = {
                'content': full_content,  # 🚀 FULL CONTENT với format IDENTICAL!
                'collection': collection,
                'document_title': preserved_document,
                'source_file': preserved_document,
                'rerank_score': 1.0,
                'similarity': 1.0,
                'source': {'file_path': str(full_source_path)},
                'section_title': 'Full Document',
                'chunk_id': 'full_document',
                'metadata': metadata  # Thêm metadata để context.py có thể sử dụng
            }
            
            logger.info(f"✅ Created nucleus chunk with FULL CONTENT: {len(full_content)} chars")
            logger.info(f"   Content preview: {full_content[:200]}...")
            logger.info(f"🎯 PHASE 4: Content format SYNCHRONIZED với context expansion")
            
            return [nucleus_chunk]  # Return list với 1 nucleus chunk duy nhất
            
        except Exception as e:
            logger.error(f"❌ Error creating real nucleus chunks: {e}")
            return []
    

            
    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Tạo session chat mới"""
        session_id = str(uuid.uuid4())
        
        session = OptimizedChatSession(
            session_id=session_id,
            created_at=time.time(),
            last_accessed=time.time(),
            metadata=metadata or {}
        )
        
        self.chat_sessions[session_id] = session
        logger.info(f"Created new chat session: {session_id}")
        
        return session_id
        
    def get_session(self, session_id: str) -> Optional[OptimizedChatSession]:
        """Lấy session theo ID"""
        session = self.chat_sessions.get(session_id)
        if session:
            session.last_accessed = time.time()
        return session
    
    def get_session_context_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy context summary của session để hiển thị trên frontend
        """
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get_context_summary()
    
    def reset_session_context(self, session_id: str) -> bool:
        """
        Reset ngữ cảnh của session về trạng thái mặc định
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        # Clear routing state but keep session alive
        session.clear_routing_state()
        
        # Optionally clear query history (comment out if want to keep chat history)
        # session.query_history = []
        
        logger.info(f"🧹 Reset context for session: {session_id}")
        return True
        
    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        reranker_k: int = 10,
        llm_k: int = 5,
        threshold: float = 0.7,
        forced_collection: Optional[str] = None,  # ⚡ THÊM THAM SỐ ANTI-LOOP
        forced_document_title: Optional[str] = None  # 🔥 NEW: Force exact document filtering
    ) -> Dict[str, Any]:
        """
        Query chính với tất cả tối ưu hóa - THIẾT KẾ GỐC: FULL DOCUMENT EXPANSION
        
        Flow:
        1. Detect ambiguous query (CPU embedding)
        2. Route query nếu clear
        3. Broad search (CPU embedding) 
        4. Rerank (GPU reranker)
        5. Context expansion: TOÀN BỘ DOCUMENT (đảm bảo ngữ cảnh pháp luật đầy đủ)
        6. Generate answer (GPU LLM)
        
        TRIẾT LÝ: Văn bản pháp luật phải được hiểu trong TOÀN BỘ ngữ cảnh của document gốc
        """
        start_time = time.time()
        self.metrics["total_queries"] += 1
        
        try:
            # Get or create session
            if session_id:
                session = self.get_session(session_id)
                if not session:
                    # Create new session with provided ID
                    session = OptimizedChatSession(
                        session_id=session_id,
                        created_at=time.time(),
                        last_accessed=time.time(),
                        metadata={}
                    )
                    self.chat_sessions[session_id] = session
                    logger.info(f"🆕 Created new session with provided ID: {session_id}")
            else:
                session_id = self.create_session()
                session = self.get_session(session_id)
                
            logger.info(f"Processing query in session {session_id}: {query[:50]}...")
            
            # Check for preserved document context from manual input
            if not forced_document_title and not forced_collection and session:
                preserved_document = session.metadata.get('preserved_document')
                if preserved_document:
                    logger.info(f"🔄 Found preserved document context: {preserved_document['title']}")
                    forced_collection = preserved_document['collection']
                    forced_document_title = preserved_document['title']
                    
                # 🔧 NEW: Check for manual input context
                manual_input_context = session.metadata.get('manual_input_context')
                if manual_input_context and manual_input_context.get('bypass_router'):
                    logger.info(f"🔄 Found manual input context: {manual_input_context['collection']}")
                    forced_collection = manual_input_context['collection']
                    # Clear manual input context after use
                    session.metadata.pop('manual_input_context', None)
            
            # Step 1: Enhanced Smart Query Routing với MULTI-LEVEL Confidence Processing + Stateful Router
            if forced_collection:
                # � FORCED ROUTING: Dành cho clarification hoặc debug
                logger.info(f"⚡ Forced routing to collection: {forced_collection} (from clarification/manual input)")
                routing_result = {
                    "target_collection": forced_collection,
                    "confidence": 0.95,  # High confidence cho forced routing
                    "confidence_level": "forced_high",
                    "inferred_filters": {}
                }
                # Get confidence level from routing result for further processing
                confidence_level = routing_result.get('confidence_level', 'forced_high')
                best_collections = [forced_collection]
                inferred_filters = {}
                was_overridden = True  # Forced routing có override
                
                # 🔥 NEW: Add document title filter if specified
                if forced_document_title:
                    inferred_filters = {"document_title": forced_document_title}
                    logger.info(f"🎯 Forced document filter: {forced_document_title}")
                
            else:
                # 🧠 SMART ROUTING: Sử dụng router bình thường
                routing_result = self.smart_router.route_query(query, session)
                confidence_level = routing_result.get('confidence_level', 'low')
                was_overridden = routing_result.get('was_overridden', False)
                inferred_filters = routing_result.get('inferred_filters', {})
                
                logger.info(f"Router confidence: {confidence_level} (score: {routing_result['confidence']:.3f})")
                if was_overridden:
                    logger.info(f"🔥 Session-based confidence override applied!")
                
                if confidence_level in ['high_confidence', 'high', 'override_high', 'high_followup']:
                    # HIGH CONFIDENCE (including overridden & follow-up) - Route trực tiếp
                    target_collection = routing_result['target_collection']
                    inferred_filters = routing_result.get('inferred_filters', {})
                    best_collections = [target_collection] if target_collection else [settings.chroma_collection_name]
                    logger.info(f"✅ HIGH CONFIDENCE ({confidence_level}) routing to: {target_collection}")
                    
                elif confidence_level in ['medium_high_confidence', 'medium_high', 'medium-high', 'override_medium_high']:
                    # MEDIUM-HIGH CONFIDENCE - Show questions within best document
                    logger.info(f"🎯 MEDIUM-HIGH CONFIDENCE ({routing_result['confidence']:.3f}) - showing questions in document")
                    
                    # 🔧 FIX: Set session context để follow-up questions có thể hoạt động 
                    if session:
                        target_collection = routing_result.get('target_collection')
                        session.last_successful_collection = target_collection
                        session.last_successful_filters = routing_result.get('inferred_filters', {})
                        session.last_successful_timestamp = start_time
                        logger.info(f"🔄 Set session context for follow-up: {target_collection}")
                    
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
                    
                elif confidence_level in ['medium_confidence', 'low-medium', 'override_medium', 'medium_followup']:
                    # 🔥 MEDIUM CONFIDENCE FIX - Trigger clarification instead of routing
                    # Vì medium confidence có risk cao matching sai topic → cần hỏi user xác nhận
                    logger.info(f"🤔 MEDIUM CONFIDENCE ({routing_result['confidence']:.3f}) - triggering clarification to avoid wrong routing")
                    
                    # 🔧 FIX: Set session context cho follow-up (medium confidence vẫn có potential collection)
                    if session:
                        target_collection = routing_result.get('target_collection')
                        session.last_successful_collection = target_collection
                        session.last_successful_filters = routing_result.get('inferred_filters', {})
                        session.last_successful_timestamp = start_time
                        logger.info(f"🔄 Set session context for follow-up (medium): {target_collection}")
                    
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
                    
                elif confidence_level in ['low_confidence', 'insufficient_context', 'low']:
                    # LOW CONFIDENCE - Hỏi lại user, không route
                    logger.info(f"🤔 LOW CONFIDENCE ({confidence_level}) - hỏi lại user thay vì route")
                    
                    # 🔧 FIX: Set session context nếu có target collection (low confidence vẫn có thể có best guess)
                    if session and routing_result.get('target_collection'):
                        target_collection = routing_result.get('target_collection')
                        session.last_successful_collection = target_collection
                        session.last_successful_filters = routing_result.get('inferred_filters', {})
                        session.last_successful_timestamp = start_time
                        logger.info(f"🔄 Set session context for follow-up (low): {target_collection}")
                    
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
                
                else:
                    # UNKNOWN CONFIDENCE LEVEL - Log warning và fallback to clarification
                    logger.warning(f"⚠️ UNKNOWN CONFIDENCE LEVEL: {confidence_level} - falling back to clarification")
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
            
            # Check for preserved document from session override
            preserved_document = None
            # 🚀 FIX: Check for both override_high and session override scenarios
            if (confidence_level == 'override_high' and 
                routing_result.get('inferred_filters') and 
                'source_file' in routing_result['inferred_filters']):
                preserved_document = routing_result['inferred_filters']['source_file']
                logger.info(f"⚡ FULL CONTEXT PRESERVATION: Using document {preserved_document} directly from session")
            elif (confidence_level == 'override_high' and 
                  session and 
                  session.metadata.get('current_document')):
                # 🚀 FIX: Use session metadata if inferred_filters doesn't have source_file
                preserved_document = session.metadata['current_document']
                logger.info(f"⚡ SESSION METADATA PRESERVATION: Using document {preserved_document} from session metadata")
            
            # If we have a preserved document, skip search and go directly to context expansion
            if preserved_document:
                # 🚀 FIX: Map document title to correct DOC_XXX folder
                doc_folder = self._map_document_title_to_doc_folder(preserved_document, best_collections[0])
                if not doc_folder:
                    logger.error(f"❌ Could not map document title '{preserved_document}' to DOC folder")
                    # Fallback to normal search
                    preserved_document = None
                else:
                    # 🚀 FIX: Load real document content instead of placeholder
                    nucleus_chunks = self._create_real_nucleus_chunks(
                        preserved_document=preserved_document,
                        collection=best_collections[0],
                        doc_folder=doc_folder,
                        query=query
                    )
                    
                    if not nucleus_chunks:
                        logger.error(f"❌ Could not create real nucleus chunks for {preserved_document}")
                        preserved_document = None
                    else:
                        logger.info(f"🔧 CREATED REAL NUCLEUS CHUNKS: {len(nucleus_chunks)} chunks with real content")
                
                # Skip to context expansion
                logger.info(f"🔒 SESSION CONTINUITY: Skipping vector search and reranking for preserved document")
                expanded_context = self.context_expansion_service.expand_context_with_nucleus(
                    nucleus_chunks=nucleus_chunks,
                    query=query  # 🎯 Pass query for prioritization
                )
                
                # Skip ahead to context building
                context_text = self._build_context_from_expanded(expanded_context, nucleus_chunks)
                
                # ✅ ENHANCED: Smart context building với intent detection
                detected_intent = self._detect_specific_intent(query)
                if detected_intent and expanded_context.get('structured_metadata'):
                    context_text = self._build_smart_context(
                        intent=detected_intent,
                        metadata=expanded_context['structured_metadata'],
                        full_text=context_text
                    )
                
                logger.info(f"Context expanded: {expanded_context['total_length']} chars from {len(expanded_context.get('source_documents', []))} documents")
                if detected_intent:
                    logger.info(f"🎯 Detected intent: {detected_intent} - Applied smart context building")
                
                # Jump to LLM generation
                logger.info("🔄 PHASE 2: LLM Generation (GPU) - Loading LLM for final answer...")
                
                # Skip all the search and reranking logic, move straight to answer generation
                answer = self._generate_answer_with_context(
                    query=query,
                    context=context_text,
                    session=session
                )
                
                # Update session history
                session.query_history.append({
                    "query": query,
                    "answer": answer,
                    "timestamp": time.time(),
                    "nucleus_chunks_count": len(nucleus_chunks),
                    "context_length": len(context_text),
                    "from_preserved_document": True
                })
                
                # Keep only last 5 queries in session
                if len(session.query_history) > 5:
                    session.query_history = session.query_history[-5:]
                
                # Update session state for next query
                session.update_successful_routing(
                    collection=target_collection, 
                    confidence=routing_result.get('confidence', 0.85),
                    filters={"source_file": preserved_document},
                    rag_content={
                        "context_text": context_text,
                        "nucleus_chunks": nucleus_chunks,
                        "expanded_context": expanded_context,
                        "collections": [target_collection]
                    }
                )
                logger.info(f"🔥 Reinforced session state with preserved document: {preserved_document}")
                
                processing_time = time.time() - start_time
                
                # Check for forms
                forms_info = self.check_document_forms([preserved_document])
                
                # Return final response with preserved document
                return {
                    "type": "answer",
                    "answer": answer,
                    "context_info": {
                        "nucleus_chunks": 1,
                        "context_length": len(context_text),
                        "source_collections": [target_collection],
                        "source_documents": [preserved_document],
                        "from_preserved_document": True
                    },
                    "session_id": session_id,
                    "processing_time": processing_time,
                    "routing_info": {
                        "best_collections": [target_collection],
                        "target_collection": target_collection,
                        "confidence": float(routing_result.get('confidence', 0.85)),
                        "confidence_level": "preserved_document",
                        "preserved_document": preserved_document
                    }
                }
                
            else:
                # Step 2: Focused Search với INTELLIGENT ADAPTIVE K SYSTEM  
                # 🚀 FIX: Use intelligent adaptive K calculation
                session_history = session.query_history if session else None
                dynamic_k = self._calculate_adaptive_k(
                    confidence_level=confidence_level,
                    confidence_score=routing_result.get('confidence', 0.0),
                    query=query,
                    session_history=session_history
                )
                
                broad_search_results = []
                for collection_name in best_collections[:2]:  # Limit to top 2 collections
                    try:
                        # ✅ CRITICAL FIX: Pass smart filters to vector search với dynamic K
                        # 🔍 DEBUG: Log filter trước khi tìm kiếm để debug vấn đề filter bị "đánh rơi"
                        logger.info(f"🔍 Chuẩn bị tìm kiếm với filter: {inferred_filters}")
                        
                        # 🔥 ADAPTIVE THRESHOLD: Hạ threshold khi có filter hoặc session override
                        adaptive_threshold = settings.similarity_threshold
                        if inferred_filters:
                            adaptive_threshold = max(0.2, settings.similarity_threshold * 0.5)  # Hạ threshold khi có filter
                            logger.info(f"🎯 ADAPTIVE THRESHOLD: {settings.similarity_threshold} -> {adaptive_threshold} (có filter)")
                        elif was_overridden:
                            # 🔥 SESSION OVERRIDE: Hạ threshold để đảm bảo tìm được context trong session collection
                            adaptive_threshold = max(0.15, settings.similarity_threshold * 0.4)  # Hạ threshold mạnh cho session override
                            logger.info(f"🎯 SESSION OVERRIDE THRESHOLD: {settings.similarity_threshold} -> {adaptive_threshold} (session override)")
                        else:
                            logger.info(f"📊 STANDARD THRESHOLD: {adaptive_threshold} (không có filter)")
                        
                        results = self.vectordb_service.search_in_collection(
                            collection_name=collection_name,
                            query=query,
                            top_k=dynamic_k,
                            similarity_threshold=adaptive_threshold,
                            where_filter=inferred_filters if inferred_filters else None
                        )
                        
                        # Process results and add to broad search results
                        for result in results:
                            result["collection"] = collection_name
                        
                        broad_search_results.extend(results)
                        
                    except Exception as e:
                        logger.warning(f"Error searching in collection {collection_name}: {e}")
            
            logger.info(f"📊 Dynamic search: {len(broad_search_results)} docs (k={dynamic_k}, confidence={confidence_level})")
            
            if not broad_search_results:
                return {
                    "type": "no_results",
                    "message": "Không tìm thấy thông tin liên quan đến câu hỏi của bạn.",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            logger.info(f"Found {len(broad_search_results)} candidate chunks")
            
            # Step 4: SEQUENTIAL PROCESSING để tối ưu VRAM (6GB limit)
            # Phase 1: Reranking - Load Reranker, Unload LLM nếu cần
            logger.info("🔄 PHASE 1: Reranking (GPU) - Optimizing VRAM usage...")
            
            # Temporarily unload LLM để đảm bảo VRAM cho reranker
            if hasattr(self.llm_service, 'unload_model'):
                self.llm_service.unload_model()
            
            if settings.use_reranker and len(broad_search_results) > 1:
                # ✅ ENHANCED RERANKING: Consensus-based document selection for better accuracy
                docs_to_rerank = broad_search_results  # RERANK ALL DOCUMENTS
                logger.info(f"🎯 ENHANCED RERANKING - Analyzing {len(broad_search_results)} candidates for consensus")
                
                if len(broad_search_results) >= 5:
                    # ✅ NEW METHOD: Consensus-based document selection (more robust)
                    consensus_document = self.reranker_service.get_consensus_document(
                        query=query,
                        documents=docs_to_rerank,
                        top_k=5,  # Analyze top 5 candidates
                        consensus_threshold=0.6,  # 3/5 = 60%
                        min_rerank_score=-0.5,  # Adjusted for legal documents
                        router_confidence=routing_result.get('confidence', 0.0),
                        router_confidence_level=routing_result.get('confidence_level', 'low'),
                        router_selected_document=routing_result.get('best_match', {}).get('document')
                    )
                    
                    if consensus_document:
                        nucleus_chunks = [consensus_document]
                        logger.info(f"✅ CONSENSUS FOUND: Selected document based on chunk agreement")
                    else:
                        # Fallback to traditional single best document
                        logger.warning("❌ NO CONSENSUS: Falling back to traditional single best document")
                        nucleus_chunks = self.reranker_service.rerank_documents(
                            query=query,
                            documents=docs_to_rerank,
                            top_k=1,
                            router_confidence=routing_result.get('confidence', 0.0),
                            router_confidence_level=routing_result.get('confidence_level', 'low')
                        )
                else:
                    # Not enough candidates for consensus analysis
                    logger.info(f"INSUFFICIENT CANDIDATES ({len(broad_search_results)}) - Using traditional reranking")
                    nucleus_chunks = self.reranker_service.rerank_documents(
                        query=query,
                        documents=docs_to_rerank,
                        top_k=1,  # CHỈ 1 nucleus chunk cao nhất - sẽ expand toàn bộ document chứa chunk này
                        router_confidence=routing_result.get('confidence', 0.0),
                        router_confidence_level=routing_result.get('confidence_level', 'low')
                    )
                
                # Unload reranker sau khi hoàn thành để giải phóng VRAM
                if hasattr(self.reranker_service, 'unload_model'):
                    self.reranker_service.unload_model()
                
                # 🚨 INTELLIGENT CONFIDENCE CHECK - Kiểm tra COMBINED confidence trước khi gọi LLM
                router_confidence = routing_result.get('confidence', 0.0)
                best_score = nucleus_chunks[0].get('rerank_score', 0) if nucleus_chunks and len(nucleus_chunks) > 0 else 0.0
                
                # Calculate combined confidence score
                combined_confidence = (router_confidence * 0.4 + best_score * 0.6)  # Reranker có trọng số cao hơn
                logger.info(f"🎯 Combined Confidence: {combined_confidence:.4f} (Router: {router_confidence:.4f}, Rerank: {best_score:.4f})")
                
                # SMART CLARIFICATION THRESHOLD - Tránh câu trả lời sai lệch
                CLARIFICATION_THRESHOLD = 0.3  # Điều chỉnh threshold này theo cần thiết
                
                if combined_confidence < CLARIFICATION_THRESHOLD:
                    logger.warning(f"🚨 COMBINED CONFIDENCE QUÁ THẤP ({combined_confidence:.4f} < {CLARIFICATION_THRESHOLD}) - Kích hoạt Smart Clarification")
                    
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
                
                if nucleus_chunks and len(nucleus_chunks) > 0:
                    logger.info(f"Best rerank score: {best_score:.4f}")
                    logger.info("🎯 PURE RERANKER MODE - No protective logic, full expansion strategy")
            
                logger.info(f"Selected {len(nucleus_chunks)} nucleus chunk with rerank-based strategy")
            else:
                nucleus_chunks = broad_search_results[:1]  # Fallback: lấy chunk tốt nhất theo vector similarity
                
            # Step 5: INTELLIGENT Context Expansion - Ưu tiên nucleus chunk + context liên quan
            expanded_context = None
            logger.info("🎯 INTELLIGENT CONTEXT EXPANSION - Ưu tiên nucleus chunk từ reranker")
            self.metrics["context_expansions"] += 1
            
            # 🚀 PHASE 6: COMPLETE CONTENT MATCHING - FINAL FIX
            # Fix nucleus chunks để có content đầy đủ thay vì chỉ 2000 chars
            enhanced_nucleus_chunks = []
            for chunk in nucleus_chunks:
                try:
                    # 🎯 PHASE 6: DEBUG LOGGING - Xem chunk structure
                    logger.debug(f"🔍 Processing chunk: {chunk.keys()}")
                    logger.debug(f"🔍 Chunk source: {chunk.get('source', {})}")
                    logger.debug(f"🔍 Chunk collection: {chunk.get('collection', '')}")
                    
                    # 🎯 PHASE 6: SMART EXTRACTION với ROUTER INFORMATION
                    source_info = chunk.get('source', {})
                    collection = chunk.get('collection', '')
                    
                    # 🚀 PHASE 6: Try multiple extraction strategies
                    document_title = None
                    doc_folder = None
                    
                    # Strategy 1: Use router information (most reliable)
                    if routing_result and routing_result.get('best_match', {}).get('document'):
                        router_document = routing_result['best_match']['document']
                        if router_document:
                            document_title = router_document
                            logger.info(f"🎯 Strategy 1 (Router): Found document: {document_title}")
                    
                    # Strategy 2: Try document_title from source
                    elif source_info.get('document_title'):
                        document_title = source_info.get('document_title')
                        logger.debug(f"🎯 Strategy 2: Found document_title: {document_title}")
                    
                    # Strategy 3: Try source_file from source
                    elif source_info.get('source_file'):
                        document_title = source_info.get('source_file')
                        logger.debug(f"🎯 Strategy 3: Found source_file: {document_title}")
                    
                    # Strategy 4: Try to extract from file_path
                    elif source_info.get('file_path'):
                        file_path = source_info.get('file_path')
                        logger.debug(f"🎯 Strategy 4: Found file_path: {file_path}")
                        # Extract document name from path: .../DOC_001/01. Đăng ký khai sinh.json
                        if 'DOC_' in file_path and '.json' in file_path:
                            parts = file_path.split('\\')  # Windows path
                            if len(parts) >= 2:
                                doc_folder = parts[-2]  # DOC_001
                                # Try to find the actual document file
                                doc_dir = f"data/storage/collections/{collection}/documents/{doc_folder}"
                                if os.path.exists(doc_dir):
                                    # Look for JSON files in the directory
                                    for file in os.listdir(doc_dir):
                                        if file.endswith('.json'):
                                            document_title = file.replace('.json', '')
                                            logger.debug(f"🎯 Strategy 4: Found document from path: {document_title}")
                                            break
                    
                    # Strategy 5: Use router collection + first document (fallback)
                    if not document_title and collection:
                        # Use the first document in collection as fallback
                        collection_path = f"data/storage/collections/{collection}/documents"
                        if os.path.exists(collection_path):
                            doc_folders = [d for d in os.listdir(collection_path) if d.startswith('DOC_')]
                            if doc_folders:
                                doc_folder = doc_folders[0]  # Use first DOC folder
                                doc_dir = f"{collection_path}/{doc_folder}"
                                if os.path.exists(doc_dir):
                                    for file in os.listdir(doc_dir):
                                        if file.endswith('.json'):
                                            document_title = file.replace('.json', '')
                                            logger.info(f"🎯 Strategy 5 (Fallback): Found document from collection: {document_title}")
                                            break
                    
                    # 🚀 PHASE 6: Create enhanced nucleus chunk nếu tìm được document
                    if document_title and collection:
                        # Map document title to DOC folder nếu chưa có
                        if not doc_folder:
                            doc_folder = self._map_document_title_to_doc_folder(document_title, collection)
                        
                        if doc_folder:
                            logger.info(f"🎯 Attempting to enhance: {document_title} in {doc_folder}")
                            # Create enhanced nucleus chunk với full content
                            enhanced_chunks = self._create_real_nucleus_chunks(
                                preserved_document=document_title,
                                collection=collection,
                                doc_folder=doc_folder,
                                query=query
                            )
                            if enhanced_chunks:
                                enhanced_nucleus_chunks.extend(enhanced_chunks)
                                logger.info(f"✅ Enhanced nucleus chunk for {document_title} with full content")
                            else:
                                # Fallback to original chunk
                                enhanced_nucleus_chunks.append(chunk)
                                logger.warning(f"⚠️ Could not enhance {document_title}, using original chunk")
                        else:
                            # Fallback to original chunk
                            enhanced_nucleus_chunks.append(chunk)
                            logger.warning(f"⚠️ Could not map {document_title} to DOC folder")
                    else:
                        # Fallback to original chunk
                        enhanced_nucleus_chunks.append(chunk)
                        logger.warning(f"⚠️ Could not extract document info from chunk: {chunk.keys()}")
                        
                except Exception as e:
                    logger.error(f"❌ Error enhancing nucleus chunk: {e}")
                    # Fallback to original chunk
                    enhanced_nucleus_chunks.append(chunk)
            
            # Use enhanced nucleus chunks if available, otherwise fallback to original
            if enhanced_nucleus_chunks:
                nucleus_chunks = enhanced_nucleus_chunks
                logger.info(f"🚀 Using enhanced nucleus chunks: {len(nucleus_chunks)} chunks with full content")
            else:
                logger.warning("⚠️ No enhanced nucleus chunks available, using original")
            
            # 🧠 SMART OPTIMIZATION: Ưu tiên nucleus chunk + context liên quan thay vì cắt ngẫu nhiên
            # Logic: Luôn giữ nguyên nucleus chunk + thêm context xung quanh nếu còn chỗ
            # Step 5: Context Expansion - THIẾT KẾ GỐC: FULL DOCUMENT
            logger.info("Context expansion: Loading TOÀN BỘ DOCUMENT để đảm bảo ngữ cảnh pháp luật đầy đủ")
            
            expanded_context = self.context_expansion_service.expand_context_with_nucleus(
                nucleus_chunks=nucleus_chunks,
                query=query  # 🎯 Pass query for prioritization
            )
            
            # 🎯 PHASE 1: Apply highlighting cho nucleus chunks
            context_text = self._build_context_from_expanded(expanded_context, nucleus_chunks)
            
            # ✅ ENHANCED: Smart context building với intent detection
            detected_intent = self._detect_specific_intent(query)
            if detected_intent and expanded_context.get('structured_metadata'):
                context_text = self._build_smart_context(
                    intent=detected_intent,
                    metadata=expanded_context['structured_metadata'],
                    full_text=context_text
                )
            
            logger.info(f"Context expanded: {expanded_context['total_length']} chars from {len(expanded_context.get('source_documents', []))} documents")
            if detected_intent:
                logger.info(f"🎯 Detected intent: {detected_intent} - Applied smart context building")
            
            # Phase 2: LLM Generation - Load LLM cho generation phase
            logger.info("🔄 PHASE 2: LLM Generation (GPU) - Loading LLM for final answer...")
            
            # Step 6: Generate Answer (GPU LLM)
            if not session:
                return {
                    "type": "error",
                    "error": "Session not found",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            answer = self._generate_answer_with_context(
                query=query,
                context=context_text,
                session=session
            )
            
            # Update session history
            session.query_history.append({
                "query": query,
                "answer": answer,
                "timestamp": time.time(),
                "nucleus_chunks_count": len(nucleus_chunks),
                "context_length": len(context_text)
            })
            
            # Keep only last 5 queries in session (giảm từ 10 để tiết kiệm memory)
            if len(session.query_history) > 5:
                session.query_history = session.query_history[-5:]
            
            # 🔥 Update session state for Stateful Router
            # Chỉ update state khi routing thành công với confidence đủ tốt (0.78+)
            logger.info(f"🔍 Session update check: routing_result={routing_result is not None}, confidence={routing_result.get('confidence', 0) if routing_result else 'None'}")
            if routing_result and routing_result.get('confidence', 0) >= 0.78:
                target_collection = routing_result.get('target_collection')
                logger.info(f"🔍 Target collection for session update: {target_collection}")
                if target_collection:
                    rag_content = {
                        "context_text": context_text,
                        "nucleus_chunks": nucleus_chunks,
                        "expanded_context": expanded_context,
                        "collections": best_collections
                    }
                    
                    # 🔧 FIX: Also preserve document information from successful queries
                    enhanced_filters = routing_result.get('inferred_filters', {}).copy()
                    if expanded_context and expanded_context.get('source_documents'):
                        # Get the first/main document name
                        source_docs = expanded_context['source_documents']
                        if source_docs:
                            main_doc = source_docs[0] if isinstance(source_docs, list) else str(source_docs)
                            # Extract document title from path
                            if isinstance(main_doc, str) and main_doc:
                                doc_name = main_doc.split('\\')[-1].replace('.json', '') if '\\' in main_doc else main_doc
                                enhanced_filters["source_file"] = doc_name
                                # Also store in session metadata for persistence
                                session.metadata["current_document"] = doc_name
                    
                    session.update_successful_routing(
                        collection=target_collection, 
                        confidence=routing_result.get('confidence', 0),
                        filters=enhanced_filters,  # 🔧 Enhanced filters with document info
                        rag_content=rag_content
                    )
                    logger.info(f"🔥 Updated session state: {target_collection} (confidence: {routing_result.get('confidence', 0):.3f})")
                
            processing_time = time.time() - start_time
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["total_queries"] - 1) + processing_time) 
                / self.metrics["total_queries"]
            )
            
            # 📎 CHECK FOR FORMS: If documents have forms, include them in response
            source_documents = expanded_context.get("source_documents", []) if expanded_context else []
            forms_info = self.check_document_forms(source_documents)
            
            # Extract source documents from expanded context and nucleus chunks
            source_documents = []
            
            # Strategy 1: Try to get from expanded_context
            if expanded_context and expanded_context.get('source_documents'):
                source_documents = expanded_context['source_documents']
                logger.info(f"📝 Extracted source_documents from expanded_context: {source_documents}")
            
            # Strategy 2: Extract from nucleus_chunks if empty
            if not source_documents and nucleus_chunks:
                for chunk in nucleus_chunks:
                    doc_title = chunk.get('document_title') or chunk.get('source_file')
                    if doc_title and doc_title not in source_documents:
                        source_documents.append(doc_title)
                logger.info(f"📝 Extracted source_documents from nucleus_chunks: {source_documents}")
            
            # Strategy 3: Try to extract from enhanced nucleus chunks' metadata
            if not source_documents and hasattr(self, '_last_enhanced_chunks'):
                for chunk in getattr(self, '_last_enhanced_chunks', []):
                    metadata = chunk.get('metadata', {})
                    title = metadata.get('title') or chunk.get('document_title')
                    if title and title not in source_documents:
                        source_documents.append(title)
                logger.info(f"📝 Extracted source_documents from enhanced chunks: {source_documents}")
            
            response = {
                "type": "answer",
                "answer": answer,
                "context_info": {
                    "nucleus_chunks": len(nucleus_chunks),
                    "context_length": len(context_text),
                    "source_collections": list(set(chunk.get("collection", "") for chunk in nucleus_chunks)),
                    "source_documents": source_documents  # Use extracted source_documents
                },
                "context_details": {
                    "total_length": expanded_context.get("total_length", len(context_text)) if expanded_context else len(context_text),
                    "expansion_strategy": expanded_context.get("expansion_strategy", "unknown") if expanded_context else "no_expansion",
                    "source_documents": source_documents,  # Use extracted source_documents
                    "nucleus_chunks_count": len(nucleus_chunks)
                },
                "session_id": session_id,
                "processing_time": processing_time,
                "routing_info": {
                    "best_collections": best_collections,
                    "target_collection": routing_result.get('target_collection'),
                    "confidence": float(routing_result.get('confidence', 0.0)),
                    "original_confidence": float(routing_result.get('original_confidence', 0.0)) if routing_result.get('original_confidence') is not None else None,
                    "was_overridden": routing_result.get('was_overridden', False),
                    "inferred_filters": routing_result.get('inferred_filters', {}),
                    "confidence_level": routing_result.get('confidence_level', 'unknown'),
                    "status": routing_result.get('status', 'routed')
                }
            }
            
            # � FORM PROCESSING: Use consolidated SimpleFormDetectionService only
            try:
                # Use SimpleFormDetectionService for all form processing
                response = self.form_detection_service.enhance_rag_response_with_forms(response)
                
                # Update answer with form references if forms found
                form_attachments = response.get("form_attachments", [])
                if form_attachments:
                    # Check if answer doesn't already mention forms
                    if "form" not in response["answer"].lower() and "mẫu" not in response["answer"].lower():
                        # Add form reference to answer
                        form_text = "\n\n📋 **Biểu mẫu/tờ khai liên quan:**\n"
                        for form in form_attachments:
                            form_text += f"- {form['document_title']}: Xem biểu mẫu đính kèm\n"
                        response["answer"] += form_text
                    
                    logger.info(f"📎 Enhanced response with {len(form_attachments)} form attachments")
                    
            except Exception as e:
                logger.error(f"Error in form detection: {e}")
                # Continue without forms if error occurs
            
            # 💰 ENHANCED FEE INFORMATION: Integrate with FeeService
            try:
                # Get document metadata for fee information
                doc_metadata = {}
                if response.get("source_documents"):
                    # Try to get metadata from the first source document
                    first_doc = response["source_documents"][0]
                    if isinstance(first_doc, dict) and "metadata" in first_doc:
                        doc_metadata = first_doc["metadata"]
                    elif isinstance(first_doc, str):
                        # If it's a document path, we might need to load metadata
                        # For now, skip if we can't get metadata easily
                        pass
                
                if doc_metadata:
                    # Use FeeService to enhance response with fee information
                    response = self.fee_service.enhance_rag_response_with_fee_info(response, doc_metadata)
                    
                    logger.info("💰 Enhanced response with fee information")
                    
            except Exception as e:
                logger.error(f"Error in fee service: {e}")
                # Continue without fee info if error occurs
            
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced query: {e}")
            return {
                "type": "error",
                "error": str(e),
                "session_id": session_id,
                "processing_time": time.time() - start_time
            }
            
    def handle_clarification(
        self,
        session_id: str,
        selected_option: Dict[str, Any],  # 🔧 CHANGE: Nhận full option object thay vì string
        original_query: str
    ) -> Dict[str, Any]:
        """
        MULTI-TURN CONVERSATION: Xử lý phản hồi clarification với nhiều giai đoạn
        - Giai đoạn 2: proceed_with_collection → Generate document suggestions  
        - Giai đoạn 2.5: proceed_with_document → Generate question suggestions within document
        - Giai đoạn 3: proceed_with_question → Run RAG with clarified query
        """
        start_time = time.time()  # 🔧 ADD: Track processing time
        session = self.get_session(session_id)
        if not session:
            return {
                "type": "error", 
                "error": f"Session {session_id} not found",
                "session_id": session_id,
                "processing_time": 0.0
            }
            
        action = selected_option.get('action')
        collection = selected_option.get('collection')
        
        if action == 'show_document_questions' and collection:
            # 🎯 MEDIUM-HIGH CONFIDENCE: Hiển thị câu hỏi trong document cụ thể để chọn
            document = selected_option.get('document', '')
            procedure = selected_option.get('procedure', '')
            
            logger.info(f"🎯 Medium-High Step: User confirmed '{procedure}' in document '{document}'. Showing specific questions.")
            
            try:
                # Sử dụng method mới để lấy câu hỏi liên quan đến procedure trong document
                if document:
                    # Lấy câu hỏi từ document cụ thể
                    document_filename = f"{document}"
                    matching_questions = self.smart_router.get_questions_from_specific_document(collection, document_filename)
                    logger.info(f"🚀 SMART LOADING: Retrieved {len(matching_questions)} questions directly from document {document_filename}")
                else:
                    # Fallback: Sử dụng procedure để lấy câu hỏi liên quan
                    matching_questions = self.smart_router.get_procedure_questions_limited(
                        collection_name=collection,
                        procedure=procedure,
                        limit=20
                    )
                    logger.info(f"🚀 SMART LOADING: Retrieved {len(matching_questions)} procedure-related questions for '{procedure}'")
                
                if not matching_questions:
                    logger.warning(f"⚠️ No questions found for procedure '{procedure}' in document '{document}'")
                    # Fallback
                    collection_questions = self.smart_router.get_example_questions_for_collection(collection)
                    matching_questions = collection_questions[:10]
                    logger.info(f"🔄 Fallback: Loaded {len(matching_questions)} questions (limited from {len(collection_questions)})")
                
                # Create question suggestions (sorted by relevance)
                suggestions = []
                for i, q in enumerate(matching_questions[:8]):  # Top 8 questions
                    question_text = q.get('text', str(q)) if isinstance(q, dict) else str(q)
                    suggestions.append({
                        "id": str(i + 1),
                        "title": question_text,
                        "description": f"Câu hỏi về {procedure}",
                        "action": "proceed_with_question",
                        "collection": collection,
                        "document": document,
                        "procedure": procedure,
                        "question_text": question_text,
                        "source_file": q.get('source', '') if isinstance(q, dict) else '',
                        "category": q.get('category', 'general') if isinstance(q, dict) else 'general'
                    })
                
                # Add manual input option
                suggestions.append({
                    "id": str(len(suggestions) + 1),
                    "title": "Câu hỏi khác...",
                    "description": f"Tôi muốn hỏi về vấn đề khác trong {procedure}",
                    "action": "manual_input",
                    "collection": collection,
                    "document": document,
                    "procedure": procedure
                })
                
                clarification_response = {
                    "message": f"Đây là các câu hỏi về '{procedure}'. Hãy chọn câu hỏi phù hợp:",
                    "options": suggestions,
                    "show_manual_input": True,
                    "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {procedure}...",
                    "context": "document_questions",
                    "metadata": {
                        "collection": collection,
                        "document": document,
                        "procedure": procedure,
                        "stage": "document_questions"
                    }
                }
                
                # Update session state
                session.metadata["routing_state"] = {
                    "collection": collection,
                    "document": document,
                    "procedure": procedure,
                    "stage": "document_questions"
                }
                self.chat_sessions[session_id] = session
                
                return {
                    "answer": clarification_response["message"],
                    "clarification": clarification_response,
                    "collection": collection,
                    "document": document,
                    "procedure": procedure,
                    "type": "clarification_needed",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            except Exception as e:
                logger.error(f"❌ Error in document question generation: {e}")
                return {
                    "answer": f"Có lỗi khi tải câu hỏi về '{procedure}'. Vui lòng thử lại.",
                    "type": "error",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
        
        elif action == 'show_categories':
            # 🔄 User muốn chọn thủ tục khác, hiển thị category suggestions
            logger.info(f"🔄 User wants different categories. Showing all available options.")
            
            try:
                # Get available collections
                collections = self.smart_router.get_collections()
                
                # Create category suggestions
                suggestions = []
                for i, collection_info in enumerate(collections, 1):
                    collection_name = collection_info.get('name')
                    display_name = collection_info.get('display_name', collection_name)
                    description = collection_info.get('description', '')
                    
                    suggestions.append({
                        "id": str(i),
                        "title": display_name,
                        "description": description,
                        "action": "proceed_with_collection",
                        "collection": collection_name
                    })
                
                clarification_response = {
                    "message": "Hãy chọn lĩnh vực thủ tục bạn quan tâm:",
                    "options": suggestions,
                    "show_manual_input": True,
                    "manual_input_placeholder": "Hoặc mô tả cụ thể thủ tục bạn cần...",
                    "context": "category_selection",
                    "metadata": {
                        "stage": "category_selection"
                    }
                }
                
                # Reset session state
                session.metadata["routing_state"] = {
                    "stage": "category_selection"
                }
                self.chat_sessions[session_id] = session
                
                return {
                    "answer": clarification_response["message"],
                    "clarification": clarification_response,
                    "type": "clarification_needed",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            except Exception as e:
                logger.error(f"❌ Error in category generation: {e}")
                return {
                    "answer": "Có lỗi khi tải danh sách thủ tục. Vui lòng thử lại.",
                    "type": "error",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
        
        elif action == 'proceed_with_collection' and collection:
            # 🎯 GIAI ĐOẠN 2: User chọn collection, hiển thị documents để chọn
            logger.info(f"🎯 Clarification Step 2: User selected collection '{collection}'. Showing documents.")
            
            try:
                # 🚀 OPTIMIZATION: Lấy danh sách documents trực tiếp, không qua questions
                collection_documents_list = self.smart_router.get_collection_documents_directly(collection)
                
                # Convert to dictionary format for compatibility
                collection_documents = {}
                for doc_info in collection_documents_list:
                    filename = doc_info['filename']
                    
                    # Clean up document name for display
                    display_name = doc_info['title'][:50] + "..." if len(doc_info['title']) > 50 else doc_info['title']
                    if '. ' in filename:
                        clean_name = filename.split('. ', 1)[1] if '. ' in filename else filename
                        display_name = clean_name
                    
                    collection_documents[display_name] = {
                        "filename": f"{collection}/documents/{filename}/questions.json",
                        "title": display_name,
                        "description": doc_info['description'],
                        "question_count": doc_info['question_count']
                    }
                
                logger.info(f"🚀 OPTIMIZATION: Retrieved {len(collection_documents)} documents directly (no questions loaded)")
                
                if not collection_documents:
                    logger.warning(f"⚠️ No documents found in collection '{collection}'")
                    return {
                        "answer": f"Không tìm thấy tài liệu nào trong '{collection}'. Vui lòng thử lại.",
                        "type": "error",
                        "session_id": session_id,
                        "processing_time": time.time() - start_time
                    }
                
                # Convert to list and limit to top 8 documents
                document_list = list(collection_documents.values())
                document_list = sorted(document_list, key=lambda x: x["question_count"], reverse=True)[:8]
                
                # Tạo suggestions cho document selection
                document_suggestions = []
                for i, doc in enumerate(document_list):
                    document_suggestions.append({
                        "id": str(i + 1),
                        "title": doc['title'],
                        "description": f"Tài liệu: {doc['title']} ({doc['question_count']} câu hỏi)",
                        "action": "proceed_with_document",
                        "collection": collection,
                        "document_filename": doc['filename'],
                        "document_title": doc['title']
                    })
                
                # Tạo clarification response cho document selection
                clarification_response = {
                    "message": f"Bạn đã chọn '{collection}'. Hãy chọn tài liệu cụ thể:",
                    "options": document_suggestions,
                    "show_manual_input": True,
                    "manual_input_placeholder": "Hoặc nhập câu hỏi cụ thể của bạn...",
                    "context": "document_selection",
                    "metadata": {
                        "collection": collection,
                        "available_documents": document_list,
                        "stage": "document_selection"
                    }
                }
                
                # Update session state
                session.metadata["routing_state"] = {
                    "collection": collection,
                    "available_documents": document_list,
                    "stage": "document_selection"
                }
                self.chat_sessions[session_id] = session
                
                return {
                    "answer": clarification_response["message"],
                    "clarification": clarification_response,
                    "collection": collection,
                    "documents": document_list,
                    "type": "clarification_needed",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            except Exception as e:
                logger.error(f"❌ Error in document selection: {e}")
                return {
                    "answer": f"Có lỗi khi tải danh sách tài liệu trong '{collection}'. Vui lòng thử lại.",
                    "type": "error",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
        
        if action == 'show_document_questions' and collection:
            # 🎯 MEDIUM-HIGH CONFIDENCE: Show questions for specific procedure directly
            procedure = selected_option.get('procedure')
            document_title = selected_option.get('document_title') or procedure
            
            logger.info(f"🎯 Medium-High Confidence: Showing questions for procedure '{procedure}' in collection '{collection}'")
            
            try:
                # 🚀 OPTIMIZATION: Sử dụng procedure-limited loading thay vì load toàn bộ collection
                matching_questions = self.smart_router.get_procedure_questions_limited(
                    collection, procedure, limit=20
                )
                
                # If no specific matches, fallback to limited collection loading
                if not matching_questions:
                    logger.info(f"⚠️ No procedure-specific questions found for '{procedure}', using fallback")
                    # Fallback: Lấy 10 questions đầu tiên trong collection thay vì toàn bộ
                    all_questions = self.smart_router.get_example_questions_for_collection(collection)
                    matching_questions = all_questions[:10]  # Chỉ lấy 10 thay vì toàn bộ
                
                logger.info(f"🚀 OPTIMIZATION: Retrieved {len(matching_questions)} procedure-related questions (limited loading)")
                
                # Create question suggestions (from optimized loading)
                suggestions = []
                for i, q in enumerate(matching_questions[:5]):
                    question_text = q.get('text', str(q)) if isinstance(q, dict) else str(q)
                    suggestions.append({
                        "id": str(i + 1),
                        "title": question_text,
                        "description": f"Câu hỏi về {procedure}",
                        "action": "proceed_with_question",
                        "collection": collection,
                        "document_title": document_title,
                        "question_text": question_text,
                        "source_file": q.get('source', '') if isinstance(q, dict) else '',
                        "category": q.get('category', 'general') if isinstance(q, dict) else 'general'
                    })
                
                # Add manual input option
                suggestions.append({
                    "id": str(len(suggestions) + 1),
                    "title": "Câu hỏi khác...",
                    "description": f"Tôi muốn hỏi về vấn đề khác trong {procedure}",
                    "action": "manual_input",
                    "collection": collection,
                    "document_title": document_title
                })
                
                clarification_response = {
                    "message": f"Đây là các câu hỏi thường gặp về '{procedure}'. Hãy chọn câu hỏi phù hợp:",
                    "options": suggestions,
                    "show_manual_input": True,
                    "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {procedure}...",
                    "context": "medium_high_questions",
                    "metadata": {
                        "collection": collection,
                        "procedure": procedure,
                        "document_title": document_title,
                        "stage": "medium_high_questions"
                    }
                }
                
                # Update session state
                session.metadata["routing_state"] = {
                    "collection": collection,
                    "procedure": procedure,
                    "document_title": document_title,
                    "stage": "medium_high_questions"
                }
                self.chat_sessions[session_id] = session
                
                return {
                    "answer": clarification_response["message"],
                    "clarification": clarification_response,
                    "collection": collection,
                    "document_title": document_title,
                    "type": "clarification_needed",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            except Exception as e:
                logger.error(f"❌ Error in medium-high question generation: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "answer": f"Có lỗi khi tải câu hỏi về '{procedure}'. Vui lòng thử lại.",
                    "type": "error",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
        
        if action == 'proceed_with_document' and collection:
            # 🎯 GIAI ĐOẠN 2.5: User chọn document, generate question suggestions trong document đó
            document_filename = selected_option.get('document_filename')
            document_title = selected_option.get('document_title')
            
            logger.info(f"🎯 Clarification Step 2.5: User selected document '{document_title}' in collection '{collection}'. Generating question suggestions.")
            
            try:
                # 🚀 OPTIMIZATION: Lấy questions trực tiếp từ document cụ thể thay vì load toàn bộ collection
                if document_filename:
                    # Sử dụng method mới để lấy chỉ questions của document này
                    document_questions = self.smart_router.get_questions_from_specific_document(collection, document_filename)
                    logger.info(f"🚀 SMART LOADING: Retrieved {len(document_questions)} questions directly from document {document_filename}")
                else:
                    # Fallback: Document filename không rõ, phải load collection
                    logger.warning(f"⚠️ Document filename not specified, falling back to collection loading")
                    logger.info(f"🔄 Fallback: Loading limited questions from collection {collection}")
                    collection_questions = self.smart_router.get_example_questions_for_collection(collection)
                    document_questions = collection_questions[:10]  # Limit to 10 instead of all
                    logger.info(f"🔄 Fallback: Loaded {len(document_questions)} questions (limited from {len(collection_questions)})")
                
                if not document_questions:
                    logger.warning(f"⚠️ No questions found for document {document_title}")
                    # Fallback: Lấy từ collection nhưng giới hạn số lượng
                    logger.info(f"🔄 Fallback: Loading limited questions from collection {collection}")
                    collection_questions = self.smart_router.get_example_questions_for_collection(collection)
                    document_questions = collection_questions[:5]  # Chỉ lấy 5 questions thay vì toàn bộ
                    logger.info(f"🔄 Fallback: Loaded {len(document_questions)} questions (limited from {len(collection_questions)})")
                
                # Create suggestions from document questions
                suggestions = []
                for i, q in enumerate(document_questions[:5]):
                    question_text = q.get('text', str(q)) if isinstance(q, dict) else str(q)
                    suggestions.append({
                        "id": str(i + 1),
                        "title": question_text,
                        "description": f"Câu hỏi về {document_title}",
                        "action": "proceed_with_question",
                        "collection": collection,
                        "document_filename": document_filename,
                        "document_title": document_title,
                        "question_text": question_text,
                        "source_file": q.get('source', '') if isinstance(q, dict) else '',
                        "category": q.get('category', 'general') if isinstance(q, dict) else 'general'
                    })
                
                # Add manual input option
                suggestions.append({
                    "id": str(len(suggestions) + 1),
                    "title": "Câu hỏi khác...",
                    "description": f"Tôi muốn hỏi về vấn đề khác trong {document_title}",
                    "action": "manual_input",
                    "collection": collection,
                    "document_filename": document_filename,
                    "document_title": document_title
                })
                
                collection_display = self.smart_router.collection_mappings.get(collection, {}).get('display_name', collection.replace('_', ' ').title())
                
                clarification_response = {
                    "message": f"Bạn đã chọn tài liệu '{document_title}'. Hãy chọn câu hỏi phù hợp:",
                    "options": suggestions,
                    "show_manual_input": True,
                    "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {document_title}...",
                    "context": "question_selection",
                    "metadata": {
                        "collection": collection,
                        "document_filename": document_filename,
                        "document_title": document_title,
                        "stage": "question_selection"
                    }
                }
                
                # Update session state
                session.metadata["routing_state"] = {
                    "collection": collection,
                    "document_filename": document_filename,
                    "document_title": document_title,
                    "stage": "question_selection"
                }
                self.chat_sessions[session_id] = session
                
                return {
                    "answer": clarification_response["message"],
                    "clarification": clarification_response,
                    "collection": collection,
                    "document_title": document_title,
                    "type": "clarification_needed",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            except Exception as e:
                logger.error(f"❌ Error in document question generation: {e}")
                return {
                    "answer": f"Có lỗi khi tải câu hỏi cho '{document_title}'. Vui lòng thử lại.",
                    "type": "error",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
        elif action == 'proceed_with_question':
            # 🎯 GIAI ĐOẠN 3 → 4: User chọn câu hỏi cụ thể, chạy RAG
            question_text = selected_option.get('question_text')
            document_title = selected_option.get('document_title')  # 🔥 NEW: Get exact document title
            source_file = selected_option.get('source_file')  # 🔥 NEW: For debugging
            
            if question_text and collection:
                logger.info(f"🚀 Clarification Step 3→4: User selected question '{question_text}' in collection '{collection}'.")
                
                # 🔧 FIX: Get the correct document title from source_file instead of using clarification document_title
                actual_document_title = document_title
                if source_file:
                    # Extract DOC_XXX from source_file like "quy_trinh_pbgdpl_htpldn/documents/DOC_001/questions.json"
                    doc_id = None
                    if "/DOC_" in source_file:
                        parts = source_file.split("/")
                        for part in parts:
                            if part.startswith("DOC_"):
                                doc_id = part
                                break
                    
                    if doc_id:
                        # Get the actual document title from the content JSON file
                        try:
                            content_files = list(Path(f"data/storage/collections/{collection}/documents/{doc_id}").glob("*.json"))
                            content_files = [f for f in content_files if f.name != "questions.json"]
                            
                            if content_files:
                                with open(content_files[0], 'r', encoding='utf-8') as f:
                                    content_data = json.load(f)
                                
                                if 'metadata' in content_data and 'title' in content_data['metadata']:
                                    actual_document_title = content_data['metadata']['title']
                                    logger.info(f"🔧 CORRECTED: Using actual document title from {doc_id}: '{actual_document_title}'")
                                else:
                                    logger.warning(f"🔧 No metadata title found in {doc_id}, keeping original title")
                        except Exception as e:
                            logger.warning(f"🔧 Error getting actual document title: {e}")
                
                logger.info(f"🎯 Target document: '{actual_document_title}' (source: {source_file})")
                
                # Chạy RAG với câu hỏi ĐÃ ĐƯỢC LÀM RÕ và collection ĐÃ CHỈ ĐỊNH
                return self.process_query(
                    query=question_text,  # 🔥 Dùng câu hỏi cụ thể, không phải original query mơ hồ
                    session_id=session_id,
                    forced_collection=collection,  # 🔥 Force routing to selected collection
                    forced_document_title=actual_document_title  # 🔥 Use corrected document title
                )
            else:
                return {
                    "type": "error",
                    "error": "Missing question_text or collection for proceed_with_question action",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
            
        elif action == 'manual_input':
            # 🎯 MANUAL INPUT: Sử dụng centralized override system
            manual_query = selected_option.get('manual_query', original_query)
            collection = selected_option.get('collection')
            document = selected_option.get('document')
            clarification_context = selected_option.get('clarification_context', {})
            
            logger.info(f"🎯 Manual Input: '{manual_query}' in collection '{collection}'" + 
                       (f", document '{document}'" if document else ""))
            
            if collection:
                # Create override context for manual input
                override_context = self._handle_manual_input_override(
                    query=manual_query,
                    collection=collection,
                    document=document,
                    clarification_context=clarification_context
                )
                
                logger.info(f"🎯 Manual Input Override: {override_context.override_type.value}")
                
                # Process query with override
                return self.process_query(
                    query=manual_query,
                    session_id=session_id,
                    forced_collection=collection,
                    forced_document_title=document
                )
            else:
                # No collection specified, fall back to normal processing
                return self.process_query(
                    query=manual_query,
                    session_id=session_id
                )
        
        elif action == 'old_manual_input':
            # 🔧 IMPROVED: Manual input với context preservation
            logger.info(f"🔄 Manual input requested by user. Preserving valuable context.")
            
            # ✅ SMART CONTEXT PRESERVATION: Giữ context có giá trị thay vì clear all
            original_routing = session.metadata.get('original_routing_context', {})
            
            # 🔧 FIX: Get collection from original routing context, not from selected_option
            selected_collection = (selected_option.get('collection') or 
                                 original_routing.get('target_collection'))
            selected_document = selected_option.get('document_filename')  # Document user đã chọn (if any)
            document_title = selected_option.get('document_title')  # Document title (if any)
            
            logger.info(f"🔍 Context check: selected_collection={selected_collection}, original_target={original_routing.get('target_collection')}")
            
            # Determine context to preserve based on conversation stage
            if selected_document and selected_collection:
                # Case 2: User đã chọn document → Preserve document-level context
                logger.info(f"🔄 CASE 2: Preserving document context: {document_title} in {selected_collection}")
                session.last_successful_collection = selected_collection
                session.last_successful_confidence = original_routing.get('confidence', 0.7)
                session.last_successful_timestamp = time.time()
                session.last_successful_filters = original_routing.get('inferred_filters', {})
                
                # Also preserve document-specific context
                session.metadata['preserved_document'] = {
                    'filename': selected_document,
                    'title': document_title,
                    'collection': selected_collection
                }
                
                # Clear only metadata về clarification process
                session.metadata.pop('original_routing_context', None)
                session.metadata.pop('original_query', None)
                
                return {
                    "type": "manual_input_request",
                    "message": f"Vui lòng nhập câu hỏi cụ thể về '{document_title}'. Tôi sẽ tìm kiếm trong tài liệu này.",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time,
                    "context_preserved": True,
                    "preserved_collection": selected_collection,
                    "preserved_document": document_title
                }
                
            elif selected_collection:
                # Case 1: User đã chọn collection → Preserve collection context
                logger.info(f"🔄 CASE 1: Preserving collection context: {selected_collection}")
                session.last_successful_collection = selected_collection
                session.last_successful_confidence = original_routing.get('confidence', 0.7)
                session.last_successful_timestamp = time.time()
                session.last_successful_filters = original_routing.get('inferred_filters', {})
                
                # Clear only metadata về clarification process
                session.metadata.pop('original_routing_context', None)
                session.metadata.pop('original_query', None)
                
                return {
                    "type": "manual_input_request",
                    "message": f"Vui lòng nhập lại câu hỏi cụ thể hơn về '{selected_collection}'. Tôi sẽ tìm kiếm trong lĩnh vực này.",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time,
                    "context_preserved": True,
                    "preserved_collection": selected_collection
                }
            else:
                # 🔧 FIX: Check if we have ANY collection context to preserve
                if selected_collection:
                    logger.info(f"🔄 FOUND COLLECTION CONTEXT: Preserving collection context: {selected_collection}")
                    session.last_successful_collection = selected_collection
                    session.last_successful_confidence = original_routing.get('confidence', 0.7)
                    session.last_successful_timestamp = time.time()
                    session.last_successful_filters = original_routing.get('inferred_filters', {})
                    
                    # Clear only metadata về clarification process
                    session.metadata.pop('original_routing_context', None)
                    session.metadata.pop('original_query', None)
                    
                    # 🔥 NEW: Set manual input context for next query
                    session.metadata['manual_input_context'] = {
                        'collection': selected_collection,
                        'bypass_router': True,
                        'preserve_collection': True
                    }
                    
                    return {
                        "type": "manual_input_request",
                        "message": f"Vui lòng nhập lại câu hỏi cụ thể hơn về '{selected_collection}'. Tôi sẽ tìm kiếm trong lĩnh vực này.",
                        "session_id": session_id,
                        "processing_time": time.time() - start_time,
                        "context_preserved": True,
                        "preserved_collection": selected_collection
                    }
                else:
                    # Không có collection context → Clear session (fallback)
                    logger.info(f"🔄 No collection context to preserve, clearing session state.")
                    session.clear_routing_state()
                    session.metadata.clear()
                    
                    return {
                        "type": "manual_input_request",
                        "message": "Vui lòng nhập lại câu hỏi cụ thể hơn. Tôi sẽ tìm kiếm trong ngữ cảnh phù hợp.",
                        "session_id": session_id,
                        "processing_time": time.time() - start_time,
                        "context_preserved": False
                    }
            
            # ✅ Update session access time  
            session.last_accessed = time.time()
            
        else:
            # Invalid action
            return {
                "type": "error",
                "error": f"Invalid clarification action: {action}",
                "session_id": session_id, 
                "processing_time": 0.0
            }
        
    def _build_context_from_expanded(self, expanded_context: Dict[str, Any], nucleus_chunks: Optional[List[Dict]] = None) -> str:
        """
        🎯 PHASE 1: Build context với highlighting cho nucleus chunks
        🧹 PHASE 3: Clean formatting - bỏ decorative symbols
        """
        context_parts = []
        
        for doc_content in expanded_context.get("expanded_content", []):
            source = doc_content.get("source", "N/A")
            text = doc_content.get("text", "")
            chunk_count = doc_content.get("chunk_count", 0)
            
            # Apply highlighting cho nucleus chunk nếu có
            if nucleus_chunks and self.context_expansion_service:
                nucleus_chunk = nucleus_chunks[0]  # Lấy nucleus chunk đầu tiên
                
                # 🔍 DEBUG: Log nucleus chunk structure
                logger.info(f"🔍 Nucleus chunk keys: {list(nucleus_chunk.keys())}")
                logger.info(f"🔍 Nucleus chunk content preview: {nucleus_chunk.get('content', 'NO_CONTENT')[:100]}...")
                
                # Use simplified text directly without highlighting
                # 🧹 PHASE 3: Clean format - bỏ dấu ===
                context_parts.append(f"Tài liệu: {source} ({chunk_count} đoạn)\n{text}")
                logger.info("✅ Used simplified content directly without highlighting")
            else:
                # 🧹 PHASE 3: Clean format - bỏ dấu ===
                context_parts.append(f"Tài liệu: {source} ({chunk_count} đoạn)\n{text}")
            
        return "\n\n".join(context_parts)
    
    def _detect_specific_intent(self, query: str) -> Optional[str]:
        """
        Phát hiện các ý định cụ thể từ câu hỏi của người dùng
        Đây là version đơn giản tập trung vào metadata fields phổ biến
        """
        query_lower = query.lower()
        
        # Intent patterns cho từng loại thông tin
        fee_keywords = ['phí', 'lệ phí', 'bao nhiêu tiền', 'tốn tiền', 'giá', 'chi phí', 'miễn phí']
        time_keywords = ['thời gian', 'bao lâu', 'mất bao lâu', 'khi nào xong', 'mấy ngày', 'thời hạn']
        form_keywords = ['mẫu', 'biểu mẫu', 'tờ khai', 'form', 'đơn', 'giấy tờ cần']
        agency_keywords = ['cơ quan', 'nơi làm', 'đâu', 'ở đâu', 'địa điểm', 'nộp ở đâu']
        requirements_keywords = ['điều kiện', 'yêu cầu', 'cần gì', 'hồ sơ', 'giấy tờ']

        if any(keyword in query_lower for keyword in fee_keywords):
            return 'query_fee'
        if any(keyword in query_lower for keyword in time_keywords):
            return 'query_time'
        if any(keyword in query_lower for keyword in form_keywords):
            return 'query_form'
        if any(keyword in query_lower for keyword in agency_keywords):
            return 'query_agency'
        if any(keyword in query_lower for keyword in requirements_keywords):
            return 'query_requirements'
        
        return None
    
    def _build_smart_context(self, intent: Optional[str], metadata: Dict[str, Any], full_text: str) -> str:
        """
        🧹 PHASE 3: Enhanced smart context building - Cải thiện thông tin về phí
        """
        priority_info = ""
        
        if intent == 'query_fee':
            fee_text = metadata.get('fee_text', '')
            fee_vnd = metadata.get('fee_vnd', 0)
            
            if fee_text:
                # Xử lý thông tin phí chi tiết và rõ ràng
                if fee_vnd == 0 and "Miễn" in fee_text:
                    # Trường hợp miễn phí thủ tục chính nhưng có phí phụ
                    priority_info = f"THÔNG TIN VỀ PHÍ:\n{fee_text}\n\n"
                else:
                    # Trường hợp có phí
                    priority_info = f"LỆ PHÍ: {fee_text}\n\n"
            elif fee_vnd == 0:
                priority_info = f"LỆ PHÍ: Miễn phí\n\n"
            else:
                priority_info = f"LỆ PHÍ: {fee_vnd:,} VNĐ\n\n"
        
        elif intent == 'query_time':
            time_text = metadata.get('processing_time_text', '')
            if time_text:
                priority_info = f"THỜI GIAN XỬ LÝ: {time_text}\n\n"

        elif intent == 'query_form':
            has_form = metadata.get('has_form', False)
            form_text = "Có biểu mẫu/tờ khai cần điền" if has_form else "Không có biểu mẫu cụ thể"
            priority_info = f"BIỂU MẪU: {form_text}\n\n"
            
        elif intent == 'query_agency':
            agency = metadata.get('executing_agency', '')
            if agency:
                priority_info = f"CƠ QUAN THỰC HIỆN: {agency}\n\n"
                
        elif intent == 'query_requirements':
            requirements = metadata.get('requirements_conditions', '')
            if requirements:
                priority_info = f"ĐIỀU KIỆN/YÊU CẦU: {requirements}\n\n"

        # Kết hợp thông tin ưu tiên với full context - CLEAN FORMAT
        if priority_info:
            return f"{priority_info}THÔNG TIN CHI TIẾT:\n{full_text}"
        else:
            # Không có intent cụ thể - giữ nguyên context
            return full_text
        
    def _generate_answer_with_context(
        self,
        query: str,
        context: str,
        session: OptimizedChatSession
    ) -> str:
        """Generate answer với context và session history sử dụng ChatML format"""
        
        # CHUẨN BỊ CHAT HISTORY CÓ CẤU TRÚC cho ChatML template
        chat_history_structured = []
        if len(session.query_history) > 0:
            # 🚀 PERFORMANCE OPTIMIZATION: Chỉ lấy 1 lượt hỏi-đáp gần nhất để giảm prompt length
            recent_queries = session.query_history[-1:]  # Only last 1 query thay vì 3
            logger.info(f"⚡ Chat history: {len(recent_queries)} entries (optimized for speed)")
            
            for item in recent_queries:
                chat_history_structured.append({"role": "user", "content": item['query']})
                # Rút gọn answer để tránh context overflow
                answer_preview = item['answer'][:100] + "..." if len(item['answer']) > 100 else item['answer']
                chat_history_structured.append({"role": "assistant", "content": answer_preview})
            
        # 🎯 PHASE 2: Use Complete Prompt Generation (Single Layer)  
        # Create complete prompt ready for LLM - no further formatting needed
        complete_prompt = prompt_service.get_complete_rag_prompt(
            query=query,
            context=context,
            confidence_level="medium",
            chat_history=chat_history_structured
        )
        
        logger.info(f"� Generated complete prompt, length: {len(complete_prompt)} chars")

        try:
            # 🔥 SIMPLIFIED: Send complete prompt directly to LLM 
            # NO additional formatting in language_model.py
            response_data = self.llm_service.generate_response_direct(
                complete_prompt=complete_prompt,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            # Extract response text from dict
            if isinstance(response_data, dict) and "response" in response_data:
                return response_data["response"].strip()
            elif isinstance(response_data, str):
                return response_data.strip()
            else:
                return str(response_data).strip()
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Xin lỗi, có lỗi xảy ra khi tạo câu trả lời: {e}"
            
    def get_health_status(self) -> Dict[str, Any]:
        """Trạng thái health của service"""
        try:
            # Lấy thống kê từ router thay vì vectordb để accurate hơn
            try:
                router_collections = self.smart_router.get_collections()
                total_collections = len(router_collections)
                total_documents = sum(col.get('file_count', 0) for col in router_collections)
            except:
                # Fallback nếu router chưa ready
                total_collections = 0
                total_documents = 0
                    
            return {
                "status": "healthy",
                "total_collections": total_collections,
                "total_documents": total_documents,
                "llm_loaded": self.llm_service is not None and hasattr(self.llm_service, 'model') and self.llm_service.model is not None,
                "reranker_loaded": self.reranker_service is not None and hasattr(self.reranker_service, 'model') and self.reranker_service.model is not None,
                "embedding_device": "CPU (VRAM optimized)",
                "llm_device": "GPU",
                "reranker_device": "GPU", 
                "active_sessions": len(self.chat_sessions),
                "metrics": self.metrics,
                "router_ready": hasattr(self, 'smart_router') and self.smart_router is not None,
                "context_expansion": {
                    "simplified_mode": True,
                    "strategy": "content_first"
                },
                "ambiguous_patterns": 0  # Placeholder
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Dọn dẹp sessions cũ"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        old_sessions = [
            session_id for session_id, session in self.chat_sessions.items()
            if session.last_accessed < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.chat_sessions[session_id]
            
        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old sessions")
            
        return len(old_sessions)

    def check_document_forms(self, source_documents: List[str]) -> List[Dict[str, Any]]:
        """
        Check if documents have forms and collect form information
        
        Args:
            source_documents: List of document names/titles
            
        Returns:
            List of form info dictionaries
        """
        forms_info = []
        
        if not path_config:
            logger.warning("PathConfig not available, cannot check for forms")
            return forms_info
            
        try:
            for doc_name in source_documents:
                # Search for document across collections
                for collection in path_config.list_collections():
                    documents = path_config.list_documents(collection)
                    
                    # Search by document title or file name
                    matching_doc = None
                    for doc in documents:
                        doc_content = path_config.load_document_json(collection, doc["doc_id"])
                        if doc_content:
                            doc_title = doc_content.get('metadata', {}).get('title', '')
                            if (doc_name in doc_title or doc_title in doc_name or 
                                doc_name in doc.get('json_file', '') or doc_name in doc.get('doc_file', '')):
                                matching_doc = doc
                                break
                    
                    if matching_doc:
                        doc_content = path_config.load_document_json(collection, matching_doc["doc_id"])
                        
                        if doc_content and doc_content.get('metadata', {}).get('has_form'):
                            # Get forms for this document
                            forms_path = path_config.get_document_forms_path(collection, matching_doc["doc_id"])
                            if forms_path and forms_path.exists():
                                forms_list = []
                                for form_file in forms_path.iterdir():
                                    if form_file.is_file() and form_file.suffix.lower() in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
                                        forms_list.append({
                                            'filename': form_file.name,
                                            'path': str(form_file),
                                            'size': form_file.stat().st_size,
                                            'type': form_file.suffix.lower()
                                        })
                                
                                if forms_list:
                                    forms_info.append({
                                        'document': doc_name,
                                        'collection': collection,
                                        'title': doc_content.get('metadata', {}).get('title', doc_name),
                                        'forms': forms_list
                                    })
                        break  # Found document in this collection
                        
        except Exception as e:
            logger.error(f"Error checking document forms: {e}")
            
        return forms_info

    # API Compatibility Methods
    def query(self, question: Optional[str] = None, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Compatibility method cho API routes"""
        # Hỗ trợ cả 'question' và 'query' parameters
        query_text = question or query
        if not query_text:
            raise ValueError("Either 'question' or 'query' parameter is required")
        return self.process_query(query_text, **kwargs)
    
    @property
    def query_router(self):
        """Compatibility property cho API routes"""
        # Tạo wrapper với explain_routing method
        class RouterWrapper:
            def __init__(self, smart_router):
                self.smart_router = smart_router
                # Copy tất cả methods từ smart_router
                for attr in dir(smart_router):
                    if not attr.startswith('_') and callable(getattr(smart_router, attr)):
                        setattr(self, attr, getattr(smart_router, attr))
            
            def explain_routing(self, question: str) -> Dict[str, Any]:
                """Explain routing decision cho question"""
                try:
                    # Sử dụng smart router để classify
                    route_result = self.smart_router.route_query(question)
                    return {
                        'question': question,
                        'route': route_result.get('route_name', 'general'),
                        'confidence': route_result.get('confidence', 0.0),
                        'reasoning': route_result.get('reasoning', 'No reasoning available'),
                        'suggested_collections': route_result.get('suggested_collections', [])
                    }
                except Exception as e:
                    logger.error(f"Error explaining routing: {e}")
                    return {
                        'question': question,
                        'route': 'general',
                        'confidence': 0.0,
                        'reasoning': f'Error: {str(e)}',
                        'suggested_collections': []
                    }
        
        return RouterWrapper(self.smart_router)

    def build_index(self, collection_name: Optional[str] = None, force_rebuild: bool = False, **kwargs) -> Dict[str, Any]:
        """Build index cho collection hoặc tất cả collections"""
        try:
            if collection_name:
                # Build specific collection
                if self.vectordb_service.collection_exists(collection_name):
                    stats = self.vectordb_service.get_collection_stats(collection_name)
                    return {
                        'status': 'success',
                        'collections_processed': 1,
                        'collection_name': collection_name,
                        'message': f'Collection {collection_name} already exists and ready',
                        'document_count': stats.get('document_count', 0)
                    }
                else:
                    return {
                        'status': 'error',
                        'collections_processed': 0,
                        'collection_name': collection_name,
                        'error': f'Collection {collection_name} does not exist',
                        'suggestion': 'Run python tools/2_build_vectordb_modernized.py to build collections'
                    }
            else:
                # Build all collections - return info about existing ones
                collections = self.vectordb_service.list_collections()
                return {
                    'status': 'success',
                    'collections_processed': len(collections),
                    'message': f'Found {len(collections)} existing collections',
                    'collections': [col['name'] for col in collections],
                    'total_documents': sum(col.get('document_count', 0) for col in collections),
                    'suggestion': 'Use python tools/2_build_vectordb_modernized.py to build new collections from documents'
                }
        except Exception as e:
            logger.error(f"Error in build_index: {e}")
            return {
                'status': 'error',
                'collections_processed': 0,
                'error': str(e)
            }
    
    def _generate_smart_clarification(self, routing_result: Dict[str, Any], query: str, session_id: str, start_time: float) -> Dict[str, Any]:
        """Tạo clarification thông minh dựa trên confidence level"""
        try:
            # Gọi Smart Clarification Service để tạo clarification thông minh
            clarification_service = ClarificationService()
            clarification_response = clarification_service.generate_clarification(
                query=query,
                confidence=routing_result.get('confidence', 0.0),
                routing_result=routing_result
            )
            
            # Merge clarification response with required fields
            processing_time = time.time() - start_time
            
            # Get the main response from clarification service
            response = clarification_response.copy()
            
            # 🔧 DEBUG: Log clarification service response
            logger.info(f"📋 Clarification service response target_collection: {clarification_response.get('target_collection')}")
            logger.info(f"📋 Routing result target_collection: {routing_result.get('target_collection')}")
            
            # Add required fields that API expects
            response.update({
                "session_id": session_id,
                "processing_time": processing_time,
                "routing_info": {
                    "target_collection": routing_result.get('target_collection'),
                    "router_confidence": routing_result.get('confidence', 0.0),
                    "status": "smart_clarification"
                }
            })
            
            # 🔧 FIX: Ensure target_collection is at top level (don't override from clarification service)
            if 'target_collection' not in response or response.get('target_collection') is None:
                response['target_collection'] = routing_result.get('target_collection')
            
            # 🔧 STORE ROUTING CONTEXT: Save original routing info to session for Step 2→3 similarity matching
            session = self.get_session(session_id)
            if session:
                session.metadata['original_routing_context'] = routing_result
                session.metadata['original_query'] = query
                logger.info(f"💾 Stored original routing context for session {session_id}")
            
            return convert_numpy_types(response)
            
        except Exception as e:
            logger.error(f"Error generating smart clarification: {e}")
            processing_time = time.time() - start_time
            
            fallback_response = {
                "type": "clarification_needed",
                "confidence": routing_result.get('confidence', 0.0),
                "clarification": {
                    "message": "Xin lỗi, tôi không rõ ý định của câu hỏi. Bạn có thể diễn đạt rõ hơn không?",
                    "options": [
                        {
                            'id': 'retry',
                            'title': "Hãy diễn đạt lại câu hỏi",
                            'description': "Tôi sẽ cố gắng hiểu rõ hơn",
                            'action': 'manual_input'
                        }
                    ],
                    "style": "fallback"
                },
                "session_id": session_id,
                "processing_time": processing_time,
                "routing_info": {
                    "target_collection": routing_result.get('target_collection'),
                    "router_confidence": routing_result.get('confidence', 0.0),
                    "status": "smart_clarification_error",
                    "error": str(e)
                }
            }
            return convert_numpy_types(fallback_response)
    
    def _activate_vector_backup_strategy(self, routing_result: Dict[str, Any], query: str, session_id: str, start_time: float) -> Dict[str, Any]:
        """Kích hoạt Vector Backup Strategy khi Smart Router hoàn toàn thất bại"""
        try:
            logger.info("🚨 Activating Vector Backup Strategy - searching across all collections")
            
            # Thực hiện vector search trực tiếp trên tất cả collections để tìm topics liên quan
            all_collections = self.vectordb_service.list_collections()
            backup_results = []
            
            for collection_info in all_collections[:3]:  # Limit to top 3 collections for performance
                collection_name = collection_info["name"]
                try:
                    collection = self.vectordb_service.get_collection(collection_name)
                    search_results = self.vectordb_service.search_in_collection(
                        collection_name,
                        query,
                        top_k=2,  # Chỉ lấy top 2 results per collection
                        similarity_threshold=0.3,
                        where_filter={}
                    )
                    
                    if search_results:
                        best_result = search_results[0]
                        backup_results.append({
                            'collection': collection_name,
                            'score': best_result.get('similarity', best_result.get('score', 0)),
                            'content': best_result.get('content', best_result.get('document', ''))[:200] + "...",
                            'metadata': best_result.get('metadata', {}),
                            'source': best_result.get('metadata', {}).get('source', 'N/A')
                        })
                        
                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Sort by score và tạo suggestions
            backup_results.sort(key=lambda x: x['score'], reverse=True)
            
            options = []
            for i, result in enumerate(backup_results[:3], 1):
                # Trích xuất title từ metadata nếu có
                metadata = result.get('metadata', {})
                title = metadata.get('document_title', metadata.get('title', f"Thủ tục {result['collection']}"))
                
                option = {
                    'id': str(i),
                    'title': title,
                    'description': f"Điểm tương đồng: {result['score']:.2f} - {result['content']}",
                    'collection': result['collection'],
                    'backup_score': result['score']
                }
                options.append(option)
            
            clarification_msg = "Tôi không tìm thấy câu hỏi mẫu phù hợp, nhưng dựa trên tìm kiếm trong dữ liệu, câu hỏi của bạn có thể liên quan đến:"
            
            if not options:
                clarification_msg = "Xin lỗi, tôi không tìm thấy thông tin phù hợp. Bạn có thể thử với từ khóa khác không?"
            
            logger.info(f"Vector backup strategy found {len(options)} potential matches")
            
            return {
                "type": "clarification_needed",
                "status": "vector_backup",
                "confidence": routing_result.get('confidence', 0.0),
                "clarification": clarification_msg,
                "options": options,
                "backup_results": len(backup_results),
                "session_id": session_id,
                "processing_time": time.time() - start_time,
                "strategy": "vector_backup"
            }
            
        except Exception as e:
            logger.error(f"Error in vector backup strategy: {e}")
            return {
                "type": "clarification_needed",
                "status": "fallback_error", 
                "clarification": "Xin lỗi, có lỗi hệ thống khi xử lý câu hỏi. Vui lòng thử lại sau.",
                "session_id": session_id,
                "processing_time": time.time() - start_time
            }
    
    @property  
    def document_processor(self):
        """Compatibility property cho API routes với hỗ trợ new structure"""
        import os
        
        class DocumentProcessorCompat:
            def get_available_collections(self, documents_dir=None):
                """Lấy danh sách collections từ new structure hoặc old structure"""
                try:
                    # Try new structure first
                    if path_config.is_new_structure_available():
                        collections = []
                        for collection_name in path_config.list_collections():
                            documents = path_config.list_documents(collection_name)
                            doc_count = len([doc for doc in documents if doc["json_path"]])
                            
                            if doc_count > 0:
                                collections.append({
                                    'name': collection_name,
                                    'path': str(path_config.get_collection_dir(collection_name)),
                                    'document_count': doc_count,
                                    'structure': 'new'  # Indicate new structure
                                })
                        
                        logger.info(f"📁 Found {len(collections)} collections in new structure")
                        return collections
                    
                    # Fallback to old structure
                    if documents_dir and os.path.exists(documents_dir):
                        collections = []
                        for item in os.listdir(documents_dir):
                            item_path = os.path.join(documents_dir, item)
                            if os.path.isdir(item_path):
                                # Count JSON files instead of PDF files for old structure
                                json_count = len([f for f in os.listdir(item_path) 
                                               if f.lower().endswith('.json')])
                                if json_count > 0:
                                    collections.append({
                                        'name': item,
                                        'path': item_path,
                                        'document_count': json_count,
                                        'structure': 'old'  # Indicate old structure
                                    })
                        
                        logger.info(f"📁 Found {len(collections)} collections in old structure")
                        return collections
                    
                    logger.warning("📁 No document structure found (neither new nor old)")
                    return []
                    
                except Exception as e:
                    logger.error(f"Error getting available collections: {e}")
                    return []

    def _extract_document_title_from_id(self, document_id: str) -> Optional[str]:
        """Extract document title from document ID for form detection fallback"""
        try:
            if not document_id:
                return None
            
            # For new structure, document_id might be DOC_001 
            # We need to find the actual document title
            # This is a fallback method when context expansion fails
            
            # Try to match with known patterns
            if document_id.startswith("DOC_"):
                # Common titles for DOC_001 in different collections
                common_titles = {
                    "DOC_001": ["Đăng ký khai sinh", "Khai sinh", "Dang ky khai sinh"]
                }
                
                if document_id in common_titles:
                    return common_titles[document_id][0]  # Return first match
            
            # If no pattern match, return the document_id itself as fallback
            return document_id
            
        except Exception as e:
            logger.error(f"Error extracting document title from ID {document_id}: {e}")
            return None
        
        return DocumentProcessorCompat()