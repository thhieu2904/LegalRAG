"""
Session Management API Endpoints
===============================

Expose session statistics and management for admin dashboard
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ..services.rag_engine import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global rag_service instance - will be set by main.py  
rag_service: Optional["RAGService"] = None

@router.get("/sessions/stats")
async def get_session_stats():
    """
    Get session statistics for dashboard
    
    Returns:
        Session statistics including active sessions, daily count, etc.
    """
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        stats = rag_service.get_session_stats()
        
        logger.info(f"📊 Session stats request: {stats['total_active_sessions']} active, {stats['today_session_count']} today")
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting session stats: {e}")
        raise HTTPException(status_code=500, detail=f"Session stats error: {str(e)}")

@router.get("/sessions/list")
async def list_active_sessions():
    """
    List all active sessions with basic info
    
    Returns:
        List of active sessions with ID, created time, last accessed, query count
    """
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        sessions_data = []
        
        for session_id, session in rag_service.chat_sessions.items():
            sessions_data.append({
                "session_id": session_id,
                "created_at": session.created_at,
                "last_accessed": session.last_accessed,
                "query_count": len(session.query_history),
                "last_successful_collection": session.last_successful_collection,
                "metadata": session.metadata
            })
        
        # Sort by last accessed (most recent first)
        sessions_data.sort(key=lambda x: x['last_accessed'], reverse=True)
        
        logger.info(f"📋 Sessions list request: {len(sessions_data)} active sessions")
        
        return {
            "success": True,
            "data": sessions_data,
            "total": len(sessions_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Sessions list error: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """
    Get detailed information about a specific session
    
    Args:
        session_id: Session ID (e.g., "20250928-001")
        
    Returns:
        Detailed session information including query history
    """
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        session = rag_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Build detailed response
        session_detail = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_accessed": session.last_accessed,
            "query_count": len(session.query_history),
            "query_history": [
                {
                    "timestamp": q.get("timestamp", 0),
                    "query": q.get("query", "")[:100],  # Truncate for privacy
                    "collection": q.get("collection"),
                    "processing_time": q.get("processing_time", 0),
                    "confidence": q.get("confidence", 0)
                }
                for q in session.query_history[-10:]  # Last 10 queries only
            ],
            "last_successful_collection": session.last_successful_collection,
            "last_successful_confidence": session.last_successful_confidence,
            "consecutive_low_confidence_count": session.consecutive_low_confidence_count,
            "metadata": session.metadata
        }
        
        logger.info(f"🔍 Session detail request: {session_id} ({len(session.query_history)} queries)")
        
        return {
            "success": True,
            "data": session_detail
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session detail: {e}")
        raise HTTPException(status_code=500, detail=f"Session detail error: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session
    
    Args:
        session_id: Session ID to delete
        
    Returns:
        Success confirmation
    """
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        if session_id not in rag_service.chat_sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        del rag_service.chat_sessions[session_id]
        
        logger.info(f"🗑️ Deleted session: {session_id}")
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Session deletion error: {str(e)}")

@router.post("/sessions/cleanup")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """
    Clean up sessions older than specified hours
    
    Args:
        max_age_hours: Maximum age in hours (default 24)
        
    Returns:
        Cleanup results
    """
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        sessions_to_delete = []
        for session_id, session in rag_service.chat_sessions.items():
            if session.last_accessed < cutoff_time:
                sessions_to_delete.append(session_id)
        
        # Delete old sessions
        for session_id in sessions_to_delete:
            del rag_service.chat_sessions[session_id]
        
        logger.info(f"🧹 Cleaned up {len(sessions_to_delete)} old sessions (>{max_age_hours}h)")
        
        return {
            "success": True,
            "data": {
                "deleted_count": len(sessions_to_delete),
                "deleted_sessions": sessions_to_delete,
                "remaining_sessions": len(rag_service.chat_sessions)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error during session cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Session cleanup error: {str(e)}")