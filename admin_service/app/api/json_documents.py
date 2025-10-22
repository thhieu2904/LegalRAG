"""
JSON Document CRUD API
======================
Admin interface for JSON document editing with backup and rebuild support.
Similar pattern to questions.py.

Provides:
- View JSON content
- Edit JSON documents
- Backup management
- Rebuild trigger
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ..services.rag_client import get_rag_client
from ..core.admin_path_config import get_admin_path_config

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class JsonUpdateRequest(BaseModel):
    """Request to update JSON document"""
    data: Dict[str, Any] = Field(..., description="Complete JSON document data")
    trigger_rebuild: bool = Field(False, description="Trigger cache rebuild after update (default: False, manual rebuild recommended)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "DOC_001",
                    "title": "Hướng dẫn thủ tục",
                    "sections": []
                },
                "trigger_rebuild": False
            }
        }


class JsonRestoreRequest(BaseModel):
    """Request to restore from backup"""
    backup_filename: str = Field(..., description="Backup filename to restore")
    trigger_rebuild: bool = Field(True, description="Auto-trigger cache rebuild after restore")


class RebuildRequest(BaseModel):
    """Request to trigger rebuild manually"""
    scope: str = Field("document", description="Rebuild scope: document/collection/all")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/collections/{collection_name}/documents/{doc_id}/json")
async def get_document_json(collection_name: str, doc_id: str):
    """
    Get processed JSON document content
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        
    Returns:
        JSON document data
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"📋 Getting JSON for: {collection_name}/{doc_id}")
        
        # Call RAG Internal API
        rag_client = get_rag_client()
        result = await rag_client.get_json_document(collection_name, doc_id)
        
        logger.info(f"✅ Retrieved JSON: {collection_name}/{doc_id}")
        
        return {
            "success": True,
            "data": result.get("data"),
            "collection": collection_name,
            "doc_id": doc_id,
            "file_path": result.get("file_path")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting JSON for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get JSON document: {str(e)}"
        )


@router.put("/collections/{collection_name}/documents/{doc_id}/json")
async def update_document_json(
    collection_name: str,
    doc_id: str,
    request: JsonUpdateRequest
):
    """
    Update processed JSON document
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        request: Update request with data and rebuild option
        
    Returns:
        Update status with backup info and rebuild status
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"✏️ Updating JSON for: {collection_name}/{doc_id}")
        
        # Call RAG Internal API
        rag_client = get_rag_client()
        result = await rag_client.update_json_document(
            collection_name,
            doc_id,
            request.data,
            auto_rebuild=request.trigger_rebuild
        )
        
        logger.info(f"✅ Updated JSON: {collection_name}/{doc_id}")
        
        if request.trigger_rebuild and result.get("rebuild_triggered"):
            logger.info(f"🔄 Cache rebuild triggered for {collection_name}/{doc_id}")
        
        return {
            "success": True,
            "message": f"JSON document updated for {doc_id}",
            "collection": collection_name,
            "doc_id": doc_id,
            "backup_created": result.get("backup_path") is not None,
            "backup_path": result.get("backup_path"),
            "rebuild_triggered": result.get("rebuild_triggered", False),
            "rebuild_status": result.get("rebuild_status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating JSON for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update JSON document: {str(e)}"
        )


@router.get("/collections/{collection_name}/documents/{doc_id}/json/backups")
async def list_json_backups(collection_name: str, doc_id: str):
    """
    List available JSON backups for document
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        
    Returns:
        List of backups with metadata
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"📦 Listing backups for: {collection_name}/{doc_id}")
        
        # Call RAG Internal API
        rag_client = get_rag_client()
        backups = await rag_client.list_json_backups(collection_name, doc_id)
        
        logger.info(f"✅ Found {len(backups)} backups for {doc_id}")
        
        return {
            "success": True,
            "data": backups,
            "collection": collection_name,
            "doc_id": doc_id,
            "total": len(backups)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing backups for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.post("/collections/{collection_name}/documents/{doc_id}/json/restore")
async def restore_json_backup(
    collection_name: str,
    doc_id: str,
    request: JsonRestoreRequest
):
    """
    Restore JSON from backup
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        request: Restore request with backup filename and rebuild option
        
    Returns:
        Restore status
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"↩️ Restoring backup for: {collection_name}/{doc_id}")
        logger.info(f"   Backup file: {request.backup_filename}")
        
        # Call RAG Internal API
        rag_client = get_rag_client()
        result = await rag_client.restore_json_backup(
            collection_name,
            doc_id,
            request.backup_filename,
            auto_rebuild=request.trigger_rebuild
        )
        
        logger.info(f"✅ Restored from backup: {request.backup_filename}")
        
        if request.trigger_rebuild and result.get("rebuild_triggered"):
            logger.info(f"🔄 Cache rebuild triggered after restore")
        
        return {
            "success": True,
            "message": f"Restored from backup: {request.backup_filename}",
            "collection": collection_name,
            "doc_id": doc_id,
            "restored_from": request.backup_filename,
            "safety_backup_created": result.get("backup_path") is not None,
            "rebuild_triggered": result.get("rebuild_triggered", False),
            "rebuild_status": result.get("rebuild_status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error restoring backup for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.post("/collections/{collection_name}/documents/{doc_id}/json/rebuild")
async def trigger_json_rebuild(
    collection_name: str,
    doc_id: str,
    request: RebuildRequest = RebuildRequest(scope="document")
):
    """
    Manually trigger cache rebuild for document
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        request: Rebuild request with scope
        
    Returns:
        Rebuild trigger status
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"🔄 Manual rebuild trigger for: {collection_name}/{doc_id}")
        logger.info(f"   Scope: {request.scope}")
        
        # Call existing rebuild API through RAG client
        rag_client = get_rag_client()
        result = await rag_client.trigger_rebuild(
            scope=request.scope,
            collection=collection_name,
            doc_id=doc_id
        )
        
        logger.info(f"✅ Rebuild triggered: {collection_name}/{doc_id}")
        
        return {
            "success": True,
            "message": f"Rebuild triggered for {doc_id}",
            "collection": collection_name,
            "doc_id": doc_id,
            "scope": request.scope,
            "pid": result.get("pid"),
            "status": result.get("status", "queued")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error triggering rebuild for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger rebuild: {str(e)}"
        )


@router.get("/collections/{collection_name}/documents/{doc_id}/json/rebuild/status")
async def get_json_rebuild_status(collection_name: str, doc_id: str):
    """
    Get rebuild status for document
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        
    Returns:
        Rebuild status and progress
    """
    try:
        logger.info(f"📊 Checking rebuild status for: {collection_name}/{doc_id}")
        
        # Call existing rebuild status API through RAG client
        rag_client = get_rag_client()
        status = await rag_client.get_rebuild_status()
        
        # Filter for this specific document if in progress
        is_relevant = (
            status.get("scope") == "document" and
            status.get("collection") == collection_name and
            status.get("doc_id") == doc_id
        )
        
        return {
            "success": True,
            "data": status,
            "is_relevant": is_relevant,
            "collection": collection_name,
            "doc_id": doc_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting rebuild status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get rebuild status: {str(e)}"
        )
