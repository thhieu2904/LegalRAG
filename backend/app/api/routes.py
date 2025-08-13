from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import QueryRequest, QueryResponse, HealthResponse, IndexingRequest, IndexingResponse
from app.services.rag_engine import OptimizedEnhancedRAGService as RAGService
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Router sẽ được inject RAG service
router = APIRouter()

# Global RAG service instance (sẽ được thiết lập trong main.py)
rag_service: Optional[RAGService] = None

def get_rag_service():
    """Dependency để lấy RAG service"""
    if rag_service is None:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    return rag_service

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Endpoint để hỏi đáp với tài liệu - sử dụng cấu hình đã tối ưu"""
    try:
        result = rag.query(
            question=request.question,
            max_tokens=request.max_tokens or 2048,
            temperature=request.temperature or 0.1,  # Sử dụng temperature thấp mặc định
            broad_search_k=request.top_k or 15  # Map top_k to broad_search_k
        )
        
        return QueryResponse(
            answer=result['answer'],
            sources=result['sources'],
            source_files=result.get('source_files', []),
            processing_time=result['processing_time'],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check(rag: RAGService = Depends(get_rag_service)):
    """Endpoint kiểm tra tình trạng hệ thống với multi-collection support"""
    try:
        health_status = rag.get_health_status()
        
        return HealthResponse(
            status="healthy" if health_status['status'] == 'healthy' else "unhealthy",
            model_loaded=health_status['model_loaded'],
            vectordb_status=health_status['vectordb_status'],
            total_collections=health_status.get('total_collections', 0),
            total_documents=health_status.get('total_documents', 0),
            collections=health_status.get('collections', []),
            query_router_available=health_status.get('query_router_available', False)
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections")
async def list_collections(rag: RAGService = Depends(get_rag_service)):
    """Liệt kê tất cả collections và thông tin của chúng"""
    try:
        collections_info = rag.vectordb_service.list_collections()
        available_collections = rag.document_processor.get_available_collections(rag.documents_dir)
        
        return {
            'existing_collections': collections_info,
            'available_collections': available_collections,
            'total_collections': len(collections_info),
            'total_documents': sum(col['document_count'] for col in collections_info)
        }
        
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/routing/explain")
async def explain_query_routing(
    request: QueryRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Giải thích tại sao hệ thống chọn collection cụ thể cho câu hỏi"""
    try:
        if not hasattr(rag, 'query_router') or not rag.query_router:
            raise HTTPException(status_code=500, detail="Query router not available")
        
        explanation = rag.query_router.explain_routing(request.question)
        
        return {
            'query': request.question,
            'routing_explanation': explanation,
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error explaining routing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    try:
        health_status = rag.get_health_status()
        
        return HealthResponse(
            status=health_status['status'],
            version="1.0.0",
            model_loaded=health_status['model_loaded'],
            vectordb_status=health_status['vectordb_status']
        )
        
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index", response_model=IndexingResponse)
async def build_index(
    request: Optional[IndexingRequest] = None,
    rag: RAGService = Depends(get_rag_service)
):
    """Endpoint để xây dựng index cho tài liệu với cấu hình cải thiện"""
    try:
        force_rebuild = request.force_rebuild if request and request.force_rebuild is not None else False
        
        # Sử dụng cấu hình từ settings
        from app.core.config import settings
        result = rag.build_index(
            force_rebuild=force_rebuild,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap
        )
        
        return IndexingResponse(
            status=result['status'],
            collections_processed=result.get('collections_processed', 0),
            total_documents=result.get('total_documents', 0),
            total_chunks=result.get('total_chunks', 0),
            processing_time=result['processing_time'],
            collections_detail=result.get('collections_detail', {}),
            message=result['message']
        )
        
    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(rag: RAGService = Depends(get_rag_service)):
    """Endpoint để lấy thống kê hệ thống"""
    try:
        health_status = rag.get_health_status()
        return {
            "document_count": health_status.get('document_count', 0),
            "collection_name": health_status.get('collection_name', ''),
            "embedding_model": health_status.get('embedding_model', ''),
            "model_info": health_status.get('model_info', {}),
            "status": health_status.get('status', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
