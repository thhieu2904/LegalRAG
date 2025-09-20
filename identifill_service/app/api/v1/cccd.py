"""
CCCD Processing API - Unified QR Scanner and Card Detection
Handles all CCCD-related image processing tasks
"""

from fastapi import APIRouter, HTTPException
import logging
from app.models.schemas import (
    QRScanRequest, 
    QRScanResponse, 
    CardDetectionRequest, 
    CardDetectionResponse
)
from app.services.qr_scanner import QRCodeScanner
from app.services.card_detector import CardDetector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
qr_scanner = QRCodeScanner()
card_detector = CardDetector()


# ==============================================
# CCCD SCANNING ENDPOINTS
# ==============================================

@router.post("/scan", response_model=QRScanResponse)
async def scan_cccd(request: QRScanRequest):
    """
    Production CCCD scanning endpoint.
    Uses optimized region extraction for maximum accuracy.
    """
    try:
        logger.info(f"Received CCCD scan request with mode: {request.scan_mode}")
        logger.info(f"Image data length: {len(request.image_data) if request.image_data else 0}")
        
        if request.scan_mode.value != "qr":
            raise HTTPException(
                status_code=400, 
                detail="Only QR scan mode is supported in this endpoint"
            )
        
        if not request.image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        result = qr_scanner.scan_qr_from_base64(request.image_data)
        logger.info(f"CCCD scan result: success={result.success}, message={result.message}")
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in CCCD scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test")
async def test_cccd_endpoint():
    """
    Test endpoint for CCCD scanner
    """
    return {"message": "CCCD Scanner API is working", "status": "healthy"}


# ==============================================
# CARD DETECTION ENDPOINTS
# ==============================================

@router.post("/detect", response_model=CardDetectionResponse)
async def detect_card(request: CardDetectionRequest):
    """
    Detect and optionally crop ID card from image
    """
    try:
        result = card_detector.detect_card_from_base64(
            request.image_data, 
            request.auto_crop
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/card/test")
async def test_card_detector():
    """
    Test endpoint for card detector
    """
    return {"message": "Card Detector API is working", "status": "healthy"}


# ==============================================
# COMBINED HEALTH CHECK
# ==============================================

@router.get("/health")
async def cccd_health_check():
    """
    Health check for all CCCD processing services
    """
    return {
        "message": "CCCD Processing API is working",
        "status": "healthy",
        "services": {
            "qr_scanner": "available",
            "card_detector": "available"
        },
        "endpoints": {
            "cccd_scan": "/api/v1/cccd/scan",
            "cccd_test": "/api/v1/cccd/test", 
            "card_detect": "/api/v1/cccd/detect",
            "card_test": "/api/v1/cccd/card/test"
        }
    }