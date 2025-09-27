"""
LegalRAG Admin Service
======================

Microservice for admin panel operations:
- Collections management
- Documents listing  
- Questions management
- Storage operations

Uses PathConfig for Docker/Local compatibility - NO hardcoded paths!
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path
import sys

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from app.api import collections, documents, questions, analytics
from app.core.config import AdminConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LegalRAG Admin Service",
    description="Admin operations for Legal document management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server
        "http://localhost:5173",   # Vite dev server  
        "http://localhost:8080",   # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(collections.router, prefix="/api", tags=["collections"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(questions.router, prefix="/api", tags=["questions"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "LegalRAG Admin Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test AdminPathConfig initialization
        from app.core.admin_path_config import get_admin_path_config
        path_config = get_admin_path_config()
        
        return {
            "status": "healthy",
            "service": "admin",
            "environment": path_config.environment,
            "collections_dir": str(path_config.collections_dir),
            "collections_exist": path_config.collections_dir.exists()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("🚀 Starting LegalRAG Admin Service...")
    logger.info("📋 Available endpoints:")
    logger.info("   - GET  / (service info)")
    logger.info("   - GET  /health (health check)")
    logger.info("   - GET  /api/collections (collections list)")
    logger.info("   - GET  /api/collections/{collection}/documents (documents list)")
    logger.info("   - GET  /api/questions/collections/{collection}/documents/{doc_id} (questions)")
    logger.info("   - GET  /docs (API documentation)")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=True,
        log_level="info"
    )