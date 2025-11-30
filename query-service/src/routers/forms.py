"""
Form Router - Forwards form operations to form-service

This router acts as a gateway for form-related operations:
- Render template to HTML (for preview)
- Fill template with data
- Scan CCCD QR code
- Save filled form to MinIO

All actual processing is done by form-service (port 8015).
User-facing API is here at query-service (port 8002).
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import logging
import base64

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forms", tags=["Forms"])


# ============= MODELS =============

class CCCDData(BaseModel):
    """Parsed CCCD data from QR code - matches form-service output"""
    scan_cccd: str  # Số căn cước công dân
    scan_cmnd: Optional[str] = None  # Số CMND cũ
    scan_ho_ten: str  # Họ và tên
    scan_ngay_sinh: str  # Ngày sinh
    scan_gioi_tinh: str  # Giới tính
    scan_dia_chi: str  # Địa chỉ
    scan_ngay_cap: str  # Ngày cấp


class CCCDScanRequest(BaseModel):
    """Request to scan CCCD QR code"""
    image_data: str  # Base64 encoded image


class CCCDScanResponse(BaseModel):
    """Response from CCCD scanning - matches form-service output exactly"""
    success: bool
    message: Optional[str] = None
    data: Optional[CCCDData] = None
    processing_time: Optional[float] = None
    confidence: Optional[float] = None


class FormRenderRequest(BaseModel):
    """Request to render form template to HTML"""
    template_path: str  # Path in MinIO: forms/{doc_id}/{filename}


class FormRenderResponse(BaseModel):
    """Response with rendered HTML"""
    success: bool
    message: str
    html_content: Optional[str] = None  # Match form-service response
    raw_html: Optional[str] = None
    placeholders: Optional[list] = None
    template_path: Optional[str] = None


class FormFillRequest(BaseModel):
    """Request to fill form template with data"""
    template_path: str  # Path in MinIO: forms/{doc_id}/{filename}
    data: Dict[str, Any]  # Mapping of placeholders to values
    session_id: Optional[str] = None  # For naming saved file
    cccd_number: Optional[str] = None  # For naming saved file


class FormFillResponse(BaseModel):
    """Response with filled form"""
    success: bool
    message: str
    file_bytes: Optional[str] = None  # Base64 encoded DOCX
    saved_path: Optional[str] = None  # Path where form was saved (if auto-save)


class FormSaveRequest(BaseModel):
    """Request to save filled form to MinIO"""
    file_bytes: str  # Base64 encoded DOCX
    session_id: str
    form_id: str  # Form template UUID (for DB logging)
    form_name: str
    cccd_number: Optional[str] = None


class FormSaveResponse(BaseModel):
    """Response from saving form"""
    success: bool
    message: str
    saved_path: Optional[str] = None
    submission_id: Optional[str] = None  # ID in form_submissions table


# ============= HTTP CLIENT =============

_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


# ============= ENDPOINTS =============

@router.post("/cccd/scan", response_model=CCCDScanResponse)
async def scan_cccd(request: CCCDScanRequest):
    """
    Scan CCCD QR code from image.
    
    Forwards to form-service for processing.
    
    Args:
        request: Contains base64 encoded image
        
    Returns:
        Parsed CCCD data or error message
    """
    try:
        client = await get_http_client()
        
        response = await client.post(
            f"{settings.FORM_SERVICE_URL}/cccd/scan",
            json={"image_data": request.image_data}
        )
        
        if response.status_code == 200:
            data = response.json()
            return CCCDScanResponse(**data)
        else:
            error_detail = response.json().get("detail", "Form service error")
            return CCCDScanResponse(
                success=False,
                message=f"Scan failed: {error_detail}",
                data=None
            )
            
    except httpx.TimeoutException:
        logger.error("Form service timeout during CCCD scan")
        return CCCDScanResponse(
            success=False,
            message="Request timeout. Please try again.",
            data=None
        )
    except Exception as e:
        logger.error(f"CCCD scan error: {e}")
        return CCCDScanResponse(
            success=False,
            message=f"Error: {str(e)}",
            data=None
        )


@router.post("/cccd/scan/upload", response_model=CCCDScanResponse)
async def scan_cccd_upload(file: UploadFile = File(...)):
    """
    Scan CCCD QR code from uploaded image file.
    
    Alternative endpoint that accepts file upload instead of base64.
    
    Args:
        file: Uploaded image file (JPEG, PNG)
        
    Returns:
        Parsed CCCD data or error message
    """
    try:
        # Read and encode file
        contents = await file.read()
        image_data = base64.b64encode(contents).decode("utf-8")
        
        # Forward to form-service
        client = await get_http_client()
        
        response = await client.post(
            f"{settings.FORM_SERVICE_URL}/cccd/scan",
            json={"image_data": image_data}
        )
        
        if response.status_code == 200:
            data = response.json()
            return CCCDScanResponse(**data)
        else:
            error_detail = response.json().get("detail", "Form service error")
            return CCCDScanResponse(
                success=False,
                message=f"Scan failed: {error_detail}",
                data=None
            )
            
    except Exception as e:
        logger.error(f"CCCD upload scan error: {e}")
        return CCCDScanResponse(
            success=False,
            message=f"Error: {str(e)}",
            data=None
        )


@router.post("/render", response_model=FormRenderResponse)
async def render_form(request: FormRenderRequest):
    """
    Render form template to HTML for preview.
    
    Forwards to form-service which downloads from storage-service
    and converts DOCX to HTML.
    
    Args:
        request: Contains template path in MinIO
        
    Returns:
        HTML content of the form
    """
    try:
        client = await get_http_client()
        
        response = await client.post(
            f"{settings.FORM_SERVICE_URL}/render",
            json={"template_path": request.template_path}
        )
        
        if response.status_code == 200:
            data = response.json()
            return FormRenderResponse(**data)
        else:
            error_detail = response.json().get("detail", "Form service error")
            return FormRenderResponse(
                success=False,
                message=f"Render failed: {error_detail}",
                html_content=None
            )
            
    except httpx.TimeoutException:
        logger.error("Form service timeout during render")
        return FormRenderResponse(
            success=False,
            message="Request timeout. Please try again.",
            html_content=None
        )
    except Exception as e:
        logger.error(f"Form render error: {e}")
        return FormRenderResponse(
            success=False,
            message=f"Error: {str(e)}",
            html_content=None
        )


@router.post("/fill", response_model=FormFillResponse)
async def fill_form(request: FormFillRequest):
    """
    Fill form template with data.
    
    Forwards to form-service which:
    1. Downloads template from storage-service
    2. Fills placeholders with provided data
    3. Returns filled DOCX as base64
    
    Args:
        request: Contains template path and data mapping
        
    Returns:
        Base64 encoded filled DOCX
    """
    try:
        client = await get_http_client()
        
        payload = {
            "template_path": request.template_path,
            "data": request.data
        }
        
        if request.session_id:
            payload["session_id"] = request.session_id
        if request.cccd_number:
            payload["cccd_number"] = request.cccd_number
        
        response = await client.post(
            f"{settings.FORM_SERVICE_URL}/fill",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return FormFillResponse(**data)
        else:
            error_detail = response.json().get("detail", "Form service error")
            return FormFillResponse(
                success=False,
                message=f"Fill failed: {error_detail}",
                file_bytes=None
            )
            
    except httpx.TimeoutException:
        logger.error("Form service timeout during fill")
        return FormFillResponse(
            success=False,
            message="Request timeout. Please try again.",
            file_bytes=None
        )
    except Exception as e:
        logger.error(f"Form fill error: {e}")
        return FormFillResponse(
            success=False,
            message=f"Error: {str(e)}",
            file_bytes=None
        )


@router.post("/save", response_model=FormSaveResponse)
async def save_form(request: FormSaveRequest):
    """
    Save filled form to MinIO and log to form_submissions table.
    
    Saves to: user_forms/{session_id}/{cccd}_{form_name}.docx
    If no CCCD: user_forms/{session_id}/{form_name}.docx
    
    Args:
        request: Contains base64 file, session_id, form_id, form_name, optional CCCD
        
    Returns:
        Path where form was saved + submission_id
    """
    # Import db_client from main module
    from ..main import db_client
    
    try:
        client = await get_http_client()
        
        # Build filename - sanitize form_name
        import re
        safe_name = re.sub(r'[^\w\s-]', '', request.form_name)
        safe_name = re.sub(r'\s+', '-', safe_name.strip())
        safe_name = safe_name.lower()[:50]
        
        if request.cccd_number and len(request.cccd_number) == 12:
            filename = f"{request.cccd_number}_{safe_name}.docx"
        else:
            filename = f"{safe_name}.docx"
        
        folder = f"user_forms/{request.session_id}"
        
        # Upload to storage-service
        # Decode base64 to bytes
        file_bytes = base64.b64decode(request.file_bytes)
        
        # Use multipart/form-data for file upload with folder param
        response = await client.post(
            f"{settings.STORAGE_SERVICE_URL}/upload",
            params={"folder": folder},  # Use query param for folder
            files={"file": (filename, file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            timeout=30.0
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            saved_path = result.get("file_path", f"{folder}/{filename}")
            
            # Log to form_submissions table for admin dashboard
            submission_id = None
            if db_client:
                submission_id = db_client.insert_form_submission(
                    form_id=request.form_id,
                    output_file_path=saved_path
                )
                if submission_id:
                    logger.info(f"✅ Form submission logged: {submission_id}")
                else:
                    logger.warning("⚠️ Failed to log form submission to DB")
            
            return FormSaveResponse(
                success=True,
                message="Form saved successfully",
                saved_path=saved_path,
                submission_id=submission_id
            )
        else:
            error_detail = response.json().get("detail", "Storage service error")
            return FormSaveResponse(
                success=False,
                message=f"Save failed: {error_detail}",
                saved_path=None
            )
            
    except Exception as e:
        logger.error(f"Form save error: {e}")
        return FormSaveResponse(
            success=False,
            message=f"Error: {str(e)}",
            saved_path=None
        )


@router.get("/health")
async def forms_health():
    """Check form-service health"""
    try:
        client = await get_http_client()
        response = await client.get(f"{settings.FORM_SERVICE_URL}/health", timeout=5.0)
        
        if response.status_code == 200:
            return {"status": "healthy", "form_service": "connected"}
        else:
            return {"status": "degraded", "form_service": "error"}
    except:
        return {"status": "unhealthy", "form_service": "disconnected"}
