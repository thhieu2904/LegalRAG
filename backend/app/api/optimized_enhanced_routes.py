"""
API Routes cho Optimized Enhanced RAG Service
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Global service reference (sẽ được set từ main.py)
optimized_enhanced_rag_service = None

router = APIRouter(prefix="/api/v2", tags=["Optimized Enhanced RAG"])

# Request models
class OptimizedQueryRequest(BaseModel):
    query: str = Field(..., description="Câu hỏi của người dùng")
    session_id: Optional[str] = Field(None, description="ID session chat (tùy chọn)")
    max_context_length: int = Field(3000, description="Độ dài context tối đa")
    use_ambiguous_detection: bool = Field(True, description="Có phát hiện câu hỏi mơ hồ không")
    use_full_document_expansion: bool = Field(True, description="Có mở rộng toàn bộ document không")

class ClarificationRequest(BaseModel):
    session_id: str = Field(..., description="ID session chat")
    selected_option: str = Field(..., description="Lựa chọn người dùng")
    original_query: str = Field(..., description="Câu hỏi gốc")

class SessionCreateRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata cho session")

# Response models
class QueryResponse(BaseModel):
    type: str
    session_id: str
    processing_time: float
    answer: Optional[str] = None
    clarification: Optional[Dict[str, Any]] = None
    generated_questions: Optional[List[str]] = None
    context_info: Optional[Dict[str, Any]] = None
    routing_info: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    created_at: float
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    total_collections: Optional[int] = None
    total_documents: Optional[int] = None
    llm_loaded: Optional[bool] = None
    reranker_loaded: Optional[bool] = None
    embedding_device: Optional[str] = None
    llm_device: Optional[str] = None
    reranker_device: Optional[str] = None
    active_sessions: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    ambiguous_patterns: Optional[int] = None
    context_expansion: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def get_service():
    """Dependency để lấy service"""
    if optimized_enhanced_rag_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return optimized_enhanced_rag_service

@router.post("/optimized-query", response_model=QueryResponse)
async def optimized_query(
    request: OptimizedQueryRequest,
    service = Depends(get_service)
):
    """
    Enhanced query với tối ưu VRAM và xử lý câu hỏi mơ hồ
    
    Features:
    - Phát hiện câu hỏi mơ hồ tự động
    - Tối ưu VRAM (Embedding CPU, LLM/Reranker GPU)
    - Context expansion với nucleus strategy
    - Session management
    """
    try:
        result = service.enhanced_query(
            query=request.query,
            session_id=request.session_id,
            max_context_length=request.max_context_length,
            use_ambiguous_detection=request.use_ambiguous_detection,
            use_full_document_expansion=request.use_full_document_expansion
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in optimized query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clarify", response_model=QueryResponse)
async def handle_clarification(
    request: ClarificationRequest,
    service = Depends(get_service)
):
    """
    Xử lý phản hồi clarification từ người dùng
    """
    try:
        result = service.handle_clarification(
            session_id=request.session_id,
            selected_option=request.selected_option,
            original_query=request.original_query
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error handling clarification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/create", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    service = Depends(get_service)
):
    """Tạo session chat mới"""
    try:
        session_id = service.create_session(metadata=request.metadata)
        session = service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")
            
        return SessionResponse(
            session_id=session_id,
            created_at=session.created_at,
            metadata=session.metadata
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    service = Depends(get_service)
):
    """Lấy thông tin session"""
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "last_accessed": session.last_accessed,
        "query_count": len(session.query_history),
        "recent_queries": [item["query"][:50] + "..." for item in session.query_history[-3:]],
        "metadata": session.metadata
    }

@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    service = Depends(get_service)
):
    """Xóa session"""
    if session_id not in service.chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    del service.chat_sessions[session_id]
    
    return {"message": f"Session {session_id} deleted successfully"}

@router.get("/health", response_model=HealthResponse)
async def get_health_status(service = Depends(get_service)):
    """Trạng thái health của optimized service"""
    try:
        health_data = service.get_health_status()
        return HealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return HealthResponse(status="error", error=str(e))

@router.post("/cleanup-sessions")
async def cleanup_old_sessions(
    max_age_hours: int = 24,
    service = Depends(get_service)
):
    """Dọn dẹp sessions cũ"""
    try:
        cleaned_count = service.cleanup_old_sessions(max_age_hours)
        return {
            "message": f"Cleaned up {cleaned_count} old sessions",
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ambiguous-patterns")
async def get_ambiguous_patterns(service = Depends(get_service)):
    """Lấy danh sách patterns câu hỏi mơ hồ"""
    try:
        patterns = service.ambiguous_service.ambiguous_patterns
        templates = service.ambiguous_service.clarification_templates
        stats = service.ambiguous_service.get_stats()
        
        return {
            "patterns": patterns,
            "templates": templates,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting ambiguous patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ambiguous-patterns")
async def add_ambiguous_pattern(
    category: str,
    examples: List[str],
    threshold: float = 0.7,
    service = Depends(get_service)
):
    """Thêm pattern mới cho câu hỏi mơ hồ"""
    try:
        service.ambiguous_service.add_ambiguous_pattern(
            category=category,
            examples=examples,
            threshold=threshold
        )
        
        return {
            "message": f"Added new ambiguous pattern: {category}",
            "category": category,
            "examples_count": len(examples),
            "threshold": threshold
        }
        
    except Exception as e:
        logger.error(f"Error adding ambiguous pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context-expansion/stats")
async def get_context_expansion_stats(service = Depends(get_service)):
    """Thống kê context expansion service"""
    try:
        stats = service.context_expansion_service.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting context expansion stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/context-expansion/rebuild-cache")
async def rebuild_metadata_cache(service = Depends(get_service)):
    """Rebuild metadata cache (sau khi có documents mới)"""
    try:
        service.context_expansion_service.rebuild_metadata_cache()
        stats = service.context_expansion_service.get_stats()
        
        return {
            "message": "Metadata cache rebuilt successfully",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error rebuilding metadata cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
