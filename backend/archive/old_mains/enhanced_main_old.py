"""
Enhanced Main.py với Enhanced RAG Service
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.services.enhanced_rag_service_v2 import EnhancedRAGService
from app.utils.model_loader import auto_setup_models
from app.api import enhanced_routes

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
vectordb_service = None
llm_service = None
enhanced_rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle của ứng dụng với Enhanced RAG"""
    # Startup
    logger.info("🚀 Starting Enhanced LegalRAG API...")
    
    try:
        # Khởi tạo services
        global vectordb_service, llm_service, enhanced_rag_service
        logger.info("Initializing core services...")
        
        # VectorDB Service
        vectordb_service = VectorDBService()
        logger.info("✅ VectorDB service initialized")
        
        # LLM Service với tối ưu VRAM
        llm_service = LLMService()
        logger.info("✅ LLM service initialized")
        
        # Enhanced RAG Service
        documents_dir = settings.base_dir / "data" / "documents"  
        enhanced_rag_service = EnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        logger.info("✅ Enhanced RAG service initialized")
        
        # Set global service for enhanced routes
        enhanced_routes.enhanced_rag_service = enhanced_rag_service
        
        # Log system capabilities
        health_status = enhanced_rag_service.get_health_status()
        logger.info("📊 System Status:")
        logger.info(f"  - Collections: {health_status.get('total_collections', 0)}")
        logger.info(f"  - Documents: {health_status.get('total_documents', 0)}")
        logger.info(f"  - LLM Loaded: {health_status.get('llm_loaded', False)}")
        logger.info(f"  - Reranker: {health_status.get('reranker_loaded', False)}")
        logger.info(f"  - Context Window: {settings.context_length} tokens")
        
        logger.info("🎉 Enhanced LegalRAG API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Enhanced services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Enhanced LegalRAG API...")
    
    # Cleanup sessions if needed
    if enhanced_rag_service:
        active_sessions = len(enhanced_rag_service.chat_sessions)
        if active_sessions > 0:
            logger.info(f"Cleaning up {active_sessions} active chat sessions...")
            enhanced_rag_service.chat_sessions.clear()

# Tạo Enhanced FastAPI app
app = FastAPI(
    title=f"{settings.app_name} (Enhanced)",
    version=f"{settings.app_version}-enhanced",
    description="""
    Enhanced LegalRAG - Hệ thống hỏi đáp thông minh về thủ tục hành chính
    
    🔥 **New Enhanced Features:**
    - **Smart Query Preprocessing**: Tự động làm rõ câu hỏi mơ hồ
    - **Session Management**: Quản lý lịch sử hội thoại thông minh
    - **Hybrid Retrieval**: Tối ưu ngữ cảnh với nhiều chiến lược
    - **Optimized VRAM**: Giảm context window để tiết kiệm bộ nhớ
    - **Context Synthesis**: Tự động tổng hợp ngữ cảnh từ hội thoại
    
    📡 **Available Endpoints:**
    - `/api/v1/enhanced-query` - Enhanced query với preprocessing
    - `/api/v1/clarify` - Xử lý câu trả lời làm rõ
    - `/api/v1/session/create` - Tạo session chat
    - `/api/v1/session/{id}` - Quản lý session
    - `/api/v1/query` - Legacy endpoint (backward compatibility)
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

# Đăng ký enhanced routes
app.include_router(
    enhanced_routes.router, 
    prefix="/api/v1", 
    tags=["Enhanced Legal RAG"]
)

@app.get("/")
async def root():
    """Enhanced root endpoint"""
    return {
        "message": "Enhanced LegalRAG API",
        "version": f"{settings.app_version}-enhanced",
        "status": "running",
        "features": {
            "query_preprocessing": "✅ Smart clarification & context synthesis",
            "session_management": "✅ Conversation history tracking", 
            "hybrid_retrieval": "✅ Optimized context strategies",
            "vram_optimization": f"✅ Context window: {settings.context_length} tokens",
            "backward_compatibility": "✅ Legacy API support"
        },
        "endpoints": {
            "enhanced_query": "/api/v1/enhanced-query",
            "clarification": "/api/v1/clarify", 
            "session_create": "/api/v1/session/create",
            "legacy_query": "/api/v1/query",
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
async def api_health():
    """Enhanced health check"""
    return {
        "status": "ok", 
        "message": "Enhanced LegalRAG API is running",
        "service_type": "enhanced_rag",
        "context_window": settings.context_length,
        "features_enabled": True
    }

# Enhanced startup message
@app.on_event("startup")
async def startup_message():
    """Enhanced startup message"""
    logger.info("="*60)
    logger.info("🎯 ENHANCED LEGALRAG API READY")
    logger.info("="*60)
    logger.info("📋 Features Overview:")
    logger.info("  🧠 Smart Query Preprocessing")
    logger.info("  💬 Session Management") 
    logger.info("  🎯 Hybrid Retrieval Strategy")
    logger.info("  ⚡ Optimized VRAM Usage")
    logger.info("  🔄 Backward Compatibility")
    logger.info("="*60)
    logger.info(f"🌐 API Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔗 Test Endpoint: http://{settings.host}:{settings.port}/api/v1/enhanced-query")
    logger.info("="*60)

if __name__ == "__main__":
    # Enhanced development server
    logger.info("🔧 Starting Enhanced LegalRAG in development mode...")
    logger.info(f"📊 Configuration:")
    logger.info(f"  - Context Length: {settings.context_length}")
    logger.info(f"  - Max Tokens: {settings.max_tokens}")
    logger.info(f"  - Temperature: {settings.temperature}")
    logger.info(f"  - Broad Search K: {settings.broad_search_k}")
    logger.info(f"  - Use Reranker: {settings.use_reranker}")
    
    uvicorn.run(
        "enhanced_main:app",  # Use enhanced main
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        access_log=True
    )
