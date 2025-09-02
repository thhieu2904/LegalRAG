"""
🔥 Router CRUD API - ESSENTIAL READ-ONLY ENDPOINTS

❌ CRUD operations (CREATE/UPDATE/DELETE) chưa được implement
💡 Chỉ có READ operations để support clarification flow
🎯 Dự định tương lai: Thêm CRUD để quản lý questions.json và document.json

Chức năng hiện tại:
- GET /router/collections: Lấy danh sách collections
- GET /router/collections/{name}/questions: Lấy questions cho clarification
- GET /router/health: Health check

Tính năng sẽ thêm trong tương lai:
- POST /router/collections/{name}/questions: Thêm question mới
- PUT /router/collections/{name}/questions/{id}: Sửa question
- DELETE /router/collections/{name}/questions/{id}: Xóa question
- POST/PUT cho document metadata management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from ..services.router import QueryRouter
from ..core.config import settings

# Setup router
router = APIRouter(prefix="/router", tags=["Router Essential"])

# Global router instance
_router_instance = None
_embedding_model = None

def get_router_instance() -> QueryRouter:
    """Get router instance - needed for clarification"""
    global _router_instance, _embedding_model
    
    if _router_instance is None:
        try:
            # Load embedding model
            if _embedding_model is None:
                _embedding_model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
            
            # Create router instance
            _router_instance = QueryRouter(_embedding_model)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize router: {e}")
    
    return _router_instance

@router.get("/health", summary="Router Health Check")
async def router_health():
    """Health check for router service"""
    try:
        router_instance = get_router_instance()
        return {
            "status": "healthy", 
            "collections": len(router_instance.collection_mappings),
            "cache_loaded": bool(router_instance.example_questions)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/collections", summary="Get Available Collections")
async def get_collections(router_instance: QueryRouter = Depends(get_router_instance)):
    """Get list of available collections - needed for clarification"""
    try:
        collections = router_instance.get_collections()
        return {
            "collections": collections,
            "total": len(collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collections: {e}")

@router.get("/collections/{collection_name}/questions", summary="Get Questions for Collection")
async def get_collection_questions(
    collection_name: str,
    router_instance: QueryRouter = Depends(get_router_instance)
):
    """Get example questions for a collection - needed for clarification"""
    try:
        # 🚀 OPTIMIZATION: Sử dụng method mới với limit
        questions = router_instance.get_example_questions_for_collection(collection_name)
        
        # Giới hạn số lượng questions trả về để tránh performance issues
        limited_questions = questions[:50]  # Chỉ trả về 50 questions đầu tiên
        
        return {
            "collection": collection_name,
            "questions": limited_questions,
            "total": len(limited_questions),
            "total_available": len(questions),
            "note": f"Showing first 50 questions out of {len(questions)} total"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting questions for {collection_name}: {e}")
