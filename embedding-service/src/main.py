"""
Embedding Service - Vietnamese Document Embedding
Model: dangvantuan/vietnamese-document-embedding (768 dims, 8192 tokens)
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import numpy as np

from .config import settings
from .models import (
    EmbedRequest,
    EmbedBatchRequest,
    ChunkAndEmbedRequest,
    EmbedResponse,
    EmbedBatchResponse,
    ChunkAndEmbedResponse,
    ChunkInfo,
    ChunkWithEmbedding,
    HealthResponse,
)
from .auth import verify_admin_key

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global model and chunker
model = None
chunker = None


# ============= APP =============

app = FastAPI(
    title="Embedding Service",
    description="Vietnamese Document Embedding with Legal Document Chunking",
    version="2.0.0"
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
    """Load model and chunker on startup"""
    global model, chunker
    
    logger.info(f"🚀 Loading Vietnamese embedding model: {settings.MODEL_NAME}")
    
    try:
        from sentence_transformers import SentenceTransformer
        from .chunking import LegalDocumentChunker  # Uses UniversalDocumentChunker via alias
        
        # Load embedding model
        model = SentenceTransformer(
            settings.MODEL_NAME,
            cache_folder=settings.MODEL_CACHE_DIR,
            device=settings.DEVICE,
            trust_remote_code=True
        )
        
        # Initialize chunker
        chunker = LegalDocumentChunker(
            model_name=settings.MODEL_NAME,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        
        logger.info(f"✅ Model loaded on device: {settings.DEVICE}")
        logger.info(f"✅ Model dimension: {settings.EMBEDDING_DIMENSION}")
        logger.info(f"✅ Max sequence length: {settings.MAX_SEQ_LENGTH}")
        logger.info(f"✅ Chunker configured: {settings.CHUNK_SIZE} tokens/chunk, {settings.CHUNK_OVERLAP} overlap")
        logger.info(f"✅ Embedding Service started")
    
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global model, chunker
    if model:
        del model
    if chunker:
        del chunker
    logger.info("🛑 Embedding Service stopped")


# ============= HEALTH CHECK =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health"""
    global model
    
    return HealthResponse(
        status="healthy" if model else "unhealthy",
        service=settings.SERVICE_NAME,
        model_loaded=model is not None,
        model_name=settings.MODEL_NAME,
        device=settings.DEVICE,
        embedding_dimension=settings.EMBEDDING_DIMENSION,
        max_seq_length=settings.MAX_SEQ_LENGTH
    )


# ============= PUBLIC ENDPOINTS =============

@app.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """
    Embed single text (for user queries)
    
    Public endpoint - no authentication required
    Use case: User asks question → embed query → search vectors
    """
    global model, chunker
    
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Encode text
        embedding = model.encode(request.text, convert_to_numpy=True)
        
        # Count tokens
        tokens = chunker.count_tokens(request.text) if chunker else 0
        
        logger.info(f"✅ Embedded text: {len(request.text)} chars, {tokens} tokens")
        
        return EmbedResponse(
            success=True,
            embedding=embedding.tolist(),
            dimension=len(embedding),
            tokens=tokens
        )
    
    except Exception as e:
        logger.error(f"❌ Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed-batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    """
    Embed multiple texts (for batch queries)
    
    Public endpoint - no authentication required
    Use case: Multiple queries at once
    """
    global model
    
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    try:
        # Encode all texts
        embeddings = model.encode(
            request.texts,
            batch_size=settings.BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        logger.info(f"✅ Embedded {len(request.texts)} texts")
        
        return EmbedBatchResponse(
            success=True,
            embeddings=embeddings.tolist(),
            total=len(embeddings),
            dimension=embeddings.shape[1]
        )
    
    except Exception as e:
        logger.error(f"❌ Batch embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= ADMIN ENDPOINT =============

@app.post("/chunk-and-embed", response_model=ChunkAndEmbedResponse, dependencies=[Depends(verify_admin_key)])
async def chunk_and_embed(request: ChunkAndEmbedRequest):
    """
    Chunk document and create embeddings (ADMIN ONLY)
    
    Protected endpoint - requires X-API-Key header
    
    Flow:
      1. Admin-service calls storage-service → gets cleaned text
      2. Admin-service calls this endpoint with cleaned text
      3. This service chunks text by legal structure
      4. This service creates embeddings for each chunk
      5. Returns chunks + embeddings to admin-service
      6. Admin-service stores in PostgreSQL
    
    Args:
        text: Cleaned plaintext from storage-service
        document_id: Document identifier
        metadata: Optional metadata from admin-service
        add_overlap: Whether to add overlap between chunks
    
    Returns:
        Chunks with embeddings and metadata
    """
    global model, chunker
    
    if not model or not chunker:
        raise HTTPException(status_code=503, detail="Model or chunker not loaded")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided")
    
    try:
        # Step 1: Chunk text with legal structure awareness
        chunks = chunker.chunk_text(request.text, add_overlap=request.add_overlap)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Chunking produced no results")
        
        # Step 2: Extract text from chunks for embedding
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        # Step 3: Create embeddings for all chunks
        embeddings = model.encode(
            chunk_texts,
            batch_size=settings.BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        # Step 4: Combine chunks with embeddings
        results = []
        for chunk_data, embedding in zip(chunks, embeddings):
            chunk_info = ChunkInfo(
                text=chunk_data['text'],
                tokens=chunk_data['tokens'],
                chunk_index=chunk_data['chunk_index'],
                chapter=chunk_data['chapter'],
                article=chunk_data['article'],
                section=chunk_data['section'],
                type=chunk_data['type']
            )
            
            results.append(ChunkWithEmbedding(
                chunk_info=chunk_info,
                embedding=embedding.tolist()
            ))
        
        logger.info(f"✅ Processed document: {len(results)} chunks, {len(request.text)} chars")
        
        return ChunkAndEmbedResponse(
            success=True,
            document_id=request.document_id,
            total_chunks=len(results),
            chunks=results,
            dimension=embeddings.shape[1],
            metadata=request.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chunk and embed failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= INFO ENDPOINT =============

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "embedding-service",
        "version": "2.0.0",
        "model": settings.MODEL_NAME,
        "dimension": settings.EMBEDDING_DIMENSION,
        "max_tokens": settings.MAX_SEQ_LENGTH,
        "endpoints": {
            "public": {
                "embed": "POST /embed - Embed single text (queries)",
                "embed_batch": "POST /embed-batch - Embed multiple texts"
            },
            "admin": {
                "chunk_and_embed": "POST /chunk-and-embed - Chunk document and embed (requires X-API-Key)"
            },
            "health": "GET /health",
            "docs": "GET /docs"
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
