"""
FastAPI application for Vietnamese document reranking.
"""
import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings

from .models import (
    RerankRequest,
    RerankResponse,
    RerankResult,
    HealthResponse,
    ErrorResponse
)
from .reranker import VietnameseReranker

# ============================================
# Configuration
# ============================================

class Settings(BaseSettings):
    """Service configuration from environment variables."""
    
    # Service config
    service_name: str = "rerank-service"
    service_port: int = 8013
    service_host: str = "0.0.0.0"
    
    # Model config
    model_name: str = "BAAI/bge-reranker-v2-m3"
    model_cache_dir: str = "/app/models"
    model_max_length: int = 1024
    
    # Hardware config
    device: str = "cpu"
    
    # Inference config
    batch_size: int = 16
    top_k: int = 5
    
    # Security
    api_key_enabled: bool = False
    api_key: str = "rerank-secret-key-change-in-production"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# ============================================
# Logging Setup
# ============================================

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================
# Global State
# ============================================

reranker: Optional[VietnameseReranker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - load model on startup."""
    global reranker
    
    logger.info("=" * 60)
    logger.info(f"Starting {settings.service_name}")
    logger.info("=" * 60)
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"Device: {settings.device}")
    logger.info(f"Batch Size: {settings.batch_size}")
    logger.info(f"Default Top-K: {settings.top_k}")
    logger.info("=" * 60)
    
    try:
        # Initialize reranker
        reranker = VietnameseReranker(
            model_name=settings.model_name,
            device=settings.device,
            max_length=settings.model_max_length,
            cache_dir=settings.model_cache_dir
        )
        logger.info("✓ Reranker initialized successfully")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize reranker: {e}")
        raise
    
    yield
    
    logger.info(f"Shutting down {settings.service_name}")


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title=settings.service_name,
    description="Vietnamese document reranking service using Cross-Encoder",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Dependencies
# ============================================

def get_reranker() -> VietnameseReranker:
    """Dependency to get reranker instance."""
    if reranker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker model not loaded"
        )
    return reranker


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """Verify API key if enabled."""
    if not settings.api_key_enabled:
        return True
    
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True


# ============================================
# API Endpoints
# ============================================

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(
    reranker: VietnameseReranker = Depends(get_reranker)
):
    """
    Health check endpoint.
    
    Returns service status and model information.
    """
    info = reranker.get_info()
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        model_loaded=True,
        device=info["device"]
    )


@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(
    request: RerankRequest,
    reranker: VietnameseReranker = Depends(get_reranker),
    _: bool = Depends(verify_api_key)
):
    """
    Rerank documents based on relevance to query.
    
    **Input:**
    - query: Vietnamese search query
    - documents: List of candidate documents (max 100)
    - top_k: Number of top results to return (optional)
    
    **Output:**
    - results: Reranked documents with scores
    - processing_time: Time taken in seconds
    - model_name: Model used for reranking
    
    **Example:**
    ```
    POST /rerank
    {
      "query": "điều kiện thành lập công ty",
      "documents": [
        "Văn bản về điều kiện thành lập doanh nghiệp...",
        "Hướng dẫn đăng ký kinh doanh...",
        "Quy định về vốn điều lệ..."
      ],
      "top_k": 5
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Documents list cannot be empty"
            )
        
        if len(request.documents) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 documents allowed"
            )
        
        # Use provided top_k or default from settings
        top_k = request.top_k if request.top_k is not None else settings.top_k
        top_k = min(top_k, len(request.documents))
        
        # Perform reranking
        reranked = reranker.rerank(
            query=request.query,
            documents=request.documents,
            top_k=top_k,
            batch_size=settings.batch_size
        )
        
        # Build response
        results = [
            RerankResult(
                index=idx,
                text=text,
                score=score,
                rank=rank + 1
            )
            for rank, (idx, text, score) in enumerate(reranked)
        ]
        
        processing_time = time.time() - start_time
        
        return RerankResponse(
            results=results,
            processing_time=processing_time,
            model_name=settings.model_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reranking error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranking failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
