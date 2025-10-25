"""
Document Storage API - File storage and management endpoints
Handles saving, retrieving, and deleting stored forms/documents
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query
from fastapi.responses import FileResponse
import logging
from typing import Optional

from app.services.form_storage_service import FormStorageService
from app.models.schemas import FormSaveResponse, FormListResponse, FormStats

logger = logging.getLogger(__name__)
router = APIRouter()
storage = FormStorageService()


# ============================================
# Document Storage Endpoints
# ============================================

@router.post("/save", response_model=FormSaveResponse)
async def save_document(
    form_file: UploadFile = File(...),
    scan_cccd: str = Form(...),
    scan_ho_ten: str = Form(...),
    form_name: str = Form(...)
):
    """
    💾 Save document file and track in database
    
    Parameters:
    - form_file: Upload .docx file
    - scan_cccd: 12-digit CCCD number (required)
    - scan_ho_ten: User full name (required)
    - form_name: Form type, e.g., "contract", "request" (required)
    
    Returns:
    {
        "success": true,
        "file_id": "uuid-string",
        "file_name": "contract_20251025_103000.docx",
        "message": "Form saved successfully"
    }
    """
    try:
        # Validate CCCD format (12 digits)
        if not scan_cccd.isdigit() or len(scan_cccd) != 12:
            logger.warning(f"Invalid CCCD format: {scan_cccd}")
            raise HTTPException(
                status_code=400,
                detail="CCCD must be 12 digits"
            )
        
        # Read file content
        content = await form_file.read()
        if not content:
            logger.warning("Empty file uploaded")
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        logger.info(f"📝 Processing document save: {form_name} for CCCD: {scan_cccd}")
        
        # Save form
        result = storage.save_form(
            scan_cccd=scan_cccd,
            scan_ho_ten=scan_ho_ten,
            form_name=form_name,
            form_content=content,
            form_type="docx"
        )
        
        if not result["success"]:
            logger.error(f"Save failed: {result['message']}")
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
        
        logger.info(f"✅ Document saved successfully: {result['file_id']}")
        return FormSaveResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in save endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{scan_cccd}", response_model=FormListResponse)
async def list_documents(scan_cccd: str):
    """
    📋 List all documents for a specific CCCD
    
    Parameters:
    - scan_cccd: CCCD number (path parameter)
    
    Returns:
    {
        "success": true,
        "scan_cccd": "079123456789",
        "scan_ho_ten": "Nguyễn Văn A",
        "forms": [
            {
                "file_id": "uuid",
                "form_name": "contract",
                "file_name": "contract_20251025_103000.docx",
                "file_type": "docx",
                "file_size": 25000,
                "created_at": "2025-10-25T10:30:00"
            }
        ],
        "total_forms": 1
    }
    """
    try:
        logger.info(f"📁 Listing documents for CCCD: {scan_cccd}")
        
        result = storage.get_forms(scan_cccd)
        
        if not result["success"]:
            logger.warning(f"No documents found for CCCD: {scan_cccd}")
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        
        logger.info(f"✅ Retrieved {result['total_forms']} documents")
        return FormListResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in list endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{scan_cccd}/{file_name}")
async def download_document(scan_cccd: str, file_name: str):
    """
    📥 Download a specific document file
    
    Parameters:
    - scan_cccd: CCCD number (path parameter)
    - file_name: File name to download (path parameter)
    
    Returns:
    - File content as .docx (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    """
    try:
        logger.info(f"📥 Downloading document: {file_name} for CCCD: {scan_cccd}")
        
        result = storage.download_form(scan_cccd, file_name)
        
        if not result["success"]:
            logger.warning(f"Download failed: {result['message']}")
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        
        # Return file as FileResponse
        file_path = f"data/scanned_documents/{scan_cccd}/forms/{file_name}"
        
        logger.info(f"✅ Sending file: {file_path}")
        
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in download endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{scan_cccd}/{file_id}/{file_name}")
async def delete_document(scan_cccd: str, file_id: str, file_name: str):
    """
    🗑️ Delete a specific document
    
    Parameters:
    - scan_cccd: CCCD number (path parameter)
    - file_id: File ID to delete (path parameter)
    - file_name: File name to delete (path parameter)
    
    Returns:
    {
        "success": true,
        "message": "Form deleted successfully"
    }
    """
    try:
        logger.info(f"🗑️ Deleting document: {file_id} for CCCD: {scan_cccd}")
        
        result = storage.delete_form(scan_cccd, file_id, file_name)
        
        if not result["success"]:
            logger.error(f"Delete failed: {result['message']}")
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
        
        logger.info(f"✅ Document deleted: {file_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in delete endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=FormStats)
async def get_storage_stats():
    """
    📊 Get storage statistics
    
    Returns:
    {
        "total_users": 5,
        "total_forms": 12,
        "total_storage_bytes": 1250000,
        "total_storage_mb": 1.19
    }
    """
    try:
        logger.info("📊 Fetching storage statistics")
        
        stats = storage.get_stats()
        
        logger.info(f"✅ Stats retrieved: {stats}")
        
        return FormStats(**stats)
        
    except Exception as e:
        logger.error(f"❌ Error in stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Health Check
# ============================================

@router.get("/health")
async def storage_health_check():
    """
    🏥 Health check for document storage service
    """
    return {
        "message": "Document Storage API is working",
        "status": "healthy",
        "endpoints": {
            "save": "POST /api/v1/storage/save",
            "list": "GET /api/v1/storage/list/{scan_cccd}",
            "download": "GET /api/v1/storage/download/{scan_cccd}/{file_name}",
            "delete": "DELETE /api/v1/storage/delete/{scan_cccd}/{file_id}/{file_name}",
            "stats": "GET /api/v1/storage/stats"
        }
    }
