"""
QUESTIONS CRUD ENDPOINTS - Implementation Example
==================================================

This file demonstrates how to implement CRUD operations for questions
with proper cache invalidation and VectorDB rebuild.

⚠️ This is a REFERENCE implementation - not production code yet!
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import logging
import json
import httpx
from pathlib import Path
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)
router = APIRouter()

# ==================== DATA MODELS ====================

class QuestionVariant(BaseModel):
    """Individual question variant"""
    text: str = Field(..., min_length=1, max_length=500)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Question text cannot be empty or whitespace")
        return v.strip()

class QuestionsData(BaseModel):
    """Questions data model matching questions.json format"""
    main_question: str = Field(..., min_length=1, max_length=500)
    question_variants: List[str] = Field(default_factory=list, max_items=50)
    
    @validator('main_question')
    def validate_main_question(cls, v):
        if not v.strip():
            raise ValueError("Main question cannot be empty")
        return v.strip()
    
    @validator('question_variants')
    def validate_variants(cls, v):
        # Remove empty variants
        variants = [variant.strip() for variant in v if variant.strip()]
        
        # Check for duplicates
        if len(variants) != len(set(variants)):
            raise ValueError("Duplicate variants found")
        
        return variants
    
    class Config:
        json_schema_extra = {
            "example": {
                "main_question": "Thủ tục này được thực hiện như thế nào?",
                "question_variants": [
                    "Làm sao để thực hiện thủ tục này?",
                    "Quy trình thực hiện ra sao?",
                    "Tôi cần làm gì để hoàn thành thủ tục?"
                ]
            }
        }

class UpdateQuestionsRequest(BaseModel):
    """Request body for updating questions"""
    data: QuestionsData
    rebuild_vectordb: bool = Field(
        default=True,
        description="Whether to rebuild VectorDB after update (default: True)"
    )

class QuestionsResponse(BaseModel):
    """Response model for questions operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    cache_invalidated: bool = False
    vectordb_rebuild_queued: bool = False

# ==================== CONFIGURATION ====================

RAG_SERVICE_URL = "http://localhost:8000"
BACKUP_DIR = Path("data/backups/questions")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ==================== HELPER FUNCTIONS ====================

def get_questions_file_path(collection: str, doc_id: str) -> Path:
    """Get path to questions.json file"""
    from ..core.admin_path_config import get_admin_path_config
    
    path_config = get_admin_path_config()
    doc_dir = path_config.get_document_dir(collection, doc_id)
    return doc_dir / "questions.json"

def create_backup(file_path: Path) -> Path:
    """Create backup of questions file before update"""
    if not file_path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collection_name = file_path.parent.parent.parent.name
    doc_id = file_path.parent.name
    
    backup_filename = f"{collection_name}_{doc_id}_{timestamp}.json"
    backup_path = BACKUP_DIR / backup_filename
    
    shutil.copy2(file_path, backup_path)
    logger.info(f"📦 Created backup: {backup_path}")
    
    return backup_path

def restore_from_backup(backup_path: Path, original_path: Path):
    """Restore questions file from backup"""
    if backup_path and backup_path.exists():
        shutil.copy2(backup_path, original_path)
        logger.info(f"↩️ Restored from backup: {backup_path}")
    else:
        logger.warning(f"⚠️ Backup not found: {backup_path}")

async def invalidate_rag_cache(collection: str, doc_id: str) -> bool:
    """
    Notify RAG service to invalidate cache for updated questions
    
    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/api/internal/cache/invalidate",
                json={
                    "collection": collection,
                    "doc_id": doc_id,
                    "cache_types": ["router", "metadata"]
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Cache invalidated for {collection}/{doc_id}")
                return True
            else:
                logger.warning(
                    f"⚠️ Cache invalidation failed: {response.status_code} - {response.text}"
                )
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to invalidate cache: {e}")
        # Don't fail the entire operation if cache invalidation fails
        # Cache will expire eventually
        return False

async def rebuild_vectordb_for_document(collection: str, doc_id: str) -> bool:
    """
    Trigger selective VectorDB rebuild for updated document
    
    Returns:
        True if rebuild queued successfully, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/api/internal/vectordb/rebuild",
                json={
                    "collection": collection,
                    "doc_id": doc_id,
                    "rebuild_scope": "document",  # Only rebuild this document
                    "async_mode": True  # Background processing
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ VectorDB rebuild queued for {collection}/{doc_id}")
                return True
            else:
                logger.warning(
                    f"⚠️ VectorDB rebuild failed: {response.status_code} - {response.text}"
                )
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to queue VectorDB rebuild: {e}")
        return False

def validate_collection_and_doc(collection: str, doc_id: str):
    """Validate that collection and document exist"""
    from ..core.admin_path_config import get_admin_path_config
    
    path_config = get_admin_path_config()
    
    # Check collection exists
    available_collections = path_config.list_collections()
    if collection not in available_collections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection}' not found"
        )
    
    # Check document exists
    doc_dir = path_config.get_document_dir(collection, doc_id)
    if not doc_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found in collection '{collection}'"
        )

# ==================== CRUD ENDPOINTS ====================

@router.post(
    "/questions/collections/{collection}/documents/{doc_id}",
    response_model=QuestionsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create questions for a document",
    description="Create new questions.json file for a document. Fails if file already exists."
)
async def create_questions(
    collection: str,
    doc_id: str,
    request: UpdateQuestionsRequest,
    background_tasks: BackgroundTasks
):
    """
    Create new questions for a document
    
    Args:
        collection: Collection name
        doc_id: Document ID (e.g., DOC_001)
        request: Questions data
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response with operation details
        
    Raises:
        HTTPException: If validation fails or file already exists
    """
    try:
        # Validate collection and document exist
        validate_collection_and_doc(collection, doc_id)
        
        # Get file path
        questions_file = get_questions_file_path(collection, doc_id)
        
        # Check if file already exists
        if questions_file.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Questions file already exists for {collection}/{doc_id}. Use PUT to update."
            )
        
        logger.info(f"📝 Creating questions for {collection}/{doc_id}")
        
        # Write questions file
        questions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(request.data.dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Questions file created: {questions_file}")
        
        # Invalidate cache (don't need to wait for response)
        cache_invalidated = await invalidate_rag_cache(collection, doc_id)
        
        # Queue VectorDB rebuild if requested
        vectordb_queued = False
        if request.rebuild_vectordb:
            background_tasks.add_task(
                rebuild_vectordb_for_document,
                collection,
                doc_id
            )
            vectordb_queued = True
            logger.info(f"🔄 VectorDB rebuild queued for {collection}/{doc_id}")
        
        return QuestionsResponse(
            success=True,
            message=f"Questions created successfully for {collection}/{doc_id}",
            data={
                "collection": collection,
                "doc_id": doc_id,
                "main_question": request.data.main_question,
                "variant_count": len(request.data.question_variants)
            },
            cache_invalidated=cache_invalidated,
            vectordb_rebuild_queued=vectordb_queued
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating questions for {collection}/{doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create questions: {str(e)}"
        )

@router.put(
    "/questions/collections/{collection}/documents/{doc_id}",
    response_model=QuestionsResponse,
    summary="Update questions for a document",
    description="Update existing questions.json file. Creates backup before update."
)
async def update_questions(
    collection: str,
    doc_id: str,
    request: UpdateQuestionsRequest,
    background_tasks: BackgroundTasks
):
    """
    Update questions for a document with backup and rollback support
    
    Args:
        collection: Collection name
        doc_id: Document ID
        request: New questions data
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response with operation details
        
    Raises:
        HTTPException: If validation fails or file doesn't exist
    """
    backup_path = None
    
    try:
        # Validate collection and document exist
        validate_collection_and_doc(collection, doc_id)
        
        # Get file path
        questions_file = get_questions_file_path(collection, doc_id)
        
        # Check if file exists
        if not questions_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questions file not found for {collection}/{doc_id}. Use POST to create."
            )
        
        logger.info(f"📝 Updating questions for {collection}/{doc_id}")
        
        # Create backup
        backup_path = create_backup(questions_file)
        
        try:
            # Write updated questions
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(request.data.dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Questions file updated: {questions_file}")
            
            # Invalidate cache
            cache_invalidated = await invalidate_rag_cache(collection, doc_id)
            
            # Queue VectorDB rebuild if requested
            vectordb_queued = False
            if request.rebuild_vectordb:
                background_tasks.add_task(
                    rebuild_vectordb_for_document,
                    collection,
                    doc_id
                )
                vectordb_queued = True
                logger.info(f"🔄 VectorDB rebuild queued for {collection}/{doc_id}")
            
            # Success - can delete backup (or keep for audit trail)
            # backup_path.unlink()  # Uncomment to delete backup
            
            return QuestionsResponse(
                success=True,
                message=f"Questions updated successfully for {collection}/{doc_id}",
                data={
                    "collection": collection,
                    "doc_id": doc_id,
                    "main_question": request.data.main_question,
                    "variant_count": len(request.data.question_variants),
                    "backup_created": str(backup_path) if backup_path else None
                },
                cache_invalidated=cache_invalidated,
                vectordb_rebuild_queued=vectordb_queued
            )
            
        except Exception as e:
            # Rollback from backup
            logger.error(f"❌ Update failed, rolling back: {e}")
            restore_from_backup(backup_path, questions_file)
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating questions for {collection}/{doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update questions: {str(e)}"
        )

@router.delete(
    "/questions/collections/{collection}/documents/{doc_id}",
    response_model=QuestionsResponse,
    summary="Delete questions for a document",
    description="Delete questions.json file. Creates backup before deletion."
)
async def delete_questions(
    collection: str,
    doc_id: str,
    background_tasks: BackgroundTasks
):
    """
    Delete questions for a document
    
    Args:
        collection: Collection name
        doc_id: Document ID
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If file doesn't exist
    """
    try:
        # Validate collection and document exist
        validate_collection_and_doc(collection, doc_id)
        
        # Get file path
        questions_file = get_questions_file_path(collection, doc_id)
        
        # Check if file exists
        if not questions_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questions file not found for {collection}/{doc_id}"
            )
        
        logger.info(f"🗑️ Deleting questions for {collection}/{doc_id}")
        
        # Create backup before deletion
        backup_path = create_backup(questions_file)
        
        # Delete file
        questions_file.unlink()
        logger.info(f"✅ Questions file deleted: {questions_file}")
        
        # Invalidate cache
        cache_invalidated = await invalidate_rag_cache(collection, doc_id)
        
        # Queue VectorDB rebuild (without questions)
        background_tasks.add_task(
            rebuild_vectordb_for_document,
            collection,
            doc_id
        )
        logger.info(f"🔄 VectorDB rebuild queued for {collection}/{doc_id}")
        
        return QuestionsResponse(
            success=True,
            message=f"Questions deleted successfully for {collection}/{doc_id}",
            data={
                "collection": collection,
                "doc_id": doc_id,
                "backup_created": str(backup_path) if backup_path else None
            },
            cache_invalidated=cache_invalidated,
            vectordb_rebuild_queued=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting questions for {collection}/{doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete questions: {str(e)}"
        )

@router.patch(
    "/questions/collections/{collection}/documents/{doc_id}/variants",
    response_model=QuestionsResponse,
    summary="Update only question variants",
    description="Update question_variants array without changing main_question"
)
async def update_question_variants(
    collection: str,
    doc_id: str,
    variants: List[str],
    background_tasks: BackgroundTasks
):
    """
    Update only the question variants, keeping main_question unchanged
    
    Args:
        collection: Collection name
        doc_id: Document ID
        variants: New list of question variants
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If file doesn't exist
    """
    backup_path = None
    
    try:
        # Validate collection and document exist
        validate_collection_and_doc(collection, doc_id)
        
        # Get file path
        questions_file = get_questions_file_path(collection, doc_id)
        
        if not questions_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questions file not found for {collection}/{doc_id}"
            )
        
        logger.info(f"📝 Updating variants for {collection}/{doc_id}")
        
        # Load current data
        with open(questions_file, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        # Create backup
        backup_path = create_backup(questions_file)
        
        try:
            # Update variants only
            current_data["question_variants"] = [v.strip() for v in variants if v.strip()]
            
            # Validate using Pydantic
            validated_data = QuestionsData(**current_data)
            
            # Write updated data
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(validated_data.dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Variants updated: {questions_file}")
            
            # Invalidate cache
            cache_invalidated = await invalidate_rag_cache(collection, doc_id)
            
            # Queue VectorDB rebuild
            background_tasks.add_task(
                rebuild_vectordb_for_document,
                collection,
                doc_id
            )
            
            return QuestionsResponse(
                success=True,
                message=f"Question variants updated for {collection}/{doc_id}",
                data={
                    "collection": collection,
                    "doc_id": doc_id,
                    "variant_count": len(validated_data.question_variants)
                },
                cache_invalidated=cache_invalidated,
                vectordb_rebuild_queued=True
            )
            
        except Exception as e:
            # Rollback
            logger.error(f"❌ Variant update failed, rolling back: {e}")
            restore_from_backup(backup_path, questions_file)
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating variants for {collection}/{doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update variants: {str(e)}"
        )

# ==================== BATCH OPERATIONS ====================

class BatchUpdateItem(BaseModel):
    """Single item in batch update request"""
    collection: str
    doc_id: str
    data: QuestionsData

class BatchUpdateRequest(BaseModel):
    """Batch update request"""
    updates: List[BatchUpdateItem] = Field(..., max_items=50)
    rebuild_vectordb: bool = True

@router.post(
    "/questions/batch-update",
    response_model=QuestionsResponse,
    summary="Batch update multiple questions",
    description="Update questions for multiple documents in one request"
)
async def batch_update_questions(
    request: BatchUpdateRequest,
    background_tasks: BackgroundTasks
):
    """
    Update questions for multiple documents in batch
    
    More efficient than individual updates:
    - Single VectorDB rebuild for all affected documents
    - Batch cache invalidation
    - Transaction-like behavior (all or nothing)
    
    Args:
        request: Batch update request with list of updates
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response with batch results
    """
    try:
        logger.info(f"📦 Batch updating {len(request.updates)} questions")
        
        results = []
        backups = []
        
        # Phase 1: Validate all items
        for item in request.updates:
            try:
                validate_collection_and_doc(item.collection, item.doc_id)
                questions_file = get_questions_file_path(item.collection, item.doc_id)
                
                if not questions_file.exists():
                    raise ValueError(f"Questions file not found: {item.collection}/{item.doc_id}")
                    
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation failed for {item.collection}/{item.doc_id}: {str(e)}"
                )
        
        # Phase 2: Create backups
        for item in request.updates:
            questions_file = get_questions_file_path(item.collection, item.doc_id)
            backup_path = create_backup(questions_file)
            backups.append((questions_file, backup_path))
        
        # Phase 3: Update all files
        try:
            for item, (questions_file, backup_path) in zip(request.updates, backups):
                with open(questions_file, 'w', encoding='utf-8') as f:
                    json.dump(item.data.dict(), f, ensure_ascii=False, indent=2)
                
                results.append({
                    "collection": item.collection,
                    "doc_id": item.doc_id,
                    "status": "updated"
                })
                
                logger.info(f"✅ Updated {item.collection}/{item.doc_id}")
            
            # Phase 4: Invalidate all caches
            for item in request.updates:
                await invalidate_rag_cache(item.collection, item.doc_id)
            
            # Phase 5: Queue VectorDB rebuild (all affected documents)
            if request.rebuild_vectordb:
                affected_collections = {}
                for item in request.updates:
                    if item.collection not in affected_collections:
                        affected_collections[item.collection] = []
                    affected_collections[item.collection].append(item.doc_id)
                
                # Queue rebuild per collection
                for collection, doc_ids in affected_collections.items():
                    background_tasks.add_task(
                        rebuild_vectordb_for_document,
                        collection,
                        doc_ids[0]  # For now, rebuild per document
                        # TODO: Implement batch rebuild API
                    )
            
            logger.info(f"✅ Batch update completed: {len(results)} items")
            
            return QuestionsResponse(
                success=True,
                message=f"Batch update completed successfully",
                data={
                    "total_updated": len(results),
                    "results": results
                },
                cache_invalidated=True,
                vectordb_rebuild_queued=request.rebuild_vectordb
            )
            
        except Exception as e:
            # Rollback all updates
            logger.error(f"❌ Batch update failed, rolling back all changes: {e}")
            for questions_file, backup_path in backups:
                restore_from_backup(backup_path, questions_file)
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Batch update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch update failed: {str(e)}"
        )

# ==================== USAGE EXAMPLES ====================

"""
Example API calls:

1. CREATE questions:
POST /api/questions/collections/quy_trinh_boi_thuong_nn/documents/DOC_001
{
  "data": {
    "main_question": "Thủ tục này như thế nào?",
    "question_variants": [
      "Làm sao để thực hiện thủ tục?",
      "Quy trình ra sao?"
    ]
  },
  "rebuild_vectordb": true
}

2. UPDATE questions:
PUT /api/questions/collections/quy_trinh_boi_thuong_nn/documents/DOC_001
{
  "data": {
    "main_question": "Thủ tục này được thực hiện như thế nào?",
    "question_variants": [
      "Làm thế nào để thực hiện thủ tục này?",
      "Quy trình thực hiện ra sao?",
      "Tôi cần làm gì?"
    ]
  },
  "rebuild_vectordb": true
}

3. UPDATE variants only:
PATCH /api/questions/collections/quy_trinh_boi_thuong_nn/documents/DOC_001/variants
[
  "Biến thể 1?",
  "Biến thể 2?",
  "Biến thể 3?"
]

4. DELETE questions:
DELETE /api/questions/collections/quy_trinh_boi_thuong_nn/documents/DOC_001

5. BATCH update:
POST /api/questions/batch-update
{
  "updates": [
    {
      "collection": "quy_trinh_boi_thuong_nn",
      "doc_id": "DOC_001",
      "data": {
        "main_question": "Question 1?",
        "question_variants": ["Variant 1"]
      }
    },
    {
      "collection": "quy_trinh_boi_thuong_nn",
      "doc_id": "DOC_002",
      "data": {
        "main_question": "Question 2?",
        "question_variants": ["Variant 2"]
      }
    }
  ],
  "rebuild_vectordb": true
}
"""
