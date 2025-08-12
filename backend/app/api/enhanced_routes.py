"""
Enhanced API Routes với support cho Query Preprocessing và Session Management
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    QueryRequest, QueryResponse, HealthResponse, 
    IndexingRequest, IndexingResponse,
    # New schemas for enhanced features
    EnhancedQueryRequest, EnhancedQueryResponse,
    ClarificationRequest, ClarificationResponse,
    SessionInfoResponse
)
from app.services.enhanced_rag_service_v2 import EnhancedRAGService
from typing import Optional, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Router 
router = APIRouter()

# Global Enhanced RAG service instance
enhanced_rag_service: Optional[EnhancedRAGService] = None

def get_enhanced_rag_service():
    """Dependency để lấy Enhanced RAG service"""
    if enhanced_rag_service is None:
        raise HTTPException(status_code=500, detail="Enhanced RAG service not initialized")
    return enhanced_rag_service

# =====================================================================
# ENHANCED QUERY ENDPOINTS
# =====================================================================

@router.post("/enhanced-query", response_model=EnhancedQueryResponse)
async def enhanced_query_documents(
    request: EnhancedQueryRequest,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """
    Enhanced Query endpoint với:
    - Query preprocessing (clarification + context synthesis) 
    - Session management
    - Hybrid retrieval strategy
    """
    try:
        result = rag.query_with_preprocessing(
            question=request.question,
            session_id=request.session_id,
            enable_clarification=request.enable_clarification,
            enable_context_synthesis=request.enable_context_synthesis,
            auto_clarify_threshold=request.clarification_threshold,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            target_context_length=request.target_context_length or 2500
        )
        
        return EnhancedQueryResponse(
            type=result['type'],
            answer=result.get('answer', ''),
            original_query=result.get('original_query', request.question),
            processed_query=result.get('processed_query'),
            clarification_questions=result.get('clarification_questions', []),
            sources=result.get('sources', []),
            source_files=result.get('source_files', []),
            context_strategy=result.get('context_strategy', {}),
            preprocessing_steps=result.get('preprocessing_steps', []),
            processing_time=result.get('total_processing_time', result.get('processing_time', 0)),
            session_id=result.get('session_id'),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing enhanced query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clarify", response_model=EnhancedQueryResponse)
async def provide_clarification(
    request: ClarificationRequest,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """
    Endpoint xử lý clarification responses từ user
    """
    try:
        result = rag.provide_clarification(
            session_id=request.session_id,
            original_question=request.original_question,
            clarification_responses=request.responses
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return EnhancedQueryResponse(
            type=result['type'],
            answer=result['answer'],
            original_query=result['original_query'],
            processed_query=result['clarified_query'],
            clarification_responses=result.get('clarification_responses', {}),
            sources=result['sources'],
            source_files=result['source_files'],
            context_strategy=result.get('context_strategy', {}),
            processing_time=result['processing_time'],
            session_id=result['session_id'],
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing clarification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# SESSION MANAGEMENT ENDPOINTS  
# =====================================================================

@router.post("/session/create")
async def create_chat_session(
    metadata: Optional[Dict[str, Any]] = None,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """Tạo session chat mới"""
    try:
        session_id = rag.create_chat_session(metadata=metadata)
        return {
            "session_id": session_id,
            "created_at": datetime.now(),
            "message": "Session created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: str,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """Lấy thông tin session"""
    try:
        result = rag.get_session_info(session_id)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionInfoResponse(
            session_id=result['session_id'],
            created_at=datetime.fromtimestamp(result['created_at']),
            last_accessed=datetime.fromtimestamp(result['last_accessed']),
            conversation_turns=result['conversation_history']['total_turns'],
            topics=result['conversation_history']['topics'],
            recent_queries=result['conversation_history']['recent_queries'],
            metadata=result['metadata']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def clear_session_history(
    session_id: str,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """Xóa lịch sử session"""
    try:
        success = rag.clear_session_history(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "message": "Session history cleared successfully",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# LEGACY ENDPOINTS (Backward Compatibility)
# =====================================================================

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """Legacy query endpoint với enhanced preprocessing (để có luồng đúng)"""
    try:
        # Sử dụng query_with_preprocessing thay vì enhanced_query
        # để đảm bảo luồng xử lý đúng: Preprocessing → Clarification → RAG
        result = rag.query_with_preprocessing(
            question=request.question,
            session_id=None,  # Legacy không có session
            enable_clarification=True,  # Bật clarification cho legacy
            enable_context_synthesis=False,  # Không có lịch sử cho legacy
            auto_clarify_threshold="medium",
            max_tokens=request.max_tokens or 1024,
            temperature=request.temperature or 0.2,
            target_context_length=2500
        )
        
        # Nếu cần clarification, trả về thông báo yêu cầu làm rõ
        if result.get('type') == 'clarification_request':
            clarification_message = (
                "Câu hỏi của bạn cần được làm rõ thêm:\\n" + 
                "\\n".join(f"• {q}" for q in result.get('clarification_questions', []))
            )
            return QueryResponse(
                answer=clarification_message,
                sources=[],
                source_files=[],
                processing_time=result.get('processing_time', 0),
                timestamp=datetime.now()
            )
        
        # Trả về answer bình thường
        return QueryResponse(
            answer=result.get('answer', ''),
            sources=result.get('sources', []),
            source_files=result.get('source_files', []),
            processing_time=result.get('total_processing_time', result.get('processing_time', 0)),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing legacy query with preprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/direct-query", response_model=QueryResponse)
async def direct_query_documents(
    request: QueryRequest,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """Direct RAG query endpoint - bỏ qua preprocessing (cho testing)"""
    try:
        result = rag.enhanced_query(
            question=request.question,
            max_tokens=request.max_tokens or 1024,
            temperature=request.temperature or 0.2,
            broad_search_k=request.top_k or 15,
            target_context_length=2500
        )
        
        return QueryResponse(
            answer=result['answer'],
            sources=result['sources'],
            source_files=result.get('source_files', []),
            processing_time=result['processing_time'],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing direct query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check(rag: EnhancedRAGService = Depends(get_enhanced_rag_service)):
    """Enhanced health check endpoint"""
    try:
        status = rag.get_health_status()
        
        return HealthResponse(
            status=status['status'],
            model_loaded=status.get('llm_loaded', False),
            vectordb_status=status.get('vectordb_healthy', False),
            total_collections=status.get('total_collections', 0),
            total_documents=status.get('total_documents', 0),
            embedding_model=status.get('embedding_model', ''),
            reranker_loaded=status.get('reranker_loaded', False),
            timestamp=datetime.now(),
            additional_info={
                'service_type': status.get('service_type', 'enhanced_rag'),
                'active_sessions': status.get('active_sessions', 0),
                'enhanced_features': {
                    'query_preprocessing': True,
                    'session_management': True,
                    'hybrid_retrieval': True,
                    'context_optimization': True
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error checking enhanced health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# INDEX MANAGEMENT ENDPOINTS
# =====================================================================

@router.post("/build-index", response_model=IndexingResponse)
async def build_index(
    request: IndexingRequest,
    rag: EnhancedRAGService = Depends(get_enhanced_rag_service)
):
    """Build index endpoint"""
    try:
        result = rag.build_index(
            force_rebuild=request.force_rebuild or False,
            chunk_size=request.chunk_size or 800,
            overlap=request.overlap or 200
        )
        
        return IndexingResponse(
            status=result['status'],
            collections_processed=result.get('collections_processed', 0),
            total_documents=result.get('total_documents', 0),
            total_chunks=result.get('total_chunks', 0),
            processing_time=result.get('processing_time', 0),
            message=result.get('message', ''),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=str(e))
