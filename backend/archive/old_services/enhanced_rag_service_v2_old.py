"""
Enhanced RAG Service - RAG Service cải tiến với:
1. Query Preprocessor cho xử lý thông minh
2. Enhanced Context Service với Hybrid Retrieval
3. Session management và conversation history
4. Tối ưu VRAM và performance
"""

import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .vectordb_service import VectorDBService
from .llm_service import LLMService
from .query_router import QueryRouter
from .reranker_service import RerankerService
from .query_preprocessor import QueryPreprocessor
from .enhanced_context_service import EnhancedContextService
from .json_document_processor import JSONDocumentProcessor
from ..core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ChatSession:
    """Lưu trữ thông tin session chat"""
    session_id: str
    created_at: float
    last_accessed: float
    preprocessor: QueryPreprocessor
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancedRAGService:
    """
    Enhanced RAG Service với tính năng tiền xử lý thông minh và context tối ưu
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
        self.document_processor = JSONDocumentProcessor()
        
        # Validate services
        if not self.vectordb_service.embedding_model:
            raise RuntimeError("VectorDB service failed to load embedding model")
        
        # Core components
        self.query_router = QueryRouter(embedding_model=self.vectordb_service.embedding_model)
        
        # Reranker service
        if settings.use_reranker:
            try:
                self.reranker_service = RerankerService()
                logger.info("Reranker service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize reranker service: {e}")
                self.reranker_service = None
        else:
            self.reranker_service = None
            
        # Enhanced services
        self.enhanced_context_service = EnhancedContextService(
            vectordb_service=self.vectordb_service,
            document_processor=self.document_processor
        )
        
        # Session management
        self.chat_sessions: Dict[str, ChatSession] = {}
        self.session_timeout = 3600  # 1 hour
        self.max_sessions = 100
        
        logger.info("Enhanced RAG Service initialized successfully")

    def create_chat_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Tạo session chat mới"""
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        # Limit number of sessions
        if len(self.chat_sessions) >= self.max_sessions:
            # Remove oldest session
            oldest_session_id = min(
                self.chat_sessions.keys(),
                key=lambda k: self.chat_sessions[k].last_accessed
            )
            del self.chat_sessions[oldest_session_id]
            logger.info(f"Removed oldest session: {oldest_session_id}")
        
        # Create preprocessor for this session
        preprocessor = QueryPreprocessor(llm_service=self.llm_service)
        
        session = ChatSession(
            session_id=session_id,
            created_at=current_time,
            last_accessed=current_time,
            preprocessor=preprocessor,
            metadata=metadata or {}
        )
        
        self.chat_sessions[session_id] = session
        logger.info(f"Created chat session: {session_id}")
        
        return session_id

    def _cleanup_expired_sessions(self):
        """Dọn dẹp các session hết hạn"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.chat_sessions.items():
            if current_time - session.last_accessed > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")

    def get_session_preprocessor(self, session_id: Optional[str] = None) -> QueryPreprocessor:
        """Lấy preprocessor của session hoặc tạo temporary"""
        if session_id and session_id in self.chat_sessions:
            session = self.chat_sessions[session_id]
            session.last_accessed = time.time()
            return session.preprocessor
        else:
            # Tạo temporary preprocessor cho single query
            return QueryPreprocessor(llm_service=self.llm_service)

    def query_with_preprocessing(
        self,
        question: str,
        session_id: Optional[str] = None,
        enable_clarification: bool = True,
        enable_context_synthesis: bool = True,
        auto_clarify_threshold: str = 'medium',
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query với tiền xử lý thông minh
        """
        start_time = time.time()
        
        try:
            # Lấy preprocessor
            preprocessor = self.get_session_preprocessor(session_id)
            
            # BƯỚC 1: Tiền xử lý câu hỏi
            logger.info("Step 1: Query preprocessing...")
            preprocessing_result = preprocessor.process_query(
                user_query=question,
                enable_clarification=enable_clarification,
                enable_context_synthesis=enable_context_synthesis,
                clarification_threshold=auto_clarify_threshold
            )
            
            # Nếu cần clarification, trả về câu hỏi làm rõ
            if preprocessing_result['needs_clarification']:
                return {
                    'type': 'clarification_request',
                    'original_query': question,
                    'clarification_questions': preprocessing_result['clarification_questions'],
                    'processing_steps': preprocessing_result['processing_steps'],
                    'processing_time': time.time() - start_time,
                    'session_id': session_id
                }
            
            # BƯỚC 2: Tiến hành RAG với processed query
            processed_query = preprocessing_result['processed_query']
            logger.info(f"Step 2: RAG processing with query: '{processed_query[:100]}...'")
            
            rag_result = self.enhanced_query(
                question=processed_query,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # BƯỚC 3: Lưu vào conversation history
            if session_id:
                topic_tags = preprocessor.extract_topic_tags(rag_result['answer'])
                preprocessor.add_conversation_turn(
                    user_query=question,
                    assistant_response=rag_result['answer'],
                    topic_tags=topic_tags
                )
            
            # Kết hợp kết quả
            result = rag_result.copy()
            result.update({
                'type': 'answer',
                'original_query': question,
                'processed_query': processed_query,
                'preprocessing_applied': preprocessing_result['context_synthesized'],
                'preprocessing_steps': preprocessing_result['processing_steps'],
                'session_id': session_id,
                'total_processing_time': time.time() - start_time
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in query with preprocessing: {e}")
            # Fallback to normal query
            return self.enhanced_query(question, max_tokens, temperature, **kwargs)

    def enhanced_query(
        self,
        question: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        broad_search_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        use_routing: Optional[bool] = None,
        target_context_length: int = 2500
    ) -> Dict[str, Any]:
        """
        Enhanced RAG query với hybrid retrieval strategy
        """
        # Sử dụng config values
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        broad_search_k = broad_search_k or settings.broad_search_k
        similarity_threshold = similarity_threshold or settings.similarity_threshold
        use_routing = use_routing if use_routing is not None else settings.use_routing
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting enhanced RAG query: {question[:100]}...")
            
            # BƯỚC 1: Routing và Broad Search
            routing_info = {}
            broad_search_docs = []
            
            if use_routing:
                routing_explanation = self.query_router.explain_routing(question)
                routing_info = routing_explanation
                recommended_collections = [item[0] for item in routing_explanation['recommended_collections'][:2]]
                
                if recommended_collections:
                    for collection_name in recommended_collections:
                        collection_docs = self.vectordb_service.search_in_collection(
                            collection_name=collection_name,
                            query=question,
                            top_k=broad_search_k // len(recommended_collections) + 3,
                            similarity_threshold=similarity_threshold
                        )
                        broad_search_docs.extend(collection_docs)
                    
                    broad_search_docs.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                    broad_search_docs = broad_search_docs[:broad_search_k]
                else:
                    broad_search_docs = self.vectordb_service.search_across_collections(
                        query=question, top_k=broad_search_k, similarity_threshold=similarity_threshold
                    )
            else:
                broad_search_docs = self.vectordb_service.search_across_collections(
                    query=question, top_k=broad_search_k, similarity_threshold=similarity_threshold
                )
            
            if not broad_search_docs:
                return {
                    'answer': "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu.",
                    'sources': [],
                    'source_files': [],
                    'processing_time': time.time() - start_time,
                    'strategy_used': 'no_results'
                }
            
            # BƯỚC 2: Reranking để tìm core documents
            if self.reranker_service and self.reranker_service.is_loaded():
                reranked_docs = self.reranker_service.rerank_documents(question, broad_search_docs, top_k=8)
                if reranked_docs:
                    broad_search_docs = reranked_docs
                    logger.info(f"Reranked to {len(broad_search_docs)} top documents")
            
            # BƯỚC 3: Enhanced Context Creation với Hybrid Strategy
            context_result = self.enhanced_context_service.optimize_context_for_query(
                chunks=broad_search_docs,
                query=question,
                target_length=target_context_length
            )
            
            coherent_context = context_result.get('context', '')
            context_metadata = context_result.get('metadata', {})
            
            if not coherent_context:
                return {
                    'answer': "Có lỗi xảy ra trong quá trình tạo ngữ cảnh.",
                    'sources': [],
                    'source_files': [],
                    'processing_time': time.time() - start_time,
                    'strategy_used': 'context_creation_failed'
                }
            
            # BƯỚC 4: LLM Generation
            logger.info("Generating response with enhanced context...")
            llm_result = self.llm_service.generate_response(
                user_query=question,
                context=coherent_context,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # BƯỚC 5: Tạo response metadata
            source_files = set()
            sources = []
            
            for chunk in broad_search_docs[:context_metadata.get('chunks_included', 5)]:
                source_info = chunk.get('source', {})
                file_name = source_info.get('document_title', source_info.get('file_path', 'unknown'))
                source_files.add(file_name)
                
                sources.append({
                    'content': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'],
                    'document_title': source_info.get('document_title', ''),
                    'similarity': chunk.get('similarity', 0.0),
                    'rerank_score': chunk.get('rerank_score', 0.0),
                    'collection': chunk.get('collection', 'unknown'),
                    'file_path': source_info.get('file_path', ''),
                })
            
            processing_time = time.time() - start_time
            
            # Enhanced answer với source reference
            source_reference = f"\n\n📚 **Nguồn:** {', '.join(sorted(source_files))}"
            enhanced_answer = llm_result['response'] + source_reference
            
            return {
                'answer': enhanced_answer,
                'sources': sources,
                'source_files': sorted(list(source_files)),
                'routing_info': routing_info,
                'context_strategy': context_metadata,
                'processing_time': processing_time,
                'llm_processing_time': llm_result['processing_time'],
                'tokens_used': llm_result['total_tokens'],
                'documents_found': len(broad_search_docs),
                'strategy_used': 'enhanced_hybrid'
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced query: {e}")
            raise

    def provide_clarification(
        self,
        session_id: str,
        original_question: str,
        clarification_responses: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Xử lý câu trả lời làm rõ từ user và tiến hành RAG
        """
        try:
            if session_id not in self.chat_sessions:
                return {
                    'error': 'Session not found',
                    'message': 'Session không tồn tại hoặc đã hết hạn'
                }
            
            # Tạo clarified query từ responses
            clarified_parts = [original_question]
            for question, response in clarification_responses.items():
                if response.strip():
                    clarified_parts.append(f"{question}: {response}")
            
            clarified_query = ". ".join(clarified_parts)
            
            # Tiến hành RAG với clarified query
            result = self.enhanced_query(clarified_query)
            result.update({
                'type': 'clarified_answer',
                'original_query': original_question,
                'clarified_query': clarified_query,
                'clarification_responses': clarification_responses,
                'session_id': session_id
            })
            
            # Lưu vào conversation history
            preprocessor = self.get_session_preprocessor(session_id)
            topic_tags = preprocessor.extract_topic_tags(result['answer'])
            preprocessor.add_conversation_turn(
                user_query=original_question,
                assistant_response=result['answer'],
                topic_tags=topic_tags
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error providing clarification: {e}")
            return {
                'error': 'Processing error',
                'message': f'Lỗi xử lý: {str(e)}'
            }

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Lấy thông tin session"""
        if session_id not in self.chat_sessions:
            return {'error': 'Session not found'}
        
        session = self.chat_sessions[session_id]
        preprocessor = session.preprocessor
        history_summary = preprocessor.get_history_summary()
        
        return {
            'session_id': session_id,
            'created_at': session.created_at,
            'last_accessed': session.last_accessed,
            'conversation_history': history_summary,
            'metadata': session.metadata
        }

    def clear_session_history(self, session_id: str) -> bool:
        """Xóa lịch sử của session"""
        if session_id not in self.chat_sessions:
            return False
        
        session = self.chat_sessions[session_id]
        session.preprocessor.clear_history()
        logger.info(f"Cleared history for session: {session_id}")
        return True

    def build_index(self, force_rebuild: bool = False, **kwargs) -> Dict[str, Any]:
        """Delegate to original RAG service for index building"""
        # Import here to avoid circular dependency
        from .rag_service import RAGService
        
        temp_rag = RAGService(
            self.documents_dir, 
            self.vectordb_service, 
            self.llm_service
        )
        
        return temp_rag.build_index(force_rebuild=force_rebuild, **kwargs)

    def get_health_status(self) -> Dict[str, Any]:
        """Kiểm tra trạng thái health của Enhanced RAG service"""
        try:
            base_health = {
                'service_type': 'enhanced_rag',
                'vectordb_healthy': self.vectordb_service.embedding_model is not None,
                'llm_loaded': self.llm_service.is_loaded(),
                'reranker_loaded': self.reranker_service is not None and self.reranker_service.is_loaded(),
                'query_router_available': hasattr(self, 'query_router'),
                'enhanced_context_available': hasattr(self, 'enhanced_context_service'),
                'active_sessions': len(self.chat_sessions),
                'session_limit': self.max_sessions,
                'session_timeout': self.session_timeout
            }
            
            # Get collections info
            collections_info = self.vectordb_service.list_collections()
            total_documents = sum(col['document_count'] for col in collections_info)
            
            base_health.update({
                'total_collections': len(collections_info),
                'total_documents': total_documents,
                'collections': collections_info,
                'status': 'healthy' if (base_health['vectordb_healthy'] and base_health['llm_loaded']) else 'unhealthy'
            })
            
            return base_health
            
        except Exception as e:
            logger.error(f"Error checking enhanced health status: {e}")
            return {
                'service_type': 'enhanced_rag',
                'status': 'error',
                'error': str(e)
            }
