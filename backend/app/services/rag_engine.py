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
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path

from .vector_database import VectorDBService
from .language_model import LLMService
from .result_reranker import RerankerService
from .smart_clarification import SmartClarificationService
from .smart_router import EnhancedSmartQueryRouter, RouterBasedAmbiguousQueryService
from .smart_clarification import SmartClarificationService
from .context_expander import EnhancedContextExpansionService
from ..core.config import settings

logger = logging.getLogger(__name__)

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
    cached_rag_content: Optional[Dict[str, Any]] = None
    consecutive_low_confidence_count: int = 0
    
    def update_successful_routing(self, collection: str, confidence: float, rag_content: Optional[Dict[str, Any]] = None):
        """Cập nhật state khi routing thành công với confidence cao"""
        self.last_successful_collection = collection
        self.last_successful_confidence = confidence
        self.last_successful_timestamp = time.time()
        if rag_content:
            self.cached_rag_content = rag_content
        self.consecutive_low_confidence_count = 0  # Reset counter
        
    def should_override_confidence(self, current_confidence: float, confidence_threshold: float = 0.50) -> bool:
        """Kiểm tra có nên override confidence thấp không"""
        if not self.last_successful_collection:
            return False
            
        # Check time window - chỉ override trong vòng 10 phút
        if self.last_successful_timestamp and (time.time() - self.last_successful_timestamp > 600):
            return False
            
        # Override nếu confidence hiện tại thấp nhưng có successful context
        return current_confidence < confidence_threshold and self.last_successful_confidence > 0.85
        
    def increment_low_confidence(self):
        """Tăng counter khi gặp confidence thấp"""
        self.consecutive_low_confidence_count += 1
        
    def clear_routing_state(self):
        """Clear state khi user chuyển chủ đề hoàn toàn"""
        self.last_successful_collection = None
        self.last_successful_confidence = 0.0
        self.last_successful_timestamp = None
        self.cached_rag_content = None
        self.consecutive_low_confidence_count = 0

class OptimizedEnhancedRAGService:
    """
    Enhanced RAG Service được tối ưu VRAM và performance
    
    Kiến trúc:
    - Embedding Model: CPU (tiết kiệm VRAM cho query ngắn)
    - LLM: GPU (cần song song hóa cho context dài)  
    - Reranker: GPU (cần song song hóa cho multiple comparisons)
    """
    
    def __init__(
        self,
        documents_dir: str,
        vectordb_service: VectorDBService,
        llm_service: LLMService
    ):
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
            self.smart_router = EnhancedSmartQueryRouter(embedding_model=embedding_model)
            logger.info("✅ Enhanced Smart Query Router initialized")
            
            # Reranker Service (GPU)
            self.reranker_service = RerankerService()
            logger.info("✅ Reranker Service initialized (GPU)")
            
            # Router-based Ambiguous Query Service (CPU)
            self.ambiguous_service = RouterBasedAmbiguousQueryService(
                router=self.smart_router
            )
            logger.info("✅ Router-based Ambiguous Query Service initialized (CPU)")
            
            # Smart Clarification Service
            self.clarification_service = SmartClarificationService()
            logger.info("✅ Smart Clarification Service initialized")
            
            # Enhanced Context Expansion Service  
            self.context_expansion_service = EnhancedContextExpansionService(
                vectordb_service=self.vectordb_service,
                documents_dir=self.documents_dir
            )
            logger.info("✅ Enhanced Context Expansion Service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise
            
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
        
    def enhanced_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_context_length: int = 8000,  # INCREASED: Tăng từ 3000 lên 8000 để đảm bảo full document context
        use_ambiguous_detection: bool = True,
        use_full_document_expansion: bool = True
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
                    return {"error": f"Session {session_id} not found"}
            else:
                session_id = self.create_session()
                session = self.get_session(session_id)
                
            logger.info(f"Processing query in session {session_id}: {query[:50]}...")
            
            # Step 1: Enhanced Smart Query Routing với MULTI-LEVEL Confidence Processing + Stateful Router
            if use_ambiguous_detection:
                routing_result = self.smart_router.route_query(query, session)
                confidence_level = routing_result.get('confidence_level', 'low')
                was_overridden = routing_result.get('was_overridden', False)
                
                logger.info(f"Router confidence: {confidence_level} (score: {routing_result['confidence']:.3f})")
                if was_overridden:
                    logger.info(f"🔥 Session-based confidence override applied!")
                
                if confidence_level in ['high', 'override_high']:
                    # HIGH CONFIDENCE (including overridden) - Route trực tiếp
                    target_collection = routing_result['target_collection']
                    inferred_filters = routing_result.get('inferred_filters', {})
                    best_collections = [target_collection] if target_collection else [settings.chroma_collection_name]
                    logger.info(f"✅ HIGH CONFIDENCE routing to: {target_collection}")
                    
                elif confidence_level in ['low-medium', 'override_medium']:
                    # MEDIUM CONFIDENCE (including overridden) - Route với caution
                    target_collection = routing_result['target_collection']
                    inferred_filters = routing_result.get('inferred_filters', {})
                    best_collections = [target_collection] if target_collection else [settings.chroma_collection_name]
                    logger.info(f"⚠️ MEDIUM CONFIDENCE routing to: {target_collection}")
                    
                else:
                    # TẤT CẢ CONFIDENCE < THRESHOLD - Hỏi lại user, không route
                    logger.info(f"🤔 CONFIDENCE KHÔNG ĐỦ CAO ({confidence_level}) - hỏi lại user thay vì route")
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
            
            else:
                # Fallback routing logic (giữ nguyên logic cũ)
                routing_result = self.smart_router.route_query(query)
                confidence_level = 'fallback'  # Set default confidence level for fallback
                if routing_result.get('status') == 'routed' and routing_result.get('target_collection'):
                    target_collection = routing_result['target_collection']
                    inferred_filters = routing_result.get('inferred_filters', {})
                    best_collections = [target_collection]
                    logger.info(f"Fallback routed to collection: {target_collection}")
                else:
                    best_collections = [settings.chroma_collection_name]
                    inferred_filters = {}
                    confidence_level = 'fallback'  # Ensure confidence_level is set
            
            # Step 2: Focused Search với ĐỘNG BROAD_SEARCH_K dựa trên router confidence
            # 🚀 PERFORMANCE OPTIMIZATION: Giảm số documents cần rerank
            dynamic_k = settings.broad_search_k  # default 12
            if confidence_level == 'high':
                dynamic_k = max(8, settings.broad_search_k - 4)  # Router tự tin → ít docs hơn
                logger.info(f"🎯 HIGH CONFIDENCE: Giảm broad_search_k xuống {dynamic_k}")
            elif confidence_level in ['low-medium', 'override_medium']:
                dynamic_k = min(15, settings.broad_search_k + 3)  # Router không chắc → nhiều docs hơn
                logger.info(f"🔍 MEDIUM CONFIDENCE: Tăng broad_search_k lên {dynamic_k}")
            else:
                logger.info(f"📊 DEFAULT/FALLBACK: Sử dụng broad_search_k={dynamic_k}")
            
            broad_search_results = []
            for collection_name in best_collections[:2]:  # Limit to top 2 collections
                try:
                    # ✅ CRITICAL FIX: Pass smart filters to vector search với dynamic K
                    results = self.vectordb_service.search_in_collection(
                        collection_name=collection_name,
                        query=query,
                        top_k=dynamic_k,
                        similarity_threshold=settings.similarity_threshold,
                        where_filter=inferred_filters if inferred_filters else None
                    )
                    
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
                # ✅ FIX CRITICAL BUG: Rerank TẤT CẢ documents thay vì chỉ top 10
                # Đây là lỗi logic nghiêm trọng - không được vứt bỏ documents tiềm năng!
                docs_to_rerank = broad_search_results  # RERANK ALL DOCUMENTS
                logger.info(f"Reranking ALL {len(broad_search_results)} candidate documents (FIXED BUG)")
                
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
            
            # 🧠 SMART OPTIMIZATION: Ưu tiên nucleus chunk + context liên quan thay vì cắt ngẫu nhiên
            # Logic: Luôn giữ nguyên nucleus chunk + thêm context xung quanh nếu còn chỗ
            # Step 5: Context Expansion - THIẾT KẾ GỐC: FULL DOCUMENT
            logger.info("Context expansion: Loading TOÀN BỘ DOCUMENT để đảm bảo ngữ cảnh pháp luật đầy đủ")
            
            expanded_context = self.context_expansion_service.expand_context_with_nucleus(
                nucleus_chunks=nucleus_chunks,
                max_context_length=max_context_length,
                include_full_document=use_full_document_expansion
            )
            
            context_text = self._build_context_from_expanded(expanded_context)
            logger.info(f"Context expanded: {expanded_context['total_length']} chars from {len(expanded_context.get('source_documents', []))} documents")
            
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
            # Chỉ update state khi routing thành công với confidence cao
            if routing_result and routing_result.get('confidence', 0) >= 0.85:
                target_collection = routing_result.get('target_collection')
                if target_collection:
                    rag_content = {
                        "context_text": context_text,
                        "nucleus_chunks": nucleus_chunks,
                        "expanded_context": expanded_context,
                        "collections": best_collections
                    }
                    session.update_successful_routing(
                        collection=target_collection, 
                        confidence=routing_result.get('confidence', 0),
                        rag_content=rag_content
                    )
                    logger.info(f"🔥 Updated session state: {target_collection} (confidence: {routing_result.get('confidence', 0):.3f})")
                
            processing_time = time.time() - start_time
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["total_queries"] - 1) + processing_time) 
                / self.metrics["total_queries"]
            )
            
            return {
                "type": "answer",
                "answer": answer,
                "context_info": {
                    "nucleus_chunks": len(nucleus_chunks),
                    "context_length": len(context_text),
                    "source_collections": list(set(chunk.get("collection", "") for chunk in nucleus_chunks)),
                    "source_documents": list(expanded_context.get("source_documents", [])) if expanded_context else []
                },
                "context_details": {
                    "total_length": expanded_context.get("total_length", len(context_text)) if expanded_context else len(context_text),
                    "expansion_strategy": expanded_context.get("expansion_strategy", "unknown") if expanded_context else "no_expansion",
                    "source_documents": expanded_context.get("source_documents", []) if expanded_context else [],
                    "nucleus_chunks_count": len(nucleus_chunks)
                },
                "session_id": session_id,
                "processing_time": processing_time,
                "routing_info": {"best_collections": best_collections}
            }
            
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
        selected_option: str,
        original_query: str
    ) -> Dict[str, Any]:
        """Xử lý phản hồi clarification"""
        session = self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}
            
        # Tạo refined query
        refined_query = f"{original_query} - {selected_option}"
        
        # Process refined query (sẽ không ambiguous nữa)
        return self.enhanced_query(
            query=refined_query,
            session_id=session_id,
            use_ambiguous_detection=False  # Skip ambiguous detection for refined query
        )
        
    def _build_context_from_expanded(self, expanded_context: Dict[str, Any]) -> str:
        """Build context string từ expanded context"""
        context_parts = []
        
        for doc_content in expanded_context.get("expanded_content", []):
            source = doc_content.get("source", "N/A")
            text = doc_content.get("text", "")
            chunk_count = doc_content.get("chunk_count", 0)
            
            context_parts.append(f"=== Tài liệu: {source} ({chunk_count} đoạn) ===\n{text}")
            
        return "\n\n".join(context_parts)
        
    def _generate_answer_with_context(
        self,
        query: str,
        context: str,
        session: OptimizedChatSession
    ) -> str:
        """Generate answer với context và session history"""
        
        # Build conversation context if needed
        conversation_context = ""
        if len(session.query_history) > 0:
            # 🚀 PERFORMANCE OPTIMIZATION: Chỉ lấy 1 lượt hỏi-đáp gần nhất để giảm prompt length
            recent_queries = session.query_history[-1:]  # Only last 1 query thay vì 3
            logger.info(f"⚡ Chat history: {len(recent_queries)} entries (optimized for speed)")
            conversation_context = "Lịch sử hội thoại gần đây:\n" + "\n".join([
                f"Q: {item['query']}\nA: {item['answer'][:100]}..."  # Giảm từ 200 xuống 100 chars
                for item in recent_queries
            ]) + "\n\n"
            
        # ALWAYS use FULL system prompt - No conservative strategy
        system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam.

🚨 QUY TẮC BẮT BUỘC - KHÔNG ĐƯỢC VI PHẠM:
1. CHỈ trả lời dựa CHÍNH XÁC trên thông tin CÓ TRONG tài liệu
2. Nếu hỏi về PHÍ/TIỀN - tìm thông tin "💰 THÔNG TIN PHÍ/LỆ PHÍ" trong tài liệu
3. Nếu có thông tin "Miễn lệ phí" - phải ưu tiên nêu rõ điều này
4. KHÔNG tự sáng tạo thông tin không có trong tài liệu
5. Trả lời NGẮN GỌN (tối đa 3-4 câu)
6. Nếu không chắc chắn - nói "Theo thông tin trong tài liệu..."

Ví dụ trả lời tốt:
- "Theo thông tin trong tài liệu, đăng ký khai sinh đúng hạn được MIỄN LỆ PHÍ."
- "Tài liệu nêu rõ lệ phí là X đồng cho trường hợp Y."

TUYỆT ĐỐI KHÔNG được tự tạo ra thông tin về phí hoặc các quy định không có trong tài liệu."""
        
        logger.info(f"📝 ALWAYS using FULL system prompt (Conservative mode disabled), context length: {len(context)}")
        
        # Build enhanced context với conversation history
        enhanced_context = conversation_context + context
        
        # 🔥 TOKEN MANAGEMENT - Kiểm soát độ dài để tránh context overflow
        from app.core.config import settings
        
        # Ước tính token đơn giản (1 token ≈ 3-4 ký tự tiếng Việt)
        estimated_tokens = len(system_prompt + enhanced_context + query + "Trả lời: ") // 3
        max_context_tokens = settings.n_ctx - 500  # Để lại 500 token cho response
        
        if estimated_tokens > max_context_tokens:
            # Cắt bớt context để fit trong giới hạn
            logger.warning(f"🚨 Context overflow detected: {estimated_tokens} tokens > {max_context_tokens} max")
            
            # Tính toán space còn lại cho context
            fixed_parts_length = len(system_prompt + conversation_context + query + "Trả lời: ")
            remaining_space = (max_context_tokens * 3) - fixed_parts_length
            
            if remaining_space > 500:  # Đảm bảo có ít nhất 500 ký tự cho context
                truncated_context = context[:remaining_space] + "\n\n[...THÔNG TIN ĐÃ ĐƯỢC RÚT GỌN ĐỂ TRÁNH QUÁ TẢI...]"
                enhanced_context = conversation_context + truncated_context
                logger.info(f"✂️ Context truncated from {len(context)} to {len(truncated_context)} chars")
            else:
                # Nếu không đủ chỗ, bỏ conversation history
                enhanced_context = context[:max_context_tokens * 3 // 2] + "\n\n[...RÚT GỌN...]"
                logger.warning("⚠️ Removed conversation history due to extreme context overflow")
        
        logger.info(f"📝 Final context length: {len(enhanced_context)} chars (~{len(enhanced_context)//3} tokens)")

        try:
            response_data = self.llm_service.generate_response(
                user_query=query,
                context=enhanced_context,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system_prompt=system_prompt
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
            collections = self.vectordb_service.list_collections()
            total_documents = 0
            
            for collection_info in collections:
                try:
                    collection = self.vectordb_service.get_collection(collection_info["name"])
                    count = collection.count()
                    total_documents += count
                except:
                    continue
                    
            return {
                "status": "healthy",
                "total_collections": len(collections),
                "total_documents": total_documents,
                "llm_loaded": self.llm_service.model is not None,
                "reranker_loaded": self.reranker_service.model is not None,
                "embedding_device": "CPU (VRAM optimized)",
                "llm_device": "GPU",
                "reranker_device": "GPU",
                "active_sessions": len(self.chat_sessions),
                "metrics": self.metrics,
                "router_stats": self.smart_router.get_collection_info(),
                "context_expansion": {
                    "total_chunks_cached": len(self.context_expansion_service.document_metadata_cache),
                    **self.context_expansion_service.get_stats()
                }
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

    # API Compatibility Methods
    def query(self, question: Optional[str] = None, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Compatibility method cho API routes"""
        # Hỗ trợ cả 'question' và 'query' parameters
        query_text = question or query
        if not query_text:
            raise ValueError("Either 'question' or 'query' parameter is required")
        return self.enhanced_query(query_text, **kwargs)
    
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
                        'suggestion': 'Run python tools/2_build_vectordb_final.py to build collections'
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
                    'suggestion': 'Use python tools/2_build_vectordb_final.py to build new collections from documents'
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
            clarification_service = SmartClarificationService()
            clarification_response = clarification_service.generate_clarification(
                query=query,
                confidence=routing_result.get('confidence', 0.0),
                routing_result=routing_result
            )
            
            # Merge clarification response with required fields
            processing_time = time.time() - start_time
            
            # Get the main response from clarification service
            response = clarification_response.copy()
            
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
        """Compatibility property cho API routes"""
        import os
        
        class DocumentProcessorCompat:
            def get_available_collections(self, documents_dir):
                """Lấy danh sách collections có thể tạo từ documents"""
                try:
                    if not os.path.exists(documents_dir):
                        return []
                    
                    collections = []
                    for item in os.listdir(documents_dir):
                        item_path = os.path.join(documents_dir, item)
                        if os.path.isdir(item_path):
                            # Đếm số files PDF trong thư mục
                            pdf_count = len([f for f in os.listdir(item_path) 
                                           if f.lower().endswith('.pdf')])
                            if pdf_count > 0:
                                collections.append({
                                    'name': item,
                                    'path': item_path,
                                    'document_count': pdf_count
                                })
                    return collections
                except Exception as e:
                    logger.error(f"Error getting available collections: {e}")
                    return []
        
        return DocumentProcessorCompat()
