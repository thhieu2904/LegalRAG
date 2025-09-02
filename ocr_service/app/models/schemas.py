"""
Pydantic schemas for OCR Microservice
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing status for OCR operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CCCDSide(str, Enum):
    """CCCD side identification"""
    FRONT = "front"
    BACK = "back"


class CCCDExtractedData(BaseModel):
    """Extracted data from CCCD"""
    id_number: Optional[str] = Field(None, description="Số căn cước công dân (12 chữ số)")
    full_name: Optional[str] = Field(None, description="Họ và tên đầy đủ")
    date_of_birth: Optional[str] = Field(None, description="Ngày sinh (DD/MM/YYYY)")
    gender: Optional[str] = Field(None, description="Giới tính (Nam/Nữ)")
    nationality: Optional[str] = Field(None, description="Quốc tịch")
    hometown: Optional[str] = Field(None, description="Quê quán")
    residence: Optional[str] = Field(None, description="Nơi thường trú")
    issue_date: Optional[str] = Field(None, description="Ngày cấp")
    expiry_date: Optional[str] = Field(None, description="Ngày hết hạn")
    issued_by: Optional[str] = Field(None, description="Nơi cấp")


class ConfidenceScores(BaseModel):
    """Confidence scores for extracted data"""
    id_number: Optional[float] = Field(None, ge=0.0, le=1.0)
    full_name: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_of_birth: Optional[float] = Field(None, ge=0.0, le=1.0)
    gender: Optional[float] = Field(None, ge=0.0, le=1.0)
    nationality: Optional[float] = Field(None, ge=0.0, le=1.0)
    hometown: Optional[float] = Field(None, ge=0.0, le=1.0)
    residence: Optional[float] = Field(None, ge=0.0, le=1.0)
    issue_date: Optional[float] = Field(None, ge=0.0, le=1.0)
    expiry_date: Optional[float] = Field(None, ge=0.0, le=1.0)
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class OCRSession(BaseModel):
    """OCR processing session"""
    session_id: str = Field(..., description="Unique session identifier")
    front_image_key: Optional[str] = Field(None, description="Redis key for front image")
    back_image_key: Optional[str] = Field(None, description="Redis key for back image")
    extracted_data: Optional[CCCDExtractedData] = Field(None)
    confidence_scores: Optional[ConfidenceScores] = Field(None)
    processing_status: ProcessingStatus = Field(ProcessingStatus.PENDING)
    error_message: Optional[str] = Field(None)
    created_at: datetime = Field(..., description="Session creation time")
    updated_at: datetime = Field(..., description="Last update time")
    expires_at: datetime = Field(..., description="Session expiry time")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


# Request/Response Models

class ImageUploadRequest(BaseModel):
    """Request for image upload"""
    session_id: Optional[str] = Field(None, description="Session ID, will be created if not provided")
    side: CCCDSide = Field(..., description="CCCD side (front/back)")
    image_data: str = Field(..., description="Base64 encoded image data")
    image_format: str = Field(default="jpeg", description="Image format")


class ImageUploadResponse(BaseModel):
    """Response for image upload"""
    success: bool = Field(True)
    session_id: str = Field(..., description="Session ID")
    side: CCCDSide = Field(..., description="CCCD side")
    message: str = Field(..., description="Response message")
    image_key: str = Field(..., description="Redis key for stored image")
    image_size: int = Field(..., description="Image size in bytes")


class OCRProcessRequest(BaseModel):
    """Request for OCR processing"""
    session_id: str = Field(..., description="Session ID")
    process_both_sides: bool = Field(True, description="Require both front and back images")
    force_reprocess: bool = Field(False, description="Force reprocessing even if results exist")


class OCRProcessResponse(BaseModel):
    """Response for OCR processing"""
    success: bool = Field(True)
    session_id: str = Field(..., description="Session ID")
    processing_status: ProcessingStatus = Field(...)
    message: str = Field(..., description="Response message")
    estimated_time: Optional[float] = Field(None, description="Estimated processing time in seconds")


class OCRResultResponse(BaseModel):
    """Response for OCR results"""
    success: bool = Field(True)
    session_id: str = Field(..., description="Session ID")
    processing_status: ProcessingStatus = Field(...)
    extracted_data: Optional[CCCDExtractedData] = Field(None)
    confidence_scores: Optional[ConfidenceScores] = Field(None)
    error_message: Optional[str] = Field(None)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    message: str = Field(..., description="Response message")


class SessionStatusResponse(BaseModel):
    """Response for session status"""
    success: bool = Field(True)
    session_id: str = Field(..., description="Session ID")
    processing_status: ProcessingStatus = Field(...)
    has_front_image: bool = Field(False)
    has_back_image: bool = Field(False)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    expires_at: datetime = Field(...)
    message: str = Field(..., description="Response message")


class SessionCreateRequest(BaseModel):
    """Request to create a new session"""
    session_id: Optional[str] = Field(None, description="Optional custom session ID")
    expires_in_hours: Optional[int] = Field(None, description="Custom expiry time in hours")


class SessionCreateResponse(BaseModel):
    """Response for session creation"""
    success: bool = Field(True)
    session: OCRSession = Field(..., description="Created session details")
    message: str = Field(..., description="Response message")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    redis_connected: bool = Field(..., description="Redis connection status")
    ocr_engine_loaded: bool = Field(..., description="OCR engine status")
    active_sessions: int = Field(..., description="Number of active sessions")
    cache_stats: Dict[str, Any] = Field(..., description="Cache statistics")


class ServiceStatsResponse(BaseModel):
    """Service statistics response"""
    success: bool = Field(True)
    service_info: Dict[str, Any] = Field(..., description="Service information")
    cache_stats: Dict[str, Any] = Field(..., description="Cache statistics")
    performance_stats: Dict[str, Any] = Field(..., description="Performance statistics")
    config: Dict[str, Any] = Field(..., description="Current configuration")
    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False)
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    session_id: Optional[str] = Field(None, description="Session ID if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = Field(True)
    data: Optional[Any] = Field(None)
    message: str = Field(default="Success")
    session_id: Optional[str] = Field(None)
    processing_time: Optional[float] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = Field(default="ocr-microservice")


# Batch processing models (for future enhancement)

class BatchUploadRequest(BaseModel):
    """Request for batch image upload"""
    images: List[ImageUploadRequest] = Field(..., description="List of images to upload")
    create_sessions: bool = Field(True, description="Create sessions for each image")


class BatchProcessRequest(BaseModel):
    """Request for batch OCR processing"""
    session_ids: List[str] = Field(..., description="List of session IDs to process")
    process_both_sides: bool = Field(True, description="Require both sides for each session")


class BatchResultResponse(BaseModel):
    """Response for batch processing results"""
    success: bool = Field(True)
    results: List[OCRResultResponse] = Field(..., description="Results for each session")
    total_processed: int = Field(..., description="Total number of sessions processed")
    successful: int = Field(..., description="Number of successful extractions")
    failed: int = Field(..., description="Number of failed extractions")
    total_processing_time: float = Field(..., description="Total processing time")
    message: str = Field(..., description="Response message")
