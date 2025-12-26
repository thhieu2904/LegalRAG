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
    """CCCD data extracted from QR code - unified field naming"""
    field_cccd: str  # Số căn cước công dân (12 digits)
    field_cmnd: Optional[str] = None  # Số CMND cũ
    field_ho_ten: str  # Họ và tên
    field_ngay_sinh: str  # Ngày sinh (DD/MM/YYYY)
    field_gioi_tinh: str  # Giới tính
    field_dia_chi: str  # Địa chỉ
    field_ngay_cap: str  # Ngày cấp (DD/MM/YYYY)


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
    session_id: Optional[str] = None  # For filename generation
    form_name: Optional[str] = None  # Human-readable form name


class FormFillResponse(BaseModel):
    """Response with filled form as bytes (for download)"""
    success: bool
    file_content: Optional[bytes] = None  # Filled DOCX bytes
    filename: Optional[str] = None  # Suggested filename
    message: Optional[str] = None
    # Validation info
    total_fields: Optional[int] = None  # Total placeholders in template
    filled_fields: Optional[int] = None  # Number of filled fields
    missing_fields: Optional[list[str]] = None  # List of empty field names


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
# Form Template Admin Models
# ============================================

class DetectedPosition(BaseModel):
    """A detected fillable position in DOCX"""
    index: int  # Sequential index (0, 1, 2, ...)
    paragraph_index: int  # Paragraph index in document
    text: str  # Context text (e.g., "Họ tên: ......")
    pattern_type: str  # "dots" or "tab"
    label: str = ""  # Label text before the fillable area (e.g., "Họ tên")
    full_paragraph: str = ""  # Full paragraph text for preview
    context_before: list[str] = []  # 2-3 paragraphs before this position
    context_after: list[str] = []  # 2-3 paragraphs after this position
    
    class Config:
        # Always serialize all fields, even if empty
        exclude_none = False


class FormDetectResponse(BaseModel):
    """Response from form detection"""
    success: bool
    positions: list[DetectedPosition] = []
    total_positions: int = 0
    message: Optional[str] = None


class FormFinalizeRequest(BaseModel):
    """Request to finalize template with placeholders"""
    selected_indices: list[int]  # List of position indices to convert to fields


class FormFinalizeResponse(BaseModel):
    """Response with finalized template"""
    success: bool
    template_content: Optional[str] = None  # Base64 encoded DOCX
    placeholders: list[str] = []  # List of generated placeholders ["field_1", "field_2", ...]
    message: Optional[str] = None


# ============================================
# Health Check
# ============================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    storage_service: str
