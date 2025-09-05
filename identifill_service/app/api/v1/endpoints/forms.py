from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel

from app.services.forms.form_renderer import FormRenderingService
from app.services.template_filling_service import TemplateFillingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
form_renderer = FormRenderingService(rag_service_url="http://localhost:8000")
template_filler = TemplateFillingService(rag_service_url="http://localhost:8000")

# Request models
class CCCDFillRequest(BaseModel):
    """Request model for filling template with CCCD data"""
    scan_ho_ten: Optional[str] = None
    scan_ngay_sinh: Optional[str] = None  
    scan_dia_chi: Optional[str] = None
    scan_cccd: Optional[str] = None
    scan_gioi_tinh: Optional[str] = None
    
    # Alternative field names for compatibility
    name: Optional[str] = None
    birth_date: Optional[str] = None
    address: Optional[str] = None
    citizen_id: Optional[str] = None
    gender: Optional[str] = None
    
    template_name: Optional[str] = None  # Optional specific template name


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
            "/render/{collection_id}/{doc_id}/{form_filename} - DOCX to HTML conversion",
            "/fill-and-download/{collection_id}/{doc_id} - Fill template with CCCD data and download"
        ]
    }


@router.post("/fill-and-download/{collection_id}/{doc_id}")
async def fill_and_download_form(
    collection_id: str,
    doc_id: str, 
    request: CCCDFillRequest
):
    """
    NHIỆM VỤ 2: Fill template with CCCD data and return for download
    
    Main endpoint cho việc điền form với dữ liệu CCCD được quét
    
    Args:
        collection_id: ID collection
        doc_id: Document ID
        request: CCCD data và template options
        
    Returns:
        Filled .docx file ready for download
    """
    try:
        logger.info(f"Fill and download request: {collection_id}/{doc_id}")
        logger.info(f"CCCD data received: {request.dict()}")
        
        # Convert request to dict for processing
        cccd_data = request.dict()
        
        # Fill template with CCCD data
        filled_content = await template_filler.fill_template_with_cccd_data(
            collection_id=collection_id,
            doc_id=doc_id,
            cccd_data=cccd_data,
            template_name=request.template_name
        )
        
        # Generate filename
        filename = f"{collection_id}_{doc_id}_filled.docx"
        if request.template_name:
            # Use template name in filename
            template_base = request.template_name.replace("_template.docx", "").replace(".docx", "")
            filename = f"{template_base}_filled.docx"
        
        logger.info(f"Returning filled document: {filename} ({len(filled_content)} bytes)")
        
        # Return file for download
        return Response(
            content=filled_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fill_and_download_form: {e}")
        raise HTTPException(status_code=500, detail=f"Form filling failed: {str(e)}")


@router.get("/test/template/{collection_id}/{doc_id}")
async def test_template_access(collection_id: str, doc_id: str):
    """
    Test endpoint để kiểm tra khả năng truy cập template từ rag_service
    """
    try:
        template_content = await template_filler.download_template(collection_id, doc_id)
        return {
            "success": True,
            "message": "Template accessible",
            "template_size": len(template_content),
            "collection_id": collection_id,
            "doc_id": doc_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template access test failed: {str(e)}")
