"""
Dynamic Form Fields API Endpoint
GET /forms/{collection_id}/{doc_id}/{form_name}/fields
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import Dict, Any
import logging

from ..services.forms.field_extractor import FieldExtractor

logger = logging.getLogger(__name__)

# Router cho dynamic form fields
router = APIRouter(prefix="/forms", tags=["Dynamic Forms"])

@router.get("/{collection_id}/{doc_id}/{form_name}/fields")
async def get_form_fields(
    collection_id: str,
    doc_id: str, 
    form_name: str
) -> Dict[str, Any]:
    """
    🎯 Extract tất cả placeholder fields từ Word form
    
    Returns:
    {
        "success": true,
        "form_info": {...},
        "fields": {
            "total_fields": int,
            "scan_fields": [...],
            "form_fields": [...],
            "field_metadata": {...}
        }
    }
    """
    
    try:
        # Extract fields using FieldExtractor service
        extractor = FieldExtractor()
        
        # Construct path to Word file
        base_path = Path("../rag_service/data/storage/collections")
        form_path = base_path / collection_id / "documents" / doc_id / "forms" / form_name
        
        if not form_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Form file not found: {form_path}"
            )
        
        # Extract fields from docx
        field_data = extractor.extract_fields_from_docx(form_path)
        
        # Return structured response
        return {
            "success": True,
            "form_info": {
                "collection_id": collection_id,
                "doc_id": doc_id,
                "form_name": form_name,
                "form_path": str(form_path)
            },
            "fields": field_data,
            "api_version": "1.0"
        }
        
    except Exception as e:
        logger.error(f"Error extracting fields from {form_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract form fields: {str(e)}"
        )
