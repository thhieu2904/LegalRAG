"""
Form Service - Pydantic Models/Schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum


# ============================================
# CCCD Scanning Models
# ============================================

class ScanMode(str, Enum):
    QR = "qr"


class CCCDData(BaseModel):
    """CCCD data extracted from QR code"""
    scan_cccd: str  # Số căn cước công dân (12 digits)
    scan_cmnd: Optional[str] = None  # Số CMND cũ
    scan_ho_ten: str  # Họ và tên
    scan_ngay_sinh: str  # Ngày sinh (DD/MM/YYYY)
    scan_gioi_tinh: str  # Giới tính
    scan_dia_chi: str  # Địa chỉ
    scan_ngay_cap: str  # Ngày cấp (DD/MM/YYYY)


class CCCDScanRequest(BaseModel):
    """Request for CCCD QR scanning"""
    image_data: str  # Base64 encoded image
    scan_mode: ScanMode = ScanMode.QR


class CCCDScanResponse(BaseModel):
    """Response for CCCD QR scanning"""
    success: bool
    data: Optional[CCCDData] = None
    message: Optional[str] = None
    processing_time: Optional[float] = None
    confidence: Optional[float] = None


# ============================================
# Form Rendering Models
# ============================================

class FormRenderRequest(BaseModel):
    """Request to render a form template to HTML"""
    template_path: str  # Path in MinIO: forms/{doc_id}/{form_id}_{filename}


class FormRenderResponse(BaseModel):
    """Response with rendered HTML form"""
    success: bool
    html_content: Optional[str] = None  # Styled HTML for dangerouslySetInnerHTML
    raw_html: Optional[str] = None  # Raw HTML without wrapper
    placeholders: Optional[list[str]] = None  # List of {{placeholder}} names found
    message: Optional[str] = None


# ============================================
# Form Filling Models
# ============================================

class FormFillRequest(BaseModel):
    """Request to fill a form template with data"""
    template_path: str  # Path to template in MinIO
    data: Dict[str, Any]  # Combined data: {scan_ho_ten: "...", form_nghe_nghiep: "..."}


class FormFillResponse(BaseModel):
    """Response with filled form as bytes (for download)"""
    success: bool
    file_content: Optional[bytes] = None  # Filled DOCX bytes
    filename: Optional[str] = None  # Suggested filename
    message: Optional[str] = None


# ============================================
# Form Save Models (for filled forms storage)
# ============================================

class FormSaveRequest(BaseModel):
    """Request to save a filled form"""
    session_id: str  # Session ID for folder organization
    cccd_number: Optional[str] = None  # CCCD number (optional, from scan)
    form_name: str  # Form name for filename
    file_content: str  # Base64 encoded DOCX content


class FormSaveResponse(BaseModel):
    """Response after saving filled form"""
    success: bool
    file_path: Optional[str] = None  # Path in MinIO: user_forms/{session}/{cccd}_{form}.docx
    message: Optional[str] = None


# ============================================
# Health Check
# ============================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    storage_service: str
