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
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .vector_database import VectorDBService
from .language_model import LLMService
from .result_reranker import RerankerService
from .smart_router import EnhancedSmartQueryRouter, RouterBasedAmbiguousQueryService
from .context_expander import EnhancedContextExpansionService
from ..core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class OptimizedChatSession:
    """Session chat với thông tin tối ưu"""
    session_id: str
    created_at: float
    last_accessed: float
    query_history: List[Dict[str, Any]] = field(default_factory=list)
    context_cache: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

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
        max_context_length: int = 3000,
        use_ambiguous_detection: bool = True,
        use_full_document_expansion: bool = True
    ) -> Dict[str, Any]:
        """
        Query chính với tất cả tối ưu hóa
        
        Flow:
        1. Detect ambiguous query (CPU embedding)
        2. Route query nếu clear
        3. Broad search (CPU embedding) 
        4. Rerank (GPU reranker)
        5. Context expansion với nucleus strategy
        6. Generate answer (GPU LLM)
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
            
            # Step 1: Enhanced Smart Query Routing với MULTI-LEVEL Confidence Processing
            if use_ambiguous_detection:
                routing_result = self.smart_router.route_query(query)
                confidence_level = routing_result.get('confidence_level', 'low')
                
                logger.info(f"Router confidence: {confidence_level} (score: {routing_result['confidence']:.3f})")
                
                if confidence_level == 'high':
                    # HIGH CONFIDENCE - Route trực tiếp
                    target_collection = routing_result['target_collection']
                    inferred_filters = routing_result.get('inferred_filters', {})
                    best_collections = [target_collection] if target_collection else [settings.chroma_collection_name]
                    logger.info(f"✅ HIGH CONFIDENCE routing to: {target_collection}")
                    
                else:
                    # TẤT CẢ CONFIDENCE < HIGH THRESHOLD - Hỏi lại user, không route
                    logger.info(f"🤔 CONFIDENCE KHÔNG ĐỦ CAO ({confidence_level}) - hỏi lại user thay vì route")
                    return self._generate_smart_clarification(routing_result, query, session_id, start_time)
            
            else:
                # Fallback routing logic (giữ nguyên logic cũ)
                routing_result = self.smart_router.route_query(query)
                if routing_result.get('status') == 'routed' and routing_result.get('target_collection'):
                    target_collection = routing_result['target_collection']
                    inferred_filters = routing_result.get('inferred_filters', {})
                    best_collections = [target_collection]
                    logger.info(f"Fallback routed to collection: {target_collection}")
                else:
                    best_collections = [settings.chroma_collection_name]
                    inferred_filters = {}
            
            # Step 2: Focused Search trong target collection với smart filters
            broad_search_results = []
            for collection_name in best_collections[:2]:  # Limit to top 2 collections
                try:
                    # ✅ CRITICAL FIX: Pass smart filters to vector search
                    results = self.vectordb_service.search_in_collection(
                        collection_name=collection_name,
                        query=query,
                        top_k=settings.broad_search_k,
                        similarity_threshold=settings.similarity_threshold,
                        where_filter=inferred_filters if inferred_filters else None
                    )
                    
                    for result in results:
                        result["collection"] = collection_name
                        
                    broad_search_results.extend(results)
                    
                except Exception as e:
                    logger.warning(f"Error searching in collection {collection_name}: {e}")
            
            if not broad_search_results:
                return {
                    "type": "no_results",
                    "message": "Không tìm thấy thông tin liên quan đến câu hỏi của bạn.",
                    "session_id": session_id,
                    "processing_time": time.time() - start_time
                }
                
            logger.info(f"Found {len(broad_search_results)} candidate chunks")
            
            # Step 4: Reranking (GPU - high precision) - LẤY 1 CHUNK CAO NHẤT SAU RERANK
            if settings.use_reranker and len(broad_search_results) > 1:
                # ✅ FIX CRITICAL BUG: Rerank TẤT CẢ documents thay vì chỉ top 10
                # Đây là lỗi logic nghiêm trọng - không được vứt bỏ documents tiềm năng!
                docs_to_rerank = broad_search_results  # RERANK ALL DOCUMENTS
                logger.info(f"Reranking ALL {len(broad_search_results)} candidate documents (FIXED BUG)")
                
                nucleus_chunks = self.reranker_service.rerank_documents(
                    query=query,
                    documents=docs_to_rerank,
                    top_k=1  # CHỈ 1 nucleus chunk cao nhất - sẽ expand toàn bộ document chứa chunk này
                )
                
                # ✅ INTELLIGENT VALIDATION: Kiểm tra rerank score và điều chỉnh strategy
                if nucleus_chunks and len(nucleus_chunks) > 0:
                    best_score = nucleus_chunks[0].get('rerank_score', 0)
                    logger.info(f"Best rerank score: {best_score:.4f}")
                    
                    # CRITICAL DECISION POINT: Nếu điểm thấp, chuyển sang Conservative Strategy
                    if best_score < 0.2:  # Ngưỡng nghiêm ngặt hơn
                        logger.warning(f"⚠️  LOW RERANK SCORE ({best_score:.4f}) - Chuyển sang Conservative Strategy!")
                        logger.warning("💡 Strategy: Chỉ sử dụng chunk có liên quan nhất, KHÔNG expand full document")
                        
                        # Conservative Strategy: KHÔNG expand full document
                        use_full_document_expansion = False
                        max_context_length = 800  # Giảm context length drastically
                        
                        # Lọc thêm 1 lần nữa - chỉ giữ chunks thực sự có keyword liên quan
                        filtered_chunks = []
                        query_keywords = query.lower().split()
                        
                        for chunk in nucleus_chunks:
                            chunk_content = chunk.get('content', '').lower()
                            # Kiểm tra xem chunk có chứa từ khóa liên quan không
                            if any(keyword in chunk_content for keyword in ['phí', 'tiền', 'lệ phí', 'miễn', 'cost', 'fee']):
                                filtered_chunks.append(chunk)
                                logger.info(f"✅ Chunk được giữ lại vì có từ khóa liên quan")
                                break  # Chỉ lấy 1 chunk tốt nhất
                        
                        nucleus_chunks = filtered_chunks if filtered_chunks else nucleus_chunks[:1]
                        logger.info(f"🎯 Conservative Strategy: Sử dụng {len(nucleus_chunks)} chunk với context giới hạn")
                    
                    else:
                        logger.info(f"✅ HIGH RERANK SCORE ({best_score:.4f}) - Sử dụng Full Document Strategy")
                
                logger.info(f"Selected {len(nucleus_chunks)} nucleus chunk with rerank-based strategy")
            else:
                nucleus_chunks = broad_search_results[:1]  # Fallback: lấy chunk tốt nhất theo vector similarity
                
            # Step 5: Intelligent Context Expansion - Dựa trên rerank score để quyết định strategy
            expanded_context = None
            if use_full_document_expansion:
                logger.info("📈 Using FULL DOCUMENT expansion strategy")
                self.metrics["context_expansions"] += 1
                expanded_context = self.context_expansion_service.expand_context_with_nucleus(
                    nucleus_chunks=nucleus_chunks,
                    max_context_length=max_context_length,
                    include_full_document=True  # Full document expansion
                )
                
                context_text = self._build_context_from_expanded(expanded_context)
                logger.info(f"Context expanded: {expanded_context['total_length']} chars from {len(expanded_context.get('source_documents', []))} documents")
                
            else:
                logger.info("🎯 Using CONSERVATIVE chunk-only strategy")
                # Conservative Strategy: Chỉ sử dụng chunk chính xác, KHÔNG expand
                context_parts = []
                for chunk in nucleus_chunks:
                    source = chunk.get('metadata', {}).get('source', 'N/A')
                    content = chunk.get('content', '')
                    
                    # Chỉ lấy những câu có liên quan đến query
                    query_keywords = ['phí', 'tiền', 'lệ phí', 'miễn', 'cost', 'fee']
                    sentences = content.split('.')
                    relevant_sentences = []
                    
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in query_keywords):
                            relevant_sentences.append(sentence.strip())
                    
                    if relevant_sentences:
                        relevant_content = '. '.join(relevant_sentences[:2])  # Top 2 relevant sentences only
                        context_parts.append(f"📄 Nguồn: {source}\n{relevant_content}")
                    else:
                        # Fallback: truncated content
                        truncated_content = content[:400] + "..." if len(content) > 400 else content
                        context_parts.append(f"📄 Nguồn: {source}\n{truncated_content}")
                
                context_text = "\n\n".join(context_parts)
                logger.info(f"Conservative context: {len(context_text)} chars, focused on relevant sentences only")
            
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
            
            # Keep only last 10 queries in session
            if len(session.query_history) > 10:
                session.query_history = session.query_history[-10:]
                
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
            recent_queries = session.query_history[-3:]  # Last 3 queries
            conversation_context = "Lịch sử hội thoại gần đây:\n" + "\n".join([
                f"Q: {item['query']}\nA: {item['answer'][:200]}..." 
                for item in recent_queries
            ]) + "\n\n"
            
        # Build intelligent system prompt - tùy thuộc vào độ dài context
        context_length = len(context)
        if context_length < 1000:
            # Conservative Strategy: Context ngắn, yêu cầu LLM tập trung cao độ
            system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam.

🎯 NHIỆM VỤ: Trả lời CHÍNH XÁC dựa trên thông tin ngắn gọn được cung cấp.

QUY TẮC:
1. CHỈ dùng thông tin CÓ TRONG tài liệu
2. Trả lời NGẮN GỌN (1-2 câu) 
3. Tập trung vào từ khóa chính trong câu hỏi
4. Nếu có thông tin về "phí" hoặc "miễn phí" - nêu rõ ngay

Trả lời trực tiếp, không dài dòng."""
        else:
            # Full Document Strategy: Context dài, cần hướng dẫn chi tiết hơn
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
        
        logger.info(f"📝 Using {'CONSERVATIVE' if context_length < 1000 else 'FULL'} system prompt for context length: {context_length}")
        
        # Build enhanced context với conversation history
        enhanced_context = conversation_context + context

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
        """Tạo clarification thông minh dựa trên routing result"""
        try:
            self.metrics["ambiguous_detected"] += 1
            
            # Tạo clarification với suggestions từ routing result
            best_match = routing_result.get('matched_example', '')
            source_procedure = routing_result.get('source_procedure', '')
            confidence = routing_result.get('confidence', 0.0)
            
            # Tạo clarification message với context
            clarification_msg = f"Tôi nghĩ bạn có thể muốn hỏi về '{source_procedure}' (độ tin cậy: {confidence:.3f}). Đúng không?"
            
            # Tạo options dựa trên best match và các alternatives
            options = []
            
            # Option 1: Best match từ router
            if source_procedure:
                options.append({
                    'id': '1',
                    'title': f"Đúng - về {source_procedure}",
                    'description': f"Câu hỏi tương tự: {best_match[:100]}..." if best_match else "Đúng, tôi muốn hỏi về thủ tục này",
                    'collection': routing_result.get('target_collection'),
                    'procedure': source_procedure
                })
            
            # Option 2: Generic alternatives
            options.append({
                'id': '2', 
                'title': "Không, tôi muốn hỏi về thủ tục khác",
                'description': "Hãy cho tôi biết rõ hơn thủ tục nào bạn quan tâm",
                'collection': None,
                'procedure': None
            })
            
            if not options:
                # Fallback nếu không có suggestions - return proper structure
                return {
                    "type": "clarification_needed",
                    "status": "smart_clarification",
                    "confidence": routing_result.get('confidence', 0.0),
                    "clarification": {
                        "message": "Xin lỗi, tôi không rõ ý định của câu hỏi. Bạn có thể diễn đạt rõ hơn không?",
                        "options": [],
                        "suggestions": [
                            "Bạn có thể nói rõ hơn về thủ tục nào bạn muốn thực hiện?",
                            "Ví dụ: đăng ký khai sinh, kết hôn, chứng thực, hay thủ tục khác?"
                        ]
                    },
                    "session_id": session_id,
                    "processing_time": time.time() - start_time,
                    "strategy": "generic_clarification"
                }
            
            logger.info(f"Generated smart clarification with {len(options)} options")
            
            return {
                "type": "clarification_needed",
                "status": "smart_clarification", 
                "confidence": routing_result.get('confidence', 0.0),
                "clarification": {
                    "message": clarification_msg,
                    "options": options
                },
                "matched_example": routing_result.get('matched_example'),
                "source_procedure": routing_result.get('source_procedure'),
                "session_id": session_id,
                "processing_time": time.time() - start_time,
                "strategy": "smart_suggestion"
            }
            
        except Exception as e:
            logger.error(f"Error generating smart clarification: {e}")
            return {
                "type": "clarification_needed", 
                "status": "error",
                "clarification": "Xin lỗi, có lỗi khi xử lý câu hỏi. Bạn có thể thử lại không?",
                "session_id": session_id,
                "processing_time": time.time() - start_time
            }
    
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
