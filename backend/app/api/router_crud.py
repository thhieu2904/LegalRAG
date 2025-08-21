"""
🔥 Router CRUD API - Quản lý câu hỏi router với CRUD operations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.router import QueryRouter
from ..core.config import settings

router = APIRouter(prefix="/router", tags=["Router CRUD"])

# 🔥 Pydantic Models for Request/Response
class QuestionCreate(BaseModel):
    text: str = Field(..., description="Nội dung câu hỏi", min_length=1)
    keywords: Optional[List[str]] = Field(default=[], description="Từ khóa liên quan")
    type: Optional[str] = Field(default="variant", description="Loại câu hỏi: main, variant, user_generated")
    category: Optional[str] = Field(default="user_generated", description="Danh mục câu hỏi")
    priority_score: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Điểm ưu tiên")

class QuestionUpdate(BaseModel):
    text: Optional[str] = Field(None, description="Nội dung câu hỏi mới")
    keywords: Optional[List[str]] = Field(None, description="Từ khóa liên quan")
    category: Optional[str] = Field(None, description="Danh mục câu hỏi")
    priority_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Điểm ưu tiên")
    status: Optional[str] = Field(None, description="Trạng thái: active, inactive, deleted")

class QuestionResponse(BaseModel):
    id: str
    text: str
    collection: str
    keywords: List[str]
    type: str
    category: str
    priority_score: float
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]
    source: Optional[str]

class QuestionSearchResult(QuestionResponse):
    similarity_score: float

class CollectionInfo(BaseModel):
    name: str
    display_name: str
    total_questions: int
    active_questions: int

# 🔥 Dependency: Get Router Instance
def get_router() -> QueryRouter:
    """Get router instance từ singleton hoặc create new"""
    try:
        # Import router từ main app hoặc create new instance
        from ...main import app
        if hasattr(app.state, 'query_router'):
            return app.state.query_router
        else:
            # Fallback: create new router instance
            from sentence_transformers import SentenceTransformer
            from ..core.config import settings
            
            model = SentenceTransformer(settings.embedding_model_name)
            return QueryRouter(model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot initialize router: {e}")

# 🔥 CRUD Endpoints

@router.get("/collections", response_model=List[CollectionInfo])
async def get_collections(router_instance: QueryRouter = Depends(get_router)):
    """Lấy danh sách tất cả collections và thống kê"""
    try:
        collections_data = []
        
        for collection_name, mapping in router_instance.collection_mappings.items():
            # Count active questions
            active_questions = len([
                q for q in router_instance.get_questions_by_collection(collection_name, include_deleted=False)
            ])
            
            collections_data.append(CollectionInfo(
                name=collection_name,
                display_name=mapping['display_name'],
                total_questions=mapping['total_questions'],
                active_questions=active_questions
            ))
        
        return collections_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching collections: {e}")

@router.get("/collections/{collection_name}/questions", response_model=List[QuestionResponse])
async def get_questions_in_collection(
    collection_name: str,
    include_deleted: bool = False,
    router_instance: QueryRouter = Depends(get_router)
):
    """Lấy tất cả câu hỏi trong một collection"""
    try:
        questions = router_instance.get_questions_by_collection(collection_name, include_deleted=include_deleted)
        
        return [
            QuestionResponse(
                id=q.get('id', ''),
                text=q.get('text', ''),
                collection=q.get('collection', collection_name),
                keywords=q.get('keywords', []),
                type=q.get('type', 'variant'),
                category=q.get('category', ''),
                priority_score=q.get('priority_score', 0.5),
                status=q.get('status', 'active'),
                created_at=q.get('created_at'),
                updated_at=q.get('updated_at'),
                source=q.get('source', '')
            )
            for q in questions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching questions: {e}")

@router.post("/collections/{collection_name}/questions", response_model=Dict[str, Any])
async def create_question(
    collection_name: str,
    question_data: QuestionCreate,
    router_instance: QueryRouter = Depends(get_router)
):
    """Tạo câu hỏi mới trong collection"""
    try:
        # Convert Pydantic model to dict
        question_dict = question_data.dict()
        
        # Add collection name
        question_dict['collection'] = collection_name
        
        # Create question
        success = router_instance.add_question(collection_name, question_dict)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create question")
        
        return {
            "success": True,
            "message": f"Question created successfully in collection {collection_name}",
            "question_id": question_dict.get('id'),
            "collection": collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating question: {e}")

@router.put("/collections/{collection_name}/questions/{question_id}", response_model=Dict[str, Any])
async def update_question(
    collection_name: str,
    question_id: str,
    updates: QuestionUpdate,
    router_instance: QueryRouter = Depends(get_router)
):
    """Cập nhật câu hỏi existring"""
    try:
        # Convert to dict and filter None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Update question
        success = router_instance.update_question(collection_name, question_id, update_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Question not found or update failed")
        
        return {
            "success": True,
            "message": f"Question {question_id} updated successfully",
            "question_id": question_id,
            "collection": collection_name,
            "updates": update_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating question: {e}")

@router.delete("/collections/{collection_name}/questions/{question_id}", response_model=Dict[str, Any])
async def delete_question(
    collection_name: str,
    question_id: str,
    router_instance: QueryRouter = Depends(get_router)
):
    """Xóa câu hỏi (soft delete)"""
    try:
        success = router_instance.delete_question(collection_name, question_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Question not found or delete failed")
        
        return {
            "success": True,
            "message": f"Question {question_id} deleted successfully",
            "question_id": question_id,
            "collection": collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting question: {e}")

@router.get("/search", response_model=List[QuestionSearchResult])
async def search_questions(
    q: str,
    collection: Optional[str] = None,
    limit: int = 10,
    router_instance: QueryRouter = Depends(get_router)
):
    """Tìm kiếm câu hỏi bằng similarity search"""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        results = router_instance.search_questions(q, collection_name=collection, limit=limit)
        
        return [
            QuestionSearchResult(
                id=r.get('id', ''),
                text=r.get('text', ''),
                collection=r.get('collection', ''),
                keywords=r.get('keywords', []),
                type=r.get('type', 'variant'),
                category=r.get('category', ''),
                priority_score=r.get('priority_score', 0.5),
                status=r.get('status', 'active'),
                created_at=r.get('created_at'),
                updated_at=r.get('updated_at'),
                source=r.get('source', ''),
                similarity_score=r.get('similarity_score', 0.0)
            )
            for r in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching questions: {e}")

@router.post("/collections/{collection_name}/save", response_model=Dict[str, Any])
async def save_collection_to_file(
    collection_name: str,
    router_instance: QueryRouter = Depends(get_router)
):
    """Lưu collection vào file JSON với CRUD format"""
    try:
        success = router_instance.save_questions_to_file(collection_name)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to save collection to file")
        
        return {
            "success": True,
            "message": f"Collection {collection_name} saved to file successfully",
            "collection": collection_name,
            "format": "CRUD-ready JSON"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving collection: {e}")

@router.get("/collections/{collection_name}/stats", response_model=Dict[str, Any])
async def get_collection_stats(
    collection_name: str,
    router_instance: QueryRouter = Depends(get_router)
):
    """Lấy thống kê chi tiết về collection"""
    try:
        questions = router_instance.get_questions_by_collection(collection_name, include_deleted=True)
        
        if not questions:
            raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found")
        
        # Calculate stats
        total_questions = len(questions)
        active_questions = len([q for q in questions if q.get('status', 'active') == 'active'])
        deleted_questions = len([q for q in questions if q.get('status') == 'deleted'])
        
        # Group by type
        type_counts = {}
        category_counts = {}
        for q in questions:
            q_type = q.get('type', 'variant')
            q_category = q.get('category', 'uncategorized')
            
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
            category_counts[q_category] = category_counts.get(q_category, 0) + 1
        
        return {
            "collection_name": collection_name,
            "total_questions": total_questions,
            "active_questions": active_questions,
            "deleted_questions": deleted_questions,
            "type_distribution": type_counts,
            "category_distribution": category_counts,
            "has_vectors": collection_name in router_instance.question_vectors,
            "vector_count": len(router_instance.question_vectors.get(collection_name, [])) if collection_name in router_instance.question_vectors else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection stats: {e}")
