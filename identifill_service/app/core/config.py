from pydantic_settings import BaseSettings
import os
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    PROJECT_NAME: str = "IDentifill Service"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # 🔧 Environment Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")
    
    # 🔧 RAG Service Configuration
    # Auto-detect based on environment
    @property
    def RAG_SERVICE_URL(self) -> str:
        """Get RAG service URL based on environment"""
        # Check explicit environment variable first
        if url := os.getenv("RAG_SERVICE_URL"):
            return url
        
        # Auto-detect based on environment
        if self.ENVIRONMENT == "docker":
            return "http://rag-service:8000"
        else:
            return "http://localhost:8000"
    
    # 🔧 Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # 🔧 Timeout Configuration
    RAG_SERVICE_TIMEOUT: int = 30
    REQUEST_TIMEOUT: int = 60
    
    # 🔧 File Processing Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "/tmp/identifill_uploads"
    MODELS_DIR: str = "/app/models"
    
    # 💾 Document Storage Configuration
    STORAGE_DIR: str = "data"  # Base directory for document storage
    DATABASE_PATH: str = "data/legalrag.db"  # SQLite database location
    SCANNED_DOCUMENTS_DIR: str = "data/scanned_documents"  # Directory for stored CCCD scans and forms

    class Config:
        env_file = ".env"

    def model_post_init(self, __context) -> None:
        """Log configuration after initialization"""
        logger.info(f"🔧 Identifill Service Configuration:")
        logger.info(f"   - Environment: {self.ENVIRONMENT}")
        logger.info(f"   - RAG Service URL: {self.RAG_SERVICE_URL}")
        logger.info(f"   - Storage Directory: {self.STORAGE_DIR}")
        logger.info(f"   - Database Path: {self.DATABASE_PATH}")
        logger.info(f"   - Host: {self.HOST}:{self.PORT}")
        logger.info(f"   - CORS Origins: {len(self.BACKEND_CORS_ORIGINS)} origins")

settings = Settings()
