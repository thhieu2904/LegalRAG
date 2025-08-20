"""
API Routes for Optimized Enhanced RAG Service
Endpoints tốidef get_rag_service():
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_servicevới VRAM-optimized architecture
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from ..services.rag_engine import convert_numpy_types

# This will be set by main.py
rag_service = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["RAG Service"])

# Pydantic Models
class QueryRequest(BaseModel):
    """Request model cho query"""
    query: str = Field(..., min_length=1, description="Câu hỏi của người dùng")
    session_id: Optional[str] = Field(None, description="ID session chat (tùy chọn)")
    max_context_length: int = Field(8000, ge=500, le=12000, description="Độ dài context tối đa")  # INCREASED: 3000 → 8000
    use_ambiguous_detection: bool = Field(True, description="Có sử dụng phát hiện câu hỏi mơ hồ")
    use_full_document_expansion: bool = Field(True, description="Có mở rộng toàn bộ document")
    forced_collection: Optional[str] = Field(None, description="Force routing to specific collection (từ clarification)")  # 🔧 NEW

class ClarificationRequest(BaseModel):
    """Request model cho clarification response - FIXED STRUCTURE"""
    session_id: str = Field(..., description="Session ID")
    selected_option: Dict[str, Any] = Field(..., description="Full option object được chọn")  # 🔧 CHANGE: Dict thay vì str
    original_query: str = Field(..., description="Câu hỏi gốc")

class SessionCreateRequest(BaseModel):
    """Request model để tạo session"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata cho session")

class QueryResponse(BaseModel):
    """Response model cho query"""
    type: str = Field(..., description="Loại response: answer, clarification_needed, no_results, error")
    answer: Optional[str] = Field(None, description="Câu trả lời (nếu type=answer)")
    message: Optional[str] = Field(None, description="Thông báo (nếu type=no_results)")
    error: Optional[str] = Field(None, description="Lỗi (nếu type=error)")
    
    # Clarification fields
    category: Optional[str] = Field(None, description="Category câu hỏi mơ hồ")
    confidence: Optional[float] = Field(None, description="Confidence score")
    clarification: Optional[Dict[str, Any]] = Field(None, description="Template clarification")
    generated_questions: Optional[List[str]] = Field(None, description="Câu hỏi làm rõ được sinh")
    
    # Context info
    context_info: Optional[Dict[str, Any]] = Field(None, description="Thông tin về context")
    
    # Meta info
    session_id: str = Field(..., description="Session ID")
    processing_time: float = Field(..., description="Thời gian xử lý (seconds)")
    routing_info: Optional[Dict[str, Any]] = Field(None, description="Thông tin routing")
    session_cleared: Optional[bool] = Field(None, description="Session đã được clear hay chưa")  # 🔧 OLD: Manual input fix
    context_preserved: Optional[bool] = Field(None, description="Context có được preserve hay không")  # 🔧 NEW: Context preservation  
    preserved_collection: Optional[str] = Field(None, description="Collection được preserve")  # 🔧 NEW: Preserved collection info

# Dependency để kiểm tra service
def get_rag_service():
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_service

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    service = Depends(get_rag_service)
):
    """
    Enhanced query với tối ưu VRAM và ambiguous detection
    
    Features:
    - Phát hiện câu hỏi mơ hồ (CPU embedding)
    - Query routing thông minh
    - Context expansion với nucleus strategy
    - Session management
    - VRAM-optimized model placement
    """
    try:
        logger.info(f"Processing optimized query: {request.query[:50]}...")
        
        result = service.process_query(
            query=request.query,
            session_id=request.session_id,
            forced_collection=request.forced_collection  # 🔧 NEW: Pass forced collection
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in optimized query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clarify", response_model=QueryResponse)
async def handle_clarification(
    request: ClarificationRequest,
    service = Depends(get_rag_service)
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

@router.post("/session/create")
async def create_session(
    request: SessionCreateRequest,
    service = Depends(get_rag_service)
):
    """Tạo session chat mới"""
    try:
        session_id = service.create_session(metadata=request.metadata)
        
        return {
            "session_id": session_id,
            "message": "Session created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    service = Depends(get_rag_service)
):
    """Lấy thông tin session với context summary"""
    try:
        session = service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Lấy context summary
        context_summary = service.get_session_context_summary(session_id)
        
        # 🔧 FIX: Convert numpy types để tránh lỗi JSON serialization
        response_data = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_accessed": session.last_accessed,
            "query_count": len(session.query_history),
            "metadata": session.metadata,
            "context_summary": context_summary  # 🔥 NEW: Context summary for frontend
        }
        
        return convert_numpy_types(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/reset")
async def reset_session_context(
    session_id: str,
    service = Depends(get_rag_service)
):
    """Reset ngữ cảnh của session về trạng thái mặc định"""
    try:
        success = service.reset_session_context(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 🔧 FIX: Convert numpy types để tránh lỗi JSON serialization
        response_data = {
            "session_id": session_id,
            "message": "Session context reset successfully",
            "context_summary": service.get_session_context_summary(session_id)
        }
        
        return convert_numpy_types(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    service = Depends(get_rag_service)
):
    """Xóa session"""
    try:
        if session_id in service.chat_sessions:
            del service.chat_sessions[session_id]
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    service = Depends(get_rag_service)
):
    """
    Health check cho optimized service
    Trả về thông tin chi tiết về trạng thái hệ thống
    """
    try:
        health_status = service.get_health_status()
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/sessions/cleanup")
async def cleanup_old_sessions(
    max_age_hours: int = 24,
    service = Depends(get_rag_service)
):
    """Dọn dẹp sessions cũ"""
    try:
        cleaned_count = service.cleanup_old_sessions(max_age_hours)
        
        return {
            "message": f"Cleaned up {cleaned_count} old sessions",
            "cleaned_sessions": cleaned_count,
            "remaining_sessions": len(service.chat_sessions)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(
    service = Depends(get_rag_service)
):
    """Lấy metrics của hệ thống"""
    try:
        return {
            "performance_metrics": service.metrics,
            "active_sessions": len(service.chat_sessions),
            "ambiguous_patterns_count": len(service.ambiguous_service.ambiguous_patterns),
            "context_cache_size": len(service.context_expansion_service.document_metadata_cache)
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections/stats")
async def get_collections_stats(
    service = Depends(get_rag_service)
):
    """Thống kê collections"""
    try:
        collections = service.vectordb_service.list_collections()
        stats = []
        
        for collection_info in collections:
            collection_name = collection_info["name"]
            try:
                collection = service.vectordb_service.get_collection(collection_name)
                count = collection.count()
                stats.append({
                    "name": collection_name,
                    "document_count": count,
                    "metadata": collection_info.get("metadata", {})
                })
            except Exception as e:
                stats.append({
                    "name": collection_name,
                    "error": str(e)
                })
        
        return {
            "collections": stats,
            "total_collections": len(collections)
        }
        
    except Exception as e:
        logger.error(f"Error getting collections stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
