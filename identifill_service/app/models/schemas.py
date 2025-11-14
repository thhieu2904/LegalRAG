from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ScanMode(str, Enum):
    QR = "qr"
    OCR = "ocr"
    HYBRID = "hybrid"


class CCCDData(BaseModel):
    """Căn cước công dân data extracted from QR code"""
    scan_cccd: str  # Số căn cước công dân
    scan_cmnd: Optional[str] = None  # Số CMND cũ  
    scan_ho_ten: str  # Họ và tên
    scan_ngay_sinh: str  # Ngày sinh (DD/MM/YYYY)
    scan_gioi_tinh: str  # Giới tính
    scan_dia_chi: str  # Địa chỉ
    scan_ngay_cap: str  # Ngày cấp (DD/MM/YYYY)


class QRScanRequest(BaseModel):
    """Request model for QR code scanning"""
    image_data: str  # Base64 encoded image
    scan_mode: ScanMode = ScanMode.QR


class QRScanResponse(BaseModel):
    """Response model for QR code scanning"""
    success: bool
    data: Optional[CCCDData] = None
    message: Optional[str] = None
    processing_time: Optional[float] = None
    confidence: Optional[float] = None


class CardDetectionRequest(BaseModel):
    """Request for card detection"""
    image_data: str  # Base64 encoded image
    auto_crop: bool = True


class CardDetectionResponse(BaseModel):
    """Response for card detection"""
    success: bool
    card_detected: bool
    cropped_image: Optional[str] = None  # Base64 encoded cropped image
    confidence: Optional[float] = None
    message: Optional[str] = None


# ============================================
# Form Storage API Models
# ============================================

class FormSaveResponse(BaseModel):
    """Response model for saving form"""
    success: bool
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    message: Optional[str] = None


class FormRecord(BaseModel):
    """Model for stored form record"""
    file_id: str
    form_name: str
    file_name: str
    file_type: str
    file_size: Optional[int] = None
    created_at: str


class FormListResponse(BaseModel):
    """Response model for listing forms"""
    success: bool
    scan_cccd: Optional[str] = None
    scan_ho_ten: Optional[str] = None
    forms: Optional[list[FormRecord]] = None
    total_forms: Optional[int] = None
    message: Optional[str] = None


class FormStats(BaseModel):
    """Model for storage statistics"""
    total_users: int
    total_forms: int
    total_storage_bytes: int
    total_storage_mb: float

