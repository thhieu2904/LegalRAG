"""
Form Data API - Serve form data cho IdentiFill Service
Simple API để share form resources between services
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json
import logging
from typing import Dict, Any
import aiofiles

logger = logging.getLogger(__name__)

router = APIRouter()

# Base path to forms storage
FORMS_BASE_PATH = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"


@router.get("/data/{collection_id}/{doc_id}/{form_filename}")
async def get_form_data(collection_id: str, doc_id: str, form_filename: str):
    """
    Get form data và mapping configuration
    
    Args:
        collection_id: ID collection (e.g., quy_trinh_cap_ho_tich_cap_xa)
        doc_id: Document ID (e.g., DOC_001)
        form_filename: Form filename (e.g., Khai sinh.docx)
        
    Returns:
        Form data từ mapping.json + form file info
    """
    try:
        # Path to mapping.json
        mapping_path = FORMS_BASE_PATH / collection_id / "documents" / doc_id / "forms" / "mapping.json"
        
        if not mapping_path.exists():
            raise HTTPException(status_code=404, detail="Form mapping not found")
        
        # Load mapping data
        async with aiofiles.open(mapping_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            mapping_data = json.loads(content)
        
        # Path to actual form file
        form_path = FORMS_BASE_PATH / collection_id / "documents" / doc_id / "forms" / form_filename
        
        if not form_path.exists():
            raise HTTPException(status_code=404, detail="Form file not found")
        
        # Return form data
        return {
            "success": True,
            "data": {
                "mapping": mapping_data,
                "form_file_path": str(form_path),
                "form_exists": True,
                "collection_id": collection_id,
                "doc_id": doc_id,
                "form_filename": form_filename
            }
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in mapping file: {e}")
        raise HTTPException(status_code=400, detail="Invalid mapping.json format")
    except Exception as e:
        logger.error(f"Error getting form data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




@router.get("/file/{collection_id}/{doc_id}/{form_filename}")
async def get_form_file_info(collection_id: str, doc_id: str, form_filename: str):
    """
    Get form file info (không download, chỉ info để IdentiFill access)
    """
    try:
        form_path = FORMS_BASE_PATH / collection_id / "documents" / doc_id / "forms" / form_filename
        
        if not form_path.exists():
            raise HTTPException(status_code=404, detail="Form file not found")
        
        # Return file info
        return {
            "success": True,
            "data": {
                "file_path": str(form_path),
                "file_size": form_path.stat().st_size,
                "file_exists": True,
                "filename": form_filename
            }
        }
        
    except Exception as e:
        logger.error(f"Error accessing form file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{collection_id}/{doc_id}")
async def list_forms_in_document(collection_id: str, doc_id: str):
    """
    List all forms trong một document
    """
    try:
        forms_dir = FORMS_BASE_PATH / collection_id / "documents" / doc_id / "forms"
        
        if not forms_dir.exists():
            return {"success": True, "data": {"forms": []}}
        
        forms = []
        for form_file in forms_dir.glob("*"):
            if form_file.is_file() and form_file.suffix in ['.doc', '.docx']:
                forms.append({
                    "filename": form_file.name,
                    "size": form_file.stat().st_size,
                    "has_mapping": (forms_dir / "mapping.json").exists()
                })
        
        return {
            "success": True,
            "data": {
                "collection_id": collection_id,
                "doc_id": doc_id,
                "forms": forms,
                "total_forms": len(forms)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{collection_id}/{doc_id}/{form_filename}/download")
async def download_form_file(collection_id: str, doc_id: str, form_filename: str):
    """
    Download form file content for identifill_service to fill
    Returns actual file content for template filling
    """
    try:
        form_path = FORMS_BASE_PATH / collection_id / "documents" / doc_id / "forms" / form_filename
        
        if not form_path.exists():
            raise HTTPException(status_code=404, detail="Form file not found")
        
        if not form_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        logger.info(f"Serving form file for download: {form_path}")
        return FileResponse(
            path=str(form_path),
            filename=form_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading form file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_forms_api():
    """
    Test endpoint cho Forms API
    """
    return {
        "message": "RAG Service - Forms API is working",
        "status": "healthy",
        "endpoints": [
            "/data/{collection_id}/{doc_id}/{form_filename}",
            "/mapping/{collection_id}/{doc_id}", 
            "/file/{collection_id}/{doc_id}/{form_filename}",
            "/list/{collection_id}/{doc_id}"
        ]
    }
