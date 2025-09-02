"""
CCCD OCR Microservice
Dịch vụ nhận dạng văn bản từ Căn cước công dân
"""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings
from app.services.simple_ocr_service import get_ocr_service
from app.api.simple_routes import router

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng"""
    # Khởi động
    logger.info("🚀 Đang khởi động dịch vụ OCR...")
    
    try:
        # Khởi tạo OCR service
        logger.info("🔧 Khởi tạo OCR service...")
        service = await get_ocr_service()
        await service.initialize()
        logger.info("✅ OCR service đã sẵn sàng")
        
        # Thông tin dịch vụ
        logger.info("🎉 Dịch vụ OCR khởi động thành công!")
        logger.info(f"📡 URL dịch vụ: http://{settings.host}:{settings.port}")
        logger.info(f"📚 Tài liệu API: http://{settings.host}:{settings.port}/docs")
        logger.info(f"🏥 Kiểm tra sức khỏe: http://{settings.host}:{settings.port}/api/v1/health")
        
    except Exception as e:
        logger.error(f"❌ Lỗi khởi động dịch vụ OCR: {e}")
        raise
    
    yield
    
    # Tắt dịch vụ
    logger.info("🔄 Đang tắt dịch vụ OCR...")

# Tạo ứng dụng FastAPI
app = FastAPI(
    title="CCCD OCR Service",
    version="1.0.0",
    description="""
    🆔 **Dịch vụ nhận dạng văn bản CCCD**
    
    Dịch vụ chuyên dụng để nhận dạng và trích xuất thông tin từ 
    Căn cước công dân Việt Nam.
    
    ## � Chức năng:
    - **📄 Nhận dạng CCCD**: Trích xuất thông tin từ mặt trước và sau
    - **📷 Xử lý ảnh**: Tiền xử lý để cải thiện độ chính xác
    - **💾 Quản lý phiên**: Lưu trữ tạm thời trong bộ nhớ
    
    ## 🚀 Cách sử dụng:
    1. **Tạo phiên**: `POST /api/v1/sessions`
    2. **Tải ảnh**: `POST /api/v1/upload`
    3. **Xử lý OCR**: `POST /api/v1/process/{session_id}`  
    4. **Lấy kết quả**: `GET /api/v1/results/{session_id}`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware ghi log request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    return response

# Bao gồm các routes
app.include_router(router, prefix="/api/v1")

# Endpoint gốc
@app.get("/")
async def root():
    return {
        "service": "CCCD OCR Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Dịch vụ nhận dạng văn bản CCCD",
        "endpoints": {
            "health": "/api/v1/health",
            "docs": "/docs",
            "sessions": "/api/v1/sessions",
            "upload": "/api/v1/upload",
            "process": "/api/v1/process/{session_id}",
            "results": "/api/v1/results/{session_id}"
        }
    }

# Xử lý lỗi
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Lỗi: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Lỗi hệ thống",
            "message": str(exc),
            "service": "cccd-ocr-service"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
    
    try:
        # Cancel cleanup task
        # cleanup_task_handle.cancel()  # Skip for now
        
        # Close cache
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
