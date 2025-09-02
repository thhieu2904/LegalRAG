from fastapi import APIRouter, HTTPException
from app.models.schemas import CardDetectionRequest, CardDetectionResponse
from app.services.card_detector import CardDetector

router = APIRouter()
card_detector = CardDetector()


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


@router.get("/test")
async def test_card_detector():
    """
    Test endpoint for card detector
    """
    return {"message": "Card Detector API is working", "status": "healthy"}
