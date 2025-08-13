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
            
            # Step 1: Enhanced Smart Query Routing với Ambiguous Detection  
            if use_ambiguous_detection:
                is_ambiguous, routing_result = self.ambiguous_service.is_ambiguous(query)
                
                if is_ambiguous:
                    self.metrics["ambiguous_detected"] += 1
                    logger.info(f"Ambiguous query detected: {routing_result['status']} (confidence: {routing_result['confidence']:.2f})")
                    
                    clarification_response = self.ambiguous_service.generate_clarification_response(routing_result)
                    
                    return {
                        "type": "clarification_needed",
                        "status": routing_result['status'],
                        "confidence": routing_result['confidence'],
                        "clarification": clarification_response,
                        "matched_example": routing_result.get('matched_example'),
                        "source_procedure": routing_result.get('source_procedure'),
                        "session_id": session_id,
                        "processing_time": time.time() - start_time
                    }
                else:
                    # Query không mơ hồ - có target collection rồi
                    target_collection = routing_result['target_collection']
                    best_collections = [target_collection] if target_collection else [settings.chroma_collection_name]
                    logger.info(f"Smart routed to collection: {target_collection} (confidence: {routing_result['confidence']:.2f})")
            else:
                # Fallback: sử dụng default collection
                best_collections = [settings.chroma_collection_name]
            
            # Step 2: Focused Search trong target collection
            broad_search_results = []
            for collection_name in best_collections[:2]:  # Limit to top 2 collections
                try:
                    results = self.vectordb_service.search_in_collection(
                        collection_name=collection_name,
                        query=query,
                        top_k=settings.broad_search_k,
                        similarity_threshold=settings.similarity_threshold
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
                
                # ✅ VALIDATION: Kiểm tra rerank score để tránh chọn tài liệu không liên quan
                if nucleus_chunks and len(nucleus_chunks) > 0:
                    best_score = nucleus_chunks[0].get('rerank_score', 0)
                    logger.info(f"Best rerank score: {best_score:.4f}")
                    
                    # Nếu điểm quá thấp (< 0.1), cảnh báo nhưng vẫn tiếp tục
                    if best_score < 0.1:
                        logger.warning(f"⚠️  LOW RERANK SCORE ({best_score:.4f}) - Tài liệu có thể không liên quan!")
                        logger.warning("💡 Suggestion: Kiểm tra lại query hoặc database content")
                
                logger.info(f"Selected {len(nucleus_chunks)} nucleus chunk with highest rerank score")
            else:
                nucleus_chunks = broad_search_results[:1]  # Fallback: lấy chunk tốt nhất theo vector similarity
                
            # Step 5: Full Document Expansion - QUAN TRỌNG: Lấy toàn bộ document thay vì chỉ 1 chunk
            expanded_context = None
            if use_full_document_expansion:
                self.metrics["context_expansions"] += 1
                expanded_context = self.context_expansion_service.expand_context_with_nucleus(
                    nucleus_chunks=nucleus_chunks,
                    max_context_length=max_context_length,
                    include_full_document=True  # KEY: Lấy toàn bộ document từ file JSON gốc
                )
                
                context_text = self._build_context_from_expanded(expanded_context)
                
                logger.info(f"Context expanded: {expanded_context['total_length']} chars from {len(expanded_context.get('source_documents', []))} documents")
            else:
                # Fallback: simple concatenation
                context_text = "\n\n".join([
                    f"Tài liệu: {chunk.get('metadata', {}).get('source', 'N/A')}\n{chunk['content']}"
                    for chunk in nucleus_chunks
                ])
            
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
            
        # Build system prompt
        system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam. Hãy trả lời câu hỏi dựa trên thông tin được cung cấp.

Hướng dẫn trả lời:
1. Trả lời chính xác dựa trên thông tin trong tài liệu
2. Nếu không tìm thấy thông tin, hãy nói rõ và cung cấp trích dẫn để hỗ trợ cho câu trả lời của bạn
3. Sử dụng ngữ điệu thân thiện và chuyên nghiệp khi giao tiếp với người dùng khác về các vấn đề pháp lý liên quan đến Việt Nam"""
        
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
