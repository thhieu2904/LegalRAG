from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.cccd import router as cccd_router
from app.api.v1.forms import router as forms_router
from app.api.v1.storage import router as storage_router
from app.core.config import settings
from app.core.database import db
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="IDentifill Service - QR Code Scanner for CCCD (Restructured)",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with new simplified structure
app.include_router(cccd_router, prefix=f"{settings.API_V1_STR}/cccd", tags=["CCCD Processing"])
app.include_router(forms_router, prefix=f"{settings.API_V1_STR}/forms", tags=["Forms"])
app.include_router(storage_router, prefix=f"{settings.API_V1_STR}/storage", tags=["Document Storage"])

@app.get("/")
async def root():
    return {"message": "IDentifill Service - QR Code Scanner API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize database on service startup"""
    try:
        logger.info("🚀 Starting Identifill Service...")
        db.init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
