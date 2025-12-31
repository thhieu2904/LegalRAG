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
import gc
import torch

from .models import (
    RerankRequest,
    RerankResponse,
    RerankResult,
    DocumentScore,
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
    
    # GPU Swap Mode - for low VRAM environments (6-8GB)
    # When true: Load model on-demand, unload after use
    # When false: Load at startup, keep permanently (12GB+ VRAM)
    gpu_swap_mode: bool = False
    
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
model_loaded: bool = False


def load_model():
    """Load reranker model to GPU/CPU."""
    global reranker, model_loaded
    
    if model_loaded and reranker is not None:
        logger.info("Model already loaded")
        return
    
    logger.info(f"🔄 Loading reranker model to {settings.device}...")
    start = time.time()
    
    reranker = VietnameseReranker(
        model_name=settings.model_name,
        device=settings.device,
        max_length=settings.model_max_length,
        cache_dir=settings.model_cache_dir
    )
    
    model_loaded = True
    logger.info(f"✅ Reranker loaded in {time.time()-start:.2f}s on {settings.device.upper()}")


def unload_model():
    """Unload reranker model to free GPU memory."""
    global reranker, model_loaded
    
    if reranker is None:
        return
    
    logger.info("🔄 Unloading reranker model...")
    
    # Move model to CPU first if on GPU (helps with memory release)
    if settings.device == 'cuda' and hasattr(reranker, 'model'):
        try:
            if hasattr(reranker.model, 'model'):
                reranker.model.model.cpu()
        except Exception as e:
            logger.warning(f"Could not move model to CPU: {e}")
    
    # Delete model
    del reranker
    reranker = None
    model_loaded = False
    
    # Force cleanup
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    logger.info("✅ Reranker unloaded, VRAM freed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - load model based on swap mode."""
    global reranker, model_loaded
    
    logger.info("=" * 60)
    logger.info(f"Starting {settings.service_name}")
    logger.info("=" * 60)
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"Device: {settings.device}")
    logger.info(f"GPU Swap Mode: {settings.gpu_swap_mode}")
    logger.info(f"Batch Size: {settings.batch_size}")
    logger.info(f"Default Top-K: {settings.top_k}")
    logger.info("=" * 60)
    
    try:
        if not settings.gpu_swap_mode:
            # Non-swap mode: Load model immediately at startup
            logger.info("🚀 Non-swap mode: Loading Rerank model at startup")
            load_model()
        else:
            # Swap mode: Model will load on-demand
            logger.info("🔄 Swap mode: Rerank model will load on-demand")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize reranker: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown
    unload_model()
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
    global model_loaded
    
    # In swap mode, auto-load if needed
    if reranker is None or not model_loaded:
        if settings.gpu_swap_mode:
            load_model()
        else:
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
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and model information.
    """
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        model_loaded=model_loaded,
        device=settings.device,
        gpu_swap_mode=settings.gpu_swap_mode
    )


# ============================================
# GPU Swap Endpoints
# ============================================

@app.post("/prepare")
async def prepare_model():
    """
    Load model to GPU (for swap mode).
    Called by query-service before reranking.
    
    In non-swap mode, this is a no-op (model always loaded).
    """
    if not settings.gpu_swap_mode:
        return {
            "status": "ok",
            "message": "Non-swap mode, model always loaded",
            "model_loaded": model_loaded
        }
    
    load_model()
    return {
        "status": "ok",
        "loaded": True,
        "device": settings.device
    }


@app.post("/release")
async def release_model():
    """
    Unload model from GPU (for swap mode).
    Called by query-service after reranking to free VRAM for LLM.
    
    In non-swap mode, this is a no-op (model stays loaded).
    """
    if not settings.gpu_swap_mode:
        return {
            "status": "ok",
            "message": "Non-swap mode, model stays loaded",
            "model_loaded": model_loaded
        }
    
    unload_model()
    return {
        "status": "ok",
        "unloaded": True,
        "vram_freed": True
    }


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
    - document_ids: List of document IDs for document score aggregation
    - document_titles: List of document titles for title-aware reranking
    - top_k: Number of top chunks to return
    - include_document_scores: If True, return aggregated scores per document
    
    **Output:**
    - results: Top-K reranked chunks with scores
    - document_scores: Aggregated scores per document (for clarification logic)
    - processing_time: Time taken in seconds
    - model_name: Model used for reranking
    
    **Query-service uses document_scores to:**
    - If score_gap between top-1 and top-2 doc is large → answer directly
    - If score_gap is small → trigger clarification (ambiguous query)
    
    **Example:**
    ```
    POST /rerank
    {
      "query": "khai sinh cần gì",
      "documents": [...],
      "document_ids": ["doc_123", "doc_123", "doc_456", ...],
      "document_titles": ["Đăng ký khai sinh", "Đăng ký khai sinh", ...],
      "include_document_scores": true
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
        
        # Determine include_document_scores setting
        include_document_scores = request.include_document_scores if request.include_document_scores is not None else True
        
        # Perform reranking with new hybrid method
        reranked, doc_scores = reranker.rerank_with_scores(
            query=request.query,
            documents=request.documents,
            document_ids=request.document_ids,
            document_titles=request.document_titles,
            top_k=top_k,
            batch_size=settings.batch_size,
            include_document_scores=include_document_scores
        )
        
        # Build chunk results
        results = [
            RerankResult(
                index=idx,
                text=text,
                score=score,
                rank=rank + 1
            )
            for rank, (idx, text, score) in enumerate(reranked)
        ]
        
        # Build document scores if available
        document_scores = None
        if doc_scores:
            document_scores = [
                DocumentScore(
                    document_id=ds['document_id'],
                    avg_score=ds['avg_score'],
                    max_score=ds['max_score'],
                    chunk_count=ds['chunk_count']
                )
                for ds in doc_scores
            ]
        
        processing_time = time.time() - start_time
        
        return RerankResponse(
            results=results,
            document_scores=document_scores,
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
