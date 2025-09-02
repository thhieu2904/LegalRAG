from fastapi import APIRouter, HTTPException
import logging
from app.models.schemas import QRScanRequest, QRScanResponse
from app.services.qr_scanner import QRCodeScanner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
qr_scanner = QRCodeScanner()


@router.post("/scan", response_model=QRScanResponse)
async def scan_qr_code(request: QRScanRequest):
    """
    Scan QR code from CCCD image
    """
    try:
        logger.info(f"Received QR scan request with mode: {request.scan_mode}")
        logger.info(f"Image data length: {len(request.image_data) if request.image_data else 0}")
        
        if request.scan_mode.value != "qr":
            raise HTTPException(
                status_code=400, 
                detail="Only QR scan mode is supported in this endpoint"
            )
        
        if not request.image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        result = qr_scanner.scan_qr_from_base64(request.image_data)
        logger.info(f"QR scan result: success={result.success}, message={result.message}")
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in QR scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/scan-enhanced", response_model=QRScanResponse)
async def scan_qr_code_enhanced(request: QRScanRequest):
    """
    Scan QR code with image enhancement
    """
    try:
        logger.info(f"Received enhanced QR scan request")
        logger.info(f"Image data length: {len(request.image_data) if request.image_data else 0}")
        
        if not request.image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        result = qr_scanner.scan_with_enhancement(request.image_data)
        logger.info(f"Enhanced QR scan result: success={result.success}, message={result.message}")
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in enhanced QR scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test")
async def test_qr_endpoint():
    """
    Test endpoint for QR scanner
    """
    return {"message": "QR Scanner API is working", "status": "healthy"}
