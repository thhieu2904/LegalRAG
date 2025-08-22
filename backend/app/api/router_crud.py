"""
🔥 Router CRUD API - Quản lý câu hỏi router với CRUD operations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os
import logging

from ..services.router import QueryRouter
from ..core.config import settings

# Setup logger
logger = logging.getLogger(__name__)

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

class DocumentInfo(BaseModel):
    id: str
    title: str
    collection: str
    path: str
    question_count: int
    json_file: str

# Global instances to prevent memory leaks
_embedding_model = None
_router_instance = None

# 🔥 Dependency: Get Router Instance  
def get_router() -> QueryRouter:
    """Get router instance từ singleton hoặc create new - Fixed memory leak"""
    global _embedding_model, _router_instance
    
    try:
        # Return cached router instance if available
        if _router_instance is not None:
            return _router_instance
            
        # Try to get from main app state
        try:
            import sys
            if 'main' in sys.modules:
                main_module = sys.modules['main']
                if hasattr(main_module, 'app') and hasattr(main_module.app.state, 'query_router'):
                    if main_module.app.state.query_router:
                        _router_instance = main_module.app.state.query_router
                        return _router_instance
        except Exception:
            pass
            
        # Fallback: create router with singleton model to prevent VRAM leak
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer
            
            logger.info("🔄 Loading embedding model for router CRUD (one-time init)")
            # Use CPU to avoid CUDA memory issues in API endpoints
            _embedding_model = SentenceTransformer(settings.embedding_model_name, device='cpu')
            logger.info("✅ Embedding model loaded successfully for router CRUD")
        
        # Create router instance and cache it
        _router_instance = QueryRouter(_embedding_model)
        logger.info("✅ Router instance created and cached")
        return _router_instance
        
    except Exception as e:
        logger.error(f"❌ Cannot initialize router: {e}")
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

@router.get("/collections/{collection_name}/documents", response_model=List[DocumentInfo])
async def get_documents_in_collection(
    collection_name: str,
    router_instance: QueryRouter = Depends(get_router)
):
    """Lấy danh sách documents trong một collection - Fixed to read from filesystem"""
    try:
        # Đọc trực tiếp từ filesystem thay vì registry để tránh missing documents
        collection_path = os.path.join(settings.storage_dir, "collections", collection_name, "documents")
        
        if not os.path.exists(collection_path):
            logger.warning(f"Collection path not found: {collection_path}")
            return []
            
        documents = []
        
        # Đọc tất cả thư mục trong documents
        for doc_dir in os.listdir(collection_path):
            doc_path = os.path.join(collection_path, doc_dir)
            if not os.path.isdir(doc_path):
                continue
                
            # Tìm router_questions.json
            router_questions_path = os.path.join(doc_path, 'router_questions.json')
            
            question_count = 0
            title = doc_dir  # fallback title
            json_file = ""
            
            if os.path.exists(router_questions_path):
                try:
                    with open(router_questions_path, 'r', encoding='utf-8') as qf:
                        q_data = json.load(qf)
                        question_count = len(q_data.get('question_variants', []))
                        # Add main question to count
                        if q_data.get('main_question'):
                            question_count += 1
                        title = q_data.get('metadata', {}).get('title', title)
                except Exception as e:
                    logger.warning(f"Error reading router_questions.json for {doc_dir}: {e}")
                    
            # Tìm file JSON chính
            for file in os.listdir(doc_path):
                if file.endswith('.json') and file != 'router_questions.json':
                    json_file = file
                    break
            
            documents.append(DocumentInfo(
                id=doc_dir,
                title=title,
                collection=collection_name,
                path=f"collections/{collection_name}/documents/{doc_dir}",
                question_count=question_count,
                json_file=json_file
            ))
        
        # Sort by document ID for consistent ordering
        documents.sort(key=lambda x: x.id)
        logger.info(f"Found {len(documents)} documents in collection {collection_name}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {e}")

@router.get("/collections/{collection_name}/documents/{document_id}/questions", response_model=List[QuestionResponse])
async def get_questions_in_document(
    collection_name: str,
    document_id: str,
    include_deleted: bool = False,
    router_instance: QueryRouter = Depends(get_router)
):
    """Lấy tất cả câu hỏi trong một document cụ thể"""
    try:
        router_questions_path = None
        
        # Try to read from documents.json registry first
        documents_json_path = os.path.join(settings.storage_dir, "registry", "documents.json")
        
        if os.path.exists(documents_json_path):
            try:
                with open(documents_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                doc_info = data.get('documents', {}).get(document_id)
                if doc_info and doc_info.get('collection') == collection_name:
                    # Registry path found and matches collection
                    router_questions_path = os.path.join(
                        settings.storage_dir, 
                        doc_info.get('path', ''), 
                        'router_questions.json'
                    )
            except Exception as e:
                logger.warning(f"Error reading documents registry: {e}")
        
        # If registry lookup failed, try direct filesystem approach
        if not router_questions_path or not os.path.exists(router_questions_path):
            # Direct filesystem path approach
            direct_path = os.path.join(
                settings.storage_dir, 
                "collections", 
                collection_name, 
                "documents", 
                document_id,
                'router_questions.json'
            )
            if os.path.exists(direct_path):
                router_questions_path = direct_path
            else:
                raise HTTPException(status_code=404, detail="Document not found")
        
        if not os.path.exists(router_questions_path):
            return []
            
        with open(router_questions_path, 'r', encoding='utf-8') as f:
            q_data = json.load(f)
            
        questions = []
        question_variants = q_data.get('question_variants', [])
        
        # Thêm main question
        if q_data.get('main_question'):
            questions.append(QuestionResponse(
                id=f"{document_id}_main",
                text=q_data['main_question'],
                collection=collection_name,
                keywords=q_data.get('keywords', []),
                type="main",
                category=q_data.get('metadata', {}).get('code', ''),
                priority_score=1.0,
                status="active",
                created_at=q_data.get('metadata', {}).get('generated_at'),
                updated_at=None,
                source=document_id
            ))
        
        # Thêm question variants
        for i, variant in enumerate(question_variants):
            questions.append(QuestionResponse(
                id=f"{document_id}_variant_{i}",
                text=variant,
                collection=collection_name,
                keywords=q_data.get('keywords', []),
                type="variant",
                category=q_data.get('metadata', {}).get('code', ''),
                priority_score=0.8,
                status="active",
                created_at=q_data.get('metadata', {}).get('generated_at'),
                updated_at=None,
                source=document_id
            ))
        
        return questions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document questions: {e}")

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
