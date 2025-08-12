"""
Optimized Main.py với VRAM-optimized Enhanced RAG Service
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.services.optimized_enhanced_rag_service_v2 import OptimizedEnhancedRAGService
from app.utils.model_loader import auto_setup_models
from app.api import optimized_routes

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
vectordb_service = None
llm_service = None
optimized_rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle của ứng dụng với Optimized Enhanced RAG"""
    # Startup
    logger.info("🚀 Starting VRAM-Optimized LegalRAG API...")
    
    try:
        # Khởi tạo services
        global vectordb_service, llm_service, optimized_rag_service
        logger.info("Initializing core services with VRAM optimization...")
        
        # VectorDB Service (Embedding on CPU)
        vectordb_service = VectorDBService()
        logger.info("✅ VectorDB service initialized (Embedding: CPU)")
        
        # LLM Service (GPU for generation)
        llm_service = LLMService()
        logger.info("✅ LLM service initialized (GPU)")
        
        # Optimized Enhanced RAG Service
        documents_dir = settings.base_dir / "data" / "documents"  
        optimized_rag_service = OptimizedEnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        logger.info("✅ Optimized Enhanced RAG service initialized")
        
        # Set global service for optimized routes
        optimized_routes.optimized_rag_service = optimized_rag_service
        
        # Log system capabilities với VRAM optimization info
        health_status = optimized_rag_service.get_health_status()
        logger.info("📊 VRAM-Optimized System Status:")
        logger.info(f"  - Collections: {health_status.get('total_collections', 0)}")
        logger.info(f"  - Documents: {health_status.get('total_documents', 0)}")
        logger.info(f"  - LLM Loaded: {health_status.get('llm_loaded', False)} (GPU)")
        logger.info(f"  - Reranker: {health_status.get('reranker_loaded', False)} (GPU)")
        logger.info(f"  - Embedding: {health_status.get('embedding_device', 'CPU')}")
        logger.info(f"  - Context Window: {settings.context_length} tokens")
        logger.info(f"  - Ambiguous Patterns: {health_status.get('ambiguous_patterns', 0)}")
        logger.info(f"  - Context Cache: {health_status['context_expansion']['total_chunks_cached']} chunks")
        
        logger.info("🎉 VRAM-Optimized LegalRAG API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Optimized services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down VRAM-Optimized LegalRAG API...")
    
    # Cleanup sessions if needed
    if optimized_rag_service:
        active_sessions = len(optimized_rag_service.chat_sessions)
        if active_sessions > 0:
            logger.info(f"Cleaning up {active_sessions} active chat sessions...")
            optimized_rag_service.chat_sessions.clear()

# Tạo Optimized FastAPI app
app = FastAPI(
    title=f"{settings.app_name} (VRAM-Optimized)",
    version=f"{settings.app_version}-optimized",
    description="""
    🔥 **VRAM-Optimized LegalRAG** - Hệ thống hỏi đáp thông minh về thủ tục hành chính
    
    **🧠 VRAM-Optimized Architecture:**
    - **Embedding Model**: CPU (tiết kiệm VRAM cho query ngắn)
    - **LLM (PhoGPT-4B)**: GPU (tối ưu cho generation context dài) 
    - **Reranker**: GPU (song song hóa so sánh multiple chunks)
    
    **🔥 Enhanced Features:**
    - **Ambiguous Query Detection**: Phát hiện và xử lý câu hỏi mơ hồ
    - **Nucleus Chunk Strategy**: Context expansion thông minh
    - **Session Management**: Quản lý lịch sử hội thoại
    - **Smart Query Routing**: Định tuyến query tối ưu
    - **VRAM Optimization**: Phân bổ tài nguyên thông minh
    
    **📡 Available Optimized Endpoints:**
    - `/api/v1/optimized-query` - Enhanced query với VRAM optimization
    - `/api/v1/clarify` - Xử lý câu trả lời làm rõ
    - `/api/v1/session/create` - Tạo session chat
    - `/api/v1/session/{id}` - Quản lý session
    - `/api/v1/health` - Health check với VRAM info
    - `/api/v1/metrics` - Performance metrics
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cấu hình CORS với optimized headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include optimized routes
app.include_router(optimized_routes.router)

# Root endpoint với VRAM optimization info
@app.get("/")
async def root():
    """Root endpoint với thông tin VRAM optimization"""
    return {
        "message": "🔥 VRAM-Optimized LegalRAG API",
        "version": f"{settings.app_version}-optimized", 
        "architecture": {
            "embedding": "CPU (VRAM optimized)",
            "llm": "GPU (PhoGPT-4B)",
            "reranker": "GPU",
            "strategy": "Nucleus Chunk + Full Document Expansion"
        },
        "features": [
            "Ambiguous Query Detection",
            "Smart Context Expansion", 
            "Session Management",
            "VRAM-Optimized Model Placement"
        ],
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "vram_optimized_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
