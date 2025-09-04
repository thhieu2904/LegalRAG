from fastapi import APIRouter
from app.api.v1.endpoints import qr_scanner, card_detector, forms

api_router = APIRouter()

api_router.include_router(qr_scanner.router, prefix="/qr", tags=["qr-scanner"])
api_router.include_router(card_detector.router, prefix="/card", tags=["card-detector"])
api_router.include_router(forms.router, prefix="/forms", tags=["forms"])
