from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.forms.form_renderer import FormRenderingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
form_renderer = FormRenderingService(rag_service_url="http://localhost:8000")


@router.get("/render/{collection_id}/{doc_id}/{form_filename}")
async def render_form_to_html(collection_id: str, doc_id: str, form_filename: str):
    """
    GIAI ĐOẠN 1: Convert DOCX to HTML
    Đúng theo kế hoạch ban đầu - trả về HTML string cho frontend
    
    Args:
        collection_id: ID collection
        doc_id: Document ID  
        form_filename: Tên file DOCX
        
    Returns:
        HTML string để frontend dùng dangerouslySetInnerHTML
    """
    try:
        logger.info(f"Converting DOCX to HTML: {collection_id}/{doc_id}/{form_filename}")
        
        result = await form_renderer.convert_docx_to_html(
            collection_id=collection_id,
            doc_id=doc_id, 
            form_filename=form_filename
        )
        
        return {
            "success": True,
            "message": "DOCX converted to HTML successfully",
            "data": {
                "html_content": result["html_content"],
                "raw_html": result["raw_html"], 
                "form_metadata": result["form_metadata"],
                "conversion_messages": result["conversion_messages"],
                "placeholders": form_renderer.extract_text_placeholders(result["raw_html"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting DOCX to HTML: {e}")
        raise HTTPException(status_code=500, detail=f"DOCX conversion failed: {str(e)}")


@router.get("/test")
async def test_forms_endpoint():
    """
    Test endpoint - Giai đoạn 1 implementation
    """
    return {
        "message": "Forms API - Giai đoạn 1: DOCX to HTML",
        "status": "healthy",
        "phase": "1 - Static HTML Conversion",
        "technology": "Mammoth.js + dangerouslySetInnerHTML",
        "endpoints": [
            "/render/{collection_id}/{doc_id}/{form_filename} - DOCX to HTML conversion"
        ]
    }
