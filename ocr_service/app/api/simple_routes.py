"""
OCR API Routes - CCCD Recognition Service
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import time

from ..services.simple_ocr_service import get_ocr_service, OCRService
from ..core.config import get_settings

settings = get_settings()
router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response Models
class SessionRequest(BaseModel):
    session_id: Optional[str] = None
    expires_in_hours: Optional[int] = 2

class SessionResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class ImageUploadRequest(BaseModel):
    session_id: str
    side: str  # "front" or "back"
    image_data: str
    image_format: str = "jpeg"

class ImageUploadResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class ProcessRequest(BaseModel):
    process_both_sides: bool = True

class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class ResultResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class StatusResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class StatsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int
    service_version: str
# Get OCR service
async def get_service():
    return await get_ocr_service()

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    service: OCRService = Depends(get_service)
):
    """Tạo session mới để xử lý OCR"""
    logger.info(f"Creating session with request: {request}")
    try:
        response = await service.create_session(
            session_id=request.session_id,
            expires_in_hours=request.expires_in_hours or 2
        )
        logger.info(f"Session created: {response}")
        return response
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    request: ImageUploadRequest,
    service: OCRService = Depends(get_service)
):
    """Upload ảnh CCCD (mặt trước hoặc sau)"""
    response = await service.upload_image(
        session_id=request.session_id,
        side=request.side,
        image_data=request.image_data
    )
    return response

@router.post("/process/{session_id}", response_model=ProcessResponse)
async def process_ocr(
    session_id: str,
    request: ProcessRequest = ProcessRequest(),
    service: OCRService = Depends(get_service)
):
    """Xử lý OCR cho session"""
    response = await service.process_ocr(
        session_id=session_id,
        process_both_sides=request.process_both_sides
    )
    return response

@router.get("/results/{session_id}", response_model=ResultResponse)
async def get_results(
    session_id: str,
    service: OCRService = Depends(get_service)
):
    """Lấy kết quả OCR"""
    response = await service.get_results(session_id)
    return response

@router.get("/sessions/{session_id}/status", response_model=StatusResponse)
async def get_session_status(
    session_id: str,
    service: OCRService = Depends(get_service)
):
    """Kiểm tra trạng thái session"""
    response = await service.get_session_status(session_id)
    return response

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    service: OCRService = Depends(get_service)
):
    """Xóa session"""
    response = await service.delete_session(session_id)
    return response

@router.get("/stats", response_model=StatsResponse)
async def get_service_stats(
    service: OCRService = Depends(get_service)
):
    """Thống kê dịch vụ"""
    response = await service.get_service_stats()
    return response

@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: OCRService = Depends(get_service)
):
    """Kiểm tra sức khỏe dịch vụ"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=int(time.time() - service.start_time),
        service_version=settings.app_version
    )
