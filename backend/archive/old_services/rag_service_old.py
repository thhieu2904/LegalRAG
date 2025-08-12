import logging
import time
from typing import Dict, List, Any, Optional
from .json_document_processor import JSONDocumentProcessor
from .vectordb_service import VectorDBService
from .llm_service import LLMService
from .query_router import QueryRouter
from .reranker_service import RerankerService
from .context_expansion_service import ContextExpansionService
from ..core.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    """Service tổng hợp RAG với hỗ trợ multi-collection và intelligent routing"""
    
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
        
        # Validate VectorDB embedding model loaded
        if not self.vectordb_service.embedding_model:
            raise RuntimeError("VectorDB service failed to load embedding model - cannot initialize RAG service")
        
        # Khởi tạo Query Router với embedding model từ vectordb
        self.query_router = QueryRouter(embedding_model=self.vectordb_service.embedding_model)
        
        # Khởi tạo Reranker Service
        if settings.use_reranker:
            try:
                self.reranker_service = RerankerService()
                logger.info("Advanced Reranker service (AITeamVN/Vietnamese_Reranker) initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize reranker service: {e}")
                self.reranker_service = None
        else:
            logger.info("Reranker disabled via config")
            self.reranker_service = None
        
        # Khởi tạo Context Expansion Service
        self.context_expansion_service = ContextExpansionService(vectordb_service)
    
    def build_index(self, force_rebuild: bool = False, chunk_size: int = 800, overlap: int = 200) -> Dict[str, Any]:
        """Xây dựng index cho tài liệu với multi-collection support"""
        start_time = time.time()
        
        try:
            # Xử lý tài liệu và nhóm theo collection với content-aware chunking
            logger.info(f"Processing documents from {self.documents_dir} with content-aware chunking")
            collections_data = self.document_processor.process_directory(self.documents_dir)
            
            if not collections_data:
                return {
                    'status': 'error',
                    'collections_processed': 0,
                    'processing_time': time.time() - start_time,
                    'message': 'No documents found to process'
                }
            
            # Xử lý từng collection
            total_documents = 0
            total_chunks = 0
            processed_collections = {}
            
            for collection_name, documents in collections_data.items():
                # Clear collection nếu force rebuild
                if force_rebuild:
                    logger.info(f"Force rebuild: clearing existing collection {collection_name}")
                    self.vectordb_service.clear_collection(collection_name)
                
                # Kiểm tra nếu collection đã tồn tại
                if not force_rebuild and self.vectordb_service.collection_exists(collection_name):
                    stats = self.vectordb_service.get_collection_stats(collection_name)
                    logger.info(f"Collection {collection_name} already exists with {stats['document_count']} chunks")
                    processed_collections[collection_name] = {
                        'status': 'existed',
                        'documents': stats['document_count'],
                        'chunks': stats['total_chunks']
                    }
                    continue
                
                # Lấy metadata cho collection
                collection_metadata = None
                if documents:
                    collection_metadata = documents[0].get('collection_metadata', {})
                    collection_metadata = {
                        'description': collection_metadata.get('description', f'Collection for {collection_name}'),
                        'keywords': collection_metadata.get('keywords', '')  # Đổi từ [] thành ''
                    }
                
                # Thêm documents vào collection
                chunks_added = self.vectordb_service.add_documents_to_collection(
                    collection_name, documents, collection_metadata
                )
                
                processed_collections[collection_name] = {
                    'status': 'created',
                    'documents': len(documents),
                    'chunks': chunks_added
                }
                
                total_documents += len(documents)
                total_chunks += chunks_added
                
                logger.info(f"Collection {collection_name}: {len(documents)} documents, {chunks_added} chunks")
            
            processing_time = time.time() - start_time
            
            logger.info(f"Multi-collection index built successfully: "
                       f"{len(collections_data)} collections, {total_documents} documents, "
                       f"{total_chunks} chunks in {processing_time:.2f}s")
            
            return {
                'status': 'success',
                'collections_processed': len(collections_data),
                'total_documents': total_documents,
                'total_chunks': total_chunks,
                'processing_time': processing_time,
                'collections_detail': processed_collections,
                'message': f'Successfully processed {len(collections_data)} collections with {total_documents} documents into {total_chunks} chunks'
            }
            
        except Exception as e:
            logger.error(f"Error building multi-collection index: {e}")
            return {
                'status': 'error',
                'collections_processed': 0,
                'processing_time': time.time() - start_time,
                'message': f'Error building index: {str(e)}'
            }
    
    def query(
        self,
        question: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        broad_search_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        use_routing: Optional[bool] = None,
        context_expansion_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trả lời câu hỏi sử dụng RAG với quy trình mới:
        1. Tìm kiếm rộng
        2. Rerank để tìm hạt nhân
        3. Mở rộng ngữ cảnh 
        4. Tổng hợp câu trả lời
        """
        # Sử dụng config nếu không được cung cấp
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        broad_search_k = broad_search_k or settings.broad_search_k
        similarity_threshold = similarity_threshold or settings.similarity_threshold
        use_routing = use_routing if use_routing is not None else settings.use_routing
        context_expansion_size = context_expansion_size or settings.context_expansion_size
        start_time = time.time()
        
        try:
            logger.info(f"Starting new RAG process for query: {question[:100]}...")
            
            # BƯỚC 1: ROUTING - Xác định collection phù hợp
            routing_info = {}
            broad_search_docs = []
            
            if use_routing:
                logger.info("Step 1: Query routing...")
                routing_explanation = self.query_router.explain_routing(question)
                routing_info = routing_explanation
                
                recommended_collections = [item[0] for item in routing_explanation['recommended_collections'][:2]]
                
                if recommended_collections:
                    logger.info(f"Searching in collections: {recommended_collections}")
                    
                    # Tìm kiếm rộng trong các collection được recommend
                    for collection_name in recommended_collections:
                        collection_docs = self.vectordb_service.search_in_collection(
                            collection_name=collection_name,
                            query=question,
                            top_k=broad_search_k // len(recommended_collections) + 5,
                            similarity_threshold=similarity_threshold
                        )
                        broad_search_docs.extend(collection_docs)
                    
                    # Sort theo similarity nhưng giữ số lượng lớn
                    broad_search_docs.sort(key=lambda x: x['similarity'], reverse=True)
                    broad_search_docs = broad_search_docs[:broad_search_k]
                else:
                    logger.warning("No suitable collection found, searching across all collections")
                    broad_search_docs = self.vectordb_service.search_across_collections(
                        query=question,
                        top_k=broad_search_k,
                        similarity_threshold=similarity_threshold
                    )
            else:
                # Fallback: tìm kiếm rộng trên tất cả collections
                logger.info("Step 1: Broad search across all collections...")
                broad_search_docs = self.vectordb_service.search_across_collections(
                    query=question,
                    top_k=broad_search_k,
                    similarity_threshold=similarity_threshold
                )
            
            if not broad_search_docs:
                logger.warning("No relevant documents found in broad search")
                return {
                    'answer': "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong cơ sở dữ liệu pháp luật hiện tại.",
                    'sources': [],
                    'source_files': [],
                    'collections_searched': list(routing_info.get('recommended_collections', [])) if routing_info else ['all'],
                    'routing_info': routing_info,
                    'processing_time': time.time() - start_time,
                    'documents_found': 0,
                    'process_info': {'step': 'broad_search_failed', 'broad_docs_count': 0}
                }
            
            logger.info(f"Step 1 completed: Found {len(broad_search_docs)} documents in broad search")
            
            # BƯỚC 2: RERANKING - Tìm "Hạt nhân" chính xác nhất
            logger.info("Step 2: Reranking to find core document...")
            
            if self.reranker_service and self.reranker_service.is_loaded():
                # Sử dụng reranker để tìm document tốt nhất
                core_document = self.reranker_service.get_best_document(question, broad_search_docs)
                
                if not core_document:
                    logger.error("Reranker failed to find core document")
                    return {
                        'answer': "Có lỗi xảy ra trong quá trình xử lý câu hỏi.",
                        'sources': [],
                        'source_files': [],
                        'processing_time': time.time() - start_time,
                        'documents_found': len(broad_search_docs),
                        'process_info': {'step': 'reranking_failed', 'broad_docs_count': len(broad_search_docs)}
                    }
                
                logger.info(f"Step 2 completed: Core document selected with rerank_score={core_document.get('rerank_score', 'N/A'):.4f}")
            else:
                # Fallback: chọn document có similarity cao nhất
                logger.warning("Reranker not available, using similarity-based selection")
                core_document = broad_search_docs[0]
                core_document['rerank_score'] = core_document.get('similarity', 0)
            
            # BƯỚC 3: CONTEXT EXPANSION - Mở rộng ngữ cảnh xung quanh hạt nhân
            logger.info("Step 3: Expanding context around core document...")
            
            expanded_chunks = self.context_expansion_service.expand_context(
                core_document=core_document,
                expansion_size=context_expansion_size
            )
            
            logger.info(f"Step 3 completed: Context expanded to {len(expanded_chunks)} chunks")
            
            # BƯỚC 4: CONTEXT INTEGRATION - Tạo ngữ cảnh mạch lạc
            logger.info("Step 4: Creating coherent context...")
            
            coherent_context = self.context_expansion_service.create_coherent_context(expanded_chunks)
            
            if not coherent_context:
                logger.error("Failed to create coherent context")
                return {
                    'answer': "Có lỗi xảy ra trong quá trình tạo ngữ cảnh.",
                    'sources': [],
                    'source_files': [],
                    'processing_time': time.time() - start_time,
                    'documents_found': len(broad_search_docs),
                    'process_info': {'step': 'context_creation_failed', 'expanded_chunks_count': len(expanded_chunks)}
                }
            
            logger.info(f"Step 4 completed: Coherent context created ({len(coherent_context)} characters)")
            
            # BƯỚC 5: LLM GENERATION - Tạo câu trả lời
            logger.info("Step 5: Generating response using LLM...")
            
            # Dùng system prompt mặc định với context đơn giản
            llm_result = self.llm_service.generate_response(
                user_query=question,  # Câu hỏi đơn giản
                context=coherent_context,  # Context không có instruction
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Thu thập thông tin để trả về
            source_info = core_document.get('source', {})
            collections_used = {core_document.get('collection', 'unknown')}
            source_files = {source_info.get('document_title', source_info.get('file_path', 'unknown'))}
            
            # Tạo source information từ expanded chunks
            sources = []
            for chunk in expanded_chunks:
                chunk_source = chunk.get('source', {})
                sources.append({
                    'content': chunk['content'][:300] + "..." if len(chunk['content']) > 300 else chunk['content'],
                    'document_title': chunk_source.get('document_title', ''),
                    'document_code': chunk_source.get('document_code', ''),
                    'section_title': chunk_source.get('section_title', ''),
                    'source_reference': chunk_source.get('source_reference', ''),
                    'file_path': chunk_source.get('file_path', ''),
                    'issuing_authority': chunk_source.get('issuing_authority', ''),
                    'executing_agency': chunk_source.get('executing_agency', ''),
                    'effective_date': chunk_source.get('effective_date', ''),
                    'collection': chunk.get('collection', 'unknown'),
                    'similarity': chunk.get('similarity', 0.0),
                    'rerank_score': chunk.get('rerank_score', core_document.get('rerank_score', 0.0)),
                    'chunk_index': chunk.get('metadata', {}).get('chunk_index', 0),
                    'is_core': chunk == core_document
                })
            
            processing_time = time.time() - start_time
            
            # Tạo source reference
            source_reference = f"\n\n📚 **Nguồn tham khảo:** {', '.join(sorted(source_files))}"
            enhanced_answer = llm_result['response'] + source_reference
            
            result = {
                'answer': enhanced_answer,
                'sources': sources,
                'source_files': sorted(list(source_files)),
                'collections_used': sorted(list(collections_used)),
                'routing_info': routing_info,
                'processing_time': processing_time,
                'llm_processing_time': llm_result['processing_time'],
                'tokens_used': llm_result['total_tokens'],
                'documents_found': len(broad_search_docs),
                'process_info': {
                    'step': 'completed',
                    'broad_docs_count': len(broad_search_docs),
                    'core_document_rerank_score': core_document.get('rerank_score', 0),
                    'expanded_chunks_count': len(expanded_chunks),
                    'coherent_context_length': len(coherent_context),
                    'reranker_used': self.reranker_service is not None and self.reranker_service.is_loaded()
                }
            }
            
            logger.info(f"Step 5 completed: Query processed successfully in {processing_time:.2f}s")
            logger.info(f"Process summary: {len(broad_search_docs)} broad → core rerank → {len(expanded_chunks)} expanded → coherent context")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Kiểm tra trạng thái health của RAG service"""
        try:
            vectordb_healthy = hasattr(self.vectordb_service, 'embedding_model') and self.vectordb_service.embedding_model is not None
            llm_loaded = self.llm_service.is_loaded()
            reranker_loaded = self.reranker_service is not None and self.reranker_service.is_loaded()
            
            # Lấy thông tin về tất cả collections
            collections_info = self.vectordb_service.list_collections()
            total_documents = sum(col['document_count'] for col in collections_info)
            
            model_info = self.llm_service.get_model_info()
            reranker_info = self.reranker_service.get_model_info() if self.reranker_service else {'model_name': 'Not loaded', 'is_loaded': False}
            
            return {
                'status': 'healthy' if (vectordb_healthy and llm_loaded) else 'unhealthy',
                'vectordb_status': vectordb_healthy,
                'model_loaded': llm_loaded,
                'reranker_loaded': reranker_loaded,
                'total_collections': len(collections_info),
                'total_documents': total_documents,
                'collections': collections_info,
                'embedding_model': self.vectordb_service.embedding_model_name,
                'model_info': model_info,
                'reranker_info': reranker_info,
                'query_router_available': hasattr(self, 'query_router') and self.query_router is not None,
                'context_expansion_available': hasattr(self, 'context_expansion_service') and self.context_expansion_service is not None
            }
            
        except Exception as e:
            logger.error(f"Error checking health status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'vectordb_status': False,
                'model_loaded': False,
                'reranker_loaded': False,
                'total_collections': 0,
                'total_documents': 0
            }
