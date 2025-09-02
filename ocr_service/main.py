"""
OCR Microservice - Independen    try:
        # Initialize Redis cache
        logger.info("🔧 Initializing Redis cache...")
        # await init_cache()
        logger.info("✅ Redis cache initialized (skipped)")
        
        # Initialize OCR engine (CPU-optimized)
        logger.info("🔧 Initializing OCR engine (CPU-optimized)...")
        engine = await get_ocr_engine()
        logger.info("✅ OCR engine initialized on CPU")
        
        # Initialize OCR service
        logger.info("🔧 Initializing OCR service...")
        # await ocr_service.initialize()
        logger.info("✅ OCR service initialized (skipped)")
        
        # Background cleanup task
        # cleanup_task_handle = asyncio.create_task(cleanup_task())
        # logger.info("✅ Background cleanup task started")Service
CPU-optimized for text recognition and image processing
"""

import logging
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings
# from app.core.cache import init_cache, close_cache, cleanup_task
from app.services.ocr_engine import get_ocr_engine
# from app.services.ocr_service import ocr_service
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Starting OCR Microservice...")
    
    try:
        # Initialize Redis cache
        logger.info("🔧 Initializing Redis cache...")
        # await init_cache()  # Skip cache for now
        logger.info("✅ Redis cache initialized (skipped)")
        
        # Initialize OCR engine (CPU-optimized)
        logger.info("🔧 Initializing OCR engine (CPU-optimized)...")
        engine = await get_ocr_engine()
        logger.info("✅ OCR engine initialized on CPU")
        
        # Initialize OCR service
        logger.info("🔧 Initializing OCR service...")
        # await ocr_service.initialize()  # Skip for now
        logger.info("✅ OCR service initialized (skipped)")
        
        # Start background cleanup task
        # cleanup_task_handle = asyncio.create_task(cleanup_task())  # Skip for now
        logger.info("✅ Background cleanup task started (skipped)")
        
        # Log service info
        logger.info("🎉 OCR Microservice started successfully!")
        logger.info(f"📡 Service URL: http://{settings.host}:{settings.port}")
        logger.info(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
        logger.info(f"🏥 Health Check: http://{settings.host}:{settings.port}/health")
        logger.info(f"🔍 OCR Endpoint: http://{settings.host}:{settings.port}/api/v1/ocr")
        
    except Exception as e:
        logger.error(f"❌ Failed to start OCR microservice: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down OCR Microservice...")
    
    try:
        # Cancel cleanup task
        # cleanup_task_handle.cancel()  # Skip for now
        
        # Close cache
        # await close_cache()
        logger.info("✅ Redis cache closed (skipped)")
        
        # Cleanup OCR engine
        from app.services.ocr_engine import cleanup_ocr_engine
        await cleanup_ocr_engine()
        logger.info("✅ OCR engine cleaned up")
        
        logger.info("✅ OCR Microservice shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="CCCD OCR Microservice",
    version="1.0.0",
    description="""
    🆔 **Independent OCR Microservice for CCCD Recognition**
    
    A standalone microservice dedicated to Vietnamese Citizen Identity Card (CCCD) 
    optical character recognition using CPU-optimized processing.
    
    ## 🔥 Features:
    - **🆔 CCCD Recognition**: Front and back side text extraction
    - **📷 Image Processing**: Advanced preprocessing for better accuracy  
    - **💾 Session Management**: Temporary storage with Redis
    - **🧠 VietOCR Integration**: Specialized Vietnamese text recognition
    - **⚡ CPU Optimized**: Efficient processing without GPU requirements
    - **🔄 Auto Cleanup**: Automatic session and cache management
    
    ## 🚀 Quick Start:
    1. **Upload Images**: `POST /api/v1/ocr/upload`
    2. **Process OCR**: `POST /api/v1/ocr/process/{session_id}`  
    3. **Get Results**: `GET /api/v1/ocr/results/{session_id}`
    
    ## 🏗️ Architecture:
    - **Engine**: VietOCR with Transformer architecture
    - **Cache**: Redis for temporary storage
    - **Processing**: CPU-based for cost efficiency
    - **API**: RESTful with async FastAPI
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Include routers
app.include_router(router, prefix="/api/v1", tags=["OCR"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "CCCD OCR Microservice",
        "version": "1.0.0",
        "status": "running",
        "description": "Independent microservice for Vietnamese CCCD text recognition",
        "architecture": "CPU-optimized VietOCR processing",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "upload": "/api/v1/ocr/upload",
            "process": "/api/v1/ocr/process/{session_id}",
            "results": "/api/v1/ocr/results/{session_id}",
            "status": "/api/v1/ocr/session/{session_id}/status"
        },
        "integration": {
            "main_backend": f"http://localhost:8000",
            "this_service": f"http://{settings.host}:{settings.port}"
        }
    }

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred in the OCR service",
            "service": "ocr-microservice"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        access_log=True
    )
