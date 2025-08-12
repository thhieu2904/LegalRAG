import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.utils.model_loader import auto_setup_models  # Import tự động setup models
from app.api import routes

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
vectordb_service = None
llm_service = None
rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle của ứng dụng"""
    # Startup
    logger.info("Starting LegalRAG API...")
    
    # Skip auto setup for now - just initialize services
    # logger.info("Setting up models automatically...")
    # model_status = auto_setup_models(settings)
    
    try:
        # Khởi tạo services - models will be loaded on first request
        global vectordb_service, llm_service, rag_service
        logger.info("Initializing services...")
        
        vectordb_service = VectorDBService()
        llm_service = LLMService()
        
        documents_dir = settings.base_dir / "data" / "documents"  
        rag_service = RAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        logger.info("✅ Services initialized successfully")
        
        # Set global service for routes
        routes.rag_service = rag_service
        
        logger.info("LegalRAG API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down LegalRAG API...")

# Tạo FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="LegalRAG - Hệ thống hỏi đáp thông minh về thủ tục hành chính",
    lifespan=lifespan
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routes
app.include_router(routes.router, prefix="/api/v1", tags=["Legal RAG"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LegalRAG API",
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/api/health")
async def api_health():
    """Simple health check"""
    return {"status": "ok", "message": "API is running"}

if __name__ == "__main__":
    # For development - use string import for reload to work
    uvicorn.run(
        "main:app",  # Use string import for proper reload
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
