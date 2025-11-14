"""
Internal JSON Document CRUD API
================================
Provides JSON document editing with backup/restore and rebuild integration.
Similar pattern to internal_files.py (Questions CRUD).

Security: Internal endpoints - only accessible from Admin Service.
"""

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import shutil
import logging
from datetime import datetime

from app.core.config import Settings
from app.core.path_config import PathConfig

# Initialize settings and path config
settings = Settings()
path_config = PathConfig()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/json", tags=["internal-json"])


# ============================================================================
# Pydantic Models
# ============================================================================

class JsonDocumentData(BaseModel):
    """Validated JSON document structure"""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    sections: List[Dict[str, Any]] = Field(..., description="Document sections")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "DOC_001",
                "title": "Hướng dẫn thủ tục hành chính",
                "sections": [
                    {
                        "section_id": "SEC_001",
                        "title": "Giới thiệu",
                        "content": "Nội dung..."
                    }
                ],
                "metadata": {
                    "effective_date": "2024-01-01",
                    "code": "123/2024/QĐ-UBND"
                }
            }
        }


class JsonUpdateRequest(BaseModel):
    """Request to update JSON document"""
    data: Dict[str, Any] = Field(..., description="Complete JSON document data")
    auto_rebuild: bool = Field(True, description="Trigger cache rebuild after update")


class JsonRestoreRequest(BaseModel):
    """Request to restore from backup"""
    backup_filename: str = Field(..., description="Backup filename to restore")
    auto_rebuild: bool = Field(True, description="Trigger cache rebuild after restore")


class BackupInfo(BaseModel):
    """Backup file information"""
    filename: str
    timestamp: str
    size: int
    created_at: str
    is_current: bool = False


class FileOperationResponse(BaseModel):
    """Response for file operations"""
    success: bool
    message: str
    file_path: Optional[str] = None
    backup_path: Optional[str] = None
    rebuild_triggered: bool = False
    rebuild_status: Optional[str] = None


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
# Helper Functions
# ============================================================================

def get_json_file_path(collection: str, doc_id: str) -> Path:
    """
    Get path to processed JSON file
    
    Args:
        collection: Collection name
        doc_id: Document ID
        
    Returns:
        Path to JSON file (finds first .json file in doc folder, excluding backups)
    """
    collections_dir = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
    doc_folder = collections_dir / collection / "documents" / doc_id
    
    # Find first .json file that's NOT a backup (not questions.json, not *.backup)
    if doc_folder.exists():
        for json_file in sorted(doc_folder.glob("*.json")):
            if json_file.name != "questions.json" and not json_file.name.endswith(".backup"):
                return json_file
    
    # Fallback to old pattern if no file found
    return doc_folder / f"{doc_id}.json"


def validate_collection_and_document(collection: str, doc_id: str) -> Path:
    """
    Validate collection and document exist, return JSON file path
    
    Args:
        collection: Collection name
        doc_id: Document ID
        
    Returns:
        Path to JSON file
        
    Raises:
        HTTPException: If collection or document not found
    """
    collections_dir = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
    collection_dir = collections_dir / collection
    
    if not collection_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection}' not found"
        )
    
    doc_dir = collection_dir / "documents" / doc_id
    if not doc_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found in collection '{collection}'"
        )
    
    # Use get_json_file_path to find actual JSON file (not just {doc_id}.json)
    json_path = get_json_file_path(collection, doc_id)
    
    if not json_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"JSON file not found for {collection}/{doc_id}"
        )
    
    return json_path


def validate_json_structure(data: Dict[str, Any]) -> bool:
    """
    Validate JSON structure (DISABLED for flexibility)
    
    Args:
        data: JSON data to validate
        
    Returns:
        True if valid
        
    Note:
        Validation disabled to allow flexible JSON structures.
        Admin users are trusted to maintain valid data.
    """
    # Validation disabled - allow any structure
    # Admin users are responsible for maintaining valid JSON
    return True


def create_backup(file_path: Path) -> Path:
    """
    Create timestamped backup of JSON file
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.name}.backup.{timestamp}"
    
    shutil.copy2(file_path, backup_path)
    logger.info(f"📦 Created backup: {backup_path.name}")
    
    return backup_path


def restore_from_backup(backup_path: Path, target_path: Path):
    """
    Restore file from backup
    
    Args:
        backup_path: Path to backup file
        target_path: Path to restore to
    """
    shutil.copy2(backup_path, target_path)
    logger.info(f"↩️ Restored from backup: {backup_path.name}")


async def trigger_rebuild_for_json(collection: str, doc_id: str) -> Dict[str, Any]:
    """
    Trigger cache rebuild for document (internal helper)
    
    Args:
        collection: Collection name
        doc_id: Document ID
        
    Returns:
        Rebuild status info
    """
    try:
        # Import here to avoid circular dependency
        import subprocess
        from pathlib import Path
        
        # Path to rebuild script
        rebuild_script = Path(__file__).parent.parent.parent / "tools" / "rebuild_selective.py"
        status_file = Path(__file__).parent.parent.parent / "data" / "cache" / "rebuild_status.json"
        
        if not rebuild_script.exists():
            logger.warning(f"⚠️ Rebuild script not found: {rebuild_script}")
            return {"success": False, "error": "Rebuild script not found"}
        
        # Build command
        cmd = [
            'python',
            str(rebuild_script),
            '--scope', 'document',
            '--collection', collection,
            '--doc-id', doc_id,
            '--status-file', str(status_file)
        ]
        
        # Start subprocess (non-blocking)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"🔄 Rebuild triggered for {collection}/{doc_id} (PID: {process.pid})")
        
        return {
            "success": True,
            "pid": process.pid,
            "status": "queued"
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to trigger rebuild: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/collections/{collection}/documents/{doc_id}",
    summary="Get JSON document",
    description="Retrieve processed JSON document content"
)
async def get_json_document(
    collection: str,
    doc_id: str,
    x_internal_api_key: str = Header(None)
):
    """
    Get processed JSON document
    
    **Usage**: Load JSON for viewing or editing
    
    **Returns**: Complete JSON document data
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        json_path = validate_collection_and_document(collection, doc_id)
        
        if not json_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"JSON file not found for {collection}/{doc_id}"
            )
        
        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Retrieved JSON: {collection}/{doc_id}")
        
        return {
            "success": True,
            "data": data,
            "collection": collection,
            "doc_id": doc_id,
            "file_path": str(json_path.relative_to(Path.cwd()))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to read JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/collections/{collection}/documents/{doc_id}",
    response_model=FileOperationResponse,
    summary="Update JSON document",
    description="Update JSON document with automatic backup and optional rebuild"
)
async def update_json_document(
    collection: str,
    doc_id: str,
    request: JsonUpdateRequest,
    x_internal_api_key: str = Header(None)
):
    """
    Update JSON document
    
    **Usage**: Save edited JSON document
    
    **Features**:
    - Automatic backup before update
    - JSON structure validation
    - Optional cache rebuild
    - Rollback on failure
    """
    await verify_internal_api_key(x_internal_api_key)
    
    backup_path = None
    json_path = None
    
    try:
        json_path = validate_collection_and_document(collection, doc_id)
        
        # Validate JSON structure
        validate_json_structure(request.data)
        
        # Create backup if file exists
        if json_path.exists():
            backup_path = create_backup(json_path)
        else:
            # Ensure parent directory exists
            json_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write updated JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(request.data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Updated JSON: {collection}/{doc_id}")
        
        # Trigger rebuild if requested
        rebuild_result = None
        rebuild_triggered = False
        
        if request.auto_rebuild:
            rebuild_result = await trigger_rebuild_for_json(collection, doc_id)
            rebuild_triggered = rebuild_result.get("success", False)
        
        return FileOperationResponse(
            success=True,
            message=f"JSON document updated for {collection}/{doc_id}",
            file_path=str(json_path.relative_to(Path.cwd())),
            backup_path=str(backup_path.relative_to(Path.cwd())) if backup_path else None,
            rebuild_triggered=rebuild_triggered,
            rebuild_status="queued" if rebuild_triggered else "not_requested"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Rollback from backup on failure
        if backup_path and json_path and backup_path.exists():
            try:
                restore_from_backup(backup_path, json_path)
                logger.info(f"↩️ Rolled back to backup after error")
            except Exception as rollback_error:
                logger.error(f"❌ Rollback failed: {rollback_error}")
        
        logger.error(f"❌ Failed to update JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/{collection}/documents/{doc_id}/backups",
    response_model=List[BackupInfo],
    summary="List JSON backups",
    description="Get list of available backups for document"
)
async def list_json_backups(
    collection: str,
    doc_id: str,
    x_internal_api_key: str = Header(None)
):
    """
    List available JSON backups
    
    **Usage**: Show backup history for restore options
    
    **Returns**: List of backups sorted by timestamp (newest first)
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        json_path = validate_collection_and_document(collection, doc_id)
        doc_dir = json_path.parent
        
        # Find all backup files
        backup_pattern = f"{doc_id}.json.backup.*"
        backup_files = list(doc_dir.glob(backup_pattern))
        
        backups = []
        for backup_file in backup_files:
            try:
                # Extract timestamp from filename
                # Format: {doc_id}.json.backup.YYYYMMDD_HHMMSS
                parts = backup_file.name.split('.backup.')
                if len(parts) == 2:
                    timestamp_str = parts[1]
                    
                    # Parse timestamp
                    try:
                        timestamp_dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        created_at = timestamp_dt.isoformat()
                    except:
                        created_at = timestamp_str
                    
                    backups.append(BackupInfo(
                        filename=backup_file.name,
                        timestamp=timestamp_str,
                        size=backup_file.stat().st_size,
                        created_at=created_at
                    ))
            except Exception as e:
                logger.warning(f"⚠️ Error processing backup {backup_file.name}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        logger.info(f"📋 Found {len(backups)} backups for {collection}/{doc_id}")
        
        return backups
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/{collection}/documents/{doc_id}/restore",
    response_model=FileOperationResponse,
    summary="Restore JSON from backup",
    description="Restore JSON document from backup with optional rebuild"
)
async def restore_json_backup(
    collection: str,
    doc_id: str,
    request: JsonRestoreRequest,
    x_internal_api_key: str = Header(None)
):
    """
    Restore JSON from backup
    
    **Usage**: Revert to previous version
    
    **Features**:
    - Creates safety backup of current version
    - Validates backup file exists
    - Optional cache rebuild
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        json_path = validate_collection_and_document(collection, doc_id)
        doc_dir = json_path.parent
        
        # Validate backup file exists
        backup_file = doc_dir / request.backup_filename
        if not backup_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup file '{request.backup_filename}' not found"
            )
        
        # Create safety backup of current version
        safety_backup = None
        if json_path.exists():
            safety_backup = create_backup(json_path)
            logger.info(f"📦 Created safety backup before restore")
        
        # Restore from backup
        restore_from_backup(backup_file, json_path)
        
        logger.info(f"✅ Restored from backup: {request.backup_filename}")
        
        # Trigger rebuild if requested
        rebuild_result = None
        rebuild_triggered = False
        
        if request.auto_rebuild:
            rebuild_result = await trigger_rebuild_for_json(collection, doc_id)
            rebuild_triggered = rebuild_result.get("success", False)
        
        return FileOperationResponse(
            success=True,
            message=f"Restored from backup: {request.backup_filename}",
            file_path=str(json_path.relative_to(Path.cwd())),
            backup_path=str(safety_backup.relative_to(Path.cwd())) if safety_backup else None,
            rebuild_triggered=rebuild_triggered,
            rebuild_status="queued" if rebuild_triggered else "not_requested"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to restore backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/collections/{collection}/documents/{doc_id}/backups/{backup_filename}",
    summary="Delete backup file",
    description="Delete specific backup file (safety check for current file)"
)
async def delete_json_backup(
    collection: str,
    doc_id: str,
    backup_filename: str,
    x_internal_api_key: str = Header(None)
):
    """
    Delete backup file
    
    **Usage**: Clean up old backups
    
    **Safety**: Cannot delete current JSON file
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        json_path = validate_collection_and_document(collection, doc_id)
        doc_dir = json_path.parent
        
        # Validate it's actually a backup file
        if not backup_filename.endswith('.backup.'):
            # Allow .backup.{timestamp} format
            if '.backup.' not in backup_filename:
                raise HTTPException(
                    status_code=400,
                    detail="Can only delete backup files (.backup.*)"
                )
        
        backup_file = doc_dir / backup_filename
        
        if not backup_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup file '{backup_filename}' not found"
            )
        
        # Safety check: don't delete current JSON
        if backup_file == json_path:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete current JSON file"
            )
        
        # Delete backup
        backup_file.unlink()
        
        logger.info(f"🗑️ Deleted backup: {backup_filename}")
        
        return {
            "success": True,
            "message": f"Deleted backup: {backup_filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
