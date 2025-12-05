"""LLM Service - Multi-Provider Support (Local Vistral / Gemini API)

Provider Pattern cho phép chuyển đổi giữa các LLM backends:
- LLM_PROVIDER=local → Vistral 7B với llama-cpp-python (requires GPU)
- LLM_PROVIDER=gemini → Google Gemini API (no GPU required)

Endpoints giữ nguyên API contract để query-service không cần thay đổi.
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import settings
from .models import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
)
from .services.prompt_builder import prompt_builder
from .providers.base import BaseLLMProvider

# ============================================
# Logging Setup
# ============================================

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================
# Global State - LLM Provider Instance
# ============================================

llm_provider: Optional[BaseLLMProvider] = None


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function để lấy LLM provider instance.
    
    Provider được chọn dựa trên LLM_PROVIDER env variable:
    - "local" → LocalProvider (Vistral 7B)
    - "gemini" → GeminiProvider (Gemini API)
    """
    global llm_provider
    
    if llm_provider is None:
        if settings.llm_provider == "gemini":
            from .providers.gemini_provider import GeminiProvider
            llm_provider = GeminiProvider()
            logger.info("Using Gemini Provider")
        else:
            from .providers.local_provider import LocalProvider
            llm_provider = LocalProvider()
            logger.info("Using Local Provider (Vistral 7B)")
    
    return llm_provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize provider on startup."""
    global llm_provider
    
    logger.info("=" * 60)
    logger.info(f"Starting {settings.service_name}")
    logger.info(f"Provider: {settings.llm_provider}")
    logger.info("=" * 60)
    
    try:
        # Initialize provider
        provider = get_llm_provider()
        await provider.initialize()
        
        logger.info("=" * 60)
        logger.info(f"✓ {settings.service_name} ready")
        logger.info(f"✓ Provider: {provider.provider_name}")
        logger.info(f"✓ Model: {provider.model_name}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize provider: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.service_name}")
    if llm_provider:
        await llm_provider.shutdown()
    logger.info("✓ Shutdown complete")


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title=settings.service_name,
    description="Vietnamese Legal LLM Service - Multi-Provider Support",
    version="2.0.0",
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
# API Endpoints
# ============================================

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    provider = get_llm_provider()
    return {
        "service": settings.service_name,
        "provider": provider.provider_name,
        "model": provider.model_name,
        "status": "running" if provider.is_ready else "initializing",
        "version": "2.0.0",
        "endpoints": {
            "health": "GET /health",
            "generate": "POST /generate",
            "generate_rag": "POST /generate-rag",
            "docs": "GET /docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status và provider information.
    """
    provider = get_llm_provider()
    health = await provider.health_check()
    
    return HealthResponse(
        status=health.get("status", "unknown"),
        service=settings.service_name,
        model_loaded=provider.is_ready,
        model_name=provider.model_name,
        device=settings.device if settings.llm_provider == "local" else "api",
        n_ctx=settings.n_ctx if settings.llm_provider == "local" else 0,
        provider=provider.provider_name
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text using current LLM provider (raw prompt, no system wrapping).
    
    For RAG queries with automatic system prompt wrapping, use /generate-rag instead.
    """
    provider = get_llm_provider()
    
    if not provider.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider ({provider.provider_name}) not ready"
        )
    
    try:
        result = await provider.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            stop=request.stop
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Generation failed: {result.error}"
            )
        
        return GenerateResponse(
            success=True,
            text=result.text,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            model=result.model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


# ============================================
# RAG-Optimized Generation Endpoint
# ============================================

class RAGGenerateRequest(BaseModel):
    """Request for RAG generation with automatic system prompt wrapping."""
    question: str  # User's original question
    context: str  # Retrieved context from vector search
    history: Optional[List[dict]] = None  # Chat history (optional)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None
    stop: Optional[list[str]] = None


@app.post("/generate-rag", response_model=GenerateResponse)
async def generate_rag(request: RAGGenerateRequest):
    """
    Generate RAG response with automatic system prompt wrapping.
    
    This endpoint:
    1. Takes question + context from query service
    2. Automatically wraps with system_prompt.txt + citation_rules.txt
    3. Uses appropriate prompt format for current provider
    4. Generates response with proper guardrails against hallucination
    
    **Input:**
    - question: User's original question
    - context: Retrieved documents/chunks from vector search
    - history: Chat history (optional)
    - max_tokens, temperature, etc.: Generation parameters
    
    **Output:**
    - success: Whether generation succeeded
    - text: Generated text with citations
    - prompt_tokens, completion_tokens, total_tokens: Token counts
    - model: Model name
    """
    provider = get_llm_provider()
    
    if not provider.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider ({provider.provider_name}) not ready"
        )
    
    try:
        # Build prompt using appropriate format for provider
        formatted_prompt = prompt_builder.build_prompt_for_provider(
            question=request.question,
            context=request.context,
            history=request.history,
            provider=settings.llm_provider
        )
        
        logger.info(f"RAG Generation - Provider: {provider.provider_name}")
        logger.info(f"RAG Generation - Question: {request.question[:100]}...")
        logger.debug(f"Full Prompt:\n{formatted_prompt[:500]}...")
        
        # Generate response
        result = await provider.generate(
            prompt=formatted_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            stop=request.stop,
            repeat_penalty=request.repeat_penalty
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"RAG Generation failed: {result.error}"
            )
        
        logger.info(f"Generated {result.completion_tokens} tokens")
        
        return GenerateResponse(
            success=True,
            text=result.text,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            model=result.model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG Generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG Generation failed: {str(e)}"
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
