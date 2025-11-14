"""
RAG SERVICE INTERNAL ENDPOINTS - Cache & VectorDB Management
============================================================

These endpoints are called by Admin Service to maintain consistency
after questions are updated.

⚠️ These are INTERNAL endpoints - should not be exposed publicly!
   Use API gateway or firewall rules to restrict access.

Add these endpoints to rag_service/app/api/internal.py (create new file)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/internal", tags=["internal"])

# ==================== DATA MODELS ====================

class CacheInvalidationRequest(BaseModel):
    """Request to invalidate cache for specific document"""
    collection: str
    doc_id: str
    cache_types: List[str] = Field(
        default=["router", "metadata"],
        description="Types of cache to invalidate: router, metadata, embeddings"
    )

class VectorDBRebuildRequest(BaseModel):
    """Request to rebuild VectorDB for specific document"""
    collection: str
    doc_id: str
    rebuild_scope: str = Field(
        default="document",
        description="Scope of rebuild: document, collection, or all"
    )
    async_mode: bool = Field(
        default=True,
        description="Run rebuild in background"
    )

class InternalResponse(BaseModel):
    """Response for internal operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None

# ==================== CACHE INVALIDATION ====================

@router.post(
    "/cache/invalidate",
    response_model=InternalResponse,
    summary="Invalidate cache for updated questions"
)
async def invalidate_cache(request: CacheInvalidationRequest):
    """
    Invalidate cache entries for a document after questions update
    
    This endpoint is called by Admin Service after updating questions
    to ensure cache consistency.
    
    Cache types:
    - router: Router cache (question matching)
    - metadata: Document metadata cache
    - embeddings: Embedding cache (if applicable)
    
    Args:
        request: Cache invalidation request
        
    Returns:
        Success response with invalidated cache info
    """
    try:
        start_time = datetime.now()
        logger.info(f"🔄 Invalidating cache for {request.collection}/{request.doc_id}")
        
        invalidated_caches = []
        
        # Get RAG service instance (injected dependency)
        from ...main import rag_service
        
        # Invalidate router cache
        if "router" in request.cache_types:
            try:
                # Access router service
                router_service = rag_service.router_service
                
                # Remove cached entries for this document
                cache_key = f"{request.collection}:{request.doc_id}"
                
                # Method 1: Clear specific document from cache
                if hasattr(router_service, 'clear_document_cache'):
                    router_service.clear_document_cache(request.collection, request.doc_id)
                    invalidated_caches.append("router_document")
                    logger.info(f"✅ Router cache cleared for {cache_key}")
                
                # Method 2: Clear entire collection cache
                elif hasattr(router_service, 'clear_collection_cache'):
                    router_service.clear_collection_cache(request.collection)
                    invalidated_caches.append("router_collection")
                    logger.info(f"✅ Router cache cleared for collection {request.collection}")
                
                # Method 3: Force reload router cache
                elif hasattr(router_service, 'reload_cache'):
                    await router_service.reload_cache()
                    invalidated_caches.append("router_full_reload")
                    logger.info(f"✅ Router cache fully reloaded")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to invalidate router cache: {e}")
        
        # Invalidate metadata cache
        if "metadata" in request.cache_types:
            try:
                # Clear document metadata from cache
                if hasattr(rag_service, 'metadata_cache'):
                    cache_key = f"{request.collection}:{request.doc_id}"
                    if cache_key in rag_service.metadata_cache:
                        del rag_service.metadata_cache[cache_key]
                        invalidated_caches.append("metadata")
                        logger.info(f"✅ Metadata cache cleared for {cache_key}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to invalidate metadata cache: {e}")
        
        # Invalidate embeddings cache (if needed)
        if "embeddings" in request.cache_types:
            try:
                # Clear cached embeddings for this document
                vector_service = rag_service.vector_service
                
                if hasattr(vector_service, 'clear_document_embeddings'):
                    vector_service.clear_document_embeddings(request.collection, request.doc_id)
                    invalidated_caches.append("embeddings")
                    logger.info(f"✅ Embeddings cache cleared")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to invalidate embeddings cache: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return InternalResponse(
            success=True,
            message=f"Cache invalidated for {request.collection}/{request.doc_id}",
            data={
                "collection": request.collection,
                "doc_id": request.doc_id,
                "invalidated_caches": invalidated_caches,
                "cache_types_requested": request.cache_types
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Cache invalidation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache invalidation failed: {str(e)}"
        )

# ==================== VECTORDB REBUILD ====================

async def _rebuild_document_vectordb(collection: str, doc_id: str):
    """
    Background task to rebuild VectorDB for a single document
    
    This rebuilds only the affected document chunks with updated questions.
    """
    try:
        logger.info(f"🔨 Starting VectorDB rebuild for {collection}/{doc_id}")
        
        from ...main import vector_service
        from ...services.vector import VectorDBService
        from pathlib import Path
        
        # Get document directory
        storage_dir = Path("data/storage/collections")
        doc_dir = storage_dir / collection / "documents" / doc_id
        
        if not doc_dir.exists():
            logger.error(f"❌ Document directory not found: {doc_dir}")
            return
        
        # Find document JSON file (exclude questions.json)
        json_files = [f for f in doc_dir.glob("*.json") if f.name != "questions.json"]
        
        if not json_files:
            logger.error(f"❌ No document JSON found in {doc_dir}")
            return
        
        document_file = json_files[0]
        
        # Load questions.json
        questions_file = doc_dir / "questions.json"
        questions_data = {}
        
        if questions_file.exists():
            import json
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
        
        # Load document content
        with open(document_file, 'r', encoding='utf-8') as f:
            import json
            document_data = json.load(f)
        
        # Create document metadata with updated questions
        doc_metadata = {
            "collection": collection,
            "doc_id": doc_id,
            "source": str(document_file),
            "questions": questions_data,  # Updated questions
            **document_data  # Include all document fields
        }
        
        # Delete old chunks for this document from VectorDB
        vector_service.delete_document_chunks(collection, doc_id)
        logger.info(f"🗑️ Deleted old chunks for {collection}/{doc_id}")
        
        # Re-index document with new questions
        await vector_service.add_document(
            collection=collection,
            doc_id=doc_id,
            metadata=doc_metadata
        )
        
        logger.info(f"✅ VectorDB rebuild completed for {collection}/{doc_id}")
        
    except Exception as e:
        logger.error(f"❌ VectorDB rebuild failed for {collection}/{doc_id}: {e}")

@router.post(
    "/vectordb/rebuild",
    response_model=InternalResponse,
    summary="Rebuild VectorDB after questions update"
)
async def rebuild_vectordb(
    request: VectorDBRebuildRequest,
    background_tasks: BackgroundTasks
):
    """
    Rebuild VectorDB for documents with updated questions
    
    This endpoint is called by Admin Service after updating questions
    to re-index affected documents with new fused content.
    
    Rebuild scopes:
    - document: Rebuild only the specified document (RECOMMENDED)
    - collection: Rebuild all documents in the collection
    - all: Rebuild entire VectorDB (EXPENSIVE - avoid!)
    
    Args:
        request: VectorDB rebuild request
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response with rebuild status
    """
    try:
        logger.info(
            f"🔨 VectorDB rebuild requested: "
            f"{request.collection}/{request.doc_id} (scope: {request.rebuild_scope})"
        )
        
        if request.rebuild_scope == "document":
            # Rebuild single document (RECOMMENDED)
            if request.async_mode:
                background_tasks.add_task(
                    _rebuild_document_vectordb,
                    request.collection,
                    request.doc_id
                )
                
                return InternalResponse(
                    success=True,
                    message=f"VectorDB rebuild queued for {request.collection}/{request.doc_id}",
                    data={
                        "collection": request.collection,
                        "doc_id": request.doc_id,
                        "rebuild_scope": request.rebuild_scope,
                        "status": "queued"
                    }
                )
            else:
                # Synchronous rebuild (blocks request)
                await _rebuild_document_vectordb(request.collection, request.doc_id)
                
                return InternalResponse(
                    success=True,
                    message=f"VectorDB rebuild completed for {request.collection}/{request.doc_id}",
                    data={
                        "collection": request.collection,
                        "doc_id": request.doc_id,
                        "rebuild_scope": request.rebuild_scope,
                        "status": "completed"
                    }
                )
        
        elif request.rebuild_scope == "collection":
            # Rebuild entire collection
            # TODO: Implement collection-level rebuild
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Collection-level rebuild not implemented yet"
            )
        
        elif request.rebuild_scope == "all":
            # Rebuild entire VectorDB (VERY EXPENSIVE)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full VectorDB rebuild not allowed via this endpoint. Use CLI tools."
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rebuild_scope: {request.rebuild_scope}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ VectorDB rebuild error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"VectorDB rebuild failed: {str(e)}"
        )

# ==================== HEALTH CHECK ====================

@router.get(
    "/health",
    response_model=InternalResponse,
    summary="Internal health check"
)
async def health_check():
    """
    Health check for internal services
    
    Returns:
        Service health status
    """
    try:
        from ...main import rag_service, vector_service
        
        health_status = {
            "rag_service": "healthy" if rag_service else "not_initialized",
            "vector_service": "healthy" if vector_service else "not_initialized",
            "router_service": "healthy" if hasattr(rag_service, 'router_service') else "not_available"
        }
        
        all_healthy = all(status == "healthy" for status in health_status.values())
        
        return InternalResponse(
            success=all_healthy,
            message="Internal services health check",
            data=health_status
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

# ==================== CACHE STATISTICS ====================

@router.get(
    "/cache/stats",
    response_model=InternalResponse,
    summary="Get cache statistics"
)
async def get_cache_stats():
    """
    Get statistics about cache usage
    
    Useful for monitoring and debugging cache behavior
    
    Returns:
        Cache statistics
    """
    try:
        from ...main import rag_service
        
        stats = {
            "router_cache": {},
            "metadata_cache": {},
            "embeddings_cache": {}
        }
        
        # Router cache stats
        if hasattr(rag_service, 'router_service'):
            router_service = rag_service.router_service
            
            if hasattr(router_service, 'get_cache_stats'):
                stats["router_cache"] = router_service.get_cache_stats()
        
        # Metadata cache stats
        if hasattr(rag_service, 'metadata_cache'):
            stats["metadata_cache"] = {
                "size": len(rag_service.metadata_cache),
                "keys": list(rag_service.metadata_cache.keys())[:10]  # First 10
            }
        
        # Vector service stats
        if hasattr(rag_service, 'vector_service'):
            vector_service = rag_service.vector_service
            
            if hasattr(vector_service, 'get_stats'):
                stats["vector_service"] = vector_service.get_stats()
        
        return InternalResponse(
            success=True,
            message="Cache statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )

# ==================== CONFIGURATION ====================

"""
To enable these endpoints, add to rag_service/main.py:

from app.api import internal

app.include_router(internal.router)

Then configure security (IMPORTANT!):

1. Option A: API Key authentication
   
   from fastapi import Header, HTTPException
   
   async def verify_internal_api_key(
       x_internal_api_key: str = Header(...)
   ):
       if x_internal_api_key != settings.INTERNAL_API_KEY:
           raise HTTPException(status_code=401)
   
   router = APIRouter(
       prefix="/api/internal",
       dependencies=[Depends(verify_internal_api_key)]
   )

2. Option B: IP whitelist
   
   from fastapi import Request
   
   ALLOWED_IPS = ["127.0.0.1", "localhost", "172.17.0.1"]  # Docker
   
   async def verify_internal_ip(request: Request):
       client_ip = request.client.host
       if client_ip not in ALLOWED_IPS:
           raise HTTPException(status_code=403)
   
   router = APIRouter(
       prefix="/api/internal",
       dependencies=[Depends(verify_internal_ip)]
   )

3. Option C: Network isolation (Docker)
   
   # Only allow admin_service container to access
   # Use Docker internal network
   # Don't expose internal endpoints to host
"""

# ==================== USAGE EXAMPLES ====================

"""
Example API calls from Admin Service:

1. Invalidate cache after update:
POST http://rag_service:8000/api/internal/cache/invalidate
{
  "collection": "quy_trinh_boi_thuong_nn",
  "doc_id": "DOC_001",
  "cache_types": ["router", "metadata"]
}

2. Rebuild VectorDB (async):
POST http://rag_service:8000/api/internal/vectordb/rebuild
{
  "collection": "quy_trinh_boi_thuong_nn",
  "doc_id": "DOC_001",
  "rebuild_scope": "document",
  "async_mode": true
}

3. Check health:
GET http://rag_service:8000/api/internal/health

4. Get cache stats:
GET http://rag_service:8000/api/internal/cache/stats
"""
