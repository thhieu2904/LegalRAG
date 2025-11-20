"""
Vector Service Main API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

from .config import settings
from .database import VectorDatabase
from .models import (
    HealthResponse,
    VectorInsertRequest,
    VectorInsertResponse,
    VectorBatchInsertRequest,
    VectorBatchInsertResponse,
    SearchRequest,
    SearchResponse,
    VectorDeleteRequest,
    DeleteResponse,
    VectorCountResponse
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize app
app = FastAPI(
    title="Vector Service",
    description="Vector search using PostgreSQL pgvector",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database instance
db: VectorDatabase = None


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    global db
    
    logger.info("🚀 Starting Vector Service...")
    
    # Initialize database
    db = VectorDatabase(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB
    )
    
    # Connect with retries
    max_retries = 10
    for attempt in range(max_retries):
        if db.connect():
            logger.info("✅ Vector Service started")
            return
        logger.warning(f"⏳ Connection attempt {attempt + 1}/{max_retries} failed...")
        await asyncio.sleep(1)
    
    raise RuntimeError("Failed to connect to database")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global db
    if db:
        db.disconnect()
    logger.info("✅ Vector Service stopped")


# ============= HEALTH CHECK =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if db is None:
        return HealthResponse(status="unhealthy", db="disconnected", pgvector="unavailable")
    
    if db.health_check():
        return HealthResponse(status="healthy", db="connected", pgvector="available")
    else:
        return HealthResponse(status="unhealthy", db="disconnected", pgvector="unavailable")


# ============= INSERT OPERATIONS =============

@app.post("/insert", response_model=VectorInsertResponse)
async def insert_vector(request: VectorInsertRequest):
    """Insert single vector with embedding"""
    try:
        vector_id = db.insert_chunk(
            document_id=request.document_id,
            chunk_index=request.chunk_index,
            content=request.content,
            embedding=request.embedding,
            section_title=request.section_title,
            source_reference=request.source_reference,
            token_count=request.token_count,
            metadata=request.metadata
        )
        
        return VectorInsertResponse(
            success=True,
            vector_id=vector_id,
            message="Vector inserted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insert-batch", response_model=VectorBatchInsertResponse)
async def insert_batch(request: VectorBatchInsertRequest):
    """
    Insert multiple vector chunks (AICenter Pattern)
    
    IMPORTANT: Document must already exist in documents table.
    Admin Service creates document BEFORE calling this endpoint.
    This endpoint ONLY inserts chunks.
    """
    try:
        logger.info(f"📥 /insert-batch: {len(request.vectors)} chunks for doc {request.vectors[0].document_id if request.vectors else 'unknown'}")
        
        # AICenter Pattern: Only insert chunks, document already exists
        result = db.insert_batch_chunks_only(
            chunks=[v.dict() for v in request.vectors]
        )
        
        return VectorBatchInsertResponse(
            success=result["inserted"] > 0,
            inserted=result["inserted"],
            failed=result["failed"],
            total=result["total"]
        )
    except Exception as e:
        logger.error(f"❌ Batch insert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= SEARCH OPERATIONS =============

@app.post("/search", response_model=SearchResponse)
async def search_vectors(request: SearchRequest):
    """Search similar vectors"""
    try:
        results = db.search_similar(
            embedding=request.embedding,
            top_k=request.top_k,
            threshold=request.threshold,
            document_ids=request.document_ids
        )
        
        return SearchResponse(
            success=True,
            results=results,
            total=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= DELETE OPERATIONS =============

@app.post("/delete", response_model=DeleteResponse)
async def delete_vectors(request: VectorDeleteRequest):
    """Delete vectors (soft delete)"""
    try:
        deleted = db.delete_vectors(
            vector_ids=request.vector_ids,
            document_id=request.document_id
        )
        
        return DeleteResponse(
            success=True,
            deleted=deleted,
            message=f"Deleted {deleted} vectors"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= COUNT OPERATIONS =============

@app.get("/count", response_model=VectorCountResponse)
async def count_vectors():
    """Get vector count statistics"""
    try:
        counts = db.count_vectors()
        
        return VectorCountResponse(
            success=True,
            total_vectors=counts["total_vectors"],
            total_documents=counts["total_documents"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= ROOT ENDPOINT =============

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "vector-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "insert": "POST /insert",
            "insert_batch": "POST /insert-batch",
            "search": "POST /search",
            "delete": "POST /delete",
            "count": "GET /count",
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
