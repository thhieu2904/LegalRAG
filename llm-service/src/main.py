"""
LLM Service - PhoGPT with llama-cpp-python
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ErrorResponse
)
from .services.prompt_builder import prompt_builder

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

llm: Optional[any] = None  # Llama model instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - load model on startup."""
    global llm
    
    logger.info("=" * 60)
    logger.info(f"Starting {settings.service_name}")
    logger.info("=" * 60)
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"Model Path: {settings.model_path}")
    logger.info(f"Device: {settings.device}")
    logger.info(f"Context Window: {settings.n_ctx}")
    logger.info(f"GPU Layers: {settings.n_gpu_layers}")
    logger.info("=" * 60)
    
    try:
        from llama_cpp import Llama
        
        # Check if model file exists
        if not os.path.exists(settings.model_path):
            logger.warning(f"Model file not found: {settings.model_path}")
            logger.info("Run download_model.py to download PhoGPT model")
            raise FileNotFoundError(f"Model file not found: {settings.model_path}")
        
        # Load PhoGPT model with llama-cpp-python
        logger.info("Loading PhoGPT model (this may take a minute)...")
        llm = Llama(
            model_path=settings.model_path,
            n_ctx=settings.n_ctx,
            n_gpu_layers=settings.n_gpu_layers if settings.device == "cuda" else 0,
            n_threads=settings.n_threads,
            n_batch=settings.n_batch,
            use_mmap=settings.use_mmap,
            use_mlock=settings.use_mlock,
            verbose=settings.verbose
        )
        
        logger.info("✓ PhoGPT model loaded successfully")
        logger.info(f"✓ Using device: {settings.device}")
        if settings.device == "cuda" and settings.n_gpu_layers == -1:
            logger.info("✓ All layers loaded on GPU")
        elif settings.device == "cuda":
            logger.info(f"✓ {settings.n_gpu_layers} layers on GPU")
        
    except ImportError as e:
        logger.error(f"✗ llama-cpp-python not installed: {e}")
        logger.error("Install with: pip install llama-cpp-python")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to load model: {e}")
        raise
    
    yield
    
    logger.info(f"Shutting down {settings.service_name}")
    if llm:
        del llm


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title=settings.service_name,
    description="Vietnamese Legal LLM using PhoGPT-4B with llama-cpp",
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

def get_llm():
    """Dependency to get LLM instance."""
    if llm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM model not loaded. Please ensure model file exists."
        )
    return llm


# ============================================
# API Endpoints
# ============================================

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "model": settings.model_name,
        "device": settings.device,
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "generate": "POST /generate",
            "docs": "GET /docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and model information.
    """
    return HealthResponse(
        status="healthy" if llm is not None else "unhealthy",
        service=settings.service_name,
        model_loaded=llm is not None,
        model_name=settings.model_name,
        device=settings.device,
        n_ctx=settings.n_ctx
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(
    request: GenerateRequest,
    llm_model = Depends(get_llm)
):
    """
    Generate text using PhoGPT-4B.
    
    **Input:**
    - prompt: Vietnamese text prompt
    - max_tokens: Maximum tokens to generate (optional)
    - temperature: Sampling temperature 0-2 (optional)
    - top_p: Nucleus sampling threshold (optional)
    - top_k: Top-K sampling (optional)
    - repeat_penalty: Penalty for repetition (optional)
    - stop: Stop sequences (optional)
    
    **Output:**
    - success: Whether generation succeeded
    - text: Generated text
    - prompt_tokens: Input token count
    - completion_tokens: Generated token count
    - total_tokens: Total token count
    - model: Model name
    
    **Example:**
    ```
    POST /generate
    {
      "prompt": "Điều kiện thành lập công ty TNHH là gì?",
      "max_tokens": 512,
      "temperature": 0.7
    }
    ```
    """
    try:
        # Use defaults from settings if not provided
        max_tokens = request.max_tokens or settings.max_tokens
        temperature = request.temperature or settings.temperature
        top_p = request.top_p or settings.top_p
        top_k = request.top_k or settings.top_k
        repeat_penalty = request.repeat_penalty or settings.repeat_penalty
        
        # Format prompt cho Vistral (Vietnamese instruction format)
        # Vistral-7B-Chat được train với format đơn giản: prompt trực tiếp
        # KHÔNG cần wrap như PhoGPT vì đã có system instructions trong prompt
        formatted_prompt = request.prompt
        
        # Generate với llama-cpp-python
        output = llm_model(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=request.stop or ["---", "## ", "Người dùng:", "CÂU HỎI"],
            echo=False  # Don't include prompt in output
        )
        
        # Extract generated text
        generated_text = output["choices"][0]["text"].strip()
        
        # Token counts
        prompt_tokens = output["usage"]["prompt_tokens"]
        completion_tokens = output["usage"]["completion_tokens"]
        
        return GenerateResponse(
            success=True,
            text=generated_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=settings.model_name
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
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
