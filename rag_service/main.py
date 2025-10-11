"""
Optimized Enhanced Main.py với VRAM-optimized architecture
- Embedding Model: CPU (tiết kiệm VRAM)
- LLM:    - **Em    -    - **LLM Model**: GPU (tận dụng song song hóa cho context dài)  
    - **Reranker Model**: GPU (tận dụng song song hóa cho multiple comparisons)
    
    ## 🔥 **Enhanced Features:** Model**: GPU (tận dụng song song hóa cho multiple comparisons)
    
    ## 🔥 **Enhanced Features:**
    - **🎯 Smart Ambiguous Detection**: Tự động phát hiện câu hỏi mơ hồ
    - **🧩 Nucleus Context Expansion**: Mở rộng context từ chunk chính xác nhất
    - **💾 Session Management**: Quản lý hội thoại thông minh
    - **⚡ VRAM-Optimized**: Giảm 0.5-1GB VRAM usage
    - **🎛️ Hybrid Retrieval**: Broad search + Reranking + Context expansion**Enhanced Features:**odel**: CPU (tiết kiệm VRAM cho queries ngắn)
    - **LLM Model**: GPU (tận dụng song song hóa cho context dài)  
    - **Reranker Model**: GPU (tận dụng song song hóa cho multiple comparisons)
    
    ## 🔥 **Enhanced Features:**
    - **🎯 Smart Ambiguous Detection**: Tự động phát hiện câu hỏi mơ hồ
    - **🧩 Nucleus Context Expansion**: Mở rộng context từ chunk chính xác nhất
    - **💾 Session Management**: Quản lý hội thoại thông minh
    - **⚡ VRAM-Optimized**: Giảm 0.5-1GB VRAM usage🔥 **Enhanced Features:**# 🔥 **Enhanced Features:**ong song hóa)
- Reranker: GPU (cần song song hóa)
- Ambiguous Query Detection
- Enhanced Context Expansion
"""

import logging
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.vector import VectorDBService
from app.services.language_model import LLMService
from app.services.rag_engine import RAGService
from app.services.clarification import ClarificationService
from app.api import rag
# documents và router_crud đã được xóa

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
vectordb_service = None
llm_service = None
rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle với VRAM-optimized architecture"""
    # Startup
    logger.info("🚀 Starting LegalRAG API...")
    
    try:
        # Khởi tạo services theo thứ tự tối ưu VRAM
        global vectordb_service, llm_service, rag_service
        logger.info("Initializing VRAM-optimized services...")
        
        # 1. VectorDB Service (Embedding Model sẽ được chuyển sang CPU)
        logger.info("🔧 Initializing VectorDB service with CPU embedding...")
        vectordb_service = VectorDBService()
        logger.info("✅ VectorDB service initialized (Embedding: CPU)")
        
        # 2. LLM Service (GPU cho generation tasks)
        logger.info("🔧 Initializing LLM service on GPU...")
        llm_service = LLMService()
        logger.info("✅ LLM service initialized (LLM: GPU)")
        
        # 3. Optimized Enhanced RAG Service
        logger.info("🔧 Initializing Optimized Enhanced RAG service...")
        documents_dir = settings.base_dir / "data" / "documents"  
        rag_service = RAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        logger.info("✅ Optimized Enhanced RAG service initialized")
        
        # Set global service for routes
        rag.rag_service = rag_service
        
        # Set sessions API global reference  
        try:
            from app.api import sessions
            sessions.rag_service = rag_service
            logger.info("✅ Sessions API service reference set")
        except ImportError as e:
            logger.warning(f"⚠️ Sessions API service reference failed: {e}")
        
        # 🎯 NEW: Initialize ClarificationService with embedding model
        logger.info("🔄 Initializing ClarificationService...")
        embedding_model = getattr(rag_service.smart_router, 'embedding_model', None) if hasattr(rag_service, 'smart_router') else None
        
        clarification_service = ClarificationService(embedding_model=embedding_model)
        rag.clarification_service = clarification_service
        
        if embedding_model:
            logger.info("✅ ClarificationService initialized with embedding model for real confidence calculation")
        else:
            logger.info("✅ ClarificationService initialized with fallback confidence calculation")
        
        # Log system capabilities với thông tin VRAM optimization
        health_status = rag_service.get_health_status()
        logger.info("📊 VRAM-Optimized System Status:")
        logger.info(f"  - Collections: {health_status.get('total_collections', 0)}")
        logger.info(f"  - Documents: {health_status.get('total_documents', 0)}")
        logger.info(f"  - LLM (GPU): {health_status.get('llm_loaded', False)}")
        logger.info(f"  - Reranker (GPU): {health_status.get('reranker_loaded', False)}")
        logger.info(f"  - Embedding (CPU): {health_status.get('embedding_device', 'N/A')}")
        logger.info(f"  - Active Sessions: {health_status.get('active_sessions', 0)}")
        logger.info(f"  - Ambiguous Patterns: {health_status.get('ambiguous_patterns', 0)}")
        logger.info(f"  - Context Expansion Cache: {health_status.get('context_expansion', {}).get('total_chunks_cached', 0)} chunks")
        
        logger.info("🎉 LegalRAG API started successfully!")
        logger.info("💡 Architecture: Embedding(CPU) + LLM(GPU) + Reranker(GPU)")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down LegalRAG API...")
    
    # Cleanup sessions if needed
    if rag_service:
        active_sessions = len(rag_service.chat_sessions)
        if active_sessions > 0:
            logger.info(f"Cleaning up {active_sessions} active chat sessions...")
            rag_service.chat_sessions.clear()

# Tạo Optimized FastAPI app
app = FastAPI(
    title=f"{settings.app_name} (VRAM-Optimized)",
    version=f"{settings.app_version}-vram-optimized",
    description="""
    🚀 **VRAM-Optimized LegalRAG** - Hệ thống hỏi đáp thông minh tối ưu bộ nhớ
    
    ## 🧠 **VRAM Optimization Architecture:**
    - **Embedding Model**: CPU (tiết kiệm VRAM cho queries ngắn)
    - **LLM Model**: GPU (tận dụng song song hóa cho context dài)  
    - **Reranker Model**: GPU (tận dụng song song hóa cho multiple comparisons)
    
    ## 📱 **OCR Service Features:**
    - **🆔 CCCD Recognition**: Nhận dạng căn cước công dân với VietOCR
    - **📷 Camera Integration**: Chụp ảnh qua webcam (frontend)
    - **�️ Temporary Storage**: Lưu trữ tạm thời trong Redis
    - **🔍 Text Extraction**: Trích xuất thông tin chính xác
    - **💾 Session Management**: Quản lý session xử lý
    
    ## �🔥 **Enhanced Features:**
    - **🎯 Smart Ambiguous Detection**: Tự động phát hiện câu hỏi mơ hồ
    - **🧩 Nucleus Context Expansion**: Mở rộng context từ chunk chính xác nhất
    - **💾 Session Management**: Quản lý hội thoại thông minh
    - **⚡ VRAM-Optimized**: Giảm 0.5-1GB VRAM usage
    - **🎛️ Hybrid Retrieval**: Broad search + Reranking + Context expansion
    
    ## 📡 **Available Endpoints:**
    
    ### RAG Endpoints:
    - `/api/v2/optimized-query` - Query chính với tối ưu VRAM
    - `/api/v2/clarify` - Xử lý câu trả lời làm rõ
    - `/api/v2/session/create` - Tạo session chat
    - `/api/v2/session/{id}` - Quản lý session
    - `/api/v2/health` - Trạng thái hệ thống
    
    ## 🔬 **Technical Details:**
    - **Context Window**: 4096 tokens (tối ưu cho 6GB VRAM)
    - **Max Generation**: 1024 tokens
    - **Temperature**: 0.2 (cân bằng chính xác vs đa dạng)
    - **Cache**: Redis cho session management
    - **Session TTL**: 1 hour default
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cấu hình CORS với enhanced headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include optimized routes
app.include_router(rag.router)

# Include Sessions API for admin dashboard
try:
    from app.api import sessions
    app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
    logger.info("✅ Sessions API endpoints enabled")
except ImportError as e:
    logger.warning(f"⚠️ Sessions API not available: {e}")

# Include Collections API for frontend mapping
try:
    from app.api.collections import router as collections_router
    app.include_router(collections_router, prefix="/api/v1", tags=["collections"])
    logger.info("✅ Collections API endpoints enabled")
except ImportError as e:
    logger.warning(f"⚠️ Collections API not available: {e}")

# Include Forms API for IdentiFill service
try:
    from app.api.forms import router as forms_router
    app.include_router(forms_router, prefix="/api/forms", tags=["forms"])
    logger.info("✅ Forms API endpoints enabled")
except ImportError as e:
    logger.warning(f"⚠️ Forms API not available: {e}")

# Include Internal File Management API for Admin Service
try:
    from app.api.internal_files import router as internal_files_router
    app.include_router(internal_files_router, prefix="/api", tags=["internal-files"])
    logger.info("✅ Internal Files API endpoints enabled")
except ImportError as e:
    logger.warning(f"⚠️ Internal Files API not available: {e}")

# Include Internal Rebuild API for cache management
try:
    from app.api.internal_rebuild import router as internal_rebuild_router
    app.include_router(internal_rebuild_router, prefix="/api", tags=["internal-rebuild"])
    logger.info("✅ Internal Rebuild API endpoints enabled")
except ImportError as e:
    logger.warning(f"⚠️ Internal Rebuild API not available: {e}")

# Router CRUD API đã được xóa
# try:
#     from app.api.router_crud import router as router_crud_router
#     app.include_router(router_crud_router)
#     logger.info("✅ Router CRUD API endpoints enabled")
# except ImportError as e:
#     logger.warning(f"⚠️ Router CRUD API not available: {e}")

# Root endpoint với thông tin VRAM optimization
@app.get("/")
async def root():
    return {
        "message": "LegalRAG API",
        "version": f"{settings.app_version}-vram-optimized",
        "description": "Hệ thống hỏi đáp pháp luật với kiến trúc tối ưu VRAM",
        "architecture": {
            "embedding_model": "CPU (tiết kiệm VRAM)",
            "llm_model": "GPU (song song hóa)", 
            "reranker_model": "GPU (song song hóa)"
        },
        "status": "running",
        "endpoints": {
            "rag_query": "/api/v1/query",
            "rag_collections": "/router/collections", 
            "health": "/health"
        }
    }

# Health endpoint
@app.get("/health")
async def health():
    if rag_service:
        return rag_service.get_health_status()
    else:
        return {"status": "starting", "message": "Services are initializing..."}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Disable reload to prevent restart during model downloads
        log_level="info"
    )
