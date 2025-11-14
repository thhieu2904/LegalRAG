"""
Embedding Service - Local sentence-transformers model
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
import numpy as np

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global model
model = None


# ============= MODELS =============

class EmbedRequest(BaseModel):
    """Embedding request"""
    text: str


class EmbedBatchRequest(BaseModel):
    """Batch embedding request"""
    texts: List[str]


class EmbedResponse(BaseModel):
    """Embedding response"""
    success: bool
    embedding: List[float]
    dimension: int


class EmbedBatchResponse(BaseModel):
    """Batch embedding response"""
    success: bool
    embeddings: List[List[float]]
    total: int
    dimension: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    device: str


# ============= APP =============

app = FastAPI(
    title="Embedding Service",
    description="Text embedding using local sentence-transformers model",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Load model on startup"""
    global model
    
    logger.info(f"🚀 Loading embedding model: {settings.MODEL_NAME}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(
            settings.MODEL_NAME,
            cache_folder=settings.MODEL_CACHE_DIR,
            device=settings.DEVICE
        )
        
        logger.info(f"✅ Model loaded on device: {settings.DEVICE}")
        logger.info(f"✅ Embedding Service started")
    
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global model
    if model:
        del model
    logger.info("✅ Embedding Service stopped")


# ============= ENDPOINTS =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy" if model else "unhealthy",
        model_loaded=model is not None,
        device=settings.DEVICE
    )


@app.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """Embed single text"""
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Embed
        embedding = model.encode(request.text).tolist()
        
        return EmbedResponse(
            success=True,
            embedding=embedding,
            dimension=len(embedding)
        )
    
    except Exception as e:
        logger.error(f"❌ Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed-batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    """Embed multiple texts"""
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Embed in batches
        embeddings = model.encode(
            request.texts,
            batch_size=settings.BATCH_SIZE,
            convert_to_numpy=True
        )
        
        # Convert to lists
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        return EmbedBatchResponse(
            success=True,
            embeddings=embeddings_list,
            total=len(embeddings_list),
            dimension=len(embeddings_list[0]) if embeddings_list else 0
        )
    
    except Exception as e:
        logger.error(f"❌ Batch embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "embedding-service",
        "model": settings.MODEL_NAME,
        "device": settings.DEVICE,
        "dimension": settings.EMBEDDING_DIMENSION,
        "endpoints": {
            "health": "/health",
            "embed": "POST /embed",
            "embed_batch": "POST /embed-batch",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
