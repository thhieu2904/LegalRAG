"""
Internal File Management API
============================
Provides file read/write operations for questions.json files.
Called by Admin Service to perform CRUD operations.

Security: Internal endpoints - should only be accessible from Admin Service.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Optional
import json
import shutil
from datetime import datetime
import logging

from app.core.config import Settings

# Initialize settings
settings = Settings()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/files/questions", tags=["internal-files"])


# ============================================================================
# Request/Response Models
# ============================================================================

class QuestionsData(BaseModel):
    """Questions file structure"""
    main_question: str = Field(..., min_length=1, description="Main question text")
    question_variants: List[str] = Field(default_factory=list, description="Question variants")

    class Config:
        json_schema_extra = {
            "example": {
                "main_question": "Thủ tục đăng ký kết hôn như thế nào?",
                "question_variants": [
                    "Làm sao để đăng ký kết hôn?",
                    "Quy trình đăng ký kết hôn?",
                    "Cách đăng ký kết hôn?"
                ]
            }
        }


class FileOperationResponse(BaseModel):
    """Standard response for file operations"""
    success: bool
    message: str
    file_path: Optional[str] = None
    backup_path: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class QuestionsFileResponse(BaseModel):
    """Response with questions file data"""
    success: bool
    data: QuestionsData
    file_path: str
    last_modified: str


# ============================================================================
# Security Helper
# ============================================================================

async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    """Verify internal API key for security"""
    expected_key = getattr(settings, 'internal_api_key', 'dev-internal-key')
    
    if x_internal_api_key != expected_key:
        logger.warning(f"❌ Unauthorized access attempt - invalid API key")
        raise HTTPException(
            status_code=403,
            detail="Forbidden - Invalid internal API key"
        )


# ============================================================================
# Path Helper Functions
# ============================================================================

def get_questions_file_path(collection: str, doc_id: str) -> Path:
    """
    Get absolute path to questions.json file
    
    Args:
        collection: Collection name (e.g., 'hop_dong')
        doc_id: Document ID (e.g., 'DOC_001')
    
    Returns:
        Path object to questions.json
    """
    base_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
    file_path = base_path / collection / "documents" / doc_id / "questions.json"
    return file_path


def validate_collection_and_document(collection: str, doc_id: str) -> Path:
    """
    Validate that collection and document exist
    
    Args:
        collection: Collection name
        doc_id: Document ID
    
    Returns:
        Path to questions.json file
    
    Raises:
        HTTPException: If collection or document not found
    """
    file_path = get_questions_file_path(collection, doc_id)
    
    # Check if document directory exists
    doc_dir = file_path.parent
    if not doc_dir.exists():
        logger.error(f"❌ Document not found: {collection}/{doc_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found in collection '{collection}'"
        )
    
    return file_path


def create_backup(file_path: Path) -> Optional[Path]:
    """
    Create backup of existing file before modification
    
    Args:
        file_path: Path to file to backup
    
    Returns:
        Path to backup file, or None if source doesn't exist
    """
    if not file_path.exists():
        return None
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"questions_{timestamp}.json.backup"
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"📦 Backup created: {backup_path.name}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        return None


def restore_from_backup(backup_path: Path, target_path: Path) -> bool:
    """
    Restore file from backup
    
    Args:
        backup_path: Path to backup file
        target_path: Path to restore to
    
    Returns:
        True if restored successfully
    """
    try:
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, target_path)
            logger.info(f"♻️ Restored from backup: {backup_path.name}")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to restore from backup: {e}")
    return False


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/collections/{collection}/documents/{doc_id}",
    response_model=QuestionsFileResponse,
    summary="Read questions file",
    description="Read questions.json file for a specific document"
)
async def read_questions_file(
    collection: str,
    doc_id: str,
    x_internal_api_key: str = Header(None)
):
    """
    Read questions.json file
    
    **Usage:** Get current questions data before editing
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        file_path = validate_collection_and_document(collection, doc_id)
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Questions file not found for {collection}/{doc_id}"
            )
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get last modified time
        last_modified = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        
        logger.info(f"✅ Read questions: {collection}/{doc_id}")
        
        return QuestionsFileResponse(
            success=True,
            data=QuestionsData(**data),
            file_path=str(file_path.relative_to(Path.cwd())),
            last_modified=last_modified
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to read questions file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/{collection}/documents/{doc_id}",
    response_model=FileOperationResponse,
    summary="Create questions file",
    description="Create new questions.json file (fails if already exists)"
)
async def create_questions_file(
    collection: str,
    doc_id: str,
    data: QuestionsData,
    x_internal_api_key: str = Header(None)
):
    """
    Create new questions.json file
    
    **Usage:** Initialize questions for a new document
    
    **Note:** Will fail if file already exists (use PUT to update)
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        file_path = validate_collection_and_document(collection, doc_id)
        
        # Check if file already exists
        if file_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"Questions file already exists for {collection}/{doc_id}. Use PUT to update."
            )
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write new file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Created questions file: {collection}/{doc_id}")
        
        return FileOperationResponse(
            success=True,
            message=f"Questions file created for {collection}/{doc_id}",
            file_path=str(file_path.relative_to(Path.cwd()))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create questions file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/collections/{collection}/documents/{doc_id}",
    response_model=FileOperationResponse,
    summary="Update questions file",
    description="Update existing questions.json file (creates backup automatically)"
)
async def update_questions_file(
    collection: str,
    doc_id: str,
    data: QuestionsData,
    x_internal_api_key: str = Header(None)
):
    """
    Update questions.json file
    
    **Usage:** Modify existing questions
    
    **Features:**
    - Automatic backup before update
    - Rollback on failure
    - Validation of data structure
    """
    await verify_internal_api_key(x_internal_api_key)
    
    backup_path = None
    file_path = None
    
    try:
        file_path = validate_collection_and_document(collection, doc_id)
        
        # Create backup if file exists
        if file_path.exists():
            backup_path = create_backup(file_path)
        
        # Write updated data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Updated questions file: {collection}/{doc_id}")
        
        return FileOperationResponse(
            success=True,
            message=f"Questions file updated for {collection}/{doc_id}",
            file_path=str(file_path.relative_to(Path.cwd())),
            backup_path=str(backup_path.relative_to(Path.cwd())) if backup_path else None
        )
        
    except Exception as e:
        # Rollback from backup on failure
        if backup_path and file_path:
            restore_from_backup(backup_path, file_path)
        
        logger.error(f"❌ Failed to update questions file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/collections/{collection}/documents/{doc_id}",
    response_model=FileOperationResponse,
    summary="Delete questions file",
    description="Delete questions.json file (creates backup before deletion)"
)
async def delete_questions_file(
    collection: str,
    doc_id: str,
    x_internal_api_key: str = Header(None)
):
    """
    Delete questions.json file
    
    **Usage:** Remove questions for a document
    
    **Safety:** Creates backup before deletion for recovery
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        file_path = validate_collection_and_document(collection, doc_id)
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Questions file not found for {collection}/{doc_id}"
            )
        
        # Create backup before deletion
        backup_path = create_backup(file_path)
        
        # Delete file
        file_path.unlink()
        
        logger.info(f"✅ Deleted questions file: {collection}/{doc_id}")
        
        return FileOperationResponse(
            success=True,
            message=f"Questions file deleted for {collection}/{doc_id}",
            file_path=str(file_path.relative_to(Path.cwd())),
            backup_path=str(backup_path.relative_to(Path.cwd())) if backup_path else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete questions file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/collections/{collection}/documents/{doc_id}/variants",
    response_model=FileOperationResponse,
    summary="Update only question variants",
    description="Update question_variants array without changing main_question"
)
async def update_question_variants(
    collection: str,
    doc_id: str,
    variants: List[str],
    x_internal_api_key: str = Header(None)
):
    """
    Update only question variants
    
    **Usage:** Add/remove/modify variants without changing main question
    
    **Example:**
    ```
    PATCH /internal/files/questions/hop_dong/DOC_001/variants
    ["Variant 1", "Variant 2", "Variant 3"]
    ```
    """
    await verify_internal_api_key(x_internal_api_key)
    
    backup_path = None
    file_path = None
    
    try:
        file_path = validate_collection_and_document(collection, doc_id)
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Questions file not found for {collection}/{doc_id}"
            )
        
        # Read current data
        with open(file_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        # Create backup
        backup_path = create_backup(file_path)
        
        # Update only variants
        current_data['question_variants'] = variants
        
        # Write updated data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Updated question variants: {collection}/{doc_id} ({len(variants)} variants)")
        
        return FileOperationResponse(
            success=True,
            message=f"Question variants updated for {collection}/{doc_id}",
            file_path=str(file_path.relative_to(Path.cwd())),
            backup_path=str(backup_path.relative_to(Path.cwd())) if backup_path else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Rollback from backup on failure
        if backup_path and file_path:
            restore_from_backup(backup_path, file_path)
        
        logger.error(f"❌ Failed to update variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/{collection}/documents/{doc_id}/restore",
    response_model=FileOperationResponse,
    summary="Restore from backup",
    description="Restore questions.json from most recent backup"
)
async def restore_questions_from_backup(
    collection: str,
    doc_id: str,
    x_internal_api_key: str = Header(None)
):
    """
    Restore questions from most recent backup
    
    **Usage:** Undo accidental changes
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        file_path = validate_collection_and_document(collection, doc_id)
        
        # Find most recent backup
        backup_files = sorted(
            file_path.parent.glob("questions_*.json.backup"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not backup_files:
            raise HTTPException(
                status_code=404,
                detail=f"No backup found for {collection}/{doc_id}"
            )
        
        latest_backup = backup_files[0]
        
        # Restore from backup
        shutil.copy2(latest_backup, file_path)
        
        logger.info(f"♻️ Restored from backup: {collection}/{doc_id}")
        
        return FileOperationResponse(
            success=True,
            message=f"Questions restored from backup for {collection}/{doc_id}",
            file_path=str(file_path.relative_to(Path.cwd())),
            backup_path=str(latest_backup.relative_to(Path.cwd()))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to restore from backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
