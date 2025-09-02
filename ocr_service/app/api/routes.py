"""
OCR API Routes
FastAPI routes for OCR microservice endpoints
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from ..models.schemas import (
    ImageUploadRequest, ImageUploadResponse,
    OCRProcessRequest, OCRProcessResponse,
    OCRResultResponse, SessionStatusResponse,
    SessionCreateRequest, SessionCreateResponse,
    HealthCheckResponse, ServiceStatsResponse,
    ErrorResponse, ProcessingStatus, CCCDSide
)
from ..services.ocr_service import get_ocr_service, OCRProcessingService, OCRServiceError, SessionNotFoundError, ImageProcessingError
from ..core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

# Create router
router = APIRouter(prefix="/api/v1", tags=["OCR"])


async def get_service() -> OCRProcessingService:
    """Dependency to get OCR service"""
    try:
        return await get_ocr_service()
    except Exception as e:
        logger.error(f"Failed to get OCR service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR service unavailable"
        )


def handle_service_error(e: Exception) -> HTTPException:
    """Convert service errors to HTTP exceptions"""
    if isinstance(e, SessionNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    elif isinstance(e, ImageProcessingError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    elif isinstance(e, OCRServiceError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    else:
        logger.error(f"Unhandled service error: {str(e)}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal service error"
        )


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest = SessionCreateRequest(),
    service: OCRProcessingService = Depends(get_service)
):
    """Create a new OCR processing session"""
    try:
        expires_in_hours = request.expires_in_hours or settings.SESSION_EXPIRY_HOURS
        
        session = await service.create_session(
            session_id=request.session_id,
            expires_in_hours=expires_in_hours
        )
        
        return SessionCreateResponse(
            success=True,
            session=session,
            message="Session created successfully"
        )
        
    except Exception as e:
        raise handle_service_error(e)


@router.post("/sessions/{session_id}/upload", response_model=ImageUploadResponse)
async def upload_image(
    session_id: str,
    request: ImageUploadRequest,
    service: OCRProcessingService = Depends(get_service)
):
    """Upload image for OCR processing"""
    try:
        # Use session_id from path, override request if needed
        if request.session_id and request.session_id != session_id:
            logger.warning(f"Session ID mismatch: path={session_id}, body={request.session_id}")
        
        image_key, image_size = await service.upload_image(
            session_id=session_id,
            side=request.side,
            image_data=request.image_data,
            image_format=request.image_format
        )
        
        return ImageUploadResponse(
            success=True,
            session_id=session_id,
            side=request.side,
            message=f"{request.side.value.capitalize()} image uploaded successfully",
            image_key=image_key,
            image_size=image_size
        )
        
    except Exception as e:
        raise handle_service_error(e)


@router.post("/sessions/{session_id}/process", response_model=OCRProcessResponse)
async def process_session(
    session_id: str,
    request: OCRProcessRequest = OCRProcessRequest(session_id=""),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: OCRProcessingService = Depends(get_service)
):
    """Start OCR processing for a session"""
    try:
        # Validate session_id match
        if request.session_id and request.session_id != session_id:
            logger.warning(f"Session ID mismatch: path={session_id}, body={request.session_id}")
        
        # Update request with path session_id
        request.session_id = session_id
        
        session = await service.process_session(
            session_id=session_id,
            process_both_sides=request.process_both_sides,
            force_reprocess=request.force_reprocess
        )
        
        # Estimate processing time based on number of images
        estimated_time = 10.0  # Base time for one image
        if request.process_both_sides:
            estimated_time = 20.0  # Time for both images
        
        return OCRProcessResponse(
            success=True,
            session_id=session_id,
            processing_status=session.processing_status,
            message="OCR processing started",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        raise handle_service_error(e)


@router.get("/sessions/{session_id}/results", response_model=OCRResultResponse)
async def get_results(
    session_id: str,
    service: OCRProcessingService = Depends(get_service)
):
    """Get OCR processing results for a session"""
    try:
        session = await service.get_session_results(session_id)
        
        return OCRResultResponse(
            success=True,
            session_id=session_id,
            processing_status=session.processing_status,
            extracted_data=session.extracted_data,
            confidence_scores=session.confidence_scores,
            error_message=session.error_message,
            processing_time=session.processing_time,
            message=f"Results retrieved - status: {session.processing_status.value}"
        )
        
    except Exception as e:
        raise handle_service_error(e)


@router.get("/sessions/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    service: OCRProcessingService = Depends(get_service)
):
    """Get session status and metadata"""
    try:
        session = await service.get_session_status(session_id)
        
        return SessionStatusResponse(
            success=True,
            session_id=session_id,
            processing_status=session.processing_status,
            has_front_image=session.front_image_key is not None,
            has_back_image=session.back_image_key is not None,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            message=f"Session status: {session.processing_status.value}"
        )
        
    except Exception as e:
        raise handle_service_error(e)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    service: OCRProcessingService = Depends(get_service)
):
    """Delete a session and associated data"""
    try:
        success = await service.delete_session(session_id)
        
        if success:
            return JSONResponse(
                content={
                    "success": True,
                    "session_id": session_id,
                    "message": "Session deleted successfully"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "session_id": session_id,
                    "message": "Session not found or already deleted"
                }
            )
        
    except Exception as e:
        raise handle_service_error(e)


@router.post("/upload-and-process")
async def upload_and_process(
    side: CCCDSide,
    image_data: str,
    image_format: str = "jpeg",
    process_both_sides: bool = False,
    session_id: Optional[str] = None,
    service: OCRProcessingService = Depends(get_service)
):
    """Convenience endpoint: upload image and optionally start processing"""
    try:
        # Create session if not provided
        if session_id is None:
            session = await service.create_session()
            session_id = session.session_id
        
        # Upload image
        image_key, image_size = await service.upload_image(
            session_id=session_id,
            side=side,
            image_data=image_data,
            image_format=image_format
        )
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "side": side,
            "image_uploaded": True,
            "image_key": image_key,
            "image_size": image_size
        }
        
        # Start processing if requested and we have required images
        if not process_both_sides or side == CCCDSide.BACK:
            try:
                await service.process_session(
                    session_id=session_id,
                    process_both_sides=process_both_sides
                )
                response_data["processing_started"] = True
                response_data["message"] = "Image uploaded and processing started"
            except OCRServiceError as e:
                # Processing failed but upload succeeded
                response_data["processing_started"] = False
                response_data["processing_error"] = str(e)
                response_data["message"] = f"Image uploaded but processing failed: {str(e)}"
        else:
            response_data["processing_started"] = False
            response_data["message"] = "Image uploaded. Upload back side to start processing."
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise handle_service_error(e)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(service: OCRProcessingService = Depends(get_service)):
    """Health check endpoint"""
    try:
        health_data = await service.health_check()
        
        # Get additional stats
        stats = await service.get_service_stats()
        
        return HealthCheckResponse(
            status=health_data['service'],
            timestamp=health_data['timestamp'],
            version=settings.SERVICE_VERSION,
            redis_connected=health_data['cache_connected'],
            ocr_engine_loaded=health_data['ocr_engine_loaded'],
            active_sessions=stats['active_processing_sessions'],
            cache_stats=stats['cache_stats']
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.SERVICE_VERSION,
            redis_connected=False,
            ocr_engine_loaded=False,
            active_sessions=0,
            cache_stats={}
        )


@router.get("/stats", response_model=ServiceStatsResponse)
async def get_service_stats(service: OCRProcessingService = Depends(get_service)):
    """Get detailed service statistics"""
    try:
        stats = await service.get_service_stats()
        
        return ServiceStatsResponse(
            success=True,
            service_info={
                "name": "OCR Microservice",
                "version": settings.SERVICE_VERSION,
                "status": "running",
                "uptime": stats['ocr_engine_stats'].get('load_time', 0)
            },
            cache_stats=stats['cache_stats'],
            performance_stats={
                "service_stats": stats['service_stats'],
                "ocr_engine_stats": stats['ocr_engine_stats'],
                "active_processing": stats['active_processing_sessions']
            },
            config={
                "redis_db": settings.REDIS_DB,
                "session_expiry_hours": settings.SESSION_EXPIRY_HOURS,
                "cpu_threads": settings.TORCH_CPU_THREADS,
                "max_image_size": settings.MAX_IMAGE_SIZE_MB
            },
            message="Service statistics retrieved successfully"
        )
        
    except Exception as e:
        raise handle_service_error(e)


@router.post("/maintenance/cleanup")
async def cleanup_expired_sessions(
    background_tasks: BackgroundTasks,
    service: OCRProcessingService = Depends(get_service)
):
    """Manually trigger cleanup of expired sessions"""
    try:
        # Run cleanup in background
        background_tasks.add_task(service.cleanup_expired_sessions)
        
        return JSONResponse(content={
            "success": True,
            "message": "Cleanup task started in background"
        })
        
    except Exception as e:
        raise handle_service_error(e)


# Error handlers

# @router.exception_handler(SessionNotFoundError)
# async def session_not_found_handler(request, exc):
#     return JSONResponse(
#         status_code=status.HTTP_404_NOT_FOUND,
#         content=ErrorResponse(
#             error_code="SESSION_NOT_FOUND",
#             message=str(exc)
#         ).dict()
#     )


# @router.exception_handler(ImageProcessingError)
# async def image_processing_error_handler(request, exc):
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content=ErrorResponse(
#             error_code="IMAGE_PROCESSING_ERROR",
#             message=str(exc)
#         ).dict()
#     )


# @router.exception_handler(OCRServiceError)
# async def ocr_service_error_handler(request, exc):
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content=ErrorResponse(
#             error_code="OCR_SERVICE_ERROR",
#             message=str(exc)
#         ).dict()
#     )
